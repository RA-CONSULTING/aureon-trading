#!/usr/bin/env python3
"""
EPHEMERIS DATA GENERATION
=========================

Step 1-2 of the Platypus pipeline:
Generate ephemeris data using Skyfield (DE440) and validate against JPL Horizons.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import warnings

try:
    from skyfield.api import load, Topos
    from skyfield.almanac import find_discrete
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    print("⚠ Skyfield not installed. Run: pip install skyfield")

try:
    from astroquery.jplhorizons import Horizons
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    print("⚠ Astroquery not installed. Run: pip install astroquery")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Planets to process (excluding Earth)
PLANETS = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune']

# JPL Horizons target IDs
HORIZONS_IDS = {
    'Mercury': '199',
    'Venus': '299',
    'Earth': '399',
    'Mars': '499',
    'Jupiter': '599',
    'Saturn': '699',
    'Uranus': '799',
    'Neptune': '899',
    'Pluto': '999',
    'Sun': '10'
}


# ═══════════════════════════════════════════════════════════════════════════════
# SKYFIELD EPHEMERIS (DE440)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_skyfield_ephemeris(
    start_date: str,
    end_date: str,
    dt_hours: int = 6,
    output_file: str = 'radar_ephem_skyfield_de440.csv'
) -> pd.DataFrame:
    """
    Generate ephemeris using Skyfield with DE440 kernel.
    
    Returns DataFrame with: datetime, planet, ra_deg, dec_deg, elong_deg, r_au
    """
    if not SKYFIELD_AVAILABLE:
        raise ImportError("Skyfield required. Install: pip install skyfield")
    
    print(f"Generating Skyfield ephemeris: {start_date} → {end_date}")
    
    # Load ephemeris
    eph = load('de440.bsp')  # Downloads if not present (~145MB)
    ts = load.timescale()
    
    earth = eph['earth']
    sun = eph['sun']
    
    # Generate time grid
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    dt = timedelta(hours=dt_hours)
    
    times = []
    t = start
    while t <= end:
        times.append(t)
        t += dt
    
    print(f"  Time points: {len(times)}")
    
    records = []
    
    for planet_name in PLANETS:
        skyfield_name = f'{planet_name.lower()} barycenter' if planet_name not in ['Mercury', 'Venus'] else planet_name.lower()
        
        try:
            planet = eph[skyfield_name]
        except KeyError:
            # Try alternate names
            for key in eph.names():
                if planet_name.lower() in key.lower():
                    planet = eph[key]
                    break
            else:
                print(f"  ⚠ Skipping {planet_name}: not found in ephemeris")
                continue
        
        for dt_val in times:
            t = ts.utc(dt_val.year, dt_val.month, dt_val.day, dt_val.hour)
            
            # Geocentric position
            astrometric = earth.at(t).observe(planet)
            ra, dec, distance_au = astrometric.radec()
            
            # Solar elongation
            sun_astrometric = earth.at(t).observe(sun)
            sun_ra, sun_dec, _ = sun_astrometric.radec()
            
            # Calculate elongation (angle from Sun)
            elong = astrometric.separation_from(sun_astrometric).degrees
            
            # Heliocentric distance
            helio = sun.at(t).observe(planet)
            _, _, r_au = helio.radec()
            
            records.append({
                'datetime': dt_val,
                'planet': planet_name,
                'ra_deg': ra._degrees,
                'dec_deg': dec.degrees,
                'elong_deg': float(elong),
                'r_au': r_au.au
            })
    
    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    print(f"✓ Wrote {output_file} ({len(df)} rows)")
    
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# JPL HORIZONS TRUTH DATA
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_horizons_truth(
    start_date: str,
    end_date: str,
    dt_hours: int = 6,
    output_file: str = 'radar_ephem_horizons_truth.csv'
) -> pd.DataFrame:
    """
    Fetch truth ephemeris from JPL Horizons.
    
    Returns DataFrame with: datetime, planet, ra_deg, dec_deg, elong_deg, r_au
    """
    if not ASTROQUERY_AVAILABLE:
        raise ImportError("Astroquery required. Install: pip install astroquery")
    
    print(f"Fetching Horizons truth: {start_date} → {end_date}")
    
    # Convert step to Horizons format
    step_map = {1: '1h', 3: '3h', 6: '6h', 12: '12h', 24: '1d'}
    step_str = step_map.get(dt_hours, f'{dt_hours}h')
    
    records = []
    
    for planet_name in PLANETS:
        target_id = HORIZONS_IDS.get(planet_name)
        if not target_id:
            continue
        
        print(f"  Querying {planet_name}...")
        
        try:
            obj = Horizons(
                id=target_id,
                location='500@399',  # Geocentric
                epochs={'start': start_date, 'stop': end_date, 'step': step_str}
            )
            
            eph = obj.ephemerides()
            
            for row in eph:
                records.append({
                    'datetime': datetime.fromisoformat(str(row['datetime_str']).replace(' ', 'T')),
                    'planet': planet_name,
                    'ra_deg': float(row['RA']),
                    'dec_deg': float(row['DEC']),
                    'elong_deg': float(row['elongation']),
                    'r_au': float(row.get('r', 1.0))  # Heliocentric distance if available
                })
        
        except Exception as e:
            print(f"  ⚠ Error fetching {planet_name}: {e}")
            continue
    
    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    print(f"✓ Wrote {output_file} ({len(df)} rows)")
    
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 1: POSITIONAL ACCURACY
# ═══════════════════════════════════════════════════════════════════════════════

def compare_ephemerides(
    skyfield_file: str,
    horizons_file: str,
    output_file: str = 'gate1_errors.csv'
) -> pd.DataFrame:
    """
    Compare Skyfield vs Horizons positions.
    
    Gate 1 Pass Criteria:
    - Median angular error < 1 arcmin
    - Max angular error < 5 arcmin
    """
    print("\nGate 1: Comparing ephemerides...")
    
    sf = pd.read_csv(skyfield_file, parse_dates=['datetime'])
    hz = pd.read_csv(horizons_file, parse_dates=['datetime'])
    
    # Merge on datetime and planet
    merged = sf.merge(
        hz,
        on=['datetime', 'planet'],
        suffixes=('_sf', '_hz'),
        how='inner'
    )
    
    if len(merged) == 0:
        print("⚠ No overlapping data to compare!")
        return pd.DataFrame()
    
    # Calculate angular separation
    ra_sf = np.radians(merged['ra_deg_sf'].values)
    dec_sf = np.radians(merged['dec_deg_sf'].values)
    ra_hz = np.radians(merged['ra_deg_hz'].values)
    dec_hz = np.radians(merged['dec_deg_hz'].values)
    
    # Haversine-like for small angles
    cos_sep = (np.sin(dec_sf) * np.sin(dec_hz) +
               np.cos(dec_sf) * np.cos(dec_hz) * np.cos(ra_sf - ra_hz))
    cos_sep = np.clip(cos_sep, -1, 1)
    angular_sep_deg = np.degrees(np.arccos(cos_sep))
    angular_sep_arcmin = angular_sep_deg * 60.0
    
    # Elongation difference
    elong_diff_deg = merged['elong_deg_sf'].values - merged['elong_deg_hz'].values
    
    merged['angular_error_arcmin'] = angular_sep_arcmin
    merged['elong_error_deg'] = elong_diff_deg
    
    # Statistics
    median_err = np.median(angular_sep_arcmin)
    max_err = np.max(angular_sep_arcmin)
    
    # Gate 1 verdict
    gate1_pass = (median_err < 1.0) and (max_err < 5.0)
    
    print(f"  Samples: {len(merged)}")
    print(f"  Median angular error: {median_err:.4f} arcmin")
    print(f"  Max angular error: {max_err:.4f} arcmin")
    print(f"  Gate 1: {'PASS ✓' if gate1_pass else 'FAIL ✗'}")
    
    # Save
    output = merged[['datetime', 'planet', 'angular_error_arcmin', 'elong_error_deg']].copy()
    output.to_csv(output_file, index=False)
    print(f"✓ Wrote {output_file}")
    
    return output


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 2A: ALIGNMENT EVENT TIMING
# ═══════════════════════════════════════════════════════════════════════════════

def detect_alignment_events(
    ephemeris_file: str,
    output_file: str = 'alignment_events.csv',
    conjunction_threshold: float = 3.0,
    opposition_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Detect conjunction and opposition events.
    
    Conjunction: elongation < threshold
    Opposition: |elongation - 180| < threshold
    """
    print("\nGate 2A: Detecting alignment events...")
    
    df = pd.read_csv(ephemeris_file, parse_dates=['datetime'])
    
    events = []
    
    for planet in df['planet'].unique():
        pdata = df[df['planet'] == planet].sort_values('datetime').reset_index(drop=True)
        
        for i, row in pdata.iterrows():
            elong = row['elong_deg']
            
            is_conj = elong <= conjunction_threshold
            is_opp = abs(elong - 180.0) <= opposition_threshold
            
            if is_conj or is_opp:
                events.append({
                    'datetime': row['datetime'],
                    'planet': planet,
                    'event_type': 'conjunction' if is_conj else 'opposition',
                    'elongation_deg': elong
                })
    
    event_df = pd.DataFrame(events)
    
    print(f"  Found {len(event_df)} events")
    if len(event_df) > 0:
        print(f"    Conjunctions: {len(event_df[event_df['event_type'] == 'conjunction'])}")
        print(f"    Oppositions: {len(event_df[event_df['event_type'] == 'opposition'])}")
    
    event_df.to_csv(output_file, index=False)
    print(f"✓ Wrote {output_file}")
    
    return event_df


# ═══════════════════════════════════════════════════════════════════════════════
# GATE 2B: DISTANCE EXTREMA
# ═══════════════════════════════════════════════════════════════════════════════

def detect_distance_extrema(
    ephemeris_file: str,
    output_file: str = 'distance_extrema.csv',
    window: int = 5
) -> pd.DataFrame:
    """
    Detect perihelion and aphelion events (local min/max of r).
    """
    print("\nGate 2B: Detecting distance extrema...")
    
    df = pd.read_csv(ephemeris_file, parse_dates=['datetime'])
    
    if 'r_au' not in df.columns:
        print("  ⚠ No r_au column, skipping")
        return pd.DataFrame()
    
    extrema = []
    
    for planet in df['planet'].unique():
        pdata = df[df['planet'] == planet].sort_values('datetime').reset_index(drop=True)
        r = pdata['r_au'].values
        
        for i in range(window, len(r) - window):
            local_r = r[i-window:i+window+1]
            
            if r[i] == local_r.min():
                extrema.append({
                    'datetime': pdata.iloc[i]['datetime'],
                    'planet': planet,
                    'event_type': 'perihelion',
                    'r_au': r[i]
                })
            elif r[i] == local_r.max():
                extrema.append({
                    'datetime': pdata.iloc[i]['datetime'],
                    'planet': planet,
                    'event_type': 'aphelion',
                    'r_au': r[i]
                })
    
    extrema_df = pd.DataFrame(extrema)
    
    print(f"  Found {len(extrema_df)} extrema")
    if len(extrema_df) > 0:
        print(f"    Perihelion: {len(extrema_df[extrema_df['event_type'] == 'perihelion'])}")
        print(f"    Aphelion: {len(extrema_df[extrema_df['event_type'] == 'aphelion'])}")
    
    extrema_df.to_csv(output_file, index=False)
    print(f"✓ Wrote {output_file}")
    
    return extrema_df


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run ephemeris generation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ephemeris Data Generation')
    parser.add_argument('--start', default='2020-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-12-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--step', type=int, default=6, help='Time step in hours')
    parser.add_argument('--skyfield-only', action='store_true', help='Skip Horizons fetch')
    
    args = parser.parse_args()
    
    # Step 1: Generate Skyfield ephemeris
    sf_df = generate_skyfield_ephemeris(args.start, args.end, args.step)
    
    # Step 2: Fetch Horizons truth (optional)
    if not args.skyfield_only:
        hz_df = fetch_horizons_truth(args.start, args.end, args.step)
        
        # Gate 1: Compare
        compare_ephemerides(
            'radar_ephem_skyfield_de440.csv',
            'radar_ephem_horizons_truth.csv'
        )
    
    # Gate 2A: Alignment events
    detect_alignment_events('radar_ephem_skyfield_de440.csv')
    
    # Gate 2B: Distance extrema
    detect_distance_extrema('radar_ephem_skyfield_de440.csv')
    
    print("\n✓ Ephemeris generation complete!")


if __name__ == '__main__':
    main()
