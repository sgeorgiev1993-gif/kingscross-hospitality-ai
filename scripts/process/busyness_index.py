#!/usr/bin/env python3
import json
import datetime
from pathlib import Path

DATA = Path("data")
PROCESSED = DATA / "processed"
PRED = DATA / "predictions"
PRED.mkdir(parents=True, exist_ok=True)

def read_json(path: Path, default):
    try:
        if not path.exists():
            return default
        txt = path.read_text(encoding="utf-8").strip()
        if not txt:
            return default
        return json.loads(txt)
    except Exception:
        return default

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def utc_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def time_factor_0_1(dt: datetime.datetime):
    """
    Simple hospitality demand curve:
    - Morning low, lunch medium, after-work peak, late night moderate.
    """
    h = dt.hour
    if 6 <= h < 11:   # breakfast
        return 0.35
    if 11 <= h < 15:  # lunch
        return 0.55
    if 15 <= h < 17:  # lull
        return 0.40
    if 17 <= h < 22:  # peak
        return 0.80
    if 22 <= h < 24:  # late
        return 0.55
    return 0.20       # overnight

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def level(score):
    if score >= 80: return "Very Busy"
    if score >= 65: return "Busy"
    if score >= 45: return "Moderate"
    if score >= 25: return "Quiet"
    return "Very Quiet"

def main():
    signals = read_json(PROCESSED / "signals.json", {})
    now = datetime.datetime.utcnow()

    comfort = (((signals.get("weather") or {}).get("comfort_score")) or 0.4)  # fallback
    transport_norm = (((signals.get("transport") or {}).get("transport_stress_norm")) or 0.2)
    events_score = (((signals.get("events") or {}).get("events_score")) or 0.0)
    t_factor = time_factor_0_1(now)

    # Weighted sum in 0..1-ish
    # events strongest, then transport, then weather, then time
    raw = (
        (events_score * 0.40) +
        (transport_norm * 0.28) +
        (comfort * 0.18) +
        (t_factor * 0.14)
    )

    score = int(round(clamp(raw, 0.0, 1.0) * 100))

    # Drivers (explainability)
    drivers = []
    ev = signals.get("events") or {}
    tr = signals.get("transport") or {}
    we = signals.get("weather") or {}

    if ev.get("large", 0) >= 1:
        drivers.append(f"{ev.get('large')} large event(s) nearby")
    elif ev.get("total_today", 0) >= 3:
        drivers.append(f"{ev.get('total_today')} events today")

    bad_lines = tr.get("bad_lines", 0)
    if bad_lines >= 3:
        drivers.append("Multiple disrupted lines")
    elif bad_lines >= 1:
        drivers.append("Some transport disruption")

    temp = we.get("temperature_C")
    if isinstance(temp, (int, float)):
        if temp >= 18 and (we.get("weather_code") or 800) == 800:
            drivers.append("Comfortable weather supports walk-ins")
        elif temp <= 6:
            drivers.append("Cold weather pushes indoor demand")

    # Ensure at least one explanation
    if not drivers:
        drivers = ["Baseline estimate (limited signals)"]

    out = {
        "timestamp": utc_now_iso(),
        "crowd_score": score,
        "level": level(score),
        "weather_impact": "High" if comfort >= 0.75 else ("Medium" if comfort >= 0.45 else "Low"),
        "transport_impact": "High" if transport_norm >= 0.65 else ("Medium" if transport_norm >= 0.30 else "Low"),
        "events_impact": "High" if events_score >= 0.55 else ("Medium" if events_score >= 0.25 else "Low"),
        "restaurant_impact": "Medium",
        "drivers": drivers,
        "note": "Prototype index (heuristic). Upgrade to ML once we have more history.",
        "method": "heuristic_v1"
    }

    write_json(PRED / "busyness_today.json", out)
    print("✅ busyness_today.json written")

if __name__ == "__main__":
    main()