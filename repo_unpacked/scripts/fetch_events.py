import requests
import json
from pathlib import Path
import os

OUTPUT_FILE = Path("data/events.json")
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")

if not EVENTBRITE_TOKEN:
    raise ValueError("Missing EVENTBRITE_TOKEN in GitHub secrets.")

url = "https://www.eventbriteapi.com/v3/events/search/"

params = {
    "location.address": "Kings Cross London",
    "location.within": "2km",
    "expand": "venue,organizer",
    "sort_by": "date"
}

headers = {
    "Authorization": f"Bearer {EVENTBRITE_TOKEN}"
}

try:
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])
except Exception as e:
    print(f"❌ Error fetching events: {e}")
    events = []

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(events, f, indent=2)

print(f"✅ Saved {len(events)} events → {OUTPUT_FILE}")