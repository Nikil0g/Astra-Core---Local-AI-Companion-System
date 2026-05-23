from astra_core.core import AstraCore
from astra_core.activity import touch_user_activity
from astra_core.character_profile import get_character_name
from astra_core.settings import get_setting
from astra_core.conversation_meta import start_new_session, close_current_session
from astra_core.session_analyzer import analyze_current_session


def main():
    astra = AstraCore()
    start_new_session()

    character_name = get_character_name()
    user_name = get_setting("user_name", "User")

    print(f"{character_name} Core v0.1 запущена.")
    print("Напиши exit для выхода.\n")

    while True:
        user_text = input("Ты: ").strip()
        touch_user_activity("terminal")

        if not user_text:
            continue

        if user_text.lower() in {"exit", "quit", "выход"}:
            analyze_current_session()
            from astra_core.memory_cleanup import cleanup_memory_store
            cleanup_memory_store()  # удалит точные/битые дубли сразу после анализа
            close_current_session()
            print(f"{character_name}: я буду рядом, {user_name}.")
            break

        try:
            answer = astra.reply(user_text)
            print(f"{character_name}: {answer}\n")
        except Exception as e:
            print("Ошибка AstraCore:", e)


if __name__ == "__main__":
    main()