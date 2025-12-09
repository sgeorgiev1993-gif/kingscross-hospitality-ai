#!/usr/bin/env python3
"""
build_dashboard.py
- Reads raw JSON files in data/
- Writes data/kingscross_dashboard.json
- Appends/creates data/processed/features.csv (ML-ready)
- Writes AI insights to data/ai_insights.json (rule-based or via OpenAI if configured)
"""

import os
import json
import datetime
import csv

# Optional OpenAI call
import requests

ROOT = os.path.abspath(os.getcwd())
DATA_DIR = os.path.join(ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# Load sources (if present)
weather = load_json(os.path.join(DATA_DIR, "kingscross_weather.json")) or {}
tfl = load_json(os.path.join(DATA_DIR, "kingscross_tfl.json")) or {}
events = load_json(os.path.join(DATA_DIR, "events.json")) or []
places = load_json(os.path.join(DATA_DIR, "places_reviews.json")) or []
news = load_json(os.path.join(DATA_DIR, "news.json")) or []
history = load_json(os.path.join(DATA_DIR, "kingscross_history.json")) or []

dashboard = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "weather": weather,
    "tfl": tfl,
    "events": events,
    "places": places,
    "news": news,
    "history_count": len(history)
}

# Save dashboard
with open(os.path.join(DATA_DIR, "kingscross_dashboard.json"), "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

# Build simple features.csv row for ML
# Features: timestamp, temp, wind, tfl_issues_count, upcoming_event_count, avg_place_rating
def safe_get(d, key, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

temp = safe_get(weather, "temperature_C", None)
wind = safe_get(weather, "windspeed_kmh", None)

# count lines with non-Good Service
tfl_issues = 0
if isinstance(tfl, dict):
    for ln, val in tfl.items():
        status = val.get("status") if isinstance(val, dict) else None
        if status and status.lower() != "good service":
            tfl_issues += 1
elif isinstance(tfl, list):
    for entry in tfl:
        if entry.get("status","").lower() != "good service":
            tfl_issues += 1

event_count = len(events) if isinstance(events, list) else 0

avg_rating = None
if isinstance(places, list) and places:
    ratings = [p.get("rating") for p in places if p.get("rating") is not None]
    if ratings:
        avg_rating = sum(ratings)/len(ratings)

# create processed/features.csv header if missing
features_csv = os.path.join(PROCESSED_DIR, "features.csv")
header = ["timestamp","temp_C","wind_kmh","tfl_issues","event_count","avg_place_rating"]

row = [
    dashboard["timestamp"],
    "" if temp is None else float(temp),
    "" if wind is None else float(wind),
    tfl_issues,
    event_count,
    "" if avg_rating is None else float(avg_rating)
]

if not os.path.exists(features_csv):
    with open(features_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(row)
else:
    with open(features_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

# Create a simple AI insights summary (rule-based)
def make_rule_insights(dashboard):
    parts = []
    # transport
    if tfl_issues > 0:
        parts.append(f"There are {tfl_issues} lines with issues — expect increased footfall near alternative routes.")
    else:
        parts.append("Transport looks stable; no major line disruptions.")

    # events
    if event_count >= 3:
        parts.append(f"{event_count} upcoming events; local hospitality should prepare for busy periods.")
    elif event_count >= 1:
        parts.append(f"{event_count} event(s) scheduled — moderate impact expected.")
    else:
        parts.append("No upcoming events found — typical baseline demand.")

    # weather
    if temp is not None:
        if temp >= 25:
            parts.append("Hot weather — outdoor seating likely to be popular.")
        elif temp <= 7:
            parts.append("Cold weather — indoor seating may see higher demand.")
    # rating comment
    if avg_rating:
        parts.append(f"Average place rating is {avg_rating:.2f} — local venues have good reviews overall.")

    return " ".join(parts)

ai_insights = {
    "generated_at": dashboard["timestamp"],
    "method": "rule-based",
    "summary": make_rule_insights(dashboard)
}

# Optional: call OpenAI to improve insights if OPENAI_API_KEY env var is set
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    try:
        prompt = (
            "You are an assistant producing 3 short actionable insights for local hospitality managers "
            "based on the following facts:\n\n"
            f"{json.dumps({'tfl_issues': tfl_issues,'event_count': event_count,'temp': temp,'avg_rating': avg_rating}, ensure_ascii=False)}\n\n"
            "Return JSON with fields: insights (list of 3 short strings), urgency (Low/Medium/High)."
        )
        payload = {
            "model": "gpt-4o-mini",  # safe default; change if needed
            "messages": [{"role":"system","content":"You summarize for hospitality managers."},
                         {"role":"user","content":prompt}],
            "max_tokens": 300,
            "temperature": 0.7,
        }
        headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if resp.ok:
            j = resp.json()
            # try to extract text
            msg = j.get("choices",[{}])[0].get("message",{}).get("content")
            ai_insights = {"generated_at": dashboard["timestamp"], "method":"openai", "summary": msg}
    except Exception as e:
        # keep rule-based on failure
        ai_insights["openai_error"] = str(e)

# Save AI insights
with open(os.path.join(DATA_DIR, "ai_insights.json"), "w", encoding="utf-8") as f:
    json.dump(ai_insights, f, indent=2, ensure_ascii=False)

print("✅ Dashboard written to data/kingscross_dashboard.json")
print("✅ Features appended to data/processed/features.csv")
print("✅ AI insights written to data/ai_insights.json")
