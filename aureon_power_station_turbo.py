#!/usr/bin/env python3
"""
AUREON POWER STATION TURBO - MAXIMUM ENERGY THROUGHPUT
No talk. Pure execution. Results only.
"""
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except:
        pass

import asyncio
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('TURBO')

# Import all relay clients
try:
    from binance_client import BinanceClient
    BIN_AVAILABLE = True
except:
    BIN_AVAILABLE = False

try:
    from kraken_client import KrakenClient
    KRK_AVAILABLE = True
except:
    KRK_AVAILABLE = False

try:
    from alpaca_client import AlpacaClient
    ALP_AVAILABLE = True
except:
    ALP_AVAILABLE = False

try:
    from capital_client import CapitalClient
    CAP_AVAILABLE = True
except:
    CAP_AVAILABLE = False

@dataclass
class EnergyPulse:
    """Single energy transfer result"""
    relay: str
    symbol: str
    side: str
    quantity: float
    price: float
    value: float
    fee: float
    net_gain: float
    latency_ms: float
    success: bool
    error: str = ""

@dataclass
class PowerStationState:
    """Real-time power station metrics"""
    total_energy: float = 0.0
    energy_deployed: float = 0.0
    cycles_completed: int = 0
    successful_pulses: int = 0
    failed_pulses: int = 0
    total_fees_paid: float = 0.0
    net_energy_gain: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    @property
    def runtime_sec(self) -> float:
        return time.time() - self.start_time
    
    @property
    def gain_per_sec(self) -> float:
        if self.runtime_sec > 0:
            return self.net_energy_gain / self.runtime_sec
        return 0.0
    
    @property
    def efficiency(self) -> float:
        if self.successful_pulses + self.failed_pulses > 0:
            return self.successful_pulses / (self.successful_pulses + self.failed_pulses)
        return 0.0


class PowerStationTurbo:
    """
    MAXIMUM THROUGHPUT ENERGY ENGINE
    
    Parallel execution across all relays.
    No waiting. Pure speed.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.state = PowerStationState()
        self.relays: Dict[str, any] = {}
        self.balances: Dict[str, Dict[str, float]] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Fee profiles (energy drain per relay)
        self.fee_rates = {
            'BIN': 0.001,   # 0.1%
            'KRK': 0.0026,  # 0.26%
            'ALP': 0.0015,  # 0.15%
            'CAP': 0.002,   # 0.2%
        }
        
        # High-velocity pairs per relay
        self.turbo_pairs = {
            'BIN': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT'],
            'KRK': ['XBTUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'DOGEUSD'],
            'ALP': ['BTC/USD', 'ETH/USD', 'SOL/USD'],
            'CAP': ['BTCUSD', 'ETHUSD'],
        }
        
        self._init_relays()
    
    def _init_relays(self):
        """Initialize all available relays"""
        if BIN_AVAILABLE:
            try:
                self.relays['BIN'] = BinanceClient()
                log.info("🟡 BIN relay ONLINE")
            except Exception as e:
                log.warning(f"BIN relay failed: {e}")
        
        if KRK_AVAILABLE:
            try:
                self.relays['KRK'] = KrakenClient()
                log.info("🔵 KRK relay ONLINE")
            except Exception as e:
                log.warning(f"KRK relay failed: {e}")
        
        if ALP_AVAILABLE:
            try:
                self.relays['ALP'] = AlpacaClient()
                log.info("🟢 ALP relay ONLINE")
            except Exception as e:
                log.warning(f"ALP relay failed: {e}")
        
        if CAP_AVAILABLE:
            try:
                self.relays['CAP'] = CapitalClient()
                log.info("🟣 CAP relay ONLINE")
            except Exception as e:
                log.warning(f"CAP relay failed: {e}")
        
        log.info(f"⚡ {len(self.relays)} relays initialized")
    
    def _refresh_balances(self):
        """Parallel balance refresh across all relays"""
        def get_balance(relay_name, client):
            try:
                if relay_name == 'BIN':
                    return relay_name, client.get_balance()
                elif relay_name == 'KRK':
                    # Use state file if API rate limited
                    try:
                        bal = client.get_balance()
                        if bal:
                            return relay_name, bal
                    except:
                        pass
                    # Fallback to state file
                    try:
                        with open('aureon_kraken_state.json') as f:
                            state = json.load(f)
                            return relay_name, {'USD': state.get('balance', 0)}
                    except:
                        return relay_name, {}
                elif relay_name == 'ALP':
                    acc = client.get_account()
                    return relay_name, {'USD': float(acc.get('cash', 0))}
                elif relay_name == 'CAP':
                    accs = client.get_accounts()
                    total = sum(float(a.get('balance', 0)) for a in (accs if isinstance(accs, list) else [accs]))
                    return relay_name, {'GBP': total, 'USD': total * 1.25}
            except Exception as e:
                log.warning(f"{relay_name} balance error: {e}")
                return relay_name, {}
        
        futures = {self.executor.submit(get_balance, name, client): name 
                   for name, client in self.relays.items()}
        
        for future in as_completed(futures, timeout=15):
            try:
                relay_name, balance = future.result(timeout=10)
                self.balances[relay_name] = balance
            except Exception as e:
                log.debug(f"Balance timeout: {e}")
                pass
        
        # Calculate total energy
        total = 0.0
        for relay, bal in self.balances.items():
            usd = bal.get('USD', 0) or bal.get('USDT', 0) or 0
            total += usd
        
        self.state.total_energy = total
        return total
    
    def _get_ticker(self, relay: str, symbol: str) -> Optional[Dict]:
        """Get ticker data from relay"""
        try:
            client = self.relays.get(relay)
            if not client:
                return None
            
            if relay == 'BIN':
                return client.get_ticker(symbol)
            elif relay == 'KRK':
                return client.get_ticker(symbol)
            elif relay == 'ALP':
                return client.get_ticker(symbol)
            elif relay == 'CAP':
                return client.get_ticker(symbol)
        except:
            return None
    
    def _find_arbitrage_opportunities(self) -> List[Tuple[str, str, str, float, float]]:
        """
        Scan for cross-relay arbitrage opportunities.
        Returns: [(buy_relay, sell_relay, asset, buy_price, sell_price), ...]
        """
        opportunities = []
        
        # Common assets across relays
        common_assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE']
        
        for asset in common_assets:
            prices = {}
            
            # Get prices from each relay
            for relay in self.relays.keys():
                if relay == 'BIN':
                    ticker = self._get_ticker(relay, f'{asset}USDT')
                elif relay == 'KRK':
                    krk_symbol = 'XBT' if asset == 'BTC' else asset
                    ticker = self._get_ticker(relay, f'{krk_symbol}USD')
                elif relay == 'ALP':
                    ticker = self._get_ticker(relay, f'{asset}/USD')
                elif relay == 'CAP':
                    ticker = self._get_ticker(relay, f'{asset}USD')
                else:
                    continue
                
                if ticker:
                    bid = float(ticker.get('bid', 0) or ticker.get('bidPrice', 0) or 0)
                    ask = float(ticker.get('ask', 0) or ticker.get('askPrice', 0) or 0)
                    if bid > 0 and ask > 0:
                        prices[relay] = {'bid': bid, 'ask': ask}
            
            # Find arbitrage: buy low on one relay, sell high on another
            if len(prices) >= 2:
                relays = list(prices.keys())
                for i, buy_relay in enumerate(relays):
                    for sell_relay in relays[i+1:]:
                        buy_price = prices[buy_relay]['ask']
                        sell_price = prices[sell_relay]['bid']
                        
                        # Account for fees
                        buy_fee = self.fee_rates.get(buy_relay, 0.002)
                        sell_fee = self.fee_rates.get(sell_relay, 0.002)
                        
                        net_gain_pct = (sell_price / buy_price - 1) - buy_fee - sell_fee
                        
                        if net_gain_pct > 0.0005:  # 0.05% minimum edge
                            opportunities.append((buy_relay, sell_relay, asset, buy_price, sell_price, net_gain_pct))
                        
                        # Check reverse direction
                        buy_price_rev = prices[sell_relay]['ask']
                        sell_price_rev = prices[buy_relay]['bid']
                        net_gain_pct_rev = (sell_price_rev / buy_price_rev - 1) - buy_fee - sell_fee
                        
                        if net_gain_pct_rev > 0.0005:
                            opportunities.append((sell_relay, buy_relay, asset, buy_price_rev, sell_price_rev, net_gain_pct_rev))
        
        # Sort by edge (highest first)
        opportunities.sort(key=lambda x: x[5], reverse=True)
        return opportunities
    
    def _execute_pulse(self, relay: str, symbol: str, side: str, quantity: float) -> EnergyPulse:
        """Execute single energy pulse (trade)"""
        start = time.time()
        
        try:
            client = self.relays.get(relay)
            if not client:
                return EnergyPulse(relay, symbol, side, quantity, 0, 0, 0, 0, 0, False, "No client")
            
            # Get current price
            ticker = self._get_ticker(relay, symbol)
            if not ticker:
                return EnergyPulse(relay, symbol, side, quantity, 0, 0, 0, 0, 0, False, "No ticker")
            
            price = float(ticker.get('last', 0) or ticker.get('price', 0) or 
                         ticker.get('bid', 0) if side == 'sell' else ticker.get('ask', 0))
            
            if price <= 0:
                return EnergyPulse(relay, symbol, side, quantity, 0, 0, 0, 0, 0, False, "Invalid price")
            
            value = quantity * price
            fee = value * self.fee_rates.get(relay, 0.002)
            
            if self.dry_run:
                # Simulate execution
                latency = (time.time() - start) * 1000
                # Simulate 0.02-0.1% edge capture
                simulated_gain = value * 0.0005  # 0.05% average
                net_gain = simulated_gain - fee
                
                return EnergyPulse(
                    relay=relay,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    value=value,
                    fee=fee,
                    net_gain=net_gain,
                    latency_ms=latency,
                    success=True
                )
            else:
                # LIVE EXECUTION
                if relay == 'BIN':
                    result = client.create_order(symbol, side, 'market', quantity)
                elif relay == 'KRK':
                    result = client.create_order(symbol, side, 'market', quantity)
                elif relay == 'ALP':
                    result = client.create_order(symbol, side, 'market', quantity)
                elif relay == 'CAP':
                    result = client.create_order(symbol, side, 'market', quantity)
                
                latency = (time.time() - start) * 1000
                
                # Calculate actual gain from fill
                fill_price = float(result.get('price', price))
                actual_value = quantity * fill_price
                actual_fee = actual_value * self.fee_rates.get(relay, 0.002)
                
                return EnergyPulse(
                    relay=relay,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=fill_price,
                    value=actual_value,
                    fee=actual_fee,
                    net_gain=actual_value - value - actual_fee if side == 'sell' else 0,
                    latency_ms=latency,
                    success=True
                )
                
        except Exception as e:
            latency = (time.time() - start) * 1000
            return EnergyPulse(relay, symbol, side, quantity, 0, 0, 0, 0, latency, False, str(e))
    
    def _run_turbo_cycle(self) -> List[EnergyPulse]:
        """
        Execute one turbo cycle across all relays in parallel.
        Returns list of pulse results.
        """
        pulses = []
        
        # Find arbitrage opportunities
        opportunities = self._find_arbitrage_opportunities()
        
        if opportunities:
            # Execute best opportunity
            best = opportunities[0]
            buy_relay, sell_relay, asset, buy_price, sell_price, edge = best
            
            # Calculate position size (use 10% of available energy)
            available = self.balances.get(buy_relay, {}).get('USD', 0) or \
                       self.balances.get(buy_relay, {}).get('USDT', 0) or 0
            
            position_value = min(available * 0.1, 50)  # Max $50 per pulse
            quantity = position_value / buy_price if buy_price > 0 else 0
            
            if quantity > 0 and position_value >= 10:  # Min $10
                # Execute buy
                buy_symbol = f'{asset}USDT' if buy_relay == 'BIN' else f'{asset}USD'
                if buy_relay == 'KRK' and asset == 'BTC':
                    buy_symbol = 'XBTUSD'
                
                buy_pulse = self._execute_pulse(buy_relay, buy_symbol, 'buy', quantity)
                pulses.append(buy_pulse)
                
                if buy_pulse.success:
                    # Execute sell
                    sell_symbol = f'{asset}USDT' if sell_relay == 'BIN' else f'{asset}USD'
                    if sell_relay == 'KRK' and asset == 'BTC':
                        sell_symbol = 'XBTUSD'
                    
                    sell_pulse = self._execute_pulse(sell_relay, sell_symbol, 'sell', quantity)
                    pulses.append(sell_pulse)
                    
                    if sell_pulse.success:
                        log.info(f"⚡ ARB: {buy_relay}→{sell_relay} {asset} edge={edge*100:.3f}% gain=+{sell_pulse.net_gain:.4f}")
        
        # Also execute momentum trades on each relay
        futures = []
        for relay, pairs in self.turbo_pairs.items():
            if relay not in self.relays:
                continue
            
            # Pick random pair for momentum scan
            for symbol in pairs[:2]:  # First 2 pairs
                ticker = self._get_ticker(relay, symbol)
                if not ticker:
                    continue
                
                # Simple momentum: if price moved >0.1% in last tick, follow
                last = float(ticker.get('last', 0) or ticker.get('price', 0) or 0)
                bid = float(ticker.get('bid', 0) or ticker.get('bidPrice', 0) or 0)
                ask = float(ticker.get('ask', 0) or ticker.get('askPrice', 0) or 0)
                
                if last > 0 and bid > 0 and ask > 0:
                    spread = (ask - bid) / last
                    
                    # Only trade tight spreads
                    if spread < 0.002:  # <0.2% spread
                        available = self.balances.get(relay, {}).get('USD', 0) or \
                                   self.balances.get(relay, {}).get('USDT', 0) or 0
                        
                        position_value = min(available * 0.05, 25)  # 5% of balance, max $25
                        quantity = position_value / ask if ask > 0 else 0
                        
                        if quantity > 0 and position_value >= 5:  # Min $5
                            # Submit pulse
                            future = self.executor.submit(self._execute_pulse, relay, symbol, 'buy', quantity)
                            futures.append(future)
        
        # Collect momentum pulse results
        for future in as_completed(futures, timeout=2):
            try:
                pulse = future.result()
                pulses.append(pulse)
            except:
                pass
        
        return pulses
    
    def run(self, duration_sec: int = 60, target_gain: float = None):
        """
        RUN THE POWER STATION
        
        Args:
            duration_sec: How long to run (seconds)
            target_gain: Stop when this energy gain is reached
        """
        self.running = True
        self.state = PowerStationState()
        
        log.info("="*70)
        log.info("⚡🔋 POWER STATION TURBO - IGNITION 🔋⚡")
        log.info("="*70)
        log.info(f"Mode: {'DRY RUN' if self.dry_run else '🔴 LIVE'}")
        log.info(f"Duration: {duration_sec}s | Target: {target_gain or 'None'}")
        
        # Initial balance refresh
        initial_energy = self._refresh_balances()
        log.info(f"Initial Energy: {initial_energy:.2f} units")
        log.info("="*70)
        
        cycle = 0
        last_status = time.time()
        
        try:
            while self.running:
                cycle += 1
                cycle_start = time.time()
                
                # Execute turbo cycle
                pulses = self._run_turbo_cycle()
                
                # Update state
                self.state.cycles_completed = cycle
                for pulse in pulses:
                    if pulse.success:
                        self.state.successful_pulses += 1
                        self.state.total_fees_paid += pulse.fee
                        self.state.net_energy_gain += pulse.net_gain
                        self.state.energy_deployed += pulse.value
                    else:
                        self.state.failed_pulses += 1
                
                # Status update every 5 seconds
                if time.time() - last_status >= 5:
                    self._print_status()
                    last_status = time.time()
                    
                    # Refresh balances
                    self._refresh_balances()
                
                # Check exit conditions
                if self.state.runtime_sec >= duration_sec:
                    log.info("⏱️ Duration reached")
                    break
                
                if target_gain and self.state.net_energy_gain >= target_gain:
                    log.info(f"🎯 Target gain reached: +{self.state.net_energy_gain:.4f}")
                    break
                
                # Throttle to avoid rate limits
                cycle_time = time.time() - cycle_start
                if cycle_time < 0.1:  # Min 100ms per cycle
                    time.sleep(0.1 - cycle_time)
        
        except KeyboardInterrupt:
            log.info("⛔ Interrupted")
        
        finally:
            self.running = False
            self._print_final_report()
    
    def _print_status(self):
        """Print real-time status"""
        runtime = self.state.runtime_sec
        print(f"\r⚡ T+{runtime:.0f}s | Cycles: {self.state.cycles_completed} | "
              f"Pulses: {self.state.successful_pulses}✓/{self.state.failed_pulses}✗ | "
              f"Gain: +{self.state.net_energy_gain:.4f} | "
              f"Rate: +{self.state.gain_per_sec:.4f}/sec", end='', flush=True)
    
    def _print_final_report(self):
        """Print final execution report"""
        print()
        print("="*70)
        print("📊 POWER STATION TURBO - FINAL REPORT")
        print("="*70)
        print(f"""
  Runtime:           {self.state.runtime_sec:.1f} seconds
  Cycles Completed:  {self.state.cycles_completed}
  
  Successful Pulses: {self.state.successful_pulses}
  Failed Pulses:     {self.state.failed_pulses}
  Efficiency:        {self.state.efficiency*100:.1f}%
  
  Energy Deployed:   {self.state.energy_deployed:.2f} units
  Total Fees Paid:   {self.state.total_fees_paid:.4f} units
  
  ════════════════════════════════════════════════════════════
  NET ENERGY GAIN:   +{self.state.net_energy_gain:.4f} units
  GAIN PER SECOND:   +{self.state.gain_per_sec:.6f}/sec
  GAIN PER HOUR:     +{self.state.gain_per_sec * 3600:.4f}/hr
  ════════════════════════════════════════════════════════════
        """)
        
        # Save state
        try:
            with open('power_station_state.json', 'w') as f:
                json.dump({
                    'runtime_sec': self.state.runtime_sec,
                    'cycles': self.state.cycles_completed,
                    'successful_pulses': self.state.successful_pulses,
                    'failed_pulses': self.state.failed_pulses,
                    'net_gain': self.state.net_energy_gain,
                    'gain_per_sec': self.state.gain_per_sec,
                    'fees_paid': self.state.total_fees_paid,
                    'timestamp': time.time()
                }, f, indent=2)
        except:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Power Station Turbo')
    parser.add_argument('--live', action='store_true', help='Enable LIVE trading')
    parser.add_argument('--duration', type=int, default=60, help='Run duration in seconds')
    parser.add_argument('--target', type=float, help='Target energy gain')
    args = parser.parse_args()
    
    station = PowerStationTurbo(dry_run=not args.live)
    station.run(duration_sec=args.duration, target_gain=args.target)


if __name__ == '__main__':
    main()
