from datetime import UTC

from telethon import TelegramClient

from app.config import get_settings
from app.db import get_supabase_client


def normalize_channel_username(channel: str) -> str:
    channel = channel.strip()

    if channel.startswith("https://t.me/"):
        channel = channel.removeprefix("https://t.me/")

    return channel.removeprefix("@").strip("/")


def telegram_channel_url(username: str) -> str:
    return f"https://t.me/{username}"


def require_telegram_settings():
    settings = get_settings()

    missing = []
    if not settings.telegram_api_id:
        missing.append("TELEGRAM_API_ID")
    if not settings.telegram_api_hash:
        missing.append("TELEGRAM_API_HASH")
    if not settings.telegram_channels:
        missing.append("TELEGRAM_CHANNELS")

    if missing:
        raise RuntimeError(
            "Missing Telegram settings: "
            + ", ".join(missing)
            + ". Add them to backend/.env before running Telegram ingestion."
        )

    return settings


def get_or_create_telegram_source(supabase, username: str) -> dict:
    existing = (
        supabase.table("sources")
        .select("id,last_seen_external_id")
        .eq("type", "telegram")
        .eq("telegram_username", username)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    created = (
        supabase.table("sources")
        .insert(
            {
                "name": f"Telegram @{username}",
                "type": "telegram",
                "url": telegram_channel_url(username),
                "telegram_username": username,
                "notes": "Telegram source created by ingest_telegram_posts.py.",
            }
        )
        .execute()
    )

    return created.data[0]


def message_to_raw_payload(username: str, message) -> dict:
    message_date = message.date
    if message_date and message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=UTC)

    return {
        "telegram_channel": username,
        "telegram_message_id": message.id,
        "telegram_date": message_date.isoformat() if message_date else None,
        "telegram_url": f"{telegram_channel_url(username)}/{message.id}",
    }


def save_raw_message(supabase, source: dict, username: str, message) -> bool:
    raw_text = (message.message or "").strip()
    if not raw_text:
        return False

    external_id = str(message.id)
    existing = (
        supabase.table("raw_items")
        .select("id")
        .eq("source_id", source["id"])
        .eq("external_id", external_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        return False

    payload = message_to_raw_payload(username, message)
    supabase.table("raw_items").insert(
        {
            "source_id": source["id"],
            "external_id": external_id,
            "source_url": payload["telegram_url"],
            "raw_text": raw_text,
            "raw_payload": payload,
            "language_hint": None,
            "status": "new",
            "collected_at": payload["telegram_date"],
        }
    ).execute()

    return True


async def ingest_telegram_posts() -> None:
    settings = require_telegram_settings()
    supabase = get_supabase_client()

    client = TelegramClient(
        settings.telegram_session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )

    total_saved = 0

    async with client:
        for channel in settings.telegram_channels or []:
            username = normalize_channel_username(channel)
            source = get_or_create_telegram_source(supabase, username)

            min_id = 0
            if source.get("last_seen_external_id"):
                min_id = int(source["last_seen_external_id"])

            saved_for_channel = 0
            max_seen_id = min_id

            async for message in client.iter_messages(
                username,
                limit=settings.telegram_fetch_limit,
                min_id=min_id,
            ):
                max_seen_id = max(max_seen_id, message.id)
                if save_raw_message(supabase, source, username, message):
                    saved_for_channel += 1

            if max_seen_id > min_id:
                supabase.table("sources").update(
                    {"last_seen_external_id": str(max_seen_id)}
                ).eq("id", source["id"]).execute()

            supabase.table("processing_logs").insert(
                {
                    "source_id": source["id"],
                    "step": "telegram_ingestion",
                    "status": "success",
                    "message": f"Saved {saved_for_channel} new Telegram posts.",
                    "details": {
                        "channel": username,
                        "fetch_limit": settings.telegram_fetch_limit,
                        "last_seen_external_id": str(max_seen_id),
                    },
                }
            ).execute()

            print(f"@{username}: saved {saved_for_channel} new posts")
            total_saved += saved_for_channel

    print(f"Telegram ingestion finished. Total saved: {total_saved}")
