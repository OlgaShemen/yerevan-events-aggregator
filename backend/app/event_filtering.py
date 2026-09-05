import re


SUMMER_CAMP_PATTERN = re.compile(
    "("
    "\u043b\u0435\u0442\u043d\\w*(?:\\s+[\\w-]+){0,3}\\s+"
    "(?:"
    "\u043b\u0430\u0433\u0435\u0440\\w*|"
    "\u0448\u043a\u043e\u043b\\w*|"
    "\u0441\u043c\u0435\u043d\\w*"
    ")|"
    "\u0442\u0432\u043e\u0440\u0447\u0435\u0441\u043a\\w*\\s+\u0441\u043c\u0435\u043d\\w*|"
    "summer\\s+(?:camp|school)"
    ")",
    re.IGNORECASE,
)

COLLECTION_MARKERS = [
    "\u043f\u043e\u0434\u0431\u043e\u0440\u043a",
    "\u043c\u044b \u0441\u043e\u0431\u0440\u0430\u043b\u0438",
    "telegram-\u0431\u043e\u0442",
    "\u0431\u043e\u0442\u0435",
]


PROMOTIONAL_TITLE_PATTERN = re.compile(
    r"(?:^\s*(?:\W)*|[([]\s*)(?:"
    r"(?:рекламн\w*|промо)\s+(?:конкурс\w*|акци\w*|розыгрыш\w*)|"
    r"(?:финал\w*\s+)?розыгрыш\w*(?:\s+(?:подарк\w*|приз\w*|билет\w*|iphone\w*|apple\b))?|"
    r"(?:giveaway|sweepstakes)\b|promotional\s+(?:contest|campaign)\b"
    r")",
    re.IGNORECASE,
)
PROMOTIONAL_DESCRIPTION_PATTERN = re.compile(
    r"^\s*(?:\W)*(?:розыгрыш\w*|разыгра(?:ем|ю|ют|ываем)\b|"
    r"финал\w*\s+розыгрыш\w*|giveaway\b|sweepstakes\b)",
    re.IGNORECASE,
)
TRANSACTION_REWARD_PATTERN = re.compile(
    r"(?:подар\w*|приз\w*|выигра\w*|розыгрыш\w*|кешбэк\w*|кэшбэк\w*)"
    r"[^.!?\n]{0,100}\bза\s+(?:денежн\w*\s+)?(?:перевод\w*|покупк\w*|репост\w*|подписк\w*)\b",
    re.IGNORECASE,
)


def is_promotional_event(event: dict) -> bool:
    # Inspect this event's text, not the whole digest shared by its siblings.
    title = event.get("title") or ""
    text = title + "\n" + (event.get("description") or "")
    return bool(
        PROMOTIONAL_TITLE_PATTERN.search(title)
        or PROMOTIONAL_DESCRIPTION_PATTERN.search(event.get("description") or "")
        or TRANSACTION_REWARD_PATTERN.search(title)
        or (
            re.match(r"^\s*акция\b", title, re.IGNORECASE)
            and TRANSACTION_REWARD_PATTERN.search(text)
        )
    )


def is_non_event_collection(raw_text: str | None) -> bool:
    if not raw_text:
        return False

    text = raw_text.lower()
    return bool(SUMMER_CAMP_PATTERN.search(text)) and any(
        marker in text for marker in COLLECTION_MARKERS
    )


def should_ignore_extracted_event(event: dict, raw_text: str | None) -> bool:
    if is_promotional_event(event):
        return True

    text = " ".join(
        value
        for value in [
            event.get("title"),
            event.get("description"),
        ]
        if value
    )

    if SUMMER_CAMP_PATTERN.search(text):
        return True

    return bool(is_non_event_collection(raw_text))
