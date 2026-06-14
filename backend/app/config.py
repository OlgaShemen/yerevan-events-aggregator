from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    telegram_api_id: int | None = None
    telegram_api_hash: str | None = None
    telegram_session_name: str = "yerevan_events"
    telegram_channels: list[str] | None = None
    telegram_fetch_limit: int = 20


def get_settings() -> Settings:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    telegram_api_id_raw = os.getenv("TELEGRAM_API_ID")
    telegram_api_hash = os.getenv("TELEGRAM_API_HASH")
    telegram_session_name = os.getenv("TELEGRAM_SESSION_NAME", "yerevan_events")
    telegram_channels_raw = os.getenv("TELEGRAM_CHANNELS", "")
    telegram_fetch_limit_raw = os.getenv("TELEGRAM_FETCH_LIMIT", "20")

    telegram_api_id = int(telegram_api_id_raw) if telegram_api_id_raw else None
    telegram_channels = [
        channel.strip()
        for channel in telegram_channels_raw.split(",")
        if channel.strip()
    ]
    telegram_fetch_limit = int(telegram_fetch_limit_raw)

    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        missing_values = ", ".join(missing)
        raise RuntimeError(
            f"Missing environment variables: {missing_values}. "
            "Create backend/.env from backend/.env.example and fill in Supabase values."
        )

    return Settings(
        supabase_url=supabase_url,
        supabase_service_role_key=supabase_service_role_key,
        supabase_anon_key=supabase_anon_key,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        telegram_api_id=telegram_api_id,
        telegram_api_hash=telegram_api_hash,
        telegram_session_name=telegram_session_name,
        telegram_channels=telegram_channels,
        telegram_fetch_limit=telegram_fetch_limit,
    )
