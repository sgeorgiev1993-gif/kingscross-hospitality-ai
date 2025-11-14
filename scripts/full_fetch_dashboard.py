#!/usr/bin/env python3
import os
import requests
import json
from pathlib import Path
import datetime

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ----------------- TfL / Rail -----------------
TFL_FILE = DATA_DIR / "kingscross_tfl.json"
tfl_data = {}

try:
    with open(TFL_FILE) as f:
        tfl_data = json.load(f)
except FileNotFoundError:
    print("⚠️ TfL file missing, dashboard will skip transport data.")

# Normalize TfL to list
tfl_list = []
if isinstance(tfl_data, dict):
    for name, info in tfl_data.items():
        tfl_list.append({
            "name": name,
            "mode": info.get("mode", "unknown"),
            "status": info.get("status", "Unknown")
        })
elif isinstance(tfl_data, list):
    tfl_list = tfl_data

# ----------------- Weather -----------------
WEATHER_FILE = DATA_DIR / "kingscross_weather.json"
weather_data = {}
try:
    with open(WEATHER_FILE) as f:
        weather_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Weather file missing, dashboard will skip weather data.")

# ----------------- Eventbrite -----------------
EVENTS_FILE = DATA_DIR / "events.json"
events_data = []
try:
    with open(EVENTS_FILE) as f:
        events_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Events file missing, dashboard will skip events.")

# ----------------- Google Places / Restaurants -----------------
PLACES_FILE = DATA_DIR / "places_reviews.json"
places_data = []
try:
    with open(PLACES_FILE) as f:
        places_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Places file missing, dashboard will skip places.")

# ----------------- News -----------------
NEWS_FILE = DATA_DIR / "news.json"
news_data = []
try:
    with open(NEWS_FILE) as f:
        news_data = json.load(f)
except FileNotFoundError:
    print("⚠️ News file missing, dashboard will skip news.")

# ----------------- Combine dashboard -----------------
dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "tfl": tfl_list,
    "weather": weather_data if isinstance(weather_data, dict) else {},
    "events": events_data if isinstance(events_data, list) else [],
    "places": places_data if isinstance(places_data, list) else [],
    "news": news_data if isinstance(news_data, list) else []
}

DASHBOARD_FILE = DATA_DIR / "kingscross_dashboard.json"
with open(DASHBOARD_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"✅ Dashboard successfully saved to {DASHBOARD_FILE}")
