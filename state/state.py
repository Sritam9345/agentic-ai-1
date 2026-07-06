
from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage, HumanMessage


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
    
    change: str
    
    summary: Dict[str,Any]

