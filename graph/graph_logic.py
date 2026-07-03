from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage, HumanMessage

from LLMs.gemini_llm import llm
from tools.main import weather_api


client = llm

weather_llm = llm.bind_tools(
    [weather_api],
    tool_choice="weather_api",
)


# ==============================
# STATE
# ==============================
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

    user_query: str
    conversation_history: List[str]

    plan: List[str]
    current_step: int

    destination: str
    source_city: str
    dates: str
    duration_days: int
    travelers: str
    travel_style: str

    season: str
    weather: str
    temperature: str
    weather_risks: List[str]

    activities: List[str]
    unsuitable_activities: List[str]

    shortest_travel_route: str
    local_transport_plan: str
    travel_time_notes: List[str]

    budget: int
    estimated_cost: int
    budget_status: str
    budget_tradeoffs: List[str]

    itinerary: str

    results: Dict[str, Any]


# ==============================
# COMMON LLM CALL
# ==============================
def call_llm(prompt: str) -> str:
    response = client.invoke(prompt)

    if isinstance(response.content, str):
        return response.content.strip()

    return str(response.content).strip()


# ==============================
# SMALL PARSERS
# ==============================
def get_value(text: str, key: str) -> str:
    key = key.upper()

    for line in text.splitlines():
        if line.upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()

    return ""


def get_list_value(text: str, key: str) -> List[str]:
    value = get_value(text, key)

    if not value:
        return []

    return [x.strip() for x in value.split(",") if x.strip()]


def get_int_value(text: str, key: str) -> int:
    value = get_value(text, key)
    digits = "".join(ch for ch in value if ch.isdigit())

    return int(digits) if digits else 0


def parse_route(route_text: str) -> List[str]:
    valid = {"D", "W", "T", "B", "P", "I", "END"}

    route_text = route_text.replace("\n", ",")
    parts = [x.strip().upper() for x in route_text.split(",")]

    route = [x for x in parts if x in valid]

    if not route:
        return ["D", "W", "T", "B", "P"]

    if "I" in route:
        return ["I", "END"]

    if route == ["P"]:
        return ["D", "W", "T", "B", "P"]

    route = [x for x in route if x != "P"]

    route.append("P")

    return route


# ==============================
# TRIP FIELD EXTRACTION LLM
# ==============================
def extract_trip_fields_llm(state: GraphState, latest_input: str) -> Dict[str, Any]:
    prompt = f"""
You extract trip planning fields from user input.

Return ONLY in this format:

DESTINATION:
SOURCE_CITY:
DATES:
DURATION_DAYS:
TRAVELERS:
TRAVEL_STYLE:
SEASON:
BUDGET:

Current known state:
Destination: {state["destination"]}
Source city: {state["source_city"]}
Dates: {state["dates"]}
Duration days: {state["duration_days"]}
Travelers: {state["travelers"]}
Travel style: {state["travel_style"]}
Season: {state["season"]}
Budget: {state["budget"]}

Conversation:
{state["conversation_history"]}

Latest input:
{latest_input}
"""

    text = call_llm(prompt)

    return {
        "destination": get_value(text, "DESTINATION"),
        "source_city": get_value(text, "SOURCE_CITY"),
        "dates": get_value(text, "DATES"),
        "duration_days": get_int_value(text, "DURATION_DAYS"),
        "travelers": get_value(text, "TRAVELERS"),
        "travel_style": get_value(text, "TRAVEL_STYLE"),
        "season": get_value(text, "SEASON"),
        "budget": get_int_value(text, "BUDGET"),
    }


def apply_extracted_fields(state: GraphState, extracted: Dict[str, Any]):
    if extracted["destination"]:
        state["destination"] = extracted["destination"]

    if extracted["source_city"]:
        state["source_city"] = extracted["source_city"]

    if extracted["dates"]:
        state["dates"] = extracted["dates"]

    if extracted["duration_days"]:
        state["duration_days"] = extracted["duration_days"]

    if extracted["travelers"]:
        state["travelers"] = extracted["travelers"]

    if extracted["travel_style"]:
        state["travel_style"] = extracted["travel_style"]

    if extracted["season"]:
        state["season"] = extracted["season"]

    if extracted["budget"]:
        state["budget"] = extracted["budget"]

    return state


# ==============================
# PLANNER LLM
# ==============================
def planner_llm(state: GraphState, latest_input: str) -> Dict[str, str]:
    prompt = f"""
You are the Planner / Orchestrator Agent.

Available agents:
D = Destination and Experience Agent
W = Weather and Seasonality Agent
T = Transport and Distance Agent
B = Budget Agent
I = Itinerary Composer Agent
P = Return to Planner for human feedback
END = End graph

Your job:
1. Decide if enough information exists to continue.
2. If information is insufficient, ask one clarifying question.
3. The clarifying question must be generated by you.
4. If enough information exists, decide the route.
5. If user wants final itinerary, route must be I,END.
6. For normal planning/replanning, route must end with P.
7. Return ONLY this format:

ACTION: ASK or ROUTE
QUESTION:
ROUTE:

Known state:
Destination: {state["destination"]}
Source city: {state["source_city"]}
Dates: {state["dates"]}
Duration days: {state["duration_days"]}
Travelers: {state["travelers"]}
Travel style: {state["travel_style"]}
Season: {state["season"]}
Budget: {state["budget"]}

Agent results:
{state["results"]}

Conversation:
{state["conversation_history"]}

Latest user input:
{latest_input}

Examples:
ACTION: ASK
QUESTION: What is your budget and trip duration?
ROUTE:

ACTION: ROUTE
QUESTION:
ROUTE: D,W,T,B,P

ACTION: ROUTE
QUESTION:
ROUTE: I,END
"""

    text = call_llm(prompt)

    return {
        "action": get_value(text, "ACTION").upper(),
        "question": get_value(text, "QUESTION"),
        "route": get_value(text, "ROUTE"),
    }


# =============ANNER NODE
# ==============================
def planner_node(state: GraphState):
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
        }

    question_decision = planner_llm(
        state,
        "The current route is complete. Ask the user whether to finalize or replan.",
    )

    llm_question = question_decision["question"]

    if not llm_question:
        llm_question = call_llm(f"""
Generate one short clarifying question for the user after trip planning agents completed.

Known state:
Destination: {state["destination"]}
Dates: {state["dates"]}
Budget: {state["budget"]}
Results: {state["results"]}

Do not give route. Only ask the question.
""")

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
    }


# ==============================
# ROUTERS
# ==============================
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


def route_after_weather_agent(state: GraphState):
    if not state["messages"]:
        print("[Weather Router] No messages found.")
        return END

    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("[Weather Router] Tool call found. Going to WEATHER_TOOL.")
        return "WEATHER_TOOL"

    print("[Weather Router] No tool call found. Ending.")
    return END


# ==============================
# DESTINATION AGENT
# ==============================
def destination_agent(state: GraphState):
    print(">> Destination Agent Running")

    prompt = f"""
You are Destination and Experience Agent.

Task:
- Suggest destination regions and experiences.
- Match travel style and travelers.
- Avoid unsuitable activities.

Return ONLY this format:

ACTIVITIES:
UNSUITABLE_ACTIVITIES:
SUMMARY:

State:
Destination: {state["destination"]}
Dates: {state["dates"]}
Travelers: {state["travelers"]}
Travel style: {state["travel_style"]}
Existing results: {state["results"]}
"""

    answer = call_llm(prompt)

    state["activities"] = get_list_value(answer, "ACTIVITIES")
    state["unsuitable_activities"] = get_list_value(answer, "UNSUITABLE_ACTIVITIES")

    state["results"]["D"] = answer
    state["current_step"] += 1

    return state


# ==============================
# WEATHER AGENT
# ==============================

def infer_season_llm(state: GraphState) -> str:
    prompt = f"""
You are a Weather Season Detection Agent.

Your task:
Infer the travel season from the trip details.

Return ONLY this format:

SEASON:

Allowed values:
summer
winter
monsoon
rainy
spring
autumn

Trip details:
Destination: {state["destination"]}
Dates: {state["dates"]}
Current season in state: {state["season"]}

Rules:
- If Current season in state is already present, return that.
- If dates indicate June/July/August/September in India/Goa, prefer monsoon.
- If you cannot infer season, return summer.
"""

    answer = call_llm(prompt)

    season = get_value(answer, "SEASON").strip().lower()

    allowed = {"summer", "winter", "monsoon", "rainy", "spring", "autumn"}

    if season not in allowed:
        season = "summer"

    return season


def weather_agent(state: GraphState):
    print(">> Weather Agent Running")

    # Step 1: Weather LLM fills season before tool call
    inferred_season = infer_season_llm(state)

    print("[Weather Agent] Inferred Season:", inferred_season)

    # Update local state before tool call
    state["season"] = inferred_season

    # Step 2: Gemini calls weather_api tool
    prompt = f"""
You are Weather and Seasonality Agent.

You have access to the weather_api tool.

Task:
Use the weather_api tool to update these graph state fields:
- season
- weather
- temperature
- weather_risks

Current state:
Destination: {state["destination"]}
Dates: {state["dates"]}
Season: {state["season"]}
Activities: {state["activities"]}

Important:
You must call the weather_api tool.
Do not answer directly.
"""

    response = weather_llm.invoke([
        HumanMessage(content=prompt)
    ])

    print("[Weather Agent Tool Calls]:", response.tool_calls)

    return {
        "season": inferred_season,
        "messages": [response],
    }



def weather_done_node(state: GraphState):
    print(">> Weather Step Completed")

    return {
        "current_step": state["current_step"] + 1
    }


# ==============================
# TRANSPORT AGENT
# ==============================
def transport_agent(state: GraphState):
    print(">> Transport Agent Running")

    prompt = f"""
You are Transport and Distance Agent.

Task:
- Suggest shortest realistic travel route.
- Suggest local transport plan.
- Reduce unnecessary travel.
- Consider duration and destination.

Return ONLY this format:

SHORTEST_TRAVEL_ROUTE:
LOCAL_TRANSPORT_PLAN:
TRAVEL_TIME_NOTES:
SUMMARY:

State:
Source city: {state["source_city"]}
Destination: {state["destination"]}
Duration days: {state["duration_days"]}
Activities: {state["activities"]}
Existing results: {state["results"]}
"""

    answer = call_llm(prompt)

    state["shortest_travel_route"] = get_value(answer, "SHORTEST_TRAVEL_ROUTE")
    state["local_transport_plan"] = get_value(answer, "LOCAL_TRANSPORT_PLAN")
    state["travel_time_notes"] = get_list_value(answer, "TRAVEL_TIME_NOTES")

    state["results"]["T"] = answer
    state["current_step"] += 1

    return state


# ==============================
# BUDGET AGENT
# ==============================
def budget_agent(state: GraphState):
    print(">> Budget Agent Running")

    prompt = f"""
You are Budget Agent.

Task:
- Estimate high-level cost.
- Check budget feasibility.
- Suggest budget tradeoffs.

Return ONLY this format:

BUDGET:
ESTIMATED_COST:
BUDGET_STATUS:
BUDGET_TRADEOFFS:
SUMMARY:

State:
Destination: {state["destination"]}
Duration days: {state["duration_days"]}
Travelers: {state["travelers"]}
Budget: {state["budget"]}
Activities: {state["activities"]}
Transport: {state["shortest_travel_route"]}
Weather: {state["weather"]}
Temperature: {state["temperature"]}
Weather risks: {state["weather_risks"]}
Existing results: {state["results"]}
"""

    answer = call_llm(prompt)

    parsed_budget = get_int_value(answer, "BUDGET")
    estimated_cost = get_int_value(answer, "ESTIMATED_COST")

    if parsed_budget:
        state["budget"] = parsed_budget

    state["estimated_cost"] = estimated_cost
    state["budget_status"] = get_value(answer, "BUDGET_STATUS")
    state["budget_tradeoffs"] = get_list_value(answer, "BUDGET_TRADEOFFS")

    state["results"]["B"] = answer
    state["current_step"] += 1

    return state


# ==============================
# ITINERARY AGENT
# ==============================
def itinerary_agent(state: GraphState):
    print(">> Itinerary Agent Running")

    prompt = f"""
You are Itinerary Composer Agent.

Task:
Create final day-wise itinerary using all agent outputs.
Explain why decisions were made.
Make it user-friendly.

State:
Destination: {state["destination"]}
Source city: {state["source_city"]}
Dates: {state["dates"]}
Duration days: {state["duration_days"]}
Travelers: {state["travelers"]}
Travel style: {state["travel_style"]}
Budget: {state["budget"]}
Estimated cost: {state["estimated_cost"]}

Season: {state["season"]}
Weather: {state["weather"]}
Temperature: {state["temperature"]}
Weather risks: {state["weather_risks"]}

Activities: {state["activities"]}
Unsuitable activities: {state["unsuitable_activities"]}

Shortest route: {state["shortest_travel_route"]}
Local transport: {state["local_transport_plan"]}
Travel notes: {state["travel_time_notes"]}

Budget status: {state["budget_status"]}
Budget tradeoffs: {state["budget_tradeoffs"]}

Raw results:
{state["results"]}
"""

    answer = call_llm(prompt)

    state["itinerary"] = answer
    state["results"]["I"] = answer
    state["current_step"] += 1

    return state


# ==============================
# BUILD GRAPH
# ==============================
builder = StateGraph(GraphState)

builder.add_node("P", planner_node)
builder.add_node("D", destination_agent)
builder.add_node("W", weather_agent)
builder.add_node("WEATHER_TOOL", ToolNode([weather_api]))
builder.add_node("WEATHER_DONE", weather_done_node)
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
    route_after_weather_agent,
    {
        "WEATHER_TOOL": "WEATHER_TOOL",
        END: END,
    },
)

builder.add_edge("WEATHER_TOOL", "WEATHER_DONE")

builder.add_conditional_edges(
    "WEATHER_DONE",
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


# ==============================
# COMPILE
# ==============================
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)


# ==============================
# RUN
# ==============================


def run_graph(state: GraphState, user_input: str, thread_id: str):
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

    return graph.invoke(
        state,
        config=config,
    )


def resume_graph(user_input: str, thread_id: str):
    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 100,
    }

    return graph.invoke(
        Command(resume=user_input),
        config=config,
    )


# ==============================
# STREAMING RUN (for live "which agent is running" UI)
# ==============================

# Human-friendly labels for every node in the graph, keyed by node name.
AGENT_LABELS: Dict[str, str] = {
    "P": "🧭 Planner Agent",
    "D": "🗺️ Destination & Experience Agent",
    "W": "🌦️ Weather & Seasonality Agent",
    "WEATHER_TOOL": "🌦️ Weather Agent (fetching live weather data)",
    "WEATHER_DONE": "🌦️ Weather & Seasonality Agent",
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
    }