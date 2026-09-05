from datetime import date, datetime, timedelta, timezone


PUBLISH_CONFIDENCE_THRESHOLD = 0.75
REVIEW_REASON_LABELS = {
    "missing_date": "Нет даты",
    "missing_place": "Нет места",
    "low_confidence": "Низкая уверенность AI",
    "possible_duplicate": "Возможный дубль",
    "unconfirmed_date": "Дата не подтверждена",
    "unconfirmed_time": "Время не подтверждено",
    "unconfirmed_place": "Место не подтверждено",
}
YEREVAN_TIMEZONE = timezone(timedelta(hours=4))


def yerevan_today() -> date:
    return datetime.now(YEREVAN_TIMEZONE).date()


def has_usable_date(event: dict, today: date | None = None) -> bool:
    if event.get("date_start") or event.get("date_end"):
        return True

    schedule = event.get("recurring_schedule")
    display_until = event.get("display_until")
    if not schedule or not display_until:
        return False

    return display_until >= (today or yerevan_today()).isoformat()


def has_duplicate_candidate(event: dict, duplicate_candidate: dict | None = None) -> bool:
    if duplicate_candidate:
        return True
    ai_payload = event.get("ai_payload") or {}
    return bool(ai_payload.get("duplicate_candidate"))


def build_review_reasons(
    event: dict,
    duplicate_candidate: dict | None = None,
    *,
    today: date | None = None,
) -> list[str]:
    reasons = []
    if not has_usable_date(event, today=today):
        reasons.append("missing_date")
    if not (event.get("venue_name") or event.get("address")):
        reasons.append("missing_place")
    ai_payload = event.get("ai_payload") or {}
    evidence = event.get("evidence_validation") or ai_payload.get("evidence_validation") or {}
    has_current_evidence = evidence.get("version") == 1
    if has_current_evidence:
        for evidence_type in ("date", "time", "place"):
            result = evidence.get(evidence_type) or {}
            if result.get("required") and not result.get("confirmed"):
                reasons.append(f"unconfirmed_{evidence_type}")
    elif float(event.get("confidence_score") or 0) < PUBLISH_CONFIDENCE_THRESHOLD:
        reasons.append("low_confidence")
    if has_duplicate_candidate(event, duplicate_candidate):
        reasons.append("possible_duplicate")
    return reasons
