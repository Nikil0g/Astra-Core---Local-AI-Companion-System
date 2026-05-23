import subprocess
import os
from .settings import get_setting, BASE_DIR

PYTHON = get_setting("python_path", "python")

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.service_list = {
            "initiative": "astra_core_initiative.py",
            "voice": "astra_voice.py",
        }

    def start(self, name):
        if name not in self.service_list:
            return False, f"Unknown service: {name}"
        if name in self.services and self.services[name].poll() is None:
            return False, f"{name} already running"
        script = self.service_list[name]
        path = os.path.join(BASE_DIR, script)
        self.services[name] = subprocess.Popen([PYTHON, path], cwd=str(BASE_DIR))
        return True, f"{name} started"

    def stop(self, name):
        if name not in self.service_list:
            return False, f"Unknown service: {name}"
        proc = self.services.get(name)
        if not proc or proc.poll() is not None:
            return False, f"{name} not running"
        proc.terminate()
        return True, f"{name} stopped"

    def status(self, name):
        proc = self.services.get(name)
        if proc and proc.poll() is None:
            return "running"
        return "stopped"

    def status_all(self):
        return {name: self.status(name) for name in self.service_list}

    def start_all(self):
        results = {}
        for name in self.service_list:
            success, msg = self.start(name)
            results[name] = {"success": success, "message": msg}
        return results

    def stop_all(self):
        results = {}
        for name in self.service_list:
            success, msg = self.stop(name)
            results[name] = {"success": success, "message": msg}
        return results