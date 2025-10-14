import requests, pandas as pd, os, datetime

KEY = os.getenv("GOOGLE_PLACES_KEY")
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

LAT, LNG = 51.5308, -0.1238
RADIUS = 500

url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={LAT},{LNG}&radius={RADIUS}&type=restaurant&key={KEY}"

r = requests.get(url)
data = r.json().get("results", [])

rows = []
for p in data:
    rows.append({
        "name": p.get("name"),
        "rating": p.get("rating"),
        "user_ratings_total": p.get("user_ratings_total"),
        "address": p.get("vicinity")
    })

df = pd.DataFrame(rows)
filename = os.path.join(OUT_DIR, f"places_{datetime.date.today()}.csv")
df.to_csv(filename, index=False)
print(f"✅ Saved {len(df)} places to {filename}")
