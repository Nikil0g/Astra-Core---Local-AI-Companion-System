import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .settings import get_setting


MEMORY_STORE_FILE = Path(get_setting("base_dir")) / "memory_store.json"


def load_store() -> dict[str, Any]:
    if not MEMORY_STORE_FILE.exists():
        return {"version": 1, "memories": []}

    try:
        data = json.loads(MEMORY_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "memories": []}

    data.setdefault("version", 1)
    data.setdefault("memories", [])

    if not isinstance(data["memories"], list):
        data["memories"] = []

    return data


def save_store(store: dict[str, Any]) -> None:
    MEMORY_STORE_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_expired(memory: dict[str, Any]) -> bool:
    if memory.get("type") == "identity":
        return False

    expires_at = memory.get("expires_at")

    if not expires_at:
        return False

    try:
        expires_dt = datetime.fromisoformat(expires_at)
    except Exception:
        return False

    return datetime.now() > expires_dt


def is_broken(memory: dict[str, Any]) -> bool:
    text = str(memory.get("text", "")).strip()

    if not text:
        return True

    if text.upper() == "NONE":
        return True

    if not memory.get("id"):
        return True

    if memory.get("owner") not in {"user", "astra", "system"}:
        return True

    if not memory.get("type"):
        return True

    return False


def cleanup_memory_store() -> dict[str, int]:
    store = load_store()
    memories = store.get("memories", [])

    cleaned = []
    seen_keys = set()

    stats = {
        "before": len(memories),
        "removed_expired": 0,
        "removed_broken": 0,
        "removed_duplicates": 0,
        "after": 0,
    }

    for memory in memories:
        if is_broken(memory):
            stats["removed_broken"] += 1
            continue

        if is_expired(memory):
            stats["removed_expired"] += 1
            continue

        key = (
            memory.get("owner"),
            memory.get("type"),
            normalize_text(memory.get("text", "")),
        )

        if key in seen_keys:
            stats["removed_duplicates"] += 1
            continue

        seen_keys.add(key)
        cleaned.append(memory)

    store["memories"] = cleaned
    stats["after"] = len(cleaned)

    save_store(store)
    return stats


if __name__ == "__main__":
    stats = cleanup_memory_store()

    print("[MEMORY CLEANUP]")
    print(f"Before: {stats['before']}")
    print(f"Removed expired: {stats['removed_expired']}")
    print(f"Removed broken: {stats['removed_broken']}")
    print(f"Removed duplicates: {stats['removed_duplicates']}")
    print(f"After: {stats['after']}")