import requests
import json
import os

# Load your Eventbrite private token from environment
TOKEN = os.getenv("EVENTBRITE_TOKEN")
if not TOKEN:
    raise ValueError("Please set your EVENTBRITE_TOKEN environment variable.")

# Optional: search by location or organizer
# You can replace 'organizer.id' with a real organizer ID if you have one
url = "https://www.eventbriteapi.com/v3/events/search/"

params = {
    "q": "Kings Cross",
    "location.address": "Kings Cross, London",
    "sort_by": "date",
    "token": TOKEN
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])

    # Save to JSON file
    with open("data/events.json", "w") as f:
        json.dump(events, f, indent=2)

    print(f"✅ {len(events)} Eventbrite events saved to data/events.json")

except requests.exceptions.HTTPError as err:
    print("Error fetching events:", err)
    # Save empty list to avoid crashing the dashboard
    with open("data/events.json", "w") as f:
        json.dump([], f)
