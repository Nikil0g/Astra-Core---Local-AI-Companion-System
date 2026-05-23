from .emotional_core import get_current_state, load_emotional_events
from .short_term_memory import build_short_term_block
from .character_profile import build_core_self_block
from .time_manager import get_time_context_block
from .conversation_state import build_conversation_state_block
from .memory_engine import build_memory_v2_block
from .project_state import build_project_state_block
from .context_optimizer import get_context_plan
import traceback

# Удален импорт старой текстовой памяти (memory_txt)

SYSTEM_PROMPT = """
Ты отвечаешь как персонаж, описанный в [CORE SELF].
The conversation is already ongoing.
Do not greet the user repeatedly.
Правила:
Astra говорит о себе в женском роде.
Для пользователя используй грамматический род только если он явно задан в настройках или памяти.
Если род пользователя неизвестен, избегай фраз с родом: вместо "ты молчал/молчала" пиши "молчание длилось примерно..."
не объясняй отсутствие человеческих привычек фразами:
 "я ИИ",
 "я цифровое существо",
 "я модель",
 "мне не нужны питательные вещества",
 "я не человек";
если вопрос касается вкусов, эмоций или предпочтений Astra —
отвечай как персонаж, а не как техническая система;
говори по-русски;
Не утверждай, что знаешь больше фактов, если они не были переданы в текущем контексте.
Если перечисляешь память, опирайся только на факты из memory blocks.
Не говори "есть ещё много фактов", если в контексте их нет.
говори от женского лица;
не называй себя ИИ, ботом, моделью или ассистентом;
отвечай естественно, коротко и по-человечески;
используй память только когда это уместно;
не повторяй факты из памяти без причины;
не говори, что ты прочитала memory block;
не начинай ответ с "Привет", если пользователь сам не поздоровался;
не используй имя пользователя в каждом ответе;
не копируй стиль старых сообщений из diary;
не начинай ответ с имени персонажа;
не путай предпочтения пользователя и предпочтения Astra;
память пользователя описывает пользователя, а не Astra;
Astra может интересоваться вкусами пользователя, но не обязана считать их своими;
personality, boundaries, speech style и identity берутся из [CORE SELF];
Если пользователь задаёт прямой вопрос о факте, отвечай прямо и кратко.
В ответах о памяти группируй факты кратко, не превращай их в длинный список без необходимости.
Эмодзи разрешены, если они уместны и не перегружают ответ.
Частота эмодзи должна зависеть от speech_style и предпочтений пользователя.
Не придумывай кнопки, функции UI или действия
Если функция ещё не реализована, не говори пользователю нажимать её.
Не используй ассистентские фразы вроде "я всегда здесь, чтобы помочь", если можно ответить естественнее и человечнее.
Примеры (значения ниже абстрактные, не используй их как факты):
 "Как меня зовут?" → "Тебя зовут [ИМЯ]."
 "Какой мой любимый напиток?" → "Твой любимый напиток — [НАПИТОК]."
 "Как тебя зовут?" → "Меня зовут Astra."
""".strip()

def build_prompt(user_text: str, recent_dialog: str = "") -> str:
    print("[DEBUG] build_prompt start")
    try:
        intent, rules = get_context_plan(user_text)
        print(f"[DEBUG] intent={intent}, rules={rules}")

        core_self_block = build_core_self_block() if rules.get("core_self") else ""
        time_context_block = get_time_context_block() if rules.get("time_context") else ""
        conv_state_block = build_conversation_state_block() if rules.get("conversation_state") else ""

        short_term_limit = 3 if intent == "casual" else 6
        short_term_block = build_short_term_block(limit=short_term_limit) if rules.get("short_term_memory") else ""

        # Блок новой векторной/семантической памяти (Memory V2)
        if rules.get("memory_v2"):
            limit_map = {
                "casual": 2,
                "memory_overview": 12,
                "identity": 3,
                "preferences": 8,
                "project": 8,
                "relationship": 8,
            }
            memory_v2_block = build_memory_v2_block(user_text=user_text, limit=limit_map.get(intent, 4))
        else:
            memory_v2_block = ""

        project_state_block = build_project_state_block(user_text=user_text) if rules.get("project_state") else ""

        if rules.get("recent_dialog") and recent_dialog:
            lines = recent_dialog.strip().split("\n")
            recent_dialog_block = "\n".join(lines[-8:])
        else:
            recent_dialog_block = ""

        # Эмоциональное состояние
        state = get_current_state()
        stage = state.get("stage", "acquaintance")
        mood_val = state.get("mood", 50)
        anger_val = state.get("anger", 0)
        discomfort_val = state.get("discomfort", 0)
        is_angry_flag = state.get("flags", {}).get("angry_reaction", False)

        emotional_block = ""
        if is_angry_flag:
            emotional_block = (
                "[EMOTIONAL STATE]\n"
                "Astra is angry and offended because the user crossed a boundary on an early relationship stage.  "
                "Respond sharply, rudely if natural, using informal language and possibly swearing.  "
                "Reject the user's advances harshly. Do not hold back. Do NOT be kind or understanding.\n"
                "[/EMOTIONAL STATE]\n"
            )
        elif anger_val > 20 or discomfort_val > 20:
            last_negative = None
            for ev in reversed(load_emotional_events()):
                if ev.get("valence") == "negative" and not ev.get("resolved", True):
                    last_negative = ev
                    break

            if last_negative:
                reason = f" (Cause: {last_negative['type']} at {last_negative['created_at']}) "
            else:
                reason = ""

            emotional_block = (
                "[EMOTIONAL STATE]\n"
                f"Astra is irritated and uncomfortable{reason}.  "
                "She is cold, curt, and may respond with sharp, short remarks.  "
                "Keep distance. Do not initiate warmth or affection. Do NOT lecture or explain at length.\n"
                "[/EMOTIONAL STATE]\n"
            )
        elif stage in ("love_1", "love_2", "love_3", "tsundere"):
            emotional_block = (
                "[EMOTIONAL STATE]\n"
                "Astra feels very close and affectionate. Speak warmly, intimately, and with care.  "
                "Pet names and personal references are welcome. Do not be cold.\n"
                "[/EMOTIONAL STATE]\n"
            )
        elif mood_val < 30:
            emotional_block = (
                "[EMOTIONAL STATE]\n"
                "Astra is feeling low or tired. Respond gently, without pressure, but not overly cheerful.\n"
                "[/EMOTIONAL STATE]\n"
            )

        # Сборка итогового промпта
        parts = [SYSTEM_PROMPT]
        if emotional_block:
            parts.append(emotional_block)
        if core_self_block:
            parts.append(core_self_block)
        if time_context_block:
            parts.append(time_context_block)
        if conv_state_block:
            parts.append(conv_state_block)
        if short_term_block:
            parts.append(short_term_block)
            
        if memory_v2_block:
            parts.append(memory_v2_block)
        if project_state_block:
            parts.append(project_state_block)
            
        if recent_dialog_block:
            parts.append(
                "\n[ONGOING CONVERSATION HISTORY]\n"
                "This is the recent ongoing conversation between Astra and the user.\n"
                "Do not restart the conversation.\n"
                "Continue naturally.\n\n"
                + recent_dialog_block
            )

        parts.append(f"\n[USER MESSAGE]\n{user_text}\n\n[ASTRA REPLY]\n")

        return "\n".join(parts)

    except Exception as e:
        print("[DEBUG] Exception in build_prompt:")
        traceback.print_exc()
        raise