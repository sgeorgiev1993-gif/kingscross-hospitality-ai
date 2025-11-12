import json
import datetime

# --- Load JSON data safely ---
def load_json_file(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {path}: {e}")
        return []

# Load data
events = load_json_file("data/events.json")
places = load_json_file("data/places.json")
tfl_status = load_json_file("data/tfl_status.json")

# --- Normalize TfL status ---
lines_status = []
for l in tfl_status:
    if isinstance(l, dict):
        name = l.get("name", "Unknown")
        status = l.get("status", "Unknown")
        lines_status.append({"name": name, "status": status})

# --- Normalize events ---
clean_events = []
for e in events:
    if isinstance(e, dict):
        clean_events.append({
            "name": e.get("name", {}).get("text", "Unknown") if isinstance(e.get("name"), dict) else e.get("name", "Unknown"),
            "start": e.get("start", {}).get("local", "") if isinstance(e.get("start"), dict) else e.get("start", ""),
            "url": e.get("url", "")
        })

# --- Normalize places ---
clean_places = []
for p in places:
    if isinstance(p, dict):
        clean_places.append({
            "name": p.get("name", "Unknown"),
            "address": p.get("address", ""),
            "type": p.get("type", ""),
            "rating": p.get("rating", None)
        })

# --- Combine into dashboard ---
dashboard = {
    "timestamp": datetime.datetime.now().isoformat(),
    "events_count": len(clean_events),
    "places_count": len(clean_places),
    "lines_status": lines_status,
    "events": clean_events,
    "places": clean_places
}

# Write unified dashboard JSON
with open("data/kingscross_dashboard.json", "w") as f:
    json.dump(dashboard, f, indent=2)

print("✅ Dashboard generated successfully!")