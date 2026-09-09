from datetime import UTC
import re
from urllib.parse import urlsplit

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


SOURCE_URL_PATTERN = re.compile(
    r"(?im)^\s*источник\s*:\s*(https?://\S+)"
)


def extract_explicit_source_url(raw_text: str | None) -> str | None:
    match = SOURCE_URL_PATTERN.search(raw_text or "")
    if not match:
        return None

    url = match.group(1).rstrip(".,;!?)]}>")
    parsed = urlsplit(url)
    if not parsed.hostname or parsed.username or parsed.password:
        return None
    if parsed.hostname.lower() in {"t.me", "telegram.me", "www.t.me"}:
        path = parsed.path.lstrip("/")
        if path.startswith(("c/", "+", "joinchat/")):
            return None
    return url


def forwarded_public_url(message) -> str | None:
    forward = getattr(message, "forward", None)
    chat = getattr(forward, "chat", None)
    username = getattr(chat, "username", None)
    channel_post = getattr(forward, "channel_post", None)

    if not username or not channel_post:
        return None

    return f"{telegram_channel_url(username)}/{channel_post}"


def private_message_source_url(message) -> str | None:
    raw_text = (getattr(message, "message", None) or "").strip()
    return extract_explicit_source_url(raw_text) or forwarded_public_url(message)


def require_telegram_settings():
    settings = get_settings()

    missing = []
    if not settings.telegram_api_id:
        missing.append("TELEGRAM_API_ID")
    if not settings.telegram_api_hash:
        missing.append("TELEGRAM_API_HASH")
    if not settings.telegram_channels and not settings.telegram_private_channel_ids:
        missing.append("TELEGRAM_CHANNELS")

    if missing:
        raise RuntimeError(
            "Missing Telegram settings: "
            + ", ".join(missing)
            + ". Add them to backend/.env before running Telegram ingestion."
        )

    return settings


def get_or_create_telegram_source(
    supabase,
    source_key: str,
    source_name: str,
    public_url: str | None,
) -> dict:
    existing = (
        supabase.table("sources")
        .select("id,last_seen_external_id")
        .eq("type", "telegram")
        .eq("telegram_username", source_key)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    created = (
        supabase.table("sources")
        .insert(
            {
                "name": source_name,
                "type": "telegram",
                "url": public_url,
                "telegram_username": source_key,
                "notes": "Telegram source created by ingest_telegram_posts.py.",
            }
        )
        .execute()
    )

    return created.data[0]


def message_to_raw_payload(
    channel_label: str,
    message,
    source_url: str | None,
    private_channel_id: int | None = None,
) -> dict:
    message_date = message.date
    if private_channel_id is not None:
        # Relative dates in forwarded text belong to the original publication.
        forward = getattr(message, "fwd_from", None)
        message_date = getattr(forward, "date", None) or message_date
    if message_date and message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=UTC)

    return {
        "telegram_channel": channel_label,
        "telegram_channel_id": private_channel_id,
        "telegram_message_id": message.id,
        "telegram_date": message_date.isoformat() if message_date else None,
        "telegram_url": source_url,
        "manual_submission": private_channel_id is not None,
    }


def save_raw_message(
    supabase,
    source: dict,
    channel_label: str,
    message,
    source_url: str | None,
    private_channel_id: int | None = None,
) -> bool:
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

    payload = message_to_raw_payload(
        channel_label,
        message,
        source_url,
        private_channel_id,
    )
    supabase.table("raw_items").insert(
        {
            "source_id": source["id"],
            "external_id": external_id,
            "source_url": source_url,
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
            public_url = telegram_channel_url(username)
            source = get_or_create_telegram_source(
                supabase,
                source_key=username,
                source_name=f"Telegram @{username}",
                public_url=public_url,
            )

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
                source_url = f"{public_url}/{message.id}"
                if save_raw_message(
                    supabase,
                    source,
                    username,
                    message,
                    source_url,
                ):
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

        private_channel_ids = set(settings.telegram_private_channel_ids or [])
        if private_channel_ids:
            dialogs = await client.get_dialogs()
            private_dialogs = {
                dialog.entity.id: dialog
                for dialog in dialogs
                if dialog.is_channel and getattr(dialog.entity, "id", None) in private_channel_ids
            }

            missing_channel_ids = private_channel_ids - private_dialogs.keys()
            if missing_channel_ids:
                missing_text = ", ".join(str(channel_id) for channel_id in sorted(missing_channel_ids))
                raise RuntimeError(
                    f"Telegram private channels not found for the authorized account: {missing_text}"
                )

            for channel_id in settings.telegram_private_channel_ids or []:
                dialog = private_dialogs[channel_id]
                channel_label = dialog.name or f"private-{channel_id}"
                source_key = f"private:{channel_id}"
                source = get_or_create_telegram_source(
                    supabase,
                    source_key=source_key,
                    source_name=f"Telegram private channel: {channel_label}",
                    public_url=None,
                )

                min_id = 0
                if source.get("last_seen_external_id"):
                    min_id = int(source["last_seen_external_id"])

                saved_for_channel = 0
                max_seen_id = min_id

                async for message in client.iter_messages(
                    dialog.entity,
                    limit=settings.telegram_fetch_limit,
                    min_id=min_id,
                ):
                    max_seen_id = max(max_seen_id, message.id)
                    source_url = private_message_source_url(message)
                    if save_raw_message(
                        supabase,
                        source,
                        channel_label,
                        message,
                        source_url,
                        private_channel_id=channel_id,
                    ):
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
                            "channel": channel_label,
                            "private_channel_id": str(channel_id),
                            "fetch_limit": settings.telegram_fetch_limit,
                            "last_seen_external_id": str(max_seen_id),
                        },
                    }
                ).execute()

                print(f"{channel_label}: saved {saved_for_channel} new posts")
                total_saved += saved_for_channel

    print(f"Telegram ingestion finished. Total saved: {total_saved}")
