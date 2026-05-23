import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont, QIcon, QLinearGradient
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QTextBrowser, QTextEdit, QLineEdit, QPushButton,
    QLabel, QProgressBar, QCheckBox, QGroupBox, QFormLayout,
    QMessageBox, QSplitter, QComboBox, QDoubleSpinBox, QSpinBox,
    QFileDialog, QDialog, QDialogButtonBox, QFrame, QScrollArea
)
# Импорт из Astra Core
from astra_core.settings import load_settings, save_settings, BASE_DIR
from astra_core.core import AstraCore
from astra_core.activity import touch_user_activity
from astra_core.character_profile import get_character_name
from astra_core.conversation_meta import start_new_session, close_current_session
from astra_core.session_analyzer import analyze_current_session
from astra_core.emotional_core import STAGE_THRESHOLDS, DEFAULT_RELATIONSHIP, save_relationship_state, load_relationship_state
from astra_core.short_term_memory import clear_state
from astra_core.memory_engine import clear_all_memories
from astra_core.service_manager import ServiceManager

# === Пути к файлам (все в корне BASE_DIR) ===
RELATIONSHIP_FILE = BASE_DIR / "character" / "emergent_self" / "relationship_state.json"
MEMORY_STORE_FILE = BASE_DIR / "memory_store.json"
CONVERSATION_STATE_FILE = BASE_DIR / "conversation_state.json"
BACKUPS_DIR = BASE_DIR / "backups"
AVATAR_CONFIG_FILE = BASE_DIR / "avatar_config.json"

# === Папка с файлами личности ===
CORE_SELF_DIR = BASE_DIR / "character" / "core_self"
CORE_FILES = {
    "identity":       CORE_SELF_DIR / "identity.txt",
    "personality":    CORE_SELF_DIR / "personality.txt",
    "speech_style":   CORE_SELF_DIR / "speech_style.txt",
    "boundaries":     CORE_SELF_DIR / "boundaries.txt",
    "innate_likes":   CORE_SELF_DIR / "innate_likes.txt",
    "innate_dislikes": CORE_SELF_DIR / "innate_dislikes.txt",
}

# =====================================================================
# ТЕМА — СВЕТЛАЯ / ТЁМНАЯ
# =====================================================================
DARK_THEME = "dark"
LIGHT_THEME = "light"
PALETTES = {
    DARK_THEME: {
        "bg_deep":         "#080614", "bg_base":         "#0f0a1e", "bg_panel":        "#120d22",
        "bg_elevated":     "#1a1230", "bg_input":        "#1e1540", "bg_hover":        "#261a4a",
        "border":          "#2e1f54", "border_accent":   "#4a2d80", "accent":          "#7c3aed",
        "accent_bright":   "#a855f7", "accent_glow":     "#c084fc", "text_primary":    "#ede9fe",
        "text_secondary":  "#c4b5fd", "text_muted":      "#7c6fa0", "text_disabled":   "#4a3d6a",
        "tab_bg":          "#110c20", "tab_selected":    "#1e1540", "scrollbar":       "#2e1f54",
        "scrollbar_h":     "#7c3aed", "danger_bg":       "#3d0f1f", "danger_fg":       "#f87171",
        "danger_border":   "#7f1d1d", "success_bg":      "#052e16", "success_fg":      "#4ade80",
        "success_border":  "#14532d", "info_bg":         "#0c1a3d", "info_fg":         "#60a5fa",
        "info_border":     "#1e3a6e", "unlock_bg":       "#2d1e00", "unlock_fg":       "#fbbf24",
        "unlock_border":   "#78350f", "log_bg":          "#0d0820", "log_border":      "#1e0f3a",
        "log_color":       "#7c6fa0", "send_start":      "#7c3aed", "send_end":        "#a855f7",
        "send_h_start":    "#8b47f0", "send_h_end":      "#b965f9", "chat_msg_bg":     "#160e38",
        "chat_msg_border": "#7c3aed", "dialog_bg":       "#0f0a1e", "dialog_border":   "#7c3aed",
        "meme_bg":         "#1e1040", "meme_border":     "#7c3aed", "meme_text":       "#ddd6fe",
        "stage_bg":        "#160e38", "pbar_bg":         "#1a1030", "pbar_chunk_s":    "#7c3aed",
        "pbar_chunk_e":    "#a855f7",
    },
    LIGHT_THEME: {
        "bg_deep":         "#f5f3ff", "bg_base":         "#faf9ff", "bg_panel":        "#f0eeff",
        "bg_elevated":     "#ebe8ff", "bg_input":        "#ffffff", "bg_hover":        "#ddd6fe",
        "border":          "#c4b5fd", "border_accent":   "#8b5cf6", "accent":          "#7c3aed",
        "accent_bright":   "#9333ea", "accent_glow":     "#6d28d9", "text_primary":    "#1e0a3c",
        "text_secondary":  "#4c1d95", "text_muted":      "#6b7280", "text_disabled":   "#9ca3af",
        "tab_bg":          "#ede9fe", "tab_selected":    "#ddd6fe", "scrollbar":       "#c4b5fd",
        "scrollbar_h":     "#7c3aed", "danger_bg":       "#fff1f2", "danger_fg":       "#dc2626",
        "danger_border":   "#fca5a5", "success_bg":      "#f0fdf4", "success_fg":      "#16a34a",
        "success_border":  "#86efac", "info_bg":         "#eff6ff", "info_fg":         "#2563eb",
        "info_border":     "#93c5fd", "unlock_bg":       "#fffbeb", "unlock_fg":       "#d97706",
        "unlock_border":   "#fcd34d", "log_bg":          "#f5f3ff", "log_border":      "#c4b5fd",
        "log_color":       "#6b7280", "send_start":      "#7c3aed", "send_end":        "#9333ea",
        "send_h_start":    "#6d28d9", "send_h_end":      "#7c3aed", "chat_msg_bg":     "#f5f0ff",
        "chat_msg_border": "#8b5cf6", "dialog_bg":       "#ffffff", "dialog_border":   "#7c3aed",
        "meme_bg":         "#ede9fe", "meme_border":     "#8b5cf6", "meme_text":       "#4c1d95",
        "stage_bg":        "#ede9fe", "pbar_bg":         "#e9d5ff", "pbar_chunk_s":    "#7c3aed",
        "pbar_chunk_e":    "#9333ea",
    },
}

def build_stylesheet(theme: str) -> str:
    p = PALETTES[theme]
    return f"""
/* ===== BASE ===== */
QMainWindow, QWidget {{ background-color: {p['bg_base']}; color: {p['text_primary']}; font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif; font-size: 13px; }}
/* ===== TABS ===== */
QTabWidget::pane {{ border: 1px solid {p['border']}; background: {p['bg_base']}; border-radius: 0 6px 6px 6px; }}
QTabBar::tab {{ background: {p['tab_bg']}; color: {p['text_muted']}; padding: 10px 20px; border: 1px solid {p['border']}; border-bottom: none; margin-right: 3px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 12px; }}
QTabBar::tab:selected {{ background: {p['tab_selected']}; color: {p['accent_bright']}; border-bottom-color: {p['accent']}; border-top: 2px solid {p['accent']}; }}
QTabBar::tab:hover:!selected {{ background: {p['bg_elevated']}; color: {p['text_secondary']}; }}
/* ===== PANELS ===== */
QWidget#LeftPanel, QWidget#RightPanel {{ background: {p['bg_panel']}; border-radius: 10px; }}
QWidget#CenterPanel {{ background: {p['bg_deep']}; }}
/* ===== CHAT ===== */
QTextBrowser#ChatDisplay {{ background: {p['bg_deep']}; color: {p['text_primary']}; border: none; font-size: 13px; line-height: 1.6; padding: 10px; }}
QTextBrowser#LogBrowser {{ background: {p['log_bg']}; color: {p['log_color']}; border: 1px solid {p['log_border']}; border-radius: 8px; font-size: 11px; padding: 6px; }}
/* ===== INPUT FRAME ===== */
QFrame#InputFrame {{ background: {p['bg_elevated']}; border-top: 1px solid {p['border']}; border-radius: 0 0 8px 8px; }}
QLineEdit {{ background: {p['bg_input']}; color: {p['text_primary']}; border: 1px solid {p['border']}; border-radius: 10px; padding: 7px 14px; font-size: 13px; }}
QLineEdit:focus {{ border: 1px solid {p['accent']}; }}
/* ===== BUTTONS ===== */
QPushButton {{ background: {p['bg_elevated']}; color: {p['text_secondary']}; border: 1px solid {p['border_accent']}; border-radius: 8px; padding: 6px 16px; font-weight: 600; }}
QPushButton:hover {{ background: {p['bg_hover']}; border-color: {p['accent']}; color: {p['text_primary']}; }}
QPushButton:pressed {{ background: {p['bg_input']}; }}
QPushButton:disabled {{ background: {p['bg_panel']}; color: {p['text_disabled']}; border-color: {p['border']}; }}
QPushButton#SendBtn {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p['send_start']}, stop:1 {p['send_end']}); color: #ffffff; border: none; border-radius: 10px; }}
QPushButton#DangerBtn {{ background: {p['danger_bg']}; color: {p['danger_fg']}; border: 1px solid {p['danger_border']}; }}
QPushButton#DangerBtn:hover {{ background: {p['danger_border']}; color: #ffffff; }}
QPushButton#SuccessBtn {{ background: {p['success_bg']}; color: {p['success_fg']}; border: 1px solid {p['success_border']}; }}
QPushButton#SuccessBtn:hover {{ background: {p['success_border']}; color: #ffffff; }}
QPushButton#InfoBtn {{ background: {p['info_bg']}; color: {p['info_fg']}; border: 1px solid {p['info_border']}; }}
QPushButton#InfoBtn:hover {{ background: {p['info_border']}; color: #ffffff; }}
QPushButton#UnlockBtn {{ background: {p['unlock_bg']}; color: {p['unlock_fg']}; border: 1px solid {p['unlock_border']}; }}
QPushButton#UnlockBtn:hover {{ background: {p['unlock_border']}; color: #1a0a00; }}
QPushButton#ActionBtn {{ background: {p['bg_elevated']}; color: {p['accent_bright']}; border: 1px solid {p['border_accent']}; }}
QPushButton#ActionBtn:hover {{ background: {p['bg_hover']}; border-color: {p['accent']}; }}
/* ===== GROUPBOX ===== */
QGroupBox {{ font-weight: 700; border: 1px solid {p['border']}; border-radius: 10px; margin-top: 14px; padding-top: 18px; color: {p['accent_bright']}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; top: -1px; background: {p['bg_base']}; padding: 0 6px; }}
/* ===== PROGRESSBAR ===== */
QProgressBar {{ border-radius: 5px; background: {p['pbar_bg']}; text-align: center; font-size: 10px; color: transparent; border: none; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {p['pbar_chunk_s']}, stop:1 {p['pbar_chunk_e']}); border-radius: 5px; }}
/* ===== TEXTEDIT ===== */
QTextEdit {{ background: {p['bg_input']}; color: {p['text_primary']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 8px; }}
QTextEdit:focus {{ border: 1px solid {p['accent']}; }}
/* ===== COMBOBOX ===== */
QComboBox {{ background: {p['bg_input']}; color: {p['text_primary']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 5px 10px 5px 12px; font-size: 13px; min-height: 28px; }}
QComboBox:hover {{ border-color: {p['accent']}; }}
QComboBox:focus {{ border-color: {p['accent']}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border-left: 1px solid {p['border']}; border-top-right-radius: 8px; border-bottom-right-radius: 8px; background: {p['bg_elevated']}; }}
QComboBox QAbstractItemView {{ background: {p['bg_elevated']}; color: {p['text_primary']}; selection-background-color: {p['bg_hover']}; border: 1px solid {p['border_accent']}; border-radius: 6px; }}
/* ===== SPINBOX ===== */
QDoubleSpinBox, QSpinBox {{ background: {p['bg_input']}; color: {p['text_primary']}; border: 1px solid {p['border']}; border-radius: 8px; padding: 5px 32px 5px 10px; font-size: 13px; min-height: 28px; }}
QDoubleSpinBox:hover, QSpinBox:hover {{ border-color: {p['accent']}; }}
QDoubleSpinBox::up-button, QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 22px; height: 14px; border-left: 1px solid {p['border']}; border-bottom: 1px solid {p['border']}; border-top-right-radius: 7px; background: {p['bg_elevated']}; }}
QDoubleSpinBox::down-button, QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; height: 14px; border-left: 1px solid {p['border']}; border-top: 1px solid {p['border']}; border-bottom-right-radius: 7px; background: {p['bg_elevated']}; }}
/* ===== CHECKBOX ===== */
QCheckBox {{ color: {p['text_secondary']}; spacing: 10px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 2px solid {p['border_accent']}; background: {p['bg_input']}; }}
QCheckBox::indicator:checked {{ background: {p['accent']}; border-color: {p['accent']}; image: none; }}
/* ===== SPLITTER ===== */
QSplitter::handle {{ background: {p['border']}; width: 2px; }}
/* ===== SCROLLBAR ===== */
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: {p['scrollbar']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p['scrollbar_h']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
/* ===== LABELS ===== */
QLabel {{ color: {p['text_secondary']}; background: transparent; }}
"""

# =====================================================================
# МЕМНЫЕ ДИАЛОГИ ПОДТВЕРЖДЕНИЯ
# =====================================================================
class MemeConfirmDialog(QDialog):
    """Кастомный мемный диалог подтверждения."""
    def __init__(self, parent, meme_type: str, theme: str = DARK_THEME):
        super().__init__(parent)
        p = PALETTES[theme]
        self.setWindowTitle("⚠️ Подождите...")
        self.setFixedSize(460, 340)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {p['dialog_bg']}; border: 2px solid {p['dialog_border']}; border-radius: 14px; }}
            QLabel {{ color: {p['text_primary']}; background: transparent; }}
            QPushButton {{ border-radius: 8px; padding: 9px 26px; font-weight: bold; font-size: 13px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        memes = {
            "unlock": {"emoji": "🧠💥", "title": "ВЫ УВЕРЕНЫ, ЧТО ГОТОВЫ?", "top": "Вы собираетесь разблокировать ядро отношений.", "meme_text": "«Власть \nпортит людей»\n\n...а raw edit — базы данных 💀", "bottom": "Вы уверены? Вы точно уверены? Может, лучше не надо?", "yes": "ДА, Я ЗНАЮ ЧТО ДЕЛАЮ", "no": "нет-нет-нет отмена"},
            "clear_memory": {"emoji": "🪣🧹", "title": "АСТРА ВАС ЗАБУДЕТ...", "top": "Долгосрочная память будет полностью стёрта.", "meme_text": "Это как Men in Black\nтолько грустнее\nи без Уилла Смита 😔", "bottom": "Она забудет ВСЁ. Имя, привычки, ваши мемы. Всё.", "yes": "💀 Стереть всё", "no": "⬅️ Назад к жизни"},
            "clear_chat": {"emoji": "💬🔥", "title": "ДИАЛОГ ИСЧЕЗНЕТ", "top": "Текущий контекст диалога будет очищен.", "meme_text": "Астра: «Кто ты?\nЯ тебя не знаю»\n😶 (5 секунд назад знала)", "bottom": "Краткосрочная память сбросится. Продолжить?", "yes": "🗑️ Да, чистим", "no": "❌ Нет, стоп"}
        }
        data = memes.get(meme_type, memes["unlock"])

        emoji_lbl = QLabel(data["emoji"]); emoji_lbl.setAlignment(Qt.AlignCenter); emoji_lbl.setStyleSheet("font-size: 38px;")
        layout.addWidget(emoji_lbl)
        title_lbl = QLabel(data["title"]); title_lbl.setAlignment(Qt.AlignCenter); title_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {p['danger_fg']};")
        layout.addWidget(title_lbl)
        top_lbl = QLabel(data["top"]); top_lbl.setAlignment(Qt.AlignCenter); top_lbl.setStyleSheet(f"font-size: 12px; color: {p['text_muted']};")
        layout.addWidget(top_lbl)
        meme_box = QLabel(data["meme_text"]); meme_box.setAlignment(Qt.AlignCenter); meme_box.setWordWrap(True)
        meme_box.setStyleSheet(f"background-color: {p['meme_bg']}; border: 1px solid {p['meme_border']}; border-radius: 10px; padding: 12px; font-size: 13px; color: {p['meme_text']}; font-style: italic; line-height: 1.5;")
        layout.addWidget(meme_box)
        bottom_lbl = QLabel(data["bottom"]); bottom_lbl.setAlignment(Qt.AlignCenter); bottom_lbl.setWordWrap(True)
        bottom_lbl.setStyleSheet(f"font-size: 11px; color: {p['text_muted']};")
        layout.addWidget(bottom_lbl)

        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
        self.btn_yes = QPushButton(data["yes"])
        self.btn_yes.setStyleSheet(f"QPushButton {{ background-color: {p['danger_fg']}; color: white; border: none; border-radius: 8px; }} QPushButton:hover {{ background-color: #ef4444; }}")
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no = QPushButton(data["no"])
        self.btn_no.setStyleSheet(f"QPushButton {{ background-color: {p['success_fg']}; color: white; border: none; border-radius: 8px; }} QPushButton:hover {{ background-color: #22c55e; }}")
        self.btn_no.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_no); btn_layout.addWidget(self.btn_yes)
        layout.addLayout(btn_layout)

# =====================================================================
# ЗАГРУЗКА И ХРАНЕНИЕ АВАТАРА
# =====================================================================
def load_avatar_config() -> dict:
    if AVATAR_CONFIG_FILE.exists():
        try: return json.loads(AVATAR_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return {"path": "", "shape": "circle"}

def save_avatar_config(config: dict):
    AVATAR_CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def make_avatar_pixmap(image_path: str, shape: str, size: int = 64) -> QPixmap:
    src = QPixmap(image_path)
    if src.isNull(): return _default_avatar(size, shape)
    src = src.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    result = QPixmap(size, size); result.fill(Qt.transparent)
    painter = QPainter(result); painter.setRenderHint(QPainter.Antialiasing)
    if shape == "circle":
        painter.setBrush(QBrush(src)); painter.setPen(Qt.NoPen); painter.drawEllipse(0, 0, size, size)
        painter.setPen(QPen(QColor("#7c3aed"), 2)); painter.setBrush(Qt.NoBrush); painter.drawEllipse(1, 1, size - 2, size - 2)
    else:
        painter.setBrush(QBrush(src)); painter.setPen(Qt.NoPen); painter.drawRoundedRect(0, 0, size, size, 8, 8)
        painter.setPen(QPen(QColor("#7c3aed"), 2)); painter.setBrush(Qt.NoBrush); painter.drawRoundedRect(1, 1, size - 2, size - 2, 8, 8)
    painter.end(); return result

def _default_avatar(size: int, shape: str, theme: str = DARK_THEME) -> QPixmap:
    p = PALETTES[theme]; result = QPixmap(size, size); result.fill(Qt.transparent)
    painter = QPainter(result); painter.setRenderHint(QPainter.Antialiasing)
    if shape == "circle": painter.setBrush(QBrush(QColor(p['bg_elevated']))); painter.setPen(QPen(QColor(p['accent']), 2)); painter.drawEllipse(1, 1, size - 2, size - 2)
    else: painter.setBrush(QBrush(QColor(p['bg_elevated']))); painter.setPen(QPen(QColor(p['accent']), 2)); painter.drawRoundedRect(1, 1, size - 2, size - 2, 8, 8)
    painter.setPen(QColor(p['accent_bright'])); painter.setFont(QFont("Segoe UI", size // 3, QFont.Bold))
    painter.drawText(result.rect(), Qt.AlignCenter, "A"); painter.end(); return result

# =====================================================================
# WORKER THREAD
# =====================================================================
class AstraWorker(QThread):
    reply_received = Signal(str, str, str)
    def __init__(self, astra_core, user_text):
        super().__init__(); self.astra_core = astra_core; self.user_text = user_text
    def run(self):
        import io, sys as sys_module; old_stdout = sys_module.stdout; sys_module.stdout = buffer = io.StringIO() 
        try: answer = self.astra_core.reply(self.user_text)
        except Exception as e: answer = f"[Ошибка генерации]: {str(e)}"
        sys_module.stdout = old_stdout; console_output = buffer.getvalue(); memory_log, rel_log = "", ""
        for line in console_output.splitlines():
            if "[MEMORY ANALYZER RESULT]" in line: memory_log = line
            if "[RELATIONSHIP]" in line: rel_log = line
        self.reply_received.emit(answer, memory_log, rel_log)

# =====================================================================
# ГЛАВНОЕ ОКНО
# =====================================================================
class AstraUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.astra = AstraCore(); start_new_session()
        self.settings = load_settings(); self.character_name = get_character_name()
        self.service_manager = ServiceManager(); self.avatar_config = load_avatar_config()
        self._theme = self.settings.get("ui_theme", DARK_THEME)
        self.setWindowTitle(f"✦ {self.character_name} — Control Panel"); self.resize(1300, 820); self.setMinimumSize(900, 600)
        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); self.setCentralWidget(self.tabs)
        self.init_chat_tab(); self.init_profile_tab(); self.init_system_tab(); self.init_relationship_tab()
        self.init_memory_tab(); self.init_models_tab()
        self._apply_theme(self._theme)
        self.update_timer = QTimer(); self.update_timer.timeout.connect(self.load_relationship_bars); self.update_timer.start(2000)

    def _apply_theme(self, theme: str): self._theme = theme; QApplication.instance().setStyleSheet(build_stylesheet(theme))

    # =========================================================================
    # ВКЛАДКА 1: ЧАТ
    # =========================================================================
    def init_chat_tab(self):
        chat_widget = QWidget(); main_layout = QHBoxLayout(chat_widget); main_layout.setSpacing(0); main_layout.setContentsMargins(0, 0, 0, 0)
        left_widget = QWidget(); left_widget.setFixedWidth(240); left_widget.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(left_widget); left_layout.setContentsMargins(14, 16, 14, 14); left_layout.setSpacing(8)
        avatar_section = QVBoxLayout(); avatar_section.setAlignment(Qt.AlignHCenter); avatar_section.setSpacing(8)
        self.avatar_label = QLabel(); self.avatar_label.setAlignment(Qt.AlignCenter); self.avatar_label.setFixedSize(88, 88)
        self._refresh_avatar_label(88); avatar_section.addWidget(self.avatar_label)
        name_lbl = QLabel(self.character_name); name_lbl.setAlignment(Qt.AlignCenter); name_lbl.setStyleSheet("font-size: 16px; font-weight: 700; letter-spacing: 1.5px;")
        avatar_section.addWidget(name_lbl); left_layout.addLayout(avatar_section)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); left_layout.addWidget(sep)
        self.lbl_stage = QLabel("Стадия: ..."); self.lbl_stage.setWordWrap(True); self.lbl_stage.setAlignment(Qt.AlignCenter); self.lbl_stage.setObjectName("StageLabel")
        self.lbl_stage.setStyleSheet("font-weight: 700; font-size: 12px; border-radius: 8px; padding: 6px;")
        left_layout.addWidget(self.lbl_stage)
        depth_lbl = QLabel("Глубина отношений:"); depth_lbl.setStyleSheet("font-size: 11px; font-weight: 600;"); left_layout.addWidget(depth_lbl)
        self.pbar_depth = QProgressBar(); self.pbar_depth.setRange(0, 1000); self.pbar_depth.setFixedHeight(10); left_layout.addWidget(self.pbar_depth)
        metrics = [("mood", "😊 Настроение", "#f59e0b"), ("affection", "❤️ Привязанность", "#f43f5e"), ("trust", "🔮 Доверие", "#8b5cf6"), ("comfort", "🌿 Комфорт", "#10b981"), ("anger", "🔥 Злость", "#ef4444"), ("discomfort", "😣 Дискомфорт", "#f97316")]
        self.bars = {}
        for key, label, color in metrics:
            lbl = QLabel(label); lbl.setStyleSheet("font-size: 11px; margin-top: 4px;"); left_layout.addWidget(lbl)
            bar = QProgressBar(); bar.setRange(0, 100); bar.setFixedHeight(7); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar {{ border-radius: 4px; border: none; }} QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}")
            left_layout.addWidget(bar); self.bars[key] = bar
        left_layout.addStretch()
        self.btn_clear_chat = QPushButton("🗑 Очистить диалог"); self.btn_clear_chat.setObjectName("DangerBtn"); self.btn_clear_chat.clicked.connect(self.clear_current_chat); left_layout.addWidget(self.btn_clear_chat)
        center_widget = QWidget(); center_widget.setObjectName("CenterPanel"); center_layout = QVBoxLayout(center_widget); center_layout.setContentsMargins(10, 10, 10, 10); center_layout.setSpacing(8)
        self.chat_display = QTextBrowser(); self.chat_display.setObjectName("ChatDisplay"); self.chat_display.setOpenExternalLinks(True); center_layout.addWidget(self.chat_display, 9)
        input_frame = QFrame(); input_frame.setObjectName("InputFrame"); input_layout = QHBoxLayout(input_frame); input_layout.setContentsMargins(10, 8, 10, 8); input_layout.setSpacing(8)
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText(f"  Написать {self.character_name}..."); self.chat_input.setMinimumHeight(40); self.chat_input.returnPressed.connect(self.send_message)
        self.btn_send = QPushButton("➤ Отправить"); self.btn_send.setMinimumHeight(40); self.btn_send.setMinimumWidth(120); self.btn_send.setObjectName("SendBtn"); self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.chat_input); input_layout.addWidget(self.btn_send); center_layout.addWidget(input_frame, 1)
        right_widget = QWidget(); right_widget.setFixedWidth(230); right_widget.setObjectName("RightPanel"); right_layout = QVBoxLayout(right_widget); right_layout.setContentsMargins(10, 14, 10, 14); right_layout.setSpacing(8)
        mem_lbl = QLabel("📦 Лог памяти:"); mem_lbl.setStyleSheet("font-size: 11px; font-weight: 700;"); right_layout.addWidget(mem_lbl)
        self.log_memory = QTextBrowser(); self.log_memory.setObjectName("LogBrowser"); right_layout.addWidget(self.log_memory)
        rel_lbl = QLabel("💫 Изменения отношений:"); rel_lbl.setStyleSheet("font-size: 11px; font-weight: 700;"); right_layout.addWidget(rel_lbl)
        self.log_relations = QTextBrowser(); self.log_relations.setObjectName("LogBrowser"); right_layout.addWidget(self.log_relations)
        splitter = QSplitter(Qt.Horizontal); splitter.setHandleWidth(3); splitter.addWidget(left_widget); splitter.addWidget(center_widget); splitter.addWidget(right_widget); splitter.setStretchFactor(1, 5)
        main_layout.addWidget(splitter); self.tabs.addTab(chat_widget, "💬 Чат"); self.load_relationship_bars()

    def _refresh_avatar_label(self, size: int = 88):
        path = self.avatar_config.get("path", ""); shape = self.avatar_config.get("shape", "circle")
        pm = make_avatar_pixmap(path, shape, size) if path and Path(path).exists() else _default_avatar(size, shape, self._theme)
        self.avatar_label.setPixmap(pm)

    # =========================================================================
    # ВКЛАДКА 2: ПРОФИЛЬ ЛИЧНОСТИ
    # =========================================================================
    def init_profile_tab(self):
        profile_widget = QWidget(); layout = QVBoxLayout(profile_widget); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(10)
        avatar_group = QGroupBox("🖼 Аватар персонажа"); avatar_group_layout = QHBoxLayout(avatar_group); avatar_group_layout.setSpacing(20)
        self.profile_avatar_lbl = QLabel(); self.profile_avatar_lbl.setFixedSize(100, 100); self.profile_avatar_lbl.setAlignment(Qt.AlignCenter); self._refresh_profile_avatar()
        avatar_group_layout.addWidget(self.profile_avatar_lbl)
        avatar_controls = QVBoxLayout(); avatar_controls.setSpacing(8)
        self.btn_choose_avatar = QPushButton("📂 Выбрать изображение..."); self.btn_choose_avatar.setObjectName("ActionBtn"); self.btn_choose_avatar.clicked.connect(self.choose_avatar); avatar_controls.addWidget(self.btn_choose_avatar)
        shape_row = QHBoxLayout(); shape_lbl = QLabel("Форма аватара:"); shape_lbl.setStyleSheet("font-size: 12px;"); shape_row.addWidget(shape_lbl)
        self.cmb_avatar_shape = QComboBox(); self.cmb_avatar_shape.addItems(["circle", "square"]); self.cmb_avatar_shape.setCurrentText(self.avatar_config.get("shape", "circle")); self.cmb_avatar_shape.currentTextChanged.connect(self.on_avatar_shape_changed); shape_row.addWidget(self.cmb_avatar_shape); avatar_controls.addLayout(shape_row)
        self.btn_reset_avatar = QPushButton("✖ Сбросить аватар"); self.btn_reset_avatar.setObjectName("DangerBtn"); self.btn_reset_avatar.clicked.connect(self.reset_avatar); avatar_controls.addWidget(self.btn_reset_avatar); avatar_controls.addStretch()
        avatar_group_layout.addLayout(avatar_controls); avatar_group_layout.addStretch(); layout.addWidget(avatar_group)
        splitter_top = QSplitter(Qt.Horizontal); splitter_bottom = QSplitter(Qt.Horizontal); self.core_fields = {}
        for i, (key, filepath) in enumerate(CORE_FILES.items()):
            group = QGroupBox(f"📄 {filepath.name}"); g_layout = QVBoxLayout(group); g_layout.setContentsMargins(8, 8, 8, 8)
            text_edit = QTextEdit()
            if filepath.exists(): text_edit.setPlainText(filepath.read_text(encoding="utf-8"))
            g_layout.addWidget(text_edit); self.core_fields[key] = text_edit
            if i < 3: splitter_top.addWidget(group)
            else: splitter_bottom.addWidget(group)
        layout.addWidget(splitter_top, 1); layout.addWidget(splitter_bottom, 1)
        btn_save_profile = QPushButton("💾 Сохранить параметры личности"); btn_save_profile.setObjectName("SuccessBtn"); btn_save_profile.setMinimumHeight(38); btn_save_profile.clicked.connect(self.save_profile_files)
        layout.addWidget(btn_save_profile); self.tabs.addTab(profile_widget, "🧬 Профиль личности")

    def _refresh_profile_avatar(self):
        path = self.avatar_config.get("path", ""); shape = self.avatar_config.get("shape", "circle")
        pm = make_avatar_pixmap(path, shape, 100) if path and Path(path).exists() else _default_avatar(100, shape, self._theme)
        self.profile_avatar_lbl.setPixmap(pm)

    def choose_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение для аватара", "", "Изображения (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if path: self.avatar_config["path"] = path; save_avatar_config(self.avatar_config); self._refresh_avatar_label(88); self._refresh_profile_avatar()
    def on_avatar_shape_changed(self, shape: str): self.avatar_config["shape"] = shape; save_avatar_config(self.avatar_config); self._refresh_avatar_label(88); self._refresh_profile_avatar()
    def reset_avatar(self): self.avatar_config["path"] = ""; save_avatar_config(self.avatar_config); self._refresh_avatar_label(88); self._refresh_profile_avatar()
    def save_profile_files(self):
        try:
            for key, text_edit in self.core_fields.items(): CORE_FILES[key].write_text(text_edit.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "Успех", "Параметры личности сохранены.")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    # =========================================================================
    # ВКЛАДКА 3: СИСТЕМНЫЕ НАСТРОЙКИ
    # ========================================================================= 
    def init_system_tab(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        system_widget = QWidget(); layout = QVBoxLayout(system_widget); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(14)
        config_group = QGroupBox("⚙️ Общие настройки окружения"); form = QFormLayout(config_group); form.setSpacing(10); form.setContentsMargins(16, 16, 16, 16)
        self.inp_user_name = QLineEdit(self.settings.get("user_name", "User")); self.inp_tts_url = QLineEdit(self.settings.get("tts_url", ""))
        self.inp_user_name.setMinimumHeight(34); self.inp_tts_url.setMinimumHeight(34)
        form.addRow("👤 Имя пользователя:", self.inp_user_name); form.addRow("🔊 TTS URL:", self.inp_tts_url); layout.addWidget(config_group)
        theme_group = QGroupBox("🎨 Тема интерфейса"); theme_layout = QHBoxLayout(theme_group); theme_layout.setContentsMargins(16, 16, 16, 16); theme_layout.setSpacing(12)
        theme_label = QLabel("Выберите тему:"); theme_label.setStyleSheet("font-size: 13px;"); theme_layout.addWidget(theme_label)
        self.cmb_theme = QComboBox(); self.cmb_theme.addItems(["🌙 Тёмная тема", "☀️ Светлая тема"]); self.cmb_theme.setCurrentIndex(0 if self._theme == DARK_THEME else 1)
        self.cmb_theme.setMinimumHeight(34); self.cmb_theme.setMinimumWidth(200); self.cmb_theme.currentIndexChanged.connect(self._on_theme_changed); theme_layout.addWidget(self.cmb_theme); theme_layout.addStretch(); layout.addWidget(theme_group)
        services_group = QGroupBox("🔄 Управление фоновыми модулями"); serv_layout = QVBoxLayout(services_group); serv_layout.setContentsMargins(16, 16, 16, 16); serv_layout.setSpacing(10)
        self.chk_voice = QCheckBox("🎤 Голосовой интерфейс (astra_voice.py)"); self.chk_initiative = QCheckBox("⚡ Автономная инициативность (astra_core_initiative.py)")
        serv_layout.addWidget(self.chk_voice); serv_layout.addWidget(self.chk_initiative); layout.addWidget(services_group)
        self.chk_voice.toggled.connect(lambda checked: self.toggle_service("voice", checked)); self.chk_initiative.toggled.connect(lambda checked: self.toggle_service("initiative", checked))
        btn_save = QPushButton("💾 Сохранить общие настройки"); btn_save.setObjectName("SuccessBtn"); btn_save.setMinimumHeight(38); btn_save.clicked.connect(self.save_general_settings); layout.addWidget(btn_save); layout.addStretch()
        scroll.setWidget(system_widget); self.tabs.addTab(scroll, "⚙️ Системные настройки")

    def _on_theme_changed(self, index: int):
        theme = DARK_THEME if index == 0 else LIGHT_THEME; self._apply_theme(theme)
        try: cs = load_settings(); cs["ui_theme"] = theme; save_settings(cs); self.settings = cs
        except Exception: pass

    @Slot()
    def save_general_settings(self):
        cs = load_settings(); cs["user_name"] = self.inp_user_name.text().strip(); cs["tts_url"] = self.inp_tts_url.text().strip()
        try: save_settings(cs); self.settings = cs; QMessageBox.information(self, "Успех", "Общие настройки сохранены!")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    # =========================================================================
    # ВКЛАДКА 4: МЕТРИКИ И ОБСЛУЖИВАНИЕ
    # =========================================================================
    def init_relationship_tab(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        rel_widget = QWidget(); layout = QVBoxLayout(rel_widget); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(14)
        lock_group = QGroupBox("🔒 Параметры ядра отношений"); lock_group_layout = QVBoxLayout(lock_group); lock_group_layout.setContentsMargins(16, 16, 16, 16)
        self.lock_form = QFormLayout(); self.lock_form.setSpacing(8); self.rel_inputs = {}
        keys_labels = {"relationship_depth": "🌊 Глубина отношений", "affection": "❤️ Привязанность", "trust": "🔮 Доверие", "comfort": "🌿 Комфорт", "anger": "🔥 Злость", "mood": "😊 Настроение", "discomfort": "😣 Дискомфорт"}
        for key in keys_labels: inp = QLineEdit(); inp.setEnabled(False); inp.setMinimumHeight(32); self.lock_form.addRow(QLabel(f"{keys_labels[key]}:"), inp); self.rel_inputs[key] = inp
        lock_group_layout.addLayout(self.lock_form)
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self.btn_unlock = QPushButton("🔓 Разблокировать редактирование"); self.btn_unlock.setObjectName("UnlockBtn"); self.btn_unlock.setMinimumHeight(38); self.btn_unlock.clicked.connect(self.unlock_relations); btn_row.addWidget(self.btn_unlock)
        self.btn_apply_rel = QPushButton("✅ Записать правки ядра"); self.btn_apply_rel.setObjectName("SuccessBtn"); self.btn_apply_rel.setEnabled(False); self.btn_apply_rel.setMinimumHeight(38); self.btn_apply_rel.clicked.connect(self.save_manual_relations); btn_row.addWidget(self.btn_apply_rel)
        lock_group_layout.addLayout(btn_row); layout.addWidget(lock_group)
        layout.addStretch(); scroll.setWidget(rel_widget); self.tabs.addTab(scroll, "📊 Метрики и Сервис"); self.refresh_relationship_inputs()

    # =========================================================================
    # ВКЛАДКА 5: ПАМЯТЬ АСТРЫ
    # =========================================================================
    def init_memory_tab(self):
        """Вкладка просмотра и редактирования краткосрочной и долгосрочной памяти."""
        mem_widget = QWidget(); main_layout = QVBoxLayout(mem_widget); main_layout.setContentsMargins(14, 14, 14, 14); main_layout.setSpacing(12)
        top_bar = QHBoxLayout(); top_bar.setSpacing(10)
        self.lbl_mem_paths = QLabel(f"📂 Долгая: {MEMORY_STORE_FILE} | Короткая: {CONVERSATION_STATE_FILE}")
        self.lbl_mem_paths.setStyleSheet("font-size: 11px; font-style: italic;"); self.lbl_mem_paths.setWordWrap(True); top_bar.addWidget(self.lbl_mem_paths, 1)
        btn_refresh_mem = QPushButton("🔄 Обновить"); btn_refresh_mem.setObjectName("InfoBtn"); btn_refresh_mem.setMinimumHeight(34); btn_refresh_mem.setFixedWidth(130); btn_refresh_mem.clicked.connect(self.refresh_memory_tab); top_bar.addWidget(btn_refresh_mem)
        main_layout.addLayout(top_bar)
        splitter = QSplitter(Qt.Horizontal); splitter.setHandleWidth(4)
        long_frame = QWidget(); long_layout = QVBoxLayout(long_frame); long_layout.setContentsMargins(0, 0, 6, 0); long_layout.setSpacing(8)
        long_header = QHBoxLayout()
        long_title = QLabel("🧠 Долгосрочная память"); long_title.setStyleSheet("font-size: 14px; font-weight: 700; letter-spacing: 0.5px;"); long_header.addWidget(long_title); long_header.addStretch()
        self.lbl_mem_count = QLabel(" "); self.lbl_mem_count.setStyleSheet("font-size: 11px; color: #888;"); long_header.addWidget(self.lbl_mem_count); long_layout.addLayout(long_header)
        filter_row = QHBoxLayout(); filter_row.setSpacing(8); filter_row.addWidget(QLabel("Фильтр:"))
        self.cmb_mem_filter = QComboBox(); self.cmb_mem_filter.addItems(["Все записи", "user", "system", "temporary", "preference", "relationship", "session_summary"]); self.cmb_mem_filter.setMinimumHeight(30); self.cmb_mem_filter.currentTextChanged.connect(self._apply_memory_filter); filter_row.addWidget(self.cmb_mem_filter)
        self.inp_mem_search = QLineEdit(); self.inp_mem_search.setPlaceholderText("🔍 Поиск по тексту..."); self.inp_mem_search.setMinimumHeight(30); self.inp_mem_search.textChanged.connect(self._apply_memory_filter); filter_row.addWidget(self.inp_mem_search, 1); long_layout.addLayout(filter_row)
        self.mem_scroll = QScrollArea(); self.mem_scroll.setWidgetResizable(True); self.mem_scroll.setFrameShape(QFrame.NoFrame)
        self.mem_cards_widget = QWidget(); self.mem_cards_layout = QVBoxLayout(self.mem_cards_widget); self.mem_cards_layout.setContentsMargins(0, 0, 0, 0); self.mem_cards_layout.setSpacing(6); self.mem_cards_layout.addStretch(); self.mem_scroll.setWidget(self.mem_cards_widget); long_layout.addWidget(self.mem_scroll, 1)
        long_btns = QHBoxLayout(); long_btns.setSpacing(8)
        btn_mem_add = QPushButton("➕ Добавить запись"); btn_mem_add.setObjectName("SuccessBtn"); btn_mem_add.setMinimumHeight(36); btn_mem_add.clicked.connect(self.add_memory_record); long_btns.addWidget(btn_mem_add)
        btn_mem_save = QPushButton("💾 Сохранить изменения"); btn_mem_save.setObjectName("ActionBtn"); btn_mem_save.setMinimumHeight(36); btn_mem_save.clicked.connect(self.save_long_memory); long_btns.addWidget(btn_mem_save); long_layout.addLayout(long_btns); splitter.addWidget(long_frame)
        short_frame = QWidget(); short_layout = QVBoxLayout(short_frame); short_layout.setContentsMargins(6, 0, 0, 0); short_layout.setSpacing(8)
        short_header = QHBoxLayout()
        short_title = QLabel("💬 Краткосрочная память (контекст)"); short_title.setStyleSheet("font-size: 14px; font-weight: 700; letter-spacing: 0.5px;"); short_header.addWidget(short_title); short_header.addStretch()
        self.lbl_msg_count = QLabel(" "); short_header.addWidget(self.lbl_msg_count); short_layout.addLayout(short_header)
        self.conv_scroll = QScrollArea(); self.conv_scroll.setWidgetResizable(True); self.conv_scroll.setFrameShape(QFrame.NoFrame)
        self.conv_cards_widget = QWidget(); self.conv_cards_layout = QVBoxLayout(self.conv_cards_widget); self.conv_cards_layout.setContentsMargins(0, 0, 0, 0); self.conv_cards_layout.setSpacing(6); self.conv_cards_layout.addStretch(); self.conv_scroll.setWidget(self.conv_cards_widget); short_layout.addWidget(self.conv_scroll, 1)
        short_btns = QHBoxLayout(); short_btns.setSpacing(8)
        btn_conv_save = QPushButton("💾 Сохранить изменения"); btn_conv_save.setObjectName("ActionBtn"); btn_conv_save.setMinimumHeight(36); btn_conv_save.clicked.connect(self.save_short_memory); short_btns.addWidget(btn_conv_save); short_layout.addLayout(short_btns); splitter.addWidget(short_frame)
        splitter.setSizes([600, 500]); main_layout.addWidget(splitter)
        maintenance_group = QGroupBox("🛠 Обслуживание системы и резервное копирование"); m_layout = QVBoxLayout(maintenance_group); m_layout.setContentsMargins(16, 16, 16, 16); m_layout.setSpacing(10)
        self.btn_backup = QPushButton("📦 Создать резервную копию"); self.btn_backup.setObjectName("InfoBtn"); self.btn_backup.setMinimumHeight(38); self.btn_backup.clicked.connect(self.create_system_backup); m_layout.addWidget(self.btn_backup)
        self.btn_clear_longterm = QPushButton("🗑️ Очистить долгосрочную память"); self.btn_clear_longterm.setObjectName("DangerBtn"); self.btn_clear_longterm.setMinimumHeight(38); self.btn_clear_longterm.clicked.connect(self.clear_only_longterm_memory); m_layout.addWidget(self.btn_clear_longterm)
        main_layout.addWidget(maintenance_group); self.tabs.addTab(mem_widget, "🧠 Память")
        self._mem_data = {}; self._conv_data = {}; self._mem_cards = []; self._conv_cards = []; self.refresh_memory_tab()

    def _clear_layout(self, layout):
        while layout.count() > 1: item = layout.takeAt(0); item.widget().deleteLater()
    def _make_memory_card(self, record: dict, index: int) -> QWidget:
        p = PALETTES[self._theme]; card = QWidget(); card.setObjectName("MemCard")
        card.setStyleSheet(f"QWidget#MemCard {{ background: {p['bg_elevated']}; border: 1px solid {p['border']}; border-radius: 10px; margin: 2px; }} QWidget#MemCard:hover {{ border-color: {p['border_accent']}; }}")
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(12, 10, 12, 10); card_layout.setSpacing(6)
        header = QHBoxLayout(); header.setSpacing(8)
        type_icons = {"temporary": "⏱", "preference": "⭐", "relationship": "❤️", "session_summary": "📋", "fact": "📌", "skill": "🔧"}
        mem_type, owner, importance = record.get("type", "?"), record.get("owner", "?"), record.get("importance", 0)
        icon = type_icons.get(mem_type, "📝")
        type_lbl = QLabel(f"{icon} {mem_type}"); type_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {p['accent_bright']};"); header.addWidget(type_lbl)
        owner_lbl = QLabel(f"[ {owner} ] "); owner_lbl.setStyleSheet(f"font-size: 10px; color: {p['text_muted']};"); header.addWidget(owner_lbl)
        imp_lbl = QLabel(f"★ {importance}"); imp_lbl.setStyleSheet(f"font-size: 11px; color: {'#f59e0b' if importance >= 7 else p['text_muted']};"); header.addWidget(imp_lbl)
        id_lbl = QLabel(record.get("id", "")[:16] + "…"); id_lbl.setStyleSheet(f"font-size: 9px; color: {p['text_disabled']};"); header.addWidget(id_lbl); header.addStretch()
        btn_del = QPushButton("✕"); btn_del.setObjectName("DangerBtn"); btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet(f"QPushButton {{ background: {p['danger_bg']}; color: {p['danger_fg']}; border: 1px solid {p['danger_border']}; border-radius: 5px; font-size: 11px; font-weight: bold; padding: 0; }} QPushButton:hover {{ background: {p['danger_border']}; color: white; }}")
        btn_del.setProperty("mem_index", index); btn_del.clicked.connect(lambda _, i=index: self._delete_memory_record(i)); header.addWidget(btn_del); card_layout.addLayout(header)
        text_edit = QTextEdit(); text_edit.setPlainText(record.get("text", "")); text_edit.setFixedHeight(62); text_edit.setProperty("mem_index", index)
        text_edit.textChanged.connect(lambda te=text_edit, i=index: self._on_mem_text_changed(te, i)); card_layout.addWidget(text_edit)
        created, expires = record.get("created_at", ""), record.get("expires_at", "")
        dates_lbl = QLabel(f"создано: {created[:10] if created else '—'} | истекает: {expires[:10] if expires else '—'}"); dates_lbl.setStyleSheet(f"font-size: 10px; color: {p['text_disabled']};"); card_layout.addWidget(dates_lbl)
        card._text_edit = text_edit; card._mem_index = index; return card
    def _make_conv_card(self, msg: dict, index: int) -> QWidget:
        p = PALETTES[self._theme]; role = msg.get("role", "user"); content = msg.get("content") or msg.get("text") or msg.get("message") or ""
        role_norm = role.lower()
        if role_norm in ("astra", "assistant", "bot"): role_norm = "astra"
        elif role_norm == "user": role_norm = "user"
        else: role_norm = "system"
        role_colors = {"user": p['accent_bright'], "astra": p['accent_glow'], "system": "#10b981"}
        role_icons = {"user": "👤", "astra": "🤖", "system": "⚙️"}
        role_color, icon = role_colors.get(role_norm, p['text_secondary']), role_icons.get(role_norm, "💬")
        card = QWidget(); card.setObjectName("ConvCard"); card.setStyleSheet(f"QWidget#ConvCard {{ background: {p['bg_elevated']}; border: 1px solid {p['border']}; border-left: 3px solid {role_color}; border-radius: 8px; }}")
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(12, 8, 12, 8); card_layout.setSpacing(5)
        hdr = QHBoxLayout(); role_lbl = QLabel(f"{icon} {role.upper()} #{index+1}"); role_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {role_color};"); hdr.addWidget(role_lbl); hdr.addStretch()
        btn_del = QPushButton("✕"); btn_del.setFixedSize(22, 22)
        btn_del.setStyleSheet(f"QPushButton {{ background: {p['danger_bg']}; color: {p['danger_fg']}; border: 1px solid {p['danger_border']}; border-radius: 5px; font-size: 11px; font-weight: bold; padding: 0; }} QPushButton:hover {{ background: {p['danger_border']}; color: white; }}"); btn_del.clicked.connect(lambda _, i=index: self._delete_conv_message(i)); hdr.addWidget(btn_del); card_layout.addLayout(hdr)
        text_edit = QTextEdit(); text_edit.setPlainText(content); lines = max(3, min(len(content)//80 + content.count('\n')+1, 10)); text_edit.setFixedHeight(lines*19+16)
        text_edit.textChanged.connect(lambda te=text_edit, i=index: self._on_conv_text_changed(te, i)); card_layout.addWidget(text_edit)
        card._text_edit = text_edit; card._conv_index = index; return card

    def refresh_memory_tab(self):
        try: self._mem_data = json.loads(MEMORY_STORE_FILE.read_text(encoding="utf-8")) if MEMORY_STORE_FILE.exists() else {"version": 1, "memories": []}
        except Exception as e: self._mem_data = {"version": 1, "memories": []}; QMessageBox.warning(self, "Ошибка чтения", f"memory_store.json:\n{e}")
        try: self._conv_data = json.loads(CONVERSATION_STATE_FILE.read_text(encoding="utf-8")) if CONVERSATION_STATE_FILE.exists() else {"messages": []}
        except Exception as e: self._conv_data = {"messages": []}; QMessageBox.warning(self, "Ошибка чтения", f"conversation_state.json:\n{e}")
        self._apply_memory_filter(); self._rebuild_conv_cards()
    def _apply_memory_filter(self):
        filter_val = self.cmb_mem_filter.currentText() if hasattr(self, 'cmb_mem_filter') else "Все записи"
        search_val = self.inp_mem_search.text().lower() if hasattr(self, 'inp_mem_search') else ""
        memories = self._mem_data.get("memories", []); self._clear_layout(self.mem_cards_layout); self._mem_cards = []; shown = 0
        for i, record in enumerate(memories):
            if filter_val not in ("Все записи",):
                if record.get("type") != filter_val and record.get("owner") != filter_val: continue
            if search_val and search_val not in record.get("text", "").lower(): continue
            card = self._make_memory_card(record, i); self.mem_cards_layout.insertWidget(self.mem_cards_layout.count()-1, card); self._mem_cards.append(card); shown += 1
        self.lbl_mem_count.setText(f"показано {shown} / {len(memories)}")
    def _rebuild_conv_cards(self):
        messages = self._conv_data.get("messages", []); self._clear_layout(self.conv_cards_layout); self._conv_cards = []
        for i, msg in enumerate(messages): card = self._make_conv_card(msg, i); self.conv_cards_layout.insertWidget(self.conv_cards_layout.count()-1, card); self._conv_cards.append(card)
        self.lbl_msg_count.setText(f"{len(messages)} сообщений")
    def _on_mem_text_changed(self, text_edit: QTextEdit, index: int):
        memories = self._mem_data.get("memories", [])
        if 0 <= index < len(memories): memories[index]["text"] = text_edit.toPlainText()
    def _on_conv_text_changed(self, text_edit: QTextEdit, index: int):
        messages = self._conv_data.get("messages", [])
        if 0 <= index < len(messages):
            msg, new_text = messages[index], text_edit.toPlainText()
            if "content" in msg: msg["content"] = new_text
            elif "text" in msg: msg["text"] = new_text
            else: msg["content"] = new_text
    def _delete_memory_record(self, index: int):
        memories = self._mem_data.get("memories", [])
        if 0 <= index < len(memories): memories.pop(index); self._apply_memory_filter()
    def _delete_conv_message(self, index: int):
        messages = self._conv_data.get("messages", [])
        if 0 <= index < len(messages): messages.pop(index); self._rebuild_conv_cards()
    def add_memory_record(self):
        new_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:16]}"; now_str = datetime.now().isoformat(timespec="seconds")
        new_record = {"id": new_id, "owner": "user", "type": "preference", "text": "", "importance": 5, "confidence": 0.85, "created_at": now_str, "updated_at": now_str, "last_used": None, "usage_count": 0, "expires_at": None, "source": "manual"}
        memories = self._mem_data.setdefault("memories", []); memories.append(new_record); self._apply_memory_filter()
        QTimer.singleShot(100, lambda: self.mem_scroll.verticalScrollBar().setValue(self.mem_scroll.verticalScrollBar().maximum()))
    def save_long_memory(self):
        try:
            current = json.loads(MEMORY_STORE_FILE.read_text(encoding="utf-8")) if MEMORY_STORE_FILE.exists() else {}
            current["memories"] = self._mem_data.get("memories", [])
            if "version" not in current: current["version"] = self._mem_data.get("version", 1)
            MEMORY_STORE_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Успех", "✅ Долгосрочная память сохранена.")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить memory_store.json:\n{e}")
    def save_short_memory(self):
        try:
            current = json.loads(CONVERSATION_STATE_FILE.read_text(encoding="utf-8")) if CONVERSATION_STATE_FILE.exists() else {}
            current["messages"] = self._conv_data.get("messages", [])
            CONVERSATION_STATE_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Успех", "✅ Контекст диалога сохранён.")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить conversation_state.json:\n{e}")

    # =========================================================================
    # ВКЛАДКА 6: МОДЕЛИ (СТРОГО ПО ТЗ)
    # =========================================================================
    def init_models_tab(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(14)
        main_group = QGroupBox("🧠 Основная модель (Ollama)")
        main_form = QFormLayout(main_group); main_form.setSpacing(10); main_form.setContentsMargins(16, 16, 16, 16)
        model_row = QHBoxLayout(); model_row.setSpacing(8)
        self.cmb_main_model = QComboBox(); self.cmb_main_model.setEditable(True); self.cmb_main_model.setInsertPolicy(QComboBox.NoInsert); self.cmb_main_model.setMinimumHeight(34)
        btn_refresh_main = QPushButton("🔄 Обновить список"); btn_refresh_main.setObjectName("InfoBtn"); btn_refresh_main.setFixedHeight(34); btn_refresh_main.clicked.connect(self._refresh_ollama_models)
        model_row.addWidget(self.cmb_main_model); model_row.addWidget(btn_refresh_main); main_form.addRow("Модель:", model_row)
        cfg = self.settings.get("model_presets", {})
        current = self.settings.get("current_model", "mistral-nemo")
        self.cmb_main_model.setCurrentText(current)
        gen = cfg.get(current, {}).get("generation_params", {}) if isinstance(cfg.get(current), dict) else {}
        mem = cfg.get(current, {}).get("memory_analyzer_params", {}) if isinstance(cfg.get(current), dict) else {}
        gen_sub = QGroupBox("Параметры генерации"); gen_sub_form = QFormLayout(gen_sub); gen_sub_form.setContentsMargins(12, 12, 12, 12); gen_sub_form.setSpacing(8)
        self.spin_main_temp = QDoubleSpinBox(); self.spin_main_temp.setRange(0.0, 2.0); self.spin_main_temp.setSingleStep(0.05); self.spin_main_temp.setValue(gen.get("temperature", 0.7))
        self.spin_main_top_p = QDoubleSpinBox(); self.spin_main_top_p.setRange(0.0, 1.0); self.spin_main_top_p.setSingleStep(0.05); self.spin_main_top_p.setValue(gen.get("top_p", 0.9))
        self.spin_main_predict = QSpinBox(); self.spin_main_predict.setRange(16, 4096); self.spin_main_predict.setSingleStep(32); self.spin_main_predict.setValue(gen.get("num_predict", 256))
        self.spin_main_repeat = QDoubleSpinBox(); self.spin_main_repeat.setRange(0.5, 2.0); self.spin_main_repeat.setSingleStep(0.05); self.spin_main_repeat.setValue(gen.get("repeat_penalty", 1.0))
        gen_sub_form.addRow("Температура:", self.spin_main_temp); gen_sub_form.addRow("Top_p:", self.spin_main_top_p)
        gen_sub_form.addRow("Токены ответа:", self.spin_main_predict); gen_sub_form.addRow("Repeat Penalty:", self.spin_main_repeat)
        main_form.addRow(gen_sub)
        mem_sub = QGroupBox("Параметры анализатора памяти"); mem_sub_form = QFormLayout(mem_sub); mem_sub_form.setContentsMargins(12, 12, 12, 12); mem_sub_form.setSpacing(8)
        self.spin_mem_temp = QDoubleSpinBox(); self.spin_mem_temp.setRange(0.0, 1.0); self.spin_mem_temp.setSingleStep(0.05); self.spin_mem_temp.setValue(mem.get("temperature", 0.1))
        self.spin_mem_predict = QSpinBox(); self.spin_mem_predict.setRange(16, 512); self.spin_mem_predict.setSingleStep(16); self.spin_mem_predict.setValue(mem.get("num_predict", 100))
        mem_sub_form.addRow("Температура:", self.spin_mem_temp); mem_sub_form.addRow("Токены ответа:", self.spin_mem_predict)
        main_form.addRow(mem_sub)
        layout.addWidget(main_group)
        orch_group = QGroupBox("⚡ Оркестратор (Ollama)")
        orch_form = QFormLayout(orch_group); orch_form.setSpacing(10); orch_form.setContentsMargins(16, 16, 16, 16)
        self.chk_orch_enabled = QCheckBox("Включить оркестратор"); self.chk_orch_enabled.setChecked(self.settings.get("orchestrator_enabled", True))
        self.chk_orch_enabled.stateChanged.connect(self._update_orch_status)
        self.lbl_orch_status = QLabel("● Отключен"); self.lbl_orch_status.setStyleSheet("color: #ef4444; font-weight: bold;")
        orch_status_row = QHBoxLayout(); orch_status_row.setSpacing(8); orch_status_row.addWidget(self.chk_orch_enabled); orch_status_row.addWidget(self.lbl_orch_status); orch_status_row.addStretch(); orch_form.addRow(orch_status_row)
        orch_model_row = QHBoxLayout(); orch_model_row.setSpacing(8)
        self.cmb_orch_model = QComboBox(); self.cmb_orch_model.setEditable(True); self.cmb_orch_model.setInsertPolicy(QComboBox.NoInsert); self.cmb_orch_model.setMinimumHeight(34)
        self.cmb_orch_model.setCurrentText(self.settings.get("orchestrator_model", "phi3:mini"))
        btn_refresh_orch = QPushButton("🔄"); btn_refresh_orch.setObjectName("InfoBtn"); btn_refresh_orch.setFixedSize(34, 34); btn_refresh_orch.clicked.connect(lambda: self._refresh_ollama_models(True))
        orch_model_row.addWidget(self.cmb_orch_model); orch_model_row.addWidget(btn_refresh_orch); orch_form.addRow("Модель оркестратора:", orch_model_row)
        orch_p_sub = QGroupBox("Параметры оркестратора"); orch_p_form = QFormLayout(orch_p_sub); orch_p_form.setContentsMargins(12, 12, 12, 12); orch_p_form.setSpacing(8)
        ocfg = self.settings.get("orchestrator_params", {})
        self.spin_orch_temp = QDoubleSpinBox(); self.spin_orch_temp.setRange(0.0, 1.0); self.spin_orch_temp.setSingleStep(0.05); self.spin_orch_temp.setValue(ocfg.get("temperature", 0.0))
        self.spin_orch_top_p = QDoubleSpinBox(); self.spin_orch_top_p.setRange(0.0, 1.0); self.spin_orch_top_p.setSingleStep(0.05); self.spin_orch_top_p.setValue(ocfg.get("top_p", 0.8))
        self.spin_orch_predict = QSpinBox(); self.spin_orch_predict.setRange(10, 200); self.spin_orch_predict.setSingleStep(10); self.spin_orch_predict.setValue(ocfg.get("num_predict", 30))
        orch_p_form.addRow("Температура:", self.spin_orch_temp); orch_p_form.addRow("Top_p:", self.spin_orch_top_p); orch_p_form.addRow("Max токенов:", self.spin_orch_predict)
        orch_form.addRow(orch_p_sub)
        layout.addWidget(orch_group)
        btn_save_models = QPushButton("💾 Сохранить настройки моделей"); btn_save_models.setObjectName("SuccessBtn"); btn_save_models.setMinimumHeight(38); btn_save_models.clicked.connect(self.save_model_settings)
        layout.addWidget(btn_save_models); layout.addStretch(); scroll.setWidget(widget); self.tabs.addTab(scroll, "🤖 Модели")
        self._update_orch_status(); QTimer.singleShot(200, self._refresh_ollama_models)

    def _refresh_ollama_models(self, only_orch=False):
        try:
            proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                lines = proc.stdout.strip().splitlines()
                models = [line.split()[0] for line in lines[1:] if line.strip()]
                self.cmb_main_model.blockSignals(True); self.cmb_orch_model.blockSignals(True)
                current_main = self.cmb_main_model.currentText(); current_orch = self.cmb_orch_model.currentText()
                if not only_orch:
                    self.cmb_main_model.clear(); self.cmb_main_model.addItems(models); self.cmb_main_model.setCurrentText(current_main)
                self.cmb_orch_model.clear(); self.cmb_orch_model.addItems(models); self.cmb_orch_model.setCurrentText(current_orch)
                self.cmb_main_model.blockSignals(False); self.cmb_orch_model.blockSignals(False)
        except Exception as e: QMessageBox.warning(self, "Ollama недоступен", f"Не удалось получить список моделей:\n{e}")

    def _update_orch_status(self):
        if self.chk_orch_enabled.isChecked(): self.lbl_orch_status.setText("● Активен"); self.lbl_orch_status.setStyleSheet("color: #4ade80; font-weight: bold;")
        else: self.lbl_orch_status.setText("● Отключен"); self.lbl_orch_status.setStyleSheet("color: #ef4444; font-weight: bold;")

    @Slot()
    def save_model_settings(self):
        try:
            current_settings = load_settings(); main_model = self.cmb_main_model.currentText().strip()
            if not main_model: raise ValueError("Имя основной модели не указано")
            current_settings["current_model"] = main_model
            if "model_presets" not in current_settings or not isinstance(current_settings["model_presets"], dict): current_settings["model_presets"] = {}
            if main_model not in current_settings["model_presets"]: current_settings["model_presets"][main_model] = {}
            current_settings["model_presets"][main_model]["generation_params"] = {"temperature": round(self.spin_main_temp.value(), 2), "top_p": round(self.spin_main_top_p.value(), 2), "num_predict": self.spin_main_predict.value(), "repeat_penalty": round(self.spin_main_repeat.value(), 2)}
            current_settings["model_presets"][main_model]["memory_analyzer_params"] = {"temperature": round(self.spin_mem_temp.value(), 2), "num_predict": self.spin_mem_predict.value()}
            current_settings["orchestrator_model"] = self.cmb_orch_model.currentText().strip() or "phi3:mini"
            current_settings["orchestrator_enabled"] = self.chk_orch_enabled.isChecked()
            current_settings["orchestrator_params"] = {"temperature": round(self.spin_orch_temp.value(), 2), "top_p": round(self.spin_orch_top_p.value(), 2), "num_predict": self.spin_orch_predict.value()}
            save_settings(current_settings); self.settings = current_settings; QMessageBox.information(self, "Успех", "Настройки моделей сохранены!")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    # =========================================================================
    # БИЗНЕС-ЛОГИКА
    # =========================================================================
    def send_message(self):
        text = self.chat_input.text().strip(); p = PALETTES[self._theme]
        if not text: return
        self.chat_display.append(f'<div style="margin:6px 0;"><span style="color:{p["accent_bright"]};font-weight:bold;">Вы </span><span style="color:{p["text_muted"]};"> ▸ </span><span style="color:{p["text_primary"]};">{text}</span></div>')
        self.chat_input.clear(); touch_user_activity("ui"); self.btn_send.setEnabled(False); self.chat_input.setPlaceholderText("⏳ Думает...")
        self.worker = AstraWorker(self.astra, text); self.worker.reply_received.connect(self.on_reply_received); self.worker.start()

    @Slot(str, str, str)
    def on_reply_received(self, answer, memory_log, rel_log):
        self.btn_send.setEnabled(True); self.chat_input.setPlaceholderText(f"  Написать {self.character_name}...")
        p = PALETTES[self._theme]
        self.chat_display.append(f'<div style="margin:6px 0; padding:10px 14px; background:{p["chat_msg_bg"]}; border-left:3px solid {p["chat_msg_border"]}; border-radius:6px;"><span style="color:{p["accent_glow"]};font-weight:bold;">{self.character_name} </span><span style="color:{p["text_muted"]};"> ▸ </span><span style="color:{p["text_primary"]};">{answer}</span></div><br>')
        if memory_log: self.log_memory.append(f'<span style="color:{p["accent_bright"]};">{memory_log}</span>')
        if rel_log: self.log_relations.append(f'<span style="color:#10b981;">{rel_log}</span>')
        self.load_relationship_bars(); self.refresh_relationship_inputs()

    def load_relationship_bars(self):
        state = load_relationship_state(); depth = state.get("relationship_depth", 0); self.pbar_depth.setValue(min(depth, 1000))
        current_stage = "acquaintance"
        for low, high, stage_name in STAGE_THRESHOLDS:
            if low <= depth <= high: current_stage = stage_name; break
        self.lbl_stage.setText(f"✦ {current_stage.upper()}\nDepth: {depth}")
        for key in self.bars:
            if key in state: self.bars[key].setValue(int(state[key]))

    def refresh_relationship_inputs(self):
        state = load_relationship_state()
        for key, inp in self.rel_inputs.items():
            if not inp.isEnabled(): inp.setText(str(state.get(key, "")))

    def unlock_relations(self):
        dlg = MemeConfirmDialog(self, "unlock", self._theme)
        if dlg.exec() == QDialog.Accepted:
            for inp in self.rel_inputs.values(): inp.setEnabled(True)
            self.btn_apply_rel.setEnabled(True); self.btn_unlock.setText("🔓 Разблокировано"); self.btn_unlock.setEnabled(False)

    @Slot()
    def save_manual_relations(self):
        state = load_relationship_state()
        try:
            for key, inp in self.rel_inputs.items():
                if key in ["relationship_depth", "affection", "trust", "comfort", "anger", "mood", "discomfort"]: state[key] = int(inp.text().strip())
            save_relationship_state(state); self.load_relationship_bars()
            for inp in self.rel_inputs.values(): inp.setEnabled(False)
            self.btn_apply_rel.setEnabled(False); self.btn_unlock.setText("🔓 Разблокировать редактирование"); self.btn_unlock.setEnabled(True)
            QMessageBox.information(self, "Успех", "✅ Изменения успешно внесены в ядро!")
        except ValueError: QMessageBox.critical(self, "Ошибка", "Все поля должны содержать только целые числа!")

    def clear_current_chat(self):
        dlg = MemeConfirmDialog(self, "clear_chat", self._theme)
        if dlg.exec() == QDialog.Accepted:
            close_current_session()   # закрываем старую сессию
            start_new_session()       # начинаем новую
            clear_state()             # очищаем краткосрочную память
            self.astra.conversation.local_history.clear()  # очищаем локальную историю
            self.chat_display.clear()
            self.chat_display.append('<i>〔Система: Начата новая сессия.〕</i>')

    def toggle_service(self, name, checked):
        if checked: self.service_manager.start(name)
        else: self.service_manager.stop(name)

    def clear_only_longterm_memory(self):
        dlg = MemeConfirmDialog(self, "clear_memory", self._theme)
        if dlg.exec() == QDialog.Accepted:
            try: clear_all_memories(); QMessageBox.information(self, "Успех", "Долгосрочная память успешно очищена!")
            except Exception as e: QMessageBox.critical(self, "Ошибка", f"Не удалось очистить память: {e}")

    def create_system_backup(self):
        try:
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True); timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); copied_files = []
            for default_name, src_path in {"conversation_state.json": CONVERSATION_STATE_FILE, "memory_store.json": MEMORY_STORE_FILE, "relationship_state.json": RELATIONSHIP_FILE}.items():
                if src_path.exists():
                    parts = default_name.split("."); shutil.copy2(src_path, BACKUPS_DIR / f"{parts[0]}_{timestamp}.{parts[1]}"); copied_files.append(default_name)
            if copied_files: QMessageBox.information(self, "📦 Бэкап завершен", f"Архивировано файлов: {len(copied_files)}\n({', '.join(copied_files)})\nПапка: backups/")
            else: QMessageBox.warning(self, "Внимание", "Файлы стейтов не найдены.")
        except Exception as e: QMessageBox.critical(self, "Ошибка", f"Ошибка при бэкапе: {e}")

    def closeEvent(self, event):
        try: analyze_current_session(); from astra_core.memory_cleanup import cleanup_memory_store; cleanup_memory_store(); close_current_session(); self.service_manager.stop_all()
        except Exception: pass
        event.accept()

# =====================================================================
# ТОЧКА ВХОДА
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv); window = AstraUI(); window.show(); sys.exit(app.exec())