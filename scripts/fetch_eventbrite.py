# scripts/fetch_eventbrite.py
import requests
import json
from pathlib import Path
import os

EVENTBRITE_KEY = os.getenv("EVENTBRITE_KEY")
OUTPUT_FILE = Path("data/events.json")

if not EVENTBRITE_KEY:
    raise ValueError("Please set EVENTBRITE_KEY in your GitHub secrets.")

url = "https://www.eventbriteapi.com/v3/events/search/"
params = {
    "q": "Kings Cross",
    "location.address": "Kings Cross, London",
    "token": EVENTBRITE_KEY,
    "sort_by": "date"
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])
except Exception as e:
    print(f"Error fetching events: {e}")
    events = []

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(events, f, indent=2)

print(f"✅ Eventbrite events saved to {OUTPUT_FILE}")
