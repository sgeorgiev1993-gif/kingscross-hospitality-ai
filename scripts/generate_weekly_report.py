# scripts/generate_weekly_report.py
import json
from pathlib import Path

DATA_FOLDER = Path("data")
DASHBOARD_FILE = DATA_FOLDER / "kingscross_dashboard.json"

dashboard = {}

# Load TfL data
try:
    with open(DATA_FOLDER / "kingscross_tfl.json") as f:
        dashboard["tfl"] = json.load(f)
except Exception:
    dashboard["tfl"] = {}

# Load events
try:
    with open(DATA_FOLDER / "events.json") as f:
        dashboard["events"] = json.load(f)
except Exception:
    dashboard["events"] = []

# Load restaurants
try:
    with open(DATA_FOLDER / "restaurants.json") as f:
        dashboard["restaurants"] = json.load(f)
except Exception:
    dashboard["restaurants"] = []

# Load weather
try:
    with open(DATA_FOLDER / "kingscross_weather.json") as f:
        dashboard["weather"] = json.load(f)
except Exception:
    dashboard["weather"] = {}

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
with open(DASHBOARD_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"✅ Dashboard saved to {DASHBOARD_FILE}")
