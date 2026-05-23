# astra_core/context_optimizer.py
from .memory_engine import detect_memory_intent

# Mapping: intent -> which blocks to include
BLOCK_RULES = {
    "casual": {
        "core_self": True,        # кратко
        "time_context": True,
        "conversation_state": True,
        "short_term_memory": True, # последние 2-3 сообщения
        "txt_memory": False,       # не нужна
        "memory_v2": False,        # не грузим для casual
        "project_state": False,
        "recent_dialog": True,     # последние 6 сообщений
    },
    "memory_overview": {
        "core_self": False,
        "time_context": False,
        "conversation_state": False,
        "short_term_memory": False,
        "txt_memory": False,       # отключено, используем Memory v2
        "memory_v2": True,         # расширенный лимит 12
        "project_state": False,
        "recent_dialog": False,
    },
    "identity": {
        "core_self": False,
        "time_context": False,
        "conversation_state": False,
        "short_term_memory": False,
        "txt_memory": False,
        "memory_v2": True,         # лимит 3 (только identity)
        "project_state": False,
        "recent_dialog": False,
    },
    "preferences": {
        "core_self": False,
        "time_context": False,
        "conversation_state": False,
        "short_term_memory": False,
        "txt_memory": False,
        "memory_v2": True,         # лимит 8
        "project_state": False,
        "recent_dialog": False,
    },
    "project": {
        "core_self": False,
        "time_context": False,
        "conversation_state": False,
        "short_term_memory": False,
        "txt_memory": False,
        "memory_v2": True,         # project_decision, session_summary
        "project_state": True,
        "recent_dialog": False,
    },
    "relationship": {
        "core_self": False,
        "time_context": False,
        "conversation_state": False,
        "short_term_memory": False,
        "txt_memory": False,
        "memory_v2": True,         # relationship/mood
        "project_state": False,
        "recent_dialog": False,
    },
}

def get_context_plan(user_text: str):
    intent = detect_memory_intent(user_text)
    rules = BLOCK_RULES.get(intent, BLOCK_RULES["casual"])
    return intent, rules