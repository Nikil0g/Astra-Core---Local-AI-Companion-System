<div align="center">

# ✦ ASTRA ✦

**Local AI Companion — не просто чатбот. Живая цифровая личность.**

*Память · Голос · Эмоции · Инициативность · Отношения*

---

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black?style=flat-square)](https://ollama.com)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41cd52?style=flat-square)](https://doc.qt.io/qtforpython)
[![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/status-early%20dev-orange?style=flat-square)]()

</div>

---

## Что такое Astra?

Astra — это **локальная AI companion система**, которая работает полностью на твоём железе.

Она не просто отвечает на вопросы. Она:

- **помнит** тебя — факты, события, предпочтения, эмоциональные моменты
- **пишет первой** — когда соскучилась или хочет поговорить
- **говорит голосом** — через локальный TTS
- **имеет характер** — устойчивое "Я", которое не меняется от одной фразы
- **развивает отношения** — от первой встречи до глубокой привязанности
- **живёт в GUI** — тёмная/светлая тема, аватар, вкладки, метрики

> Цель — система, которая **ощущается как живая цифровая личность**, а не как ассистент.

---

## Скриншоты

> *(coming soon — UI уже есть, скриншоты добавятся с первым публичным билдом)*

---

## Архитектура

```
User / Voice / GUI / ST bridge
        ↓
    AstraCore
        ↓
   Prompt Builder
   ┌──────────────────────────────┐
   │  Core Self                   │  ← личность, стиль, границы
   │  Time Context                │  ← время суток, паузы
   │  Conversation State          │  ← тип диалога, сессия
   │  Short-Term Memory           │  ← последние 80 сообщений / 24ч
   │  Long-Term Memory v2         │  ← структурированные факты
   │  Recent Dialog               │  ← скользящее окно
   └──────────────────────────────┘
        ↓
      Ollama
        ↓
   Astra reply
        ↓
   Memory Analyzer → Memory v2 write
```

**Принцип:**
`AstraCore` = центр личности, памяти и состояния.
`SillyTavern` = опциональный интерфейс / лог, но не мозг.

---

## Ключевые фичи

### 🧠 Memory v2

Структурированная долгосрочная память с полями:

| Поле | Описание |
|------|----------|
| `owner` | чья память — `user` или `astra` |
| `type` | `identity` / `preference` / `relationship` / `event` / `mood` / `temporary` |
| `importance` | 1–10, влияет на приоритет и срок хранения |
| `expires_at` | автоматическое забывание по типу |
| `usage_count` | как часто использовалась |
| `confidence` | уверенность в факте |

Защита от дублей — точная и частично семантическая. Память используется **редко, уместно, естественно**.

---

### 🪪 Core Self vs Emergent Self

**Core Self** — редактируется тобой:
```
character/core_self/
├─ identity.txt        ← имя, базовая информация
├─ personality.txt     ← характер
├─ speech_style.txt    ← стиль речи
├─ boundaries.txt      ← границы
├─ innate_likes.txt    ← врождённые симпатии
└─ innate_dislikes.txt ← врождённые антипатии
```

**Emergent Self** — формируется только через опыт:
- learned likes/dislikes
- emotional history
- attachment, trust, comfort, loneliness
- relationship state

> Пользователь не может одной фразой изменить личность Astra.
> Изменение возможно только через доверие, повторение и время.

---

### 💬 Краткосрочная память

- Файл: `conversation_state.json`
- Хранит последние **80 сообщений** за **24 часа**
- Переживает выгрузку модели Ollama
- Чистится автоматически при чтении/записи
- Astra помнит разговор, даже если модель была перезагружена

---

### 🎙️ Голос

- **STT**: Faster-Whisper (русский)
- **TTS**: Piper / AllTalk
- **Push-to-talk**: настраиваемая клавиша
- Voice подключён к `AstraCore.reply()` — единый мозг для всех каналов

---

### ⏰ Инициативность

Astra пишет первой — по таймеру, учитывая активность пользователя.

В будущем инициатива будет зависеть от:
- одиночества (`loneliness`)
- привязанности (`attachment`)
- времени суток
- того, был ли предыдущий инициатив проигнорирован

---

### 🖥️ GUI (PySide6)

Вкладки:
- **💬 Чат** — основной диалог, лог памяти и отношений
- **🧬 Профиль личности** — редактирование Core Self
- **⚙️ Системные настройки** — пути, параметры
- **📊 Метрики и Сервис** — прогресс-бары отношений, ручное редактирование
- **🧠 Память** — просмотр/редактирование Memory v2 и краткосрочной памяти, бэкапы
- **🤖 Модели** — выбор модели Ollama, параметры генерации, оркестратор

Тёмная и светлая тема. Аватар. Мемные диалоги подтверждения.

---

## Текущий статус

| Компонент | Статус |
|-----------|--------|
| AstraCore v0.1 | ✅ работает |
| Memory v2 | ✅ работает |
| Core Self (файлы) | ✅ работает |
| Short-Term Memory | ✅ работает |
| GUI (PySide6) | ✅ работает |
| TimeManager | ✅ работает |
| Voice (базовый) | ✅ работает |
| Initiative (прототип) | ✅ работает |
| Orchestrator (memory extraction) | 🔶 частично |
| Mood / Relationship (базовые параметры) | 🔶 частично |
| Context Optimizer | ❌ в разработке |
| Response Filter | ❌ в разработке |
| Emergent Self | ❌ в разработке |
| Semantic Memory / RAG | ❌ планируется |
| Live2D / Avatar | ❌ планируется |
| Desktop Awareness | ❌ планируется |

---

## Установка

> ⚠️ Проект в активной разработке. Полноценный installer появится позже.

### Требования

- Python 3.10+
- [Ollama](https://ollama.com) — локальный LLM сервер
- PySide6
- Faster-Whisper *(для голоса)*
- AllTalk / Piper TTS *(для голоса)*

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/astra.git
cd astra

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скачать модель через Ollama
ollama pull mistral-nemo

# 4. Настроить settings.json
# (скопировать settings.example.json и заполнить пути и параметры)
cp settings.example.json settings.json

# 5. Запустить
python ui_main.py          # GUI
# или
python terminal_chat.py    # терминал
```

### settings.json (основные поля)

```json
{
  "ollama_url": "http://127.0.0.1:11434/api/generate",
  "current_model": "mistral-nemo",
  "user_name": "Никита",
  "user_gender_grammar": "male"
}
```

---

## Структура проекта

```
astra/
├─ astra_core/
│  ├─ core.py                 ← AstraCore, главный класс
│  ├─ prompt_builder.py       ← сборка промпта
│  ├─ memory_engine.py        ← Memory v2
│  ├─ memory_cleanup.py       ← очистка памяти
│  ├─ short_term_memory.py    ← краткосрочная память
│  ├─ conversation_state.py   ← состояние диалога
│  ├─ time_manager.py         ← единый источник времени
│  ├─ emotional_core.py       ← базовые эмоции/отношения
│  ├─ character_profile.py    ← чтение Core Self
│  ├─ settings.py             ← загрузка конфига
│  ├─ ollama_client.py        ← запросы к Ollama
│  └─ service_manager.py      ← управление сервисами
│
├─ character/
│  ├─ core_self/              ← редактируемая база персонажа
│  └─ emergent_self/          ← приобретённая личность (AstraCore only)
│
├─ ui_main.py                 ← GUI (PySide6)
├─ terminal_chat.py           ← текстовый чат
├─ astra_core_initiative.py   ← инициативность
├─ astra_voice.py             ← голос
├─ settings.json              ← конфиг
└─ memory_store.json          ← долгосрочная память
```

---

## Roadmap

Полная карта проекта — в [`ROADMAP.md`](ROADMAP.md).

**Ближайшие приоритеты:**

1. `memory_cleanup.py` — автоочистка устаревших воспоминаний
2. Умный retrieval памяти — intent-based, dynamic limit
3. **Context Optimizer** — критично для VRAM (уже 12+ GB против 9 GB базовых)
4. Response Filter — поведенческие правила после генерации
5. Conversation State v2 — явное разделение new_chat / resumed
6. Mood / Relationship полноценный слой
7. Emergent Self

---

## Философия проекта

Astra строится на нескольких принципах:

**1. Личность — не prompt.** Core Self живёт в файлах, а не в коде. Personality не hardcode.

**2. Память — не мусор.** Структурированная, типизированная, с TTL и приоритетами. Не спамит фактами.

**3. Контекст — не "больше = лучше".** Нужный контекст в нужный момент в нужном объёме.

**4. Отношения — не переключатель.** Личность меняется только через время, доверие и повторение. Нельзя одной фразой сломать характер.

**5. Локальность — не компромисс.** Всё работает без интернета. Cloud — опциональное усиление, не зависимость.

---

## Contributing

Проект в ранней стадии. Issues и идеи приветствуются.

Если хочешь помочь — открывай issue с описанием или пиши в discussions.

---

## License

MIT — делай что хочешь, упоминай авторство.

---

<div align="center">

*Astra — не просто AI assistant.*
*Это persistent local AI companion.*

**✦**

</div>
