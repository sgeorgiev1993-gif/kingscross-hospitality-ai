import os
import json
import datetime
import requests
import statistics
from math import radians, sin, cos, sqrt, atan2

# ======================================================
# CONFIG
# ======================================================
LAT, LON = 51.5308, -0.1238   # Kings Cross / Coal Drops Yard
HISTORY_LIMIT = 300

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

print("🔑 Google Places key loaded:", bool(GOOGLE_PLACES_API_KEY))

DATA_DIR = "data"
HISTORY_DIR = f"{DATA_DIR}/history"
os.makedirs(HISTORY_DIR, exist_ok=True)

DASH_FILE = f"{DATA_DIR}/kingscross_dashboard.json"
HISTORY_FILE = f"{HISTORY_DIR}/kingscross_history.json"
FORECAST_FILE = f"{DATA_DIR}/forecast.json"

now = datetime.datetime.utcnow()
timestamp = now.isoformat() + "Z"
holiday_phase = holiday_context(now)

# ======================================================
# HELPERS
# ======================================================
def holiday_context(now):
    if now.month == 12 and now.day >= 20:
        return "christmas_period"
    if now.month == 12 and now.day >= 27:
        return "pre_nye"
    if now.month == 12 and now.day == 31:
        return "nye"
    if now.month == 1 and now.day == 1:
        return "new_year_day"
    return "normal"

holiday_phase = holiday_context(now)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def lunch_signature_boost(hour, minute, venue):
    """
    Destination lunch + late-lunch aftershock
    Tuned for Morty & Bob’s / Coal Drops Yard
    """
    if not venue:
        return 0

    is_food = "food" in venue.get("types", [])
    high_rating = venue.get("rating", 0) >= 4.3

    if not (is_food and high_rating):
        return 0

    t = hour + minute / 60.0

    if 11.5 <= t < 12.0:
        return 6
    elif 12.0 <= t < 13.25:
        return 14
    elif 13.25 <= t < 13.75:
        return 9
    elif 14.0 <= t < 14.75:
        return 5
    elif 14.75 <= t < 15.25:
        return 2
    return 0

# ======================================================
# DASHBOARD BASE
# ======================================================
dashboard = {
    "timestamp": timestamp,
    "weather": None,
    "tfl": [],
    "events": [],
    "venues": [],
    "clusters": {},
    "transit_pressure": {}
}
dashboard["context"] = {
    "holiday_phase": holiday_phase,
    "date": now.strftime("%Y-%m-%d"),
    "hour": now.hour
}
# ======================================================
# 1. WEATHER SIGNAL
# ======================================================
temperature = None
condition = None

if OPENWEATHER_KEY:
    try:
        w = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": LAT, "lon": LON, "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=10
        ).json()

        temperature = w["main"]["temp"]
        condition = w["weather"][0]["main"]

        dashboard["weather"] = {
            "temperature_C": temperature,
            "windspeed_kmh": w["wind"]["speed"],
            "condition": condition
        }
    except Exception as e:
        print("Weather failed:", e)

# ======================================================
# 2. TFL TRANSPORT STRESS
# ======================================================
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

# ======================================================
# 3. EVENTBRITE SIGNAL
# ======================================================
events_count = 0

if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={"location.address": "Coal Drops Yard London", "location.within": "1km"},
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

# ======================================================
# 4. GOOGLE PLACES – FOOD VENUES ONLY
# ======================================================
if GOOGLE_PLACES_API_KEY:
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "key": GOOGLE_PLACES_API_KEY,
                "location": f"{LAT},{LON}",
                "radius": 1200,
                "type": "food"
            },
            timeout=10
        ).json()

        for place in r.get("results", [])[:25]:
            types = place.get("types", [])
            if "food" not in types:
                continue

            plat = place["geometry"]["location"]["lat"]
            plon = place["geometry"]["location"]["lng"]
            dist = haversine_km(LAT, LON, plat, plon)

            transit_reliance = 0.95 if dist < 0.3 else 0.85 if dist < 0.6 else 0.7

            dashboard["venues"].append({
                "id": place.get("place_id"),
                "name": place.get("name"),
                "rating": place.get("rating"),
                "reviews": place.get("user_ratings_total"),
                "types": types,
                "lat": plat,
                "lng": plon,
                "distance_km": round(dist, 2),
                "transit_reliance": round(transit_reliance, 2)
            })

    except Exception as e:
        print("Google Places failed:", e)

# ======================================================
# 5. HISTORY + BUSYNESS MODEL
# ======================================================
history = []
if os.path.exists(HISTORY_FILE):
    history = json.load(open(HISTORY_FILE))

busyness = 40

if temperature is not None:
    busyness += 12 if temperature >= 18 else 6 if temperature >= 12 else -6 if temperature < 5 else 0

busyness += transport_stress
busyness += events_count * 6

# Venue lunch signature (use Morty & Bob’s if present)
mb = next((v for v in dashboard["venues"] if "Morty" in v["name"]), None)
busyness += lunch_signature_boost(now.hour, now.minute, mb)

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

# ======================================================
# 6. FORECAST (NEXT 12 HOURS)
# ======================================================
values = [h["busyness"] for h in history]
avg = statistics.mean(values) if values else 55
std = statistics.pstdev(values) if len(values) > 1 else 8

forecast = []
for i in range(1, 13):
    t = now + datetime.timedelta(hours=i)
    rush = t.hour in (7,8,9,16,17,18)

    base = avg + (12 if rush else 0)
    base += lunch_signature_boost(t.hour, 0, mb)
    base = max(0, min(100, base))

    forecast.append({
        "time": t.isoformat() + "Z",
        "busyness": int(base),
        "low": int(max(base - std, 0)),
        "high": int(min(base + std, 100)),
        "rush_hour": rush,
        "confidence": "medium" if len(values) >= 8 else "low"
    })

json.dump(forecast, open(FORECAST_FILE, "w"), indent=2)

# ======================================================
# 7. CLUSTER PRESSURE (COAL DROPS YARD)
# ======================================================
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

# ======================================================
# SAVE DASHBOARD
# ======================================================
json.dump(dashboard, open(DASH_FILE, "w"), indent=2)

print("✅ Pipeline complete")
print(f"📍 Food venues: {len(dashboard['venues'])}")
print(f"🔥 Busyness now: {busyness}")
