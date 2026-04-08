#!/usr/bin/env python3
"""
🌍 QUEEN FIRM GEOCODER
Geographic coordinates for all 37 tracked trading firms
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
# HQ Coordinates for all tracked firms (lat, lon)
FIRM_COORDINATES = {
    # USA - New York
    "jane_street": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "two_sigma": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "hudson_river": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "tower_research": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "virtu": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "de_shaw": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "millennium": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    "renaissance": {"lat": 40.9176, "lon": -72.8334, "city": "Long Island", "country": "USA"},
    
    # USA - Chicago
    "citadel": {"lat": 41.8781, "lon": -87.6298, "city": "Chicago", "country": "USA"},
    "jump_trading": {"lat": 41.8781, "lon": -87.6298, "city": "Chicago", "country": "USA"},
    "drw": {"lat": 41.8781, "lon": -87.6298, "city": "Chicago", "country": "USA"},
    
    # USA - Connecticut
    "point72": {"lat": 41.0534, "lon": -73.5387, "city": "Stamford", "country": "USA"},
    "aqr": {"lat": 41.0262, "lon": -73.6282, "city": "Greenwich", "country": "USA"},
    "bridgewater": {"lat": 41.1415, "lon": -73.2107, "city": "Westport", "country": "USA"},
    
    # USA - Pennsylvania
    "susquehanna": {"lat": 40.0094, "lon": -75.2827, "city": "Bala Cynwyd", "country": "USA"},
    
    # Europe - London
    "gsa_capital": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK"},
    "man_group": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK"},
    "winton": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK"},
    "wintermute": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK"},
    
    # Europe - Amsterdam
    "optiver": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "country": "Netherlands"},
    "flow_traders": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "country": "Netherlands"},
    "imc": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "country": "Netherlands"},
    
    # Asia - Singapore
    "dbs_vickers": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore", "country": "Singapore"},
    "amber_group": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore", "country": "Singapore"},
    
    # Asia - Hong Kong
    "xtz": {"lat": 22.3193, "lon": 114.1694, "city": "Hong Kong", "country": "Hong Kong"},
    "hashkey": {"lat": 22.3193, "lon": 114.1694, "city": "Hong Kong", "country": "Hong Kong"},
    
    # Asia - South Korea
    "dunamu": {"lat": 37.5665, "lon": 126.9780, "city": "Seoul", "country": "South Korea"},
    
    # Asia - Japan
    "bitflyer": {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo", "country": "Japan"},
    
    # Middle East - Dubai
    "bitdubai": {"lat": 25.2048, "lon": 55.2708, "city": "Dubai", "country": "UAE"},
    
    # Crypto Native (Remote/Decentralized)
    "paradigm": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco", "country": "USA"},
    "electric_capital": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco", "country": "USA"},
    "multicoin": {"lat": 30.2672, "lon": -97.7431, "city": "Austin", "country": "USA"},
    "polychain": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco", "country": "USA"},
    "coinshares": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK"},
    "cumberland": {"lat": 41.8781, "lon": -87.6298, "city": "Chicago", "country": "USA"},
    "galaxy_digital": {"lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA"},
    
    # Ghosts (Defunct but patterns remain)
    "alameda_ghost": {"lat": 25.0443, "lon": -77.3504, "city": "Nassau", "country": "Bahamas"},
    "three_arrows_ghost": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore", "country": "Singapore"},
}


def get_firm_coordinates(firm_id: str) -> dict:
    """Get coordinates for a firm"""
    return FIRM_COORDINATES.get(firm_id.lower(), {
        "lat": 0, "lon": 0, "city": "Unknown", "country": "Unknown"
    })


def get_all_firm_locations() -> list:
    """Get all firm locations for map rendering"""
    locations = []
    for firm_id, coords in FIRM_COORDINATES.items():
        locations.append({
            'firm_id': firm_id,
            **coords
        })
    return locations


def get_regional_summary() -> dict:
    """Summarize firms by region"""
    regions = {}
    for firm_id, coords in FIRM_COORDINATES.items():
        country = coords['country']
        if country not in regions:
            regions[country] = []
        regions[country].append(firm_id)
    
    return {
        region: {
            'count': len(firms),
            'firms': firms
        }
        for region, firms in regions.items()
    }
