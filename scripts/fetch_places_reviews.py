# scripts/fetch_places_reviews.py
import requests
import json
from pathlib import Path
import os
import time

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
INPUT_FILE = Path("data/restaurants.json")
OUTPUT_FILE = Path("data/places_reviews.json")

if not GOOGLE_KEY:
    raise ValueError("Please set GOOGLE_PLACES_KEY in your GitHub secrets.")

if not INPUT_FILE.exists():
    raise FileNotFoundError("restaurants.json not found! Did fetch_restaurants.py run?")

with open(INPUT_FILE, "r") as f:
    restaurants = json.load(f)

all_reviews = []

for place in restaurants[:10]:  # limit to avoid quota issues
    place_id = place.get("place_id")
    if not place_id:
        continue

    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews,formatted_address",
        "key": GOOGLE_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get("result", {})
        all_reviews.append(data)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching details for {place_id}: {e}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(all_reviews, f, indent=2)

print(f"✅ Saved place reviews to {OUTPUT_FILE}")