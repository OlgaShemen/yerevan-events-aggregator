from collections.abc import Iterable


CATEGORY_KEYWORDS = [
    (
        "kids",
        [
            "\u0434\u0435\u0442\u0438",
            "\u0434\u0435\u0442\u044f\u043c",
            "\u0434\u0435\u0442\u0441\u043a\u0438\u0439",
            "\u0434\u0435\u0442\u0441\u043a\u0430\u044f",
            "\u0434\u043b\u044f \u0434\u0435\u0442\u0435\u0439",
            "\u043c\u0430\u043b\u044b\u0448",
            "kids",
        ],
    ),
    (
        "tourism",
        [
            "\u044d\u043a\u0441\u043a\u0443\u0440\u0441\u0438\u044f",
            "\u044d\u043a\u0441\u043a\u0443\u0440\u0441\u0438\u043e\u043d",
            "\u0445\u0430\u0439\u043a\u0438\u043d\u0433",
            "\u043f\u043e\u0445\u043e\u0434",
            "\u0442\u0443\u0440 ",
            "\u0442\u0443\u0440\u0438\u0437\u043c",
            "\u0438\u043c\u043c\u0435\u0440\u0441\u0438\u0432\u043d\u044b\u0439 \u0430\u0443\u0434\u0438\u043e\u0441\u043f\u0435\u043a\u0442\u0430\u043a\u043b\u044c",
            "hiking",
            "tour",
        ],
    ),
    (
        "party",
        [
            "\u043a\u0430\u0440\u0430\u043e\u043a\u0435",
            "\u043a\u0432\u0438\u0437",
            "quiz",
            "\u0438\u043d\u0442\u0435\u043b\u043b\u0435\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u0430\u044f \u0438\u0433\u0440\u0430",
            "\u0441\u0442\u0435\u043d\u0434\u0430\u043f",
            "standup",
            "stand-up",
            "open mic",
            "\u043e\u0442\u043a\u0440\u044b\u0442\u044b\u0439 \u043c\u0438\u043a\u0440\u043e\u0444\u043e\u043d",
            "\u0432\u0435\u0447\u0435\u0440\u0438\u043d\u043a\u0430",
            "party",
        ],
    ),
    (
        "theatre",
        [
            "\u0441\u043f\u0435\u043a\u0442\u0430\u043a\u043b\u044c",
            "\u043f\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430",
            "\u0431\u0430\u043b\u0435\u0442",
            "\u043e\u043f\u0435\u0440\u0430",
            "\u0442\u0435\u0430\u0442\u0440",
        ],
    ),
    (
        "concert",
        [
            "\u043a\u043e\u043d\u0446\u0435\u0440\u0442",
            "\u0434\u0436\u0430\u0437",
            "jazz",
            "live music",
            "tribute",
            "trio",
            "quartet",
            "\u0430\u043b\u044c\u0431\u043e\u043c",
        ],
    ),
    (
        "movie",
        [
            "\u043a\u0438\u043d\u043e",
            "\u0444\u0438\u043b\u044c\u043c",
            "\u043f\u043e\u043a\u0430\u0437 \u0444\u0438\u043b\u044c\u043c\u0430",
            "screening",
            "movie",
        ],
    ),
    (
        "workshop",
        [
            "\u043c\u0430\u0441\u0442\u0435\u0440-\u043a\u043b\u0430\u0441\u0441",
            "\u0432\u043e\u0440\u043a\u0448\u043e\u043f",
            "workshop",
            "\u043b\u0435\u043f\u043a\u0430",
            "\u043a\u0435\u0440\u0430\u043c\u0438\u043a\u0430",
            "\u0440\u0438\u0441\u043e\u0432\u0430\u043d\u0438\u0435",
            "\u0440\u043e\u0441\u043f\u0438\u0441\u044c",
            "\u0433\u043e\u043d\u0447\u0430\u0440",
            "\u044d\u0431\u0440\u0443",
            "\u0441\u0432\u0435\u0447\u0435\u0432\u0430\u0440\u0435\u043d\u0438\u0435",
            "\u0443\u043a\u0440\u0430\u0448\u0435\u043d\u0438\u044f",
        ],
    ),
    (
        "food",
        [
            "\u0434\u0435\u0433\u0443\u0441\u0442\u0430\u0446\u0438\u044f",
            "\u0432\u0438\u043d\u043e",
            "\u0432\u0438\u043d\u043d",
            "\u0443\u0436\u0438\u043d",
            "\u0431\u0440\u0430\u043d\u0447",
            "\u043a\u0443\u043b\u0438\u043d\u0430\u0440",
            "food",
            "wine",
        ],
    ),
]


def build_category_text(parts: Iterable[str | None]) -> str:
    return " ".join(part for part in parts if part).lower()


def keyword_matches(text: str, keyword: str) -> bool:
    if keyword == "\u043e\u043f\u0435\u0440\u0430":
        return any(token == keyword for token in text.split())

    return keyword in text


def normalize_category(event: dict, raw_text: str | None = None) -> str:
    # Use only the event title. Descriptions and raw digest posts can contain
    # unrelated events and pull categories in the wrong direction.
    text = build_category_text([event.get("title")])

    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword_matches(text, keyword) for keyword in keywords):
            return category

    return event.get("category") or "other"
