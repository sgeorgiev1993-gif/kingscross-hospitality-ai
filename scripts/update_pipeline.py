import os
import json
import datetime
import requests
import statistics

# ---------------- CONFIG ----------------
LAT, LON = 51.5308, -0.1238   # Kings Cross
HISTORY_LIMIT = 300

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY")

DATA_DIR = "data"
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "kingscross_history.json")
DASH_FILE = os.path.join(DATA_DIR, "kingscross_dashboard.json")
FORECAST_FILE = os.path.join(DATA_DIR, "forecast.json")

os.makedirs(HISTORY_DIR, exist_ok=True)

now = datetime.datetime.utcnow()
timestamp = now.isoformat() + "Z"

# ---------------- DASHBOARD BASE ----------------
dashboard = {
    "timestamp": timestamp,
    "weather": None,
    "tfl": [],
    "events": []
}

# ---------------- WEATHER ----------------
temperature = None
windspeed = None
condition = None

if OPENWEATHER_KEY:
    try:
        w = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": LAT,
                "lon": LON,
                "appid": OPENWEATHER_KEY,
                "units": "metric"
            },
            timeout=10
        ).json()

        temperature = w["main"]["temp"]
        windspeed = w["wind"]["speed"]
        condition = w["weather"][0]["main"]

        dashboard["weather"] = {
            "temperature_C": temperature,
            "windspeed_kmh": windspeed,
            "condition": condition
        }

    except Exception as e:
        print("Weather fetch failed:", e)

# ---------------- TFL ----------------
transport_stress = 0

if TFL_APP_KEY:
    try:
        tfl = requests.get(
            "https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr/Status",
            params={"app_key": TFL_APP_KEY},
            timeout=10
        ).json()

        for line in tfl:
            status = line["lineStatuses"][0]["statusSeverityDescription"]

            dashboard["tfl"].append({
                "name": line["name"],
                "mode": line["modeName"],
                "status": status
            })

            if status != "Good Service":
                transport_stress += 8

    except Exception as e:
        print("TfL fetch failed:", e)

# ---------------- EVENTS ----------------
events_count = 0

if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={
                "location.address": "Kings Cross London",
                "location.within": "1km"
            },
            timeout=10
        ).json()

        for e in r.get("events", [])[:8]:
            dashboard["events"].append({
                "name": e["name"]["text"],
                "start": e["start"]["utc"],
                "url": e["url"]
            })

        events_count = len(dashboard["events"])

    except Exception as e:
        print("Eventbrite fetch failed:", e)

# ---------------- SAVE DASHBOARD ----------------
with open(DASH_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

# ---------------- HISTORY ----------------
history = []
if os.path.exists(HISTORY_FILE):
    try:
        history = json.load(open(HISTORY_FILE))
    except:
        history = []

# ---------------- BUSYNESS MODEL ----------------
busyness = 40

# Weather effect
if temperature is not None:
    if temperature >= 18:
        busyness += 12
    elif temperature >= 12:
        busyness += 6
    elif temperature < 5:
        busyness -= 6

# Transport + events
busyness += transport_stress
busyness += events_count * 6

busyness = max(0, min(100, busyness))

history.append({
    "timestamp": timestamp,
    "busyness": busyness,
    "temperature": temperature,
    "transport_stress": transport_stress,
    "events_count": events_count
})

history = history[-HISTORY_LIMIT:]

with open(HISTORY_FILE, "w") as f:
    json.dump(history, f, indent=2)

# ---------------- FORECAST ----------------
values = [h["busyness"] for h in history if h.get("busyness") is not None]

avg = statistics.mean(values) if values else 55
std = statistics.pstdev(values) if len(values) > 1 else 8

forecast = []

for i in range(1, 13):
    t = now + datetime.timedelta(hours=i)
    rush = t.hour in (7, 8, 9, 16, 17, 18)

    base = avg + (12 if rush else 0)
    base = max(0, min(100, base))

    forecast.append({
        "time": t.isoformat() + "Z",
        "busyness": int(base),
        "low": int(max(base - std, 0)),
        "high": int(min(base + std, 100)),
        "rush_hour": rush,
        "confidence": "low" if len(values) < 6 else "medium"
    })

with open(FORECAST_FILE, "w") as f:
    json.dump(forecast, f, indent=2)

# ---------------- CLUSTER PRESSURE ----------------
clusters = {
    "transit": 40,
    "leisure": 35,
    "dining": 30
}

# Transit pressure drivers
rush_hour = now.hour in (7,8,9,16,17,18)
if rush_hour:
    clusters["transit"] += 20

clusters["transit"] += transport_stress

if temperature is not None and temperature > 10:
    clusters["transit"] += 6
    clusters["leisure"] += 6

# Events push leisure & dining
clusters["leisure"] += events_count * 6
clusters["dining"] += events_count * 4

# Clamp
for k in clusters:
    clusters[k] = max(0, min(100, clusters[k]))

dashboard["clusters"] = clusters

# Transit pressure summary
dashboard["transit_pressure"] = {
    "score": clusters["transit"],
    "level": (
        "High" if clusters["transit"] >= 70
        else "Medium" if clusters["transit"] >= 45
        else "Low"
    ),
    "drivers": [
        "Rush hour" if rush_hour else None,
        f"{transport_stress//8} disrupted lines" if transport_stress else None,
        "Events nearby" if events_count else None
    ]
}

dashboard["transit_pressure"]["drivers"] = [
    d for d in dashboard["transit_pressure"]["drivers"] if d
]

# Save updated dashboard
with open(DASH_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)
# ---------------- GOOGLE PLACES (VENUES) ----------------
VENUES_FILE = os.path.join(DATA_DIR, "venues.json")
venues = []

if GOOGLE_PLACES_KEY:
    try:
        # Morty & Bob's exact search
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": "Morty & Bob's Kings Cross",
                "inputtype": "textquery",
                "fields": "place_id,name,geometry,types,rating,user_ratings_total",
                "key": GOOGLE_PLACES_KEY
            },
            timeout=10
        ).json()

        if r.get("candidates"):
            place = r["candidates"][0]

            venues.append({
                "id": place.get("place_id"),
                "name": place.get("name"),
                "type": "restaurant",
                "lat": place["geometry"]["location"]["lat"],
                "lng": place["geometry"]["location"]["lng"],
                "rating": place.get("rating"),
                "reviews": place.get("user_ratings_total"),
                "source": "google_places",
                "distance_km": 0.4,   # fixed for now (we can calculate later)
                "transit_reliance": 0.75
            })

    except Exception as e:
        print("Google Places fetch failed:", e)

# Save venues
with open(VENUES_FILE, "w") as f:
    json.dump(venues, f, indent=2)

print(f"📍 Venues saved: {len(venues)}")

print("✅ Pipeline complete")
print(f"   Weather: {temperature}°C, {condition}")
print(f"   Transport stress: {transport_stress}")
print(f"   Events: {events_count}")
print(f"   Busyness: {busyness}")
