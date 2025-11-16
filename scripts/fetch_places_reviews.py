#!/usr/bin/env python3
import requests
import json
from pathlib import Path
import os

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
OUTPUT_FILE = Path("data/places_reviews.json")   # ✅ match dashboard

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
    raw_results = response.json().get("results", [])
except Exception as e:
    print(f"Error fetching restaurants: {e}")
    raw_results = []

# ---- Extract only useful info ----
results = []
for item in raw_results:
    results.append({
        "name": item.get("name"),
        "rating": item.get("rating", "N/A"),
        "user_ratings_total": item.get("user_ratings_total", 0),
        "address": item.get("formatted_address", "Unknown address"),
        "price_level": item.get("price_level", "N/A"),
        "types": item.get("types", [])
    })

# ---- Save to file ----
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Restaurant data saved to {OUTPUT_FILE}")