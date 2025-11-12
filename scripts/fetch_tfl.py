import requests
import json
from pathlib import Path

BASE_URL = "https://api.tfl.gov.uk/Line/Mode"
MODES = ["tube", "overground", "dlr", "tflrail", "national-rail"]
DATA_PATH = Path("data/kingscross_tfl.json")

all_lines_status = {}

for mode in MODES:
    try:
        url = f"{BASE_URL}/{mode}/Status"
        response = requests.get(url)
        response.raise_for_status()
        lines_data = response.json()
        for line in lines_data:
            name = line.get("name")
            statuses = line.get("lineStatuses", [])
            status_text = statuses[0].get("statusSeverityDescription", "Unknown") if statuses else "Unknown"
            all_lines_status[name] = {
                "mode": mode,
                "status": status_text
            }
    except Exception as e:
        print(f"Error fetching {mode}: {e}")

DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(DATA_PATH, "w") as f:
    json.dump(all_lines_status, f, indent=2)

print(f"✅ TfL data saved to {DATA_PATH}")
