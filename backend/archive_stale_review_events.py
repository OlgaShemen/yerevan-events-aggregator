import argparse
import sys

from app.db import get_supabase_client
from app.review_cleanup import (
    DEFAULT_STALE_REVIEW_DAYS,
    archive_stale_undated_review_events,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive old needs_review events that have no calendar dates."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_STALE_REVIEW_DAYS,
        help="Archive undated review events created at least this many days ago.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    if args.days < 1:
        raise ValueError("--days must be at least 1")

    archived = archive_stale_undated_review_events(
        get_supabase_client(),
        stale_days=args.days,
    )
    print(f"archived_stale_undated_review_events={archived}")


if __name__ == "__main__":
    main()
