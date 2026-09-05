import unittest

from app.venue_resolution import resolve_known_venue


class VenueResolutionTests(unittest.TestCase):
    def test_resolves_ari_weekly_schedule_from_official_link(self):
        event = {"venue_name": None, "address": None}
        text = "Расписание на неделю\n1 сентября 20:00 Клон\nБилеты: https://aristandupclub.am/"
        resolved = resolve_known_venue(event, text)
        self.assertEqual(resolved["venue_name"], "Ari Standup Club")
        self.assertEqual(resolved["address"], "ул. Вардананц, 18/1")

    def test_resolves_muha_only_from_strong_heading(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(event, "ДВИЖ в Мухе по новому графику\nСб 20:00 показ")
        self.assertEqual(resolved["venue_name"], "Бар «Муха»")
        self.assertIsNone(resolved["address"])

    def test_does_not_use_incidental_venue_word(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(event, "Подборка событий: один концерт пройдёт в баре Муха")
        self.assertIsNone(resolved["venue_name"])

    def test_fills_known_address_for_existing_venue(self):
        event = {"venue_name": "Ari Standup", "address": None}
        resolved = resolve_known_venue(event, "")
        self.assertEqual(resolved["venue_name"], "Ari Standup")
        self.assertEqual(resolved["address"], "ул. Вардананц, 18/1")

    def test_resolves_yerevan_through_engineers_from_source_text(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(
            event,
            "Экскурсия от проекта «Ереван глазами инженера»",
        )
        self.assertEqual(resolved["venue_name"], "Ереван глазами инженера")
        self.assertEqual(resolved["address"], "Уточните у организатора")
        self.assertEqual(resolved["venue_resolution"], "trusted_directory")

    def test_resolves_letters_and_numbers_from_full_name(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(
            event,
            "Встречаемся в пространстве Letters and Numbers",
        )
        self.assertEqual(resolved["venue_name"], "Letters and Numbers")
        self.assertEqual(resolved["address"], "Туманяна, 35Г")

    def test_fills_letters_and_numbers_address_for_lan_alias(self):
        event = {"venue_name": "LAN", "address": None}
        resolved = resolve_known_venue(event, "")
        self.assertEqual(resolved["venue_name"], "LAN")
        self.assertEqual(resolved["address"], "Туманяна, 35Г")
        self.assertEqual(resolved["venue_resolution"], "trusted_directory")

    def test_resolves_vair_i_with_literal_dot(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(event, "Лекция пройдёт в пространстве vair.i")
        self.assertEqual(resolved["venue_name"], "vair.i")
        self.assertEqual(resolved["address"], "Баграмян 9/59")

    def test_does_not_resolve_similar_vair_i_text_without_dot(self):
        event = {"venue_name": None, "address": None}
        resolved = resolve_known_venue(event, "Лекция пройдёт в пространстве vair-i")
        self.assertIsNone(resolved["venue_name"])


if __name__ == "__main__":
    unittest.main()
