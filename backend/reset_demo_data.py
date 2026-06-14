from app.db import get_supabase_client


def delete_all(supabase, table: str) -> None:
    supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()


def main() -> None:
    supabase = get_supabase_client()

    delete_all(supabase, "event_sources")
    delete_all(supabase, "events")
    delete_all(supabase, "venues")
    delete_all(supabase, "raw_items")
    delete_all(supabase, "processing_logs")

    supabase.table("sources").update(
        {
            "last_seen_external_id": None,
            "last_checked_at": None,
        }
    ).neq("id", "00000000-0000-0000-0000-000000000000").execute()

    print("Demo data reset completed.")
    print("Deleted event_sources, events, venues, raw_items, processing_logs.")
    print("Reset sources.last_seen_external_id and sources.last_checked_at.")


if __name__ == "__main__":
    main()
