from state.state import GraphState
from LLMs.gemini_llm import call_llm
from parsers.main import get_list_value,get_value,get_int_value
from prompts.main import budget_agent_prompt


def budget_agent(state: GraphState):
    print(">> Budget Agent Running")

    prompt = budget_agent_prompt(state)
    
    answer = call_llm(prompt)

    parsed_budget = get_int_value(answer, "BUDGET")
    estimated_cost = get_int_value(answer, "ESTIMATED_COST")

    if parsed_budget:
        state["budget"] = parsed_budget

    state["estimated_cost"] = estimated_cost
    state["budget_status"] = get_value(answer, "BUDGET_STATUS")
    state["budget_tradeoffs"] = get_list_value(answer, "BUDGET_TRADEOFFS")
    state["summary"]["B"] = get_value(answer, "SUMMARY")

    state["results"]["B"] = answer
    state["current_step"] += 1

    return state

