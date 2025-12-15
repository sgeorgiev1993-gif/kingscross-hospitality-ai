import os
import json
import datetime
import requests

os.makedirs("data", exist_ok=True)

# --- ENV KEYS ---
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
TFL_APP_KEY = os.getenv("TFL_APP_KEY")

LAT, LON = 51.5308, -0.1238  # Kings Cross

dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "weather": {},
    "tfl": []
}

# ---------------- WEATHER ----------------
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

        dashboard["weather"] = {
            "temperature_C": w["main"]["temp"],
            "windspeed_kmh": w["wind"]["speed"],
            "condition": w["weather"][0]["main"]
        }
    except Exception as e:
        print("Weather error:", e)

# ---------------- TFL ----------------
if TFL_APP_KEY:
    try:
        tfl = requests.get(
            "https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr/Status",
            params={"app_key": TFL_APP_KEY},
            timeout=10
        ).json()

        for line in tfl:
            dashboard["tfl"].append({
                "name": line["name"],
                "mode": line["modeName"],
                "status": line["lineStatuses"][0]["statusSeverityDescription"]
            })
    except Exception as e:
        print("TfL error:", e)

with open("data/kingscross_dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard updated with real data")