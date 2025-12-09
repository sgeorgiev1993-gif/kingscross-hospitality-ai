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
    tfl_data = {}

tfl_list = []

def normalize_tfl_record(name, item):
    """Ensure each TfL entry is a dict with name/mode/status."""
    # If TfL API returns a list of statuses, use the first one
    if isinstance(item, list):
        item = item[0] if item else {}

    # If still not a dict, convert to empty dict
    if not isinstance(item, dict):
        item = {}

    return {
        "name": name,
        "mode": item.get("mode", "unknown"),
        "status": item.get("status", "Unknown")
    }

# Case 1: dict structure (most common)
if isinstance(tfl_data, dict):
    for name, info in tfl_data.items():
        tfl_list.append(normalize_tfl_record(name, info))

# Case 2: list from API
elif isinstance(tfl_data, list):
    for entry in tfl_data:
        # If entry is a dict with its own name
        if isinstance(entry, dict):
            name = entry.get("name", "Unknown")
        else:
            name = "Unknown"

        tfl_list.append(normalize_tfl_record(name, entry))


# ----------------- Weather -----------------
WEATHER_FILE = DATA_DIR / "kingscross_weather.json"
weather_data = {}
try:
    with open(WEATHER_FILE) as f:
        weather_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Weather file missing, dashboard will skip weather data.")
    weather_data = {}

if not isinstance(weather_data, dict):
    weather_data = {}


# ----------------- Eventbrite -----------------
EVENTS_FILE = DATA_DIR / "events.json"
events_data = []
try:
    with open(EVENTS_FILE) as f:
        events_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Events file missing, dashboard will skip events.")
    events_data = []

if not isinstance(events_data, list):
    events_data = []


# ----------------- Google Places / Restaurants -----------------
PLACES_FILE = DATA_DIR / "places_reviews.json"
places_data = []
try:
    with open(PLACES_FILE) as f:
        places_data = json.load(f)
except FileNotFoundError:
    print("⚠️ Places file missing, dashboard will skip places.")
    places_data = []

if not isinstance(places_data, list):
    places_data = []


# ----------------- News -----------------
NEWS_FILE = DATA_DIR / "news.json"
news_data = []
try:
    with open(NEWS_FILE) as f:
        news_data = json.load(f)
except FileNotFoundError:
    print("⚠️ News file missing, dashboard will skip news.")
    news_data = []

if not isinstance(news_data, list):
    news_data = []


# ----------------- Combine dashboard -----------------
dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "tfl": tfl_list,
    "weather": weather_data,
    "events": events_data,
    "places": places_data,
    "news": news_data
}

DASHBOARD_FILE = DATA_DIR / "kingscross_dashboard.json"
with open(DASHBOARD_FILE, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"✅ Dashboard successfully saved to {DASHBOARD_FILE}")