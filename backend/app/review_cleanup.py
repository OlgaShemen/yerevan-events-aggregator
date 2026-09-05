from datetime import UTC, datetime, timedelta


DEFAULT_STALE_REVIEW_DAYS = 14


def should_archive_stale_undated_event(
    event: dict,
    *,
    now: datetime | None = None,
    stale_days: int = DEFAULT_STALE_REVIEW_DAYS,
) -> bool:
    if event.get("status") != "needs_review":
        return False
    if event.get("date_start") or event.get("date_end"):
        return False

    created_at = event.get("created_at")
    if not isinstance(created_at, str):
        return False

    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if created.tzinfo is None:
        return False

    current_time = now or datetime.now(UTC)
    return created <= current_time - timedelta(days=stale_days)


def archive_stale_undated_review_events(
    supabase,
    *,
    now: datetime | None = None,
    stale_days: int = DEFAULT_STALE_REVIEW_DAYS,
) -> int:
    current_time = now or datetime.now(UTC)
    cutoff = current_time - timedelta(days=stale_days)
    events = (
        supabase.table("events")
        .select("id,title,status,date_start,date_end,created_at")
        .eq("status", "needs_review")
        .is_("date_start", "null")
        .is_("date_end", "null")
        .lte("created_at", cutoff.isoformat())
        .execute()
        .data
        or []
    )
    stale_events = [
        event
        for event in events
        if should_archive_stale_undated_event(
            event,
            now=current_time,
            stale_days=stale_days,
        )
    ]
    if not stale_events:
        return 0

    event_ids = [event["id"] for event in stale_events]
    (
        supabase.table("events")
        .update(
            {
                "status": "archived",
                "updated_at": current_time.isoformat(),
            }
        )
        .in_("id", event_ids)
        .execute()
    )
    supabase.table("processing_logs").insert(
        [
            {
                "event_id": event["id"],
                "step": "archive_stale_review_event",
                "status": "success",
                "message": "Archived stale undated review event.",
                "details": {
                    "reason": "undated_review_older_than_limit",
                    "stale_days": stale_days,
                    "created_at": event["created_at"],
                },
            }
            for event in stale_events
        ]
    ).execute()
    return len(stale_events)
