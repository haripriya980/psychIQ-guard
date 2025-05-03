import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# === Load .env and configs ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_JOURNAL_PAGE_ID = os.getenv("NOTION_JOURNAL_PAGE_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "page_triage_log.json")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# === Recursively fetch all text blocks from a Notion page ===
def fetch_page_blocks(page_id):
    all_texts = []

    def fetch_blocks(block_id):
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            blocks = res.json().get("results", [])
            # 👇 Debug print to inspect actual block types
            print("📦 Block types found:", [b.get("type") for b in blocks])

            for block in blocks:
                block_type = block.get("type")
                data = block.get(block_type, {})

                # Extract visible text from common blocks
                if "rich_text" in data:
                    for item in data["rich_text"]:
                        plain = item.get("plain_text", "")
                        if plain.strip():
                            all_texts.append(plain.strip())

                # If nested content (like toggles), recurse
                if block.get("has_children"):
                    fetch_blocks(block["id"])
        except Exception as e:
            print(f"❌ Error reading block {block_id}: {e}")

    fetch_blocks(page_id)
    return "\n".join(all_texts)

# === Classify severity or emotion ===
def classify_text(text, mode):
    system_prompt = (
        "You are a clinical mental health triage assistant. Classify the journal entry severity as LOW, MEDIUM, or HIGH."
        if mode == "risk" else
        "You are a mental health assistant. Identify the dominant emotion in one word: SADNESS, ANGER, ANXIETY, ISOLATION, OVERWHELMED, NUMB, HOPEFUL, EMPTY."
    )
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
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
    except Exception as e:
        print("❌ LLM error:", e)
        return "UNKNOWN"

# === Summarize the journal ===
def summarize_text(text):
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Summarize this mental health journal entry in 1-2 sentences."},
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
        print("❌ Summary error:", e)
        return ""

# === Main Execution ===
def main():
    print("\n🧠 Scanning Notion journal page recursively...")
    if not NOTION_JOURNAL_PAGE_ID:
        print("❌ No NOTION_JOURNAL_PAGE_ID found in .env")
        return

    journal_text = fetch_page_blocks(NOTION_JOURNAL_PAGE_ID)
    if not journal_text.strip():
        print("⚠️ No content found.")
        return

    print("📝 Journal Text Sample:", journal_text[:100])
    risk = classify_text(journal_text, "risk")
    emotion = classify_text(journal_text, "emotion")
    summary = summarize_text(journal_text)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "risk": risk,
        "emotion": emotion,
        "summary": summary,
        "snippet": journal_text[:2000]
    }

    print(f"✅ Risk: {risk}\n✅ Emotion: {emotion}\n📝 Summary: {summary}")

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
        logs.insert(0, entry)
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        print("📦 Entry logged to page_triage_log.json")
    except Exception as e:
        print("❌ Log write error:", e)

if __name__ == "__main__":
    main()
