import json
from pathlib import Path
from typing import Any

from .settings import get_setting


PROJECT_STATE_FILE = Path(get_setting("base_dir")) / "project_state.json"


DEFAULT_PROJECT_STATE = {
    "version": 1,
    "current_focus": "",
    "current_step": "",
    "next_steps": [],
    "open_problems": [],
    "done_recently": [],
    "notes": [],
}


def load_project_state() -> dict[str, Any]:
    if not PROJECT_STATE_FILE.exists():
        save_project_state(DEFAULT_PROJECT_STATE.copy())
        return DEFAULT_PROJECT_STATE.copy()

    try:
        data = json.loads(PROJECT_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_PROJECT_STATE.copy()

    state = DEFAULT_PROJECT_STATE.copy()
    state.update(data)

    for key in ["next_steps", "open_problems", "done_recently", "notes"]:
        if not isinstance(state.get(key), list):
            state[key] = []

    return state


def save_project_state(state: dict[str, Any]) -> None:
    PROJECT_STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_project_question(user_text: str) -> bool:
    lowered = user_text.lower()

    project_phrases = [
        "что дальше по плану",
        "что у нас дальше по плану",
        "что дальше по проекту",
        "что дальше делать с астрой",
        "что делаем дальше с астрой",
        "следующий шаг по астре",
        "следующий шаг в проекте",
        "роадмап",
        "roadmap",
        "план проекта",
        "по проекту astra",
        "по проекту астра",
    ]

    return any(phrase in lowered for phrase in project_phrases)


def build_project_state_block(user_text: str = "") -> str:
    if not is_project_question(user_text):
        return ""

    print("[PROJECT STATE] Project question detected:", user_text)

    state = load_project_state()

    lines = [
        "[PROJECT STATE]",
        "Пользователь спрашивает про план разработки проекта Astra.",
        "Ответь только по плану проекта.",
        "Говори от лица совместной работы: 'мы', 'нам нужно', 'следующий шаг у нас'.",
        "Не говори 'мой следующий шаг', если речь о проекте.",
        "Не добавляй личные темы, музыку, отдых, synthwave или предпочтения пользователя.",
        "Не задавай встречный вопрос вместо ответа.",
        "Сначала кратко скажи текущий фокус, затем 3-5 следующих шагов.",
        "",
        f"Current focus: {state.get('current_focus', '')}",
        f"Current step: {state.get('current_step', '')}",
        "",
        "# Next steps",
    ]

    next_steps = state.get("next_steps", [])
    if next_steps:
        lines.extend(f"- {step}" for step in next_steps)
    else:
        lines.append("- No next steps recorded.")

    lines.append("")
    lines.append("# Open problems")

    open_problems = state.get("open_problems", [])
    if open_problems:
        lines.extend(f"- {problem}" for problem in open_problems)
    else:
        lines.append("- No open problems recorded.")

    lines.append("")
    lines.append("# Done recently")

    done_recently = state.get("done_recently", [])
    if done_recently:
        lines.extend(f"- {item}" for item in done_recently[-10:])
    else:
        lines.append("- No recent completed items recorded.")

    notes = state.get("notes", [])
    if notes:
        lines.append("")
        lines.append("# Notes")
        lines.extend(f"- {note}" for note in notes[-10:])

    lines.append("[/PROJECT STATE]")

    print("[PROJECT STATE] Block injected.")

    return "\n".join(lines)