import json
import os
import datetime

DATA_DIR = "data"
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "signals_history.json")
DASHBOARD_FILE = os.path.join(DATA_DIR, "kingscross_dashboard.json")

os.makedirs(HISTORY_DIR, exist_ok=True)

# Load dashboard snapshot
if not os.path.exists(DASHBOARD_FILE):
    print("❌ Dashboard file missing")
    exit(0)

with open(DASHBOARD_FILE) as f:
    dash = json.load(f)

# Extract signals safely
timestamp = dash.get("timestamp") or datetime.datetime.utcnow().isoformat() + "Z"

temperature = dash.get("weather", {}).get("temperature_C")
events_count = len(dash.get("events", []))

bad_statuses = [
    "Part Closure",
    "Severe Delays",
    "Reduced Service",
    "Planned Closure"
]

transport_stress = sum(
    1 for l in dash.get("tfl", [])
    if l.get("status") in bad_statuses
) * 8

# Simple explainable busyness formula
busyness = 40
if temperature is not None and temperature > 15:
    busyness += 10

busyness += transport_stress
busyness += events_count * 6
busyness = min(busyness, 100)

entry = {
    "timestamp": timestamp,
    "busyness": busyness,
    "temperature": temperature,
    "transport_stress": transport_stress,
    "events_count": events_count
}

# Load existing history
history = []
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE) as f:
        history = json.load(f)

history.append(entry)

# Keep last 7 days (168 hours)
history = history[-168:]

with open(HISTORY_FILE, "w") as f:
    json.dump(history, f, indent=2)

print("✅ History updated:", entry)