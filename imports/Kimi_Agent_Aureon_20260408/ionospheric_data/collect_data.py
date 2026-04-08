#!/usr/bin/env python3
"""
30-Day Ionospheric Data Collection System
Run this script continuously for 30 days to collect data
"""

import requests
import os
import time
from datetime import datetime, timezone
import json

# Configuration
DATA_DIR = "/mnt/okcomputer/output/ionospheric_data"
COLLECTION_LOG = []

def log_event(event_type, message, success=True):
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {"timestamp": timestamp, "type": event_type, "message": message, "success": success}
    COLLECTION_LOG.append(entry)

    # Save log
    with open(f"{DATA_DIR}/logs/collection_log.json", 'w') as f:
        json.dump(COLLECTION_LOG, f, indent=2)

    status = "✓" if success else "✗"
    print(f"{status} [{datetime.now().strftime('%H:%M:%S')}] {event_type}: {message}")

def download_schumann():
    """Download Schumann sonogram from Tomsk"""
    try:
        # Try to get the latest sonogram
        # URL pattern based on the working site
        now = datetime.now(timezone.utc)

        # The site uses Supabase storage with timestamp-based URLs
        # We need to scrape the page to get the current URL

        # Alternative: Use a simpler approach - check the main page
        main_page = "https://schumannresonancedata.com/"

        # For now, we'll use the browser automation approach
        # This requires manual intervention or selenium

        log_event("SCHUMANN", "Requires browser automation - use manual download", success=False)
        return False

    except Exception as e:
        log_event("SCHUMANN", f"Error: {str(e)}", success=False)
        return False

def download_noaa_space_weather():
    """Download NOAA space weather data"""
    try:
        urls = {
            "kp_index": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json",
            "solar_wind": "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json",
            "magnetometer": "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json",
        }

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        for name, url in urls.items():
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    filename = f"{DATA_DIR}/analysis/{name}_{timestamp}.json"
                    with open(filename, 'w') as f:
                        f.write(response.text)
                    log_event("SPACE_WEATHER", f"{name}: {len(response.text)} chars")
                else:
                    log_event("SPACE_WEATHER", f"{name}: HTTP {response.status_code}", success=False)
            except Exception as e:
                log_event("SPACE_WEATHER", f"{name}: {str(e)}", success=False)

        return True
    except Exception as e:
        log_event("SPACE_WEATHER", f"Error: {str(e)}", success=False)
        return False

def main_collection_loop():
    """Main data collection loop"""
    print("=" * 70)
    print("30-DAY IONOSPHERIC DATA COLLECTION")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Duration: 30 days")
    print(f"Data directory: {DATA_DIR}")
    print()

    # Collection counters
    schumann_count = 0
    spaceweather_count = 0

    # Collection intervals (in seconds)
    SCHUMANN_INTERVAL = 10 * 60  # 10 minutes
    SPACEWEATHER_INTERVAL = 60 * 60  # 1 hour

    last_schumann = 0
    last_spaceweather = 0

    start_time = time.time()
    end_time = start_time + (30 * 24 * 60 * 60)  # 30 days

    while time.time() < end_time:
        current_time = time.time()
        elapsed = current_time - start_time
        remaining = end_time - current_time

        # Print status every hour
        if int(elapsed) % 3600 == 0:
            days_elapsed = elapsed / (24 * 3600)
            days_remaining = remaining / (24 * 3600)
            print(f"\n[STATUS] Day {days_elapsed:.1f}/30 | {days_remaining:.1f} days remaining")
            print(f"         Schumann: {schumann_count} | Space Weather: {spaceweather_count}")

        # Collect Schumann data
        if current_time - last_schumann >= SCHUMANN_INTERVAL:
            download_schumann()
            last_schumann = current_time
            schumann_count += 1

        # Collect Space Weather data
        if current_time - last_spaceweather >= SPACEWEATHER_INTERVAL:
            download_noaa_space_weather()
            last_spaceweather = current_time
            spaceweather_count += 1

        # Sleep to prevent CPU spinning
        time.sleep(1)

    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total Schumann: {schumann_count}")
    print(f"Total Space Weather: {spaceweather_count}")

if __name__ == "__main__":
    main_collection_loop()
