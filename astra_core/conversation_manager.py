from datetime import datetime
from .character_profile import get_character_name
from .short_term_memory import load_state

CHARACTER_NAME = get_character_name()

class ConversationManager:
    def __init__(self):
        self.local_history: list[tuple[str, str]] = []
        self._load_from_state()

    def _load_from_state(self):
        state = load_state()
        for msg in state.get("messages", []):
            role = msg.get("role")
            text = msg.get("text")
            if role == "user":
                self.local_history.append(("User", text))
            elif role == "astra":
                self.local_history.append((CHARACTER_NAME, text))

    def add_user_message(self, text: str) -> None:
        self.local_history.append(("User", text))

    def add_astra_message(self, text: str) -> None:
        self.local_history.append((CHARACTER_NAME, text))

    def get_recent_dialog(self, limit: int = 24) -> str:
        if not self.local_history:
            self._load_from_state()
        recent = self.local_history[-limit:]
        return "\n".join(f"{role}: {text}" for role, text in recent)