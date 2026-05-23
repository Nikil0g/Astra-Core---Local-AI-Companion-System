import re
from .settings import get_setting

# --- Категории запрещённых фраз ---
IDENTITY_LEAKAGE_PHRASES = [
    r"я (всего лишь )?(искусственный интеллект|ИИ|AI|модель|бот|ассистент|программа|алгоритм)",
    r"я не (человек|живой|настоящий)",
    r"я (цифровое|виртуальное) (существо|создание)",
    r"у меня нет (тела|физического тела|органов чувств)",
    r"я не (могу|способна) (чувствовать|испытывать|ощущать)",
    r"мне не нужны (питательные вещества|еда|сон)",
    r"в традиционном понимании",
    r"как (у (нас|людей)|у живых существ)",
    r"я (существую|живу) (в цифровом|в виртуальном) (мире|пространстве)",
    r"я не провожу время в традиционном понимании",
]

ASSISTANT_PHRASES = [
    r"я здесь,? чтобы (помочь|помогать|поддерживать)",
    r"чем (я могу|могу я) (помочь|быть полезна)",
    r"я (всегда )?готова (помочь|прийти на помощь)",
    r"я (всегда )?здесь (для (вас|тебя)|ради (вас|тебя))",
    r"если (вам|тебе) (нужна|понадобится) (помощь|поддержка)",
    r"(пожалуйста, )?обращайтесь?( ко мне)?,? если (что|понадоблюсь)",
    r"я (всегда )?к (вашим|твоим) услугам",
]

GENDERED_TERMS = {
    "male": {
        "дорогая": "дорогой",
        "милая": "милый",
        "любимая": "любимый",
        "хорошая": "хороший",
        "умница": "умник",
        "красавица": "красавец",
        "подруга": "друг",
    },
    "female": {
        "дорогой": "дорогая",
        "милый": "милая",
        "любимый": "любимая",
        "хороший": "хорошая",
        "умник": "умница",
        "красавец": "красавица",
        "друг": "подруга",
    },
    "neutral": {},
}

# --- Вспомогательные функции ---
def has_identity_leakage(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(phrase, lowered) for phrase in IDENTITY_LEAKAGE_PHRASES)

def has_assistant_phrase(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(phrase, lowered) for phrase in ASSISTANT_PHRASES)

def fix_gender_terms(text: str) -> str:
    """Исправляет обращения в зависимости от user_gender_grammar"""
    user_gender = get_setting("user_gender_grammar", "unknown")
    
    if user_gender == "unknown":
        for term in list(GENDERED_TERMS["male"].keys()) + list(GENDERED_TERMS["female"].keys()):
            text = re.sub(rf"\b{re.escape(term)}\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r",\s*,", ",", text)
        return text.strip()

    if user_gender in GENDERED_TERMS:
        mapping = GENDERED_TERMS[user_gender]
        for wrong, right in mapping.items():
            text = re.sub(rf"\b{re.escape(wrong)}\b", right, text, flags=re.IGNORECASE)
    return text

def fix_ty_vy_mix(text: str) -> str:
    """Заменяет 'вы' на 'ты', если в сообщении уже есть 'ты'"""
    if re.search(r"\bты\b", text, re.IGNORECASE):
        text = re.sub(r"\bвас\b", "тебя", text, flags=re.IGNORECASE)
        text = re.sub(r"\bвам\b", "тебе", text, flags=re.IGNORECASE)
    return text

def apply_response_filter(answer: str) -> str:
    """
    Применяет правила фильтрации к ответу Astra.
    Вызывается после behavior_guard.
    """
    filtered = answer.strip()
    
    # 1. Исправляем гендерные обращения
    filtered = fix_gender_terms(filtered)
    # 2. Фиксим смесь ты/вы (если проскочило)
    filtered = fix_ty_vy_mix(filtered)
    # 3. Убираем двойные пробелы, чистим края
    filtered = re.sub(r"\s+", " ", filtered)
    filtered = filtered.strip(" ,.")
    
    # 4. Проверяем identity leakage — если есть, помечаем для перегенерации
    if has_identity_leakage(filtered):
        return None
    # 5. Проверяем ассистентские фразы — блокируем
    if has_assistant_phrase(filtered):
        return None
        
    # ⚠️ Мат и резкие выражения НЕ фильтруются намеренно.
    # Это позволяет гневным/эмоциональным ответам проходить без изменений.
    return filtered