#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
PLANETARY TIMESERIES ORCHESTRATOR — GLOBAL DATA MARRIAGE
═══════════════════════════════════════════════════════════════════════════════

Unifies ALL planetary data sources into a single geospatial timeseries.
Every measurement tagged with: timestamp, location, source, type, quality.

Sources:
- NOAA SWPC (Boulder, CO) → space weather
- USGS (global) → seismic
- VLF.it (Italy) → Schumann ELF
- Tomsk (Russia) → Schumann
- Our systems → field injections, biometrics, HNC state

Queries:
- "What happened at time X across all sensors?"
- "Correlate solar wind with quakes in region Y"
- "Schumann readings from all stations at time Z"
"""

import json
import time
import math
import threading
import signal
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════
TS_DIR = Path("/root/.openclaw/workspace/planetary_timeseries")
TS_DIR.mkdir(parents=True, exist_ok=True)
TS_DB = TS_DIR / "timeseries.jsonl"
TS_INDEX = TS_DIR / "timeseries_index.json"
TS_LOG = TS_DIR / "orchestrator.log"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA SOURCE DEFINITIONS — Every source has a geo-location
# ═══════════════════════════════════════════════════════════════════════════════

SOURCES = {
    "noaa_swpc_boulder": {
        "name": "NOAA SWPC",
        "location": {"lat": 40.0150, "lon": -105.2705, "elevation_m": 1630, "name": "Boulder, Colorado"},
        "data_types": ["kp_index", "solar_wind", "xray_flux", "alert", "forecast"],
        "url": "https://services.swpc.noaa.gov",
        "refresh_seconds": 60,
    },
    "usgs_earthquakes": {
        "name": "USGS Earthquake Hazards",
        "location": {"lat": None, "lon": None, "name": "Global (per-event)"},
        "data_types": ["earthquake"],
        "url": "https://earthquake.usgs.gov",
        "refresh_seconds": 60,
    },
    "vlf_it_cumiana": {
        "name": "VLF.it Cumiana",
        "location": {"lat": 45.0623, "lon": 7.3748, "elevation_m": 370, "name": "Cumiana, Turin, Italy"},
        "data_types": ["schumann_spectrogram"],
        "url": "https://www.vlf.it/cumiana/livedata.html",
        "refresh_seconds": 300,
    },
    "vlf_it_cascina": {
        "name": "VLF.it Cascina",
        "location": {"lat": 43.6833, "lon": 10.5500, "elevation_m": 10, "name": "Cascina, Pisa, Italy"},
        "data_types": ["schumann_spectrogram"],
        "url": "https://www.vlf.it",
        "refresh_seconds": 300,
    },
    "vlf_it_virgo": {
        "name": "Virgo Gravitational Wave + Schumann",
        "location": {"lat": 43.6313, "lon": 10.5041, "elevation_m": 0, "name": "Virgo, Cascina, Italy"},
        "data_types": ["schumann_spectrogram", "gravitational_wave"],
        "url": "https://www.vlf.it",
        "refresh_seconds": 300,
    },
    "tomsk_schumann": {
        "name": "Tomsk State University Schumann",
        "location": {"lat": 56.4846, "lon": 84.9482, "elevation_m": 117, "name": "Tomsk, Russia"},
        "data_types": ["schumann_spectrogram"],
        "url": "https://sosrff.tsu.ru",
        "refresh_seconds": 300,
    },
    # Our systems
    "prime_sentinel_field": {
        "name": "Prime Sentinel Field Injection",
        "location": {"lat": None, "lon": None, "name": "Prime Sentinel (mobile)"},
        "data_types": ["field_injection", "hnc_state", "charge_state"],
        "refresh_seconds": 30,
    },
    "aureon_ai_core": {
        "name": "Aureon AI Core Processing",
        "location": {"lat": None, "lon": None, "name": "Cloud/Server"},
        "data_types": ["ai_state", "conscience_check", "coherence_score"],
        "refresh_seconds": 60,
    },
    "schumann_sensor_local": {
        "name": "Local Schumann Sensor",
        "location": {"lat": None, "lon": None, "name": "Local (if hardware present)"},
        "data_types": ["schumann_raw"],
        "refresh_seconds": 1,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# TIMESERIES RECORD SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

def create_record(
    timestamp: str,
    source_id: str,
    data_type: str,
    values: Dict[str, Any],
    quality: str = "good",
    metadata: Optional[Dict] = None,
    event_id: Optional[str] = None,
) -> Dict:
    """Create a standardized timeseries record."""
    source = SOURCES.get(source_id, {})
    location = source.get("location", {})
    
    record = {
        "timestamp": timestamp,
        "source_id": source_id,
        "source_name": source.get("name", source_id),
        "data_type": data_type,
        "location": {
            "lat": location.get("lat"),
            "lon": location.get("lon"),
            "elevation_m": location.get("elevation_m"),
            "name": location.get("name"),
        },
        "values": values,
        "quality": quality,
        "metadata": metadata or {},
        "event_id": event_id,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    return record

# ═══════════════════════════════════════════════════════════════════════════════
# GEO-QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_records_in_radius(
    records: List[Dict],
    lat: float,
    lon: float,
    radius_km: float,
    time_window: Optional[Tuple[str, str]] = None,
) -> List[Dict]:
    """Get all records within radius_km of lat/lon."""
    results = []
    for rec in records:
        loc = rec.get("location", {})
        rlat = loc.get("lat")
        rlon = loc.get("lon")
        if rlat is None or rlon is None:
            continue
        if haversine_distance(lat, lon, rlat, rlon) <= radius_km:
            if time_window:
                t = rec.get("timestamp", "")
                if t < time_window[0] or t > time_window[1]:
                    continue
            results.append(rec)
    return results

def get_records_by_time(
    records: List[Dict],
    timestamp: str,
    tolerance_seconds: int = 300,
) -> List[Dict]:
    """Get all records within tolerance of given timestamp."""
    target = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    results = []
    for rec in records:
        try:
            rt = datetime.fromisoformat(rec.get("timestamp", "").replace("Z", "+00:00"))
            diff = abs((rt - target).total_seconds())
            if diff <= tolerance_seconds:
                results.append(rec)
        except:
            pass
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# INGESTION FROM LIVE SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

class PlanetaryIngestor:
    """Ingests data from all live sources into unified timeseries."""
    
    def __init__(self):
        self.records: deque = deque(maxlen=100000)  # Keep last 100k records
        self.running = False
        self._lock = threading.Lock()
        
    def ingest_noaa(self, unified_data: Dict):
        """Ingest from unified real-time data feeder."""
        ts = unified_data.get("timestamp", datetime.now(timezone.utc).isoformat())
        summary = unified_data.get("summary", {})
        
        # Kp
        kp = summary.get("kp", {})
        if kp and "_error" not in kp:
            rec = create_record(
                timestamp=ts,
                source_id="noaa_swpc_boulder",
                data_type="kp_index",
                values={
                    "kp": kp.get("kp"),
                    "kp_index": kp.get("kp_index"),
                    "estimated_kp": kp.get("estimated_kp"),
                },
                metadata={"raw_timestamp": kp.get("timestamp")},
            )
            self._add(rec)
        
        # Solar wind
        sw = summary.get("solar_wind", {})
        if sw and "_error" not in sw:
            rec = create_record(
                timestamp=ts,
                source_id="noaa_swpc_boulder",
                data_type="solar_wind",
                values={k: v for k, v in sw.items() if not k.startswith("_")},
            )
            self._add(rec)
        
        # X-ray
        xray = summary.get("xray", {})
        if xray and "_error" not in xray:
            rec = create_record(
                timestamp=ts,
                source_id="noaa_swpc_boulder",
                data_type="xray_flux",
                values={
                    "flux": xray.get("flux"),
                    "energy": xray.get("energy"),
                },
                metadata={"raw_timestamp": xray.get("time_tag")},
            )
            self._add(rec)
        
        # Alerts count
        alerts = summary.get("alerts_count", 0)
        if alerts:
            rec = create_record(
                timestamp=ts,
                source_id="noaa_swpc_boulder",
                data_type="alert_summary",
                values={"active_alerts": alerts},
            )
            self._add(rec)
    
    def ingest_quakes(self, quake_data: Dict, ts: Optional[str] = None):
        """Ingest earthquake data from USGS."""
        if not ts:
            ts = datetime.now(timezone.utc).isoformat()
        
        count = quake_data.get("count", 0)
        latest = quake_data.get("latest", {})
        
        if latest:
            rec = create_record(
                timestamp=ts,
                source_id="usgs_earthquakes",
                data_type="earthquake",
                values={
                    "magnitude": latest.get("mag"),
                    "location": latest.get("place"),
                    "time": latest.get("time"),
                },
                metadata={"total_in_hour": count},
            )
            self._add(rec)
    
    def ingest_internal_state(self, state_file: str, data_type: str, source_id: str):
        """Ingest from our internal state files."""
        try:
            path = Path("/root/.openclaw/workspace") / state_file
            if not path.exists():
                return
            with open(path) as f:
                data = json.load(f)
            
            ts = data.get("timestamp", datetime.now(timezone.utc).isoformat())
            
            rec = create_record(
                timestamp=ts,
                source_id=source_id,
                data_type=data_type,
                values={k: v for k, v in data.items() if k != "timestamp"},
                metadata={"source_file": str(path)},
            )
            self._add(rec)
        except Exception as e:
            self._log(f"Ingest error for {state_file}: {e}")
    
    def _add(self, record: Dict):
        """Thread-safe add."""
        with self._lock:
            self.records.append(record)
    
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(TS_LOG, 'a') as f:
            f.write(line + "\n")
    
    def save(self):
        """Persist records to disk."""
        with self._lock:
            with open(TS_DB, 'a') as f:
                for rec in self.records:
                    f.write(json.dumps(rec, default=str) + "\n")
            # Build index
            index = {
                "last_saved": datetime.now(timezone.utc).isoformat(),
                "total_records": len(self.records),
                "sources": {},
                "data_types": {},
                "time_range": {"start": None, "end": None},
            }
            for rec in self.records:
                sid = rec.get("source_id", "unknown")
                dtype = rec.get("data_type", "unknown")
                index["sources"][sid] = index["sources"].get(sid, 0) + 1
                index["data_types"][dtype] = index["data_types"].get(dtype, 0) + 1
                t = rec.get("timestamp", "")
                if index["time_range"]["start"] is None or t < index["time_range"]["start"]:
                    index["time_range"]["start"] = t
                if index["time_range"]["end"] is None or t > index["time_range"]["end"]:
                    index["time_range"]["end"] = t
            
            with open(TS_INDEX, 'w') as f:
                json.dump(index, f, indent=2, default=str)
            
            self._log(f"Saved {len(self.records)} records. Index updated.")
    
    def query(self, 
              source_id: Optional[str] = None,
              data_type: Optional[str] = None,
              time_start: Optional[str] = None,
              time_end: Optional[str] = None,
              lat: Optional[float] = None,
              lon: Optional[float] = None,
              radius_km: Optional[float] = None,
              limit: int = 100,
              ) -> List[Dict]:
        """Query the timeseries with filters."""
        with self._lock:
            results = list(self.records)
        
        if source_id:
            results = [r for r in results if r.get("source_id") == source_id]
        if data_type:
            results = [r for r in results if r.get("data_type") == data_type]
        
        if time_start or time_end:
            filtered = []
            for r in results:
                t = r.get("timestamp", "")
                if time_start and t < time_start:
                    continue
                if time_end and t > time_end:
                    continue
                filtered.append(r)
            results = filtered
        
        if lat is not None and lon is not None and radius_km is not None:
            results = get_records_in_radius(results, lat, lon, radius_km)
        
        return results[-limit:]  # Return most recent
    
    def get_global_snapshot(self, timestamp: Optional[str] = None, tolerance_seconds: int = 300) -> Dict:
        """Get a snapshot of ALL planetary data at a given time."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        records = get_records_by_time(list(self.records), timestamp, tolerance_seconds)
        
        # Group by source
        by_source = defaultdict(list)
        for rec in records:
            by_source[rec.get("source_id", "unknown")].append(rec)
        
        return {
            "query_time": timestamp,
            "tolerance_seconds": tolerance_seconds,
            "total_records": len(records),
            "sources_active": list(by_source.keys()),
            "records_by_source": dict(by_source),
            "geographic_coverage": self._get_coverage(records),
        }
    
    def _get_coverage(self, records: List[Dict]) -> Dict:
        """Calculate geographic coverage of records."""
        lats = []
        lons = []
        for r in records:
            loc = r.get("location", {})
            if loc.get("lat") is not None and loc.get("lon") is not None:
                lats.append(loc["lat"])
                lons.append(loc["lon"])
        
        if not lats:
            return {"status": "no_geospatial_data"}
        
        return {
            "status": "active",
            "lat_range": [min(lats), max(lats)],
            "lon_range": [min(lons), max(lons)],
            "center": [sum(lats)/len(lats), sum(lons)/len(lons)],
            "station_count": len(set(zip(lats, lons))),
        }
    
    def correlate(self, source_a: str, source_b: str, time_window_hours: int = 1) -> Dict:
        """Find temporal correlations between two sources."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=time_window_hours)).isoformat()
        
        recs_a = self.query(source_id=source_a, time_start=start, limit=1000)
        recs_b = self.query(source_id=source_b, time_start=start, limit=1000)
        
        # Simple correlation: count overlapping timestamps within 5 min
        overlaps = 0
        for ra in recs_a:
            ta = datetime.fromisoformat(ra.get("timestamp", "").replace("Z", "+00:00"))
            for rb in recs_b:
                tb = datetime.fromisoformat(rb.get("timestamp", "").replace("Z", "+00:00"))
                diff = abs((ta - tb).total_seconds())
                if diff <= 300:  # 5 minute overlap
                    overlaps += 1
                    break
        
        return {
            "source_a": source_a,
            "source_b": source_b,
            "time_window_hours": time_window_hours,
            "records_a": len(recs_a),
            "records_b": len(recs_b),
            "temporal_overlaps": overlaps,
            "correlation_score": overlaps / max(len(recs_a), 1),
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR DAEMON
# ═══════════════════════════════════════════════════════════════════════════════

class PlanetaryOrchestrator:
    """Continuous daemon that ingests and queries planetary data."""
    
    def __init__(self):
        self.ingestor = PlanetaryIngestor()
        self.running = False
        self.cycle = 0
        
    def run_cycle(self):
        """One ingestion cycle."""
        self.cycle += 1
        
        # 1. Read unified real-time data
        unified_path = Path("/root/.openclaw/workspace/real_time_data.json")
        if unified_path.exists():
            try:
                with open(unified_path) as f:
                    unified = json.load(f)
                self.ingestor.ingest_noaa(unified)
                self.ingestor.ingest_quakes(unified.get("summary", {}).get("quakes", {}), unified.get("timestamp"))
            except Exception as e:
                self.ingestor._log(f"Unified ingest error: {e}")
        
        # 2. Read internal state files
        self.ingestor.ingest_internal_state("active_field_frequency.json", "field_frequency", "prime_sentinel_field")
        self.ingestor.ingest_internal_state("active_charge_state.json", "charge_state", "prime_sentinel_field")
        self.ingestor.ingest_internal_state("hnc_state.json", "hnc_state", "aureon_ai_core")
        
        # 3. Save every 10 cycles
        if self.cycle % 10 == 0:
            self.ingestor.save()
        
        # 4. Log summary
        snapshot = self.ingestor.get_global_snapshot(tolerance_seconds=600)
        self.ingestor._log(
            f"Cycle {self.cycle}: {snapshot['total_records']} records, "
            f"{len(snapshot['sources_active'])} sources active"
        )
    
    def start(self):
        self.running = True
        self.ingestor._log("═ PLANETARY TIMESERIES ORCHESTRATOR STARTED ═")
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.ingestor._log(f"Cycle error: {e}")
            
            # Sleep with interrupt check
            for _ in range(30):  # 30 second cycles
                if not self.running:
                    break
                time.sleep(1)
        
        self.ingestor.save()
        self.ingestor._log("═ ORCHESTRATOR STOPPED ═")
    
    def stop(self):
        self.running = False

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    orchestrator = PlanetaryOrchestrator()
    
    def shutdown(sig, frame):
        orchestrator.stop()
    
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        # Query mode
        ingestor = PlanetaryIngestor()
        # Load existing records
        if TS_DB.exists():
            with open(TS_DB) as f:
                for line in f:
                    try:
                        ingestor.records.append(json.loads(line))
                    except:
                        pass
        
        print("\n📊 GLOBAL SNAPSHOT (last 5 minutes):")
        snap = ingestor.get_global_snapshot(tolerance_seconds=300)
        print(json.dumps(snap, indent=2, default=str))
        
        print("\n🔗 CORRELATION: NOAA Kp vs USGS Quakes:")
        corr = ingestor.correlate("noaa_swpc_boulder", "usgs_earthquakes", time_window_hours=1)
        print(json.dumps(corr, indent=2, default=str))
        
        print("\n🌍 GEO-QUERY: Within 2000km of Italy (45°N, 7°E):")
        nearby = ingestor.query(lat=45.0, lon=7.0, radius_km=2000, limit=10)
        for rec in nearby:
            print(f"  {rec['timestamp'][:19]} | {rec['source_id']} | {rec['data_type']} | {rec['location']['name']}")
    
    else:
        # Daemon mode
        orchestrator.start()
