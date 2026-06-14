from datetime import UTC, datetime

from app.db import get_supabase_client


SOURCE_NAME = "Manual test source"
SOURCE_URL = "manual://test-source"
RAW_EXTERNAL_ID = "manual-test-001"

RAW_TEXT = """
Jazz Night in Yerevan

Date: 2026-06-15
Time: 20:00
Venue: Mezzo Club
Address: 28 Isahakyan Street, Yerevan
Price: 5000 AMD

Live jazz evening with local musicians.
""".strip()


def get_or_create_manual_source(supabase) -> str:
    existing = (
        supabase.table("sources")
        .select("id")
        .eq("type", "manual")
        .eq("url", SOURCE_URL)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]["id"]

    created = (
        supabase.table("sources")
        .insert(
            {
                "name": SOURCE_NAME,
                "type": "manual",
                "url": SOURCE_URL,
                "notes": "Test source for manual raw item ingestion.",
            }
        )
        .execute()
    )

    return created.data[0]["id"]


def upsert_raw_item(supabase, source_id: str) -> dict:
    now = datetime.now(UTC).isoformat()

    existing = (
        supabase.table("raw_items")
        .select("id")
        .eq("source_id", source_id)
        .eq("external_id", RAW_EXTERNAL_ID)
        .limit(1)
        .execute()
    )

    payload = {
        "source_id": source_id,
        "external_id": RAW_EXTERNAL_ID,
        "source_url": SOURCE_URL,
        "raw_text": RAW_TEXT,
        "raw_payload": {
            "input_method": "manual_test",
            "created_by": "ingest_manual_raw_item.py",
        },
        "language_hint": "en",
        "status": "new",
        "collected_at": now,
        "processed_at": None,
        "error_message": None,
    }

    if existing.data:
        raw_item_id = existing.data[0]["id"]
        updated = (
            supabase.table("raw_items")
            .update(payload)
            .eq("id", raw_item_id)
            .execute()
        )
        return updated.data[0]

    created = supabase.table("raw_items").insert(payload).execute()
    return created.data[0]


def write_processing_log(supabase, source_id: str, raw_item_id: str) -> None:
    supabase.table("processing_logs").insert(
        {
            "source_id": source_id,
            "raw_item_id": raw_item_id,
            "step": "manual_raw_item_ingestion",
            "status": "success",
            "message": "Manual test raw item was saved.",
        }
    ).execute()


def main() -> None:
    supabase = get_supabase_client()

    source_id = get_or_create_manual_source(supabase)
    raw_item = upsert_raw_item(supabase, source_id)
    write_processing_log(supabase, source_id, raw_item["id"])

    print("Manual raw item ingestion works.")
    print(f"Source ID: {source_id}")
    print(f"Raw item ID: {raw_item['id']}")
    print(f"Raw item status: {raw_item['status']}")


if __name__ == "__main__":
    main()
