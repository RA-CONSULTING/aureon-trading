#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 UPDATE GARY'S LIVE LOCATION
───────────────────────────────────────────────────────────────────────────

Usage:
  python update_gary_location.py <latitude> <longitude>
  
Examples:
  python update_gary_location.py 52.5200 13.4050     # Berlin
  python update_gary_location.py 48.8566 2.3522      # Paris
  python update_gary_location.py 51.5074 -0.1278     # London
  python update_gary_location.py 40.7128 -74.0060    # New York
"""

import sys
sys.path.insert(0, '/workspaces/aureon-trading')

from aureon.utils.aureon_live_aura_location_tracker import LiveAuraLocationTracker


def update_location(lat: float, lon: float):
    """Update Gary's location"""
    tracker = LiveAuraLocationTracker()
    tracker.start()
    
    # Update GPS
    gps_data = {
        'latitude': lat,
        'longitude': lon,
        'accuracy_m': 10.0,
        'speed': 0.0
    }
    
    tracker.update_from_gps(gps_data)
    
    # Get new snapshot
    snapshot = tracker.get_current_location()
    
    if snapshot:
        print(f"\n✅ Location Updated!\n")
        print(f"📍 New Position: {snapshot['gps_latitude']:.4f}°, {snapshot['gps_longitude']:.4f}°")
        print(f"📏 Distance from Belfast: {snapshot['distance_from_belfast_km']:.1f} km")
        print(f"🧠 State: {snapshot['consciousness_state']}")
        print(f"💰 Multiplier: {snapshot['trading_multiplier']}x")
        print(f"📡 Status: {snapshot['status']}")
        return True
    else:
        print("❌ Failed to update location")
        return False


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        print("\nUsage: python update_gary_location.py <latitude> <longitude>")
        print("\nExample: python update_gary_location.py 52.5200 13.4050")
        sys.exit(1)
    
    try:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        
        if not (-90 <= lat <= 90):
            print(f"❌ Invalid latitude: {lat} (must be -90 to 90)")
            sys.exit(1)
        
        if not (-180 <= lon <= 180):
            print(f"❌ Invalid longitude: {lon} (must be -180 to 180)")
            sys.exit(1)
        
        update_location(lat, lon)
        
    except ValueError as e:
        print(f"❌ Invalid coordinates: {e}")
        print("\nUsage: python update_gary_location.py <latitude> <longitude>")
        sys.exit(1)
