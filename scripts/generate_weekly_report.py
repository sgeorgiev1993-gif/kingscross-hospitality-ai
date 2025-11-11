import json, datetime, pathlib, statistics

data_dir = pathlib.Path("data")
report = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "summary": {}
}

# --- WEATHER / TEMPERATURE HISTORY ---
history_path = data_dir / "kingscross_history.json"
if history_path.exists():
    try:
        with open(history_path) as f:
            history = json.load(f)
        temps = [d["temperature_C"] for d in history if "temperature_C" in d]
        if temps:
            report["summary"]["average_temperature_C"] = round(statistics.mean(temps), 1)
            report["summary"]["latest_temperature_C"] = temps[-1]
        else:
            report["summary"]["average_temperature_C"] = None
            report["summary"]["latest_temperature_C"] = None
    except Exception as e:
        print(f"⚠️ Error reading history: {e}")
else:
    print("⚠️ No kingscross_history.json found")

# --- EVENTS DATA ---
events_path = data_dir / "events.json"
if events_path.exists():
    try:
        with open(events_path) as f:
            events = json.load(f)
        report["summary"]["events_count"] = len(events)
        report["summary"]["upcoming_event_names"] = [e.get("name") for e in events[:5]]
    except Exception as e:
        print(f"⚠️ Error reading events: {e}")
else:
    print("⚠️ No events.json found")

# --- TFL STATUS ---
tfl_path = data_dir / "tfl_status.json"
if tfl_path.exists():
    try:
        with open(tfl_path) as f:
            tfl_data = json.load(f)
        disrupted = [l["name"] for l in tfl_data if l.get("status") not in ["Good Service", ""]]
        report["summary"]["tfl_disruptions"] = disrupted
        report["summary"]["tfl_disruption_count"] = len(disrupted)
    except Exception as e:
        print(f"⚠️ Error reading TfL data: {e}")
else:
    print("⚠️ No tfl_status.json found")

# --- SAVE REPORT ---
output_path = data_dir / "weekly_report.json"
data_dir.mkdir(exist_ok=True)
with open(output_path, "w") as f:
    json.dump(report, f, indent=2)

print("✅ Weekly report generated successfully!")
print(json.dumps(report, indent=2))
