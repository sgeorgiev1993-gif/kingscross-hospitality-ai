#!/usr/bin/env python3
"""
Train a tiny regression model from history and generate a rush-hour aware forecast with confidence.

Inputs (any one is enough):
- data/history/signals_history.json   (preferred)
- data/kingscross_history.json
- data/weather_log.json (fallback – will generate weak targets)

Outputs:
- data/forecast.json  (always)
- data/models/busyness_model.json (only if enough samples)
"""

from __future__ import annotations
import os, json, math, datetime, statistics
from typing import List, Dict, Any, Tuple

DATA_DIR = "data"
HIST_CANDIDATES = [
    os.path.join(DATA_DIR, "history", "signals_history.json"),
    os.path.join(DATA_DIR, "kingscross_history.json"),
    os.path.join(DATA_DIR, "weather_log.json"),
]
DASHBOARD_FILE = os.path.join(DATA_DIR, "kingscross_dashboard.json")
OUT_FORECAST = os.path.join(DATA_DIR, "forecast.json")
OUT_MODEL = os.path.join(DATA_DIR, "models", "busyness_model.json")

# Kings Cross approx
LAT, LON = 51.5308, -0.1238

def _read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _safe_iso_to_dt(s: str) -> datetime.datetime:
    # Accept "Z" or "+00:00"
    if not s:
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.datetime.fromisoformat(s)
    except Exception:
        dt = datetime.datetime.utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)

def _rush_hour(dt_utc: datetime.datetime) -> bool:
    # London rush hours approx in UTC (works OK in winter; good enough as heuristic)
    h = dt_utc.hour
    # Morning 7-10, Evening 16-19
    return (7 <= h <= 10) or (16 <= h <= 19)

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _transport_stress_from_dashboard(dash: Dict[str, Any]) -> int:
    bad = {"Part Closure", "Severe Delays", "Reduced Service", "Planned Closure"}
    tfl = dash.get("tfl", [])
    if isinstance(tfl, dict):
        # Sometimes you have dict of lines
        vals = []
        for k, v in tfl.items():
            if isinstance(v, dict):
                vals.append(v.get("status", ""))
        return sum(1 for s in vals if s in bad) * 8
    if isinstance(tfl, list):
        return sum(1 for l in tfl if (l.get("status") in bad)) * 8
    return 0

def _events_count_from_dashboard(dash: Dict[str, Any]) -> int:
    ev = dash.get("events", [])
    return len(ev) if isinstance(ev, list) else 0

def _weather_from_dashboard(dash: Dict[str, Any]) -> Tuple[float, float]:
    w = dash.get("weather", {}) if isinstance(dash.get("weather", {}), dict) else {}
    temp = w.get("temperature_C")
    wind = w.get("windspeed_kmh")
    try:
        temp = float(temp)
    except Exception:
        temp = None
    try:
        wind = float(wind)
    except Exception:
        wind = None
    return (temp if temp is not None else 10.0, wind if wind is not None else 10.0)

def _load_history() -> List[Dict[str, Any]]:
    raw = None
    used = None
    for p in HIST_CANDIDATES:
        raw = _read_json(p)
        if raw is not None:
            used = p
            break

    if raw is None:
        return []

    # Normalize to a list of dicts with at least timestamp
    hist: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        # weather_log.json is list of dicts with timestamp/temp/wind/weather_code
        for item in raw:
            if isinstance(item, dict):
                hist.append(item)
    elif isinstance(raw, dict):
        # Unexpected dict
        hist = [raw]
    else:
        hist = []

    # Clean merge-conflict markers if present in kingscross_history.json (rare but you showed it)
    cleaned: List[Dict[str, Any]] = []
    for item in hist:
        if not isinstance(item, dict):
            continue
        ts = item.get("timestamp")
        if isinstance(ts, str) and ("<<<<<<" in ts or ">>>>>>" in ts or "=======" in ts):
            continue
        cleaned.append(item)

    print(f"Loaded history: {len(cleaned)} rows (source: {used})")
    return cleaned

def _make_row_features(dt: datetime.datetime, temp: float, wind: float, transport_stress: float, events_count: float) -> List[float]:
    # Time cyclic features
    hour = dt.hour + dt.minute/60.0
    dow = dt.weekday()  # Mon=0
    hour_sin = math.sin(2*math.pi*hour/24.0)
    hour_cos = math.cos(2*math.pi*hour/24.0)
    dow_sin = math.sin(2*math.pi*dow/7.0)
    dow_cos = math.cos(2*math.pi*dow/7.0)
    rush = 1.0 if _rush_hour(dt) else 0.0

    # Scale some signals lightly
    return [
        1.0,                # bias
        hour_sin, hour_cos,
        dow_sin, dow_cos,
        rush,
        (temp - 10.0) / 10.0,
        (wind - 10.0) / 10.0,
        transport_stress / 40.0,
        events_count / 10.0,
    ]

def _normal_eq_ridge(X: List[List[float]], y: List[float], lam: float = 0.2) -> List[float]:
    # Solve (X^T X + lam I) w = X^T y
    n = len(X)
    m = len(X[0])
    # Build XtX and Xty
    XtX = [[0.0]*m for _ in range(m)]
    Xty = [0.0]*m
    for i in range(n):
        xi = X[i]
        yi = y[i]
        for a in range(m):
            Xty[a] += xi[a]*yi
            for b in range(m):
                XtX[a][b] += xi[a]*xi[b]

    for j in range(m):
        XtX[j][j] += lam

    # Gaussian elimination
    A = [row[:] + [Xty[i]] for i, row in enumerate(XtX)]
    for col in range(m):
        # pivot
        pivot = col
        for r in range(col+1, m):
            if abs(A[r][col]) > abs(A[pivot][col]):
                pivot = r
        A[col], A[pivot] = A[pivot], A[col]
        if abs(A[col][col]) < 1e-9:
            continue
        # normalize
        div = A[col][col]
        for k in range(col, m+1):
            A[col][k] /= div
        # eliminate
        for r in range(m):
            if r == col:
                continue
            factor = A[r][col]
            if abs(factor) < 1e-12:
                continue
            for k in range(col, m+1):
                A[r][k] -= factor * A[col][k]

    w = [A[i][m] for i in range(m)]
    return w

def _predict(w: List[float], x: List[float]) -> float:
    return sum(wi*xi for wi, xi in zip(w, x))

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    dash = _read_json(DASHBOARD_FILE) or {}
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    temp_now, wind_now = _weather_from_dashboard(dash)
    transport_stress_now = float(_transport_stress_from_dashboard(dash))
    events_count_now = float(_events_count_from_dashboard(dash))

    history = _load_history()

    # Build training set
    X: List[List[float]] = []
    y: List[float] = []

    # If history already contains "busyness", use it. Otherwise synthesize a weak target.
    for item in history:
        if not isinstance(item, dict):
            continue
        dt = _safe_iso_to_dt(str(item.get("timestamp", "")))

        # Try to get signals from history row; else fallback to "now"
        t = item.get("temperature") or item.get("temperature_C")
        w = item.get("wind") or item.get("windspeed_kmh")
        try:
            t = float(t)
        except Exception:
            t = temp_now
        try:
            w = float(w)
        except Exception:
            w = wind_now

        # transport stress in some history formats may be embedded as list of tfl statuses
        ts = item.get("transport_stress")
        if ts is None and isinstance(item.get("tfl"), list):
            bad = {"Part Closure", "Severe Delays", "Reduced Service", "Planned Closure"}
            ts = sum(1 for l in item["tfl"] if isinstance(l, dict) and l.get("status") in bad) * 8
        try:
            ts = float(ts) if ts is not None else transport_stress_now
        except Exception:
            ts = transport_stress_now

        ec = item.get("events_count")
        try:
            ec = float(ec) if ec is not None else events_count_now
        except Exception:
            ec = events_count_now

        target = item.get("busyness")
        if target is None:
            # weak synthetic target if you only have weather_log
            base = 45.0
            base += 10.0 if t > 15 else -3.0 if t < 6 else 0.0
            base += 6.0 if _rush_hour(dt) else 0.0
            base += ts
            base += ec * 6.0
            target = _clamp(base, 0, 100)

        try:
            target = float(target)
        except Exception:
            continue

        X.append(_make_row_features(dt, t, w, ts, ec))
        y.append(target)

    # Train if enough data; else fallback forecast
    os.makedirs(os.path.dirname(OUT_MODEL), exist_ok=True)

    trained = False
    w = None
    if len(y) >= 24:
        w = _normal_eq_ridge(X, y, lam=0.35)
        trained = True
        # Residual std for confidence band
        preds = [_predict(w, X[i]) for i in range(len(y))]
        resid = [y[i] - preds[i] for i in range(len(y))]
        resid_std = statistics.pstdev(resid) if len(resid) > 1 else 10.0
        resid_std = float(_clamp(resid_std, 6.0, 18.0))
        model = {
            "trained_at": now.isoformat().replace("+00:00", "Z"),
            "n_samples": len(y),
            "weights": w,
            "resid_std": resid_std,
            "feature_order": [
                "bias","hour_sin","hour_cos","dow_sin","dow_cos","rush",
                "temp_scaled","wind_scaled","transport_scaled","events_scaled"
            ],
        }
        with open(OUT_MODEL, "w", encoding="utf-8") as f:
            json.dump(model, f, indent=2)
        print(f"✅ ML model saved: {OUT_MODEL} (n={len(y)})")
    else:
        resid_std = 12.0
        print(f"⚠️ Not enough samples for ML (have {len(y)}). Using baseline forecast.")

    # Confidence string
    if len(y) >= 7*24:
        conf_str = "high"
    elif len(y) >= 24:
        conf_str = "medium"
    else:
        conf_str = "low"

    # Build forecast (next 12h)
    forecast = []
    for i in range(1, 13):
        dt = (now + datetime.timedelta(hours=i))
        rush = _rush_hour(dt)

        # rush hour uplift heuristic (even for ML)
        rush_uplift = 12.0 if rush else 0.0

        if trained and w is not None:
            xrow = _make_row_features(dt, temp_now, wind_now, transport_stress_now, events_count_now)
            base = _predict(w, xrow)
        else:
            base = 48.0

        bus = _clamp(base + rush_uplift, 0, 100)

        # band width: std + extra if rush hour or low confidence
        band = resid_std
        if conf_str == "low":
            band += 6.0
        if rush:
            band += 4.0

        low = int(_clamp(bus - band, 0, 100))
        high = int(_clamp(bus + band, 0, 100))

        forecast.append({
            "time": dt.isoformat(),
            "busyness": int(round(bus)),
            "low": low,
            "high": high,
            "confidence": conf_str,
            "rush_hour": bool(rush),
        })

    with open(OUT_FORECAST, "w", encoding="utf-8") as f:
        json.dump(forecast, f, indent=2)

    print(f"✅ forecast.json written: {OUT_FORECAST}")

if __name__ == "__main__":
    main()
