# scripts/fetch_places_reviews.py
import requests
import json
import os
from pathlib import Path

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
DATA_PATH = Path("data/kingscross_restaurants.json")

if not API_KEY:
    raise ValueError("Please set the GOOGLE_PLACES_API_KEY environment variable")

# Example: fetch restaurants around Kings Cross
LOCATION = "51.5308,-0.1238"  # Kings Cross coordinates
RADIUS = 1000  # meters
TYPE = "restaurant"

url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
params = {
    "location": LOCATION,
    "radius": RADIUS,
    "type": TYPE,
    "key": API_KEY
}

response = requests.get(url, params=params)
response.raise_for_status()
places = response.json().get("results", [])

# Extract relevant fields
restaurants = []
for place in places:
    restaurants.append({
        "name": place.get("name"),
        "address": place.get("vicinity"),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("user_ratings_total")
    })

DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(DATA_PATH, "w") as f:
    json.dump(restaurants, f, indent=2)

print(f"Restaurants data saved to {DATA_PATH}")
