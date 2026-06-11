"""Weather module — OpenWeatherMap integration"""

import requests
from typing import Optional, Dict, Any


def get_weather(api_key: Optional[str], city: str = "Vasind", country: str = "IN") -> Optional[Dict[str, Any]]:
    """
    Fetch current weather from OpenWeatherMap.
    Free key: https://openweathermap.org/api
    """
    if not api_key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": f"{city},{country}", "appid": api_key, "units": "metric"}
        r = requests.get(url, params=params, timeout=5)
        if r.ok:
            data = r.json()
            return {
                "temp":        round(data["main"]["temp"]),
                "feels_like":  round(data["main"]["feels_like"]),
                "humidity":    data["main"]["humidity"],
                "description": data["weather"][0]["description"].capitalize(),
                "wind_speed":  data["wind"]["speed"],
                "city":        data["name"],
            }
    except Exception as e:
        print(f"  ⚠ Weather: {e}")
    return None
