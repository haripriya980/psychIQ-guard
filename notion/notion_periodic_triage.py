import os
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# === Load ENV ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# === Prompt user if missing ===
NOTION_JOURNAL_DB_ID = os.getenv("NOTION_JOURNAL_DB_ID")
if not NOTION_JOURNAL_DB_ID:
    print("📝 No Notion Journal DB ID found in .env.")
    user_input = input("🔧 Please paste your Notion Journal DB ID: ").strip()
    if user_input:
        with open(os.path.join(os.path.dirname(__file__), "..", ".env"), "a") as f:
            f.write(f"\nNOTION_JOURNAL_DB_ID={user_input}")
        print("✅ Saved to .env. Restart the script.")
        exit(0)
    else:
        print("❌ No ID entered. Exiting.")
        exit(1)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

# === Fetch journal entries from Notion ===
def fetch_notion_entries():
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_DB_ID}/query"
    try:
        res = requests.post(url, headers=headers)
        return res.json().get("results", [])
    except Exception as e:
        print("❌ Failed to fetch entries:", e)
        return []

# === Send to LLM for risk ===
def classify_entry(text: str, prompt_type: str = "risk"):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    if prompt_type == "risk":
        system_prompt = (
            "You are a clinical mental health triage assistant."
            " Classify journal entry severity as LOW, MEDIUM, or HIGH."
        )
    else:
        system_prompt = (
            "You are a mental health assistant. Identify one dominant emotion:"
            " SADNESS, ANGER, ANXIETY, ISOLATION, OVERWHELMED, NUMB, HOPEFUL, EMPTY."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text.strip()}
        ]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = res.json()
        print("📨 Raw response:", data)
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
    except Exception as e:
        print("❌ Classification error:", e)
        return "UNKNOWN"

# === Main Loop ===
def main():
    print("🔁 Starting Notion Auto-Triage Monitor...")
    while True:
        entries = fetch_notion_entries()
        for entry in entries:
            props = entry.get("properties", {})
            title_obj = props.get("Title", {}).get("title", [])
            content_obj = props.get("Content", {}).get("rich_text", [])

            title = title_obj[0].get("plain_text") if title_obj else "Untitled"
            content = content_obj[0].get("plain_text") if content_obj else ""

            if not content:
                continue

            # Only classify if missing
            if "Severity" not in props or not props["Severity"].get("select"):
                risk = classify_entry(content, prompt_type="risk")
                emotion = classify_entry(content, prompt_type="emotion")

                patch_payload = {
                    "properties": {
                        "Severity": {"select": {"name": risk}},
                        "Emotion": {"rich_text": [{"text": {"content": emotion}}]}
                    }
                }

                update_url = f"https://api.notion.com/v1/pages/{entry['id']}"
                headers = {
                    "Authorization": f"Bearer {NOTION_API_KEY}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                }

                try:
                    requests.patch(update_url, headers=headers, json=patch_payload)
                    print(f"✅ Updated: {title} => {risk}, {emotion}")
                except Exception as e:
                    print("❌ Notion update error:", e)

        print("⏳ Sleeping 30 minutes...")
        time.sleep(1800)  # 30 minutes

if __name__ == "__main__":
    main()
