import json
from datetime import datetime
from pathlib import Path
from .settings import get_setting

ACTIVITY_FILE = (
    Path(get_setting("base_dir")) / "astra_activity.json"
)

# TODO:
# Future presence system:
# - absence levels
# - conversation state
# - loneliness system
# - emotional initiative triggers
# - relationship-aware initiative
# - time-of-day behavior

def touch_user_activity(source: str = "unknown") -> None:
    data = {
        "last_user_interaction": datetime.now().isoformat(),
        "source": source,
    }

    ACTIVITY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def minutes_since_last_user_activity() -> float | None:
    if not ACTIVITY_FILE.exists():
        return None

    try:
        data = json.loads(ACTIVITY_FILE.read_text(encoding="utf-8"))
        raw_time = data.get("last_user_interaction")

        if not raw_time:
            return None

        last_time = datetime.fromisoformat(raw_time)
        return (datetime.now() - last_time).total_seconds() / 60

    except Exception:
        return None