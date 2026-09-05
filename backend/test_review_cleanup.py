import unittest
from datetime import UTC, datetime

from app.review_cleanup import should_archive_stale_undated_event


NOW = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)


class ReviewCleanupTests(unittest.TestCase):
    def test_archives_old_undated_review_event(self):
        event = {
            "status": "needs_review",
            "date_start": None,
            "date_end": None,
            "created_at": "2026-08-20T11:59:00+00:00",
        }
        self.assertTrue(should_archive_stale_undated_event(event, now=NOW))

    def test_keeps_recent_undated_review_event(self):
        event = {
            "status": "needs_review",
            "date_start": None,
            "date_end": None,
            "created_at": "2026-08-30T12:00:00+00:00",
        }
        self.assertFalse(should_archive_stale_undated_event(event, now=NOW))

    def test_keeps_dated_review_event(self):
        event = {
            "status": "needs_review",
            "date_start": "2026-09-10",
            "date_end": None,
            "created_at": "2026-08-01T12:00:00+00:00",
        }
        self.assertFalse(should_archive_stale_undated_event(event, now=NOW))

    def test_keeps_non_review_event(self):
        event = {
            "status": "published",
            "date_start": None,
            "date_end": None,
            "created_at": "2026-08-01T12:00:00+00:00",
        }
        self.assertFalse(should_archive_stale_undated_event(event, now=NOW))


if __name__ == "__main__":
    unittest.main()
