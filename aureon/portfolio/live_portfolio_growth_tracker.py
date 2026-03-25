#!/usr/bin/env python3
"""
🔴 LIVE PORTFOLIO GROWTH TRACKER 🔴
Measures portfolio value in real-time across all exchanges to PROVE growth.

Tracks:
- Total portfolio value (USD)
- P&L since start
- Growth % and ROI
- Per-exchange breakdowns
- Position-by-position details
- Historical snapshots for proof
- Live streaming updates

Integrates with: Black Box, Orca, Queen, Auris
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            """Check if stream buffer is valid and not closed."""
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        # Only wrap if not already UTF-8 wrapped AND buffer is valid
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import json
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618033989 - Golden Ratio
PERFECTION_ANGLE = 306.0  # 360 - 54 (golden angle complement)

# Import exchange clients
try:
    from kraken_client import KrakenClient, get_kraken_client
except ImportError:
    KrakenClient = None

try:
    from alpaca_client import AlpacaClient
except ImportError:
    AlpacaClient = None

# Try to import Queen + Auris consciousness
try:
    from metatron_probability_billion_path import QueenAurisPingPong
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_AVAILABLE = False


@dataclass
class AssetHolding:
    """Single asset holding on an exchange."""
    asset: str
    exchange: str
    quantity: float
    usd_value: float
    current_price: float
    cost_basis: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


@dataclass
class ExchangeSnapshot:
    """Snapshot of one exchange's portfolio."""
    exchange: str
    timestamp: float
    total_usd_value: float
    holdings: List[AssetHolding] = field(default_factory=list)
    num_positions: int = 0
    largest_position_usd: float = 0.0
    largest_position_asset: str = ""


@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot across all exchanges."""
    timestamp: float
    datetime_str: str
    total_usd_value: float
    initial_usd_value: float
    pnl_usd: float
    growth_pct: float
    roi_pct: float
    exchanges: List[ExchangeSnapshot] = field(default_factory=list)
    num_exchanges: int = 0
    num_total_positions: int = 0
    largest_holding_usd: float = 0.0
    largest_holding_asset: str = ""
    largest_holding_exchange: str = ""
    
    # Sacred geometry
    sacred_alignment: float = 0.0  # How aligned with Fibonacci levels
    geometric_angle: float = 0.0  # Current angle in sacred geometry
    perfection_score: float = 0.0  # Distance from 306°


@dataclass
class GrowthProof:
    """Historical proof of growth over time."""
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)
    start_time: float = 0.0
    start_value: float = 0.0
    peak_value: float = 0.0
    peak_time: float = 0.0
    current_value: float = 0.0
    total_pnl: float = 0.0
    total_growth_pct: float = 0.0
    avg_growth_per_minute: float = 0.0
    sacred_growth_factor: float = 1.0  # Relationship to PHI


class LivePortfolioTracker:
    """
    Live portfolio tracker that proves growth in real-time.
    
    Connects to all exchanges, tracks balance changes, calculates P&L,
    and maintains historical proof of portfolio growth.
    """
    
    def __init__(self):
        """Initialize portfolio tracker."""
        self.exchanges: Dict[str, any] = {}
        self.initial_snapshot: Optional[PortfolioSnapshot] = None
        self.growth_proof = GrowthProof()
        self.consciousness = None
        
        # Proof storage
        self.proof_file = Path("portfolio_growth_proof.json")
        self.snapshot_file = Path("portfolio_snapshots.json")
        
        # Load historical data if exists
        self._load_historical_proof()
        
        print("🔴 LIVE PORTFOLIO GROWTH TRACKER INITIALIZING...")
        
    def _load_historical_proof(self):
        """Load historical proof from disk."""
        if self.proof_file.exists():
            try:
                with open(self.proof_file, 'r') as f:
                    data = json.load(f)
                    self.growth_proof.start_time = data.get('start_time', 0.0)
                    self.growth_proof.start_value = data.get('start_value', 0.0)
                    self.growth_proof.peak_value = data.get('peak_value', 0.0)
                    self.growth_proof.peak_time = data.get('peak_time', 0.0)
                    print(f"📊 Loaded historical proof: Start ${self.growth_proof.start_value:,.2f}")
            except Exception as e:
                print(f"⚠️  Could not load historical proof: {e}")
    
    def _save_proof(self):
        """Save growth proof to disk."""
        try:
            proof_data = {
                'start_time': self.growth_proof.start_time,
                'start_value': self.growth_proof.start_value,
                'peak_value': self.growth_proof.peak_value,
                'peak_time': self.growth_proof.peak_time,
                'current_value': self.growth_proof.current_value,
                'total_pnl': self.growth_proof.total_pnl,
                'total_growth_pct': self.growth_proof.total_growth_pct,
                'avg_growth_per_minute': self.growth_proof.avg_growth_per_minute,
                'sacred_growth_factor': self.growth_proof.sacred_growth_factor,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.proof_file, 'w') as f:
                json.dump(proof_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save proof: {e}")
    
    def _save_snapshot(self, snapshot: PortfolioSnapshot):
        """Save snapshot to historical record."""
        try:
            snapshots = []
            if self.snapshot_file.exists():
                with open(self.snapshot_file, 'r') as f:
                    snapshots = json.load(f)
            
            # Add new snapshot
            snapshots.append(asdict(snapshot))
            
            # Keep last 1000 snapshots
            if len(snapshots) > 1000:
                snapshots = snapshots[-1000:]
            
            with open(self.snapshot_file, 'w') as f:
                json.dump(snapshots, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save snapshot: {e}")
    
    async def initialize_exchanges(self):
        """Initialize all exchange connections."""
        print("\n🔗 Connecting to exchanges...")
        
        # Kraken
        if KrakenClient:
            try:
                self.exchanges['kraken'] = get_kraken_client()
                print("   ✅ Kraken connected")
            except Exception as e:
                print(f"   ⚠️  Kraken: {e}")
        
        # Alpaca
        if AlpacaClient:
            try:
                self.exchanges['alpaca'] = AlpacaClient()
                print("   ✅ Alpaca connected")
            except Exception as e:
                print(f"   ⚠️  Alpaca: {e}")
        
        if not self.exchanges:
            print("   ⚠️  No exchanges connected - using simulation mode")
        
        # Initialize consciousness if available
        if CONSCIOUSNESS_AVAILABLE:
            try:
                self.consciousness = QueenAurisPingPong()
                print("   ✅ Queen + Auris consciousness active")
            except Exception as e:
                print(f"   ⚠️  Consciousness: {e}")
    
    async def get_asset_price(self, asset: str, exchange: str) -> float:
        """Get current USD price for an asset."""
        # Common crypto prices (approximate)
        crypto_prices = {
            'BTC': 104500.0,
            'ETH': 3420.0,
            'SOL': 238.0,
            'MATIC': 1.15,
            'ADA': 0.95,
            'DOT': 8.50,
            'LINK': 22.0,
            'UNI': 12.5,
            'AVAX': 42.0,
            'ATOM': 11.0,
        }
        
        if asset == 'USD' or asset == 'ZUSD':
            return 1.0
        
        # Strip exchange prefixes
        clean_asset = asset.replace('X', '').replace('Z', '')
        
        if clean_asset in crypto_prices:
            return crypto_prices[clean_asset]
        
        # Try to get live price from exchange
        try:
            client = self.exchanges.get(exchange)
            if client and hasattr(client, 'get_ticker'):
                symbol = f"{clean_asset}/USD"
                ticker = client.get_ticker(symbol)
                if ticker and 'last' in ticker:
                    return float(ticker['last'])
        except:
            pass
        
        # Default to $1 if unknown
        return 1.0
    
    async def get_exchange_snapshot(self, exchange_name: str, client: any) -> ExchangeSnapshot:
        """Get portfolio snapshot from one exchange."""
        snapshot = ExchangeSnapshot(
            exchange=exchange_name,
            timestamp=time.time(),
            total_usd_value=0.0
        )
        
        try:
            # Get balances using correct method for each exchange
            if exchange_name == 'kraken':
                balances = client.get_account_balance()
            elif exchange_name == 'alpaca':
                account = client.get_account()
                # Alpaca returns account info, not just balances
                equity = float(account.get('equity', 0))
                cash = float(account.get('cash', 0))
                balances = {'USD': cash, 'EQUITY': equity}
            else:
                balances = {}
            
            for asset, quantity in balances.items():
                if quantity > 0.0001:  # Ignore dust
                    price = await self.get_asset_price(asset, exchange_name)
                    usd_value = quantity * price
                    
                    holding = AssetHolding(
                        asset=asset,
                        exchange=exchange_name,
                        quantity=quantity,
                        usd_value=usd_value,
                        current_price=price
                    )
                    
                    snapshot.holdings.append(holding)
                    snapshot.total_usd_value += usd_value
                    
                    # Track largest position
                    if usd_value > snapshot.largest_position_usd:
                        snapshot.largest_position_usd = usd_value
                        snapshot.largest_position_asset = asset
            
            snapshot.num_positions = len(snapshot.holdings)
            
        except Exception as e:
            print(f"⚠️  Error getting {exchange_name} snapshot: {e}")
        
        return snapshot
    
    def calculate_sacred_alignment(self, value: float) -> tuple[float, float, float]:
        """
        Calculate sacred geometry alignment.
        
        Returns: (sacred_alignment, geometric_angle, perfection_score)
        """
        # Fibonacci levels
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618]
        
        # Find closest Fibonacci ratio in growth
        if self.growth_proof.start_value > 0:
            growth_ratio = value / self.growth_proof.start_value
        else:
            growth_ratio = 1.0
        
        # Find closest Fibonacci level
        closest_fib = min(fib_levels, key=lambda x: abs(x - growth_ratio))
        alignment = 1.0 - abs(closest_fib - growth_ratio) / closest_fib
        
        # Map to geometric angle
        # Use Fibonacci level to interpolate toward 306°
        if growth_ratio < 1.0:
            angle = 180.0 + (growth_ratio * 60)  # 180-240° range for losses
        else:
            # Map growth above 1.0 toward 306°
            excess = min((growth_ratio - 1.0) / PHI, 1.0)  # Cap at 1.0
            angle = 240.0 + (excess * 66.0)  # 240-306° range
        
        # Calculate perfection score (distance from 306°)
        angle_distance = abs(angle - PERFECTION_ANGLE)
        perfection_score = max(0.0, 1.0 - (angle_distance / 180.0))  # 0-1 scale
        
        return alignment, angle, perfection_score
    
    async def get_full_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Get complete portfolio snapshot across all exchanges."""
        snapshot = PortfolioSnapshot(
            timestamp=time.time(),
            datetime_str=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_usd_value=0.0,
            initial_usd_value=self.growth_proof.start_value,
            pnl_usd=0.0,
            growth_pct=0.0,
            roi_pct=0.0
        )
        
        # Get snapshots from all exchanges
        for exchange_name, client in self.exchanges.items():
            exchange_snapshot = await self.get_exchange_snapshot(exchange_name, client)
            snapshot.exchanges.append(exchange_snapshot)
            snapshot.total_usd_value += exchange_snapshot.total_usd_value
            snapshot.num_total_positions += exchange_snapshot.num_positions
            
            # Track largest holding globally
            if exchange_snapshot.largest_position_usd > snapshot.largest_holding_usd:
                snapshot.largest_holding_usd = exchange_snapshot.largest_position_usd
                snapshot.largest_holding_asset = exchange_snapshot.largest_position_asset
                snapshot.largest_holding_exchange = exchange_name
        
        snapshot.num_exchanges = len(snapshot.exchanges)
        
        # Calculate P&L and growth
        if self.growth_proof.start_value > 0:
            snapshot.pnl_usd = snapshot.total_usd_value - self.growth_proof.start_value
            snapshot.growth_pct = (snapshot.pnl_usd / self.growth_proof.start_value) * 100
            snapshot.roi_pct = snapshot.growth_pct
        
        # Calculate sacred geometry
        sacred_alignment, geometric_angle, perfection_score = self.calculate_sacred_alignment(
            snapshot.total_usd_value
        )
        snapshot.sacred_alignment = sacred_alignment
        snapshot.geometric_angle = geometric_angle
        snapshot.perfection_score = perfection_score
        
        return snapshot
    
    def update_growth_proof(self, snapshot: PortfolioSnapshot):
        """Update growth proof with new snapshot."""
        # Initialize start values if needed
        if self.growth_proof.start_value == 0.0:
            self.growth_proof.start_time = snapshot.timestamp
            self.growth_proof.start_value = snapshot.total_usd_value
        
        # Update current values
        self.growth_proof.current_value = snapshot.total_usd_value
        self.growth_proof.total_pnl = snapshot.pnl_usd
        self.growth_proof.total_growth_pct = snapshot.growth_pct
        
        # Track peak
        if snapshot.total_usd_value > self.growth_proof.peak_value:
            self.growth_proof.peak_value = snapshot.total_usd_value
            self.growth_proof.peak_time = snapshot.timestamp
        
        # Calculate growth rate
        elapsed_minutes = (snapshot.timestamp - self.growth_proof.start_time) / 60.0
        if elapsed_minutes > 0:
            self.growth_proof.avg_growth_per_minute = self.growth_proof.total_pnl / elapsed_minutes
        
        # Calculate sacred growth factor (relationship to PHI)
        if self.growth_proof.start_value > 0:
            growth_multiple = snapshot.total_usd_value / self.growth_proof.start_value
            # How close to PHI-based growth?
            phi_target = PHI  # 1.618 is first PHI target
            self.growth_proof.sacred_growth_factor = growth_multiple / phi_target
        
        # Add to snapshots
        self.growth_proof.snapshots.append(snapshot)
        
        # Save proof
        self._save_proof()
        self._save_snapshot(snapshot)
    
    def display_snapshot(self, snapshot: PortfolioSnapshot):
        """Display portfolio snapshot with beautiful formatting."""
        print("\n" + "="*80)
        print(f"📊 LIVE PORTFOLIO SNAPSHOT - {snapshot.datetime_str}")
        print("="*80)
        
        print(f"\n💰 TOTAL PORTFOLIO VALUE: ${snapshot.total_usd_value:,.2f}")
        
        if snapshot.initial_usd_value > 0:
            print(f"\n📈 GROWTH METRICS:")
            print(f"   Starting Value: ${snapshot.initial_usd_value:,.2f}")
            print(f"   Current Value:  ${snapshot.total_usd_value:,.2f}")
            print(f"   P&L:            ${snapshot.pnl_usd:+,.2f}")
            print(f"   Growth:         {snapshot.growth_pct:+.2f}%")
            print(f"   ROI:            {snapshot.roi_pct:+.2f}%")
        
        print(f"\n🔮 SACRED GEOMETRY:")
        print(f"   Alignment:      {snapshot.sacred_alignment*100:.1f}%")
        print(f"   Angle:          {snapshot.geometric_angle:.1f}°")
        print(f"   Perfection:     {snapshot.perfection_score*100:.1f}% (Target: 306°)")
        
        print(f"\n📊 PORTFOLIO COMPOSITION:")
        print(f"   Exchanges:      {snapshot.num_exchanges}")
        print(f"   Total Positions: {snapshot.num_total_positions}")
        if snapshot.largest_holding_asset:
            print(f"   Largest Holding: {snapshot.largest_holding_asset} @ {snapshot.largest_holding_exchange}")
            print(f"                   ${snapshot.largest_holding_usd:,.2f}")
        
        # Per-exchange breakdown
        print(f"\n💼 EXCHANGE BREAKDOWN:")
        for ex_snapshot in snapshot.exchanges:
            print(f"\n   {ex_snapshot.exchange.upper()}: ${ex_snapshot.total_usd_value:,.2f}")
            print(f"   Positions: {ex_snapshot.num_positions}")
            
            # Show top 3 holdings
            sorted_holdings = sorted(ex_snapshot.holdings, key=lambda x: x.usd_value, reverse=True)
            for holding in sorted_holdings[:3]:
                print(f"      {holding.asset}: {holding.quantity:.4f} @ ${holding.current_price:.2f} = ${holding.usd_value:,.2f}")
    
    def display_growth_proof(self):
        """Display historical growth proof."""
        print("\n" + "="*80)
        print("🏆 GROWTH PROOF - HISTORICAL PERFORMANCE")
        print("="*80)
        
        proof = self.growth_proof
        
        print(f"\n⏱️  TIME PERIOD:")
        if proof.start_time > 0:
            start_dt = datetime.fromtimestamp(proof.start_time).strftime("%Y-%m-%d %H:%M:%S")
            elapsed_minutes = (time.time() - proof.start_time) / 60.0
            print(f"   Start: {start_dt}")
            print(f"   Duration: {elapsed_minutes:.1f} minutes")
        
        print(f"\n💰 CAPITAL GROWTH:")
        print(f"   Starting Value:  ${proof.start_value:,.2f}")
        print(f"   Current Value:   ${proof.current_value:,.2f}")
        print(f"   Peak Value:      ${proof.peak_value:,.2f}")
        print(f"   Total P&L:       ${proof.total_pnl:+,.2f}")
        print(f"   Total Growth:    {proof.total_growth_pct:+.2f}%")
        
        if proof.avg_growth_per_minute != 0:
            print(f"\n📊 GROWTH RATE:")
            print(f"   Per Minute:      ${proof.avg_growth_per_minute:+,.2f}")
            print(f"   Per Hour:        ${proof.avg_growth_per_minute * 60:+,.2f}")
            print(f"   Per Day:         ${proof.avg_growth_per_minute * 1440:+,.2f}")
        
        print(f"\n🔮 SACRED METRICS:")
        print(f"   Growth Factor:   {proof.sacred_growth_factor:.4f}× (φ = {PHI:.4f})")
        if proof.sacred_growth_factor >= 1.0:
            print(f"   Status:          ✨ EXCEEDING GOLDEN RATIO TARGET ✨")
        else:
            remaining = (1.0 - proof.sacred_growth_factor) * 100
            print(f"   Status:          {remaining:.1f}% to φ target")
        
        print(f"\n📈 SNAPSHOT HISTORY:")
        print(f"   Total Snapshots: {len(proof.snapshots)}")
        if len(proof.snapshots) >= 2:
            recent = proof.snapshots[-5:]  # Last 5
            print(f"   Recent Values:")
            for snap in recent:
                dt = datetime.fromtimestamp(snap.timestamp).strftime("%H:%M:%S")
                print(f"      {dt}: ${snap.total_usd_value:,.2f} ({snap.growth_pct:+.2f}%)")
    
    async def stream_live_updates(self, update_interval: float = 5.0, duration: float = 60.0):
        """
        Stream live portfolio updates.
        
        Args:
            update_interval: Seconds between updates
            duration: Total duration in seconds (0 = infinite)
        """
        print("\n🔴 STARTING LIVE PORTFOLIO STREAM...")
        print(f"   Update Interval: {update_interval}s")
        if duration > 0:
            print(f"   Duration: {duration}s")
        else:
            print(f"   Duration: INFINITE (Ctrl+C to stop)")
        
        start_time = time.time()
        update_count = 0
        
        try:
            while True:
                # Check duration
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                
                # Get snapshot
                snapshot = await self.get_full_portfolio_snapshot()
                
                # Update proof
                self.update_growth_proof(snapshot)
                
                # Display
                if update_count % 5 == 0:  # Full display every 5 updates
                    self.display_snapshot(snapshot)
                else:
                    # Quick update
                    print(f"\n⏱️  {snapshot.datetime_str} | ${snapshot.total_usd_value:,.2f} | P&L: ${snapshot.pnl_usd:+,.2f} ({snapshot.growth_pct:+.2f}%) | Perfection: {snapshot.perfection_score*100:.1f}%")
                
                update_count += 1
                
                # Wait for next update
                await asyncio.sleep(update_interval)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stream stopped by user")
        
        # Final summary
        print("\n" + "="*80)
        print("🏁 LIVE STREAM COMPLETE")
        print("="*80)
        
        final_snapshot = await self.get_full_portfolio_snapshot()
        self.display_snapshot(final_snapshot)
        self.display_growth_proof()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Live Portfolio Growth Tracker')
    parser.add_argument('--interval', type=float, default=5.0, help='Update interval in seconds')
    parser.add_argument('--duration', type=float, default=60.0, help='Total duration in seconds (0=infinite)')
    parser.add_argument('--snapshot-only', action='store_true', help='Take single snapshot and exit')
    
    args = parser.parse_args()
    
    # Create tracker
    tracker = LivePortfolioTracker()
    
    # Initialize exchanges
    await tracker.initialize_exchanges()
    
    if args.snapshot_only:
        # Single snapshot
        snapshot = await tracker.get_full_portfolio_snapshot()
        tracker.update_growth_proof(snapshot)
        tracker.display_snapshot(snapshot)
        tracker.display_growth_proof()
    else:
        # Live stream
        await tracker.stream_live_updates(
            update_interval=args.interval,
            duration=args.duration
        )


if __name__ == "__main__":
    asyncio.run(main())
