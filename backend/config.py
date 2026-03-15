import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
# Always try to load the project-root .env (works even when running from /backend)
load_dotenv(_ENV_PATH, override=False)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
    debug: bool = _env_flag("DEBUG", False)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key2: str = os.getenv("GEMINI_API_KEY2", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    pdf_path: str = os.getenv("PDF_PATH", "./backend/data/portfolio.pdf")
    google_service_account_json: str = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON", "./backend/credentials/service_account.json"
    )
    google_sheets_spreadsheet_id: str = os.getenv(
        "GOOGLE_SHEETS_SPREADSHEET_ID", ""
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500")
    cors_allow_origins_raw: str = os.getenv("CORS_ALLOW_ORIGINS", "")
    expose_debug_otps: bool = _env_flag("EXPOSE_DEBUG_OTPS", app_env != "production")
    otp_ttl_minutes: int = int(os.getenv("OTP_TTL_MINUTES", "10"))
    auth_rate_limit_window_seconds: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "900"))
    auth_request_otp_limit: int = int(os.getenv("AUTH_REQUEST_OTP_LIMIT", "5"))
    auth_verify_otp_limit: int = int(os.getenv("AUTH_VERIFY_OTP_LIMIT", "10"))
    admin_login_limit: int = int(os.getenv("ADMIN_LOGIN_LIMIT", "5"))
    # Optional SMTP configuration for sending OTP emails (e.g. via Gmail)
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    google_calendar_booking_url: str = os.getenv(
        "GOOGLE_CALENDAR_BOOKING_URL", "https://calendar.google.com/"
    )
    google_calendar_id: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    google_calendar_timezone: str = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Kolkata")
    google_calendar_impersonate_user: str = os.getenv("GOOGLE_CALENDAR_IMPERSONATE_USER", "")
    default_meet_link: str = os.getenv(
        "DEFAULT_MEET_LINK", "https://meet.google.com/xjo-xdyr-gfw"
    )
    imagekit_private_key: str = os.getenv("IMAGEKIT_PRIVATE_KEY", "")
    imagekit_public_key: str = os.getenv("IMAGEKIT_PUBLIC_KEY", "")
    imagekit_url: str = os.getenv("IMAGEKIT_URL", "")
    imagekit_resume_folder: str = os.getenv("IMAGEKIT_RESUME_FOLDER", "/resumes")
    uploaded_resume_dir: str = os.getenv("UPLOADED_RESUME_DIR", "./backend/data/uploads")
    public_backend_url: str = os.getenv("PUBLIC_BACKEND_URL", "")
    vobiz_auth_id: str = os.getenv("VOBIZ_AUTH_ID", "")
    vobiz_auth_token: str = os.getenv("VOBIZ_AUTH_TOKEN", "")
    vobiz_webhook_secret: str = os.getenv("VOBIZ_WEBHOOK_SECRET", "")
    vobiz_call_delay_seconds: int = int(os.getenv("VOBIZ_CALL_DELAY_SECONDS", "30"))
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")
    admin_email: str = os.getenv("ADMIN_EMAIL", "")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_agent_resume",
    )

    @property
    def cors_allow_origins(self) -> list[str]:
        raw_value = self.cors_allow_origins_raw or self.frontend_origin
        origins = [item.strip().rstrip("/") for item in raw_value.split(",") if item.strip()]
        return origins

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def resolve_project_path(path_value: str) -> Path:
    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return candidate
    return (_PROJECT_ROOT / candidate).resolve()
