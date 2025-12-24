import os
import json
import datetime
import requests
import statistics
from math import radians, sin, cos, sqrt, atan2

# ======================================================
# CONFIG
# ======================================================
LAT, LON = 51.5308, -0.1238  # Kings Cross / Coal Drops Yard
HISTORY_LIMIT = 600          # keep more during seasonal mode
OBS_LIMIT = 3000             # observations for Christmas/NYE learning

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

DATA_DIR = "data"
HISTORY_DIR = f"{DATA_DIR}/history"
os.makedirs(HISTORY_DIR, exist_ok=True)

DASH_FILE = f"{DATA_DIR}/kingscross_dashboard.json"
HISTORY_FILE = f"{HISTORY_DIR}/kingscross_history.json"
FORECAST_FILE = f"{DATA_DIR}/forecast.json"
OBS_FILE = f"{DATA_DIR}/observations.json"
ANOM_FILE = f"{DATA_DIR}/anomalies.json"

# ======================================================
# HELPERS
# ======================================================

def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def safe_save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def utc_iso(dt: datetime.datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def holiday_phase(dt: datetime.datetime) -> str:
    if dt.month == 12 and dt.day == 31:
        return "nye"
    if dt.month == 12 and 27 <= dt.day <= 30:
        return "pre_nye"
    if dt.month == 12 and 20 <= dt.day <= 26:
        return "christmas_period"
    if dt.month == 1 and dt.day == 1:
        return "new_year_day"
    return "normal"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def compute_transport_stress(tfl_lines):
    stress = 0
    disrupted = 0
    for l in tfl_lines:
        st = l.get("status", "")
        if st and st != "Good Service":
            stress += 8
            disrupted += 1
    return stress, disrupted


def lunch_signature_boost(hour, minute, venue):
    if not venue:
        return 0

    types = venue.get("types", []) or []
    rating = float(venue.get("rating") or 0)

    is_foodish = any(t in types for t in ["restaurant", "cafe", "bar", "meal_takeaway", "food"])
    if not (is_foodish and rating >= 4.3):
        return 0

    t = hour + minute / 60.0
    if 11.5 <= t < 12.0:
        return 6
    elif 12.0 <= t < 13.25:
        return 14
    elif 13.25 <= t < 13.75:
        return 9
    elif 14.0 <= t < 14.75:
        return 6
    elif 14.75 <= t < 15.25:
        return 2
    return 0


# ---------------- ANOMALY HELPERS ----------------

def anomaly_confidence(base=0.55, agreements=0, penalties=0):
    c = base + 0.08 * agreements - 0.10 * penalties
    return clamp(c, 0.40, 0.95)


def anomaly_persistence(anoms, typ, window=6):
    recent = [a for a in anoms[-window:] if a.get("type") == typ]
    if len(recent) >= 4:
        return "established"
    if len(recent) >= 2:
        return "emerging"
    return "transient"


def add_anomaly(anoms, *, ts, typ, severity, confidence, explanation, drivers):
    persistence = anomaly_persistence(anoms, typ)

    anoms.append({
        "timestamp": ts,
        "type": typ,
        "severity": severity,
        "confidence": round(float(confidence), 2),
        "persistence": persistence,
        "explanation": explanation,
        "drivers": drivers
    })


def seasonal_baseline(history, hour_utc):
    hist = history[-400:] if len(history) > 400 else history
    same_hour = [
        h for h in hist
        if isinstance(h.get("timestamp"), str)
        and datetime.datetime.fromisoformat(h["timestamp"].replace("Z","")).hour == hour_utc
    ]
    vals = [h["busyness"] for h in same_hour if isinstance(h.get("busyness"), (int, float))]
    if len(vals) >= 8:
        return vals[-80:]
    return [h["busyness"] for h in hist if isinstance(h.get("busyness"), (int, float))][-120:]

# ======================================================
# TIME / CONTEXT
# ======================================================
now = datetime.datetime.utcnow()
timestamp = utc_iso(now)
phase = holiday_phase(now)

context = {
    "holiday_phase": phase,
    "date": now.strftime("%Y-%m-%d"),
    "hour": now.hour
}

print("🔑 Google Places key loaded:", bool(GOOGLE_PLACES_API_KEY))
print("🗓️ Seasonal context:", context)

# ======================================================
# DASHBOARD BASE
# ======================================================
dashboard = {
    "timestamp": timestamp,
    "context": context,
    "weather": None,
    "tfl": [],
    "events": [],
    "venues": [],
    "clusters": {},
    "transit_pressure": {}
}

# ======================================================
# 1) WEATHER
# ======================================================
temperature = None
windspeed = None
condition = None

if OPENWEATHER_KEY:
    try:
        w = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": LAT, "lon": LON, "appid": OPENWEATHER_KEY, "units": "metric"},
            timeout=12
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

# ======================================================
# 2) TFL
# ======================================================
if TFL_APP_KEY:
    try:
        tfl = requests.get(
            "https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr/Status",
            params={"app_key": TFL_APP_KEY},
            timeout=12
        ).json()

        for line in tfl:
            status = line["lineStatuses"][0]["statusSeverityDescription"]
            dashboard["tfl"].append({
                "name": line["name"],
                "mode": line["modeName"],
                "status": status
            })
    except Exception as e:
        print("TfL failed:", e)

transport_stress, disrupted_lines = compute_transport_stress(dashboard["tfl"])

# ======================================================
# 3) EVENTBRITE
# ======================================================
events_count = 0
if EVENTBRITE_TOKEN:
    try:
        r = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers={"Authorization": f"Bearer {EVENTBRITE_TOKEN}"},
            params={"location.address": "Coal Drops Yard London", "location.within": "1km"},
            timeout=12
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
# 4) GOOGLE PLACES – FOOD-RELEVANT VENUES
#    (Don’t use type="food" — it’s unreliable. Use multiple types.)
# ======================================================
venues = []
if GOOGLE_PLACES_API_KEY:
    try:
        seen = set()
        types_to_pull = ["restaurant", "cafe", "bar", "meal_takeaway"]

        for t in types_to_pull:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "key": GOOGLE_PLACES_API_KEY,
                    "location": f"{LAT},{LON}",
                    "radius": 1400,
                    "type": t
                },
                timeout=12
            ).json()

            if r.get("status") not in (None, "OK", "ZERO_RESULTS"):
                # keep visible for debugging in Actions logs
                print(f"Google Places status for type={t}: {r.get('status')} — {r.get('error_message')}")

            for place in r.get("results", [])[:30]:
                pid = place.get("place_id")
                if not pid or pid in seen:
                    continue
                seen.add(pid)

                plat = place["geometry"]["location"]["lat"]
                plon = place["geometry"]["location"]["lng"]
                dist = haversine_km(LAT, LON, plat, plon)

                transit_reliance = 0.95 if dist < 0.35 else 0.85 if dist < 0.8 else 0.70

                venues.append({
                    "id": pid,
                    "name": place.get("name"),
                    "rating": place.get("rating"),
                    "reviews": place.get("user_ratings_total"),
                    "types": place.get("types", []),
                    "lat": plat,
                    "lng": plon,
                    "distance_km": round(dist, 2),
                    "transit_reliance": round(transit_reliance, 2),
                    # placeholder; UI can compute later
                    "transport_impact": 0.0
                })

        # Sort: closest first, then by reviews
        venues.sort(key=lambda v: (v.get("distance_km", 9), -(v.get("reviews") or 0)))

    except Exception as e:
        print("Google Places failed:", e)

dashboard["venues"] = venues

# ======================================================
# 5) HISTORY + BUSYNESS MODEL (seasonal mode)
# ======================================================
history = safe_load_json(HISTORY_FILE, [])

# choose "validator venue" (Morty & Bob's) if present, otherwise best-rated nearby
validator = None
for v in dashboard["venues"]:
    if v.get("name") and "Morty" in v["name"]:
        validator = v
        break
if validator is None and dashboard["venues"]:
    validator = dashboard["venues"][0]

busyness = 40

# weather effect
if temperature is not None:
    if temperature >= 18:
        busyness += 12
    elif temperature >= 12:
        busyness += 6
    elif temperature < 5:
        busyness -= 6

# transport + events
busyness += transport_stress
busyness += events_count * 6

# seasonal uplift: christmas_period & pre_nye slightly increase baseline
if phase == "christmas_period":
    busyness += 4
elif phase == "pre_nye":
    busyness += 6
elif phase == "nye":
    busyness += 10
elif phase == "new_year_day":
    busyness += 3

# lunch signature (venue-led)
busyness += lunch_signature_boost(now.hour, now.minute, validator)

busyness = int(clamp(busyness, 0, 100))

history.append({
    "timestamp": timestamp,
    "busyness": busyness,
    "temperature": temperature,
    "transport_stress": transport_stress,
    "events_count": events_count,
    "holiday_phase": phase
})
history = history[-HISTORY_LIMIT:]
safe_save_json(HISTORY_FILE, history)

# ======================================================
# 6) FORECAST (next 12 hours)
# ======================================================
values = [h["busyness"] for h in history if isinstance(h.get("busyness"), (int, float))]
avg = statistics.mean(values) if values else 55
std = statistics.pstdev(values) if len(values) > 1 else 10

forecast = []
for i in range(1, 13):
    t = now + datetime.timedelta(hours=i)
    rush = t.hour in (7, 8, 9, 16, 17, 18)

    base = avg + (12 if rush else 0)

    # seasonal uplift in forecast too
    ph = holiday_phase(t)
    if ph == "christmas_period":
        base += 4
    elif ph == "pre_nye":
        base += 6
    elif ph == "nye":
        base += 10
    elif ph == "new_year_day":
        base += 3

    # lunch signature only around lunch hours
    base += lunch_signature_boost(t.hour, 0, validator)

    base = clamp(base, 0, 100)

    forecast.append({
        "time": utc_iso(t),
        "busyness": int(base),
        "low": int(clamp(base - std, 0, 100)),
        "high": int(clamp(base + std, 0, 100)),
        "rush_hour": rush,
        "confidence": "medium" if len(values) >= 10 else "low"
    })

safe_save_json(FORECAST_FILE, forecast)

# ======================================================
# 7) CLUSTERS + TRANSIT PRESSURE (Coal Drops Yard story)
# ======================================================
clusters = {"transit": 40, "leisure": 35, "dining": 30}

if now.hour in (7, 8, 9, 16, 17, 18):
    clusters["transit"] += 20

clusters["transit"] += transport_stress
clusters["leisure"] += events_count * 6
clusters["dining"] += events_count * 4

# seasonal pushes
if phase in ("christmas_period", "pre_nye"):
    clusters["leisure"] += 6
    clusters["dining"] += 6
if phase == "nye":
    clusters["leisure"] += 12
    clusters["dining"] += 10

clusters = {k: int(clamp(v, 0, 100)) for k, v in clusters.items()}
dashboard["clusters"] = clusters

drivers = []
if now.hour in (7, 8, 9, 16, 17, 18):
    drivers.append("Rush hour")
if disrupted_lines:
    drivers.append(f"{disrupted_lines} disrupted lines")
if events_count:
    drivers.append("Events nearby")
if phase != "normal":
    drivers.append(f"Holiday phase: {phase}")

tp_score = clusters["transit"]
tp_level = "High" if tp_score >= 70 else "Medium" if tp_score >= 45 else "Low"

dashboard["transit_pressure"] = {
    "score": tp_score,
    "level": tp_level,
    "drivers": drivers
}

# ======================================================
# 8) OBSERVATIONS (raw “truth log” for seasonal mode)
# ======================================================
observations = safe_load_json(OBS_FILE, [])
observations.append({
    "timestamp": timestamp,
    "context": context,
    "signals": {
        "busyness": busyness,
        "transport_stress": transport_stress,
        "disrupted_lines": disrupted_lines,
        "events_count": events_count,
        "temperature_C": temperature,
        "weather_condition": condition
    }
})
observations = observations[-OBS_LIMIT:]
safe_save_json(OBS_FILE, observations)

# ======================================================
# 9) ANOMALY ENGINE (v1 explainable, taxonomy-friendly)
# ======================================================
anomalies = safe_load_json(ANOM_FILE, [])

# baseline for this hour
baseline_vals = seasonal_baseline(history, now.hour)
b_avg = statistics.mean(baseline_vals) if baseline_vals else 55
b_std = statistics.pstdev(baseline_vals) if len(baseline_vals) > 1 else 10

# compare vs forecast (the run generates forecast; first point is next hour, so baseline is better here)
z = (busyness - b_avg) / max(b_std, 1)

drivers = []
agreements = 0
penalties = 0

if phase != "normal":
    drivers.append(f"holiday_phase:{phase}")
    agreements += 1

if transport_stress >= 16:
    drivers.append("transport_disruption")
    agreements += 1

if events_count >= 2:
    drivers.append("events")
    agreements += 1

if condition and str(condition).lower() in ("clear", "clouds"):
    drivers.append("fair_weather")
    agreements += 1

# Demand anomalies
if z >= 2.0:
    sev = "high" if z >= 3.0 else "medium"
    conf = anomaly_confidence(0.58, agreements=agreements, penalties=penalties)
    add_anomaly(
        anomalies,
        ts=timestamp,
        typ="unexpected_peak",
        severity=sev,
        confidence=conf,
        explanation=f"Demand is significantly above baseline for this hour (z≈{z:.1f}).",
        drivers=drivers
    )

if z <= -2.0:
    sev = "high" if z <= -3.0 else "medium"
    conf = anomaly_confidence(0.56, agreements=max(agreements-1, 0), penalties=penalties+1)
    add_anomaly(
        anomalies,
        ts=timestamp,
        typ="suppressed_demand",
        severity=sev,
        confidence=conf,
        explanation=f"Demand is significantly below baseline for this hour (z≈{z:.1f}).",
        drivers=drivers
    )

# Prolonged peak: last 3 points >= (baseline avg + 1 std)
if len(history) >= 2:
    last3 = [h.get("busyness") for h in history[-3:] if isinstance(h.get("busyness"), (int, float))]
    if len(last3) == 3 and all(v >= (b_avg + b_std) for v in last3):
        conf = anomaly_confidence(0.62, agreements=agreements+1, penalties=penalties)
        add_anomaly(
            anomalies,
            ts=timestamp,
            typ="prolonged_peak",
            severity="medium",
            confidence=conf,
            explanation="Demand has stayed elevated for multiple consecutive runs, longer than baseline norm.",
            drivers=drivers
        )

# Volatile demand: last 4 points range is large
if len(history) >= 5:
    last4 = [h.get("busyness") for h in history[-4:] if isinstance(h.get("busyness"), (int, float))]
    if len(last4) == 4 and (max(last4) - min(last4)) >= 22:
        conf = anomaly_confidence(0.55, agreements=max(agreements-1, 0), penalties=penalties+1)
        add_anomaly(
            anomalies,
            ts=timestamp,
            typ="volatile_demand",
            severity="low",
            confidence=conf,
            explanation="Demand fluctuated sharply within a short window.",
            drivers=drivers
        )

# Keep last ~500 anomalies
anomalies = anomalies[-500:]
safe_save_json(ANOM_FILE, anomalies)

# ======================================================
# SAVE DASHBOARD (FINAL)
# ======================================================
safe_save_json(DASH_FILE, dashboard)

print("✅ Pipeline complete")
print(f"📍 Venues loaded: {len(dashboard['venues'])}")
print(f"🔥 Busyness now: {busyness}")
print(f"🧠 Baseline avg/std: {b_avg:.1f}/{b_std:.1f} (hour={now.hour} UTC)")
print(f"🚨 Anomalies total: {len(anomalies)} (latest written if triggered)")
