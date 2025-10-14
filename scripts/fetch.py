import requests, pandas as pd, os, datetime

APP_ID = os.getenv("TFL_APP_ID")
APP_KEY = os.getenv("TFL_APP_KEY")
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

# King's Cross St. Pancras Station (ID)
STOP_POINT = "940GZZLUKSX"

url = f"https://api.tfl.gov.uk/StopPoint/{STOP_POINT}/Arrivals?app_id={APP_ID}&app_key={APP_KEY}"

r = requests.get(url)
data = r.json()

rows = []
for item in data:
    rows.append({
        "line": item.get("lineName"),
        "platform": item.get("platformName"),
        "timeToStation_sec": item.get("timeToStation"),
        "destination": item.get("destinationName")
    })

df = pd.DataFrame(rows)
filename = os.path.join(OUT_DIR, f"tfl_{datetime.date.today()}.csv")
df.to_csv(filename, index=False)
print(f"✅ Saved TfL arrivals data to {filename}")
