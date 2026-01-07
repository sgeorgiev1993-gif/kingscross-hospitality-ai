import json
import os
from collections import Counter, defaultdict
import pandas as pd

DATA_DIR = "data"

ANOM_FILE = os.path.join(DATA_DIR, "anomalies.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history/kingscross_history.json")
OUT_FILE = os.path.join(DATA_DIR, "seasonal_insights_2025.json")

# ------------------------
# Load data
# ------------------------
with open(ANOM_FILE, "r", encoding="utf-8") as f:
    anomalies = json.load(f)

with open(HISTORY_FILE, "r", encoding="utf-8") as f:
    history = json.load(f)

df = pd.DataFrame(anomalies)
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

# ------------------------
# Core summaries
# ------------------------
summary = {}

summary["total_anomalies"] = len(df)
summary["date_range"] = {
    "start": df["timestamp"].min().isoformat(),
    "end": df["timestamp"].max().isoformat()
}

# ------------------------
# By type
# ------------------------
summary["by_type"] = (
    df.groupby("type")
      .size()
      .sort_values(ascending=False)
      .to_dict()
)

# ------------------------
# By severity
# ------------------------
summary["by_severity"] = (
    df.groupby("severity")
      .size()
      .sort_values(ascending=False)
      .to_dict()
)

# ------------------------
# Persistence analysis
# ------------------------
if "persistence" in df.columns:
    summary["by_persistence"] = (
        df.groupby("persistence")
          .size()
          .sort_values(ascending=False)
          .to_dict()
    )
else:
    summary["by_persistence"] = {}

# ------------------------
# Hour-of-day clustering
# ------------------------
df["hour"] = df["timestamp"].dt.hour
summary["peak_hours"] = (
    df.groupby("hour")
      .size()
      .sort_values(ascending=False)
      .head(6)
      .to_dict()
)

# ------------------------
# Drivers
# ------------------------
driver_counter = Counter()
for drivers in df["drivers"]:
    for d in drivers:
        driver_counter[d] += 1

summary["top_drivers"] = dict(driver_counter.most_common(10))

# ------------------------
# Confidence bands
# ------------------------
summary["confidence_stats"] = {
    "avg": round(df["confidence"].mean(), 3),
    "min": round(df["confidence"].min(), 3),
    "max": round(df["confidence"].max(), 3)
}

# ------------------------
# Narrative helpers (machine-readable)
# ------------------------
summary["interpretation"] = {
    "dominant_anomaly": df["type"].value_counts().idxmax(),
    "most_common_driver": driver_counter.most_common(1)[0][0],
    "most_unstable_hours": list(summary["peak_hours"].keys())[:3],
    "data_quality_note": (
        "Confidence reflects signal agreement, not ground truth. "
        "Seasonal period shows elevated volatility compared to normal weeks."
    )
}

# ------------------------
# Save
# ------------------------
with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("✅ Seasonal insights generated")
print(f"📄 Output: {OUT_FILE}")