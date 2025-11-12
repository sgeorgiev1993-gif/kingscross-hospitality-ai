# scripts/generate_weekly_report.py
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
OUTPUT_JSON = DATA_DIR / "kingscross_dashboard.json"

def load_json(file_name):
    file_path = DATA_DIR / file_name
    if file_path.exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def combine_events():
    events = load_json("events.json")
    combined = []
    for event in events.get("events", []):
        combined.append({
            "name": event.get("name", "Unknown"),
            "start_time": event.get("start_time", ""),
            "venue": event.get("venue", ""),
            "url": event.get("url", "")
        })
    return combined

def combine_restaurants():
    restaurants = load_json("restaurants.json")
    combined = []
    for r in restaurants.get("restaurants", []):
        combined.append({
            "name": r.get("name", "Unknown"),
            "rating": r.get("rating", "N/A"),
            "address": r.get("address", ""),
            "url": r.get("url", "")
        })
    return combined

def generate_dashboard():
    dashboard = {}

    # Events
    dashboard["events"] = combine_events()

    # Restaurants
    dashboard["restaurants"] = combine_restaurants()

    # TfL / rail status
    dashboard["transport"] = load_json("kingscross_tfl.json")

    # Weather
    dashboard["weather"] = load_json("kingscross_weather.json")

    # News (if available)
    dashboard["news"] = load_json("news.json")

    # Add a timestamp
    dashboard["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Save the dashboard JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(dashboard, f, indent=2)

    print(f"Dashboard saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    generate_dashboard()
