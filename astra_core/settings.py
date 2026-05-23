import json
from pathlib import Path

# Автоматическое определение корневой папки проекта.
# settings.py лежит внутри astra_core/, поэтому .parent.parent указывает на корень репозитория.
# Работает на Windows, Linux и macOS без привязки к конкретному диску.
BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "ollama_url": "http://127.0.0.1:11434/api/generate",
    "model": "mistral-nemo",
    "tts_url": "http://127.0.0.1:7851/api/tts-generate",
    "tts_voice": "ru_RU-irina-medium.onnx",
    "mic_device": 20,
    "sample_rate": 48000,
    "push_to_talk_key": "num 7",
    "base_dir": str(BASE_DIR),
}

def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_SETTINGS.copy()
        
    settings = DEFAULT_SETTINGS.copy()
    settings.update(data)
    return settings

def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def get_setting(key: str, default=None):
    # Ленивый импорт – разрывает циклическую зависимость с model_params
    from .model_params import get_current_model, get_generation_params, get_memory_analyzer_params
    
    if key == "model":
        return get_current_model()
    if key == "generation_params":
        return get_generation_params()
    if key == "memory_analyzer_params":
        return get_memory_analyzer_params()
        
    return load_settings().get(key, default)