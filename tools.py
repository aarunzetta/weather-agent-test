import requests

def get_weather(city: str) -> dict:
    """
    Fetches current weather + rain probability for a city.
    Uses two free APIs:
      1. Open-Meteo Geocoding → turns city name into lat/lon
      2. Open-Meteo Forecast  → gets weather data for that lat/lon
    No API key needed!
    """

    # ── Step 1: Get coordinates from city name ──────────────
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}

    geo_response = requests.get(geo_url, params=geo_params)
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        return {"error": f"City '{city}' not found. Try a nearby major city."}

    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    location_name = location["name"]
    country = location.get("country", "")

    # ── Step 2: Get weather forecast for those coordinates ──
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ],
        "hourly": "precipitation_probability",
        "forecast_days": 1,          # today only
        "timezone": "auto",          # auto-detect timezone from coordinates
    }

    weather_response = requests.get(weather_url, params=weather_params)
    weather_data = weather_response.json()

    # ── Step 3: Pull out the numbers we care about ──────────
    current = weather_data["current"]
    hourly  = weather_data["hourly"]

    # Average rain probability over the next 6 hours
    rain_probs = hourly["precipitation_probability"][:6]
    avg_rain_chance = round(sum(rain_probs) / len(rain_probs), 1)
    max_rain_chance = max(rain_probs)

    # Decode WMO weather code into a readable description
    weather_code = current["weather_code"]
    description = decode_weather_code(weather_code)

    return {
        "location": f"{location_name}, {country}",
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current["temperature_2m"],
        "humidity_percent": current["relative_humidity_2m"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "current_condition": description,
        "current_precipitation_mm": current["precipitation"],
        "rain_chance_next_6h_avg": avg_rain_chance,
        "rain_chance_next_6h_max": max_rain_chance,
        "hourly_rain_chances": rain_probs,
    }


def decode_weather_code(code: int) -> str:
    """Converts WMO weather codes into plain English."""
    codes = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Icy fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail",
    }
    return codes.get(code, f"Unknown condition (code {code})")
