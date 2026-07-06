from state.state import GraphState
from typing import List, Dict, Any
from parsers.main import get_value,get_int_value,get_list_value
from LLMs.gemini_llm import call_llm
from prompts.main import trip_extraction_prompt

def extract_trip_fields_llm(state: GraphState, latest_input: str) -> Dict[str, Any]:
    prompt = trip_extraction_prompt(state=state,latest_input=latest_input)
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

