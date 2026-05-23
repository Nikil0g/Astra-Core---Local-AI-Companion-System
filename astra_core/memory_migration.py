from pathlib import Path

from .config import MEMORY_FACTS, MEMORY_EVENTS, DIARY
from .memory_engine import save_analyzed_memory, memory_exists


def read_clean_lines(path: Path) -> list[str]:
    if not path.exists():
        return []

    lines = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line:
            continue

        if line.upper() == "NONE":
            continue

        lines.append(line)

    return lines


def migrate_facts() -> int:
    count = 0
    lines = read_clean_lines(MEMORY_FACTS)

    for line in lines:
        if memory_exists(line, owner="user"):
            continue

        saved = save_analyzed_memory(
            kind="FACT",
            text=line,
            source="migration_txt_facts",
        )

        if saved:
            count += 1

    return count


def migrate_events() -> int:
    count = 0
    lines = read_clean_lines(MEMORY_EVENTS)

    for line in lines:
        saved = save_analyzed_memory(
            kind="EVENT",
            text=line,
            source="migration_txt_events",
        )

        if saved:
            count += 1

    return count


def migrate_diary() -> int:
    count = 0
    lines = read_clean_lines(DIARY)

    for line in lines:
        saved = save_analyzed_memory(
            kind="DIARY",
            text=line,
            source="migration_txt_diary",
        )

        if saved:
            count += 1

    return count


def migrate_all() -> None:
    facts_count = migrate_facts()
    events_count = migrate_events()
    diary_count = migrate_diary()

    print("Memory migration complete.")
    print(f"Facts migrated: {facts_count}")
    print(f"Events migrated: {events_count}")
    print(f"Diary migrated: {diary_count}")


if __name__ == "__main__":
    migrate_all()