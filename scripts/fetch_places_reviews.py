# scripts/fetch_places_reviews.py
import requests
import json
from pathlib import Path
import os

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
OUTPUT_FILE = Path("data/restaurants.json")

if not GOOGLE_KEY:
    raise ValueError("Please set GOOGLE_PLACES_KEY in your GitHub secrets.")

url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
params = {
    "query": "restaurants in Kings Cross, London",
    "key": GOOGLE_KEY
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
except Exception as e:
    print(f"Error fetching restaurants: {e}")
    results = []

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Restaurants saved to {OUTPUT_FILE}")
