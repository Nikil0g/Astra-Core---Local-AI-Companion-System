import requests
from .settings import get_setting
from .model_params import get_current_model, get_generation_params

def ask_ollama(
    prompt: str,
    model: str = None,
    temperature: float = None,
    top_p: float = None,
    num_predict: int = None,
    num_ctx: int = None,
    repeat_penalty: float = None,
) -> str:
    # Если model не передан явно — берём из настроек
    if model is None:
        model = get_current_model()
    params = get_generation_params()

    if not isinstance(params, dict):
        params = {}

    temp  = temperature    if temperature    is not None else params.get("temperature",    1.0)
    top   = top_p          if top_p          is not None else params.get("top_p",          0.9)
    pred  = num_predict    if num_predict    is not None else params.get("num_predict",    160)
    ctx   = num_ctx        if num_ctx        is not None else params.get("num_ctx",       8192)
    rpen  = repeat_penalty if repeat_penalty is not None else params.get("repeat_penalty", 1.0)

    url = get_setting("ollama_url")

    payload = {
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature":    temp,
            "top_p":          top,
            "num_predict":    pred,
            "num_ctx":        ctx,
            "repeat_penalty": rpen,
        },
    }

    print(f"[DEBUG ollama_client] Using model: {model!r}")
    print(f"[DEBUG ollama_client] → model={model!r} temp={temp} top_p={top} "
          f"num_predict={pred} num_ctx={ctx}")

    response = requests.post(url, json=payload, timeout=120)

    if response.status_code != 200:
        print(f"[ERROR ollama_client] {response.status_code}: {response.text}")
    response.raise_for_status()

    result = response.json().get("response", "").strip()
    print(f"[DEBUG ollama_client] ← preview: {repr(result[:120])}")
    return result