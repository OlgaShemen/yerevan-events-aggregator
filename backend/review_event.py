import argparse
from datetime import UTC, datetime
import sys

from app.db import get_supabase_client


ALLOWED_FIELDS = {
    "title",
    "description",
    "category",
    "language",
    "date_start",
    "time_start",
    "date_end",
    "time_end",
    "venue_name",
    "address",
    "price_text",
    "source_url",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review and update events.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    publish = subparsers.add_parser("publish", help="Publish a reviewed event.")
    publish.add_argument("--event-id", required=True)

    reject = subparsers.add_parser("reject", help="Reject an event.")
    reject.add_argument("--event-id", required=True)
    reject.add_argument("--reason", default="Rejected during manual review.")

    update = subparsers.add_parser("update", help="Update event fields.")
    update.add_argument("--event-id", required=True)
    update.add_argument(
        "--set",
        action="append",
        default=[],
        help="Field update in field=value format. Can be used multiple times.",
    )

    return parser.parse_args()


def parse_updates(raw_updates: list[str]) -> dict:
    updates = {}

    for raw_update in raw_updates:
        if "=" not in raw_update:
            raise ValueError(f"Invalid update '{raw_update}'. Use field=value.")

        field, value = raw_update.split("=", 1)
        field = field.strip()

        if field not in ALLOWED_FIELDS:
            allowed = ", ".join(sorted(ALLOWED_FIELDS))
            raise ValueError(f"Field '{field}' is not allowed. Allowed fields: {allowed}")

        value = value.strip()
        updates[field] = value if value else None

    if not updates:
        raise ValueError("No updates provided. Use --set field=value.")

    updates["updated_at"] = datetime.now(UTC).isoformat()
    return updates


def get_event(supabase, event_id: str) -> dict:
    response = (
        supabase.table("events")
        .select("id,title,status")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise RuntimeError(f"Event not found: {event_id}")

    return response.data[0]


def write_log(supabase, event_id: str, status: str, message: str, details: dict) -> None:
    supabase.table("processing_logs").insert(
        {
            "event_id": event_id,
            "step": "manual_event_review",
            "status": status,
            "message": message,
            "details": details,
        }
    ).execute()


def publish_event(supabase, event_id: str) -> None:
    event = get_event(supabase, event_id)
    supabase.table("events").update(
        {
            "status": "published",
            "updated_at": datetime.now(UTC).isoformat(),
        }
    ).eq("id", event_id).execute()
    write_log(
        supabase,
        event_id,
        "success",
        "Event was published during manual review.",
        {"previous_status": event["status"]},
    )
    print(f"Published event: {event['title']}")


def reject_event(supabase, event_id: str, reason: str) -> None:
    event = get_event(supabase, event_id)
    supabase.table("events").update(
        {
            "status": "rejected",
            "updated_at": datetime.now(UTC).isoformat(),
        }
    ).eq("id", event_id).execute()
    write_log(
        supabase,
        event_id,
        "success",
        "Event was rejected during manual review.",
        {"previous_status": event["status"], "reason": reason},
    )
    print(f"Rejected event: {event['title']}")


def update_event(supabase, event_id: str, updates: dict) -> None:
    event = get_event(supabase, event_id)
    supabase.table("events").update(updates).eq("id", event_id).execute()
    write_log(
        supabase,
        event_id,
        "success",
        "Event was updated during manual review.",
        {"previous_status": event["status"], "updates": updates},
    )
    print(f"Updated event: {event['title']}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()

    if args.command == "publish":
        publish_event(supabase, args.event_id)
    elif args.command == "reject":
        reject_event(supabase, args.event_id, args.reason)
    elif args.command == "update":
        update_event(supabase, args.event_id, parse_updates(args.set))


if __name__ == "__main__":
    main()
