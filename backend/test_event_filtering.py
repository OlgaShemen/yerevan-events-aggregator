import unittest

from app.event_filtering import should_ignore_extracted_event


class PromotionalEventFilteringTests(unittest.TestCase):
    def test_promotional_offers_are_ignored(self):
        for title in [
            "Акция KWIKPAY: подарки Apple за переводы в Армению",
            "Розыгрыш билетов на концерт",
            "Рекламный конкурс магазина",
            "Giveaway: win an iPhone",
            "Подарок за покупку",
        ]:
            with self.subTest(title=title):
                self.assertTrue(should_ignore_extracted_event({"title": title}, None))

    def test_promotion_details_can_be_in_description(self):
        self.assertTrue(should_ignore_extracted_event({
            "title": "Акция KWIKPAY",
            "description": "Подарки Apple за переводы в Армению",
        }, None))

    def test_real_events_with_prizes_are_kept(self):
        for title in [
            "Музыкальный конкурс молодых исполнителей",
            "Шахматный турнир с призами",
            "Квиз: подарки победителям от спонсора",
            "Благотворительная акция: уборка парка",
        ]:
            with self.subTest(title=title):
                self.assertFalse(should_ignore_extracted_event({"title": title}, None))

    def test_promotional_sibling_does_not_hide_real_event(self):
        self.assertFalse(should_ignore_extracted_event(
            {"title": "Джазовый концерт"},
            "Джазовый концерт. Акция KWIKPAY: подарки Apple за переводы в Армению",
        ))


if __name__ == "__main__":
    unittest.main()
