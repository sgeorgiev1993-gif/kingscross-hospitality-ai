import requests, pandas as pd, os, datetime

KEY = os.getenv("OPENWEATHER_KEY")
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

LAT, LNG = 51.5308, -0.1238
url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LNG}&appid={KEY}&units=metric"

r = requests.get(url)
data = r.json()

df = pd.DataFrame([{
    "date": datetime.date.today(),
    "temp": data["main"]["temp"],
    "feels_like": data["main"]["feels_like"],
    "weather": data["weather"][0]["description"],
}])

filename = os.path.join(OUT_DIR, f"weather_{datetime.date.today()}.csv")
df.to_csv(filename, index=False)
print(f"✅ Saved weather data to {filename}")
