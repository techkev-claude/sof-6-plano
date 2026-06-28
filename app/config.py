import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DB_PATH = os.environ.get("DB_PATH", "/app/data/plano.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 5, "pool_pre_ping": True}
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = os.environ.get("UPLOADS_PATH", "/app/uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB default; overridden from AppConfig
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    BABEL_DEFAULT_LOCALE = "de"
    BABEL_DEFAULT_TIMEZONE = "UTC"
    SCHEDULER_API_ENABLED = False
    RATELIMIT_STORAGE_URL = "memory://"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key"
