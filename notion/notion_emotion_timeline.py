import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil import parser

# === Load ENV ===
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_JOURNAL_DB_ID = os.getenv("NOTION_JOURNAL_DB_ID")

# === Headers for Notion API ===
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# === Fetch entries ===
def fetch_entries():
    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_DB_ID}/query"
    try:
        res = requests.post(url, headers=headers)
        res.raise_for_status()
        return res.json().get("results", [])
    except Exception as e:
        print("❌ Error fetching Notion entries:", e)
        return []

# === Extract emotion and timestamp ===
def extract_timeline_data(entries):
    data = []
    for entry in entries:
        props = entry.get("properties", {})
        emotion_field = props.get("Emotion", {}).get("rich_text", [])
        created_time = entry.get("created_time")

        if emotion_field and created_time:
            emotion = emotion_field[0].get("plain_text", "")
            timestamp = parser.parse(created_time)
            data.append((timestamp, emotion.upper()))
    return data

# === Plot timeline ===
def plot_emotion_timeline(data):
    if not data:
        print("⚠️ No emotion data found.")
        return

    timestamps, emotions = zip(*sorted(data))
    y_ticks = list(range(len(emotions)))

    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, y_ticks, marker='o', linestyle='-', color='skyblue')

    for i, emotion in enumerate(emotions):
        plt.text(timestamps[i], y_ticks[i], emotion, fontsize=9, verticalalignment='bottom')

    plt.title("🧠 Emotion Timeline")
    plt.xlabel("Date")
    plt.ylabel("Journal Entry Index")
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "emotion_timeline.png")
    plt.savefig(output_path)
    print(f"📈 Emotion timeline saved to {output_path}")

# === Main ===
def main():
    print("📊 Generating Emotion Timeline...")
    entries = fetch_entries()
    timeline_data = extract_timeline_data(entries)
    plot_emotion_timeline(timeline_data)

if __name__ == "__main__":
    main()
