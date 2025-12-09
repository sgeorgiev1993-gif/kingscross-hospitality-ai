# scripts/fetch_tfl.py
import requests
import json
from pathlib import Path

BASE_URL = "https://api.tfl.gov.uk/Line/Mode"
MODES = ["tube", "overground", "dlr", "tflrail", "national-rail"]
OUTPUT_FILE = Path("data/kingscross_tfl.json")

all_lines_status = {}

for mode in MODES:
    try:
        url = f"{BASE_URL}/{mode}/Status"
        response = requests.get(url)
        response.raise_for_status()
        lines_data = response.json()
        
        for line in lines_data:
            name = line.get("name", "Unknown")
            status_entries = line.get("lineStatuses", [])
            if status_entries and isinstance(status_entries[0], dict):
                status_text = status_entries[0].get("statusSeverityDescription", "Unknown")
            else:
                status_text = "Unknown"
            all_lines_status[name] = {
                "mode": mode,
                "status": status_text
            }
    except Exception as e:
        print(f"Error fetching {mode}: {e}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(all_lines_status, f, indent=2)

print(f"✅ TfL & Rail status saved to {OUTPUT_FILE}")
