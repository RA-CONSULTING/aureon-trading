#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
REAL-TIME DATA FEEDER — UNIFIED
═══════════════════════════════════════════════════════════════════════

Pulls live data from verified working NOAA + USGS endpoints.
NO synthetic data. NO simulation. Only what instruments measure.

Writes to: real_time_data.json (shared state file)
Updates every 60 seconds.

Verified endpoints (tested 2026-06-20):
- Kp index:     services.swpc.noaa.gov/json/planetary_k_index_1m.json
- Solar wind:   services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json
- Magnetometers: services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json
- X-ray flux:   services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json
- Alerts:       services.swpc.noaa.gov/products/alerts.json
- Forecast:     services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json
- Quakes:       earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
"""

import json, time, urllib.request, urllib.error, ssl, signal, sys, os
from datetime import datetime, timezone

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

DATA_FILE = "/root/.openclaw/workspace/real_time_data.json"
LOG_FILE = "/root/.openclaw/workspace/daemon_logs/real_data_feeder.log"

# ═══════════════════════════════════════════════════════════════════════
# VERIFIED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

ENDPOINTS = {
    "kp_index": {
        "url": "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
        "type": "json",
        "desc": "Planetary K-index, 1-minute",
    },
    "solar_wind_plasma": {
        "url": "https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json",
        "type": "json",
        "desc": "Solar wind plasma, 5-min",
    },
    "solar_wind_mag": {
        "url": "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json",
        "type": "json",
        "desc": "Solar wind magnetic field, 5-min",
    },
    "xray_flux": {
        "url": "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json",
        "type": "json",
        "desc": "GOES X-ray flux, 7-day",
    },
    "alerts": {
        "url": "https://services.swpc.noaa.gov/products/alerts.json",
        "type": "json",
        "desc": "NOAA space weather alerts",
    },
    "forecast": {
        "url": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json",
        "type": "json",
        "desc": "Kp forecast",
    },
    "scales": {
        "url": "https://services.swpc.noaa.gov/products/noaa-scales.json",
        "type": "json",
        "desc": "NOAA space weather scales",
    },
    "quakes": {
        "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
        "type": "json",
        "desc": "USGS earthquakes, last hour",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# FETCH
# ═══════════════════════════════════════════════════════════════════════

def fetch_json(url, timeout=15):
    """Fetch JSON from URL. Returns dict or None."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Aureon-DataBot/1.0; RealDataOnly)',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            data = resp.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}: {e.reason}", "_url": url}
    except urllib.error.URLError as e:
        return {"_error": f"URL Error: {e.reason}", "_url": url}
    except Exception as e:
        return {"_error": str(e), "_url": url}

# ═══════════════════════════════════════════════════════════════════════
# PROCESS
# ═══════════════════════════════════════════════════════════════════════

def extract_kp_summary(data):
    """Extract latest Kp from NOAA data."""
    if not data or "_error" in data:
        return None
    try:
        if isinstance(data, list) and len(data) > 0:
            latest = data[-1]
            if isinstance(latest, dict):
                return {
                    "timestamp": latest.get("time_tag"),
                    "kp_index": latest.get("kp_index"),
                    "estimated_kp": latest.get("estimated_kp"),
                    "kp": latest.get("kp"),
                }
            # Fallback for list format
            return {
                "timestamp": latest[0] if len(latest) > 0 else None,
                "kp": float(latest[1]) if len(latest) > 1 else None,
            }
    except Exception as e:
        return {"_error": f"Parse error: {e}"}
    return None

def extract_solar_wind_summary(data):
    """Extract latest solar wind params."""
    if not data or "_error" in data:
        return None
    try:
        if isinstance(data, list) and len(data) > 1:
            # Header row + data rows
            header = data[0]
            latest = data[-1]
            return {header[i]: latest[i] for i in range(min(len(header), len(latest)))}
    except Exception as e:
        return {"_error": f"Parse error: {e}"}
    return None

def extract_xray_summary(data):
    """Extract latest X-ray flux."""
    if not data or "_error" in data:
        return None
    try:
        if isinstance(data, list) and len(data) > 0:
            latest = data[-1]
            return {
                "time_tag": latest.get("time_tag") if isinstance(latest, dict) else None,
                "flux": latest.get("flux") if isinstance(latest, dict) else None,
                "energy": latest.get("energy") if isinstance(latest, dict) else None,
            }
    except Exception as e:
        return {"_error": f"Parse error: {e}"}
    return None

def extract_quake_summary(data):
    """Extract quake count and latest."""
    if not data or "_error" in data:
        return None
    try:
        features = data.get("features", [])
        count = len(features)
        latest = None
        if count > 0:
            f = features[0]
            props = f.get("properties", {})
            latest = {
                "mag": props.get("mag"),
                "place": props.get("place"),
                "time": props.get("time"),
            }
        return {"count": count, "latest": latest}
    except Exception as e:
        return {"_error": f"Parse error: {e}"}
    return None

# ═══════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════

def collect_all():
    """Fetch all endpoints and compile unified state."""
    results = {}
    
    for name, cfg in ENDPOINTS.items():
        raw = fetch_json(cfg["url"])
        results[name] = {
            "_raw": raw,
            "_fetched_at": datetime.now(timezone.utc).isoformat(),
            "_url": cfg["url"],
        }
    
    # Extract summaries
    summary = {
        "kp": extract_kp_summary(results["kp_index"]["_raw"]),
        "solar_wind": extract_solar_wind_summary(results["solar_wind_plasma"]["_raw"]),
        "xray": extract_xray_summary(results["xray_flux"]["_raw"]),
        "quakes": extract_quake_summary(results["quakes"]["_raw"]),
        "alerts_count": len(results["alerts"]["_raw"]) if isinstance(results["alerts"]["_raw"], list) else 0,
    }
    
    # Build unified output
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "real_time_data_feeder",
        "data_policy": "REAL_ONLY_NO_SYNTHETIC",
        "summary": summary,
        "endpoints": results,
    }
    
    return output

def write_output(data):
    """Write to shared state file."""
    # Write atomically
    tmp = DATA_FILE + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_FILE)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

# ═══════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════

running = True

def shutdown(sig, frame):
    global running
    running = False
    log("Shutting down (signal received)")

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log("═ REAL-TIME DATA FEEDER STARTED ═")
    log(f"Data file: {DATA_FILE}")
    log(f"Endpoints: {len(ENDPOINTS)}")
    
    while running:
        try:
            data = collect_all()
            write_output(data)
            
            # Quick summary log
            s = data["summary"]
            kp = s.get("kp", {})
            kp_val = kp.get("kp", "?") if kp else "?"
            quakes = s.get("quakes", {})
            quake_count = quakes.get("count", "?") if quakes else "?"
            
            log(f"Kp={kp_val} | Quakes={quake_count} | Alerts={s.get('alerts_count', '?')}")
            
        except Exception as e:
            log(f"ERROR: {e}")
        
        # Sleep with interrupt check
        for _ in range(60):
            if not running:
                break
            time.sleep(1)
    
    log("═ FEEDER STOPPED ═")
