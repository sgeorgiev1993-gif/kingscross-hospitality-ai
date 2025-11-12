# scripts/generate_weekly_report.py
import json
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path("data")

# ------------------------
# Load Data
# ------------------------
def load_json(file):
    path = DATA_DIR / file
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}

tfl_data = load_json("kingscross_tfl.json")
events_data = load_json("events.json")
news_data = load_json("news.json")
weather_data = load_json("kingscross_weather.json")

# ------------------------
# Summarize Transport
# ------------------------
transport_summary = []
for line, info in tfl_data.items():
    status = info.get("status", "Unknown")
    mode = info.get("mode", "")
    transport_summary.append({"line": line, "mode": mode, "status": status})

transport_df = pd.DataFrame(transport_summary)

# ------------------------
# Summarize Events
# ------------------------
events_summary = []
for event in events_data:
    events_summary.append({
        "name": event.get("name", "Unknown"),
        "start": event.get("start", ""),
        "venue": event.get("venue", ""),
        "url": event.get("url", "")
    })
events_df = pd.DataFrame(events_summary)

# ------------------------
# Summarize News
# ------------------------
news_summary = []
for article in news_data:
    news_summary.append({
        "title": article.get("title", ""),
        "source": article.get("source", ""),
        "url": article.get("url", "")
    })
news_df = pd.DataFrame(news_summary)

# ------------------------
# Weather Summary
# ------------------------
weather_summary = {}
if weather_data:
    weather_summary = {
        "temp": weather_data.get("main", {}).get("temp", "N/A"),
        "condition": weather_data.get("weather", [{}])[0].get("description", "N/A")
    }

# ------------------------
# Save Combined JSON
# ------------------------
dashboard_json = {
    "transport": transport_summary,
    "events": events_summary,
    "news": news_summary,
    "weather": weather_summary
}
with open(DATA_DIR / "kingscross_dashboard.json", "w") as f:
    json.dump(dashboard_json, f, indent=2)

# ------------------------
# Generate Dashboard Plot
# ------------------------
plt.figure(figsize=(12, 8))
plt.axis('off')
plt.title("King's Cross Dashboard", fontsize=18, weight="bold")

y = 0.95
def add_text_block(title, lines, fontsize=10):
    global y
    plt.text(0.02, y, title, fontsize=fontsize+2, weight="bold")
    y -= 0.04
    for line in lines:
        plt.text(0.04, y, line, fontsize=fontsize)
        y -= 0.03
    y -= 0.02

# Transport
transport_lines = [f"{row['mode'].capitalize()}: {row['line']} — {row['status']}" for _, row in transport_df.iterrows()]
add_text_block("🚇 Transport Status", transport_lines[:20])

# Events
event_lines = [f"{row['start']} — {row['name']} @ {row['venue']}" for _, row in events_df.iterrows()]
add_text_block("🎟 Upcoming Events", event_lines[:10])

# News
news_lines = [f"{row['title']} ({row['source']})" for _, row in news_df.iterrows()]
add_text_block("📰 Latest News", news_lines[:10])

# Weather
weather_lines = [f"Temperature: {weather_summary.get('temp', 'N/A')}°C",
                 f"Condition: {weather_summary.get('condition', 'N/A')}"]
add_text_block("🌤 Weather", weather_lines)

plt.tight_layout()
plt.savefig(DATA_DIR / "kingscross_dashboard.png", dpi=150)
print(f"✅ Dashboard generated at {DATA_DIR/'kingscross_dashboard.png'}")
