import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .settings import get_setting


META_FILE = Path(get_setting("base_dir")) / "conversation_meta.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def minutes_between(start: str | None, end: str | None = None) -> float | None:
    start_dt = parse_iso(start)

    if start_dt is None:
        return None

    end_dt = parse_iso(end) if end else datetime.now()

    if end_dt is None:
        return None

    return (end_dt - start_dt).total_seconds() / 60


def is_different_day(start: str | None, end: str | None = None) -> bool:
    start_dt = parse_iso(start)

    if start_dt is None:
        return False

    end_dt = parse_iso(end) if end else datetime.now()

    if end_dt is None:
        return False

    return start_dt.date() != end_dt.date()


def default_meta() -> dict[str, Any]:
    return {
        "current_session_id": None,
        "session_started_at": None,
        "previous_session_started_at": None,
        "previous_session_closed_at": None,
        "last_user_message_at": None,
        "last_astra_message_at": None,
        "message_count_this_session": 0,
        "total_sessions": 0,
    }


def load_meta() -> dict[str, Any]:
    if not META_FILE.exists():
        return default_meta()

    try:
        data = json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return default_meta()

    meta = default_meta()
    meta.update(data)
    return meta


def save_meta(meta: dict[str, Any]) -> None:
    META_FILE.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def start_new_session() -> None:
    meta = load_meta()
    now = now_iso()

    meta["previous_session_started_at"] = meta.get("session_started_at")
    meta["current_session_id"] = f"session_{now.replace(':', '-').replace('.', '-')}"
    meta["session_started_at"] = now
    meta["message_count_this_session"] = 0
    meta["total_sessions"] = int(meta.get("total_sessions", 0) or 0) + 1

    save_meta(meta)


def close_current_session() -> None:
    meta = load_meta()
    meta["previous_session_closed_at"] = now_iso()
    save_meta(meta)


def mark_user_message() -> None:
    meta = load_meta()
    meta["last_user_message_at"] = now_iso()
    meta["message_count_this_session"] = int(
        meta.get("message_count_this_session", 0) or 0
    ) + 1
    save_meta(meta)


def mark_astra_message() -> None:
    meta = load_meta()
    meta["last_astra_message_at"] = now_iso()
    save_meta(meta)


def get_conversation_meta() -> dict[str, Any]:
    meta = load_meta()

    session_started_at = meta.get("session_started_at")
    previous_session_closed_at = meta.get("previous_session_closed_at")
    last_user_message_at = meta.get("last_user_message_at")
    last_astra_message_at = meta.get("last_astra_message_at")

    meta["minutes_since_session_started"] = minutes_between(session_started_at)
    meta["minutes_since_previous_session_closed"] = minutes_between(
        previous_session_closed_at
    )
    meta["minutes_since_last_user_message"] = minutes_between(last_user_message_at)
    meta["minutes_since_last_astra_message"] = minutes_between(last_astra_message_at)

    meta["new_day_since_last_user_message"] = is_different_day(last_user_message_at)
    meta["new_day_since_previous_session"] = is_different_day(
        previous_session_closed_at
    )

    return meta