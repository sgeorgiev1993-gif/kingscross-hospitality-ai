import requests, pandas as pd, os, datetime

TOKEN = os.getenv("EVENTBRITE_TOKEN")
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

# King's Cross approximate coordinates
LAT, LNG = 51.5308, -0.1238
RADIUS = "3km"

url = f"https://www.eventbriteapi.com/v3/events/search/?location.latitude={LAT}&location.longitude={LNG}&location.within={RADIUS}&expand=venue"
headers = {"Authorization": f"Bearer {TOKEN}"}

resp = requests.get(url, headers=headers)
data = resp.json().get("events", [])

rows = []
for e in data:
    rows.append({
        "name": e.get("name", {}).get("text"),
        "start": e.get("start", {}).get("local"),
        "end": e.get("end", {}).get("local"),
        "url": e.get("url"),
        "venue": e.get("venue", {}).get("name"),
    })

df = pd.DataFrame(rows)
filename = os.path.join(OUT_DIR, f"eventbrite_{datetime.date.today()}.csv")
df.to_csv(filename, index=False)
print(f"✅ Saved {len(df)} events to {filename}")
