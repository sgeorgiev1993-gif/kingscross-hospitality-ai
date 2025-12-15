import json, os, datetime

os.makedirs("data", exist_ok=True)

# Temporary mock data (replace APIs later)
dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "weather": {
        "temperature_C": 13.4,
        "windspeed_kmh": 9.1
    },
    "tfl": [
        {"name": "Northern", "status": "Good Service"},
        {"name": "Piccadilly", "status": "Part Closure"},
        {"name": "Victoria", "status": "Good Service"}
    ]
}

with open("data/kingscross_dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard written")