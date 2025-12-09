# scripts/fetch_weather.py
import requests
import json
from pathlib import Path
import os

WEATHER_KEY = os.getenv("OPENWEATHER_KEY")
OUTPUT_FILE = Path("data/kingscross_weather.json")

if not WEATHER_KEY:
    raise ValueError("Please set OPENWEATHER_KEY in your GitHub secrets.")

url = "https://api.openweathermap.org/data/2.5/weather"
params = {
    "q": "Kings Cross, London, UK",
    "appid": WEATHER_KEY,
    "units": "metric"
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"Error fetching weather: {e}")
    data = {}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Weather saved to {OUTPUT_FILE}")
