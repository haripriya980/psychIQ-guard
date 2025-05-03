import json
import os
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil import parser

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "page_triage_log.json")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "visuals")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_logs():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def plot_risk_timeline(entries):
    dates = []
    risks = []
    for entry in entries:
        ts = parser.parse(entry["timestamp"])
        risk_level = entry.get("risk", "").upper()
        score = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(risk_level, 0)
        if score:
            dates.append(ts)
            risks.append(score)

    if not dates:
        print("⚠️ No valid risk entries to plot.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(dates, risks, marker='o', linestyle='-', color='crimson')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    plt.yticks([1, 2, 3], ["LOW", "MEDIUM", "HIGH"])
    plt.title("Emotional Risk Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Severity Level")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "risk_timeline.png"))
    plt.close()
    print("✅ Saved risk_timeline.png")

def simplify_emotion(e):
    e = e.upper()
    if any(word in e for word in ["SAD", "SADNESS", "DEPRESS"]): return "SADNESS"
    if any(word in e for word in ["ANGER", "ANGRY", "FRUSTRAT"]): return "ANGER"
    if any(word in e for word in ["ANXIETY", "ANXIOUS", "WORRY"]): return "ANXIETY"
    if any(word in e for word in ["ISOLATE", "LONELY", "ALONE"]): return "ISOLATION"
    if any(word in e for word in ["OVERWHELMED", "TOO MUCH", "BURDEN"]): return "OVERWHELMED"
    if any(word in e for word in ["NUMB", "DISCONNECT", "EMPTY INSIDE"]): return "NUMB"
    if any(word in e for word in ["HOPE", "HOPEFUL"]): return "HOPEFUL"
    if any(word in e for word in ["EMPTY"]): return "EMPTY"
    if any(word in e for word in ["SUICIDAL", "END LIFE", "DIE"]): return "SUICIDAL"
    return "UNKNOWN"


def plot_emotion_frequency(entries):
    simplified = [simplify_emotion(entry.get("emotion", "")) for entry in entries]
    emotion_counts = Counter(simplified)

    if not emotion_counts:
        print("⚠️ No emotion data found.")
        return

    emotions = list(emotion_counts.keys())
    values = [emotion_counts[e] for e in emotions]

    plt.figure(figsize=(10, 5))
    plt.bar(emotions, values, color="skyblue")
    plt.title("Detected Emotion Frequency")
    plt.xlabel("Emotion")
    plt.ylabel("Count")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "emotion_frequency.png"))
    plt.close()
    print("✅ Saved emotion_frequency.png")

if __name__ == "__main__":
    data = load_logs()
    plot_risk_timeline(data)
    plot_emotion_frequency(data)
