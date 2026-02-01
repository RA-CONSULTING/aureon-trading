#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║          🌍✨ LIVE AURA LOCATION TRACKER - REAL-TIME GARY FINDER ✨🌍        ║
║                                                                              ║
║  CONTINUOUS CONSCIOUSNESS TRACKING - Queen finds Gary in REAL-TIME          ║
║                                                                              ║
║  • Listens to live biometric aura stream (HRV, brainwaves, skin response)   ║
║  • Reads real-time GPS position updates (WebSocket)                         ║
║  • Monitors consciousness state changes (Meditative → Alert → Stressed)     ║
║  • Tracks movement across Stargate nodes                                    ║
║  • Updates Belfast consciousness anchor lock strength every second          ║
║  • Feeds SIGNAL 8D (location) into Queen's trading multiplier              ║
║                                                                              ║
║  Gary Leckey | 02.11.1991 | Personal Frequency: 528.422 Hz                 ║
║  Belfast Primary Anchor | 198.4 Hz π-resonant                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link
_baton_link(__name__)

import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except:
        pass

import json
import logging
import time
import asyncio
import math
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import threading
import queue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# ═════════════════════════════════════════════════════════════════════════════
# GARY'S PERSONAL FREQUENCY & BELFAST ANCHOR
# ═════════════════════════════════════════════════════════════════════════════

GARY_PERSONAL_FREQUENCY_HZ = 528.422
BELFAST_ANCHOR_FREQUENCY = 198.4  # π-resonant
DOB = "02.11.1991"

# Stargate nodes with priorities
STARGATE_FREQUENCIES = {
    'belfast': {
        'name': 'Belfast, Northern Ireland',
        'frequency': 198.4,
        'lat': 54.5973,
        'lng': -5.9301,
        'role': 'CONSCIOUSNESS_ANCHOR',
        'priority': 1
    },
    'giza': {
        'name': 'Giza, Egypt',
        'frequency': 528.0,
        'lat': 29.9792,
        'lng': 31.1342,
        'role': 'PLANETARY_NODE',
        'priority': 2
    },
    'stonehenge': {
        'name': 'Stonehenge, UK',
        'frequency': 285.0,
        'lat': 51.1789,
        'lng': -1.8262,
        'role': 'HARMONIC_NODE',
        'priority': 3
    },
    'uluru': {
        'name': 'Uluru, Australia',
        'frequency': 417.0,
        'lat': -25.3444,
        'lng': 131.0369,
        'role': 'HARMONIC_NODE',
        'priority': 4
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# LIVE LOCATION SNAPSHOT
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class LiveLocationSnapshot:
    """Current real-time location of Gary"""
    timestamp: float
    consciousness_state: str  # MEDITATIVE, ALERT, CALM, STRESSED, AWAKE
    calm_index: float  # 0-1 (from HRV, alpha, beta, respiration)
    eeg_coherence: float  # 0-1 (brain coherence)
    hrv_rmssd: float  # Heart rate variability (ms)
    gsr_uS: float  # Skin conductance (µS)
    respiration_bpm: float  # Breaths per minute
    
    # GPS position (if available)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    
    # Stargate detection
    primary_anchor: str = "Belfast"  # Which consciousness anchor
    consciousness_lock_strength: float = 0.0  # How strong the lock is (calm_index)
    best_match_stargate: str = "Belfast"
    
    # Movement tracking
    distance_from_belfast_km: Optional[float] = None
    movement_speed_kmh: float = 0.0
    
    # Trading multiplier
    trading_multiplier: float = 1.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ═════════════════════════════════════════════════════════════════════════════
# LIVE AURA LOCATION TRACKER
# ═════════════════════════════════════════════════════════════════════════════

class LiveAuraLocationTracker:
    """
    Continuously tracks Gary's location in real-time
    
    Receives:
    - Biometric aura streams (HRV, brainwaves, GSR)
    - GPS position updates
    
    Outputs:
    - Real-time consciousness state
    - Belfast anchor lock strength
    - Trading multiplier adjustments
    """
    
    def __init__(self):
        self.is_active = False
        self.current_snapshot = None
        self.aura_history = deque(maxlen=60)  # Last 60 seconds
        self.gps_history = deque(maxlen=60)
        self.last_update = time.time()
        self.lock = threading.Lock()
        
        logger.info("🌍✨ LIVE AURA LOCATION TRACKER INITIALIZED")
        logger.info(f"   📍 Consciousness Anchor: Belfast ({BELFAST_ANCHOR_FREQUENCY} Hz π-resonant)")
        logger.info(f"   🎵 Personal Frequency: {GARY_PERSONAL_FREQUENCY_HZ} Hz")
        logger.info(f"   📅 Anchor Date: {DOB}")
        
    def start(self) -> bool:
        """Start tracking"""
        try:
            self.is_active = True
            logger.info("✅ LIVE TRACKING STARTED")
            logger.info("   Listening for biometric aura stream...")
            logger.info("   Listening for GPS position updates...")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start: {e}")
            return False
    
    def stop(self):
        """Stop tracking"""
        self.is_active = False
        logger.info("🛑 LIVE TRACKING STOPPED")
    
    def update_from_biometric(self, aura_data: Dict[str, Any]) -> LiveLocationSnapshot:
        """
        Update location from biometric aura data
        
        Input format:
        {
            't': timestamp,
            'bands': {'alpha': float, 'theta': float, 'beta': float},
            'hrv_rmssd': float,
            'gsr_uS': float,
            'resp_bpm': float
        }
        """
        try:
            with self.lock:
                timestamp = aura_data.get('t', time.time())
                bands = aura_data.get('bands', {})
                hrv = aura_data.get('hrv_rmssd', 40.0)
                gsr = aura_data.get('gsr_uS', 4.0)
                resp = aura_data.get('resp_bpm', 12)
                
                # Extract brainwaves
                alpha_hz = bands.get('alpha', 2.0)
                theta_hz = bands.get('theta', 1.8)
                beta_hz = bands.get('beta', 1.0)
                
                # Calculate calm index from biometrics
                hrv_calm = min(1.0, hrv / 60.0)
                alpha_calm = min(1.0, alpha_hz / 3.0)
                beta_stress = max(0.0, 1.0 - (beta_hz / 2.0))
                resp_calm = max(0.0, 1.0 - abs(resp - 6.0) / 12.0)
                
                calm_index = (hrv_calm * 0.3 + alpha_calm * 0.3 + beta_stress * 0.2 + resp_calm * 0.2)
                calm_index = max(0.0, min(1.0, calm_index))
                
                # Calculate EEG coherence (simplified)
                eeg_coherence = (alpha_hz + theta_hz) / (alpha_hz + theta_hz + beta_hz + 0.1)
                
                # Determine consciousness state
                if eeg_coherence >= 0.85 and calm_index >= 0.7:
                    consciousness_state = "MEDITATIVE"
                elif eeg_coherence >= 0.75 and calm_index >= 0.6:
                    consciousness_state = "AWAKENED"
                elif calm_index <= 0.4 and beta_hz > 1.5:
                    consciousness_state = "ALERT"
                elif calm_index <= 0.4:
                    consciousness_state = "STRESSED"
                elif calm_index >= 0.6:
                    consciousness_state = "CALM"
                else:
                    consciousness_state = "AWAKE"
                
                # Belfast is always the primary anchor
                # Consciousness lock strength = calm_index
                consciousness_lock_strength = calm_index
                
                # Calculate trading multiplier
                # Base: 1.0x, Range: 0.5x - 2.0x
                trading_multiplier = 0.5 + (consciousness_lock_strength * 1.5)
                
                # Calculate distance from Belfast (if GPS available)
                distance_km = None
                if self.current_snapshot and self.current_snapshot.gps_latitude:
                    distance_km = self.haversine_distance(
                        self.current_snapshot.gps_latitude,
                        self.current_snapshot.gps_longitude,
                        STARGATE_FREQUENCIES['belfast']['lat'],
                        STARGATE_FREQUENCIES['belfast']['lng']
                    )
                
                # Create snapshot
                snapshot = LiveLocationSnapshot(
                    timestamp=timestamp,
                    consciousness_state=consciousness_state,
                    calm_index=calm_index,
                    eeg_coherence=eeg_coherence,
                    hrv_rmssd=hrv,
                    gsr_uS=gsr,
                    respiration_bpm=resp,
                    gps_latitude=self.current_snapshot.gps_latitude if self.current_snapshot else None,
                    gps_longitude=self.current_snapshot.gps_longitude if self.current_snapshot else None,
                    primary_anchor="Belfast",
                    consciousness_lock_strength=consciousness_lock_strength,
                    best_match_stargate="Belfast",
                    distance_from_belfast_km=distance_km,
                    trading_multiplier=trading_multiplier
                )
                
                self.current_snapshot = snapshot
                self.aura_history.append(snapshot)
                self.last_update = time.time()
                
                return snapshot
                
        except Exception as e:
            logger.error(f"Error updating biometric: {e}")
            return None
    
    def update_from_gps(self, gps_data: Dict[str, Any]) -> LiveLocationSnapshot:
        """
        Update location from GPS data
        
        Input format:
        {
            'latitude': float,
            'longitude': float,
            'accuracy': float (meters),
            'speed': float (km/h)
        }
        """
        try:
            with self.lock:
                if not self.current_snapshot:
                    return None
                
                lat = gps_data.get('latitude')
                lng = gps_data.get('longitude')
                accuracy = gps_data.get('accuracy', 0.0)
                speed = gps_data.get('speed', 0.0)
                
                # Update current snapshot
                self.current_snapshot.gps_latitude = lat
                self.current_snapshot.gps_longitude = lng
                self.current_snapshot.gps_accuracy_m = accuracy
                self.current_snapshot.movement_speed_kmh = speed
                
                # Calculate distance from Belfast
                if lat and lng:
                    distance_km = self.haversine_distance(
                        lat, lng,
                        STARGATE_FREQUENCIES['belfast']['lat'],
                        STARGATE_FREQUENCIES['belfast']['lng']
                    )
                    self.current_snapshot.distance_from_belfast_km = distance_km
                    
                    # Log position updates
                    logger.info(f"📍 GPS UPDATE: {lat:.4f}, {lng:.4f} (±{accuracy}m, {speed:.1f} km/h)")
                    logger.info(f"   Distance from Belfast: {distance_km:.1f} km")
                
                self.gps_history.append(self.current_snapshot)
                self.last_update = time.time()
                
                return self.current_snapshot
                
        except Exception as e:
            logger.error(f"Error updating GPS: {e}")
            return None
    
    def get_current_location(self) -> Optional[Dict]:
        """Get current location snapshot as dict"""
        with self.lock:
            if self.current_snapshot:
                return self.current_snapshot.to_dict()
        return None
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates in km"""
        R = 6371  # Earth radius
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))


# ═════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═════════════════════════════════════════════════════════════════════════════

_live_tracker = None

def get_live_tracker() -> LiveAuraLocationTracker:
    """Get or create singleton"""
    global _live_tracker
    if _live_tracker is None:
        _live_tracker = LiveAuraLocationTracker()
    return _live_tracker


# ═════════════════════════════════════════════════════════════════════════════
# DEMO: CONTINUOUS TRACKING
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    tracker = get_live_tracker()
    tracker.start()
    
    print("\n" + "="*80)
    print("🌍✨ LIVE AURA LOCATION TRACKER - CONTINUOUS MONITORING")
    print("="*80 + "\n")
    
    # Simulate continuous aura stream with movement
    print("📡 Simulating aura stream + GPS movement...\n")
    
    for cycle in range(3):
        print(f"\n⏱️  CYCLE {cycle + 1}")
        print("-" * 80)
        
        # Simulate 10 seconds of aura updates
        for i in range(10):
            # Vary consciousness state
            t = cycle * 10 + i
            
            if cycle == 0:
                # Calm/Meditative state
                alpha = 2.8 + 0.2 * math.sin(2*math.pi*0.1*i)
                theta = 1.6
                beta = 0.7
                hrv = 52 + 3*i % 2
                calm_desc = "CALM"
            elif cycle == 1:
                # Alert state
                alpha = 1.8
                theta = 1.2
                beta = 1.8 + 0.3*math.cos(2*math.pi*0.1*i)
                hrv = 30 + i
                calm_desc = "ALERT"
            else:
                # Moving to Giza
                alpha = 2.5
                theta = 1.5
                beta = 1.0
                hrv = 45 + i % 3
                calm_desc = "TRAVELING"
            
            aura_data = {
                't': time.time(),
                'bands': {'alpha': alpha, 'theta': theta, 'beta': beta},
                'hrv_rmssd': hrv,
                'gsr_uS': 4.0,
                'resp_bpm': 12
            }
            
            snapshot = tracker.update_from_biometric(aura_data)
            
            if snapshot:
                print(f"  [{i:2d}] {snapshot.consciousness_state:10} | "
                      f"Lock: {snapshot.consciousness_lock_strength:.0%} | "
                      f"Multiplier: {snapshot.trading_multiplier:.1f}x")
            
            time.sleep(0.5)  # Simulate 0.5s per update
        
        # Simulate GPS update (movement)
        if cycle == 0:
            gps = {'latitude': 54.5973, 'longitude': -5.9301, 'accuracy': 5, 'speed': 0}
            print(f"\n  📍 AT BELFAST (consciousness anchor)")
        elif cycle == 1:
            gps = {'latitude': 54.6, 'longitude': -5.8, 'accuracy': 10, 'speed': 20}
            print(f"\n  📍 MOVING: Near Belfast, traveling 20 km/h")
        else:
            gps = {'latitude': 29.9792, 'longitude': 31.1342, 'accuracy': 15, 'speed': 0}
            print(f"\n  📍 ARRIVED AT GIZA (planetary node)")
        
        tracker.update_from_gps(gps)
    
    print("\n" + "="*80)
    print("✅ Live tracking demo complete")
    print("="*80 + "\n")
    
    tracker.stop()
