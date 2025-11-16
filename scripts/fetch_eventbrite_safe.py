import requests
import json
import os

TOKEN = os.getenv("EVENTBRITE_TOKEN")
ORGANIZER_ID = os.getenv("EVENTBRITE_ORGANIZER_ID")  # optional

if not TOKEN:
    raise ValueError("Please set your EVENTBRITE_TOKEN environment variable.")

def fetch_by_organizer(organizer_id):
    url = f"https://www.eventbriteapi.com/v3/organizers/{organizer_id}/events/"
    params = {"token": TOKEN, "status": "live"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])
    return events

def fetch_by_location():
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "q": "Kings Cross",
        "location.address": "London",
        "location.within": "5km",
        "sort_by": "date",
        "token": TOKEN
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])
    return events

# Try organizer first, fallback to location search
try:
    if ORGANIZER_ID:
        events = fetch_by_organizer(ORGANIZER_ID)
    else:
        events = []

    if not events:
        events = fetch_by_location()

    # Save events to JSON
    with open("data/events.json", "w") as f:
        json.dump(events, f, indent=2)

    print(f"✅ {len(events)} Eventbrite events saved to data/events.json")

except requests.exceptions.HTTPError as err:
    print("Error fetching events:", err)
    with open("data/events.json", "w") as f:
        json.dump([], f)
