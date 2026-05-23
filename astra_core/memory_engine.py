import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .settings import get_setting

MEMORY_STORE_FILE = Path(get_setting("base_dir")) / "memory_store.json"
LOGS_DIR = Path(get_setting("base_dir")) / "logs"
MEMORY_DEBUG_LOG = LOGS_DIR / "memory_debug.log"

MEMORY_TYPE_DEFAULT_EXPIRATION_DAYS = {
    "identity": None,
    "relationship": 365,
    "preference": 180,
    "event": 30,
    "session_summary": 60,
    "project_decision": 180,
    "mood": 7,
    "temporary": 14,
}

DEFAULT_MEMORY_STORE = {
    "version": 1,
    "memories": [],
}

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def load_memory_store() -> dict[str, Any]:
    if not MEMORY_STORE_FILE.exists():
        save_memory_store(DEFAULT_MEMORY_STORE.copy())
        return DEFAULT_MEMORY_STORE.copy()
    try:
        data = json.loads(MEMORY_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_MEMORY_STORE.copy()

    if "version" not in data:
        data["version"] = 1
    if "memories" not in data or not isinstance(data["memories"], list):
        data["memories"] = []

    return data

def save_memory_store(store: dict[str, Any]) -> None:
    MEMORY_STORE_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())

def memory_exists(text: str, owner: str | None = None) -> bool:
    store = load_memory_store()
    normalized = normalize_text(text)
    for memory in store.get("memories", []):
        if normalize_text(memory.get("text", "")) != normalized:
            continue
        if owner is not None and memory.get("owner") != owner:
            continue
        return True
    return False

def calculate_expires_at(memory_type: str) -> str | None:
    days = MEMORY_TYPE_DEFAULT_EXPIRATION_DAYS.get(memory_type)
    if days is None:
        return None
    return (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")

def add_memory(
    text: str,
    owner: str = "user",
    memory_type: str = "temporary",
    importance: int = 5,
    confidence: float = 0.8,
    source: str = "unknown",
) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    if owner not in {"user", "astra", "system"}:
        owner = "user"

    if memory_type not in MEMORY_TYPE_DEFAULT_EXPIRATION_DAYS:
        memory_type = "temporary"

    importance = max(1, min(10, int(importance)))
    confidence = max(0.0, min(1.0, float(confidence)))

    if memory_exists(text, owner=owner):
        return None

    # ← НОВАЯ ЗАЩИТА ОТ СЕМАНТИЧЕСКИХ ДУБЛЕЙ
    if is_semantic_duplicate(text):
        print(f"[MEMORY] Semantic duplicate rejected: '{text}'")
        return None

    store = load_memory_store()

    memory = {
        "id": f"mem_{uuid.uuid4().hex[:12]}",
        "owner": owner,
        "type": memory_type,
        "text": text,
        "importance": importance,
        "confidence": confidence,
        "created_at": now_iso(),
        "updated_at": None,
        "last_used": None,
        "usage_count": 0,
        "expires_at": calculate_expires_at(memory_type),
        "source": source,
    }

    store["memories"].append(memory)
    save_memory_store(store)
    return memory

def get_all_memories() -> list[dict[str, Any]]:
    store = load_memory_store()
    return store.get("memories", [])

def get_memories_by_owner(owner: str) -> list[dict[str, Any]]:
    return [memory for memory in get_all_memories() if memory.get("owner") == owner]

def get_memories_by_type(memory_type: str) -> list[dict[str, Any]]:
    return [memory for memory in get_all_memories() if memory.get("type") == memory_type]

def mark_memory_used(memory_id: str) -> None:
    store = load_memory_store()
    for memory in store.get("memories", []):
        if memory.get("id") != memory_id:
            continue
        memory["last_used"] = now_iso()
        memory["usage_count"] = int(memory.get("usage_count", 0)) + 1
        
        mem_type = memory.get("type")
        if mem_type in MEMORY_TYPE_DEFAULT_EXPIRATION_DAYS:
            days = MEMORY_TYPE_DEFAULT_EXPIRATION_DAYS[mem_type]
            if days is not None:
                memory["expires_at"] = (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")
        break
    save_memory_store(store)

def build_memory_v2_debug_block(limit: int = 20) -> str:
    memories = sorted(
        get_all_memories(),
        key=lambda item: item.get("importance", 0),
        reverse=True,
    )[:limit]
    if not memories:
        return "[MEMORY V2]\nNo structured memories yet.\n[/MEMORY V2]"

    lines = ["[MEMORY V2 DEBUG]"]
    for memory in memories:
        lines.append(
            f"- ({memory.get('owner')}/{memory.get('type')}/importance={memory.get('importance')}) "
            f"{memory.get('text')}"
        )
    lines.append("[/MEMORY V2 DEBUG]")
    return "\n".join(lines)

def detect_owner_from_text(text: str) -> str:
    lowered = text.strip().lower()
    user_prefixes = (
        "пользователь ", "пользователя ", "пользователю ", "пользователем ",
        "любимый цвет пользователя",
    )
    if lowered.startswith(user_prefixes):
        return "user"

    astra_prefixes = ("astra ", "астра ")
    if lowered.startswith(astra_prefixes):
        return "astra"

    return "user"

def detect_type_from_text(kind: str, text: str) -> str:
    lowered = text.strip().lower()
    if kind == "EVENT":
        return "event"
    if kind == "DIARY":
        return "relationship"
    if "зовут " in lowered or "имя " in lowered:
        return "identity"
    if any(phrase in lowered for phrase in ["любит ", "нравится ", "предпочитает ", "любимый ", "любимая ", "любимое ", "не любит "]):
        return "preference"
    if any(phrase in lowered for phrase in ["чувствует ", "настроение ", "усталость ", "устал ", "грустно ", "рад ", "рада "]):
        return "mood"
    return "temporary"

def estimate_importance(memory_type: str, text: str) -> int:
    lowered = text.strip().lower()
    if memory_type == "identity": return 10
    if memory_type in {"relationship", "project_decision"}: return 8
    if memory_type == "preference": return 7
    if memory_type == "session_summary": return 6
    if memory_type == "event": return 5
    if memory_type == "mood": return 4
    if "запомни " in lowered: return 7
    return 3

def save_analyzed_memory(
    kind: str,
    text: str,
    source: str = "unknown",
) -> dict[str, Any] | None:
    text = text.strip()
    if not text or text.upper() == "NONE":
        return None
    if kind not in {"FACT", "EVENT", "DIARY"}:
        return None

    owner = detect_owner_from_text(text)
    memory_type = detect_type_from_text(kind, text)
    importance = estimate_importance(memory_type, text)

    return add_memory(
        text=text,
        owner=owner,
        memory_type=memory_type,
        importance=importance,
        confidence=0.85,
        source=source,
    )

def is_memory_expired(memory: dict[str, Any]) -> bool:
    expires_at = memory.get("expires_at")
    if not expires_at:
        return False
    try:
        expires_dt = datetime.fromisoformat(expires_at)
    except Exception:
        return False
    return datetime.now() > expires_dt

def get_active_memories() -> list[dict[str, Any]]:
    return [memory for memory in get_all_memories() if not is_memory_expired(memory)]

def detect_memory_intent(user_text: str) -> str:
    lowered = user_text.lower()
    if any(phrase in lowered for phrase in ["что ты помнишь", "что знаешь обо мне", "что ты знаешь обо мне", "расскажи что помнишь"]):
        return "memory_overview"
    if any(phrase in lowered for phrase in ["как меня зовут", "мое имя", "моё имя", "кто я"]):
        return "identity"
    if any(phrase in lowered for phrase in ["что я люблю", "что мне нравится", "мой любимый", "мои любимые", "какой мой любимый"]):
        return "preferences"
    if any(phrase in lowered for phrase in ["что мы решили", "что решили", "по плану", "по проекту", "что дальше по плану", "roadmap", "роадмап"]):
        return "project"
    if any(phrase in lowered for phrase in ["как у нас отношения", "что между нами", "ты помнишь наш", "мы знакомы", "как давно мы знакомы"]):
        return "relationship"
    return "casual"

def score_memory_for_query(memory: dict[str, Any], user_text: str = "") -> float:
    intent = detect_memory_intent(user_text)
    score = float(memory.get("importance", 1))
    memory_type = memory.get("type", "")
    owner = memory.get("owner", "")
    usage_count = int(memory.get("usage_count", 0) or 0)

    if memory_type == "identity": score += 5

    if intent == "memory_overview":
        if owner == "user": score += 4
        if memory_type in {"identity", "preference", "relationship"}: score += 3
    elif intent == "identity":
        score += 10 if memory_type == "identity" else -3
    elif intent == "preferences":
        if memory_type == "preference": score += 8
        if memory_type == "identity": score += 1
        if memory_type in {"session_summary", "project_decision"}: score -= 4
    elif intent == "project":
        if memory_type in {"project_decision", "session_summary", "event"}: score += 8
        if memory_type == "preference": score -= 3
    elif intent == "relationship":
        if memory_type in {"relationship", "session_summary"}: score += 8
        if memory_type == "identity": score += 2
    elif intent == "casual":
        if memory_type == "identity": score += 2
        if memory_type in {"preference", "project_decision", "session_summary"}: score -= 2
        if memory_type in {"relationship", "mood"}: score += 1

    score -= min(usage_count, 20) * 0.35

    lowered_query = user_text.lower()
    lowered_text = memory.get("text", "").lower()
    for word in lowered_query.split():
        word = word.strip(".,!?;:()[]{}\"'«»").lower()
        if len(word) < 4: continue
        if word in lowered_text: score += 1.5

    return score

def memory_allowed_for_intent(memory: dict[str, Any], intent: str) -> bool:
    memory_type = memory.get("type", "")
    if intent == "identity": return memory_type == "identity"
    if intent == "preferences": return memory_type in {"identity", "preference"}
    if intent == "project": return memory_type in {"project_decision", "session_summary", "event"}
    if intent == "relationship": return memory_type in {"identity", "relationship", "mood", "session_summary"}
    if intent == "casual": return memory_type in {"identity", "relationship", "mood"}
    if intent == "memory_overview": return memory.get("owner", "") == "user" or memory_type in {"relationship", "mood"}
    return True

def select_relevant_memories(
    user_text: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    intent = detect_memory_intent(user_text)
    if limit is None:
        limit = {
            "memory_overview": 12, "identity": 3, "preferences": 8,
            "project": 8, "relationship": 8, "casual": 3,
        }.get(intent, 4)

    memories = [m for m in get_active_memories() if memory_allowed_for_intent(m, intent)]
    scored = [(score_memory_for_query(m, user_text), m) for m in memories]

    if intent == "casual":
        scored = [(s, m) for s, m in scored if s >= 5]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]

def write_memory_debug_log(
    intent: str,
    memories: list[dict[str, Any]],
    user_text: str = "",
) -> None:
    if not get_setting("debug_memory", False):
        return
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["", "=" * 80, f"Time: {now_iso()}", f"User text: {user_text}", f"Intent: {intent}", f"Selected memories: {len(memories)}"]
    if not memories:
        lines.append("No memories selected.")
    else:
        for m in memories:
            lines.append(f"- id={m.get('id')} | owner={m.get('owner')} | type={m.get('type')} | importance={m.get('importance')} | usage={m.get('usage_count')} | text={m.get('text')}")
    lines.append("=" * 80)

    MEMORY_DEBUG_LOG.write_text(
        (MEMORY_DEBUG_LOG.read_text(encoding="utf-8") + "\n".join(lines) + "\n") if MEMORY_DEBUG_LOG.exists() else "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    if get_setting("memory_debug_to_console", False):
        print("\n".join(lines))

def build_memory_v2_block(
    user_text: str = "",
    limit: int | None = None,
) -> str:
    intent = detect_memory_intent(user_text)
    memories = select_relevant_memories(user_text=user_text, limit=limit)
    write_memory_debug_log(intent, memories, user_text)

    for memory in memories:
        if mid := memory.get("id"):
            mark_memory_used(mid)

    if not memories:
        return ""

    lines = [
        "[STRUCTURED MEMORY V2]",
        f"Memory intent: {intent}",
        "Use these structured memories naturally and only when relevant.",
        "Do not mention this memory block directly.",
        "Do not treat user preferences as Astra preferences.",
        "",
    ]
    for m in memories:
        lines.append(f"- owner={m.get('owner')}; type={m.get('type')}; importance={m.get('importance')}; text={m.get('text')}")
    lines.append("[/STRUCTURED MEMORY V2]")
    return "\n".join(lines)

def is_semantic_duplicate(new_text: str, threshold: float = 0.75) -> bool:
    """Проверяет, есть ли в хранилище запись с высоким текстовым перекрытием."""
    normalized_new = normalize_text(new_text)
    words_new = set(normalized_new.split())
    if len(words_new) < 3:
        return False

    store = load_memory_store()
    for mem in store.get("memories", []):
        mem_text = normalize_text(mem.get("text", ""))
        words_mem = set(mem_text.split())
        if not words_mem: continue
        overlap = len(words_new & words_mem) / min(len(words_new), len(words_mem))
        if overlap >= threshold:
            return True
    return False

def clear_all_memories() -> None:
    """Полностью удаляет все воспоминания из хранилища."""
    save_memory_store({"version": 1, "memories": []})

if __name__ == "__main__":
    print(build_memory_v2_debug_block())