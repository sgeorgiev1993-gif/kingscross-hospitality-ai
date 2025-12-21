#!/bin/bash
# Full KingsCross Dashboard - Chrome OS safe, patched, nice UI

cd ~/kingscross-hospitality-ai || { echo "Project folder not found!"; exit 1; }
mkdir -p data
mkdir -p scripts

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install requests jinja2

# ---- 1️⃣ Eventbrite fetch script ----
cat > scripts/fetch_eventbrite_safe.py << 'EOF'
import requests, json, os

TOKEN = "HVAXJ7RGGWBJRROIIXYK"  # Private token included
ORGANIZER_ID = os.getenv("EVENTBRITE_ORGANIZER_ID")

def fetch_by_organizer(organizer_id):
    url = f"https://www.eventbriteapi.com/v3/organizers/{organizer_id}/events/"
    resp = requests.get(url, params={"token": TOKEN, "status": "live"})
    resp.raise_for_status()
    return resp.json().get("events", [])

def fetch_by_location():
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "q": "Kings Cross",
        "location.address": "London",
        "location.within": "5km",
        "sort_by": "date",
        "token": TOKEN
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("events", [])

try:
    events = fetch_by_organizer(ORGANIZER_ID) if ORGANIZER_ID else []
    if not events:
        events = fetch_by_location()
    with open("data/events.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"✅ {len(events)} Eventbrite events saved")
except:
    with open("data/events.json", "w") as f:
        json.dump([], f)
    print("⚠️ Eventbrite fetch failed, saved empty list")
EOF

# ---- 2️⃣ News fetch script ----
cat > scripts/fetch_news_safe.py << 'EOF'
import requests, json

NEWS_KEY = "c64b577ae41141ee847b0c451cda79f5"

url = f"https://newsapi.org/v2/everything?q=Kings+Cross&sortBy=publishedAt&apiKey={NEWS_KEY}"

try:
    r = requests.get(url)
    r.raise_for_status()
    articles = r.json().get("articles", [])
    with open("data/news.json", "w") as f:
        json.dump(articles, f, indent=2)
    print(f"✅ {len(articles)} news articles saved")
except:
    with open("data/news.json", "w") as f:
        json.dump([], f)
    print("⚠️ News fetch failed, saved empty list")
EOF

# ---- 3️⃣ Places/Restaurants fetch script ----
cat > scripts/fetch_places_safe.py << 'EOF'
import requests, json

GOOGLE_KEY = "GOOGLE_PLACES_API_KEY"
LOCATION = "51.5308,-0.1238"  # Kings Cross approximate lat/lng
RADIUS = 1000  # meters
TYPE = "restaurant"

url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={LOCATION}&radius={RADIUS}&type={TYPE}&key={GOOGLE_KEY}"

try:
    r = requests.get(url)
    r.raise_for_status()
    places = r.json().get("results", [])
    with open("data/restaurants.json", "w") as f:
        json.dump(places, f, indent=2)
    print(f"✅ {len(places)} restaurants saved")
except:
    with open("data/restaurants.json", "w") as f:
        json.dump([], f)
    print("⚠️ Places fetch failed, saved empty list")
EOF

# ---- 4️⃣ Run all fetches in parallel ----
python3 scripts/fetch_eventbrite_safe.py &
python3 scripts/fetch_news_safe.py &
python3 scripts/fetch_places_safe.py &
wait
echo "✅ All fetches completed!"

# ---- 5️⃣ Patch dashboard safely ----
DASH_FILE=~/kingscross-hospitality-ai/full_fetch_dashboard.py
if [ -f "$DASH_FILE" ]; then
    sed -i "s/info.get('mode'/info[0].get('mode', 'unknown') if isinstance(info,list) and len(info)>0 else 'unknown'/g" "$DASH_FILE"
fi

# ---- 6️⃣ Run dashboard ----
if [ -f "$DASH_FILE" ]; then
    python3 "$DASH_FILE"
fi

# ---- 7️⃣ Simple UI improvements ----
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Kings Cross Dashboard</title>
<style>
body { font-family: Arial, sans-serif; background:#f4f4f4; margin:0; padding:0; }
header { background:#333; color:white; padding:1rem; text-align:center; }
section { background:white; margin:1rem auto; padding:1rem; border-radius:10px; max-width:800px; box-shadow:0 0 10px rgba(0,0,0,0.1);}
h2 { border-bottom:2px solid #eee; padding-bottom:0.5rem; }
ul { list-style:none; padding:0; }
li { margin:0.5rem 0; }
</style>
</head>
<body>
<header><h1>Kings Cross Dashboard</h1></header>
<section><h2>Transport Status</h2><pre id="transport">Loading...</pre></section>
<section><h2>Upcoming Events</h2><pre id="events">Loading...</pre></section>
<section><h2>Restaurants & Places</h2><pre id="places">Loading...</pre></section>
<section><h2>Local News</h2><pre id="news">Loading...</pre></section>
<section><h2>Weather</h2><pre id="weather">Loading...</pre></section>
</body>
</html>
EOF

echo "✅ Dashboard UI updated!"
