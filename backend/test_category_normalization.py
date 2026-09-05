import unittest

from app.category_normalization import normalize_category


class LectureCategoryTests(unittest.TestCase):
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
