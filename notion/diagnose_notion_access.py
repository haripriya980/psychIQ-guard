import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def run_search():
    print("🔍 Running Notion integration access check...")
    url = "https://api.notion.com/v1/search"
    payload = {
        "query": "Journal",
        "filter": {"value": "page", "property": "object"},
        "sort": {"direction": "descending", "timestamp": "last_edited_time"}
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        pages = res.json().get("results", [])
        print(f"📄 Found {len(pages)} pages.")
        for p in pages:
            title = p.get("properties", {}).get("title", {}).get("title", [])
            name = title[0]["plain_text"] if title else "Untitled"
            print(f"➡️ {name} | ID: {p['id']}")
    except Exception as e:
        print("❌ Error while querying Notion search:", e)

if __name__ == "__main__":
    run_search()
