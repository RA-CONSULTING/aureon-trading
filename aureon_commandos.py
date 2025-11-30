#!/usr/bin/env python3
"""
🦆⚔️ QUANTUM QUACKERS COMMANDO PATTERNS ⚔️🦆
==========================================

Battle-tested animal warfare strategies from Quantum Quackers TypeScript system

COMMANDOS:
  🦁 LION HUNT - Full pride scan, adaptive target switching
  🐺 LONE WOLF - Single momentum sniper
  🐜 ARMY ANTS - Floor scavenger for small quick trades
  🐝 HUMMINGBIRD - Quick pollination rotations

Gary Leckey's Animal Army | November 2025
"""

import logging
import math
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 🦁 PRIDE SCANNER - Lion's Territory Mapping
# ═══════════════════════════════════════════════════════════════════════════

class PrideScanner:
    """
    Scans ALL trading pairs for best opportunities (LION COMMANDO)
    Ported from scripts/prideScanner.ts
    
    Flow:
      1. Get all 24h tickers from Binance
      2. Filter by volume + volatility thresholds
      3. Calculate opportunity score = volume × |change%|
      4. Return top opportunities sorted by score
    """
    
    def __init__(self, client):
        self.client = client
        self.pride_map = {"eth_pairs": [], "usdt_pairs": [], "cross_pairs": []}
    
    def scan_pride(self, min_volume_usd=100000, min_volatility=2.0, quote_assets=None) -> List[Dict]:
        """
        Scan entire market for hunting targets
        
        Returns list of dicts with:
          - symbol
          - volume_usd (24h quote volume)
          - change_pct (24h price change %)
          - opportunity_score (volume × volatility)
          - price
        """
        if quote_assets is None:
            quote_assets = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB']
        
        try:
            tickers = self.client.get_24h_tickers()
            targets = []
            
            for t in tickers:
                sym = t.get('symbol', '')
                # Check if symbol ends with any allowed quote asset
                if not any(sym.endswith(q) for q in quote_assets):
                    continue
                
                vol = float(t.get('quoteVolume', 0))
                change = abs(float(t.get('priceChangePercent', 0)))
                
                if vol > min_volume_usd and change > min_volatility:
                    # Opportunity score = volume × volatility (normalized)
                    score = (vol / 1000000) * change
                    
                    targets.append({
                        'symbol': sym,
                        'volume_usd': vol,
                        'change_pct': float(t.get('priceChangePercent', 0)),
                        'opportunity_score': score,
                        'price': float(t.get('lastPrice', 0))
                    })
            
            # Sort by opportunity score (highest first)
            targets.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            logger.info(f"🦁 PRIDE SCAN: Found {len(targets)} hunting targets")
            return targets[:50]  # Top 50 opportunities
            
        except Exception as e:
            logger.error(f"Pride scan error: {e}")
            return []
    
    def get_top_prey(self, n=10) -> List[str]:
        """Get top N prey symbols"""
        targets = self.scan_pride()
        return [t['symbol'] for t in targets[:n]]


# ═══════════════════════════════════════════════════════════════════════════
# 🐺 LONE WOLF - Momentum Hunter
# ═══════════════════════════════════════════════════════════════════════════

class LoneWolf:
    """
    Single momentum sniper (LONE WOLF COMMANDO)
    Ported from scripts/loneWolf.ts
    
    Strategy:
      - Scans universe for highest momentum (price change %)
      - Weights by log(volume) for liquidity
      - Returns single best momentum champion
    """
    
    def __init__(self, client):
        self.client = client
        self.last_kill = None
    
    def pick_momentum_prey(self, universe: List[str]) -> Optional[Dict]:
        """
        Select highest momentum target from universe
        
        Scoring: momentum × log(1 + volume)
        Returns dict with symbol, score, momentum
        """
        best = {'symbol': None, 'score': -999999, 'momentum': 0}
        
        for sym in universe:
            try:
                stats = self.client.get_24h_ticker(sym)
                momentum = float(stats.get('priceChangePercent', 0))
                volume = float(stats.get('quoteVolume', 0))
                
                # Score = momentum weighted by log volume
                score = momentum * math.log(1 + max(1, volume))
                
                if score > best['score']:
                    best = {
                        'symbol': sym,
                        'score': score,
                        'momentum': momentum,
                        'volume': volume
                    }
                    
            except Exception as e:
                logger.debug(f"Wolf prey check failed for {sym}: {e}")
                continue
        
        if best['symbol']:
            logger.info(f"🐺 WOLF TARGET: {best['symbol']} (momentum={best['momentum']:.2f}%, score={best['score']:.1f})")
            self.last_kill = best
        
        return best if best['symbol'] else None


# ═══════════════════════════════════════════════════════════════════════════
# 🐜 ARMY ANTS - Floor Scavengers
# ═══════════════════════════════════════════════════════════════════════════

class ArmyAnts:
    """
    Floor scavenger for small quick trades (ARMY ANTS COMMANDO)
    Ported from scripts/armyAnts.ts
    
    Strategy:
      - Find small liquid alts with volume > $50K
      - Target quick rotations with tight TP/SL
      - Collect scraps from the floor
    """
    
    def __init__(self, client):
        self.client = client
        self.scavenge_history = []
    
    def find_scraps(self, min_notional=11, min_volume=50000, quote_assets=None) -> List[Dict]:
        """
        Find small liquid opportunities on the floor
        
        Returns list of dicts with:
          - symbol
          - price
          - volume (24h quote volume)
        """
        if quote_assets is None:
            quote_assets = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB']
        
        # Define stablecoins to avoid stablecoin-to-stablecoin pairs
        stablecoins = {'USDT', 'USDC', 'BUSD', 'TUSD', 'USDP', 'DAI', 'FDUSD'}
        
        try:
            tickers = self.client.get_24h_tickers()
            scraps = []
            
            for t in tickers:
                sym = t.get('symbol', '')
                
                # Check if symbol ends with any allowed quote asset
                quote_match = None
                for q in quote_assets:
                    if sym.endswith(q):
                        quote_match = q
                        break
                
                if not quote_match:
                    continue
                
                # Skip stablecoin-to-stablecoin pairs (e.g., USDCUSDT)
                base = sym[:-len(quote_match)]
                if base in stablecoins and quote_match in stablecoins:
                    continue
                
                price = float(t.get('lastPrice', 0))
                volume = float(t.get('quoteVolume', 0))
                
                # Small liquid alts: volume > threshold, affordable notional
                if volume > min_volume and price * min_notional < volume:
                    scraps.append({
                        'symbol': sym,
                        'price': price,
                        'volume': volume
                    })
            
            # Sort by volume (most liquid first)
            scraps.sort(key=lambda x: x['volume'], reverse=True)
            
            logger.info(f"🐜 ANTS FOUND: {len(scraps)} scraps on the floor")
            return scraps[:20]
            
        except Exception as e:
            logger.error(f"Scrap finding error: {e}")
            return []
    
    def record_scavenge(self, symbol: str, profit: float):
        """Record a scavenging result"""
        self.scavenge_history.append({
            'symbol': symbol,
            'profit': profit,
            'timestamp': datetime.now().isoformat()
        })


# ═══════════════════════════════════════════════════════════════════════════
# 🐝 HUMMINGBIRD - Pollination Rotator
# ═══════════════════════════════════════════════════════════════════════════

class Hummingbird:
    """
    Quick pollination rotations (HUMMINGBIRD COMMANDO)
    Ported from scripts/hummingbird.ts
    
    Strategy:
      - Quick in-and-out rotations
      - Tight TP/SL for rapid nectar collection
      - Grows the hive incrementally
    """
    
    def __init__(self, client):
        self.client = client
        self.nectar_collected = 0.0
        self.flights = 0
    
    def pollinate(self, symbol: str, spend_usd=12, tp=0.006, sl=-0.005) -> Dict:
        """
        Plan a quick rotation trade
        
        Returns dict with:
          - symbol
          - tp (take profit %)
          - sl (stop loss %)
          - spend (USD amount)
        """
        self.flights += 1
        
        return {
            'symbol': symbol,
            'tp': tp,
            'sl': sl,
            'spend': spend_usd,
            'flight_number': self.flights
        }
    
    def collect_nectar(self, profit: float):
        """Record nectar collected from a successful flight"""
        self.nectar_collected += profit
        logger.info(f"🐝 NECTAR COLLECTED: +${profit:.2f} (total=${self.nectar_collected:.2f})")


# ═══════════════════════════════════════════════════════════════════════════
# 🦁 LION HUNT PATTERN - Adaptive Target Switching
# ═══════════════════════════════════════════════════════════════════════════

class LionHunt:
    """
    Continuous adaptive multi-symbol trading (LION HUNT COMMANDO)
    Ported from scripts/lionHunt.ts
    
    Flow:
      1. Pride Scanner → Maps all pairs, scores by opportunity
      2. Select Best Prey → Highest volatility × volume
      3. Hunt Target → Execute trades with consciousness
      4. Return to Pride → Repeat
    """
    
    def __init__(self, client, scanner: PrideScanner):
        self.client = client
        self.scanner = scanner
        self.hunt_count = 0
        self.current_prey = None
    
    def select_prey(self, targets: List[Dict], elephant_memory=None) -> Optional[Dict]:
        """
        Select best prey from targets
        
        Filters out:
          - Elephant memory cooldowns
          - Recently failed hunts
        
        Returns best available target
        """
        if elephant_memory:
            targets = [t for t in targets if not elephant_memory.should_avoid(t['symbol'])]
        
        if not targets:
            return None
        
        # Select highest opportunity score
        prey = targets[0]
        self.current_prey = prey
        self.hunt_count += 1
        
        logger.info(f"🦁 HUNT #{self.hunt_count} - Selected: {prey['symbol']} (score={prey['opportunity_score']:.1f})")
        return prey
    
    def calculate_opportunity(self, target: Dict) -> float:
        """Calculate opportunity score for a target"""
        volatility = abs(target.get('change_pct', 0))
        volume = target.get('volume_usd', 0) / 1000000  # In millions
        return volatility * volume * 100


# ═══════════════════════════════════════════════════════════════════════════
# 🦆 COMMANDO CONTROLLER - Unified Command
# ═══════════════════════════════════════════════════════════════════════════

class QuackCommandos:
    """
    Unified controller for all Quack Commandos - DYNAMIC ECOSYSTEM
    
    Coordinates:
      🦁 Lion - Pride scanning & adaptive switching (reserved slots)
      🐺 Wolf - Momentum hunting (reserved slots)
      🐜 Ants - Floor scavenging (reserved slots)
      🐝 Hummingbird - Pollination rotations (reserved slots)
    
    Each commando gets reserved slots and can borrow from idle commandos!
    """
    
    def __init__(self, client, config=None):
        self.client = client
        self.config = config or {}
        
        # Initialize commandos
        self.pride_scanner = PrideScanner(client)
        self.lone_wolf = LoneWolf(client)
        self.army_ants = ArmyAnts(client)
        self.hummingbird = Hummingbird(client)
        self.lion_hunt = LionHunt(client, self.pride_scanner)
        
        # 🦆⚔️ DYNAMIC ECOSYSTEM SLOT TRACKING ⚔️🦆
        self.slot_config = {
            'lion': self.config.get('LION_SLOTS', 3),
            'wolf': self.config.get('WOLF_SLOTS', 2),
            'ants': self.config.get('ANTS_SLOTS', 1),
            'hummingbird': self.config.get('HUMMINGBIRD_SLOTS', 1),
        }
        self.allow_borrowing = self.config.get('ALLOW_SLOT_BORROWING', True)
        
        # Track which positions belong to which commando
        self.position_owners: Dict[str, str] = {}  # symbol -> commando name
        
        # Track commando activity for slot borrowing
        self.last_activity = {
            'lion': 0,
            'wolf': 0,
            'ants': 0,
            'hummingbird': 0,
        }
        self.idle_threshold = 120  # Seconds before considered idle
        
        logger.info(f"🦆 QUACK COMMANDOS DEPLOYED! Ecosystem: Lion={self.slot_config['lion']}, Wolf={self.slot_config['wolf']}, Ants={self.slot_config['ants']}, Hummingbird={self.slot_config['hummingbird']}")
    
    def get_commando_targets(self, elephant_memory=None, allowed_quotes=None) -> Dict:
        """
        Get targets from all commandos
        
        Returns dict with:
          - pride_targets: Top opportunities from Lion
          - wolf_prey: Momentum champion from Wolf
          - ant_scraps: Floor scraps from Ants
          - best_prey: Lion's selected target
        """
        # 🦁 Lion: Full pride scan with allowed quote assets
        pride_targets = self.pride_scanner.scan_pride(quote_assets=allowed_quotes)
        
        # 🐺 Wolf: Pick momentum champion
        wolf_universe = [p['symbol'] for p in pride_targets[:20]]
        wolf_prey = self.lone_wolf.pick_momentum_prey(wolf_universe) if wolf_universe else None
        
        # 🐜 Ants: Find floor scraps with allowed quotes
        ant_scraps = self.army_ants.find_scraps(quote_assets=allowed_quotes)
        
        # 🦁 Lion: Select best prey
        best_prey = self.lion_hunt.select_prey(pride_targets, elephant_memory)
        
        return {
            'pride_targets': pride_targets,
            'wolf_prey': wolf_prey,
            'ant_scraps': ant_scraps,
            'best_prey': best_prey
        }
    
    def calculate_commando_boost(self, symbol: str, commando_targets: Dict) -> float:
        """
        Calculate boost multiplier from commando intelligence
        
        Returns multiplier >= 1.0
        """
        boost = 1.0
        
        pride_targets = commando_targets.get('pride_targets', [])
        wolf_prey = commando_targets.get('wolf_prey')
        ant_scraps = commando_targets.get('ant_scraps', [])
        
        # 🦁 LION: Top 10 pride targets get +20% boost
        for i, target in enumerate(pride_targets[:10]):
            if target['symbol'] == symbol:
                boost += 0.20
                logger.info(f"🦁 LION BOOST: {symbol} in top {i+1} pride targets (+20%)")
                break
        
        # 🐺 WOLF: Momentum champion gets +25% boost
        if wolf_prey and wolf_prey['symbol'] == symbol:
            boost += 0.25
            logger.info(f"🐺 WOLF BOOST: {symbol} is momentum champion (+25%, momentum={wolf_prey['momentum']:.2f}%)")
        
        # 🐜 ANTS: Floor scraps get +15% boost
        if any(s['symbol'] == symbol for s in ant_scraps):
            boost += 0.15
            logger.info(f"🐜 ANTS BOOST: {symbol} found on the floor (+15%)")
        
        return boost
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🦆⚔️ DYNAMIC ECOSYSTEM SLOT MANAGEMENT ⚔️🦆
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_active_slots(self, commando: str) -> int:
        """Count how many positions this commando currently owns"""
        return sum(1 for owner in self.position_owners.values() if owner == commando)
    
    def get_available_slots(self, commando: str) -> int:
        """Get slots available for this commando (own + borrowable)"""
        own_slots = self.slot_config.get(commando, 0)
        used_slots = self.get_active_slots(commando)
        base_available = own_slots - used_slots
        
        if not self.allow_borrowing:
            return max(0, base_available)
        
        # Check for borrowable slots from idle commandos
        import time
        now = time.time()
        borrowable = 0
        
        for other, other_slots in self.slot_config.items():
            if other == commando:
                continue
            
            # If other commando is idle, we can borrow their unused slots
            if now - self.last_activity.get(other, 0) > self.idle_threshold:
                other_used = self.get_active_slots(other)
                other_free = other_slots - other_used
                if other_free > 0:
                    borrowable += other_free
                    logger.debug(f"🔄 {commando} can borrow {other_free} slots from idle {other}")
        
        return max(0, base_available) + borrowable
    
    def can_enter(self, commando: str, current_total_positions: int, max_positions: int) -> bool:
        """Check if this commando can enter a new position"""
        # Global cap check
        if current_total_positions >= max_positions:
            return False
        
        # Commando-specific slot check
        available = self.get_available_slots(commando)
        return available > 0
    
    def record_entry(self, symbol: str, commando: str):
        """Record that a commando owns a position"""
        import time
        self.position_owners[symbol] = commando
        self.last_activity[commando] = time.time()
        logger.info(f"🦆 {commando.upper()} claimed {symbol} | Active slots: {self.get_active_slots(commando)}/{self.slot_config.get(commando, 0)}")
    
    def record_exit(self, symbol: str, pnl: float = 0.0):
        """Record that a position was closed"""
        commando = self.position_owners.pop(symbol, None)
        if commando:
            logger.info(f"🦆 {commando.upper()} released {symbol} (PnL: ${pnl:+.2f})")
            # Update commando-specific stats
            if commando == 'ants' and pnl != 0:
                self.army_ants.record_scavenge(symbol, pnl)
            elif commando == 'hummingbird' and pnl > 0:
                self.hummingbird.collect_nectar(pnl)
    
    def get_next_entry_recommendation(self, commando_targets: Dict, current_positions: set, 
                                       current_total: int, max_positions: int,
                                       elephant_memory=None) -> Optional[Dict]:
        """
        Get the next recommended entry from the dynamic ecosystem.
        Each commando competes for slots based on their strategy.
        
        Returns dict with:
          - symbol: Target symbol
          - commando: Which commando recommends it
          - reason: Why this target
          - score: Priority score
        """
        import time
        recommendations = []
        
        # 🦁 LION: Pride coherence-based entries
        if self.can_enter('lion', current_total, max_positions):
            pride = commando_targets.get('pride_targets', [])
            for i, target in enumerate(pride[:5]):
                sym = target['symbol']
                if sym not in current_positions:
                    if elephant_memory and elephant_memory.should_avoid(sym):
                        continue
                    recommendations.append({
                        'symbol': sym,
                        'commando': 'lion',
                        'reason': f"Pride #{i+1} (score={target['opportunity_score']:.1f})",
                        'score': target['opportunity_score'] * 1.0,  # Lion base weight
                        'price': target.get('price', 0),
                        'change': target.get('change_pct', 0),
                    })
            self.last_activity['lion'] = time.time()
        
        # 🐺 WOLF: Momentum champion entry
        if self.can_enter('wolf', current_total, max_positions):
            wolf = commando_targets.get('wolf_prey')
            if wolf and wolf['symbol'] not in current_positions:
                sym = wolf['symbol']
                if not (elephant_memory and elephant_memory.should_avoid(sym)):
                    recommendations.append({
                        'symbol': sym,
                        'commando': 'wolf',
                        'reason': f"Momentum champion (mom={wolf['momentum']:.1f}%)",
                        'score': wolf['score'] * 1.5,  # Wolf gets priority boost
                        'price': wolf.get('price', 0),
                        'change': wolf.get('momentum', 0),
                    })
            self.last_activity['wolf'] = time.time()
        
        # 🐜 ANTS: Floor scavenger entries
        if self.can_enter('ants', current_total, max_positions):
            scraps = commando_targets.get('ant_scraps', [])
            for scrap in scraps[:3]:
                sym = scrap['symbol']
                if sym not in current_positions:
                    if elephant_memory and elephant_memory.should_avoid(sym):
                        continue
                    # Ants prefer small, liquid, low volatility
                    vol_score = scrap['volume'] / 1000000  # Normalize volume
                    recommendations.append({
                        'symbol': sym,
                        'commando': 'ants',
                        'reason': f"Floor scrap (vol=${scrap['volume']/1000:.0f}k)",
                        'score': vol_score * 0.8,  # Ants slightly lower priority
                        'price': scrap.get('price', 0),
                        'change': 0,  # Ants don't care about change
                    })
            self.last_activity['ants'] = time.time()
        
        # 🐝 HUMMINGBIRD: Quick rotation entries (needs open slots)
        if self.can_enter('hummingbird', current_total, max_positions):
            # Hummingbird picks from lion's pride but with tight TP/SL
            pride = commando_targets.get('pride_targets', [])
            for target in pride[5:10]:  # Skip lion's top picks
                sym = target['symbol']
                if sym not in current_positions:
                    if elephant_memory and elephant_memory.should_avoid(sym):
                        continue
                    recommendations.append({
                        'symbol': sym,
                        'commando': 'hummingbird',
                        'reason': f"Quick rotation (volatility play)",
                        'score': target['opportunity_score'] * 0.7,  # Lower priority than lion
                        'price': target.get('price', 0),
                        'change': target.get('change_pct', 0),
                        'tp': 0.006,  # Tight TP
                        'sl': -0.005,  # Tight SL
                    })
            self.last_activity['hummingbird'] = time.time()
        
        if not recommendations:
            return None
        
        # Sort by score and return best
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        winner = recommendations[0]
        logger.info(f"🦆 ECOSYSTEM PICK: {winner['commando'].upper()} → {winner['symbol']} ({winner['reason']})")
        
        return winner
    
    def get_status(self) -> str:
        """Get commando status report with ecosystem slots"""
        import time
        now = time.time()
        
        def slot_status(commando):
            active = self.get_active_slots(commando)
            total = self.slot_config.get(commando, 0)
            idle = "🔴" if now - self.last_activity.get(commando, 0) > self.idle_threshold else "🟢"
            return f"{idle} {active}/{total}"
        
        return f"""
🦆 QUACK COMMANDOS ECOSYSTEM STATUS:
  🦁 LION:        {slot_status('lion')} slots | Hunt #{self.lion_hunt.hunt_count} | Current: {self.lion_hunt.current_prey['symbol'] if self.lion_hunt.current_prey else 'None'}
  🐺 WOLF:        {slot_status('wolf')} slots | Last Kill: {self.lone_wolf.last_kill['symbol'] if self.lone_wolf.last_kill else 'None'}
  🐜 ANTS:        {slot_status('ants')} slots | Scavenged {len(self.army_ants.scavenge_history)} scraps
  🐝 HUMMINGBIRD: {slot_status('hummingbird')} slots | Flights={self.hummingbird.flights} | Nectar=${self.hummingbird.nectar_collected:.2f}
"""
