import os
import json
import datetime
import requests
import statistics
import time
from math import radians, sin, cos, sqrt, atan2

# ================= CONFIG =================
LAT, LON = 51.5308, -0.1238   # Kings Cross
HISTORY_LIMIT = 300

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

print("🔑 Google Places key loaded:", bool(GOOGLE_PLACES_API_KEY))

DATA_DIR = "data"
HISTORY_DIR = os.path.join(DATA_DIR, "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "kingscross_history.json")
DASH_FILE = os.path.join(DATA_DIR, "kingscross_dashboard.json")
FORECAST_FILE = os.path.join(DATA_DIR, "forecast.json")

os.makedirs(HISTORY_DIR, exist_ok=True)

now = datetime.datetime.utcnow()
timestamp = now.isoformat() + "Z"

# ================= HELPERS =================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# ================= DASHBOARD BASE =================
dashboard = {
    "timestamp": timestamp,
    "weather": None,
    "tfl": [],
    "events": [],
    "venues": [],
    "clusters": {},
    "transit_pressure": {}
}

# ================= WEATHER =================
temperature = None
windspeed = None
condition = None

if OPENWEATHER_KEY:
    try:
        w = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": LAT, "lon": LON, "appid": OPENWEATHER_KEY, "units": "metric"},
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
        print("Weather failed:", e)

# ================= TFL =================
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
        print("TfL failed:", e)

# ================= EVENTS =================
events_count = 0

if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={"location.address": "Kings Cross London", "location.within": "1km"},
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
        print("Eventbrite failed:", e)

# ---------------- GOOGLE PLACES (FOOD VENUES – COAL DROPS FOCUS) ----------------
venues = []

def add_place(place):
    venues.append({
        "id": place.get("place_id"),
        "name": place.get("name"),
        "rating": place.get("rating"),
        "reviews": place.get("user_ratings_total"),
        "types": place.get("types", []),
        "lat": place["geometry"]["location"]["lat"],
        "lng": place["geometry"]["location"]["lng"]
    })

if GOOGLE_PLACES_API_KEY:
    try:
        # 1️⃣ Broad FOOD search (not restaurant)
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "key": GOOGLE_PLACES_API_KEY,
                "location": f"{LAT},{LON}",
                "radius": 900,
                "type": "food"  # 👈 KEY CHANGE
            },
            timeout=10
        ).json()

        for place in r.get("results", []):
            add_place(place)

        # 2️⃣ Force Coal Drops Yard anchor venues
        anchors = [
            "Morty & Bob's Kings Cross",
            "Dishoom King's Cross",
            "Coal Drops Yard restaurants",
            "Casa Pastor Kings Cross",
            "Parrillan Kings Cross"
        ]

        for q in anchors:
            fr = requests.get(
                "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
                params={
                    "input": q,
                    "inputtype": "textquery",
                    "fields": "place_id,name,geometry,types,rating,user_ratings_total",
                    "key": GOOGLE_PLACES_API_KEY
                },
                timeout=10
            ).json()

            for c in fr.get("candidates", []):
                add_place(c)

        # 3️⃣ De-duplicate by place_id
        seen = {}
        for v in venues:
            seen[v["id"]] = v
        venues = list(seen.values())

        # 4️⃣ Distance + transit reliance
        final = []
        for v in venues:
            dist = haversine_km(LAT, LON, v["lat"], v["lng"])
            transit_reliance = 0.95 if dist < 0.35 else 0.85 if dist < 0.7 else 0.7

            v["distance_km"] = round(dist, 2)
            v["transit_reliance"] = round(transit_reliance, 2)
            final.append(v)

        dashboard["venues"] = sorted(final, key=lambda x: x["distance_km"])

        print(f"🍽 Food venues loaded: {len(dashboard['venues'])}")

    except Exception as e:
        print("Google Places FOOD fetch failed:", e)

# sort + cap venues
dashboard["venues"] = sorted(
    dashboard["venues"],
    key=lambda v: (v["distance_km"], -(v.get("rating") or 0))
)[:30]

# ================= HISTORY =================
history = []
if os.path.exists(HISTORY_FILE):
    try:
        history = json.load(open(HISTORY_FILE))
    except:
        history = []

busyness = 40
if temperature is not None:
    busyness += 12 if temperature >= 18 else 6 if temperature >= 12 else -6 if temperature < 5 else 0

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
json.dump(history, open(HISTORY_FILE, "w"), indent=2)

# ================= FORECAST =================
values = [h["busyness"] for h in history]
avg = statistics.mean(values) if values else 55
std = statistics.pstdev(values) if len(values) > 1 else 8

forecast = []
for i in range(1, 13):
    t = now + datetime.timedelta(hours=i)
    rush = t.hour in (7,8,9,16,17,18)
    base = min(100, avg + (12 if rush else 0))

    forecast.append({
        "time": t.isoformat() + "Z",
        "busyness": int(base),
        "low": int(max(base - std, 0)),
        "high": int(min(base + std, 100)),
        "rush_hour": rush,
        "confidence": "low" if len(values) < 6 else "medium"
    })

json.dump(forecast, open(FORECAST_FILE, "w"), indent=2)

# ================= CLUSTERS =================
clusters = {"transit": 40, "leisure": 35, "dining": 30}
if now.hour in (7,8,9,16,17,18):
    clusters["transit"] += 20
clusters["transit"] += transport_stress
clusters["leisure"] += events_count * 6
clusters["dining"] += events_count * 4

dashboard["clusters"] = {k: max(0, min(100, v)) for k,v in clusters.items()}

dashboard["transit_pressure"] = {
    "score": dashboard["clusters"]["transit"],
    "level": "High" if dashboard["clusters"]["transit"] >= 70 else
             "Medium" if dashboard["clusters"]["transit"] >= 45 else "Low"
}

# per-venue transport impact
for v in dashboard["venues"]:
    v["transport_impact"] = round(transport_stress * v["transit_reliance"], 1)

json.dump(dashboard, open(DASH_FILE, "w"), indent=2)

print("✅ Pipeline complete")
print(f"📍 Venues fetched: {len(dashboard['venues'])}")