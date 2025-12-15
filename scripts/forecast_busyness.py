import json
import os
from datetime import datetime, timedelta

HISTORY_FILE = "data/history/signals_history.json"
OUT_FILE = "data/forecast.json"

if not os.path.exists(HISTORY_FILE):
    print("No history yet")
    exit(0)

history = json.load(open(HISTORY_FILE))
recent = history[-6:]

avg_busyness = sum(h["busyness"] for h in recent) / len(recent)
avg_temp = sum(h["temperature"] for h in recent) / len(recent)
avg_events = sum(h["events_count"] for h in recent) / len(recent)

forecast = []
now = datetime.utcnow()

for i in range(1, 13):  # next 12 hours
    hour = now + timedelta(hours=i)
    predicted = avg_busyness

    if avg_events > 2:
        predicted += 8
    if avg_temp > 18:
        predicted += 5

    forecast.append({
        "time": hour.isoformat() + "Z",
        "busyness": min(int(predicted), 100)
    })

json.dump(forecast, open(OUT_FILE, "w"), indent=2)
print("Forecast generated")