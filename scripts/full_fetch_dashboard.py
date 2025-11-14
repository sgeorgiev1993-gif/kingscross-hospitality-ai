# scripts/full_fetch_dashboard.py
import os
import json
import requests
import datetime
from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ----------------- Weather -----------------
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")
if not WEATHER_KEY:
    raise ValueError("OPENWEATHER_KEY missing!")

weather_file = DATA_DIR / "kingscross_weather.json"
r = requests.get(
    "https://api.openweathermap.org/data/2.5/weather",
    params={"q": "Kings Cross, London, UK", "appid": WEATHER_KEY, "units": "metric"}
)
weather_data = r.json()
weather_info = {
    "temperature_C": weather_data.get("main", {}).get("temp"),
    "windspeed_kmh": weather_data.get("wind", {}).get("speed"),
    "weather_code": weather_data.get("weather", [{}])[0].get("id")
}
with open(weather_file, "w") as f:
    json.dump(weather_info, f, indent=2)

# ----------------- TfL -----------------
TFL_KEY = os.getenv("TFL_APP_KEY")
if not TFL_KEY:
    raise ValueError("TFL_APP_KEY missing!")

tfl_file = DATA_DIR / "kingscross_tfl.json"
MODES = ["tube", "overground", "dlr", "tflrail", "national-rail"]
all_lines = []

for mode in MODES:
    url = f"https://api.tfl.gov.uk/Line/Mode/{mode}/Status"
    r = requests.get(url)
    for line in r.json():
        all_lines.append({
            "name": line.get("name"),
            "mode": mode,
            "status": line.get("lineStatuses", [{}])[0].get("statusSeverityDescription", "Unknown")
        })

with open(tfl_file, "w") as f:
    json.dump(all_lines, f, indent=2)

# ----------------- Eventbrite -----------------
EB_TOKEN = os.getenv("EVENTBRITE_TOKEN")
if not EB_TOKEN:
    raise ValueError("EVENTBRITE_TOKEN missing!")

events_file = DATA_DIR / "events.json"
eb_url = f"https://www.eventbriteapi.com/v3/events/search/"
params = {"location.address": "Kings Cross, London", "q": "Kings Cross", "sort_by": "date", "token": EB_TOKEN}
r = requests.get(eb_url, params=params)
events_data = r.json().get("events", [])
events = [{"name": e.get("name", {}).get("text"), "start": e.get("start", {}).get("local"), "url": e.get("url")} for e in events_data]

with open(events_file, "w") as f:
    json.dump(events, f, indent=2)

# ----------------- Google Places / Restaurants -----------------
GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
if not GOOGLE_KEY:
    raise ValueError("GOOGLE_PLACES_KEY missing!")

places_file = DATA_DIR / "restaurants.json"
places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
params = {"query": "restaurants in Kings Cross, London", "key": GOOGLE_KEY}
r = requests.get(places_url, params=params)
places_data = r.json().get("results", [])

with open(places_file, "w") as f:
    json.dump(places_data, f, indent=2)

# ----------------- News -----------------
NEWS_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_KEY:
    raise ValueError("NEWS_API_KEY missing!")

news_file = DATA_DIR / "news.json"
news_url = "https://newsapi.org/v2/everything"
params = {"q": "Kings Cross London", "language": "en", "pageSize": 10, "sortBy": "publishedAt", "apiKey": NEWS_KEY}
r = requests.get(news_url, params=params)
news_data = r.json().get("articles", [])

with open(news_file, "w") as f:
    json.dump(news_data, f, indent=2)

# ----------------- Combined Dashboard -----------------
dashboard_file = DATA_DIR / "kingscross_dashboard.json"
dashboard = {
    "weather": weather_info,
    "tfl": all_lines,
    "events": events,
    "places": places_data,
    "news": news_data
}

with open(dashboard_file, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"✅ Full dashboard data saved to {dashboard_file}")
