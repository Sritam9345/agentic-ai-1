from typing import List, Dict, Any
from state.state import GraphState
from graph.graph_logic import graph
from langgraph.graph import END
from langgraph.types import Command

from langchain_core.messages import  HumanMessage



AGENT_LABELS: Dict[str, str] = {
    "P": "🧭 Planner Agent",
    "D": "🗺️ Destination & Experience Agent",
    "W": "🌦️ Weather & Seasonality Agent",
    "T": "🚗 Transport & Distance Agent",
    "B": "💰 Budget Agent",
    "I": "🧳 Itinerary Composer Agent",
}


def _stream_and_get_final(input_data, thread_id: str):
    """
    Shared streaming helper.

    Streams the graph node-by-node (stream_mode="updates") purely to report
    progress ({"node": ..., "label": ...} events) so the UI can show which
    agent is currently running.

    Once the run finishes (or hits an interrupt), the authoritative final
    state is read back from the checkpointer via graph.get_state(), rather
    than being hand-assembled from the partial "updates" stream. This keeps
    behavior identical to run_graph/resume_graph (correct message-history
    reducers, correct "__interrupt__" payload, etc.).
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 100,
    }

    for update in graph.stream(input_data, config=config, stream_mode="updates"):
        for node_name in update.keys():
            if node_name == "__interrupt__":
                continue

            yield {
                "node": node_name,
                "label": AGENT_LABELS.get(node_name, node_name),
            }

    snapshot = graph.get_state(config)
    final_state: Dict[str, Any] = dict(snapshot.values)

    pending_interrupts = []
    for task in snapshot.tasks:
        if task.interrupts:
            pending_interrupts.extend(task.interrupts)

    if pending_interrupts:
        final_state["__interrupt__"] = tuple(pending_interrupts)

    yield {
        "node": "__final__",
        "label": "Done",
        "final_state": final_state,
    }


def stream_graph(state: GraphState, user_input: str, thread_id: str):
    """
    Streaming equivalent of run_graph. Yields progress events as
    {"node": <id>, "label": <friendly name>} while agents execute, then a
    final {"node": "__final__", "final_state": <dict>} event carrying the
    same payload run_graph would have returned.
    """
    state["messages"].append(
        HumanMessage(content=user_input)
    )

    state["conversation_history"] += (
        f"\nUser: {user_input}"
    )

    yield from _stream_and_get_final(state, thread_id)


def stream_resume_graph(user_input: str, thread_id: str):
    """
    Streaming equivalent of resume_graph. Same event shape as stream_graph.
    """
    yield from _stream_and_get_final(Command(resume=user_input), thread_id)



def get_initial_state() -> GraphState:
    
    return {
        "messages": [],
        "conversation_history": [],
        "user_query": "",
        "destination": "",
        "source_city": "",
        "dates": "",
        "duration_days": 0,
        "travelers": "",
        "travel_style": "",

        "season": "",
        "weather": "",
        "temperature": "",
        "weather_risks": "",

        "budget": "",
        "estimated_cost": "",
        "budget_status": "",
        "budget_tradeoffs": "",

        "activities": "",
        "unsuitable_activities": "",

        "shortest_travel_route": "",
        "local_transport_plan": "",
        "travel_time_notes": "",

        "itinerary": "",

        "plan": [],
        "current_step": 0,

        "results": {},
        
        "change": "",
        "summary":{}
    }