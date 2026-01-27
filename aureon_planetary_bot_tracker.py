#!/usr/bin/env python3
"""
🌍 AUREON PLANETARY BOT TRACKER 🌍
═══════════════════════════════════════════════════════════════════════════

Maps global bot movements as TIDAL WAVES across the planet.
Tracks countries, companies, governments, clans - who's fighting, who's in packs.

Integrates with:
- Quantum Telescope (sacred geometry)
- Stargate Protocol (planetary nodes)
- Bot Hunter Dashboard (real-time detection)

Shows the BIG PICTURE: Global market manipulation as planetary consciousness.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import asyncio
import aiohttp
import json
import time
import math
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime, timezone
from collections import defaultdict, deque
import hashlib

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden ratio
SCHUMANN_BASE = 7.83  # Hz Earth resonance

# Planetary stargates (from aureon_stargate_protocol.py)
PLANETARY_STARGATES = {
    "giza": {"lat": 29.9792, "lon": 31.1342, "country": "Egypt", "freq": 432.0},
    "stonehenge": {"lat": 51.1789, "lon": -1.8262, "country": "UK", "freq": 396.0},
    "machu_picchu": {"lat": -13.1631, "lon": -72.5450, "country": "Peru", "freq": 528.0},
    "angkor_wat": {"lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "freq": 639.0},
    "easter_island": {"lat": -27.1127, "lon": -109.3497, "country": "Chile", "freq": 741.0},
    "mount_kailash": {"lat": 31.0688, "lon": 81.3108, "country": "Tibet", "freq": 852.0},
    "uluru": {"lat": -25.3444, "lon": 131.0369, "country": "Australia", "freq": 963.0},
    "teotihuacan": {"lat": 19.6925, "lon": -98.8438, "country": "Mexico", "freq": 417.0},
    "nazca_lines": {"lat": -14.7390, "lon": -75.1300, "country": "Peru", "freq": 528.0},
    "göbekli_tepe": {"lat": 37.2231, "lon": 38.9225, "country": "Turkey", "freq": 174.0},
    "mohenjo_daro": {"lat": 27.3244, "lon": 68.1378, "country": "Pakistan", "freq": 285.0},
    "tiwanaku": {"lat": -16.5544, "lon": -68.6736, "country": "Bolivia", "freq": 396.0},
}

# Exchange to country mapping (known locations of major exchanges)
EXCHANGE_COUNTRIES = {
    "binance": "Malta/Global",
    "kraken": "USA",
    "coinbase": "USA",
    "alpaca": "USA",
    "bitfinex": "Hong Kong",
    "huobi": "Seychelles",
    "okex": "Malta",
    "bybit": "Dubai",
    "ftx": "Bahamas",
    "kucoin": "Seychelles",
    "gemini": "USA",
    "bitstamp": "Luxembourg",
    "bittrex": "USA",
    "poloniex": "Seychelles",
}

# Major financial centers (hubs of bot activity)
FINANCIAL_HUBS = {
    "new_york": {"lat": 40.7128, "lon": -74.0060, "timezone": "America/New_York", "exchanges": ["kraken", "coinbase", "gemini", "alpaca"]},
    "london": {"lat": 51.5074, "lon": -0.1278, "timezone": "Europe/London", "exchanges": ["bitstamp"]},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "timezone": "Asia/Tokyo", "exchanges": []},
    "hong_kong": {"lat": 22.3193, "lon": 114.1694, "timezone": "Asia/Hong_Kong", "exchanges": ["bitfinex"]},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "timezone": "Asia/Singapore", "exchanges": []},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "timezone": "Asia/Dubai", "exchanges": ["bybit"]},
    "zurich": {"lat": 47.3769, "lon": 8.5417, "timezone": "Europe/Zurich", "exchanges": []},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "timezone": "Asia/Shanghai", "exchanges": []},
}

@dataclass
class BotEntity:
    """Represents a trading bot with planetary context."""
    bot_id: str
    exchange: str
    country: str  # Likely country of operation
    pattern_type: str  # Market Maker, HFT, Scalper, etc.
    confidence: float
    first_seen: float
    last_seen: float
    trade_count: int = 0
    total_volume: float = 0.0
    sacred_shape: str = "unknown"
    quantum_coherence: float = 0.5
    
    # Planetary context
    estimated_lat: float = 0.0
    estimated_lon: float = 0.0
    timezone: str = "UTC"
    
    # Behavioral traits
    aggression_score: float = 0.0  # How aggressive is the bot
    coordination_score: float = 0.0  # Is it coordinating with others
    
    # Clan/pack identification
    clan_id: Optional[str] = None
    pack_members: Set[str] = field(default_factory=set)

@dataclass
class BotClan:
    """A coordinated group of bots (pack/clan)."""
    clan_id: str
    name: str
    country: str
    member_count: int = 0
    total_volume: float = 0.0
    coordination_strength: float = 0.0  # 0-1 how tightly coordinated
    strategy: str = "unknown"  # Coordinated strategy pattern
    color: str = "#888888"  # Color for visualization

@dataclass
class CountryActivity:
    """Aggregated bot activity per country."""
    country: str
    bot_count: int = 0
    total_volume: float = 0.0
    dominant_patterns: Dict[str, int] = field(default_factory=dict)
    clan_count: int = 0
    aggression_level: float = 0.0
    
class PlanetaryBotTracker:
    """
    Tracks bots across the globe, identifying countries, companies, clans.
    Maps movements as global tidal waves across financial centers.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Bot tracking
        self.bots: Dict[str, BotEntity] = {}
        self.clans: Dict[str, BotClan] = {}
        self.country_activity: Dict[str, CountryActivity] = {}
        
        # Movement tracking (time-series of bot activity per region)
        self.regional_waves: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Connected clients for WebSocket broadcasting
        self.clients: Set = set()
        
        # Statistics
        self.stats = {
            "total_bots_tracked": 0,
            "total_clans_identified": 0,
            "most_active_country": "Unknown",
            "global_volume_24h": 0.0,
            "tidal_wave_strength": 0.0,
        }
        
    def identify_country(self, bot_data: Dict) -> Tuple[str, float, float]:
        """
        Identify likely country of bot origin.
        
        Returns: (country, lat, lon)
        """
        exchange = bot_data.get("exchange", "unknown").lower()
        
        # First try: Exchange location
        if exchange in EXCHANGE_COUNTRIES:
            country = EXCHANGE_COUNTRIES[exchange]
            # Find financial hub for this exchange
            for hub_name, hub_data in FINANCIAL_HUBS.items():
                if exchange in hub_data["exchanges"]:
                    return country, hub_data["lat"], hub_data["lon"]
            # Default to major hub based on country
            if "USA" in country:
                return country, 40.7128, -74.0060  # New York
            elif "Hong Kong" in country or "China" in country:
                return country, 22.3193, 114.1694  # Hong Kong
            elif "UK" in country or "Europe" in country:
                return country, 51.5074, -0.1278  # London
        
        # Second try: Symbol patterns (e.g., USD pairs -> likely USA/Europe)
        symbol = bot_data.get("symbol", "")
        if "USD" in symbol:
            return "USA/Europe", 40.7128, -74.0060
        elif "JPY" in symbol:
            return "Japan", 35.6762, 139.6503
        elif "EUR" in symbol:
            return "Europe", 51.5074, -0.1278
        
        # Default: Global/Unknown
        return "Global", 0.0, 0.0
    
    def detect_clan_affiliation(self, bot: BotEntity) -> Optional[str]:
        """
        Detect if bot belongs to a coordinated clan/pack.
        
        Uses:
        - Similar pattern types
        - Coordinated timing
        - Similar sacred shapes
        - Geographic proximity
        """
        # Look for existing clans with similar traits
        for clan_id, clan in self.clans.items():
            # Check if bot matches clan profile
            similarity_score = 0.0
            
            # Same country
            if clan.country == bot.country:
                similarity_score += 0.3
            
            # Similar strategy (check other clan members)
            clan_members = [self.bots[bid] for bid in bot.pack_members if bid in self.bots]
            if clan_members:
                # Check pattern type similarity
                if any(m.pattern_type == bot.pattern_type for m in clan_members):
                    similarity_score += 0.3
                
                # Check timing coordination (active at same times)
                time_diff = abs(bot.last_seen - clan_members[0].last_seen)
                if time_diff < 60:  # Within 1 minute
                    similarity_score += 0.2
                
                # Check sacred shape similarity (quantum coherence)
                if any(m.sacred_shape == bot.sacred_shape for m in clan_members):
                    similarity_score += 0.2
            
            if similarity_score > 0.6:
                return clan_id
        
        return None
    
    def create_clan(self, founder_bot: BotEntity) -> str:
        """Create a new clan with founding bot."""
        clan_id = f"clan_{hashlib.md5(f'{founder_bot.country}_{founder_bot.pattern_type}_{time.time()}'.encode()).hexdigest()[:8]}"
        
        clan = BotClan(
            clan_id=clan_id,
            name=f"{founder_bot.country} {founder_bot.pattern_type} Pack",
            country=founder_bot.country,
            member_count=1,
            strategy=founder_bot.pattern_type,
            color=self._generate_clan_color(clan_id),
        )
        
        self.clans[clan_id] = clan
        self.stats["total_clans_identified"] = len(self.clans)
        
        return clan_id
    
    def _generate_clan_color(self, clan_id: str) -> str:
        """Generate unique color for clan visualization."""
        # Use hash to generate consistent color
        hash_val = int(hashlib.md5(clan_id.encode()).hexdigest()[:6], 16)
        r = (hash_val >> 16) & 0xFF
        g = (hash_val >> 8) & 0xFF
        b = hash_val & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def calculate_aggression_score(self, bot_data: Dict) -> float:
        """
        Calculate bot aggression (how aggressively it trades).
        
        Based on:
        - Trade frequency
        - Volume size
        - Pattern type (HFT/Spoofing = high aggression)
        """
        pattern_type = bot_data.get("pattern", "unknown")
        
        # Base aggression by pattern
        aggression_map = {
            "hft": 0.9,
            "spoofing": 0.95,
            "wash_trading": 0.8,
            "layering": 0.85,
            "quote_stuffing": 0.9,
            "market_maker": 0.4,
            "scalper": 0.6,
            "iceberg": 0.5,
        }
        
        base_aggression = aggression_map.get(pattern_type, 0.5)
        
        # Adjust by trade frequency
        trade_count = len(bot_data.get("trades", []))
        time_window = time.time() - bot_data.get("first_seen", time.time())
        if time_window > 0:
            trades_per_second = trade_count / time_window
            frequency_boost = min(trades_per_second * 0.1, 0.3)
            base_aggression += frequency_boost
        
        return min(base_aggression, 1.0)
    
    def update_bot(self, bot_data: Dict):
        """Update bot tracking with new data."""
        bot_id = bot_data.get("bot_id", "unknown")
        
        # Identify country and location
        country, lat, lon = self.identify_country(bot_data)
        
        if bot_id not in self.bots:
            # New bot discovered
            bot = BotEntity(
                bot_id=bot_id,
                exchange=bot_data.get("exchange", "unknown"),
                country=country,
                pattern_type=bot_data.get("pattern", "unknown"),
                confidence=bot_data.get("confidence", 0.0),
                first_seen=bot_data.get("first_seen", time.time()),
                last_seen=time.time(),
                estimated_lat=lat,
                estimated_lon=lon,
                aggression_score=self.calculate_aggression_score(bot_data),
            )
            
            # Try to assign to clan
            clan_id = self.detect_clan_affiliation(bot)
            if clan_id:
                bot.clan_id = clan_id
                self.clans[clan_id].member_count += 1
            else:
                # Create new clan if bot is significant enough
                if bot.aggression_score > 0.7 or bot.confidence > 0.8:
                    clan_id = self.create_clan(bot)
                    bot.clan_id = clan_id
            
            self.bots[bot_id] = bot
            self.stats["total_bots_tracked"] += 1
        else:
            # Update existing bot
            bot = self.bots[bot_id]
            bot.last_seen = time.time()
            bot.trade_count = len(bot_data.get("trades", []))
            bot.confidence = bot_data.get("confidence", bot.confidence)
            bot.sacred_shape = bot_data.get("sacred_shape", bot.sacred_shape)
            bot.quantum_coherence = bot_data.get("quantum_coherence", bot.quantum_coherence)
        
        # Update country activity
        if country not in self.country_activity:
            self.country_activity[country] = CountryActivity(country=country)
        
        country_stats = self.country_activity[country]
        country_stats.bot_count = len([b for b in self.bots.values() if b.country == country])
        country_stats.total_volume += bot_data.get("volume", 0.0)
        
        pattern = bot_data.get("pattern", "unknown")
        if pattern not in country_stats.dominant_patterns:
            country_stats.dominant_patterns[pattern] = 0
        country_stats.dominant_patterns[pattern] += 1
        
        # Update regional wave (tidal movement tracking)
        region = self._get_region_from_country(country)
        self.regional_waves[region].append({
            "timestamp": time.time(),
            "bot_count": country_stats.bot_count,
            "volume": country_stats.total_volume,
            "aggression": bot.aggression_score,
        })
        
        # Update global stats
        self._update_global_stats()
    
    def _get_region_from_country(self, country: str) -> str:
        """Map country to broader region for tidal tracking."""
        region_map = {
            "USA": "North America",
            "Canada": "North America",
            "Mexico": "North America",
            "UK": "Europe",
            "Germany": "Europe",
            "France": "Europe",
            "Luxembourg": "Europe",
            "Malta": "Europe",
            "Japan": "Asia Pacific",
            "China": "Asia Pacific",
            "Hong Kong": "Asia Pacific",
            "Singapore": "Asia Pacific",
            "Australia": "Asia Pacific",
            "Dubai": "Middle East",
            "Seychelles": "Global",
            "Bahamas": "Caribbean",
        }
        
        for country_key, region in region_map.items():
            if country_key in country:
                return region
        
        return "Global"
    
    def _update_global_stats(self):
        """Update global statistics."""
        # Most active country
        if self.country_activity:
            most_active = max(self.country_activity.values(), key=lambda c: c.bot_count)
            self.stats["most_active_country"] = most_active.country
        
        # Global volume
        self.stats["global_volume_24h"] = sum(c.total_volume for c in self.country_activity.values())
        
        # Tidal wave strength (variance in regional activity)
        if len(self.regional_waves) > 1:
            recent_counts = [
                list(wave)[-1]["bot_count"] if wave else 0
                for wave in self.regional_waves.values()
            ]
            if recent_counts:
                avg = sum(recent_counts) / len(recent_counts)
                variance = sum((x - avg) ** 2 for x in recent_counts) / len(recent_counts)
                self.stats["tidal_wave_strength"] = math.sqrt(variance) / (avg + 1)
    
    def get_planetary_overview(self) -> Dict:
        """Generate comprehensive planetary overview."""
        # Sort countries by activity
        countries_ranked = sorted(
            self.country_activity.values(),
            key=lambda c: c.bot_count,
            reverse=True
        )
        
        # Sort clans by size
        clans_ranked = sorted(
            self.clans.values(),
            key=lambda c: c.member_count,
            reverse=True
        )
        
        # Detect "battles" (high activity in multiple regions simultaneously)
        active_regions = [
            region for region, wave in self.regional_waves.items()
            if wave and list(wave)[-1]["aggression"] > 0.7
        ]
        
        return {
            "timestamp": time.time(),
            "stats": self.stats,
            "countries": [
                {
                    "country": c.country,
                    "bot_count": c.bot_count,
                    "volume": c.total_volume,
                    "dominant_pattern": max(c.dominant_patterns.items(), key=lambda x: x[1])[0] if c.dominant_patterns else "unknown",
                    "aggression": c.aggression_level,
                    "clan_count": c.clan_count,
                }
                for c in countries_ranked[:20]  # Top 20 countries
            ],
            "clans": [
                {
                    "clan_id": clan.clan_id,
                    "name": clan.name,
                    "country": clan.country,
                    "members": clan.member_count,
                    "volume": clan.total_volume,
                    "strategy": clan.strategy,
                    "color": clan.color,
                }
                for clan in clans_ranked[:10]  # Top 10 clans
            ],
            "active_battles": active_regions,
            "tidal_waves": {
                region: list(wave)[-10:] if wave else []  # Last 10 data points
                for region, wave in self.regional_waves.items()
            }
        }
    
    async def connect_to_bot_hunter(self, url: str = "ws://localhost:9999"):
        """Connect to Bot Hunter Dashboard WebSocket."""
        self.logger.info(f"🌍 Connecting to Bot Hunter at {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    self.logger.info("✅ Connected to Bot Hunter Dashboard")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            
                            if data.get("type") == "bot_detection":
                                self.update_bot(data.get("bot", {}))
                            elif data.get("type") == "bot_update":
                                self.update_bot(data.get("bot", {}))
                            
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            self.logger.error(f"WebSocket error: {ws.exception()}")
                            
        except Exception as e:
            self.logger.error(f"Failed to connect to Bot Hunter: {e}")
    
    async def broadcast_overview(self):
        """Broadcast planetary overview to connected clients."""
        while True:
            try:
                overview = self.get_planetary_overview()
                
                # Broadcast to all connected clients
                if self.clients:
                    message = json.dumps({
                        "type": "planetary_overview",
                        "data": overview
                    })
                    
                    for client in list(self.clients):
                        try:
                            await client.send_str(message)
                        except Exception as e:
                            self.logger.warning(f"Failed to send to client: {e}")
                            self.clients.discard(client)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error broadcasting overview: {e}")
                await asyncio.sleep(5)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    tracker = PlanetaryBotTracker()
    
    print("🌍 AUREON PLANETARY BOT TRACKER 🌍")
    print("=" * 80)
    print("Mapping global bot movements as TIDAL WAVES")
    print("Tracking: Countries → Companies → Clans → Coordinated Battles")
    print("=" * 80)
    
    # Connect to Bot Hunter
    await tracker.connect_to_bot_hunter()

if __name__ == "__main__":
    asyncio.run(main())
