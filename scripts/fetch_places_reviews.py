# scripts/fetch_places_reviews.py
import requests
import json
from pathlib import Path

API_KEY = "YOUR_GOOGLE_PLACES_API_KEY"  # will be passed via GitHub Secrets
LOCATION = "51.5308,-0.1238"  # Kings Cross latitude, longitude
RADIUS = 1000  # meters
TYPE = "restaurant"
DATA_PATH = Path("data/restaurants.json")

def fetch_restaurants():
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={LOCATION}&radius={RADIUS}&type={TYPE}&key={API_KEY}"
    )
    restaurants = []
    while url:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        restaurants.extend(data.get("results", []))
        url = data.get("next_page_token")
        if url:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?pagetoken={url}&key={API_KEY}"

    # Simplify data
    output = []
    for r in restaurants:
        output.append({
            "name": r.get("name"),
            "rating": r.get("rating"),
            "address": r.get("vicinity"),
            "place_id": r.get("place_id")
        })

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(output)} restaurants to {DATA_PATH}")

if __name__ == "__main__":
    fetch_restaurants()
