import os
import shutil
import json
from datetime import datetime

VCS_DIR = ".myvcs"
VERSIONS_DIR = os.path.join(VCS_DIR, "versions")
HISTORY_FILE = os.path.join(VCS_DIR, "history.json")

def init_vcs():
    os.makedirs(VERSIONS_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

def get_next_version():
    if not os.path.exists(HISTORY_FILE):
        return "0001"
    with open(HISTORY_FILE) as f:
        history = json.load(f)
    return f"{len(history)+1:04d}"

def commit(files, message):
    version = get_next_version()
    version_path = os.path.join(VERSIONS_DIR, version)
    os.makedirs(version_path)
    for file in files:
        shutil.copy2(file, version_path)
    # 记录历史
    with open(HISTORY_FILE) as f:
        history = json.load(f)
    history.append({
        "version": version,
        "message": message,
        "files": files,
        "time": datetime.now().isoformat()
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def log():
    with open(HISTORY_FILE) as f:
        history = json.load(f)
    for entry in history:
        print(f"Version: {entry['version']}, Time: {entry['time']}, Message: {entry['message']}")

def checkout(version):
    version_path = os.path.join(VERSIONS_DIR, version)
    if not os.path.exists(version_path):
        print("Version not found!")
        return
    for file in os.listdir(version_path):
        shutil.copy2(os.path.join(version_path, file), file)
