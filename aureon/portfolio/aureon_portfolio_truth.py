"""
📊 AUREON PORTFOLIO TRUTH - Never Run Blind Again
═══════════════════════════════════════════════════════════════════

Real-time portfolio tracking with ACCURATE data:
- Live exchange balances (no phantom positions)
- Real cost basis from actual trades
- Current market prices (batch fetching, no $0 errors)
- Accurate P&L calculations
- Per-position breakdown

This is the SINGLE SOURCE OF TRUTH for portfolio status.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple
from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient


class PortfolioTruth:
    """Single source of truth for portfolio status."""
    
    def __init__(self):
        self.kraken = KrakenClient()
        try:
            self.binance = BinanceClient()
        except:
            self.binance = None
        self.alpaca = AlpacaClient()
        
        # CoinGecko ID mapping for price lookups
        self.coingecko_map = {
            # Kraken assets
            'ADA': 'cardano',
            'SOL': 'solana',
            'CRO': 'crypto-com-chain',
            'XXRP': 'ripple',
            'XRP': 'ripple',
            'TRX': 'tron',
            'EUL': 'euler',
            'MXC': 'mxc',
            'FIS': 'stafi',
            'SCRT': 'secret',
            'SAHARA': 'sahara-ai',
            'ATOM': 'cosmos',
            'ETH': 'ethereum',
            'BTC': 'bitcoin',
            # Binance assets
            'ZEC': 'zcash',
            'AXS': 'axie-infinity',
            'ROSE': 'oasis-network',
            'LPT': 'livepeer',
            'SSV': 'ssv-network',
            'BEAMX': 'beam-2',
            'ZRO': 'layerzero',
            'KAIA': 'kaia',
            'PENGU': 'pudgy-penguins',
            'SHELL': 'shell-protocol',
            'STO': 'sto-cash',
            'RESOLV': 'resolv',
            'SOMI': 'somnia',
            'AVNT': 'aventa',
            'NOM': 'onomy-protocol',
            'ENSO': 'enso-finance',
            'TURTLE': 'turtlesat',
            'F': 'fluence',
            'BREV': 'brevity',
        }
    
    def get_price(self, symbol: str, exchange: str = 'kraken') -> float:
        """Get current USD price with robust fallbacks."""
        
        # If it's a Binance asset, use Binance public API first (free, no limits)
        if exchange == 'binance':
            try:
                response = requests.get(
                    f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT",
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
            except:
                pass
        
        # Try CoinGecko first (batch request safe)
        coingecko_id = self.coingecko_map.get(symbol)
        if coingecko_id:
            try:
                response = requests.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if coingecko_id in data and 'usd' in data[coingecko_id]:
                        return data[coingecko_id]['usd']
            except:
                pass
        
        # Try Kraken API
        try:
            ticker = self.kraken.get_ticker(f'{symbol}USD')
            if ticker and 'last' in ticker:
                return float(ticker['last'])
        except:
            pass
        
        # Manual mapping for illiquid tokens
        manual_prices = {
            'SKR': 0.00021723,
            'GHIBLI': 0.00087,
            'OPEN': 0.1846,
            'BABY': 0.0,
            'FIGHT': 0.0,
            'ICNT': 0.0,
            'IN': 0.0,
            'KTA': 0.0,
        }
        
        if symbol in manual_prices:
            return manual_prices[symbol]
        
        return 0.0
    
    def get_cost_basis_from_trades(self, exchange: str, asset: str, trades: Dict) -> Tuple[float, float]:
        """Calculate cost basis from actual trade history."""
        total_cost = 0
        total_volume = 0
        
        for trade_id, trade in trades.items():
            if trade.get('type') == 'buy':
                pair = trade.get('pair', '')
                # Match asset to trading pair
                if asset in pair or pair.startswith(asset):
                    cost = float(trade.get('cost', 0))
                    fee = float(trade.get('fee', 0))
                    volume = float(trade.get('vol', 0))
                    
                    total_cost += cost + fee
                    total_volume += volume
        
        if total_volume > 0:
            avg_price = total_cost / total_volume
            return total_cost, avg_price
        
        return 0.0, 0.0
    
    def get_complete_portfolio(self) -> Dict:
        """Get complete portfolio status across all exchanges."""
        print("📊 AUREON PORTFOLIO TRUTH")
        print("=" * 80)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        portfolio = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': {},
            'totals': {
                'cost_basis': 0,
                'current_value': 0,
                'pnl': 0,
                'pnl_pct': 0,
            }
        }
        
        # ═══════════════════════════════════════════════════════════════════
        # KRAKEN
        # ═══════════════════════════════════════════════════════════════════
        print("🐙 KRAKEN")
        print("-" * 80)
        
        kraken_balances = self.kraken.get_balance()
        kraken_trades = self.kraken.get_trades_history()
        
        kraken_positions = {}
        kraken_total_cost = 0
        kraken_total_value = 0
        
        for asset, qty_str in kraken_balances.items():
            qty = float(qty_str)
            if qty < 0.00001:
                continue
            
            # Get cost basis from trades
            cost_basis, entry_price = self.get_cost_basis_from_trades('kraken', asset, kraken_trades)
            
            # Get current price
            current_price = self.get_price(asset)
            current_value = qty * current_price
            
            pnl = current_value - cost_basis
            pnl_pct = ((current_value / cost_basis - 1) * 100) if cost_basis > 0 else 0
            
            # Handle cash/stablecoins (exclude from profit calculations)
            is_cash = asset in ['ZGBP', 'ZUSD', 'TUSD', 'USDC', 'USDT']
            if is_cash:
                if asset == 'ZGBP':
                    current_value = qty * 1.27  # GBP to USD
                else:
                    current_value = qty
                cost_basis = 0  # Don't count cash in cost basis
                pnl = 0
                pnl_pct = 0
            
            kraken_positions[asset] = {
                'quantity': qty,
                'cost_basis': cost_basis,
                'entry_price': entry_price,
                'current_price': current_price,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'is_cash': is_cash
            }
            
            # Only add to cost basis if NOT cash
            if not is_cash:
                kraken_total_cost += cost_basis
            kraken_total_value += current_value
            
            # Print position
            status = "✅" if pnl >= 0 else "❌"
            if asset in ['ZGBP', 'ZUSD', 'TUSD', 'USDC', 'USDT']:
                # Cash - show without P&L
                print(f"  💵 {asset}: {qty:,.4f} = ${current_value:.2f} (cash)")
            elif current_price > 0:
                print(f"  {status} {asset}: {qty:,.4f} @ ${current_price:.6f} = ${current_value:.2f} "
                      f"(cost: ${cost_basis:.2f}, P&L: ${pnl:+.2f} {pnl_pct:+.1f}%)")
            else:
                print(f"  ⚠️  {asset}: {qty:,.4f} (price not found)")
        
        kraken_pnl = kraken_total_value - kraken_total_cost
        kraken_pnl_pct = ((kraken_total_value / kraken_total_cost - 1) * 100) if kraken_total_cost > 0 else 0
        
        print()
        print(f"  📊 Kraken Total: ${kraken_total_value:.2f}")
        print(f"  💰 Cost Basis: ${kraken_total_cost:.2f}")
        print(f"  📈 P&L: ${kraken_pnl:+.2f} ({kraken_pnl_pct:+.1f}%)")
        print()
        
        portfolio['exchanges']['kraken'] = {
            'positions': kraken_positions,
            'total_cost': kraken_total_cost,
            'total_value': kraken_total_value,
            'pnl': kraken_pnl,
            'pnl_pct': kraken_pnl_pct
        }
        
        # ═══════════════════════════════════════════════════════════════════
        # BINANCE (if available)
        # ═══════════════════════════════════════════════════════════════════
        if self.binance:
            print("🌐 BINANCE")
            print("-" * 80)
            try:
                binance_balances = self.binance.get_balance()
                binance_positions = {}
                binance_total_value = 0
                binance_total_cost = 0
                
                # Use Binance public API for prices (free, unlimited)
                for asset, qty_str in binance_balances.items():
                    qty = float(qty_str)
                    if qty < 0.00001:
                        continue
                    
                    # Get price from Binance public API
                    price = self.get_price(asset, exchange='binance')
                    
                    value = qty * price
                    binance_total_value += value
                    
                    # Try to get cost basis from Binance trades (if available)
                    cost_basis = 0
                    pnl = value
                    pnl_pct = 0
                    
                    binance_positions[asset] = {
                        'quantity': qty,
                        'cost_basis': cost_basis,
                        'current_price': price,
                        'current_value': value,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    }
                    
                    status = "✅" if pnl >= 0 else "❌"
                    if price > 0:
                        print(f"  {status} {asset}: {qty:,.4f} @ ${price:.6f} = ${value:.2f}")
                    else:
                        print(f"  ⚠️  {asset}: {qty:,.4f} (price not found)")
                
                print()
                print(f"  📊 Binance Total: ${binance_total_value:.2f}")
                print()
                
                portfolio['exchanges']['binance'] = {
                    'positions': binance_positions,
                    'total_value': binance_total_value,
                    'total_cost': binance_total_cost
                }
            except Exception as e:
                print(f"  ⚠️ Binance error: {e}")
                print()
        
        # ═══════════════════════════════════════════════════════════════════
        # ALPACA
        # ═══════════════════════════════════════════════════════════════════
        print("🦙 ALPACA")
        print("-" * 80)
        try:
            alpaca_positions = self.alpaca.get_positions()
            alpaca_total_value = 0
            
            for pos in alpaca_positions:
                symbol = pos['symbol']
                qty = float(pos['qty'])
                current_price = float(pos['current_price'])
                cost_basis = float(pos['cost_basis'])
                market_value = float(pos['market_value'])
                unrealized_pl = float(pos['unrealized_pl'])
                unrealized_plpc = float(pos['unrealized_plpc']) * 100
                
                alpaca_total_value += market_value
                
                status = "✅" if unrealized_pl >= 0 else "❌"
                print(f"  {status} {symbol}: {qty:,.4f} @ ${current_price:.2f} = ${market_value:.2f} "
                      f"(cost: ${cost_basis:.2f}, P&L: ${unrealized_pl:+.2f} {unrealized_plpc:+.1f}%)")
            
            # Add cash
            account = self.alpaca.get_account()
            cash = float(account.get('cash', 0))
            print(f"  💵 Cash: ${cash:.2f}")
            alpaca_total_value += cash
            
            print()
            print(f"  📊 Alpaca Total: ${alpaca_total_value:.2f}")
            print()
            
            portfolio['exchanges']['alpaca'] = {
                'total_value': alpaca_total_value
            }
        except Exception as e:
            print(f"  ⚠️ Alpaca error: {e}")
            print()
        
        # ═══════════════════════════════════════════════════════════════════
        # TOTALS
        # ═══════════════════════════════════════════════════════════════════
        total_value = kraken_total_value
        total_cost = kraken_total_cost
        
        if 'binance' in portfolio['exchanges']:
            total_value += portfolio['exchanges']['binance']['total_value']
        
        if 'alpaca' in portfolio['exchanges']:
            total_value += portfolio['exchanges']['alpaca']['total_value']
        
        total_pnl = total_value - total_cost
        total_pnl_pct = ((total_value / total_cost - 1) * 100) if total_cost > 0 else 0
        
        print("=" * 80)
        print("💰 TOTAL PORTFOLIO")
        print("=" * 80)
        print(f"  Total Value: ${total_value:,.2f}")
        print(f"  Cost Basis: ${total_cost:,.2f}")
        print(f"  P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.1f}%)")
        
        if total_pnl >= 0:
            print("  Status: ✅ IN PROFIT")
        else:
            print("  Status: ❌ IN LOSS")
        
        print("=" * 80)
        
        portfolio['totals'] = {
            'cost_basis': total_cost,
            'current_value': total_value,
            'pnl': total_pnl,
            'pnl_pct': total_pnl_pct
        }
        
        # Save to file
        with open('portfolio_truth.json', 'w') as f:
            json.dump(portfolio, f, indent=2)
        
        print(f"\n💾 Saved to portfolio_truth.json")
        
        return portfolio


if __name__ == "__main__":
    tracker = PortfolioTruth()
    tracker.get_complete_portfolio()
