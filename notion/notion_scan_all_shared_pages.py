import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib

# === Load .env ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
ALERT_EMAIL = os.getenv("ALERT_EMAIL_ADDRESS")
ALERT_PASS = os.getenv("ALERT_EMAIL_PASSWORD")
TO_EMAIL = os.getenv("ALERT_TO_EMAIL")
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "page_triage_log.json")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"
}

# === Fetch shared pages (manual list for now) ===
SHARED_PAGES = [os.getenv("NOTION_JOURNAL_PAGE_ID")]

# === Fetch blocks recursively ===
def fetch_page_blocks(page_id):
    def recurse_blocks(block_id):
        try:
            url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
            res = requests.get(url, headers=HEADERS)
            res.raise_for_status()
            blocks = res.json().get("results", [])
            content = []
            for block in blocks:
                block_type = block.get("type")
                text_items = block.get(block_type, {}).get("rich_text", [])
                for item in text_items:
                    content.append(item.get("plain_text", ""))
                if block.get("has_children"):
                    content += recurse_blocks(block["id"])
            return content
        except Exception as e:
            print(f"❌ Error reading block {block_id}:", e)
            return []

    return "\n".join(recurse_blocks(page_id))

# === OpenRouter classify ===
def classify_text(text, prompt_type):
    system_prompt = {
        "risk": "You are a clinical mental health triage assistant. Assess severity (LOW, MEDIUM, HIGH) and explain briefly.",
        "emotion": "You are a mental health assistant. Identify the dominant emotion in ONE word (e.g., SADNESS, ANGER, NUMB...)."
    }[prompt_type]

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text.strip()}
        ]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                            json=payload)
        data = res.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print("❌ Classification error:", e)
        return "UNKNOWN"

# === Email alert ===
def send_email(subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = ALERT_EMAIL
        msg["To"] = TO_EMAIL
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(ALERT_EMAIL, ALERT_PASS)
            smtp.send_message(msg)
        print("📧 Email alert sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)

# === Main Execution ===
def main():
    print("📘 Scanning all shared Notion pages...")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    for page_id in SHARED_PAGES:
        print(f"🔍 Scanning page {page_id}...")
        text = fetch_page_blocks(page_id)
        if not text.strip():
            print("⚠️ No content found.")
            continue

        summary = classify_text(text, "risk")
        emotion = classify_text(text, "emotion")

        risk = "UNKNOWN"
        if "HIGH" in summary.upper():
            risk = "HIGH"
        elif "MEDIUM" in summary.upper():
            risk = "MEDIUM"
        elif "LOW" in summary.upper():
            risk = "LOW"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "risk": risk,
            "risk_reason": summary,
            "emotion": emotion,
            "snippet": text[:2000]
        }

        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []
            logs.insert(0, entry)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
            print("✅ Triage complete. Entry saved.")
        except Exception as e:
            print("❌ Log write error:", e)

        if risk == "HIGH":
            send_email(
                "🚨 PsychicGuard: High-Risk Journal Entry Detected",
                f"Summary:\n{summary}\n\nEmotion: {emotion}\n\nSnippet:\n{text[:500]}"
            )

if __name__ == "__main__":
    main()
