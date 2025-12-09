# scripts/generate_weekly_report.py
import json
from pathlib import Path

# Define paths to all data sources
DATA_DIR = Path("data")
DASHBOARD_FILE = DATA_DIR / "kingscross_dashboard.json"

# Load JSON data safely
def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def main():
    dashboard = {}

    # --- TfL / Rail status ---
    tfl_data = load_json(DATA_DIR / "kingscross_tfl.json")
    dashboard["transport"] = []
    for line, info in tfl_data.items():
        dashboard["transport"].append({
            "name": line,
            "mode": info.get("mode", "unknown"),
            "status": info.get("status", "Unknown")
        })

    # --- Eventbrite events ---
    events_data = load_json(DATA_DIR / "events.json")
    dashboard["events"] = []
    if isinstance(events_data, list):
        for event in events_data:
            dashboard["events"].append({
                "name": event.get("name", "Unknown"),
                "start": event.get("start", ""),
                "url": event.get("url", "")
            })

    # --- Google Places / restaurants ---
    places_data = load_json(DATA_DIR / "places.json")
    dashboard["restaurants"] = []
    if isinstance(places_data, list):
        for place in places_data:
            dashboard["restaurants"].append({
                "name": place.get("name", "Unknown"),
                "rating": place.get("rating", "N/A"),
                "address": place.get("vicinity", "")
            })

    # --- Weather ---
    weather_data = load_json(DATA_DIR / "kingscross_weather.json")
    dashboard["weather"] = weather_data if isinstance(weather_data, dict) else {}

    # --- News ---
    news_data = load_json(DATA_DIR / "news.json")
    dashboard["news"] = []
    if isinstance(news_data, list):
        for article in news_data:
            dashboard["news"].append({
                "title": article.get("title", ""),
                "url": article.get("url", "")
            })

    # --- Write dashboard ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(dashboard, f, indent=2)

    print(f"Dashboard successfully saved to {DASHBOARD_FILE}")

if __name__ == "__main__":
    main()