#!/usr/bin/env python3
import os
import json
import time
import requests
from pathlib import Path

OUTPUT_FILE = Path("data/places_reviews.json")
GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")

if not GOOGLE_KEY:
    raise ValueError("❌ GOOGLE_PLACES_KEY is missing. Add it to GitHub Secrets.")

def fetch_page(url, params):
    """Fetch a single page of Google Places results."""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching Google Places: {e}")
        return {}

def format_place(raw):
    """Normalise data for the dashboard."""
    return {
        "name": raw.get("name", "Unknown"),
        "rating": raw.get("rating", None),
        "user_ratings_total": raw.get("user_ratings_total", 0),
        "address": raw.get("formatted_address", ""),
        "types": raw.get("types", []),
        "price_level": raw.get("price_level", None),
        "place_id": raw.get("place_id", None),
        "url": f"https://www.google.com/maps/place/?q=place_id:{raw.get('place_id')}"
               if raw.get("place_id") else None
    }

def fetch_restaurants():
    print("🍽 Fetching Google Places data for Kings Cross restaurants...")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": "restaurants in Kings Cross London",
        "key": GOOGLE_KEY
    }

    all_results = []

    while True:
        data = fetch_page(url, params)
        results = data.get("results", [])
        all_results.extend(results)

        # Pagination?
        next_page = data.get("next_page_token")
        if next_page:
            print("⏳ Waiting for next_page_token...")
            time.sleep(2)
            params = {"pagetoken": next_page, "key": GOOGLE_KEY}
        else:
            break

    print(f"✅ Found {len(all_results)} restaurants")

    # Normalise all items
    cleaned = [format_place(p) for p in all_results]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    print(f"📁 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_restaurants()