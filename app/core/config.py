import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.lower() in {"true", "1", "yes", "on"}


def _expires_to_ms(raw: str) -> int:
    value = raw.strip().lower()
    if value.endswith("ms"):
        return int(value[:-2])
    unit = value[-1]
    amount = int(value[:-1]) if unit.isalpha() else int(value)
    return amount * {"s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}.get(
        unit, 1000
    )


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./isp_manager.db")
        self.jwt_access_secret = os.getenv(
            "JWT_ACCESS_SECRET", "dev-secret-change-me-at-least-32-characters"
        )
        if len(self.jwt_access_secret) < 32:
            raise RuntimeError("JWT_ACCESS_SECRET must be at least 32 characters")

        self.jwt_access_expires_in = os.getenv("JWT_ACCESS_EXPIRES_IN", "15m")
        self.refresh_token_expires_in = os.getenv("REFRESH_TOKEN_EXPIRES_IN", "7d")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "isp-manager-api")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "isp-manager-api")

        self.access_cookie_name = os.getenv("ACCESS_COOKIE_NAME", "access_token")
        self.refresh_cookie_name = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
        self.csrf_cookie_name = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
        self.csrf_header_name = os.getenv("CSRF_HEADER_NAME", "x-csrf-token").lower()

        self.node_env = os.getenv("NODE_ENV", "development")
        self.app_name = os.getenv("APP_NAME", "ISP Manager API")
        self.port = int(os.getenv("PORT", "3000"))
        self.frontend_origins = os.getenv("FRONTEND_ORIGINS", "")
        self.trust_proxy = _bool(os.getenv("TRUST_PROXY"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.swagger_enabled = _bool(os.getenv("SWAGGER_ENABLED"), True)
        self.sentry_dsn = os.getenv("SENTRY_DSN") or None
        self.sentry_enabled = _bool(os.getenv("SENTRY_ENABLED"))
        self.sentry_send_default_pii = _bool(os.getenv("SENTRY_SEND_DEFAULT_PII"))

        same_site = os.getenv("COOKIE_SAMESITE", "strict").lower()
        self.cookie_samesite = (
            same_site if same_site in {"strict", "lax", "none"} else "strict"
        )
        self.cookie_domain = os.getenv("COOKIE_DOMAIN") or None
        self.cookie_secure = _bool(
            os.getenv("COOKIE_SECURE"), default=self.node_env == "production"
        )
        cookie_max_age = os.getenv("COOKIE_MAX_AGE")
        self.cookie_max_age = (
            int(cookie_max_age)
            if cookie_max_age
            else _expires_to_ms(self.jwt_access_expires_in)
        )
        self.refresh_cookie_max_age = _expires_to_ms(self.refresh_token_expires_in)

    @property
    def frontend_origins_list(self) -> list[str]:
        return [
            item.strip() for item in self.frontend_origins.split(",") if item.strip()
        ]

    @property
    def access_expires_seconds(self) -> int:
        return self.cookie_max_age // 1000

    def validate_runtime(self) -> None:
        if self.node_env == "production" and not self.frontend_origins_list:
            raise RuntimeError("FRONTEND_ORIGINS is required in production")
        if self.node_env == "production" and self.database_url.startswith("sqlite"):
            raise RuntimeError("DATABASE_URL must be configured in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
