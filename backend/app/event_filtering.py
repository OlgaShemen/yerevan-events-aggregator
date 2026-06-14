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


def is_non_event_collection(raw_text: str | None) -> bool:
    if not raw_text:
        return False

    text = raw_text.lower()
    return bool(SUMMER_CAMP_PATTERN.search(text)) and any(
        marker in text for marker in COLLECTION_MARKERS
    )


def should_ignore_extracted_event(event: dict, raw_text: str | None) -> bool:
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
