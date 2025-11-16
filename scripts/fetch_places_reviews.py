#!/usr/bin/env python3
"""
Fetch restaurants near Kings Cross, get photo & reviews, save photos locally,
and write data/places_reviews.json with fields:
  - name, rating, user_ratings_total, address, price_level, place_id, photo, review_excerpt
Also saves first photo to data/photos/<place_id>.jpg (if available).
"""
import os
import json
import time
import requests
from pathlib import Path
from io import BytesIO

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_KEY")
if not GOOGLE_KEY:
    raise ValueError("Missing GOOGLE_PLACES_KEY environment variable (GitHub secret).")

DATA_DIR = Path("data")
PHOTOS_DIR = DATA_DIR / "photos"
OUTPUT_FILE = DATA_DIR / "places_reviews.json"

TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

# Search parameters (center on King's Cross)
params = {
    "query": "restaurants in Kings Cross London",
    "key": GOOGLE_KEY
}

def fetch_json(url, params):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}

def download_photo(photo_reference, dest_path, maxwidth=800):
    """
    Uses the Place Photo endpoint to download a photo (binary) and save locally.
    """
    try:
        params = {"maxwidth": maxwidth, "photoreference": photo_reference, "key": GOOGLE_KEY}
        r = requests.get(PHOTO_URL, params=params, timeout=20, stream=True)
        r.raise_for_status()
        # Google responds with an image (redirects). We save the content.
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download photo {photo_reference}: {e}")
        return False

def clean_text(s):
    if not s:
        return ""
    return " ".join(str(s).split())  # collapse whitespace

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    print("🔎 Running textsearch for restaurants...")
    search_data = fetch_json(TEXTSEARCH_URL, params)
    results = search_data.get("results", [])

    print(f"Found {len(results)} candidate places (first page).")

    places_out = []

    # Optionally handle pagination (up to ~60 results). We'll process first page for now to be conservative.
    # If you want all pages, implement next_page_token handling (with sleep).
    for i, r in enumerate(results):
        place_id = r.get("place_id")
        name = r.get("name")
        rating = r.get("rating")
        user_ratings_total = r.get("user_ratings_total")
        address = r.get("formatted_address") or r.get("vicinity") or ""
        price_level = r.get("price_level")

        place = {
            "place_id": place_id,
            "name": name,
            "rating": rating,
            "user_ratings_total": user_ratings_total,
            "address": address,
            "price_level": price_level,
            "photo": None,
            "review_excerpt": None
        }

        if not place_id:
            print(f"Skipping place (no place_id): {name}")
            places_out.append(place)
            continue

        # Fetch details for photo and reviews
        print(f"[{i+1}/{len(results)}] Getting details for {name} ({place_id})")
        details = fetch_json(DETAILS_URL, {"place_id": place_id, "fields": "photo,reviews,formatted_address,opening_hours,website", "key": GOOGLE_KEY})
        result = details.get("result", {})

        # Photo
        photos = result.get("photos") or []
        if photos:
            first_photo_ref = photos[0].get("photo_reference")
            if first_photo_ref:
                dest_filename = f"{place_id}.jpg"
                dest_path = PHOTOS_DIR / dest_filename
                success = download_photo(first_photo_ref, dest_path, maxwidth=800)
                if success:
                    # Save relative path for the dashboard to use
                    place["photo"] = f"data/photos/{dest_filename}"
                else:
                    place["photo"] = None
            else:
                place["photo"] = None
        else:
            place["photo"] = None

        # Reviews: take first review text as excerpt if available
        reviews = result.get("reviews") or []
        if reviews:
            # choose longest review or first non-empty
            excerpt = None
            for rv in reviews:
                txt = rv.get("text") or ""
                if txt and len(txt) > 30:
                    excerpt = clean_text(txt[:220])  # short excerpt
                    break
            if not excerpt and reviews:
                excerpt = clean_text(reviews[0].get("text", "")[:220])
            place["review_excerpt"] = excerpt
        else:
            place["review_excerpt"] = None

        # small throttle to be polite / avoid quota bursts
        time.sleep(0.5)

        places_out.append(place)

    # Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(places_out, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(places_out)} places to {OUTPUT_FILE}")
    print(f"✅ Photos (if any) saved to {PHOTOS_DIR}")

if __name__ == "__main__":
    main()