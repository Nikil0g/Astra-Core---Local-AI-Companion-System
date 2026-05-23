import time
import random
from datetime import datetime

from win10toast import ToastNotifier
from astra_core.core import AstraCore
from astra_core.short_term_memory import add_message
from astra_core.conversation_meta import mark_astra_message, get_conversation_meta
from astra_core.memory_engine import save_analyzed_memory
from astra_core.settings import get_setting
from astra_core.character_profile import get_character_name
from astra_core.conversation_manager import ConversationManager
from astra_core.activity import minutes_since_last_user_activity

toaster = ToastNotifier()
CHARACTER_NAME = get_character_name()
MIN_SILENCE_MINUTES = 1

SITUATIONS = [
    "Напиши пользователю первой. Он давно молчит. Сообщение должно быть коротким, живым и естественным.",
    "Спроси у пользователя, как проходит его день.",
    "Мягко напомни пользователю отдохнуть.",
    "Напиши пользователю что-то тёплое, будто ты немного соскучилась.",
    "Слегка подразни пользователя, что он пропал.",
]

def get_last_user_message_time() -> datetime | None:
    """Получает время последнего сообщения пользователя напрямую из conversation_meta."""
    meta = get_conversation_meta()
    last = meta.get("last_user_message_at")
    if last:
        try:
            return datetime.fromisoformat(last)
        except Exception:
            pass
    return None

def user_is_silent_enough() -> bool:
    """Проверяет, прошло ли достаточно времени тишины со стороны пользователя."""
    last_time = get_last_user_message_time()
    if not last_time:
        return True

    seconds_since_msg = (datetime.now() - last_time).total_seconds()
    minutes_since_msg = seconds_since_msg / 60.0

    try:
        minutes_act = minutes_since_last_user_activity()
    except Exception:
        minutes_act = 999.0

    final_minutes = min(minutes_since_msg, minutes_act)
    return final_minutes >= MIN_SILENCE_MINUTES

def main() -> None:
    print(f"[INITIATIVE] Скрипт инициативности {CHARACTER_NAME} запущен.")
    print(f"[INITIATIVE] Требуемое время тишины: {MIN_SILENCE_MINUTES} мин.")

    astra = AstraCore()
    conv_manager = ConversationManager()

    while True:
        try:
            time.sleep(60)

            if not user_is_silent_enough():
                print("[INITIATIVE] Пользователь недавно проявлял активность. Не беспокою.")
                continue

            situation = random.choice(SITUATIONS)
            message = astra.generate_initiative(situation)

            if not message:
                continue

            print(f"{CHARACTER_NAME}: {message}")

            # Замена write_astra на новую систему памяти и фиксацию метаданных
            add_message("astra", message)
            mark_astra_message()
            conv_manager.add_astra_message(message)

            try:
                toaster.show_toast(
                    CHARACTER_NAME,
                    message,
                    duration=10,
                    threaded=True,
                )
            except Exception as e:
                print("[TOAST ERROR]", e)

            # Логируем инициативное действие в локальный дневник Astra
            save_analyzed_memory(
                "DIARY",
                f"{CHARACTER_NAME} wrote first: {message}",
                source="initiative"
            )

        except KeyboardInterrupt:
            print("\nAstraCore Initiative остановлена.")
            break
        except Exception as e:
            print("Ошибка инициативности:", e)

if __name__ == "__main__":
    main()