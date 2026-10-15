import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _flag(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'cartopedia.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookies de session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _flag("COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # Captcha Cap (auto-hébergé). Désactivé tant que les 3 valeurs ne sont pas définies.
    CAP_ENDPOINT = os.environ.get("CAP_ENDPOINT", "").rstrip("/")
    CAP_SITE_KEY = os.environ.get("CAP_SITE_KEY", "")
    CAP_SECRET = os.environ.get("CAP_SECRET", "")
    CAP_WIDGET_URL = os.environ.get(
        "CAP_WIDGET_URL", "https://cdn.jsdelivr.net/npm/cap-widget@0.1.58"
    )

    # Limites de débit
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # Règles du jeu
    PACK_SIZE = 4
    FREE_PACK_INTERVAL = timedelta(hours=8)
    PAID_PACK_PRICE = 80
    START_COINS = 240
    ALBUM_PAGE_SIZE = 24
    CATALOG_CACHE_SECONDS = 600

    WTF_CSRF_TIME_LIMIT = None


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    CAP_ENDPOINT = ""
