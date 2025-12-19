import os, json, datetime, requests, statistics
from pathlib import Path

LAT, LON = 51.5308, -0.1238

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")

DATA_DIR = Path("data")
HIST_DIR = DATA_DIR / "history"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HIST_DIR.mkdir(parents=True, exist_ok=True)

dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "weather": {},
    "tfl": [],
    "events": []
}

# WEATHER
if OPENWEATHER_KEY:
    try:
        w = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": LAT, "lon": LON, "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=15
        ).json()
        if "main" in w and "wind" in w and "weather" in w and w["weather"]:
            dashboard["weather"] = {
                "temperature_C": w["main"]["temp"],
                "windspeed_kmh": w["wind"]["speed"],
                "condition": w["weather"][0].get("main", "")
            }
    except Exception as e:
        print("Weather error:", e)

# TFL
if TFL_APP_KEY:
    try:
        r = requests.get(
            "https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr/Status",
            params={"app_key": TFL_APP_KEY},
            timeout=15
        ).json()
        if isinstance(r, list):
            for line in r:
                statuses = line.get("lineStatuses") or []
                status = statuses[0].get("statusSeverityDescription", "Unknown") if statuses else "Unknown"
                dashboard["tfl"].append({
                    "name": line.get("name", "Unknown"),
                    "mode": line.get("modeName", "Unknown"),
                    "status": status
                })
    except Exception as e:
        print("TfL error:", e)

# EVENTS (Eventbrite)
if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={
                "location.address": "Kings Cross London",
                "location.within": "1km",
                "sort_by": "date",
            },
            timeout=20
        ).json()
        for e in (r.get("events") or [])[:8]:
            name = (e.get("name") or {}).get("text")
            start = (e.get("start") or {}).get("utc")
            url = e.get("url")
            if name and start and url:
                dashboard["events"].append({"name": name, "start": start, "url": url})
    except Exception as e:
        print("Eventbrite error:", e)

# Save dashboard
with open(DATA_DIR / "kingscross_dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2)

# HISTORY
hist_file = HIST_DIR / "kingscross_history.json"
history = []
if hist_file.exists():
    try:
        history = json.load(open(hist_file, "r", encoding="utf-8"))
        if not isinstance(history, list):
            history = []
    except Exception:
        history = []

temp = dashboard.get("weather", {}).get("temperature_C", 10)
stress = sum(1 for l in dashboard["tfl"] if l.get("status") != "Good Service") * 8
events_score = len(dashboard["events"]) * 6
busyness = min(40 + (10 if temp > 15 else 0) + stress + events_score, 100)

history.append({"timestamp": dashboard["timestamp"], "busyness": busyness})
history = history[-300:]

with open(hist_file, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2)

# FORECAST
values = [h.get("busyness", 50) for h in history] or [50]
avg = sum(values) / len(values)
std = statistics.pstdev(values) if len(values) > 1 else 8

forecast = []
now = datetime.datetime.utcnow()
for i in range(1, 13):
    t = now + datetime.timedelta(hours=i)
    rush = t.hour in (7, 8, 9, 16, 17, 18)
    base = avg + (12 if rush else 0)
    forecast.append({
        "time": t.isoformat() + "Z",
        "busyness": int(min(base, 100)),
        "low": int(max(base - std, 0)),
        "high": int(min(base + std, 100)),
        "rush_hour": rush
    })

with open(DATA_DIR / "forecast.json", "w", encoding="utf-8") as f:
    json.dump(forecast, f, indent=2)

print("✅ Updated: data/kingscross_dashboard.json, data/history/kingscross_history.json, data/forecast.json")
