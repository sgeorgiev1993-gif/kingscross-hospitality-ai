import json
import os
from datetime import datetime

DASHBOARD = "data/kingscross_dashboard.json"
EVENTS = "data/events.json"
HISTORY_DIR = "data/history"
HISTORY_FILE = f"{HISTORY_DIR}/signals_history.json"

os.makedirs(HISTORY_DIR, exist_ok=True)

try:
    dashboard = json.load(open(DASHBOARD))
except Exception:
    print("No dashboard data")
    exit(0)

events = []
if os.path.exists(EVENTS):
    try:
        events = json.load(open(EVENTS))
    except Exception:
        events = []

temp = dashboard.get("weather", {}).get("temperature_C", 0)

bad_status = ["Part Closure", "Severe Delays", "Reduced Service"]
transport_stress = sum(
    1 for l in dashboard.get("tfl", [])
    if l.get("status") in bad_status
) * 8

event_score = min(len(events) * 6, 30)

busyness = 40
if temp > 15:
    busyness += 10
busyness += transport_stress
busyness += event_score

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "busyness": min(busyness, 100),
    "temperature": temp,
    "transport_stress": transport_stress,
    "events_count": len(events)
}

history = []
if os.path.exists(HISTORY_FILE):
    history = json.load(open(HISTORY_FILE))

history.append(entry)
history = history[-300:]

json.dump(history, open(HISTORY_FILE, "w"), indent=2)
print("History updated with events")