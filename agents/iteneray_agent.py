from state.state import GraphState
from LLMs.gemini_llm import call_llm
from prompts.main import iternary_agent_prompt


def itinerary_agent(state: GraphState):
    print(">> Itinerary Agent Running")

    prompt = iternary_agent_prompt(state)
    answer = call_llm(prompt)

    state["itinerary"] = answer
    state["results"]["I"] = answer
    state["current_step"] += 1

    return state

