import requests
import structlog
from app.models import AppConfig

log = structlog.get_logger()


def get_travel_time(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float,
                    mode: str = "transit") -> int | None:
    api_key = AppConfig.get("google_maps_api_key")
    if not api_key:
        return None
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={origin_lat},{origin_lng}&destination={dest_lat},{dest_lng}"
            f"&mode={mode}&key={api_key}"
        )
        data = requests.get(url, timeout=5).json()
        if data.get("routes"):
            seconds = data["routes"][0]["legs"][0]["duration"]["value"]
            return seconds // 60
    except Exception as e:
        log.error("maps_client_error", error=str(e))
    return None
