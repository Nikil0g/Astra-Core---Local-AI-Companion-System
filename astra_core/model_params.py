import json
from pathlib import Path
from .settings import BASE_DIR

def _load_settings():
    path = BASE_DIR / "settings.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_current_model():
    s = _load_settings()
    return s.get("current_model") or s.get("model", "")

def get_generation_params():
    s = _load_settings()
    current = get_current_model()
    presets = s.get("model_presets")
    
    result = {"temperature": 0.8, "top_p": 0.9, "num_predict": 256, "num_ctx": 8192, "repeat_penalty": 1.1}
    
    if isinstance(presets, dict) and current in presets:
        preset = presets[current]
        if isinstance(preset, dict):
            params = preset.get("generation_params")
            if isinstance(params, dict):
                result = params
    else:
        # fallback
        fallback = s.get("generation_params")
        if isinstance(fallback, dict):
            result = fallback
            
    print(f"[DEBUG model_params] get_generation_params returns type={type(result)}, value={result}")
    return result

def get_memory_analyzer_params():
    s = _load_settings()
    current = get_current_model()
    presets = s.get("model_presets")
    
    result = {"temperature": 0.1, "top_p": 0.8, "num_predict": 100}
    
    if isinstance(presets, dict) and current in presets:
        preset = presets[current]
        if isinstance(preset, dict):
            params = preset.get("memory_analyzer_params")
            if isinstance(params, dict):
                result = params
    else:
        fallback = s.get("memory_analyzer_params")
        if isinstance(fallback, dict):
            result = fallback
            
    print(f"[DEBUG model_params] get_memory_analyzer_params returns type={type(result)}, value={result}")
    return result