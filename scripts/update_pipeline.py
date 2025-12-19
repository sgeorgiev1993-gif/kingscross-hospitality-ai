import os, json, datetime, requests, statistics

LAT, LON = 51.5308, -0.1238

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")

os.makedirs("data/history", exist_ok=True)

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
            timeout=10
        ).json()

        dashboard["weather"] = {
            "temperature_C": w["main"]["temp"],
            "windspeed_kmh": w["wind"]["speed"],
            "condition": w["weather"][0]["main"]
        }
    except Exception:
        pass

# TFL
if TFL_APP_KEY:
    try:
        r = requests.get(
            "https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr/Status",
            params={"app_key": TFL_APP_KEY},
            timeout=10
        ).json()

        for line in r:
            dashboard["tfl"].append({
                "name": line.get("name"),
                "mode": line.get("modeName"),
                "status": (line.get("lineStatuses") or [{}])[0].get("statusSeverityDescription", "Unknown")
            })
    except Exception:
        pass

# EVENTS
if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={"location.address": "Kings Cross London", "location.within": "1km"},
            timeout=10
        ).json()

        for e in (r.get("events") or [])[:5]:
            dashboard["events"].append({
                "name": e["name"]["text"],
                "start": e["start"]["utc"],
                "url": e["url"]
            })
    except Exception:
        pass

# Write dashboard
with open("data/kingscross_dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2)

# HISTORY
hist_file = "data/history/kingscross_history.json"
history = []
if os.path.exists(hist_file):
    try:
        history = json.load(open(hist_file))
    except Exception:
        history = []

temp = dashboard.get("weather", {}).get("temperature_C", 10)
stress = sum(1 for l in dashboard.get("tfl", []) if l.get("status") != "Good Service") * 8
events_pressure = len(dashboard.get("events", [])) * 6

busyness = min(40 + (10 if temp > 15 else 0) + stress + events_pressure, 100)

history.append({"timestamp": dashboard["timestamp"], "busyness": busyness})
history = history[-300:]

with open(hist_file, "w") as f:
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

with open("data/forecast.json", "w") as f:
    json.dump(forecast, f, indent=2)

print("✅ Pipeline complete: dashboard + history + forecast")
