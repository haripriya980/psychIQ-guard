import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# === Load .env variables ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_JOURNAL_PAGE_ID = os.getenv("NOTION_JOURNAL_PAGE_ID")
NOTION_JOURNAL_DB_ID = os.getenv("NOTION_JOURNAL_DB_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# === Recursively fetch all paragraphs from journal page ===
def fetch_paragraph_blocks(block_id):
    paragraphs = []

    def recurse_blocks(block_id):
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        try:
            res = requests.get(url, headers=HEADERS)
            res.raise_for_status()
            blocks = res.json().get("results", [])
            for block in blocks:
                block_type = block.get("type")
                if block_type in {"paragraph", "quote"}:
                    texts = block.get(block_type, {}).get("rich_text", [])
                    text = "".join(t.get("plain_text", "") for t in texts if t.get("plain_text"))
                    if text.strip():
                        paragraphs.append(text.strip())
                if block.get("has_children"):
                    recurse_blocks(block["id"])
        except Exception as e:
            print(f"❌ Error reading block {block_id}:", e)

    recurse_blocks(block_id)
    return paragraphs

# === Call LLM ===
def classify_text(text, mode="risk"):
    system_prompt = (
        "Classify the journal entry severity as LOW, MEDIUM, or HIGH."
        if mode == "risk" else
        "Identify the dominant emotion: SADNESS, ANGER, ANXIETY, ISOLATION, OVERWHELMED, NUMB, HOPEFUL, EMPTY."
    )
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                     "Content-Type": "application/json"},
                            json=payload)
        return res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
    except Exception as e:
        print("❌ LLM error:", e)
        return "UNKNOWN"

def summarize_text(text):
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Summarize this journal paragraph in 1-2 lines."},
            {"role": "user", "content": text}
        ]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                     "Content-Type": "application/json"},
                            json=payload)
        return res.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print("❌ Summary error:", e)
        return ""

# === Push to Notion DB ===
def push_to_notion_db(text, risk, emotion, summary):
    payload = {
        "parent": {"database_id": NOTION_JOURNAL_DB_ID},
        "properties": {
            "Title": {
                "title": [{"text": {"content": f"Entry - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]
            },
            "Content": {
                "rich_text": [{"text": {"content": text[:2000]}}]
            },
            "Severity": {
                "select": {"name": risk}
            },
            "Emotion": {
                "rich_text": [{"text": {"content": emotion}}]
            },
            "Summary": {
                "rich_text": [{"text": {"content": summary}}]
            }
        }
    }
    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        if res.status_code in [200, 201]:
            print("✅ Added entry to Notion DB.")
        else:
            print("❌ Failed to add entry:", res.json())
    except Exception as e:
        print("❌ Notion push error:", e)

# === Main ===
def main():
    print("🧠 Scanning journal page for paragraphs...")
    if not NOTION_JOURNAL_PAGE_ID or not NOTION_JOURNAL_DB_ID:
        print("❌ Missing NOTION_JOURNAL_PAGE_ID or NOTION_JOURNAL_DB_ID in .env")
        return

    paragraphs = fetch_paragraph_blocks(NOTION_JOURNAL_PAGE_ID)
    if not paragraphs:
        print("⚠️ No content found.")
        return

    for para in paragraphs:
        risk = classify_text(para, mode="risk")
        emotion = classify_text(para, mode="emotion")
        summary = summarize_text(para)
        print(f"\n📌 Entry:\nText: {para}\nRisk: {risk}\nEmotion: {emotion}\nSummary: {summary}")
        push_to_notion_db(para, risk, emotion, summary)

if __name__ == "__main__":
    main()
