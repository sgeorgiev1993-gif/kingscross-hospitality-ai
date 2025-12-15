#!/usr/bin/env python3
import json
import os
import math
import datetime
from pathlib import Path

DATA = Path("data")
PROCESSED = DATA / "processed"
HISTORY = DATA / "history"

PROCESSED.mkdir(parents=True, exist_ok=True)
HISTORY.mkdir(parents=True, exist_ok=True)

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

def parse_iso(ts: str):
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z",""))
    except Exception:
        return None

# --- Weather fallback ---
def get_weather():
    w = read_json(DATA / "kingscross_weather.json", {})
    if isinstance(w, dict) and w.get("temperature_C") is not None:
        return w

    # fallback: weather_log.json (list)
    log = read_json(DATA / "weather_log.json", [])
    if isinstance(log, list) and log:
        last = log[-1]
        if isinstance(last, dict) and last.get("temperature_C") is not None:
            return last

    return {}

def weather_comfort_score(temp_c: float | None, weather_code: int | None):
    """
    Rough comfort proxy 0..1.
    Good around ~18C, worse if too cold/hot.
    Weather code (OpenWeather) rough penalty for rain/snow.
    """
    if temp_c is None or (isinstance(temp_c, float) and math.isnan(temp_c)):
        return None

    # temp score: peak at 18C, falls off with distance
    dist = abs(temp_c - 18.0)
    temp_score = max(0.0, 1.0 - (dist / 18.0))  # dist 0 -> 1, dist 18 -> 0

    penalty = 0.0
    if weather_code is not None:
        # 2xx thunderstorm, 3xx drizzle, 5xx rain, 6xx snow
        if 200 <= weather_code < 300:
            penalty = 0.35
        elif 300 <= weather_code < 400:
            penalty = 0.18
        elif 500 <= weather_code < 600:
            penalty = 0.30
        elif 600 <= weather_code < 700:
            penalty = 0.40
        elif 700 <= weather_code < 800:
            penalty = 0.10  # mist/haze
        else:
            penalty = 0.0

    return max(0.0, min(1.0, temp_score - penalty))

# --- Transport stress ---
STATUS_POINTS = {
    "Good Service": 0,
    "Minor Delays": 15,
    "Severe Delays": 40,
    "Part Closure": 55,
    "Planned Closure": 60,
    "Service Closed": 70,
    "Suspended": 70,
    "Reduced Service": 20,
    "Special Service": 20,
}

def get_transport():
    # Prefer dashboard tfl if present
    dash = read_json(DATA / "kingscross_dashboard.json", {})
    tfl = None
    if isinstance(dash, dict) and dash.get("tfl") is not None:
        tfl = dash.get("tfl")

    if tfl is None:
        # kingscross_tfl.json might be dict {line:{mode,status}} or list
        tfl = read_json(DATA / "kingscross_tfl.json", None)

    # tfl_status.json is another possible source
    if tfl is None:
        ts = read_json(DATA / "tfl_status.json", {})
        if isinstance(ts, dict):
            tfl = ts.get("status")

    lines = []
    if isinstance(tfl, list):
        for x in tfl:
            if isinstance(x, dict):
                lines.append({
                    "name": x.get("name", "Unknown"),
                    "mode": x.get("mode", "unknown"),
                    "status": x.get("status", "Unknown")
                })
    elif isinstance(tfl, dict):
        for name, obj in tfl.items():
            if isinstance(obj, dict):
                lines.append({
                    "name": name,
                    "mode": obj.get("mode", "unknown"),
                    "status": obj.get("status", "Unknown")
                })

    # stress: average points, plus count of bad lines
    pts = []
    bad_count = 0
    for l in lines:
        s = l.get("status") or "Unknown"
        p = STATUS_POINTS.get(s, 15)  # unknown -> mild penalty
        pts.append(p)
        if p >= 40:
            bad_count += 1

    if pts:
        avg = sum(pts) / len(pts)
    else:
        avg = None

    return {
        "lines": lines,
        "transport_stress": avg,      # 0..70-ish
        "bad_lines": bad_count,
        "line_count": len(lines)
    }

# --- Events intelligence ---
LARGE_KEYWORDS = [
    "concert", "festival", "sold out", "arena", "o2", "headline", "premiere"
]

def classify_event_size(name: str):
    n = (name or "").lower()
    for kw in LARGE_KEYWORDS:
        if kw in n:
            return "large"
    # basic heuristic: long names / “tour” / “live” often bigger
    if "live" in n or "tour" in n:
        return "medium"
    return "small"

def get_events():
    events = read_json(DATA / "events.json", [])
    if not isinstance(events, list):
        events = []

    now = datetime.datetime.utcnow()
    today = now.date()
    evening_cut = datetime.time(17, 0)

    total_today = 0
    evening = 0
    large = 0

    cleaned = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        name = ev.get("name") or ev.get("title") or "Event"
        start = ev.get("start") or ev.get("start_local") or ev.get("local") or ""
        dt = parse_iso(start) if isinstance(start, str) else None

        size = classify_event_size(name)
        if size == "large":
            large += 1

        if dt and dt.date() == today:
            total_today += 1
            if dt.time() >= evening_cut:
                evening += 1

        cleaned.append({
            "name": name,
            "start": start,
            "url": ev.get("url"),
            "size": size
        })

    return {
        "events": cleaned,
        "total_today": total_today,
        "evening": evening,
        "large": large
    }

def clamp01(x):
    return max(0.0, min(1.0, x))

def main():
    ts = utc_now_iso()

    weather = get_weather()
    temp = weather.get("temperature_C")
    wind = weather.get("windspeed_kmh")
    wcode = weather.get("weather_code")

    comfort = weather_comfort_score(temp, wcode)

    transport = get_transport()
    events = get_events()

    # Normalize transport stress to 0..1-ish for downstream use
    t_stress = transport.get("transport_stress")
    t_norm = None
    if isinstance(t_stress, (int, float)):
        # 0->0, 60->1
        t_norm = clamp01(t_stress / 60.0)

    # simple events score 0..1
    # large events weigh more
    e_score = clamp01((events["total_today"] * 0.08) + (events["large"] * 0.18))

    signals = {
        "timestamp": ts,
        "weather": {
            "temperature_C": temp,
            "windspeed_kmh": wind,
            "weather_code": wcode,
            "comfort_score": comfort
        },
        "transport": {
            "transport_stress": t_stress,
            "transport_stress_norm": t_norm,
            "bad_lines": transport.get("bad_lines"),
            "line_count": transport.get("line_count")
        },
        "events": {
            "total_today": events["total_today"],
            "evening": events["evening"],
            "large": events["large"],
            "events_score": e_score
        }
    }

    write_json(PROCESSED / "signals.json", signals)

    # --- append to history (json list) ---
    hist_path = HISTORY / "signals_history.json"
    hist = read_json(hist_path, [])
    if not isinstance(hist, list):
        hist = []

    hist.append(signals)

    # keep last 14 days if hourly ~ 336 points
    if len(hist) > 336:
        hist = hist[-336:]

    write_json(hist_path, hist)

    # Optional: overwrite kingscross_weather.json if empty so frontend always has something
    if not isinstance(read_json(DATA / "kingscross_weather.json", {}), dict) or not (read_json(DATA / "kingscross_weather.json", {}).get("temperature_C") is not None):
        if temp is not None:
            write_json(DATA / "kingscross_weather.json", {
                "temperature_C": temp,
                "windspeed_kmh": wind,
                "weather_code": wcode
            })

    print("✅ signals.json written, history updated")

if __name__ == "__main__":
    main()