import subprocess
import os
from astra_core.settings import get_setting

PYTHON = get_setting("python_path")
BASE_DIR = get_setting("base_dir")

services = {}

# TODO:
# Future GUI / tray manager:
# - start/stop services from UI
# - service status indicators
# - auto-start selected modules
# - background tray mode
# - voice toggle
# - initiative toggle
# - avatar toggle

SERVICE_LIST = {
    "initiative": "astra_core_initiative.py",
    "voice": "astra_voice.py",
}

def start_service(name):
    if name in services and services[name].poll() is None:
        print(f"{name} уже запущен.")
        return

    script = SERVICE_LIST[name]
    path = os.path.join(BASE_DIR, script)

    services[name] = subprocess.Popen(
        [PYTHON, path],
        cwd=BASE_DIR
    )

    print(f"{name} запущен.")

def stop_service(name):
    proc = services.get(name)

    if not proc or proc.poll() is not None:
        print(f"{name} не запущен.")
        return

    proc.terminate()
    print(f"{name} остановлен.")

def status():
    for name in SERVICE_LIST:
        proc = services.get(name)
        state = "работает" if proc and proc.poll() is None else "остановлен"
        print(f"{name}: {state}")

def start_all():
    start_service("initiative")
    start_service("voice")

def stop_all():
    for name in SERVICE_LIST:
        stop_service(name)

while True:
    print("\n=== ASTRA CONTROL ===")
    print("1. Запустить всё")
    print("2. Остановить всё")
    print("3. Статус")
    print("4. Запустить инициативность")
    print("5. Запустить голос")
    print("6. Остановить инициативность")
    print("7. Остановить голос")
    print("0. Выход")

    choice = input("> ").strip()

    if choice == "1":
        start_all()
    elif choice == "2":
        stop_all()
    elif choice == "3":
        status()
    elif choice == "4":
        start_service("initiative")
    elif choice == "5":
        start_service("voice")
    elif choice == "6":
        stop_service("initiative")
    elif choice == "7":
        stop_service("voice")
    elif choice == "0":
        stop_all()
        break
    else:
        print("Неизвестная команда.")