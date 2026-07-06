from state.state import GraphState
from LLMs.gemini_llm import call_llm
from parsers.main import get_int_value,parse_route,get_list_value,get_value
from field_extraction.main import extract_trip_fields_llm,apply_extracted_fields
from prompts.main import llm_question_prompt,planner_agent_prompt
from typing import List, Dict, Any
from langgraph.types import interrupt, Command

def planner_llm(state: GraphState, latest_input: str) -> Dict[str, str]:
    
    prompt = planner_agent_prompt(state,latest_input)
    
    text = call_llm(prompt)

    return {
        "action": get_value(text, "ACTION").upper(),
        "question": get_value(text, "QUESTION"),
        "route": get_value(text, "ROUTE"),
        "change": get_value(text, "CHANGE") or ""
    }



def planner_agent(state: GraphState):
    print("\n>> Planner Agent Running")

    plan = state["plan"]
    current_step = state["current_step"]

    cycle = False

    if len(plan) - 1 == current_step and current_step != 0:
        print("hitl hit")
        cycle = True

    if cycle is False:
        latest_input = state["user_query"]

        state["conversation_history"].append(f"User: {latest_input}")

        extracted = extract_trip_fields_llm(state, latest_input)
        state = apply_extracted_fields(state, extracted)

        decision = planner_llm(state, latest_input)

        print("[Planner Raw Decision]", decision)

        if decision["action"] == "ASK":
            human_answer = interrupt({
                "question": decision["question"],
                "reason": "Planner needs more information before routing.",
            })

            state["conversation_history"].append(f"User: {human_answer}")

            extracted = extract_trip_fields_llm(state, str(human_answer))
            state = apply_extracted_fields(state, extracted)

            decision = planner_llm(state, str(human_answer))

        new_plan = parse_route(decision["route"])

        print("[Planner] Route:", new_plan)

        return {
            **state,
            "plan": new_plan,
            "current_step": 0,
            "change":decision["change"]
            
        }

    question_decision = planner_llm(
        state,
        "The current route is complete. Ask the user whether to finalize or replan.",
    )

    llm_question = question_decision["question"]

    if not llm_question:
        
        llm_question_prompt_value = llm_question_prompt(state)
        
        llm_question = call_llm(llm_question_prompt_value)

    human_answer = interrupt({
        "question": llm_question,
        "current_results": state["results"],
    })

    state["conversation_history"].append(f"User: {human_answer}")

    extracted = extract_trip_fields_llm(state, str(human_answer))
    state = apply_extracted_fields(state, extracted)

    decision = planner_llm(state, str(human_answer))

    if decision["action"] == "ASK":
        second_answer = interrupt({
            "question": decision["question"],
            "reason": "Planner needs one more clarification.",
        })

        state["conversation_history"].append(f"User: {second_answer}")

        extracted = extract_trip_fields_llm(state, str(second_answer))
        state = apply_extracted_fields(state, extracted)

        decision = planner_llm(state, str(second_answer))

    new_plan = parse_route(decision["route"])

    print("[Planner] New Route:", new_plan)

    return {
        **state,
        "plan": new_plan,
        "current_step": 0,
        "change":decision["change"] or ""
    }
