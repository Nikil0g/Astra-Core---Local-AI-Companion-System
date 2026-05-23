import json
from pathlib import Path

from .settings import get_setting
from .ollama_client import ask_ollama
from .memory_engine import add_memory, memory_exists, is_semantic_duplicate
from .conversation_meta import get_conversation_meta, parse_iso


CONVERSATION_STATE_FILE = Path(get_setting("base_dir")) / "conversation_state.json"


def load_recent_session_messages(limit: int = 60) -> list[dict]:
    if not CONVERSATION_STATE_FILE.exists():
        return []

    try:
        state = json.loads(CONVERSATION_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    messages = state.get("messages", [])

    if not isinstance(messages, list):
        return []

    meta = get_conversation_meta()
    session_started_at = parse_iso(meta.get("session_started_at"))

    if session_started_at is None:
        return messages[-limit:]

    current_session_messages = []

    for msg in messages:
        created_at = parse_iso(msg.get("created_at"))

        if created_at is None:
            continue

        if created_at >= session_started_at:
            current_session_messages.append(msg)

    return current_session_messages[-limit:]


def format_messages_for_analysis(messages: list[dict]) -> str:
    lines = []

    for msg in messages:
        role = msg.get("role", "unknown")
        text = msg.get("text", "").strip()
        created_at = msg.get("created_at", "")

        if not text:
            continue

        lines.append(f"{created_at} | {role}: {text}")

    return "\n".join(lines)


def is_useless_session_memory(text: str) -> bool:
    lowered = text.strip().lower()

    useless_phrases = [
        "не было принято никаких решений",
        "решений не было",
        "не было решений",
        "пользователь общался с astra",
        "пользователь задавал вопросы",
        "пользователь спрашивал о себе",
        "в ходе сессии пользователь общался",
        # приветствия
        "пользователь приветствовал",
        "пользователь поприветствовал",
        "упомянул, что он здесь",
        "упомянул, что вернулся",
        "сказал, что он тут",
        "просто поздоровался",
        "сессия началась с приветствия",
        "пользователь зашёл и поздоровался",
        "пользователь написал «привет»",
        "пользователь появился и поздоровался",
        # новые шаблоны для summary-мусора
        "пользователь поделился",
        "пользователь рассказал",
        "пользователь упомянул",
        "в ходе диалога",
        "в ходе общения",
        "в рамках сессии",
        "обсуждалось",
        "затрагивалось",
        "говорилось о",
        "пользователь выразил",
        "пользователь отметил",
    ]

    return any(phrase in lowered for phrase in useless_phrases)


def parse_session_analysis(result: str) -> list[tuple[str, str]]:
    """
    Expected lines:
    SESSION_SUMMARY: ...
    PROJECT_DECISION: ...
    RELATIONSHIP: ...
    MOOD: ...
    NONE
    """
    result = result.strip()

    if not result or result.upper() == "NONE":
        return []

    parsed = []

    for raw_line in result.splitlines():
        line = raw_line.strip()

        if not line or line.upper() == "NONE":
            continue

        if line.upper().endswith(": NONE"):
            continue

        if line.startswith("SESSION_SUMMARY:"):
            text = line.replace("SESSION_SUMMARY:", "").strip()
            if text and text.upper() != "NONE" and not is_useless_session_memory(text):
                parsed.append(("session_summary", text))

        elif line.startswith("PROJECT_DECISION:"):
            text = line.replace("PROJECT_DECISION:", "").strip()
            if text and text.upper() != "NONE" and not is_useless_session_memory(text):
                parsed.append(("project_decision", text))

        elif line.startswith("RELATIONSHIP:"):
            text = line.replace("RELATIONSHIP:", "").strip()
            if text and text.upper() != "NONE" and not is_useless_session_memory(text):
                parsed.append(("relationship", text))

        elif line.startswith("MOOD:"):
            text = line.replace("MOOD:", "").strip()
            if text and text.upper() != "NONE" and not is_useless_session_memory(text):
                parsed.append(("mood", text))

    return parsed


def analyze_current_session(limit: int = 60) -> list[dict]:
    messages = load_recent_session_messages(limit=limit)

    if len(messages) < 5:
        print("[SESSION ANALYZER] Недостаточно сообщений для анализа.")
        return []

    dialog = format_messages_for_analysis(messages)

    if not dialog.strip():
        print("[SESSION ANALYZER] Пустой диалог.")
        return []

    prompt = f"""
Ты модуль анализа сессии Astra.

Твоя задача — найти важные итоги всей сессии, а не отдельные сухие факты.

ВАЖНО:
Quick memory analyzer уже сохраняет конкретные факты пользователя.
Ты НЕ должен дублировать атомарные факты вроде:
- Пользователь любит гранатовый чай.
- Пользователя зовут Никита.
- Пользователь любит synthwave.
- Любимый цвет пользователя — фиолетовый.

КРИТИЧНО:
- Не используй прошлую память, примеры или знания вне текущего диалога.
- Анализируй только текст в блоке "Диалог сессии".
- Если в диалоге нет прямого эмоционального выражения — не создавай RELATIONSHIP или MOOD.
- Лучше сохранить меньше, чем придумать лишнее.

КРИТИЧНО:
Не сохраняй обычное описание того, что пользователь просто задавал вопросы.
Не сохраняй summary, если в сессии не было важного прогресса, решения, эмоционального момента или новой идеи.
Не сохраняй строки вроде:
- "Пользователь общался с Astra"
- "Пользователь задавал вопросы"
- "Пользователь спрашивал о себе"
- "Не было принято решений"
- "Решений не было"

Если решений по проекту не было — не пиши PROJECT_DECISION вообще или пиши PROJECT_DECISION: NONE.
Если сессия была обычным тестом без важного вывода — ответь NONE.
Лучше сохранить ничего, чем записать бесполезный итог.

Сохраняй только:
- краткий итог сессии;
- важные решения по проекту;
- важные эмоциональные моменты;
- повторяющиеся темы, которые важны для отношений или поведения Astra;
- состояние пользователя, если оно явно проявлялось в течение сессии.

Не выдумывай.
Не усиливай отношения искусственно.
Не пиши, что отношения романтические, если это прямо не следует из сессии.
Не сохраняй обычный small talk.
Не сохраняй технический мусор.
Не сохраняй отдельные preference facts — их сохраняет быстрый анализатор.

Форматы ответа, каждая строка отдельно:

SESSION_SUMMARY: ...
PROJECT_DECISION: ...
RELATIONSHIP: ...
MOOD: ...
NONE

Не копируй примеры и не используй их как факты.
Примеры ниже показывают только формат, а не содержание текущей сессии.

Формат:
SESSION_SUMMARY: краткий нейтральный итог того, что реально обсуждалось
PROJECT_DECISION: конкретное решение, которое пользователь явно принял
RELATIONSHIP: только явно выраженный эмоционально значимый момент между пользователем и Astra
MOOD: только явно выраженное настроение пользователя

RELATIONSHIP и MOOD сохраняй только если пользователь прямо выразил эмоцию или отношение.
Если эмоция не была явно сказана — не добавляй RELATIONSHIP или MOOD.

Если важных итогов нет — ответь NONE.

Диалог сессии:
{dialog}
""".strip()

    result = ask_ollama(
        prompt,
        temperature=0.2,
        top_p=0.8,
        num_predict=300,
    )

    print("[SESSION ANALYZER RESULT]")
    print(result)

    parsed = parse_session_analysis(result)
    saved_memories = []

    for memory_type, text in parsed:
        if not text:
            continue

        # semantic duplicate protection
        if is_semantic_duplicate(text):
            continue

        # exact duplicate protection
        if memory_exists(text):
            continue

        if memory_type == "session_summary":
            importance = 6
            owner = "system"
            expires_days_type = "session_summary"

        elif memory_type == "project_decision":
            importance = 8
            owner = "system"
            expires_days_type = "project_decision"

        elif memory_type == "relationship":
            importance = 8
            owner = "user"
            expires_days_type = "relationship"

        elif memory_type == "mood":
            importance = 4
            owner = "user"
            expires_days_type = "mood"

        else:
            importance = 3
            owner = "system"
            expires_days_type = "temporary"

        saved = add_memory(
            text=text,
            owner=owner,
            memory_type=expires_days_type,
            importance=importance,
            confidence=0.8,
            source="session_analyzer",
        )

        if saved:
            saved_memories.append(saved)

    print(f"[SESSION ANALYZER] Saved memories: {len(saved_memories)}")
    return saved_memories


if __name__ == "__main__":
    analyze_current_session()