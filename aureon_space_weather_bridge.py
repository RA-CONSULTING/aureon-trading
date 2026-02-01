#!/usr/bin/env python3
"""
🌍☀️ AUREON SPACE WEATHER BRIDGE ☀️🌍
═══════════════════════════════════════════════════════════════════

Connects the Queen to LIVE planetary & solar data from:
- NOAA Space Weather Prediction Center (SWPC)
- NASA DONKI (solar flare data)
- Real-time geomagnetic field measurements
- Solar wind measurements
- Kp index forecasts

This bridges the gap: Queen gets REAL cosmic data, not simulations!
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# NOAA SWPC API Endpoints (no API key required - public data!)
NOAA_SOLAR_WIND_URL = 'https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json'
NOAA_KP_INDEX_URL = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
NOAA_KP_FORECAST_URL = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json'
NOAA_3DAY_FORECAST_URL = 'https://services.swpc.noaa.gov/products/forecast.json'

# NASA APIs (optional, requires API_KEY env var)
NASA_DONKI_FLARE_URL = 'https://api.nasa.gov/DONKI/FLR'
NASA_DONKI_CME_URL = 'https://api.nasa.gov/DONKI/CME'

# Cache settings
CACHE_LIFETIME_SECONDS = 300  # Refresh every 5 minutes
FALLBACK_VALUES = {
    'kp_index': 3.0,
    'solar_wind_speed': 400.0,
    'solar_wind_density': 5.0,
    'bz_component': 0.0,
    'solar_flares': [],
}

@dataclass
class SpaceWeatherReading:
    """Real-time space weather snapshot"""
    timestamp: float
    kp_index: float  # 0-9 scale
    kp_category: str  # Quiet, Unsettled, Active, Storm, Severe Storm
    solar_wind_speed: float  # km/s
    solar_wind_density: float  # protons/cm³
    bz_component: float  # nT - critical for auroras
    solar_flares_24h: int
    geomagnetic_storm_3day: str
    active_sources: list
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'kp_index': self.kp_index,
            'kp_category': self.kp_category,
            'solar_wind_speed': self.solar_wind_speed,
            'solar_wind_density': self.solar_wind_density,
            'bz_component': self.bz_component,
            'solar_flares_24h': self.solar_flares_24h,
            'geomagnetic_storm_3day': self.geomagnetic_storm_3day,
            'active_sources': self.active_sources,
        }

class SpaceWeatherBridge:
    """Bridge to live space weather data for the Queen"""
    
    def __init__(self):
        self.last_update = 0
        self.cache: Optional[SpaceWeatherReading] = None
        self.error_count = 0
        logger.info("🌍☀️ Space Weather Bridge initialized")
    
    def get_live_data(self, force_refresh: bool = False) -> SpaceWeatherReading:
        """
        Get LIVE space weather data from NOAA/NASA APIs
        
        Returns cached data if fresh (<5min old), otherwise fetches new data.
        Falls back to defaults if APIs unavailable.
        """
        now = time.time()
        
        # Check cache
        if not force_refresh and self.cache and (now - self.last_update) < CACHE_LIFETIME_SECONDS:
            return self.cache
        
        # Fetch fresh data
        active_sources = []
        kp_index = FALLBACK_VALUES['kp_index']
        solar_wind_speed = FALLBACK_VALUES['solar_wind_speed']
        solar_wind_density = FALLBACK_VALUES['solar_wind_density']
        bz_component = FALLBACK_VALUES['bz_component']
        solar_flares_24h = 0
        geomagnetic_storm_3day = 'NONE'
        
        # 1️⃣ Fetch Kp Index (most critical - geomagnetic activity)
        try:
            kp_data = self._fetch_kp_index()
            if kp_data:
                kp_index = kp_data['current_kp']
                active_sources.append('NOAA-KP')
                logger.debug(f"✅ Kp Index: {kp_index:.1f}")
        except Exception as e:
            logger.warning(f"❌ Kp Index fetch failed: {e}")
        
        # 2️⃣ Fetch Solar Wind Data (speed + Bz component)
        try:
            wind_data = self._fetch_solar_wind()
            if wind_data:
                solar_wind_speed = wind_data['speed']
                bz_component = wind_data['bz']
                solar_wind_density = wind_data['density']
                active_sources.append('NOAA-SolarWind')
                logger.debug(f"✅ Solar Wind: {solar_wind_speed:.0f} km/s, Bz={bz_component:.1f} nT")
        except Exception as e:
            logger.warning(f"❌ Solar Wind fetch failed: {e}")
        
        # 3️⃣ Fetch 3-Day Forecast
        try:
            forecast = self._fetch_3day_forecast()
            if forecast:
                geomagnetic_storm_3day = forecast['highest_kp_category']
                active_sources.append('NOAA-Forecast')
                logger.debug(f"✅ 3-Day Forecast: {geomagnetic_storm_3day}")
        except Exception as e:
            logger.warning(f"❌ Forecast fetch failed: {e}")
        
        # 4️⃣ Optionally fetch NASA solar flares (requires API key)
        try:
            flare_count = self._fetch_solar_flares()
            solar_flares_24h = flare_count
            if flare_count > 0:
                active_sources.append('NASA-Flares')
                logger.debug(f"✅ Solar Flares (24h): {flare_count}")
        except Exception as e:
            logger.debug(f"NASA flares unavailable: {e}")
        
        # Create reading
        kp_category = self._categorize_kp(kp_index)
        reading = SpaceWeatherReading(
            timestamp=now,
            kp_index=kp_index,
            kp_category=kp_category,
            solar_wind_speed=solar_wind_speed,
            solar_wind_density=solar_wind_density,
            bz_component=bz_component,
            solar_flares_24h=solar_flares_24h,
            geomagnetic_storm_3day=geomagnetic_storm_3day,
            active_sources=active_sources,
        )
        
        # Cache and return
        self.cache = reading
        self.last_update = now
        self.error_count = 0
        
        logger.info(f"🌍☀️ Space Weather Update: Kp={kp_index:.1f} ({kp_category}), Wind={solar_wind_speed:.0f}km/s, Sources={', '.join(active_sources)}")
        return reading
    
    def _fetch_kp_index(self) -> Optional[Dict]:
        """Fetch current Kp index from NOAA"""
        try:
            resp = requests.get(NOAA_KP_INDEX_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            # Parse CSV format: skip header (1 row), get latest entry
            if len(data) > 1:
                latest = data[-1]
                # Format: [date, time, kp_index, ...]
                kp = float(latest[2]) if len(latest) > 2 else 3.0
                return {'current_kp': kp}
        except Exception as e:
            logger.debug(f"Kp fetch error: {e}")
        return None
    
    def _fetch_solar_wind(self) -> Optional[Dict]:
        """Fetch solar wind data from NOAA"""
        try:
            resp = requests.get(NOAA_SOLAR_WIND_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            # Parse CSV format: skip header, get most recent
            if len(data) > 1:
                latest = data[-1]
                # Format: [date, time, density, temperature, Bz, speed, ...]
                if len(latest) > 5:
                    return {
                        'density': float(latest[2]) if latest[2] else 5.0,
                        'bz': float(latest[4]) if latest[4] else 0.0,
                        'speed': float(latest[5]) if latest[5] else 400.0,
                    }
        except Exception as e:
            logger.debug(f"Solar wind fetch error: {e}")
        return None
    
    def _fetch_3day_forecast(self) -> Optional[Dict]:
        """Fetch 3-day forecast from NOAA"""
        try:
            resp = requests.get(NOAA_3DAY_FORECAST_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            if data and '3dayforecast' in data:
                forecast = data['3dayforecast']
                # Find highest Kp expected
                max_kp = 0
                for day in forecast:
                    for kp_val in [float(day.get(k, 0)) for k in ['kp_1', 'kp_2', 'kp_3']]:
                        max_kp = max(max_kp, kp_val)
                
                return {'highest_kp_category': self._categorize_kp(max_kp)}
        except Exception as e:
            logger.debug(f"Forecast fetch error: {e}")
        return None
    
    def _fetch_solar_flares(self) -> int:
        """Fetch solar flares from NASA (requires API key)"""
        try:
            api_key = self._get_nasa_api_key()
            if not api_key:
                return 0
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')
            
            url = f"{NASA_DONKI_FLARE_URL}?startDate={yesterday}&endDate={today}&api_key={api_key}"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            return len(data) if isinstance(data, list) else 0
        except Exception as e:
            logger.debug(f"NASA flares fetch error: {e}")
        return 0
    
    def _categorize_kp(self, kp: float) -> str:
        """Categorize Kp index into trading-relevant categories"""
        if kp < 1:
            return 'Very Quiet'
        elif kp < 3:
            return 'Quiet'
        elif kp < 5:
            return 'Unsettled'
        elif kp < 6:
            return 'Active'
        elif kp < 7:
            return 'Minor Storm'
        elif kp < 8:
            return 'Major Storm'
        else:
            return 'Severe Storm'
    
    def _get_nasa_api_key(self) -> Optional[str]:
        """Get NASA API key from environment"""
        import os
        key = os.environ.get('NASA_API_KEY')
        if key and key != 'DEMO_KEY':
            return key
        return None
    
    def get_cosmic_score(self, reading: SpaceWeatherReading) -> float:
        """
        Convert space weather data into cosmic alignment score for Queen
        
        Range: 0.0 (very bad) to 1.0 (optimal)
        
        Scoring:
        - Kp Index: lower is better (Kp < 3 = good)
        - Solar wind: 350-450 km/s is optimal
        - Bz component: negative is better for auroras, but neutral is stable
        """
        score = 0.5  # Start at neutral
        
        # Kp Index impact (most important)
        # Kp 0-2 = quiet (good) -> +0.3
        # Kp 3-4 = unsettled -> neutral
        # Kp 5+ = storm -> -0.2 to -0.3
        if reading.kp_index < 3:
            score += 0.3
        elif reading.kp_index >= 7:
            score -= 0.3
        elif reading.kp_index >= 5:
            score -= 0.15
        
        # Solar wind speed (moderate variation is good)
        wind = reading.solar_wind_speed
        if 350 <= wind <= 450:
            score += 0.2  # Optimal range
        elif 250 <= wind <= 550:
            score += 0.1  # Acceptable
        elif wind < 250 or wind > 600:
            score -= 0.1  # Extreme values = instability
        
        # Bz component (south/negative is risky for communications)
        bz = reading.bz_component
        if -2 <= bz <= 2:
            score += 0.1  # Neutral/stable
        elif bz < -5:
            score -= 0.15  # Strong south component = substorm risk
        
        # Solar flares (count impacts confidence)
        if reading.solar_flares_24h > 2:
            score -= 0.1  # Multiple flares = unpredictable
        
        # Clamp to 0-1
        return max(0.0, min(1.0, score))


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_bridge_instance: Optional[SpaceWeatherBridge] = None

def get_space_weather_bridge() -> SpaceWeatherBridge:
    """Get or create the global Space Weather Bridge"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = SpaceWeatherBridge()
    return _bridge_instance

def get_live_space_weather(force_refresh: bool = False) -> SpaceWeatherReading:
    """Get live space weather data"""
    bridge = get_space_weather_bridge()
    return bridge.get_live_data(force_refresh=force_refresh)

def get_cosmic_alignment_from_space_weather(force_refresh: bool = False) -> float:
    """
    Get cosmic alignment score based on REAL space weather data
    This is what the Queen should use!
    """
    bridge = get_space_weather_bridge()
    reading = bridge.get_live_data(force_refresh=force_refresh)
    return bridge.get_cosmic_score(reading)


if __name__ == '__main__':
    # Test it
    logging.basicConfig(level=logging.DEBUG)
    bridge = get_space_weather_bridge()
    
    print("\n🌍☀️ TESTING SPACE WEATHER BRIDGE 🌍☀️\n")
    
    reading = get_live_space_weather(force_refresh=True)
    print(f"Kp Index: {reading.kp_index:.1f} ({reading.kp_category})")
    print(f"Solar Wind: {reading.solar_wind_speed:.0f} km/s")
    print(f"Bz Component: {reading.bz_component:.1f} nT")
    print(f"Active Sources: {', '.join(reading.active_sources)}")
    
    cosmic_score = bridge.get_cosmic_score(reading)
    print(f"👑 Cosmic Alignment Score: {cosmic_score:.0%}")
    print(f"   (Queen should use this for trading confidence!)")
