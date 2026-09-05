import unittest

from app.deduplication import duplicate_reason, select_review_duplicate


class DeduplicationTests(unittest.TestCase):
    def test_flags_same_dated_event(self):
        first = {
            "title": "Органные сказки",
            "date_start": "2026-09-12",
            "time_start": "18:00",
            "venue_name": "Концертный зал",
        }
        second = {**first, "venue_name": None}
        self.assertIsNotNone(duplicate_reason(first, second))

    def test_keeps_different_sessions(self):
        first = {
            "title": "Органные сказки",
            "date_start": "2026-09-12",
            "time_start": "12:00",
            "venue_name": "Концертный зал",
        }
        second = {**first, "time_start": "18:00"}
        self.assertIsNone(duplicate_reason(first, second))

    def test_keeps_same_title_at_clearly_different_venues(self):
        first = {
            "title": "Открытый микрофон",
            "date_start": "2026-09-12",
            "time_start": "20:00",
            "venue_name": "Ari Standup Club",
        }
        second = {**first, "venue_name": "Бар «Муха»"}
        self.assertIsNone(duplicate_reason(first, second))

    def test_flags_same_recurring_activity_in_one_week(self):
        first = {
            "title": "SUP-тур на Азатское водохранилище",
            "date_start": None,
            "time_start": "09:00",
            "recurring_schedule": "Ежедневно 09:00-15:00 и 16:00-22:00",
            "display_until": "2026-09-13",
            "venue_name": "ЖД вокзал",
        }
        second = {**first, "title": "SUP тур на Азатское вдхр."}
        self.assertIsNotNone(duplicate_reason(first, second))

    def test_keeps_recurring_activity_from_another_week(self):
        first = {
            "title": "SUP-тур на Азатское водохранилище",
            "date_start": None,
            "recurring_schedule": "Ежедневно",
            "display_until": "2026-09-13",
        }
        second = {**first, "display_until": "2026-09-20"}
        self.assertIsNone(duplicate_reason(first, second))

    def test_different_giveaways_are_not_duplicates(self):
        first = {
            "title": "Unplugged screening (розыгрыш билетов)",
            "date_start": "2026-09-10",
            "time_start": "12:00",
            "venue_name": None,
        }
        second = {
            **first,
            "title": "Silent Disco Yerevan (розыгрыш билетов)",
        }
        self.assertIsNone(duplicate_reason(first, second))

    def test_selects_newer_review_card_for_flagging(self):
        first = {
            "id": "old",
            "title": "Органные сказки",
            "date_start": "2026-09-12",
            "status": "needs_review",
            "created_at": "2026-09-01T10:00:00+00:00",
        }
        second = {
            **first,
            "id": "new",
            "created_at": "2026-09-02T10:00:00+00:00",
        }
        candidate = duplicate_reason(first, second)
        target, other = select_review_duplicate(candidate)
        self.assertEqual(target["id"], "new")
        self.assertEqual(other["id"], "old")

    def test_does_not_flag_two_published_cards(self):
        first = {
            "title": "Органные сказки",
            "date_start": "2026-09-12",
            "status": "published",
        }
        second = dict(first)
        candidate = duplicate_reason(first, second)
        self.assertIsNone(select_review_duplicate(candidate))


if __name__ == "__main__":
    unittest.main()
