import time
import queue
import uuid
import os
import requests
import numpy as np
import keyboard
import sounddevice as sd
import pygame
from scipy.io.wavfile import write as write_wav
from faster_whisper import WhisperModel

from astra_core.core import AstraCore
from astra_core.character_profile import get_character_name
from astra_core.activity import touch_user_activity
from astra_core.settings import get_setting
from astra_core.short_term_memory import add_message
from astra_core.conversation_meta import mark_user_message, mark_astra_message

# Voice / STT settings
TTS_URL = get_setting("tts_url")
TTS_VOICE = get_setting("tts_voice")
MIC_DEVICE = get_setting("mic_device")
SAMPLE_RATE = get_setting("sample_rate")
PUSH_TO_TALK_KEY = get_setting("push_to_talk_key")
WHISPER_MODEL = get_setting("whisper_model")
WHISPER_DEVICE = get_setting("whisper_device")
WHISPER_COMPUTE_TYPE = get_setting("whisper_compute_type")

audio_queue = queue.Queue()
whisper = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE,
)
astra = AstraCore()
CHARACTER_NAME = get_character_name()

def speak_text(text: str) -> None:
    audio_file = None
    try:
        response = requests.post(
            TTS_URL,
            json={"text": text, "speaker": TTS_VOICE},
            timeout=30
        )
        response.raise_for_status()
        
        audio_file = f"voice_output_{uuid.uuid4().hex}.wav"
        with open(audio_file, "wb") as f:
            f.write(response.content)
            
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        
    except Exception as e:
        print("[TTS ERROR]", e)
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception:
                pass

def callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

def record_push_to_talk() -> bool:
    print(f"\n[Зажми {PUSH_TO_TALK_KEY.upper()} для записи...]")
    keyboard.wait(PUSH_TO_TALK_KEY)
    
    audio_data = []
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, device=MIC_DEVICE, callback=callback):
        print("Запись пошла... Отпусти клавишу для завершения.")
        while keyboard.is_pressed(PUSH_TO_TALK_KEY):
            try:
                data = audio_queue.get_nowait()
                audio_data.append(data)
            except queue.Empty:
                time.sleep(0.02)
                
    if not audio_data:
        print("Запись пуста.")
        return False
        
    audio = np.concatenate(audio_data, axis=0)
    write_wav("voice_input.wav", SAMPLE_RATE, audio)
    print("Запись остановлена.")
    return True

def transcribe_audio() -> str:
    segments, info = whisper.transcribe(
        "voice_input.wav",
        language="ru",
        beam_size=5,
        vad_filter=True,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()

def main() -> None:
    print(f"{CHARACTER_NAME} Voice Mode запущен.")
    print(f"Зажми {PUSH_TO_TALK_KEY.upper()}, чтобы говорить.")
    print("Ctrl + C для выхода.")

    while True:
        try:
            recorded = record_push_to_talk()

            if not recorded:
                continue

            user_text = transcribe_audio()
            print("Ты:", user_text)

            if not user_text:
                print(f"{CHARACTER_NAME}: я не расслышала...")
                continue

            touch_user_activity("voice")

            # Фиксация реплики пользователя в общей памяти проекта
            add_message("user", user_text)
            mark_user_message()

            # Генерация ответа через ядро (внутри core.py также пишутся логи)
            answer = astra.reply(user_text)
            print(f"{CHARACTER_NAME}:", answer)

            # Фиксация ответа Astra
            add_message("astra", answer)
            mark_astra_message()

            speak_text(answer)

        except KeyboardInterrupt:
            print("\nVoice Mode остановлен.")
            break

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()