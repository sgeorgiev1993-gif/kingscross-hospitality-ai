import os
import requests
import json
import datetime
import pathlib
import matplotlib.pyplot as plt

# Ensure data folder exists
pathlib.Path("data").mkdir(exist_ok=True)

# ----------------- OpenWeather -----------------
API_KEY = os.getenv("OPENWEATHER_KEY")
if not API_KEY:
    raise Exception("❌ OPENWEATHER_KEY missing")

LAT, LON = 51.5308, -0.1238
r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric")
data = r.json()
if "main" not in data:
    raise Exception(f"❌ OpenWeather API error: {data}")

weather_info = {
    "temperature_C": data["main"]["temp"],
    "windspeed_kmh": data["wind"]["speed"],
    "weather_code": data["weather"][0]["id"]
}

with open("data/kingscross_weather.json", "w") as f:
    json.dump(weather_info, f, indent=2)

# ----------------- TfL -----------------
TFL_KEY = os.getenv("TFL_APP_KEY")
if not TFL_KEY:
    raise Exception("❌ TFL_APP_KEY missing")

# fetch all lines
tfl_r = requests.get(f"https://api.tfl.gov.uk/Line/Mode/tube,overground,dlr,tram,river-bus,coach,national-rail/Status?app_key={TFL_KEY}")
tfl_data = tfl_r.json()

kings_cross_lines = {"Northern","Piccadilly","Victoria","Circle","Hammersmith & City","Metropolitan"}
tfl_filtered = []
for line in tfl_data:
    if line.get("name") in kings_cross_lines:
        status = line["lineStatuses"][0]["statusSeverityDescription"]
        tfl_filtered.append({"name": line["name"], "mode": line["modeName"], "status": status})

with open("data/kingscross_tfl.json", "w") as f:
    json.dump(tfl_filtered, f, indent=2)

# ----------------- Eventbrite -----------------
EB_TOKEN = os.getenv("EVENTBRITE_TOKEN")
if not EB_TOKEN:
    raise Exception("❌ EVENTBRITE_TOKEN missing")

eb_url = f"https://www.eventbriteapi.com/v3/events/search/?location.address=Kings+Cross+London&token={EB_TOKEN}&sort_by=date"
eb_r = requests.get(eb_url)
try:
    eb_data = eb_r.json()
except Exception as e:
    print("⚠️ Failed to parse Eventbrite response:", e)
    eb_data = {}

events = []
for e in eb_data.get("events", []):
    try:
        events.append({
            "name": e["name"]["text"],
            "start": e["start"]["local"],
            "url": e["url"]
        })
    except Exception:
        continue

with open("data/events.json", "w") as f:
    json.dump(events, f, indent=2)

print(f"🔹 Fetched {len(events)} Eventbrite events")

# ----------------- Dashboard JSON -----------------
dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "weather": weather_info,
    "tfl": tfl_filtered
}

with open("data/kingscross_dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2)

# ----------------- History -----------------
history_path = "data/kingscross_history.json"
history = []

if os.path.exists(history_path):
    try:
        with open(history_path) as f:
            history = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Malformed history JSON detected — resetting history.")
        history = []

history.append({
    "timestamp": dashboard["timestamp"],
    "temperature_C": weather_info["temperature_C"],
    "tfl": tfl_filtered
})
history = history[-24:]
with open(history_path, "w") as f:
    json.dump(history, f, indent=2)

# ----------------- Dashboard Image -----------------
color_map = {
    "Good Service": "green",
    "Minor Delays": "orange",
    "Severe Delays": "red",
    "Part Closure": "purple",
    "Planned Closure": "gray",
    "Service Closed": "black"
}

# Current dashboard
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
timestamps = [datetime.datetime.fromisoformat(d["timestamp"].replace("Z", "")) for d in history]
temps = [d["temperature_C"] for d in history]

ax1.plot(timestamps, temps, marker="o", color="blue")
ax1.set_title("Kings Cross Temperature Trend (°C)")
ax1.set_xlabel("Time (UTC)")
ax1.set_ylabel("Temperature °C")
ax1.grid(True)

names = [line["name"] for line in tfl_filtered]
statuses = [line["status"] for line in tfl_filtered]
colors = [color_map.get(s, "gray") for s in statuses]
ax2.barh(names, [1]*len(names), color=colors)
for i, s in enumerate(statuses):
    ax2.text(0.02, i, s, va="center", ha="left", color="white", fontsize=10, fontweight="bold")
ax2.set_xlim(0, 1)
ax2.set_xticks([])
ax2.set_title("TfL Line Status at Kings Cross")

fig.text(0.5, 0.01, datetime.datetime.utcnow().strftime("Updated: %d %b %Y, %H:%M UTC"), ha="center", fontsize=9, color="gray")
plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("data/kingscross_dashboard.png")
plt.close(fig)

# Last 24h temp + TfL image
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(timestamps, temps, marker="o", color='blue', label="Temperature °C")
ax.set_title("Kings Cross Last 24h: Temp + TfL Status")
ax.set_ylabel("Temperature (°C)")
ax.set_xticks(timestamps)
ax.set_xticklabels([t.strftime("%H:%M") for t in timestamps], rotation=45)
plt.tight_layout()
plt.savefig("data/kingscross_temp_24h_tfl.png")
plt.close(fig)

print("✅ Dashboard generated successfully")
