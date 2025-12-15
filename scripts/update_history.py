import json, os
from datetime import datetime

DASHBOARD = "data/kingscross_dashboard.json"
HISTORY_DIR = "data/history"
HISTORY_FILE = f"{HISTORY_DIR}/signals_history.json"

os.makedirs(HISTORY_DIR, exist_ok=True)

try:
    dashboard = json.load(open(DASHBOARD))
except Exception:
    print("No dashboard yet")
    exit(0)

temp = dashboard.get("weather", {}).get("temperature_C", 0)
bad = ["Part Closure", "Severe Delays", "Reduced Service"]

transport_stress = sum(
    1 for l in dashboard.get("tfl", [])
    if l.get("status") in bad
) * 10

busyness = 40 + (10 if temp > 15 else 0) + transport_stress

entry = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "busyness": min(busyness, 100),
    "temperature": temp,
    "transport_stress": transport_stress
}

history = []
if os.path.exists(HISTORY_FILE):
    history = json.load(open(HISTORY_FILE))

history.append(entry)
history = history[-200:]

json.dump(history, open(HISTORY_FILE, "w"), indent=2)
print("History updated")