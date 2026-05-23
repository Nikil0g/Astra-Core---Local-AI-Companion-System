import re
from .ollama_client import ask_ollama
from .settings import get_setting

def extract_fact(user_text: str) -> str:
    # ----- 1. Быстрый префильтр -----
    markers = ["я ", "меня ", "мне ", "моё ", "мой ", "у меня", "я."]
    if not any(m in user_text.lower() for m in markers) or len(user_text.split()) < 3:
        return "NONE"

    # ----- 2. Очистка от слов-паразитов (для улучшения работы регулярок) -----
    cleaned = re.sub(r'\b(вот|ну|так|просто|конечно|вообще|очень|типа|прямо|как бы|наверное)\s+', ' ', user_text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # ----- 3. Регулярные выражения (приоритет) -----
    patterns = [
        (r"меня зовут\s+([А-Яа-яA-Za-z][А-Яа-яA-Za-z\s]+?)(?:[.,!?]|$)", "Пользователя зовут {}"),
        (r"моё имя\s+([А-Яа-яA-Za-z][А-Яа-яA-Za-z\s]+?)(?:[.,!?]|$)", "Пользователя зовут {}"),
        (r"моя фамилия\s+([А-Яа-яA-Za-z][А-Яа-яA-Za-z\s]+?)(?:[.,!?]|$)", "Фамилия пользователя {}"),
        (r"я\s+люблю\s+(.+?)(?:[.,!?]|$)", "Пользователь любит {}"),
        (r"я\s+обожаю\s+(.+?)(?:[.,!?]|$)", "Пользователь обожает {}"),
        (r"мне\s+нравится\s+(.+?)(?:[.,!?]|$)", "Пользователю нравится {}"),
        (r"я\s+играю\s+в\s+(.+?)(?:[.,!?]|$)", "Пользователь играет в {}"),
        (r"я\s+работаю\s+(.+?)(?:[.,!?]|$)", "Пользователь работает {}"),
        (r"у меня есть\s+(.+?)(?:[.,!?]|$)", "У пользователя есть {}"),
        (r"я\s+хочу\s+(.+?)(?:[.,!?]|$)", "Пользователь хочет {}"),
        (r"я\s+не\s+люблю\s+(.+?)(?:[.,!?]|$)", "Пользователь не любит {}"),
    ]
    for pattern, template in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            fact_text = template.format(match.group(1).strip())
            return f"FACT: {fact_text}"

    # ----- 4. Если регулярки не сработали, пробуем LLM (если включён) -----
    orch_enabled = get_setting("orchestrator_enabled", True)
    if not orch_enabled:
        return "NONE"

    model = get_setting("orchestrator_model", "phi3:mini")
    orch_params = get_setting("orchestrator_params", {})
    temp = orch_params.get("temperature", 0.0)
    top_p = orch_params.get("top_p", 0.8)
    num_predict = orch_params.get("num_predict", 50)

    prompt = f"""Ты извлекаешь факты о пользователе. Сообщение: {user_text}

Если пользователь явно сообщает о себе информацию (имя, предпочтение, действие), ответь FACT: текст, начиная с "Пользователь ...". Иначе NONE.
Не добавляй ничего, кроме FACT: ... или NONE.

Примеры:
"я люблю пить колу" → FACT: Пользователь любит пить колу.
"меня зовут Никита" → FACT: Пользователя зовут Никита.
"я вот люблю ромашки" → FACT: Пользователь любит ромашки.
"моя фамилия Логинов" → FACT: Фамилия пользователя Логинов.
"привет" → NONE
"ты кто?" → NONE

Твой ответ:"""
    result = ask_ollama(prompt, model=model, temperature=temp, top_p=top_p, num_predict=num_predict)
    result = result.strip().splitlines()[0].strip()
    # Исправляем возможное двойное "FACT: FACT:"
    if result.startswith("FACT: FACT:"):
        result = result.replace("FACT: FACT:", "FACT:", 1).strip()
    # Проверка формата
    if not (result.startswith("FACT: ") or result == "NONE"):
        result = "NONE"

    # ----- 5. Пост-валидация для FACT: проверяем пересечение ключевых слов -----
    if result.startswith("FACT: "):
        fact_text = result[6:].lower()
        user_lower = user_text.lower()
        # Извлекаем значащие слова из сообщения пользователя (длина >=4)
        user_words = set(re.findall(r'\b[а-яёa-z]{4,}\b', user_lower))
        if user_words:
            # Хотя бы одно слово должно быть в факте
            if not any(word in fact_text for word in user_words):
                result = "NONE"
    return result