import unittest

from app.category_normalization import normalize_category


class LectureCategoryTests(unittest.TestCase):
    def test_concert_tour_is_not_tourism(self):
        event = {
            "title": "ЭЛИЗИУМ — Greatest Hits Tour",
            "description": "Концерт группы ЭЛИЗИУМ в рамках тура.",
            "category": "tourism",
        }
        self.assertEqual(normalize_category(event), "concert")

    def test_children_in_album_title_does_not_mean_kids_event(self):
        event = {
            "title": "Ди Курцман — «Дети Просвета»",
            "description": "Концертная программа Ди Курцмана.",
            "category": "kids",
        }
        self.assertEqual(normalize_category(event), "concert")

    def test_ari_standup_context_corrects_performer_name(self):
        event = {"title": "Артур Чапарян", "venue_name": "Ari Standup", "category": "tourism"}
        self.assertEqual(normalize_category(event), "party")

    def test_explicit_event_type_beats_venue_fallback(self):
        event = {"title": "Лекция в Ari Standup", "venue_name": "Ari Standup", "category": "party"}
        self.assertEqual(normalize_category(event), "lecture")

    def test_real_kids_tour_stays_kids(self):
        event = {"title": "Пешеходная экскурсия для детей", "category": "tourism"}
        self.assertEqual(normalize_category(event), "kids")

    def test_real_guided_tour_stays_tourism(self):
        event = {"title": "Guided tour of Yerevan", "category": "other"}
        self.assertEqual(normalize_category(event), "tourism")

    def test_lecture_titles_are_normalized(self):
        examples = [
            "Лекция об архитектуре Еревана",
            "Лекторий: история армянского кино",
            "Public talk with an urbanist",
            "Դասախոսություն Երևանի պատմության մասին",
        ]
        for title in examples:
            with self.subTest(title=title):
                self.assertEqual(normalize_category({"title": title}), "lecture")

    def test_nearby_formats_keep_their_categories(self):
        examples = [
            ({"title": "Кинопоказ и обсуждение фильма"}, "movie"),
            ({"title": "Мастер-класс по архитектурному скетчингу"}, "workshop"),
            ({"title": "Спектакль о писателе"}, "theatre"),
            ({"title": "Квиз об истории Еревана"}, "party"),
        ]
        for event, expected in examples:
            with self.subTest(title=event["title"]):
                self.assertEqual(normalize_category(event), expected)


if __name__ == "__main__":
    unittest.main()
