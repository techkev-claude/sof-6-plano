import structlog
from cryptography.fernet import Fernet, InvalidToken
from app.models import AppConfig

log = structlog.get_logger()


def get_fernet() -> Fernet | None:
    key = AppConfig.get("fernet_key")
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception:
        return None


def encrypt_file(data: bytes) -> bytes | None:
    f = get_fernet()
    if not f:
        return None
    return f.encrypt(data)


def decrypt_file(data: bytes) -> bytes | None:
    f = get_fernet()
    if not f:
        return None
    try:
        return f.decrypt(data)
    except InvalidToken:
        log.error("fernet_decryption_failed")
        return None
