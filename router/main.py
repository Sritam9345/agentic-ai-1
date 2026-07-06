from state.state import GraphState
from langgraph.graph import StateGraph, END

def route_next(state: GraphState):
    step = state["current_step"]
    plan = state["plan"]

    if not plan:
        print("[Router] Empty plan. Ending.")
        return END

    if step >= len(plan):
        print("[Router] Plan completed. Ending.")
        return END

    next_agent = plan[step]

    print(f"\n[Router] Current Step: {step}")
    print(f"[Router] Plan: {plan}")
    print(f"[Router] Next Step: {next_agent}")

    return next_agent
