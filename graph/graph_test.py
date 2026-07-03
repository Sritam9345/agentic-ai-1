from typing import List, Dict
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver



class GraphState(TypedDict):
    user_query: str
    plan: List[str]
    current_step: int
    results: Dict[str, str]
    cycle: bool


def planner_node(state: GraphState):
    query = state["user_query"]

    cycle = False

    plan = state["plan"]

    if len(state['plan']) -1 == state['current_step'] and state["current_step"]!=0:
        print("hitl hit")
        cycle = True

    if cycle == False:
        if "cheap" in query:
            plan = ["B", "W", "D","P"]
        elif "full" in query:
            plan = ["T", "B", "W", "D","P"]
        else:
            plan = ["T", "B", "W","P"]

        print(f"\n[Planner] Generated Plan: {plan}")


    if cycle == True:
        
        human_input = interrupt({
                "question": "Route completed. Do you want to stop or give a new route?",
                "instructions": {
                    "stop": "type yes or stop to end",
                    "new_plan": "type TBW / BWD / D etc. for a new route"
                }
            })


        if human_input == "yes":
            plan = ["I","END"]
        else:
            print(human_input)
            plan = []
            for i in human_input:
                if i != "P":
                    plan.append(i)
            
            plan.append("P")
                
            print(plan)



    return {
        "plan": plan,
        "current_step": 0,
        "results": {}
    }


def route_next(state: GraphState):
    step = state["current_step"]
    plan = state["plan"]

    next_agent = plan[step]
    print(f"\n[Router] Next Step: {next_agent}")
    return next_agent


def transport_node(state: GraphState):
    print(">> Transport Agent Running")

    state["results"]["T"] = "Transport planned"
    state["current_step"] += 1

    return state


def budget_node(state: GraphState):
    print(">> Budget Agent Running")

    state["results"]["B"] = "Budget calculated"
    state["current_step"] += 1

    return state


def weather_node(state: GraphState):
    print(">> Weather Agent Running")

    state["results"]["W"] = "Weather checked"
    state["current_step"] += 1

    return state


def destination_node(state: GraphState):
    print(">> Destination Agent Running")

    state["results"]["D"] = "Destination decided"
    state["current_step"] += 1

    return state


def approval_node(state: GraphState):
    print("Waiting for human approval...")

    human_input = interrupt({
        "question": "Approve the plan?",
        "plan": state["plan"]
    })

    state["results"]["U"] = human_input
    state["current_step"] += 1

    return state

def itenary_node(state: GraphState):
    print(">> Iterenary Agent Running")

    state["results"]["I"] = "Iterenary Agent Done"
    state["current_step"] += 1

    return state

builder = StateGraph(GraphState)

builder.add_node("P", planner_node)
builder.add_node("T", transport_node)
builder.add_node("B", budget_node)
builder.add_node("W", weather_node)
builder.add_node("D", destination_node)
builder.add_node("U", approval_node)
builder.add_node("I",itenary_node)

builder.set_entry_point("P")


mapping = {
    "T": "T",
    "B": "B",
    "W": "W",
    "D": "D",
    "U": "U",
    "P" :"P",
    "END": END,
    "I":"I"
}


builder.add_conditional_edges(
    "P",
    route_next,
    mapping
)


for node in ["T", "B", "W", "D", "U"]:
    builder.add_conditional_edges(
        node,
        route_next,
        mapping
    )


checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)


config = {
    "configurable": {
        "thread_id": "1"
    }
}


result = graph.invoke(
    {"user_query": "cheap",
     "plan": [],
     "current_step":0},
    config=config
)

print("\nFIRST RESULT:")

while "__interrupt__" in result:

    human_answer = input("Enter yes or suggest new plan like TBW , BWD etc: ")
    
    result = graph.invoke(
        Command(resume=human_answer),
        config=config
    )


print(result)
