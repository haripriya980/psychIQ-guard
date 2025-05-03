import os
import time
import requests
import json
from dotenv import load_dotenv

# === Load .env ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_JOURNAL_DB_ID = os.getenv("NOTION_JOURNAL_DB_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

if not NOTION_JOURNAL_DB_ID:
    print("❌ NOTION_JOURNAL_DB_ID is missing.")
    exit(1)

def fetch_notion_entries():
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_DB_ID}/query"
    try:
        res = requests.post(url, headers=headers)
        data = res.json()
        print(f"📥 Fetched {len(data.get('results', []))} entries from Notion.")
        return data.get("results", [])
    except Exception as e:
        print("❌ Failed to fetch entries:", e)
        return []

def generate_summary(text: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = "Summarize the following mental health journal entry in 1-2 sentences."

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
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print("❌ Summary generation error:", e)
        return ""

def main():
    print("🔁 Starting summary generation...")
    entries = fetch_notion_entries()

    for entry in entries:
        props = entry.get("properties", {})
        title_obj = props.get("Title", {}).get("title", [])
        content_obj = props.get("Content", {}).get("rich_text", [])
        summary_obj = props.get("Summary", {}).get("rich_text", [])

        title = title_obj[0].get("plain_text") if title_obj else "Untitled"
        content = content_obj[0].get("plain_text") if content_obj else ""
        summary = summary_obj[0].get("plain_text") if summary_obj else ""

        if not content:
            print(f"⏭️ Skipping '{title}' — no content.")
            continue
        if summary:
            print(f"✅ Skipping '{title}' — already has a summary.")
            continue

        generated = generate_summary(content)
        if not generated:
            print(f"❌ No summary generated for '{title}'")
            continue

        update_url = f"https://api.notion.com/v1/pages/{entry['id']}"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        patch_payload = {
            "properties": {
                "Summary": {
                    "rich_text": [{
                        "text": {
                            "content": generated[:2000]
                        }
                    }]
                }
            }
        }

        try:
            res = requests.patch(update_url, headers=headers, json=patch_payload)
            if res.status_code == 200:
                print(f"✅ Summary added for '{title}'")
            else:
                print(f"❌ Failed to update Notion for '{title}':", res.text)
        except Exception as e:
            print(f"❌ Exception updating Notion for '{title}':", e)

if __name__ == "__main__":
    main()
