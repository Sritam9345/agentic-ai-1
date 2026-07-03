from typing_extensions import Annotated

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import InjectedState
from langgraph.types import Command


@tool
def weather_api(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Hardcoded weather API.

    Reads season from graph state.
    If season is missing, defaults to summer.
    Updates weather, temperature, and weather_risks.
    """

    season = state.get("season") or "summer"
    season = season.strip().lower()

    weather_db = {
        "summer": {
            "weather": "Hot and humid",
            "temperature": "32°C - 38°C",
            "weather_risks": [
                "Heat exhaustion",
                "Dehydration",
                "Strong afternoon sun",
            ],
        },
        "winter": {
            "weather": "Pleasant and cool",
            "temperature": "18°C - 28°C",
            "weather_risks": [
                "Cool evenings",
                "Early morning fog",
            ],
        },
        "monsoon": {
            "weather": "Rainy and humid",
            "temperature": "24°C - 30°C",
            "weather_risks": [
                "Heavy rainfall",
                "Waterlogging",
                "Travel delays",
                "Outdoor activity disruption",
            ],
        },
        "rainy": {
            "weather": "Rainy and humid",
            "temperature": "24°C - 30°C",
            "weather_risks": [
                "Heavy rainfall",
                "Waterlogging",
                "Travel delays",
                "Outdoor activity disruption",
            ],
        },
        "spring": {
            "weather": "Warm and pleasant",
            "temperature": "24°C - 32°C",
            "weather_risks": [
                "Mild heat",
                "Occasional dust or pollen discomfort",
            ],
        },
        "autumn": {
            "weather": "Mild and comfortable",
            "temperature": "22°C - 30°C",
            "weather_risks": [
                "Occasional humidity",
                "Slight temperature variation",
            ],
        },
        "fall": {
            "weather": "Mild and comfortable",
            "temperature": "22°C - 30°C",
            "weather_risks": [
                "Occasional humidity",
                "Slight temperature variation",
            ],
        },
    }

    if season not in weather_db:
        season = "summer"

    weather_info = weather_db[season]

    weather_result = {
        "season": season,
        "weather": weather_info["weather"],
        "temperature": weather_info["temperature"],
        "weather_risks": weather_info["weather_risks"],
    }

    old_results = state.get("results", {})

    return Command(
        update={
            "season": season,
            "weather": weather_info["weather"],
            "temperature": weather_info["temperature"],
            "weather_risks": weather_info["weather_risks"],
            "results": {
                **old_results,
                "W": weather_result,
                "WEATHER_API": weather_result,
            },
            "messages": [
                ToolMessage(
                    content=f"Weather updated using weather_api: {weather_result}",
                    name="weather_api",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )