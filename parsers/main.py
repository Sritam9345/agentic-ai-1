from typing import List, Dict, Any


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

