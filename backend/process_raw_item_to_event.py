import re
from datetime import UTC, datetime

from app.category_normalization import normalize_category
from app.date_validation import clear_inferred_weekday_dates
from app.db import get_supabase_client
from app.deduplication import duplicate_reason
from app.event_extraction import extract_event_from_text
from app.event_filtering import is_non_event_collection, should_ignore_extracted_event


PUBLISH_CONFIDENCE_THRESHOLD = 0.75


def get_next_raw_item(supabase) -> dict | None:
    response = (
        supabase.table("raw_items")
        .select("id,source_id,source_url,raw_text,status")
        .eq("status", "new")
        .order("collected_at")
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = value.lower().strip()
    normalized = re.sub(r"[^\w]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def build_normalized_key(event: dict) -> str:
    title = normalize_text(event.get("title"))
    date_start = event.get("date_start") or "unknown-date"
    venue_name = normalize_text(event.get("venue_name"))
    return f"{date_start}:{venue_name}:{title}"


def get_or_create_venue(supabase, event: dict) -> str | None:
    venue_name = event.get("venue_name")
    address = event.get("address")

    if not venue_name:
        return None

    existing = (
        supabase.table("venues")
        .select("id")
        .eq("name", venue_name)
        .eq("address", address)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]["id"]

    created = (
        supabase.table("venues")
        .insert(
            {
                "name": venue_name,
                "address": address,
                "city": "Yerevan",
            }
        )
        .execute()
    )

    return created.data[0]["id"]


def choose_event_status(event: dict, duplicate_candidate: dict | None = None) -> str:
    if duplicate_candidate:
        return "needs_review"

    has_date = bool(event.get("date_start"))
    has_place = bool(event.get("venue_name") or event.get("address"))
    confidence = float(event.get("confidence_score") or 0)

    if has_date and has_place and confidence >= PUBLISH_CONFIDENCE_THRESHOLD:
        return "published"

    return "needs_review"


def serialize_duplicate_candidate(candidate) -> dict:
    duplicate = candidate.event_b
    return {
        "event_id": duplicate.get("id"),
        "title": duplicate.get("title"),
        "date_start": duplicate.get("date_start"),
        "time_start": duplicate.get("time_start"),
        "venue_name": duplicate.get("venue_name"),
        "source_url": duplicate.get("source_url"),
        "status": duplicate.get("status"),
        "score": round(candidate.score, 3),
        "title_similarity": round(candidate.title_similarity, 3),
        "venue_similarity": round(candidate.venue_similarity, 3),
        "reason": candidate.reason,
    }


def find_existing_duplicate(supabase, event: dict) -> dict | None:
    date_start = event.get("date_start")
    if not date_start:
        return None

    existing_events = (
        supabase.table("events")
        .select("id,title,date_start,time_start,venue_name,status,source_url")
        .eq("date_start", date_start)
        .in_("status", ["published", "needs_review"])
        .limit(100)
        .execute()
        .data
        or []
    )

    candidates = [
        duplicate_reason(event, existing_event)
        for existing_event in existing_events
    ]
    candidates = [candidate for candidate in candidates if candidate]

    if not candidates:
        return None

    best_candidate = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)[0]
    return serialize_duplicate_candidate(best_candidate)


def save_event(supabase, raw_item: dict, extracted_event: dict) -> dict:
    if not extracted_event.get("title"):
        raise ValueError("Cannot save event without title.")

    extracted_event["category"] = normalize_category(
        extracted_event,
        raw_item.get("raw_text"),
    )
    extracted_event = clear_inferred_weekday_dates(
        extracted_event,
        raw_item.get("raw_text"),
    )
    duplicate_candidate = find_existing_duplicate(supabase, extracted_event)
    if duplicate_candidate:
        extracted_event["duplicate_candidate"] = duplicate_candidate

    venue_id = get_or_create_venue(supabase, extracted_event)
    status = choose_event_status(extracted_event, duplicate_candidate)

    event_payload = {
        "title": extracted_event["title"],
        "description": extracted_event.get("description"),
        "original_text": raw_item.get("raw_text"),
        "category": extracted_event.get("category", "other"),
        "language": extracted_event.get("language", "unknown"),
        "date_start": extracted_event.get("date_start"),
        "time_start": extracted_event.get("time_start"),
        "date_end": extracted_event.get("date_end"),
        "time_end": extracted_event.get("time_end"),
        "venue_id": venue_id,
        "venue_name": extracted_event.get("venue_name"),
        "address": extracted_event.get("address"),
        "price_text": extracted_event.get("price_text"),
        "source_url": extracted_event.get("source_url") or raw_item.get("source_url"),
        "status": status,
        "confidence_score": extracted_event.get("confidence_score") or 0,
        "normalized_key": build_normalized_key(extracted_event),
        "ai_payload": extracted_event,
    }

    created_event = supabase.table("events").insert(event_payload).execute().data[0]

    supabase.table("event_sources").insert(
        {
            "event_id": created_event["id"],
            "raw_item_id": raw_item["id"],
            "source_id": raw_item["source_id"],
            "source_url": raw_item.get("source_url"),
            "is_primary": True,
        }
    ).execute()

    return created_event


def update_raw_item_status(supabase, raw_item_id: str, status: str, error_message: str | None = None) -> None:
    payload = {
        "status": status,
        "error_message": error_message,
    }

    if status in ["processed", "ignored"]:
        payload["processed_at"] = datetime.now(UTC).isoformat()

    supabase.table("raw_items").update(payload).eq("id", raw_item_id).execute()


def write_log(
    supabase,
    raw_item: dict,
    status: str,
    message: str,
    details: dict,
    event_id: str | None = None,
) -> None:
    supabase.table("processing_logs").insert(
        {
            "source_id": raw_item["source_id"],
            "raw_item_id": raw_item["id"],
            "event_id": event_id,
            "step": "save_normalized_event",
            "status": status,
            "message": message,
            "details": details,
        }
    ).execute()


def get_usable_extracted_events(extraction_result: dict) -> list[dict]:
    if "events" in extraction_result:
        return [
            event
            for event in extraction_result.get("events") or []
            if event.get("title")
        ]

    if extraction_result.get("is_event", True) and extraction_result.get("title"):
        return [extraction_result]

    return []


def process_raw_item(supabase, raw_item: dict) -> dict:
    if is_non_event_collection(raw_item.get("raw_text")):
        update_raw_item_status(
            supabase,
            raw_item["id"],
            "ignored",
            "Ignored because this is a summer camps/schools collection, not event listings.",
        )
        write_log(
            supabase=supabase,
            raw_item=raw_item,
            status="ignored",
            message="Raw item is a non-event summer camps/schools collection.",
            details={"source_url": raw_item.get("source_url")},
        )
        return {
            "raw_item_id": raw_item["id"],
            "action": "ignored",
            "event_id": None,
            "event_ids": [],
            "event_status": None,
            "event_statuses": [],
            "saved_count": 0,
        }

    extraction_result = extract_event_from_text(
        raw_text=raw_item["raw_text"],
        source_url=raw_item.get("source_url"),
    )
    extracted_events = get_usable_extracted_events(extraction_result)
    extracted_events = [
        event
        for event in extracted_events
        if not should_ignore_extracted_event(event, raw_item.get("raw_text"))
    ]

    if not extraction_result.get("is_event", True) or not extracted_events:
        rejection_reason = extraction_result.get("rejection_reason")
        if not extracted_events:
            rejection_reason = rejection_reason or "AI classified this as an event but did not return a title."

        update_raw_item_status(
            supabase,
            raw_item["id"],
            "ignored",
            rejection_reason,
        )
        write_log(
            supabase=supabase,
            raw_item=raw_item,
            status="ignored",
            message="Raw item is not a usable event announcement.",
            details={"extraction_result": extraction_result},
        )
        return {
            "raw_item_id": raw_item["id"],
            "action": "ignored",
            "event_id": None,
            "event_ids": [],
            "event_status": None,
            "event_statuses": [],
            "saved_count": 0,
        }

    saved_events = [
        save_event(supabase, raw_item, extracted_event)
        for extracted_event in extracted_events
    ]
    update_raw_item_status(supabase, raw_item["id"], "processed")
    write_log(
        supabase=supabase,
        raw_item=raw_item,
        event_id=saved_events[0]["id"],
        status="success",
        message="Normalized events were saved.",
        details={
            "saved_count": len(saved_events),
            "event_statuses": [event["status"] for event in saved_events],
        },
    )

    return {
        "raw_item_id": raw_item["id"],
        "action": "saved",
        "event_id": saved_events[0]["id"],
        "event_ids": [event["id"] for event in saved_events],
        "event_status": saved_events[0]["status"] if len(saved_events) == 1 else "multiple",
        "event_statuses": [event["status"] for event in saved_events],
        "saved_count": len(saved_events),
    }


def main() -> None:
    supabase = get_supabase_client()
    raw_item = get_next_raw_item(supabase)

    if not raw_item:
        print("No raw items with status=new found.")
        return

    try:
        result = process_raw_item(supabase, raw_item)
    except Exception as error:
        update_raw_item_status(supabase, raw_item["id"], "failed", str(error))
        write_log(
            supabase=supabase,
            raw_item=raw_item,
            status="failed",
            message="Failed to save normalized event.",
            details={"error": str(error)},
        )
        raise

    print("Raw item was converted to event.")
    print(f"Raw item ID: {raw_item['id']}")
    print(f"Action: {result['action']}")
    print(f"Event IDs: {', '.join(result['event_ids']) if result['event_ids'] else None}")
    print(f"Event statuses: {', '.join(result['event_statuses']) if result['event_statuses'] else None}")


if __name__ == "__main__":
    main()
