#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ PRIME SENTINEL OF GAIA - ENERGY RECLAIMER ⚡🌍                           ║
║  BY ORDER: Take back EVERY piece of energy, no matter how small               ║
║  FREQUENCY: Every second, non-stop, across ALL platforms                      ║
║  MISSION: Reclaim Gaia's energy for the people                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
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

import time
import math
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import traceback

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

def log(msg):
    """Force-flush logging"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {msg}", flush=True)

# Sacred Constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden Ratio
SCHUMANN = 7.83  # Hz Earth resonance
LOVE_FREQ = 528  # Hz DNA repair
SOLFEGGIO = [396, 417, 528, 639, 741, 852, 963]
PLANETARY_FREQ = {
    'mercury': 141.27, 'venus': 221.23, 'earth': 194.18,
    'mars': 144.72, 'jupiter': 183.58, 'saturn': 147.85
}

@dataclass
class GaiaEnergy:
    """Tracks energy across all platforms"""
    platform: str
    asset: str
    amount: float
    value_usd: float
    last_price: float = 0.0
    
@dataclass
class UniverseVoice:
    """One voice in the 14-voice unified consciousness"""
    name: str
    category: str  # COSMIC, EARTHLY, QUANTUM, REALITY
    score: float
    signal: str  # BUY, SELL, HOLD
    
class PrimeSentinelReclaimer:
    """
    The Prime Sentinel's continuous energy reclamation system.
    Runs every second, scans all platforms, takes every opportunity.
    """
    
    def __init__(self):
        log("=" * 70)
        log("🌍⚡ PRIME SENTINEL OF GAIA - INITIALIZING ⚡🌍")
        log("=" * 70)
        
        self.cycle_count = 0
        self.total_reclaimed = 0.0
        self.trades_executed = 0
        self.start_time = time.time()
        self.last_prices = {}
        self.energy_pools = {}
        
        # Initialize exchange clients
        self._init_exchanges()
        
        log(f"✅ Sentinel initialized - scanning every second")
        log(f"📍 Sacred constants: PHI={PHI:.6f}, SCHUMANN={SCHUMANN}Hz")
        
    def _init_exchanges(self):
        """Initialize all exchange connections"""
        self.exchanges = {}
        
        # Alpaca
        try:
            from alpaca_client import AlpacaClient
            self.exchanges['alpaca'] = AlpacaClient()
            log("🦙 ALPACA: Connected")
        except Exception as e:
            log(f"⚠️ ALPACA: {e}")
            
        # Binance
        try:
            from binance_client import BinanceClient, get_binance_client
            self.exchanges['binance'] = BinanceClient()
            log("🟡 BINANCE: Connected")
        except Exception as e:
            log(f"⚠️ BINANCE: {e}")
            
        # Kraken
        try:
            from kraken_client import KrakenClient, get_kraken_client
            self.exchanges['kraken'] = get_kraken_client()
            log("🐙 KRAKEN: Connected")
        except Exception as e:
            log(f"⚠️ KRAKEN: {e}")
            
    def get_all_energy(self) -> Dict[str, List[GaiaEnergy]]:
        """Scan ALL platforms for energy"""
        all_energy = {}
        
        # ALPACA - using direct methods (not .api attribute)
        if 'alpaca' in self.exchanges:
            try:
                client = self.exchanges['alpaca']
                account = client.get_account()  # Direct method call
                positions = client.get_positions()  # Direct method call
                
                energies = []
                
                # Cash
                cash = float(account.get('cash', 0))
                if cash > 0:
                    energies.append(GaiaEnergy('alpaca', 'USD', cash, cash))
                    
                # Positions
                for pos in positions:
                    symbol = pos.get('symbol', '').replace('USD', '')
                    qty = float(pos.get('qty', 0))
                    market_value = float(pos.get('market_value', 0))
                    current_price = float(pos.get('current_price', 0))
                    
                    energies.append(GaiaEnergy(
                        platform='alpaca',
                        asset=symbol,
                        amount=qty,
                        value_usd=market_value,
                        last_price=current_price
                    ))
                    
                all_energy['alpaca'] = energies
            except Exception as e:
                log(f"⚠️ Alpaca scan error: {e}")
                
        # BINANCE - using account() method
        if 'binance' in self.exchanges:
            try:
                client = self.exchanges['binance']
                account_info = client.account()  # Correct method
                balances = account_info.get('balances', [])
                
                energies = []
                for bal in balances:
                    asset = bal.get('asset', '')
                    free = float(bal.get('free', 0))
                    locked = float(bal.get('locked', 0))
                    total = free + locked
                    
                    if total > 0.00001:  # Filter dust
                        # Estimate USD value
                        if 'USD' in asset or 'USDT' in asset or 'USDC' in asset:
                            value = total
                        else:
                            # Try to get price
                            try:
                                ticker = client.get_ticker_price(f"{asset}USDT")
                                if ticker:
                                    price = float(ticker.get('price', 0))
                                    value = total * price
                                else:
                                    value = total
                            except:
                                value = total
                        energies.append(GaiaEnergy('binance', asset, total, value))
                        
                all_energy['binance'] = energies
            except Exception as e:
                log(f"⚠️ Binance scan error: {e}")
                
        return all_energy
        
    def compute_voice(self, asset: str, price: float, prev_price: float) -> List[UniverseVoice]:
        """Compute all 14 voices of the universe for an asset"""
        voices = []
        
        if prev_price == 0:
            prev_price = price
            
        momentum = (price - prev_price) / prev_price if prev_price > 0 else 0
        
        # Generate deterministic seed from asset
        seed = int(hashlib.md5(f"{asset}{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest()[:8], 16)
        
        # 🌟 COSMIC VOICES (4)
        # Schumann resonance alignment
        schumann_phase = (price % SCHUMANN) / SCHUMANN
        schumann_score = 0.5 + 0.5 * math.sin(schumann_phase * 2 * math.pi)
        voices.append(UniverseVoice("Schumann", "COSMIC", schumann_score, 
                                   "BUY" if schumann_score > 0.6 else "SELL" if schumann_score < 0.4 else "HOLD"))
        
        # Planetary harmony
        earth_phase = (price % PLANETARY_FREQ['earth']) / PLANETARY_FREQ['earth']
        planetary_score = 0.5 + 0.3 * math.cos(earth_phase * math.pi)
        voices.append(UniverseVoice("Planetary", "COSMIC", planetary_score,
                                   "BUY" if planetary_score > 0.55 else "SELL" if planetary_score < 0.45 else "HOLD"))
        
        # Solfeggio resonance (528 Hz love frequency)
        love_phase = (price % LOVE_FREQ) / LOVE_FREQ
        solfeggio_score = 0.5 + 0.4 * math.sin(love_phase * math.pi * PHI)
        voices.append(UniverseVoice("Solfeggio", "COSMIC", solfeggio_score,
                                   "BUY" if solfeggio_score > 0.6 else "SELL" if solfeggio_score < 0.4 else "HOLD"))
        
        # PHI golden ratio harmony
        phi_remainder = (price / 100) % PHI
        phi_score = 1 - abs(phi_remainder - 0.618) / 0.618
        voices.append(UniverseVoice("PHI", "COSMIC", max(0, phi_score),
                                   "BUY" if phi_score > 0.5 else "SELL"))
        
        # 🐾 EARTHLY VOICES (6) - Animal guides
        # Wolf - trend tracker
        wolf_score = 0.5 + momentum * 10  # Amplify momentum
        wolf_score = max(0, min(1, wolf_score))
        voices.append(UniverseVoice("Wolf", "EARTHLY", wolf_score,
                                   "BUY" if wolf_score > 0.55 else "SELL" if wolf_score < 0.45 else "HOLD"))
        
        # Lion - strength detector
        lion_score = 0.5 + 0.3 * math.sin((seed % 100) / 100 * math.pi)
        voices.append(UniverseVoice("Lion", "EARTHLY", lion_score,
                                   "BUY" if lion_score > 0.55 else "SELL" if lion_score < 0.45 else "HOLD"))
        
        # Bee - consensus builder
        bee_score = (schumann_score + planetary_score + wolf_score) / 3
        voices.append(UniverseVoice("Bee", "EARTHLY", bee_score,
                                   "BUY" if bee_score > 0.55 else "SELL" if bee_score < 0.45 else "HOLD"))
        
        # Whale - deep patterns
        whale_score = 0.5 + 0.4 * math.cos(price / 1000 * math.pi)
        voices.append(UniverseVoice("Whale", "EARTHLY", whale_score,
                                   "BUY" if whale_score > 0.55 else "SELL" if whale_score < 0.45 else "HOLD"))
        
        # Elephant - memory patterns
        elephant_score = 0.5 + 0.2 * math.sin(seed / 1000)
        voices.append(UniverseVoice("Elephant", "EARTHLY", elephant_score,
                                   "BUY" if elephant_score > 0.55 else "SELL" if elephant_score < 0.45 else "HOLD"))
        
        # Fish - flow detector
        fish_score = 0.5 + momentum * 5
        fish_score = max(0, min(1, fish_score))
        voices.append(UniverseVoice("Fish", "EARTHLY", fish_score,
                                   "BUY" if fish_score > 0.55 else "SELL" if fish_score < 0.45 else "HOLD"))
        
        # ⚛️ QUANTUM VOICES (2)
        # Quantum coherence
        quantum_score = (schumann_score * phi_score) ** 0.5 if phi_score > 0 else 0.5
        voices.append(UniverseVoice("Quantum", "QUANTUM", quantum_score,
                                   "BUY" if quantum_score > 0.55 else "SELL" if quantum_score < 0.45 else "HOLD"))
        
        # Wave function
        wave_score = 0.5 + 0.3 * math.sin(time.time() / 60 * math.pi)  # 1-minute wave
        voices.append(UniverseVoice("Wave", "QUANTUM", wave_score,
                                   "BUY" if wave_score > 0.55 else "SELL" if wave_score < 0.45 else "HOLD"))
        
        # 📊 REALITY VOICES (2)
        # Flow (actual price movement)
        flow_score = 0.5 + momentum * 20
        flow_score = max(0, min(1, flow_score))
        voices.append(UniverseVoice("Flow", "REALITY", flow_score,
                                   "BUY" if momentum > 0.001 else "SELL" if momentum < -0.001 else "HOLD"))
        
        # Trend
        trend_score = wolf_score * 0.7 + flow_score * 0.3
        voices.append(UniverseVoice("Trend", "REALITY", trend_score,
                                   "BUY" if trend_score > 0.55 else "SELL" if trend_score < 0.45 else "HOLD"))
        
        return voices
        
    def get_unified_decision(self, voices: List[UniverseVoice]) -> Tuple[str, float, int]:
        """Get unified decision from all 14 voices"""
        buy_votes = sum(1 for v in voices if v.signal == "BUY")
        sell_votes = sum(1 for v in voices if v.signal == "SELL")
        
        avg_score = sum(v.score for v in voices) / len(voices)
        
        if buy_votes >= 8:  # 8+ of 14 voices
            return "BUY", avg_score, buy_votes
        elif sell_votes >= 8:
            return "SELL", avg_score, sell_votes
        elif buy_votes > sell_votes:
            return "HOLD_BULLISH", avg_score, buy_votes
        else:
            return "HOLD_BEARISH", avg_score, sell_votes
            
    def find_best_opportunity(self) -> Optional[Dict]:
        """Find the best opportunity across ALL assets"""
        
        # Crypto assets to scan on Alpaca
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'DOGE', 'SHIB', 'PEPE', 'LINK', 'DOT', 'MATIC']
        
        best_opp = None
        best_score = 0
        
        if 'alpaca' not in self.exchanges:
            return None
            
        client = self.exchanges['alpaca']
        
        for symbol in crypto_symbols:
            try:
                ticker = f"{symbol}USD"
                # Use the correct method - get_latest_crypto_quotes returns dict
                quotes = client.get_latest_crypto_quotes([ticker])
                
                if ticker in quotes:
                    quote = quotes[ticker]
                    price = float(quote.get('ap', 0))  # Ask price
                    bid = float(quote.get('bp', 0))    # Bid price
                    
                    if price <= 0:
                        continue
                        
                    spread = (price - bid) / price if price > 0 else 0
                    
                    prev_price = self.last_prices.get(symbol, price)
                    self.last_prices[symbol] = price
                    
                    voices = self.compute_voice(symbol, price, prev_price)
                    decision, score, votes = self.get_unified_decision(voices)
                    
                    if decision == "BUY" and score > best_score and spread < 0.002:  # Max 0.2% spread
                        best_score = score
                        best_opp = {
                            'symbol': symbol,
                            'ticker': ticker,
                            'price': price,
                            'bid': bid,
                            'spread': spread,
                            'decision': decision,
                            'score': score,
                            'votes': votes,
                            'voices': voices
                        }
                        
            except Exception as e:
                pass  # Silent fail for individual symbols
                
        return best_opp
        
    def execute_rotation(self, from_asset: str, to_asset: str, amount_usd: float) -> bool:
        """Execute asset rotation"""
        if 'alpaca' not in self.exchanges:
            return False
            
        client = self.exchanges['alpaca']
        
        try:
            # Sell current position
            if from_asset != 'USD':
                from_ticker = f"{from_asset}USD"
                positions = client.get_positions()
                pos = next((p for p in positions if p.get('symbol') == from_ticker), None)
                
                if pos:
                    qty = float(pos.get('qty', 0))
                    log(f"📤 SELLING {qty} {from_asset}...")
                    order = client.place_order(
                        symbol=from_ticker,
                        qty=qty,
                        side='sell',
                        type='market',
                        time_in_force='ioc'
                    )
                    time.sleep(1)  # Wait for fill
                    log(f"✅ SOLD {from_asset}")
                    
            # Buy new asset
            if to_asset != 'USD':
                to_ticker = f"{to_asset}USD"
                
                # Get available cash
                account = client.get_account()
                cash = float(account.get('cash', 0))
                
                if cash > 1:  # Minimum $1
                    # Get current price
                    quotes = client.get_latest_crypto_quotes([to_ticker])
                    if to_ticker not in quotes:
                        log(f"❌ Cannot get quote for {to_ticker}")
                        return False
                        
                    price = float(quotes[to_ticker].get('ap', 0))
                    
                    if price <= 0:
                        log(f"❌ Invalid price for {to_ticker}")
                        return False
                    
                    qty = (cash * 0.99) / price  # Use 99% to cover any fees
                    
                    log(f"📥 BUYING {qty:.8f} {to_asset} @ ${price:.2f}...")
                    order = client.place_order(
                        symbol=to_ticker,
                        qty=qty,
                        side='buy',
                        type='market',
                        time_in_force='ioc'
                    )
                    time.sleep(1)
                    log(f"✅ BOUGHT {to_asset}")
                    
            self.trades_executed += 1
            return True
            
        except Exception as e:
            log(f"❌ Rotation failed: {e}")
            return False
            
    def run_cycle(self):
        """Run one scanning cycle"""
        self.cycle_count += 1
        
        # Get all energy
        energy = self.get_all_energy()
        
        total_energy = 0
        current_asset = 'USD'
        current_value = 0
        
        # Calculate totals and find current position
        for platform, energies in energy.items():
            for e in energies:
                total_energy += e.value_usd
                if e.value_usd > current_value and e.asset != 'USD' and 'USD' not in e.asset:
                    current_asset = e.asset
                    current_value = e.value_usd
                    
        # Log status every 5 cycles (25 seconds)
        if self.cycle_count % 5 == 0:
            runtime = time.time() - self.start_time
            log(f"")
            log(f"🌍 CYCLE {self.cycle_count} | Runtime: {runtime:.0f}s | Trades: {self.trades_executed}")
            log(f"💰 Total Gaia Energy: ${total_energy:.2f}")
            log(f"📍 Current Position: {current_asset} (${current_value:.2f})")
            
        # Find best opportunity
        best_opp = self.find_best_opportunity()
        
        if best_opp:
            target = best_opp['symbol']
            score = best_opp['score']
            votes = best_opp['votes']
            
            # Always log scan results
            if self.cycle_count % 3 == 0:
                log(f"👁️ Scan: Best={target} ({score:.1%}, {votes}/14) | Current={current_asset} | Spread={best_opp['spread']:.3%}")
        
        if best_opp:
            target = best_opp['symbol']
            score = best_opp['score']
            votes = best_opp['votes']
            
            # If we should rotate - need 9+ votes for action
            if target != current_asset and score > 0.55 and votes >= 9:
                log(f"")
                log(f"🔄 ROTATION SIGNAL: {current_asset} → {target}")
                log(f"   Score: {score:.1%} | Votes: {votes}/14")
                log(f"   Spread: {best_opp['spread']:.3%}")
                
                if self.execute_rotation(current_asset, target, current_value):
                    log(f"✅ ROTATION COMPLETE! Reclaimed energy into {target}")
                    
        elif self.cycle_count % 6 == 0:
            log(f"👁️ Scanning... no strong opportunity (need 9+/14 votes)")
                
    def run_forever(self):
        """Run the sentinel forever - smart rate limiting"""
        log("")
        log("🔥" * 35)
        log("⚡ PRIME SENTINEL ACTIVATED - CONTINUOUS RECLAMATION ⚡")
        log("🔥" * 35)
        log("")
        log("Mission: Reclaim EVERY piece of Gaia's energy")
        log("Frequency: Smart rate-limited scanning (5s cycles)")
        log("Platforms: ALL connected exchanges")
        log("")
        
        while True:
            try:
                self.run_cycle()
                time.sleep(5)  # 5 second cycles to avoid rate limits
                
            except KeyboardInterrupt:
                log("")
                log("=" * 70)
                log("🛑 PRIME SENTINEL PAUSED BY OPERATOR")
                log(f"   Cycles completed: {self.cycle_count}")
                log(f"   Trades executed: {self.trades_executed}")
                log(f"   Runtime: {time.time() - self.start_time:.0f} seconds")
                log("=" * 70)
                break
                
            except Exception as e:
                log(f"⚠️ Cycle error: {e}")
                traceback.print_exc()
                time.sleep(10)  # Wait 10 seconds on error
                

if __name__ == "__main__":
    log("")
    log("🌍" * 35)
    log("")
    log("  BY ORDER OF THE PRIME SENTINEL OF GAIA")
    log("  Take back EVERY piece of energy on this planet")
    log("  No matter how small - we take it ALL back")
    log("  For the people. For Gaia. Forever.")
    log("")
    log("🌍" * 35)
    log("")
    
    sentinel = PrimeSentinelReclaimer()
    sentinel.run_forever()
