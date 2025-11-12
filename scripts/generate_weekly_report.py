# scripts/generate_weekly_report.py
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
DASHBOARD_FILE = Path("index.html")

def load_json_safe(filepath):
    """Load JSON and return empty dict on failure."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                return {i: item for i, item in enumerate(data)}
            else:
                return {}
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

# Load all data sources
event_data = load_json_safe(DATA_DIR / "events.json")
places_data = load_json_safe(DATA_DIR / "places_reviews.json")
tfl_data = load_json_safe(DATA_DIR / "kingscross_tfl.json")
weather_data = load_json_safe(DATA_DIR / "kingscross_weather.json")

# Prepare summaries
def summarize_events(events):
    summary = []
    for e in events.values():
        name = e.get("name", "Unnamed Event")
        date = e.get("start_date", "Unknown Date")
        summary.append(f"{date}: {name}")
    return summary

def summarize_places(places):
    summary = []
    for p in places.values():
        name = p.get("name", "Unnamed Place")
        rating = p.get("rating", "N/A")
        summary.append(f"{name} (Rating: {rating})")
    return summary

def summarize_tfl(tfl):
    summary = []
    for line, info in tfl.items():
        status = info.get("status", "Unknown") if isinstance(info, dict) else "Unknown"
        mode = info.get("mode", "N/A") if isinstance(info, dict) else "N/A"
        summary.append(f"{line} ({mode}): {status}")
    return summary

def summarize_weather(weather):
    temp = weather.get("temperature", "N/A") if isinstance(weather, dict) else "N/A"
    condition = weather.get("condition", "N/A") if isinstance(weather, dict) else "N/A"
    return f"Temp: {temp}, Condition: {condition}"

# Generate dashboard HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>KingsCross Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h2 {{ color: #2E86C1; }}
        ul {{ line-height: 1.5; }}
    </style>
</head>
<body>
    <h1>KingsCross Dashboard</h1>
    
    <h2>Upcoming Events</h2>
    <ul>
        {"".join(f"<li>{e}</li>" for e in summarize_events(event_data))}
    </ul>

    <h2>Restaurants & Places</h2>
    <ul>
        {"".join(f"<li>{p}</li>" for p in summarize_places(places_data))}
    </ul>

    <h2>TfL & Rail Status</h2>
    <ul>
        {"".join(f"<li>{t}</li>" for t in summarize_tfl(tfl_data))}
    </ul>

    <h2>Current Weather</h2>
    <p>{summarize_weather(weather_data)}</p>
</body>
</html>
"""

# Save dashboard
DASHBOARD_FILE.write_text(html_content, encoding="utf-8")
print(f"Dashboard saved to {DASHBOARD_FILE}")
