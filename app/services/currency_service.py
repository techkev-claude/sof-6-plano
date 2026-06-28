import time
from datetime import date
import requests
import structlog

log = structlog.get_logger()
_cache: dict = {}
CACHE_TTL = 24 * 3600
BASE_URL = "https://api.frankfurter.app"


def get_rate(from_currency: str, to_currency: str, on_date: date | None = None) -> float | None:
    if from_currency == to_currency:
        return 1.0

    date_str = str(on_date) if on_date else "latest"
    cache_key = f"{date_str}:{from_currency}:{to_currency}"

    cached = _cache.get(cache_key)
    if cached and (on_date or time.time() - cached["ts"] < CACHE_TTL):
        return cached["rate"]

    try:
        url = f"{BASE_URL}/{date_str}?from={from_currency}&to={to_currency}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"].get(to_currency)
        if rate:
            _cache[cache_key] = {"rate": rate, "ts": time.time()}
        return rate
    except Exception as e:
        log.error("currency_fetch_error", error=str(e))
        return None
