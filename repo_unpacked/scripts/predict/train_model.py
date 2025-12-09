#!/usr/bin/env python3
"""
train_model.py
- Trains a RandomForestRegressor from data/processed/features.csv
- If the CSV includes 'crowd_score' column it is used as target.
- Otherwise create pseudo-targets using a heuristic and train (bootstrap).
- Saves models/model.joblib
"""

import os, csv, math
from pathlib import Path

ROOT = os.path.abspath(os.getcwd())
PROCESSED = os.path.join(ROOT, "data", "processed")
MODEL_DIR = os.path.join(ROOT, "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

features_csv = os.path.join(PROCESSED, "features.csv")
if not os.path.exists(features_csv):
    print("No features.csv found; nothing to train on.")
    raise SystemExit(0)

import pandas as pd
df = pd.read_csv(features_csv)

# Ensure numeric columns present
for col in ["temp_C","wind_kmh","tfl_issues","event_count","avg_place_rating"]:
    if col not in df.columns:
        df[col] = 0

# If target present, use it; else create pseudo target
if "crowd_score" in df.columns:
    y = df["crowd_score"].astype(float)
else:
    # create pseudo-target with heuristic
    def pseudo(r):
        score = 50
        score += (r.get("event_count",0) * 8)
        score += (r.get("tfl_issues",0) * 5)
        t = r.get("temp_C") or 0
        if 20 <= t <= 28:
            score += 5
        if t < 5 or t > 30:
            score -= 5
        avg = r.get("avg_place_rating") or 4.0
        score += (avg - 4.0)*3
        return max(0, min(100, score))
    y = df.apply(lambda r: pseudo(r), axis=1)

X = df[["temp_C","wind_kmh","tfl_issues","event_count","avg_place_rating"]].fillna(0)

from sklearn.ensemble import RandomForestRegressor
from joblib import dump

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)
dump(model, MODEL_PATH)

print(f"Trained model saved to {MODEL_PATH}")
