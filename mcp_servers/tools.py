from fastmcp import FastMCP


mcp = FastMCP("tools Server")

@mcp.tool
def get_weather(season: str):
    """
    Returns weather information for a season.
    """
    season = (season or "summer").strip().lower()

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

    info = weather_db[season]

    return {
        "season": season,
        "weather": info["weather"],
        "temperature": info["temperature"],
        "weather_risks": info["weather_risks"],
    }
    
    
@mcp.tool
def transport_api(user_source_city: str, user_destination: str):
    """
    Returns predefined transport route details between popular Indian cities.
    Params:
    - user_source_city: name of the source city
    - user_destination: name of the destination city
    """
 
    source_city = user_source_city.strip().lower()
    destination = user_destination.strip().lower()
 
    
    routes_db = {
        ("delhi", "manali"): {
            "distance_km": 540,
            "mode": "Overnight Volvo bus / Self-drive",
            "duration": "12-14 hours",
            "local_transport": "Shared taxis, rented scooters within Manali",
        },
        ("delhi", "goa"): {
            "distance_km": 1870,
            "mode": "Flight",
            "duration": "2.5 hours",
            "local_transport": "Rented scooters, prepaid taxis, local buses",
        },
        ("delhi", "jaipur"): {
            "distance_km": 280,
            "mode": "Train / Self-drive",
            "duration": "4-5 hours",
            "local_transport": "Auto-rickshaws, app cabs",
        },
        ("delhi", "rishikesh"): {
            "distance_km": 240,
            "mode": "Train + local taxi / Self-drive",
            "duration": "6-7 hours",
            "local_transport": "Shared autos, rented bikes",
        },
        ("mumbai", "goa"): {
            "distance_km": 590,
            "mode": "Overnight train / Flight",
            "duration": "8-10 hours (train), 1 hour (flight)",
            "local_transport": "Rented scooters, prepaid taxis",
        },
        ("mumbai", "pune"): {
            "distance_km": 150,
            "mode": "Train / Self-drive",
            "duration": "3 hours",
            "local_transport": "App cabs, auto-rickshaws",
        },
        ("bangalore", "goa"): {
            "distance_km": 560,
            "mode": "Overnight bus / Flight",
            "duration": "9-10 hours (bus), 1.5 hours (flight)",
            "local_transport": "Rented scooters, prepaid taxis",
        },
        ("bangalore", "coorg"): {
            "distance_km": 260,
            "mode": "Self-drive / Bus",
            "duration": "5-6 hours",
            "local_transport": "Rented cars, local jeeps for estate visits",
        },
        ("chennai", "pondicherry"): {
            "distance_km": 170,
            "mode": "Self-drive / Bus",
            "duration": "3 hours",
            "local_transport": "Rented bicycles, auto-rickshaws",
        },
        ("kolkata", "darjeeling"): {
            "distance_km": 610,
            "mode": "Overnight train + shared jeep",
            "duration": "10-12 hours",
            "local_transport": "Shared jeeps, toy train for sightseeing",
        },
    }
 
    key = (source_city, destination)
    reverse_key = (destination, source_city)
 
    if key in routes_db:
        route = routes_db[key]
        actual_source, actual_destination = source_city, destination
    elif reverse_key in routes_db:
        # Route exists in reverse direction; distance/mode still apply either way
        route = routes_db[reverse_key]
        actual_source, actual_destination = destination, source_city
    else:
        return {
            "source_city": user_source_city,
            "destination": user_destination,
            "found": False,
            "message": "No predefined route available between these cities.",
        }
 
    return {
        "source_city": actual_source,
        "destination": actual_destination,
        "found": True,
        "distance_km": route["distance_km"],
        "mode": route["mode"],
        "duration": route["duration"],
        "local_transport": route["local_transport"],
    }



if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=9000,   
    )