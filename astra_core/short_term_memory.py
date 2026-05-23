import json
from datetime import datetime, timedelta
from pathlib import Path
from .settings import get_setting

SHORT_TERM_FILE = (
    Path(get_setting("base_dir")) / "conversation_state.json"
)
MAX_AGE_HOURS = 24
MAX_MESSAGES = 80


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_state() -> dict:
    if not SHORT_TERM_FILE.exists():
        return {"messages": []}

    try:
        return json.loads(SHORT_TERM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"messages": []}


def save_state(state: dict) -> None:
    SHORT_TERM_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# TODO:
# Before deleting expired short-term memories:
# - analyze importance
# - promote important memories into long-term memory
# - promote emotional moments into relationship memory
# - later integrate semantic retrieval

def cleanup_state(state: dict) -> dict:
    cutoff = datetime.now() - timedelta(hours=MAX_AGE_HOURS)

    cleaned = []

    for msg in state.get("messages", []):
        raw_time = msg.get("created_at")

        try:
            created_at = datetime.fromisoformat(raw_time)
        except Exception:
            continue

        if created_at >= cutoff:
            cleaned.append(msg)

    cleaned = cleaned[-MAX_MESSAGES:]

    state["messages"] = cleaned
    return state


def add_message(role: str, text: str) -> None:
    state = load_state()
    state = cleanup_state(state)

    state.setdefault("messages", []).append(
        {
            "role": role,
            "text": text.strip(),
            "created_at": now_iso(),
        }
    )

    state = cleanup_state(state)
    save_state(state)


def build_short_term_block(limit: int = 30) -> str:
    state = cleanup_state(load_state())
    save_state(state)

    messages = state.get("messages", [])[-limit:]

    if not messages:
        return ""

    lines = [
        "[SHORT-TERM CONVERSATION MEMORY]",
        "This is the recent conversation context from the last 24 hours.",
        "Use this before long-term memory when answering questions about what was just said.",
        "If this conflicts with long-term memory about recent dialogue, trust this block.",
        "",
    ]

    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "")
        created_at = msg.get("created_at", "")

        lines.append(f"- {created_at} | {role}: {text}")

    lines.append("[/SHORT-TERM CONVERSATION MEMORY]")

    return "\n".join(lines)


def clear_state() -> None:
    """Полностью очищает буфер короткой памяти для новой сессии."""
    save_state({"messages": []})