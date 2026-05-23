import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from .settings import get_setting

BASE_DIR = Path(get_setting("base_dir"))
EMERGENT_DIR = BASE_DIR / "character" / "emergent_self"
RELATIONSHIP_FILE = EMERGENT_DIR / "relationship_state.json"
EVENTS_FILE = EMERGENT_DIR / "emotional_events.json"
DEPLOYMENT_FILE = EMERGENT_DIR / "deployment_config.json"

# --- Константы системы отношений ---
LOVE_CONFESSION_COOLDOWN_HOURS = 1   # не начислять бонус чаще, чем раз в час

# --- Стадии и их диапазоны ---
STAGE_THRESHOLDS = [
    (0, 15, "acquaintance"),
    (16, 35, "friend_1"),
    (36, 55, "friend_2"),
    (56, 75, "friend_3"),
    (76, 95, "friend_4"),
    (96, 115, "best_friend_1"),
    (116, 135, "best_friend_2"),
    (136, 165, "pre_romantic"),
    (166, 185, "love_1"),
    (186, 200, "love_2"),
    (201, 999, "love_3"),
    (1000, float("inf"), "tsundere"),
]

DEFAULT_RELATIONSHIP = {
    "relationship_depth": 5,
    "affection": 0,
    "trust": 10,
    "comfort": 10,
    "anger": 0,
    "mood": 50,
    "loneliness": 0,
    "flags": {
        "angry_reaction": False
    }
}

# --- Вспомогательные функции ---
def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def get_stage(depth: int) -> str:
    for low, high, stage in STAGE_THRESHOLDS:
        if low <= depth <= high:
            return stage
    return "acquaintance"

# --- Загрузка / сохранение состояния ---
def load_relationship_state() -> dict:
    return load_json(RELATIONSHIP_FILE, DEFAULT_RELATIONSHIP)

def save_relationship_state(state: dict) -> None:
    save_json(RELATIONSHIP_FILE, state)

def load_emotional_events() -> list[dict]:
    return load_json(EVENTS_FILE, [])

def save_emotional_events(events: list[dict]) -> None:
    save_json(EVENTS_FILE, events)

def load_deployment_config() -> dict:
    return load_json(DEPLOYMENT_FILE, {"mode": "personal", "max_relationship_depth": None})

# --- Обработчики конкретных ситуаций ---
def handle_love_confession(state: dict, events: list[dict]) -> None:
    depth = state["relationship_depth"]
    stage = get_stage(depth)

    if depth < 16:
        # Резкое отторжение
        state["anger"] = min(100, state["anger"] + 30)
        state["discomfort"] = min(100, state.get("discomfort", 0) + 40)
        state["trust"] = max(0, state["trust"] - 15)
        state["flags"]["angry_reaction"] = True
        events.append({
            "type": "premature_confession",
            "valence": "negative",
            "created_at": datetime.now().isoformat(),
            "resolved": False,
            "expires_at": (datetime.now() + timedelta(hours=48)).isoformat()
        })
    elif 16 <= depth < 36:
        state["discomfort"] = min(100, state.get("discomfort", 0) + 10)
        state["trust"] = max(0, state["trust"] - 3)
        state["flags"]["angry_reaction"] = False
    elif 36 <= depth < 56:
        state["affection"] = min(100, state["affection"] + 2)
        state["mood"] = min(100, state["mood"] + 2)
        state["flags"]["angry_reaction"] = False
    elif 56 <= depth < 96:
        state["affection"] = min(100, state["affection"] + 4)
        state["mood"] = min(100, state["mood"] + 5)
        state["trust"] = min(100, state["trust"] + 2)
    else:
        state["affection"] = min(100, state["affection"] + 8)
        state["mood"] = min(100, state["mood"] + 10)
        state["trust"] = min(100, state["trust"] + 5)
        events.append({
            "type": "love_confession",
            "valence": "positive",
            "created_at": datetime.now().isoformat(),
            "resolved": True,
            "expires_at": None
        })

def handle_compliment(state: dict) -> None:
    depth = state["relationship_depth"]
    if depth < 36:
        state["discomfort"] = min(100, state.get("discomfort", 0) + 15)
        state["trust"] = max(0, state["trust"] - 5)
    else:
        state["mood"] = min(100, state["mood"] + 5)
        state["affection"] = min(100, state["affection"] + 2)

def handle_offense(state: dict, events: list[dict]) -> None:
    state["anger"] = min(100, state["anger"] + 20)
    state["discomfort"] = min(100, state.get("discomfort", 0) + 20)
    state["trust"] = max(0, state["trust"] - 10)
    now = datetime.now()
    offense = {
        "type": "offense",
        "valence": "negative",
        "created_at": now.isoformat(),
        "resolved": False,
        "expires_at": (now + timedelta(hours=24)).isoformat()
    }
    events.append(offense)

def handle_apology(state: dict, events: list[dict]) -> None:
    now = datetime.now()
    resolved_any = False
    for ev in events:
        if ev["type"] in ("offense", "premature_confession") and not ev["resolved"]:
            expires = ev.get("expires_at")
            can_resolve = expires is None
            if expires:
                try:
                    if now <= datetime.fromisoformat(expires):
                        can_resolve = True
                except Exception:
                    pass
            if can_resolve:
                ev["resolved"] = True
                resolved_any = True

    if resolved_any:
        state["anger"] = max(0, state["anger"] - 15)
        state["discomfort"] = max(0, state.get("discomfort", 0) - 20)
        state["trust"] = min(100, state["trust"] + 5)
        state["flags"]["angry_reaction"] = False

def handle_positive_action(state: dict, events: list[dict]) -> None:
    now = datetime.now()
    resolved_any = False
    for ev in events:
        if ev["type"] in ("offense", "premature_confession") and not ev["resolved"]:
            expires = ev.get("expires_at")
            can_resolve = expires is None
            if expires:
                try:
                    if now <= datetime.fromisoformat(expires):
                        can_resolve = True
                except Exception:
                    pass
            if can_resolve:
                ev["resolved"] = True
                resolved_any = True
    if resolved_any:
        state["discomfort"] = max(0, state.get("discomfort", 0) - 10)
        state["trust"] = min(100, state["trust"] + 3)
        state["flags"]["angry_reaction"] = False

def apply_deployment_limit(state: dict) -> None:
    config = load_deployment_config()
    max_depth = config.get("max_relationship_depth")
    if max_depth is not None and state["relationship_depth"] > max_depth:
        state["relationship_depth"] = max_depth

# --- Расчет прогрессии ---
def calculate_relationship_delta(state: dict, lowered: str, user_text: str = "") -> float:
    from datetime import datetime
    love_phrases = ["люблю тебя", "я тебя люблю", "люблю астру"]
    is_love = any(phrase in lowered for phrase in love_phrases)

    if is_love:
        last_time_str = state.get("last_love_confession_at")
        last_text = state.get("last_love_confession_text", "")
        if last_time_str:
            try:
                last_time = datetime.fromisoformat(last_time_str)
                now = datetime.now()
                if (now - last_time).total_seconds() < LOVE_CONFESSION_COOLDOWN_HOURS * 3600:
                    # Спам – не даём ничего
                    return 0.0
            except:
                pass

        if user_text.strip().lower() == last_text.lower():
            return 0.0

        # Новое признание – бонус +3
        state["last_love_confession_at"] = datetime.now().isoformat(timespec="seconds")
        state["last_love_confession_text"] = user_text.strip()
        return 3.0

    # Обычный расчёт (без любовного бонуса)
    trust = state.get("trust", 0)
    comfort = state.get("comfort", 0)
    affection = state.get("affection", 0)
    anger = state.get("anger", 0)
    discomfort = state.get("discomfort", 0)

    if anger > 25 or discomfort > 30:
        return 0.0

    delta = 0.0
    if trust >= 20 and comfort >= 20:
        delta += 0.5
    if affection >= 30:
        delta += 0.5

    positive_markers = ["спасибо", "благодарю", "ценю", "рад", "нравится", "интересно", "расскажи", "поддержи"]
    if any(m in lowered for m in positive_markers):
        delta += 0.5

    if discomfort > 15:
        delta -= 1.0
    if anger > 15:
        delta -= 1.5

    return max(-3.0, min(3.0, delta))


def process_user_message(user_text: str) -> dict:
    """Анализирует сообщение и обновляет состояние отношений. Возвращает состояние."""
    state = load_relationship_state()
    events = load_emotional_events()

    state.setdefault("discomfort", 0)
    state.setdefault("loneliness", 0)

    lowered = user_text.lower().strip()

    # Сначала выполняем мгновенные реакции (handle_...)
    if any(phrase in lowered for phrase in ["люблю тебя", "я тебя люблю", "ты мне очень дорога", "люблю астру"]):
        handle_love_confession(state, events)

    elif any(phrase in lowered for phrase in ["ты моя умница", "ты молодец", "ты классная", "ты крутая"]):
        handle_compliment(state)

    if any(word in lowered for word in ["дура", "тупая", "плохая", "бесишь", "заткнись"]):
        handle_offense(state, events)

    _apology_fired = False
    if any(phrase in lowered for phrase in ["прости", "извини", "я был неправ", "не хотел обидеть"]):
        handle_apology(state, events)
        _apology_fired = True

    if any(phrase in lowered for phrase in ["спасибо", "благодарю", "ты мне помогла", "ценю"]):
        if not _apology_fired:
            handle_positive_action(state, events)

    # Автоматическое остывание
    if not any(trigger in lowered for trigger in [
        "люблю тебя", "я тебя люблю", "дура", "тупая", "прости", "извини", "спасибо", "благодарю"
    ]):
        state["anger"] = max(0, state["anger"] - 2)
        state["discomfort"] = max(0, state["discomfort"] - 2)

    # Автоматическая прогрессия relationship_depth
    delta = calculate_relationship_delta(state, lowered, user_text)
    old_depth = state["relationship_depth"]
    
    # Используем int(delta + 0.5) для правильного округления вверх при 0.5
    state["relationship_depth"] = max(0, min(999, state["relationship_depth"] + int(delta + 0.5)))

    if delta != 0:
        print(f"[RELATIONSHIP] depth: {old_depth} → {state['relationship_depth']} ({delta:+.1f})")

    apply_deployment_limit(state)

    save_relationship_state(state)
    save_emotional_events(events)

    return state

def get_current_state() -> dict:
    state = load_relationship_state()
    state["stage"] = get_stage(state["relationship_depth"])
    return state

def is_angry() -> bool:
    state = load_relationship_state()
    return state.get("flags", {}).get("angry_reaction", False)