import structlog
from app.models import AppConfig

log = structlog.get_logger()


def get_ai_client():
    provider = AppConfig.get("ai_provider", "anthropic")
    if provider == "anthropic":
        key = AppConfig.get("anthropic_api_key")
        if not key:
            return None, None
        try:
            import anthropic
            return anthropic.Anthropic(api_key=key), "anthropic"
        except Exception as e:
            log.error("anthropic_init_error", error=str(e))
            return None, None
    elif provider == "openai":
        key = AppConfig.get("openai_api_key")
        if not key:
            return None, None
        try:
            import openai
            return openai.OpenAI(api_key=key), "openai"
        except Exception as e:
            log.error("openai_init_error", error=str(e))
            return None, None
    return None, None


def is_ai_available() -> bool:
    client, _ = get_ai_client()
    return client is not None


def chat_completion(messages: list, system: str = "", model: str | None = None) -> str | None:
    client, provider = get_ai_client()
    if not client:
        return None
    try:
        if provider == "anthropic":
            m = model or "claude-sonnet-4-6"
            resp = client.messages.create(
                model=m,
                max_tokens=4096,
                system=system or "Du bist ein hilfreicher Reiseplaner-Assistent.",
                messages=messages,
            )
            return resp.content[0].text
        elif provider == "openai":
            m = model or "gpt-4o-mini"
            all_messages = []
            if system:
                all_messages.append({"role": "system", "content": system})
            all_messages.extend(messages)
            resp = client.chat.completions.create(model=m, messages=all_messages)
            return resp.choices[0].message.content
    except Exception as e:
        log.error("ai_completion_error", error=str(e))
        return None
