from state.state import GraphState
from LLMs.gemini_llm import call_llm
from field_extraction.main import get_int_value,get_value,get_list_value
from prompts.main import destination_agent_prompt


def destination_agent(state: GraphState):
    print(">> Destination Agent Running")

    prompt = destination_agent_prompt(state)
    
    answer = call_llm(prompt)

    state["activities"] = get_list_value(answer, "ACTIVITIES")
    state["unsuitable_activities"] = get_list_value(answer, "UNSUITABLE_ACTIVITIES")
    state["summary"]["D"] = get_value(answer, "SUMMARY")

    state["results"]["D"] = answer
    state["current_step"] += 1

    return state

