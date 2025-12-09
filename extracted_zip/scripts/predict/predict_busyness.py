#!/usr/bin/env python3
"""
predict_busyness.py
- Use models/model.joblib if present to predict 'crowd_score'
- Otherwise use a simple heuristic
- Outputs data/predictions/busyness_today.json
"""

import os, json, datetime
from pathlib import Path

ROOT = os.path.abspath(os.getcwd())
DATA_DIR = os.path.join(ROOT, "data")
PROCESSED = os.path.join(DATA_DIR, "processed")
MODEL_PATH = os.path.join("models", "model.joblib")
OUT_DIR = os.path.join(DATA_DIR, "predictions")
os.makedirs(OUT_DIR, exist_ok=True)

# Load latest features row
features_file = os.path.join(PROCESSED, "features.csv")
latest = None
if os.path.exists(features_file):
    import csv
    with open(features_file, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        if reader:
            latest = reader[-1]

# Heuristic baseline function
def heuristic_predict(latest_row):
    # default base
    base = 50
    if not latest_row:
        return base
    try:
        temp = float(latest_row.get("temp_C") or 0)
        tfl_issues = int(latest_row.get("tfl_issues") or 0)
        event_count = int(latest_row.get("event_count") or 0)
        avg_rating = float(latest_row.get("avg_place_rating") or 4.0)
    except Exception:
        temp=0; tfl_issues=0; event_count=0; avg_rating=4.0
    score = base
    score += (event_count * 8)            # events boost
    score += (tfl_issues * 5)             # disruption causes crowding elsewhere
    # weather: comfortable temps make people go out; extremes reduce
    if temp >= 20 and temp <= 28:
        score += 5
    if temp < 5 or temp > 30:
        score -= 5
    # good ratings increase linger time slightly
    score += (avg_rating - 4.0) * 3
    # clamp 0-100
    score = max(0, min(100, score))
    return round(score, 1)

prediction = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "crowd_score": None,
    "method": None,
    "note": ""
}

# Try ML model
if os.path.exists(MODEL_PATH):
    try:
        import joblib
        import pandas as pd
        model = joblib.load(MODEL_PATH)
        # create a DataFrame with expected columns
        # We'll try to match header order from features.csv
        df = None
        if latest:
            df = pd.DataFrame([{
                "temp_C": float(latest.get("temp_C") or 0),
                "wind_kmh": float(latest.get("wind_kmh") or 0),
                "tfl_issues": int(latest.get("tfl_issues") or 0),
                "event_count": int(latest.get("event_count") or 0),
                "avg_place_rating": float(latest.get("avg_place_rating") or 4.0)
            }])
        if df is not None:
            pred = model.predict(df)[0]
            prediction["crowd_score"] = float(round(pred,1))
            prediction["method"] = "model"
        else:
            prediction["crowd_score"] = heuristic_predict(latest)
            prediction["method"] = "heuristic"
    except Exception as e:
        prediction["method"] = "heuristic_fallback"
        prediction["note"] = f"model error: {e}"
        prediction["crowd_score"] = heuristic_predict(latest)
else:
    # no model: heuristic
    prediction["method"] = "heuristic"
    prediction["crowd_score"] = heuristic_predict(latest)

# Save prediction
out_file = os.path.join(OUT_DIR, "busyness_today.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(prediction, f, indent=2, ensure_ascii=False)

print(f"✅ Prediction written to {out_file}")
