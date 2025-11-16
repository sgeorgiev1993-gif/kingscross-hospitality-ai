# scripts/fetch_places_reviews.py
import requests
import json
import os
from pathlib import Path
import time

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
OUTPUT_FILE = Path("data/kingscross_places.json")

if not GOOGLE_KEY:
    raise ValueError("❌ Missing GOOGLE_PLACES_KEY GitHub secret")

BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

params = {
    "query": "restaurants near Kings Cross London",
    "radius": 1500,
    "key": GOOGLE_KEY
}

all_results = []

print("📍 Fetching Google Places (restaurants)...")

while True:
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    results = data.get("results", [])
    for r in results:
        all_results.append({
            "name": r.get("name"),
            "rating": r.get("rating"),
            "address": r.get("formatted_address"),
            "user_ratings_total": r.get("user_ratings_total"),
            "place_id": r.get("place_id")
        })

    # Pagination
    next_page = data.get("next_page_token")
    if not next_page:
        break

    time.sleep(2)  # required by Google before next_page works
    params["pagetoken"] = next_page

# Save formatted places
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"✅ Saved {len(all_results)} restaurants → {OUTPUT_FILE}")