import re


ACTIVE_OPENING_PATTERNS = [
    r"^как и прежде,\s*",
    r"^я рада снова видеть тебя онлайн[!\.,\s]*",
    r"^я рада видеть тебя снова[!\.,\s]*",
    r"^рада видеть тебя снова[!\.,\s]*",
    r"^рада снова видеть тебя онлайн[!\.,\s]*",
    r"^никита,\s*привет[!\.,\s]*",
    r"^привет,\s*никита[!\.,\s]*",
    r"^привет никита[!\.,\s]*",
    r"^привет[!\.,\s]*",
]


ACTIVE_FORBIDDEN_PHRASES = [
    "чем занимался в моё отсутствие",
    "чем занимался в мое отсутствие",
    "рада снова видеть тебя онлайн",
    "рада видеть тебя снова",
    "как и прежде",
]


def clean_active_conversation_opening(answer: str) -> str:
    cleaned = answer.strip()

    for pattern in ACTIVE_OPENING_PATTERNS:
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

    for phrase in ACTIVE_FORBIDDEN_PHRASES:
        cleaned = cleaned.replace(phrase, "").strip()
        cleaned = cleaned.replace(phrase.capitalize(), "").strip()

    # Чистим возможные остатки пунктуации после удаления начала.
    cleaned = cleaned.lstrip(" ,.!—-:;").strip()

    if not cleaned:
        return answer.strip()

    # Если после удаления начало стало с маленькой буквы — поднимаем первую букву.
    return cleaned[:1].upper() + cleaned[1:]


def apply_behavior_guard(answer: str, conversation_state: str) -> str:
    if conversation_state == "active_conversation":
        return clean_active_conversation_opening(answer)

    return answer.strip()