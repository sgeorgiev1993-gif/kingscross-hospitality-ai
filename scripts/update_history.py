import json
import os
from datetime import datetime

# Paths
DASHBOARD_PATH = "data/kingscross_dashboard.json"
HISTORY_DIR = "data/history"
HISTORY_PATH = f"{HISTORY_DIR}/signals_history.json"

os.makedirs(HISTORY_DIR, exist_ok=True)

# Load dashboard
try:
    with open(DASHBOARD_PATH) as f:
        dashboard = json.load(f)
except Exception:
    print("No dashboard data found")
    exit(0)

# Extract signals safely
weather = dashboard.get("weather", {})
tfl = dashboard.get("tfl", [])

# Simple transport stress score
bad_status = ["Severe Delays", "Part Closure", "Planned Closure", "Reduced Service"]
transport_stress = sum(
    1 for line in tfl if line.get("status") in bad_status
) * 5

# Simple busyness heuristic (temporary)
busyness_score = 40
if weather.get("temperature_C", 0) > 18:
    busyness_score += 10
if transport_stress > 20:
    busyness_score += 15

record = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "busyness_score": min(busyness_score, 100),
    "weather": {
        "temperature_C": weather.get("temperature_C")
    },
    "transport": {
        "transport_stress": transport_stress
    }
}

# Load history
if os.path.exists(HISTORY_PATH):
    try:
        history = json.load(open(HISTORY_PATH))
    except Exception:
        history = []
else:
    history = []

history.append(record)
history = history[-200:]  # keep last 200 points

with open(HISTORY_PATH, "w") as f:
    json.dump(history, f, indent=2)

print("History updated:", HISTORY_PATH)