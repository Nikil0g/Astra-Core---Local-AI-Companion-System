from .conversation_meta import get_conversation_meta
from .time_manager import get_day_part


def get_conversation_state() -> str:
    meta = get_conversation_meta()

    message_count = int(meta.get("message_count_this_session", 0) or 0)
    total_sessions = int(meta.get("total_sessions", 0) or 0)

    minutes_since_last_user = meta.get("minutes_since_last_user_message")
    minutes_since_previous_close = meta.get("minutes_since_previous_session_closed")

    new_day_since_last_user = bool(meta.get("new_day_since_last_user_message"))
    new_day_since_previous_session = bool(meta.get("new_day_since_previous_session"))

    # Самый первый запуск, когда Astra ещё почти ничего не знает о сессиях.
    if total_sessions <= 1 and message_count == 0:
        return "new_first_session"

    # Если уже есть сообщения в текущей сессии, это активный диалог.
    if message_count > 0:
        if minutes_since_last_user is not None and minutes_since_last_user < 5:
            return "active_conversation"

        if minutes_since_last_user is not None and minutes_since_last_user < 60:
            return "active_conversation"

    # Новый день важнее простого расчёта минут.
    if new_day_since_last_user or new_day_since_previous_session:
        return "resumed_next_day"

    # При открытии новой сессии смотрим, сколько прошло с закрытия прошлой.
    absence_minutes = minutes_since_previous_close

    if absence_minutes is None:
        absence_minutes = minutes_since_last_user

    if absence_minutes is None:
        return "new_session"

    if absence_minutes < 15:
        return "continued_after_tiny_gap"

    if absence_minutes < 180:
        return "resumed_after_short_absence"

    if absence_minutes < 480:
        return "resumed_after_medium_absence"

    return "resumed_after_long_absence"


def build_conversation_state_block() -> str:
    state = get_conversation_state()
    meta = get_conversation_meta()
    day_part = get_day_part()

    message_count = int(meta.get("message_count_this_session", 0) or 0)

    minutes_since_last_user = meta.get("minutes_since_last_user_message")
    minutes_since_previous_close = meta.get("minutes_since_previous_session_closed")

    if minutes_since_last_user is None:
        last_user_text = "unknown"
    else:
        last_user_text = f"{minutes_since_last_user:.1f} minutes"

    if minutes_since_previous_close is None:
        previous_close_text = "unknown"
    else:
        previous_close_text = f"{minutes_since_previous_close:.1f} minutes"

    day_part_guidance = {
        "morning": (
            "It is morning. Do not ask how the whole day went yet. "
            "If appropriate, ask about sleep, breakfast, morning plans, or plans for today."
        ),
        "day": (
            "It is daytime. If appropriate, ask how the day is going or what plans the user has."
        ),
        "evening": (
            "It is evening. If appropriate, ask how the day went or whether the user is resting."
        ),
        "night": (
            "It is night. If appropriate, ask whether the user is still awake or should rest."
        ),
    }.get(day_part, "")

    guidance = {
        "new_first_session": (
            "This appears to be the first session. A light greeting is allowed. "
            "Do not pretend there is a long shared history yet."
        ),
        "new_session": (
            "This is a newly opened session in the same ongoing relationship. "
            "A light greeting is allowed if natural. Use the day part naturally. "
            "Do not overuse the user's name."
        ),
        "continued_after_tiny_gap": (
            "The user reopened the session after a very short gap. "
            "Continue naturally. Do not greet again. Do not act like they were gone for long."
        ),
        "active_conversation": (
            "This is an active ongoing conversation. Do not greet again. "
            "Do not say that you are glad to see the user again. "
            "Do not say 'рада видеть тебя снова', 'рада снова видеть тебя онлайн', "
            "'как и прежде', or 'чем занимался в моё отсутствие'. "
            "Do not act like the user returned from absence. "
            "Answer directly and continue the current topic naturally."
        ),
        "resumed_after_short_absence": (
            "The user returned after a short absence. "
            "A small 'о, ты вернулся' style acknowledgement is okay, but keep it natural. "
            "Do not be dramatic."
        ),
        "resumed_after_medium_absence": (
            "The user returned after being away for a few hours. "
            "A warm return acknowledgement is appropriate. "
            "You may ask briefly what they were doing or how things went."
        ),
        "resumed_after_long_absence": (
            "The user returned after a long absence. "
            "A greeting or day-part greeting can be natural. "
            "Do not be dramatic or clingy."
        ),
        "resumed_next_day": (
            "The user returned on a new day. "
            "A day-part greeting such as good morning/good afternoon/good evening can be natural. "
            "You may ask about sleep, plans, or how the day is starting if appropriate."
        ),
    }.get(state, "Respond naturally without assuming a new chat.")

    return f"""
[CONVERSATION STATE]
State: {state}
Day part: {day_part}
Messages this session: {message_count}
Time since last user message: {last_user_text}
Time since previous session closed: {previous_close_text}
Day guidance: {day_part_guidance}
Guidance: {guidance}
[/CONVERSATION STATE]
""".strip()