import os
import sys
import json
import urllib.request
import subprocess
import shutil

REPO_OWNER = "anhedonuya"
REPO_NAME = "UniInARow"
FILES_TO_UPDATE = ["game.py", "version.txt"]
LOCAL_VERSION_FILE = "version.txt"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"

def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return "0.0.0"
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()

def get_remote_version():
    try:
        url = f"{GITHUB_API_URL}version.txt"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3.raw"})
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8").strip()
    except Exception:
        return None

def download_file(filename):
    try:
        url = f"{GITHUB_API_URL}{filename}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3.raw"})
        with urllib.request.urlopen(req) as response:
            content = response.read()
            with open(filename, "wb") as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"Ошибка скачивания {filename}: {e}")
        return False

def update_game():
    print("🔄 Обновление...")
    for f in FILES_TO_UPDATE:
        if not download_file(f):
            print(f"❌ Ошибка обновления {f}")
            return False
    print("✅ Обновление завершено!")
    return True

def restart_game():
    """Перезапускает игру без консоли"""
    try:
        # Пытаемся найти pythonw.exe
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.path.exists(pythonw):
            subprocess.Popen([pythonw, "game.py"], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Если pythonw нет — запускаем через python
            subprocess.Popen([sys.executable, "game.py"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        # Запасной вариант через run.bat
        subprocess.Popen(["run.bat"], shell=True)
    sys.exit(0)

def main():
    local = get_local_version()
    remote = get_remote_version()
    
    if remote is None:
        print("❌ Не удалось проверить обновления")
        sys.exit(1)
    
    if local != remote:
        print(f"📦 Доступно обновление: {local} → {remote}")
        if update_game():
            print("🔄 Перезапуск игры...")
            restart_game()
        else:
            print("❌ Ошибка обновления")
            sys.exit(1)
    else:
        print("✅ Игра актуальна")
        sys.exit(0)

if __name__ == "__main__":
    main()