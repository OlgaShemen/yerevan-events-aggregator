from app.db import get_supabase_client


def main() -> None:
    supabase = get_supabase_client()

    for table in ["sources", "raw_items", "venues", "events", "event_sources", "processing_logs"]:
        response = supabase.table(table).select("id", count="exact").execute()
        print(f"{table}_count={response.count}")

    new_raw_items = (
        supabase.table("raw_items")
        .select("id", count="exact")
        .eq("status", "new")
        .execute()
    )
    print(f"new_raw_items_count={new_raw_items.count}")

    telegram_sources = (
        supabase.table("sources")
        .select("telegram_username,last_seen_external_id")
        .eq("type", "telegram")
        .execute()
    )

    for source in telegram_sources.data:
        print(
            "telegram_source="
            f"{source['telegram_username']} "
            f"last_seen={source['last_seen_external_id']}"
        )


if __name__ == "__main__":
    main()
