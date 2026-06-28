import time
import requests
import structlog
from app.extensions import db
from app.models import Trip, AppConfig

log = structlog.get_logger()
_cache: dict = {}
CACHE_TTL = 6 * 3600


def get_trip_weather(trip_id: int, api_key: str) -> list:
    trip = db.session.get(Trip, trip_id)
    if not trip or not trip.destination:
        return []

    cache_key = f"{trip_id}:{trip.destination}"
    cached = _cache.get(cache_key)
    if cached and time.time() - cached["ts"] < CACHE_TTL:
        return cached["data"]

    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={trip.destination}&limit=1&appid={api_key}"
        geo = requests.get(geo_url, timeout=5).json()
        if not geo:
            return []
        lat, lon = geo[0]["lat"], geo[0]["lon"]
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}"
            f"&appid={api_key}&units=metric&lang=de"
        )
        data = requests.get(forecast_url, timeout=5).json()
        result = _parse_forecast(data)
        _cache[cache_key] = {"ts": time.time(), "data": result}
        return result
    except Exception as e:
        log.error("weather_client_error", error=str(e))
        return []


def _parse_forecast(data: dict) -> list:
    daily: dict = {}
    for item in data.get("list", []):
        date = item["dt_txt"].split(" ")[0]
        if date not in daily:
            daily[date] = {"temps": [], "icons": [], "rain": False}
        daily[date]["temps"].append(item["main"]["temp"])
        daily[date]["icons"].append(item["weather"][0]["icon"])
        if item.get("rain"):
            daily[date]["rain"] = True

    result = []
    for date, info in daily.items():
        result.append({
            "date": date,
            "icon": info["icons"][len(info["icons"]) // 2],
            "temp_min": round(min(info["temps"]), 1),
            "temp_max": round(max(info["temps"]), 1),
            "rain": info["rain"],
        })
    return result
