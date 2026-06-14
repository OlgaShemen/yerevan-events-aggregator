from app.db import get_supabase_client


def main() -> None:
    supabase = get_supabase_client()
    response = supabase.table("sources").select("id,name,type").limit(1).execute()

    print("Supabase connection works.")
    print(f"Rows returned: {len(response.data)}")


if __name__ == "__main__":
    main()
