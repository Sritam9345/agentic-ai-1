

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

from langchain_core.messages import HumanMessage


from state.state import GraphState


from agents.planner_agent import planner_agent
from agents.destination_agent import destination_agent
from agents.weather_agent import weather_agent
from agents.transportation_agent import transport_agent
from agents.budget_agent import budget_agent
from agents.iteneray_agent import itinerary_agent

from router.main import route_next



builder = StateGraph(GraphState)

builder.add_node("P", planner_agent)
builder.add_node("D", destination_agent)
builder.add_node("W", weather_agent)
builder.add_node("T", transport_agent)
builder.add_node("B", budget_agent)
builder.add_node("I", itinerary_agent)

builder.set_entry_point("P")


mapping = {
    "P": "P",
    "D": "D",
    "W": "W",
    "T": "T",
    "B": "B",
    "I": "I",
    "END": END,
}


builder.add_conditional_edges(
    "P",
    route_next,
    mapping,
)

builder.add_conditional_edges(
    "D",
    route_next,
    mapping,
)

builder.add_conditional_edges(
    "W",
    route_next,
    mapping,
)


builder.add_conditional_edges(
    "T",
    route_next,
    mapping,
)

builder.add_conditional_edges(
    "B",
    route_next,
    mapping,
)

builder.add_conditional_edges(
    "I",
    route_next,
    mapping,
)



checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)



async def run_graph(state: GraphState, user_input: str, thread_id: str):
    state["messages"].append(
        HumanMessage(content=user_input)
    )

    state["conversation_history"] += (
        f"\nUser: {user_input}"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 100,
    }

    return await graph.ainvoke(
        state,
        config=config,
    )


async def resume_graph(user_input: str, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 100,
    }

    return await graph.ainvoke(
        Command(resume=user_input),
        config=config,
    )

