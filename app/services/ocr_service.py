import base64
import structlog
from app.services.ai_client import get_ai_client

log = structlog.get_logger()


def extract_ticket_data(file_bytes: bytes, mimetype: str) -> dict:
    client, provider = get_ai_client()
    if not client or provider != "anthropic":
        return {}
    try:
        b64 = base64.b64encode(file_bytes).decode()
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": mimetype, "data": b64}},
                    {"type": "text", "text": "Extrahiere Datum, Uhrzeit, Von, Nach, Buchungsnummer aus diesem Ticket als JSON."}
                ]
            }]
        )
        import json
        text = resp.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        log.error("ocr_error", error=str(e))
    return {}
