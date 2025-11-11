import os, requests, json, datetime, pathlib, matplotlib.pyplot as plt, pandas as pd

# Create data folder if missing
pathlib.Path("data").mkdir(exist_ok=True)

# --- WEATHER DATA ---
API_KEY = os.getenv("OPENWEATHER_KEY")
LAT, LON = 51.5308, -0.1238
r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric")
data = r.json()
weather_info = {"temperature_C": data["main"]["temp"], "windspeed_kmh": data["wind"]["speed"], "weather_code": data["weather"][0]["id"]}

# --- TFL DATA (all rail modes) ---
tfl_key = os.getenv("TFL_APP_KEY")
modes = ["tube","overground","dlr","national-rail","tram","river-bus"]
tfl_data = []
for mode in modes:
    r = requests.get(f"https://api.tfl.gov.uk/Line/Mode/{mode}/Status?app_key={tfl_key}")
    try:
        tfl_data += r.json()
    except Exception as e:
        print(f"⚠️ Failed fetching {mode}: {e}")

kings_cross_lines = ["Northern","Piccadilly","Victoria","Circle","Hammersmith & City","Metropolitan","Overground","DLR","Tram"]
tfl_filtered = [{"name": l["name"], "mode": l["modeName"], "status": l["lineStatuses"][0]["statusSeverityDescription"]} for l in tfl_data if l["name"] in kings_cross_lines]

with open("data/kingscross_tfl.json","w") as f:
    json.dump(tfl_filtered, f, indent=2)

# --- EVENTBRITE EVENTS ---
EB_TOKEN = os.getenv("EVENTBRITE_TOKEN")
eb_url = f"https://www.eventbriteapi.com/v3/events/search/?location.address=Kings+Cross+London&token={EB_TOKEN}&sort_by=date"
eb_r = requests.get(eb_url)
data = eb_r.json()
events = []
for e in data.get("events", []):
    if isinstance(e.get("name"), dict) and "text" in e["name"]:
        events.append({
            "name": e["name"]["text"],
            "start": e.get("start", {}).get("local", ""),
            "url": e.get("url", "")
        })
with open("data/events.json","w") as f:
    json.dump(events, f, indent=2)

# --- DASHBOARD JSON ---
dashboard = {"timestamp": datetime.datetime.utcnow().isoformat()+"Z", "weather": weather_info, "tfl": tfl_filtered}
with open("data/kingscross_dashboard.json","w") as f:
    json.dump(dashboard, f, indent=2)

# --- HISTORY FOR LAST 24H ---
history_path = "data/kingscross_history.json"
history = []
if os.path.exists(history_path):
    try:
        with open(history_path) as f:
            history = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Malformed history JSON detected — resetting history.")

history.append({"timestamp": dashboard["timestamp"], "temperature_C": dashboard["weather"]["temperature_C"], "tfl": dashboard["tfl"]})
history = history[-24:]
with open(history_path, "w") as f:
    json.dump(history, f, indent=2)

# --- DASHBOARD IMAGE ---
color_map = {"Good Service":"green","Minor Delays":"orange","Severe Delays":"red","Part Closure":"purple","Planned Closure":"gray","Service Closed":"black"}
fig, (ax1, ax2) = plt.subplots(1,2,figsize=(12,5))
timestamps = [datetime.datetime.fromisoformat(d["timestamp"].replace("Z","")) for d in history]
temps = [d["temperature_C"] for d in history]
ax1.plot(timestamps, temps, marker="o", color="blue")
ax1.set_title("Kings Cross Temperature Trend (°C)")
ax1.set_xlabel("Time (UTC)"); ax1.set_ylabel("Temperature °C"); ax1.grid(True)

names = [line["name"] for line in tfl_filtered]
statuses = [line["status"] for line in tfl_filtered]
colors = [color_map.get(s,"gray") for s in statuses]
ax2.barh(names,[1]*len(names),color=colors)
for i,s in enumerate(statuses): ax2.text(0.02,i,s,va="center",ha="left",color="white",fontsize=10,fontweight="bold")
ax2.set_xlim(0,1); ax2.set_xticks([]); ax2.set_title("TfL Line Status at Kings Cross")
fig.text(0.5,0.01,datetime.datetime.utcnow().strftime("Updated: %d %b %Y, %H:%M UTC"),ha="center",fontsize=9,color="gray")
plt.tight_layout(rect=[0,0.03,1,1])
plt.savefig("data/kingscross_dashboard.png")
plt.close(fig)

# --- LAST 24H TEMP + TFLS IMAGE ---
fig, ax = plt.subplots(figsize=(10,6))
ax.plot(timestamps, temps, marker="o", color='blue', label="Temperature °C")
ax.set_title("Kings Cross Last 24h: Temp + TfL Status")
ax.set_ylabel("Temperature (°C)")
ax.set_xticks(timestamps)
ax.set_xticklabels([t.strftime("%H:%M") for t in timestamps], rotation=45)
plt.tight_layout()
plt.savefig("data/kingscross_temp_24h_tfl.png")
plt.close(fig)
