import json
from pathlib import Path

DATA_DIR = Path("data")
DASHBOARD_FILE = DATA_DIR / "kingscross_dashboard.json"

# Load all sources safely
def load_json(filename):
    try:
        with open(DATA_DIR / filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

dashboard = {
    "tfl": load_json("kingscross_tfl.json"),
    "weather": load_json("kingscross_weather.json"),
    "events": load_json("events.json"),
    "places": load_json("places_reviews.json"),
    "news": load_json("news.json"),
}

# Save combined dashboard
DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(DASHBOARD_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"Dashboard saved to {DASHBOARD_FILE}")
