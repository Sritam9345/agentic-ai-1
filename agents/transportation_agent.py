from state.state import GraphState
from LLMs.gemini_llm import call_llm
from parsers.main import get_list_value,get_value
from prompts.main import transport_agent_prompt


def transport_agent(state: GraphState):
    print(">> Transport Agent Running")

    prompt = transport_agent_prompt(state)
    answer = call_llm(prompt)
    
    
    

    state["shortest_travel_route"] = get_value(answer, "SHORTEST_TRAVEL_ROUTE")
    state["local_transport_plan"] = get_value(answer, "LOCAL_TRANSPORT_PLAN")
    state["travel_time_notes"] = get_list_value(answer, "TRAVEL_TIME_NOTES")
    print("hi1")
    state["summary"]["T"] = get_value(answer, "SUMMARY")
    print("hi2")
    state["results"]["T"] = answer
    state["current_step"] += 1
    print("hi3")
    return state
