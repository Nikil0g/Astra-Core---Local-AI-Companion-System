from .prompt_builder import build_prompt
from .ollama_client import ask_ollama
from .conversation_manager import ConversationManager
from .short_term_memory import add_message
from .memory_engine import save_analyzed_memory
from .conversation_meta import mark_user_message, mark_astra_message
from .conversation_state import get_conversation_state
from .behavior_guard import apply_behavior_guard
from .response_filter import apply_response_filter
from .emotional_core import process_user_message
from .orchestrator import extract_fact


def remove_repeated_greeting(answer: str, recent_dialog: str) -> str:
    if not recent_dialog.strip():
        return answer
    
    greetings = [
        "Привет!", "Привет, ", "Здравствуй!", "Здравствуй, ",
        "Добрый день!", "Добрый день, ", "Приветствую!", "Приветствую, "
    ]
    cleaned = answer.strip()

    for greeting in greetings:
        if cleaned.startswith(greeting):
            cleaned = cleaned[len(greeting):].strip()
            break

    return cleaned


class AstraCore:
    def __init__(self):
        self.conversation = ConversationManager()

    def get_recent_dialog(self, limit: int = 12) -> str:
        return self.conversation.get_recent_dialog(limit)

    def reply(self, user_text: str) -> str:
        recent_dialog = self.get_recent_dialog()
        
        # Сначала обновляем эмоциональное состояние
        process_user_message(user_text)
        
        prompt = build_prompt(user_text, recent_dialog)

        # Параметры берутся из конфигурации/модуля ollama_client автоматически
        answer = ask_ollama(prompt)

        conversation_state = get_conversation_state()
        answer = apply_behavior_guard(answer, conversation_state)
        answer = remove_repeated_greeting(answer, recent_dialog)

        # Применяем response filter
        filtered = apply_response_filter(answer)
        if filtered is None:
            # Если фильтр забраковал ответ, запрашиваем модель заново
            retry_prompt = build_prompt(user_text, recent_dialog)
            retry_prompt += "\n\nВАЖНО: Отвечай естественно, как живой человек. Не используй ассистентские фразы. Не объясняй свою природу."
            answer = ask_ollama(retry_prompt)
            answer = apply_behavior_guard(answer, conversation_state)
            answer = remove_repeated_greeting(answer, recent_dialog)
            filtered = apply_response_filter(answer)
            if filtered is None:
                # Если и второй раз не вышло, используем резервный ответ
                filtered = "Я рада тебя видеть! Как дела?"
        answer = filtered

        mark_user_message()
        mark_astra_message()

        add_message("user", user_text)
        add_message("astra", answer)

        self.conversation.add_user_message(user_text)
        self.conversation.add_astra_message(answer)

        self.try_save_memory(user_text, answer)

        return answer

    def generate_initiative(self, situation: str) -> str:
        recent_dialog = self.get_recent_dialog()

        internal_request = f"""
[INTERNAL INITIATIVE REQUEST]
Это не сообщение пользователя.
Это внутренняя ситуация для Astra.
Ситуация:
{situation}
Задача:
Напиши пользователю первой короткое, естественное сообщение.
Не говори, что это системная инструкция.
Не упоминай internal request.
""".strip()

        prompt = build_prompt(
            user_text=internal_request,
            recent_dialog=recent_dialog,
        )
        answer = ask_ollama(prompt)
        answer = remove_repeated_greeting(answer, recent_dialog)

        mark_astra_message()

        add_message("astra", answer)
        self.conversation.add_astra_message(answer)

        return answer

    def try_save_memory(self, user_text: str, astra_answer: str) -> None:
        result = extract_fact(user_text)
        print("[MEMORY ANALYZER RESULT] ", repr(result))
        if result.startswith("FACT: "):
            text = result.replace("FACT: ", "").strip()
            save_analyzed_memory("FACT", text, source="terminal")
        # EVENT и DIARY пока не используем