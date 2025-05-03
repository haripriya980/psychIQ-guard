import os
import sys
import time
import json
import requests
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from notion_logger import log_to_notion
import hashlib
last_logged_hash = None
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
print("🔐 Loaded OPENROUTER_API_KEY:", os.getenv("OPENROUTER_API_KEY"))

# === Fix import path for notion_logger ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 # ✅ Will work now

# === CONFIG ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

JOURNAL_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "journal"))
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "triage_log.json"))

# === Emotion Severity Detection ===
def analyze_text_with_openrouter(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a clinical mental health triage assistant. "
                    "Given a journal entry, classify the emotional severity as one of the following:\n"
                    "- HIGH: suicidal ideation, emotional collapse, or crisis\n"
                    "- MEDIUM: depression, burnout, emotional fatigue\n"
                    "- LOW: calm, neutral, or non-urgent tone\n"
                    "Respond ONLY with one word: LOW, MEDIUM, or HIGH"
                )
            },
            {
                "role": "user",
                "content": f"Classify this journal entry:\n\n{text.strip()}"
            }
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        print("📨 Raw response (risk):", data)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
        return content if content in {"LOW", "MEDIUM", "HIGH"} else "UNKNOWN"
    except Exception as e:
        print("❌ OpenRouter error:", e)
        return "ERROR"

# === Emotion Type Detection ===
def detect_emotion_type(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = (
        "You are a mental health emotion classifier. "
        "Given a journal entry, identify the dominant emotion using ONE word only. "
        "Possible emotions include: SADNESS, ANGER, ANXIETY, ISOLATION, OVERWHELMED, NUMB, HOPEFUL, EMPTY.\n"
        "Respond ONLY with one word from this list."
    )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text.strip()}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        print("📨 Raw response (emotion):", data)
        emotion = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
        return emotion if emotion.isalpha() else "UNKNOWN"
    except Exception as e:
        print("❌ Emotion classifier error:", e)
        return "UNKNOWN"

# === Log Entry ===
def log_risk_entry(entry_path, text, risk_level, emotion_type):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file": os.path.basename(entry_path),
        "text_snippet": text.strip()[:100],
        "risk": risk_level,
        "emotion": emotion_type
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.insert(0, entry)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("❌ Log write error:", e)

# === File Watcher ===
class JournalHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_logged_hash
        if not event.is_directory and event.src_path.endswith(".txt"):
            try:
                with open(event.src_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    content_hash = hashlib.sha256(content.encode()).hexdigest()

                    if content_hash == last_logged_hash:
                        return  # 🚫 Prevent duplicate logging

                    last_logged_hash = content_hash

                    print(f"\n📝 New Journal Update: {event.src_path}")
                    urgency = analyze_text_with_openrouter(content)
                    emotion = detect_emotion_type(content)
                    print(f"🔍 Risk Level: {urgency}")
                    print(f"🧠 Emotion Detected: {emotion}")
                    log_risk_entry(event.src_path, content, urgency, emotion)

                    if urgency == "HIGH":
                        print("🚨 ALERT: High-risk content detected.")
                        log_to_notion(content, urgency)

            except Exception as e:
                print("❌ File read error:", e)


# === Watch Folder Setup ===
if __name__ == "__main__":
    if not os.path.exists(JOURNAL_FOLDER):
        os.makedirs(JOURNAL_FOLDER)

    print(f"📂 Watching journal folder: {JOURNAL_FOLDER}")
    event_handler = JournalHandler()
    observer = Observer()
    observer.schedule(event_handler, JOURNAL_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

#OPEN Router API KEY KEEP IT SAFE DO NOT LOSE IT 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