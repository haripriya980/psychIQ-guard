import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = "1e8c303a710c805fa3c2e8c7380f1d5e"  # Replace with your actual DB ID

def log_to_notion(text: str, risk: str):
    """Send a high-risk journal entry to your Notion database."""
    if not NOTION_API_KEY:
        print("❌ Notion API key not found.")
        return

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Title": {
                "title": [{
                    "text": {
                        "content": f"High Risk Entry - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                }]
            },
            "Severity": {
                "select": {
                    "name": risk
                }
            },
            "Content": {
                "rich_text": [{
                    "text": {
                        "content": text[:2000]  # Notion limit
                    }
                }]
            }
        }
    }

    try:
        response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Logged to Notion.")
        else:
            print("❌ Notion logging failed:", response.json())
    except Exception as e:
        print("❌ Notion request error:", e)
