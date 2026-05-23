from pathlib import Path
from .settings import get_setting

BASE_DIR = Path(get_setting("base_dir"))
CORE_SELF_DIR = BASE_DIR / "character" / "core_self"


CORE_FILES = {
    "identity": "identity.txt",
    "personality": "personality.txt",
    "speech_style": "speech_style.txt",
    "boundaries": "boundaries.txt",
    "innate_likes": "innate_likes.txt",
    "innate_dislikes": "innate_dislikes.txt",
}


def read_text_file(path: Path) -> str:
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8").strip()


def get_character_name() -> str:
    identity_path = CORE_SELF_DIR / "identity.txt"
    content = read_text_file(identity_path)

    for line in content.splitlines():
        line = line.strip()

        if line.lower().startswith("имя персонажа:"):
            name = line.split(":", 1)[1].strip()

            if name:
                return name

    return "Astra"


def build_core_self_block() -> str:
    parts = ["[CORE SELF]"]

    for section_name, filename in CORE_FILES.items():
        path = CORE_SELF_DIR / filename
        content = read_text_file(path)

        if not content:
            continue

        parts.append(f"\n# {section_name.upper()}")
        parts.append(content)

    parts.append("[/CORE SELF]")

    return "\n".join(parts)