"""
💰 AUREON CAPITAL MOBILIZER
═══════════════════════════════════════════════════════════════

Intelligently mobilizes locked capital across exchanges:
1. Identifies free stablecoins (USDT, USDC, USD) on all exchanges
2. Converts between stablecoins when needed (USDT → USDC for buys)
3. Harvests profitable positions to free up buying power
4. Aggregates total buying power across all stablecoins

This solves: "System has $2.03 USDC but skipping trades needing $5.50"
Reality: May have $50 USDT + profitable positions worth $200
"""

import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class CapitalSummary:
    """Summary of available capital across all forms."""
    exchange: str
    free_stablecoins: Dict[str, float] = field(default_factory=dict)  # {USDT: 50, USDC: 2}
    total_stable_usd: float = 0.0
    locked_positions: Dict[str, float] = field(default_factory=dict)  # {SHELL: 82.7, GUN: 9.9}
    harvestable_positions: List[Dict] = field(default_factory=list)  # Profitable positions we can exit
    harvestable_value_usd: float = 0.0
    total_buying_power_usd: float = 0.0  # free + harvestable

@dataclass
class StablecoinConversion:
    """Plan to convert one stablecoin to another."""
    exchange: str
    from_asset: str
    to_asset: str
    amount: float
    pair: str  # e.g., "USDT/USDC"
    reason: str

class AureonCapitalMobilizer:
    """
    🚀 Mobilizes locked capital across exchanges.
    
    Flow:
    1. audit_capital() → See where money is (free + locked)
    2. plan_mobilization() → Decide what to convert/harvest
    3. execute_mobilization() → Actually do it
    """
    
    def __init__(self):
        """Initialize mobilizer with exchange clients."""
        self.exchange_clients = {}
        self._load_exchange_clients()
        
        # Load cost basis tracker for profit calculations
        try:
            from cost_basis_tracker import CostBasisTracker
            self.cost_basis = CostBasisTracker()
        except:
            self.cost_basis = None
            print("⚠️  Cost basis tracker not available - can't evaluate profits")
    
    def _load_exchange_clients(self):
        """Load exchange clients dynamically."""
        try:
            from binance_client import BinanceClient
            self.exchange_clients['binance'] = BinanceClient()
        except Exception as e:
            print(f"⚠️  Binance client not available: {e}")
        
        try:
            from kraken_client import KrakenClient
            self.exchange_clients['kraken'] = KrakenClient()
        except Exception as e:
            print(f"⚠️  Kraken client not available: {e}")
        
        try:
            from alpaca_client import AlpacaClient
            self.exchange_clients['alpaca'] = AlpacaClient()
        except Exception as e:
            print(f"⚠️  Alpaca client not available: {e}")
        
        try:
            from capital_client import CapitalClient
            self.exchange_clients['capital'] = CapitalClient()
        except Exception as e:
            print(f"⚠️  Capital.com client not available: {e}")
    
    def audit_capital(self, exchange: str = None) -> Dict[str, CapitalSummary]:
        """
        Audit all capital across exchanges.
        
        Returns: {exchange_name: CapitalSummary}
        """
        summaries = {}
        
        exchanges_to_audit = [exchange] if exchange else self.exchange_clients.keys()
        
        for exch in exchanges_to_audit:
            if exch == 'binance':
                summaries[exch] = self._audit_binance()
            elif exch == 'kraken':
                summaries[exch] = self._audit_kraken()
            elif exch == 'alpaca':
                summaries[exch] = self._audit_alpaca()
            elif exch == 'capital':
                summaries[exch] = self._audit_capital()
        
        return summaries
    
    def _audit_binance(self) -> CapitalSummary:
        """Audit Binance capital."""
        summary = CapitalSummary(exchange='binance')
        
        if 'binance' not in self.exchange_clients:
            return summary
        
        client = self.exchange_clients['binance']
        balances = client.get_balance()  # Use BinanceClient.get_balance()
        
        stables = ['USDT', 'USDC', 'USD', 'BUSD', 'FDUSD']
        
        for asset, amount in balances.items():
            if amount <= 0:
                continue
            
            # Stablecoins = free capital
            if asset in stables:
                summary.free_stablecoins[asset] = amount
                summary.total_stable_usd += amount
            
            # Crypto = locked capital
            else:
                summary.locked_positions[asset] = amount
        
        # Check which locked positions are profitable (harvestable)
        if self.cost_basis:
            for asset, amount in summary.locked_positions.items():
                # Try to get current price and cost basis
                try:
                    # Try multiple symbol formats
                    for quote in ['USDC', 'USDT', 'USD']:
                        symbol = f"{asset}/{quote}"
                        ticker = client.get_ticker(symbol)  # Use BinanceClient.get_ticker()
                        
                        if not ticker or 'last' not in ticker:
                            continue
                        
                        current_price = ticker['last']
                        
                        # Check if profitable
                        can_sell, info = self.cost_basis.can_sell_profitably(
                            symbol=symbol,
                            current_price=current_price,
                            quantity=amount,
                            exchange='binance'
                        )
                        
                        if can_sell:
                            harvest_value = info.get('gross_value', 0)
                            summary.harvestable_positions.append({
                                'asset': asset,
                                'amount': amount,
                                'symbol': symbol,
                                'entry_price': info.get('entry_price'),
                                'current_price': current_price,
                                'profit_pct': info.get('profit_pct'),
                                'net_profit': info.get('net_profit'),
                                'harvest_value_usd': harvest_value
                            })
                            summary.harvestable_value_usd += harvest_value
                            break  # Found profitable exit
                except Exception as e:
                    pass  # Can't price this asset
        
        summary.total_buying_power_usd = summary.total_stable_usd + summary.harvestable_value_usd
        return summary
    
    def _audit_kraken(self) -> CapitalSummary:
        """Audit Kraken capital."""
        summary = CapitalSummary(exchange='kraken')
        
        if 'kraken' not in self.exchange_clients:
            return summary
        
        client = self.exchange_clients['kraken']
        balances = client.get_balance()
        
        stables = ['USD', 'USDT', 'USDC', 'ZUSD']
        
        for asset, amount in balances.items():
            if amount <= 0:
                continue
            
            # Stablecoins
            if any(s in asset for s in stables):
                summary.free_stablecoins[asset] = amount
                summary.total_stable_usd += amount
            else:
                summary.locked_positions[asset] = amount
        
        # TODO: Add Kraken profit checking when cost basis supports it
        summary.total_buying_power_usd = summary.total_stable_usd
        return summary
    
    def _audit_alpaca(self) -> CapitalSummary:
        """Audit Alpaca capital."""
        summary = CapitalSummary(exchange='alpaca')
        
        if 'alpaca' not in self.exchange_clients:
            return summary
        
        client = self.exchange_clients['alpaca']
        
        try:
            # Get account info for cash
            account = client.get_account()
            cash = float(account.get('cash', 0))
            summary.free_stablecoins['USD'] = cash
            summary.total_stable_usd = cash
            
            # Get positions
            positions = client.get_positions()
            for pos in positions:
                symbol = pos.get('symbol', '')
                qty = float(pos.get('qty', 0))
                if qty > 0:
                    summary.locked_positions[symbol] = qty
            
            # TODO: Add profit checking for Alpaca positions
        except Exception as e:
            pass  # Silently handle errors
        
        summary.total_buying_power_usd = summary.total_stable_usd
        return summary
    
    def _audit_capital(self) -> CapitalSummary:
        """Audit Capital.com capital."""
        summary = CapitalSummary(exchange='capital')
        
        if 'capital' not in self.exchange_clients:
            return summary
        
        client = self.exchange_clients['capital']
        
        try:
            # Get account info
            accounts = client.get_accounts()
            if accounts and len(accounts) > 0:
                balance = float(accounts[0].get('balance', {}).get('balance', 0))
                summary.free_stablecoins['GBP'] = balance
                summary.total_stable_usd = balance * 1.27  # Rough GBP to USD conversion
            
            # Get positions
            positions = client.get_positions()
            for pos_data in positions:
                pos = pos_data.get('position', {})
                market = pos_data.get('market', {})
                symbol = market.get('instrumentName', 'unknown')
                size = float(pos.get('size', 0))
                if size > 0:
                    summary.locked_positions[symbol] = size
            
            # TODO: Add profit checking for Capital.com positions
        except Exception as e:
            pass  # Silently handle errors
        
        summary.total_buying_power_usd = summary.total_stable_usd
        return summary
    
    def plan_mobilization(self, 
                         target_quote: str, 
                         needed_amount: float,
                         exchange: str) -> Dict:
        """
        Plan how to mobilize capital to meet a target.
        
        Args:
            target_quote: Desired stablecoin (e.g., "USDC")
            needed_amount: Amount needed in USD
            exchange: Exchange to mobilize on
        
        Returns:
            {
                'available': float,
                'shortfall': float,
                'conversions': [StablecoinConversion],
                'harvests': [position_dict],
                'feasible': bool
            }
        """
        summary = self.audit_capital(exchange)[exchange]
        
        plan = {
            'available': summary.free_stablecoins.get(target_quote, 0),
            'shortfall': 0,
            'conversions': [],
            'harvests': [],
            'feasible': False
        }
        
        # Check if we already have enough
        if plan['available'] >= needed_amount:
            plan['feasible'] = True
            return plan
        
        shortfall = needed_amount - plan['available']
        plan['shortfall'] = shortfall
        
        # Strategy 1: Convert other stablecoins
        for stable, amount in summary.free_stablecoins.items():
            if stable == target_quote:
                continue
            
            if amount >= shortfall:
                # We can convert this to meet the need
                conversion = StablecoinConversion(
                    exchange=exchange,
                    from_asset=stable,
                    to_asset=target_quote,
                    amount=shortfall,
                    pair=f"{stable}/{target_quote}",
                    reason=f"Convert ${shortfall:.2f} {stable} → {target_quote} to meet buy requirement"
                )
                plan['conversions'].append(conversion)
                plan['feasible'] = True
                return plan
        
        # Strategy 2: Harvest profitable positions
        for position in sorted(summary.harvestable_positions, 
                              key=lambda p: p.get('profit_pct', 0), 
                              reverse=True):
            if shortfall <= 0:
                break
            
            plan['harvests'].append(position)
            shortfall -= position.get('harvest_value_usd', 0)
        
        if shortfall <= 0:
            plan['feasible'] = True
        
        return plan
    
    def execute_mobilization(self, plan: Dict, dry_run: bool = True) -> bool:
        """
        Execute a mobilization plan.
        
        Args:
            plan: Plan from plan_mobilization()
            dry_run: If True, just print what would happen
        
        Returns: Success bool
        """
        if not plan['feasible']:
            print(f"❌ Plan not feasible - shortfall: ${plan['shortfall']:.2f}")
            return False
        
        # Execute conversions
        for conv in plan['conversions']:
            print(f"\n🔄 Converting {conv.amount:.2f} {conv.from_asset} → {conv.to_asset} on {conv.exchange}")
            print(f"   Reason: {conv.reason}")
            
            if not dry_run:
                # TODO: Implement actual conversion via exchange API
                # For now, just print
                print("   ⚠️  Conversion not yet implemented - requires exchange API call")
        
        # Execute harvests
        for harvest in plan['harvests']:
            asset = harvest['asset']
            profit_pct = harvest.get('profit_pct', 0)
            net_profit = harvest.get('net_profit', 0)
            
            print(f"\n📤 Harvesting {asset}: +{profit_pct:.1f}% (${net_profit:.2f} profit)")
            
            if not dry_run:
                # TODO: Implement actual sell via exchange API
                print("   ⚠️  Harvest not yet implemented - requires exchange API call")
        
        return True
    
    def print_capital_report(self):
        """Print a comprehensive capital report."""
        summaries = self.audit_capital()
        
        print("\n" + "=" * 80)
        print("💰 AUREON CAPITAL MOBILIZATION REPORT")
        print("=" * 80)
        
        total_free = 0
        total_locked_count = 0
        total_harvestable = 0
        total_buying_power = 0
        
        for exch, summary in summaries.items():
            print(f"\n📊 {exch.upper()}")
            print("-" * 80)
            
            # Free stablecoins
            print("\n   💵 Free Stablecoins:")
            for stable, amt in summary.free_stablecoins.items():
                print(f"      {stable:8} ${amt:>10.2f}")
            print(f"      {'─' * 25}")
            print(f"      {'TOTAL':8} ${summary.total_stable_usd:>10.2f}")
            total_free += summary.total_stable_usd
            
            # Locked positions
            print(f"\n   🔒 Locked Positions: {len(summary.locked_positions)} assets")
            total_locked_count += len(summary.locked_positions)
            
            # Harvestable
            if summary.harvestable_positions:
                print(f"\n   🌾 Harvestable (Profitable): {len(summary.harvestable_positions)} positions")
                for pos in summary.harvestable_positions:
                    asset = pos['asset']
                    profit = pos.get('profit_pct', 0)
                    value = pos.get('harvest_value_usd', 0)
                    print(f"      {asset:8} +{profit:>6.1f}% = ${value:>8.2f}")
                print(f"      {'─' * 30}")
                print(f"      {'TOTAL':8}         ${summary.harvestable_value_usd:>8.2f}")
                total_harvestable += summary.harvestable_value_usd
            
            # Total buying power
            print(f"\n   💪 TOTAL BUYING POWER: ${summary.total_buying_power_usd:.2f}")
            print(f"      (Free: ${summary.total_stable_usd:.2f} + Harvestable: ${summary.harvestable_value_usd:.2f})")
            total_buying_power += summary.total_buying_power_usd
        
        print("\n" + "=" * 80)
        print(f"🌍 GLOBAL TOTALS:")
        print(f"   Free Stablecoins:     ${total_free:.2f}")
        print(f"   Locked Positions:     {total_locked_count} assets")
        print(f"   Harvestable Value:    ${total_harvestable:.2f}")
        print(f"   ─────────────────────────────────")
        print(f"   💪 TOTAL BUYING POWER: ${total_buying_power:.2f}")
        print("=" * 80 + "\n")


def main():
    """Demo the capital mobilizer."""
    mobilizer = AureonCapitalMobilizer()
    
    # Print capital report
    mobilizer.print_capital_report()
    
    # Example: Plan to mobilize $10 USDC on Binance
    print("\n🧪 TEST: Plan mobilization for $10 USDC buy on Binance")
    print("-" * 80)
    plan = mobilizer.plan_mobilization(target_quote='USDC', needed_amount=10.0, exchange='binance')
    
    print(f"\n📋 MOBILIZATION PLAN:")
    print(f"   Available now: ${plan['available']:.2f} USDC")
    print(f"   Needed: $10.00 USDC")
    print(f"   Shortfall: ${plan['shortfall']:.2f}")
    print(f"   Feasible: {'✅ YES' if plan['feasible'] else '❌ NO'}")
    
    if plan['conversions']:
        print(f"\n   🔄 Conversions needed: {len(plan['conversions'])}")
        for conv in plan['conversions']:
            print(f"      {conv.from_asset} → {conv.to_asset}: ${conv.amount:.2f}")
    
    if plan['harvests']:
        print(f"\n   🌾 Harvests needed: {len(plan['harvests'])}")
        for harv in plan['harvests']:
            print(f"      {harv['asset']}: +{harv.get('profit_pct', 0):.1f}% = ${harv.get('harvest_value_usd', 0):.2f}")
    
    if plan['feasible']:
        print("\n✅ This trade is feasible with capital mobilization!")
    else:
        print("\n❌ Not enough capital even after mobilization")


if __name__ == '__main__':
    main()
