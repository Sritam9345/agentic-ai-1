from state.state import GraphState
from LLMs.gemini_llm import call_llm
from field_extraction.main import get_int_value,get_list_value,get_value
from mcp import ClientSession
import json
import asyncio
from mcp.client.streamable_http import streamable_http_client
from typing import List, Dict, Any
from prompts.main import weather_agent_prompt


def infer_season_llm(state: GraphState) -> str:
    
    prompt = weather_agent_prompt(state)
    
    answer = call_llm(prompt)

    season = get_value(answer, "SEASON").strip().lower()
    
    tool_required = get_value(answer, "TOOL").strip().lower()
    
    summary = get_value(answer, "SUMMARY")

    allowed = {"summer", "winter", "monsoon", "rainy", "spring", "autumn"}
    
    allowed_tool = {"yes","no"}

    if season not in allowed:
        season = "summer"
    
    if tool_required not in allowed_tool:
        tool_required = "yes"

    return season , tool_required , summary


async def _fetch_weather_from_mcp(season: str) -> Dict[str, Any]:
    async with streamable_http_client(
        "http://localhost:9000/mcp"
    ) as (read, write, get_session_id_callback):
        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_weather",
                {
                    "season": season
                },
            )

            print(result.content[0].text)

            return json.loads(result.content[0].text)


def weather_agent(state: GraphState):
    print(">> Weather Agent Running")

    inferred_season, tool_required , summary = infer_season_llm(state)

    print("[Weather Agent] Inferred Season:", inferred_season)

    data: Dict[str, Any] = {}

    if tool_required == "yes":
        data = asyncio.run(_fetch_weather_from_mcp(inferred_season))
        
    current_summary = state["summary"]
    
    current_summary["W"] = summary    

    
    return {
        "season": inferred_season,
        "weather": data.get("weather") or state["weather"],
        "temperature": data.get("temperature") or state["temperature"],
        "weather_risks": data.get("weather_risks") or state["weather_risks"],
        "current_step": state["current_step"] + 1,
        "summary": current_summary
        
    }



