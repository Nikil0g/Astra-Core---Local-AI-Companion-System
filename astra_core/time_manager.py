from datetime import datetime
from zoneinfo import ZoneInfo

from .settings import get_setting
from .activity import minutes_since_last_user_activity


DEFAULT_TIMEZONE = "Europe/Moscow"


def get_timezone() -> str:
    return get_setting("timezone", DEFAULT_TIMEZONE)


def now() -> datetime:
    timezone = ZoneInfo(get_timezone())
    return datetime.now(timezone)


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def get_day_part() -> str:
    hour = now().hour

    if 5 <= hour < 12:
        return "morning"

    if 12 <= hour < 17:
        return "day"

    if 17 <= hour < 23:
        return "evening"

    return "night"


def get_time_context_block() -> str:
    minutes = minutes_since_last_user_activity()

    if minutes is None:
        last_activity_text = "unknown"
    else:
        last_activity_text = f"{minutes:.1f} minutes ago"

    return f"""
[TIME CONTEXT]
Current time: {now_iso()}
Timezone: {get_timezone()}
Day part: {get_day_part()}
Last user activity: {last_activity_text}
[/TIME CONTEXT]
""".strip()


def get_absence_level() -> str:
    minutes = minutes_since_last_user_activity()

    if minutes is None:
        return "unknown"

    if minutes < 5:
        return "active_conversation"

    if minutes < 60:
        return "short_absence"

    if minutes < 360:
        return "medium_absence"

    if minutes < 1440:
        return "long_absence"

    return "very_long_absence"