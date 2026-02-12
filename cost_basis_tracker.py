"""
💰 COST BASIS TRACKER
═══════════════════════════════════════════════════════════════

Tracks real purchase prices for all positions across exchanges.
This data feeds into the ecosystem to prevent selling at a loss.

Features:
- Fetches real trade history from exchanges
- Calculates FIFO/average cost basis
- Persists to JSON for session continuity
- Provides profit/loss checks before any sale

Usage:
    tracker = CostBasisTracker()
    tracker.sync_from_exchanges()  # Fetch real purchase prices
    
    # Before selling:
    can_sell, info = tracker.can_sell_profitably('BTCUSDC', current_price=95000)
    if can_sell:
        # Proceed with sale
    else:
        print(f"Would lose ${info['potential_loss']}")
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
import time
import builtins
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List

# ═══════════════════════════════════════════════════════════════════════════════
# 🔇 WINDOWS UTF-8 FIX - MUST BE BEFORE ANY PRINT STATEMENTS!
# ═══════════════════════════════════════════════════════════════════════════════
import sys
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
        # Only wrap if not already UTF-8 wrapped AND buffer is valid (prevents re-wrapping + closed buffer errors)
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

def _safe_print(*args, **kwargs):
    """Safe print that handles closed stdout/stderr."""
    try:
        builtins.print(*args, **kwargs)
    except (ValueError, OSError, IOError):
        # Silently ignore if stdout/stderr is closed
        pass

load_dotenv()

COST_BASIS_FILE = "cost_basis_history.json"


@dataclass
class Trade:
    """Represents a single buy trade lot."""
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)
    fee: float = 0.0
    order_id: Optional[str] = None

"""
💰 COST BASIS TRACKER
═══════════════════════════════════════════════════════════════

Tracks real purchase prices for all positions across exchanges.
This data feeds into the ecosystem to prevent selling at a loss.

Features:
- Fetches real trade history from exchanges
- Calculates FIFO/average cost basis
- Persists to JSON for session continuity
- Provides profit/loss checks before any sale

Usage:
    tracker = CostBasisTracker()
    tracker.sync_from_exchanges()  # Fetch real purchase prices
    
    # Before selling:
    can_sell, info = tracker.can_sell_profitably('BTCUSDC', current_price=95000)
    if can_sell:
        # Proceed with sale
    else:
        print(f"Would lose ${info['potential_loss']}")
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
import time
import builtins
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List

# ═══════════════════════════════════════════════════════════════════════════════
# 🔇 WINDOWS UTF-8 FIX - MUST BE BEFORE ANY PRINT STATEMENTS!
# ═══════════════════════════════════════════════════════════════════════════════
import sys
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
        # Only wrap if not already UTF-8 wrapped AND buffer is valid (prevents re-wrapping + closed buffer errors)
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

def _safe_print(*args, **kwargs):
    """Safe print that handles closed stdout/stderr."""
    try:
        builtins.print(*args, **kwargs)
    except (ValueError, OSError, IOError):
        # Silently ignore if stdout/stderr is closed
        pass

load_dotenv()

COST_BASIS_FILE = "cost_basis_history.json"


@dataclass
class Trade:
    """Represents a single buy trade lot."""
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)
    fee: float = 0.0
    order_id: Optional[str] = None

class CostBasisTracker:
    """Track real cost basis for all positions."""
    
    def __init__(self, filepath: str = COST_BASIS_FILE, clients=None):
        self.filepath = filepath
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trade_lots: Dict[str, List[Trade]] = {}  # 🆕 For FIFO
        self.last_sync: float = 0
        self.clients = clients or {}
        self._load()
    
    def set_clients(self, clients):
        """Inject shared exchange clients."""
        self.clients = clients

    @staticmethod
    def _strip_known_quote(symbol: str) -> str:
        """Strip a known quote suffix without using rstrip character semantics."""
        symbol = (symbol or '').replace('/', '')
        for quote in ('USDT', 'USDC', 'ZUSD', 'USD', 'EUR', 'GBP', 'BTC', 'ETH'):
            if symbol.endswith(quote) and len(symbol) > len(quote):
                return symbol[:-len(quote)]
        return symbol

    @staticmethod
    def _normalize_kraken_pair(pair: str) -> str:
        """Convert Kraken pair naming (e.g., XXBTZUSD, XPEPEZUSD) to BTCUSD/PEPEUSD style."""
        raw = (pair or '').upper()
        p = raw.replace('/', '')
        if not p:
            return p

        if '/' in raw:
            base, quote = raw.split('/', 1)
            base = base.lstrip('XZ')
            quote = quote.lstrip('XZ')
            if base in ('XBT', 'BT'):
                base = 'BTC'
            if base in ('XDG', 'DG'):
                base = 'DOGE'
            if quote == 'XBT':
                quote = 'BTC'
            return f"{base}{quote}"

        quotes = ('USDT', 'USDC', 'USD', 'EUR', 'GBP', 'BTC', 'ETH')
        for quote in quotes:
            zq = f"Z{quote}"
            if p.endswith(zq):
                base = p[:-len(zq)]
            elif p.endswith(quote):
                base = p[:-len(quote)]
            else:
                continue

            if base.startswith(('XX', 'ZZ')):
                base = base[2:]
            elif base.startswith(('X', 'Z')):
                base = base[1:]

            if base in ('XBT', 'BT'):
                base = 'BTC'
            if base in ('XDG', 'DG'):
                base = 'DOGE'
            return f"{base}{quote}"

        stripped = p
        if stripped.startswith(('XX', 'ZZ')):
            stripped = stripped[2:]
        elif stripped.startswith(('X', 'Z')):
            stripped = stripped[1:]
        if stripped in ('XBT', 'BT'):
            return 'BTC'
        if stripped in ('XDG', 'DG'):
            return 'DOGE'
        return stripped.replace('XBT', 'BTC')

    def _load(self):
        """Load cost basis data from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self.positions = data.get('positions', {})
                    self.last_sync = data.get('last_sync', 0)
                    
                    # 🆕 Load trade lots for FIFO
                    trade_lots_data = data.get('trade_lots', {})
                    self.trade_lots = {
                        k: [Trade(**t) for t in v]
                        for k, v in trade_lots_data.items()
                    }
                    
                    _safe_print(f"📊 Cost Basis Tracker: Loaded {len(self.positions)} positions and {len(self.trade_lots)} trade lots from {self.filepath}")
            except Exception as e:
                _safe_print(f"⚠️ Failed to load cost basis file: {e}")
                self.positions = {}
                self.trade_lots = {}
        
        # 🆕 SYNC with Orca's Tracked Positions
        if os.path.exists("tracked_positions.json"):
            try:
                with open("tracked_positions.json", "r") as f:
                    tracked = json.load(f)
                    added_count = 0
                    for sym, data in tracked.items():
                        # Normalize symbol (remove / for matching)
                        norm_sym = sym.replace('/', '')
                        if norm_sym not in self.positions:
                            self.positions[norm_sym] = {
                                'exchange': data.get('exchange', 'unknown'),
                                'avg_entry_price': data.get('entry_price', 0),
                                'total_quantity': data.get('entry_qty', 0),
                                'total_cost': data.get('entry_cost', 0),
                                'total_fees': 0,
                                'trade_count': 1,
                                'last_trade': data.get('entry_time', time.time()),
                                'synced_at': time.time()
                            }
                            added_count += 1
                    if added_count > 0:
                        _safe_print(f"📊 Cost Basis Tracker: Integrated {added_count} positions from tracked_positions.json")
            except Exception as e:
                _safe_print(f"⚠️ Failed to integrate tracked positions: {e}")
    
    def _save(self):
        """Save cost basis data to file."""
        try:
            # 🆕 Serialize trade lots
            trade_lots_serializable = {
                k: [t.__dict__ for t in v]
                for k, v in self.trade_lots.items()
            }
            
            data = {
                'positions': self.positions,
                'trade_lots': trade_lots_serializable,
                'last_sync': self.last_sync,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save cost basis file: {e}")
    
    def sync_from_binance(self, symbols: list = None) -> int:
        """Sync cost basis from Binance trade history.
        
        Returns number of positions updated.
        """
        try:
            if self.clients and 'binance' in self.clients:
                client = self.clients['binance']
            else:
                from binance_client import BinanceClient
                client = get_binance_client()
        except Exception as e:
            print(f"⚠️ Failed to initialize Binance client: {e}")
            return 0
        
        # Get current balances to know which symbols to check
        account = client.account()
        balances = account.get('balances', [])
        
        updated = 0
        for bal in balances:
            asset = bal['asset']
            free = float(bal.get('free', 0))
            locked = float(bal.get('locked', 0))
            total = free + locked
            
            if total <= 0:
                continue
            
            # Skip stablecoins and Binance Earn (LD) assets
            if asset in ['USDC', 'USDT', 'USD', 'EUR', 'GBP', 'BUSD', 'FDUSD', 'TUSD'] or asset.startswith('LD'):
                continue
            
            # 🔧 Only try EUR for major coins that Binance actually supports
            BINANCE_EUR_SUPPORTED = {'BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'SHIB', 'MATIC', 'LTC', 'AVAX', 'LINK', 'ATOM'}
            quote_options = ['USDC', 'USDT']
            if asset in BINANCE_EUR_SUPPORTED:
                quote_options.append('EUR')
            
            # Try different quote currencies
            for quote in quote_options:
                symbol = f"{asset}{quote}"
                try:
                    cost_basis = client.calculate_cost_basis(symbol)
                    if cost_basis and cost_basis['total_quantity'] > 0:
                        position_key = f"binance:{symbol}"
                        self.positions[position_key] = {
                            'exchange': 'binance',
                            'symbol': symbol,
                            'asset': asset,
                            'quote': quote,
                            'avg_entry_price': cost_basis['avg_entry_price'],
                            'total_quantity': cost_basis['total_quantity'],
                            'total_cost': cost_basis['total_cost'],
                            'total_fees': cost_basis['total_fees'],
                            'trade_count': cost_basis['trade_count'],
                            'first_trade': cost_basis['first_trade'],
                            'last_trade': cost_basis['last_trade'],
                            'synced_at': time.time()
                        }
                        updated += 1
                        _safe_print(f"   📦 {position_key}: avg entry ${cost_basis['avg_entry_price']:.6f} "
                              f"({cost_basis['trade_count']} trades)")
                        break
                except Exception as e:
                    continue
        
        self.last_sync = time.time()
        self._save()
        return updated
    
    def sync_from_kraken(self) -> int:
        """Sync cost basis from Kraken trade history."""
        try:
            if self.clients and 'kraken' in self.clients:
                client = self.clients['kraken']
            else:
                from kraken_client import KrakenClient, get_kraken_client
                client = get_kraken_client()

            if getattr(client, 'dry_run', False):
                print("   ⚪ Kraken in dry-run mode - skipping")
                return 0
        except Exception as e:
            print(f"   ⚠️ Failed to initialize Kraken client: {e}")
            return 0
        
        # Get trade history
        try:
            trades = client.get_trades_history()
            if not trades:
                print("   ⚪ No Kraken trade history found")
                return 0
        except Exception as e:
            print(f"   ⚠️ Failed to get Kraken trade history: {e}")
            return 0
        
        # Group trades by pair and calculate cost basis
        pair_trades = {}
        for trade_id, trade in trades.items():
            pair = trade.get('pair', '')
            if pair not in pair_trades:
                pair_trades[pair] = []
            pair_trades[pair].append(trade)
        
        updated = 0
        for pair, pair_trade_list in pair_trades.items():
            # Reset trade lots for this pair to rebuild from history
            symbol_norm = self._normalize_kraken_pair(pair)
            position_key = f"kraken:{symbol_norm}"
            self.trade_lots[position_key] = []

            total_qty = 0.0
            total_cost = 0.0
            total_fees = 0.0
            buy_trades = 0
            first_trade = None
            last_trade = None
            
            for trade in sorted(pair_trade_list, key=lambda x: float(x.get('time', 0))):
                trade_type = trade.get('type', '')
                qty = float(trade.get('vol', 0))
                price = float(trade.get('price', 0))
                fee = float(trade.get('fee', 0))
                timestamp = float(trade.get('time', 0))
                
                if trade_type == 'buy':
                    # Add to lots for FIFO
                    self.trade_lots[position_key].append(Trade(price=price, quantity=qty, fee=fee, timestamp=timestamp))
                    
                    total_qty += qty
                    total_cost += qty * price
                    total_fees += fee
                    buy_trades += 1
                elif trade_type == 'sell':
                    # Apply FIFO logic to lots
                    sell_qty_rem = qty
                    for lot in self.trade_lots.get(position_key, []):
                        if sell_qty_rem <= 0: break
                        take_qty = min(lot.quantity, sell_qty_rem)
                        lot.quantity -= take_qty
                        sell_qty_rem -= take_qty

                    total_qty -= qty
                    if total_qty > 0:
                        # Recalculate average cost from remaining lots
                        new_total_cost = sum(l.price * l.quantity for l in self.trade_lots.get(position_key, []))
                        total_cost = new_total_cost
                
                if first_trade is None or timestamp < first_trade:
                    first_trade = timestamp
                if last_trade is None or timestamp > last_trade:
                    last_trade = timestamp
            
            if total_qty > 0 and buy_trades > 0:
                avg_entry = total_cost / total_qty
                # Normalize pair name without stripping in-symbol X/Z characters
                symbol = self._normalize_kraken_pair(pair)
                position_key = f"kraken:{symbol}"
                
                self.positions[position_key] = {
                    'exchange': 'kraken',
                    'symbol': symbol,
                    'asset': symbol[:-3] if len(symbol) > 3 else symbol,
                    'quote': symbol[-3:] if len(symbol) > 3 else 'USD',
                    'avg_entry_price': avg_entry,
                    'total_quantity': total_qty,
                    'total_cost': total_cost,
                    'total_fees': total_fees,
                    'trade_count': buy_trades,
                    'first_trade': int(first_trade * 1000) if first_trade else None,
                    'last_trade': int(last_trade * 1000) if last_trade else None,
                    'synced_at': time.time()
                }
                updated += 1
                _safe_print(f"   📦 {position_key}: avg entry ${avg_entry:.6f} ({buy_trades} trades)")
        
        self._save()
        return updated
    
    def sync_from_alpaca(self) -> int:
        """Sync cost basis from Alpaca trade history."""
        try:
            if self.clients and 'alpaca' in self.clients:
                client = self.clients['alpaca']
            else:
                from alpaca_client import AlpacaClient
                client = AlpacaClient()
        except Exception as e:
            print(f"   ⚠️ Failed to initialize Alpaca client: {e}")
            return 0
        
        # Alpaca provides positions with avg_entry_price directly!
        try:
            positions = client.get_positions()
            if not positions:
                print("   ⚪ No Alpaca positions found")
                return 0
        except Exception as e:
            print(f"   ⚠️ Failed to get Alpaca positions: {e}")
            return 0
        
        updated = 0
        for pos in positions:
            symbol = pos.get('symbol', '')
            avg_entry = float(pos.get('avg_entry_price', 0))
            qty = float(pos.get('qty', 0))
            
            if avg_entry > 0 and qty > 0:
                position_key = f"alpaca:{symbol}"
                
                # 🆕 Create a single trade lot for Alpaca positions since it gives aggregates
                self.trade_lots[position_key] = [Trade(price=avg_entry, quantity=qty)]
                
                self.positions[position_key] = {
                    'exchange': 'alpaca',
                    'symbol': symbol,
                    'asset': symbol,
                    'quote': 'USD',
                    'avg_entry_price': avg_entry,
                    'total_quantity': qty,
                    'total_cost': avg_entry * qty,
                    'total_fees': 0,  # Alpaca has zero commission
                    'trade_count': 1,  # Position-based, not trade-based
                    'synced_at': time.time()
                }
                updated += 1
                _safe_print(f"   📦 {position_key}: avg entry ${avg_entry:.6f}")
        
        self._save()
        return updated
    
    def sync_from_capital(self) -> int:
        """Sync cost basis from Capital.com positions."""
        try:
            if self.clients and 'capital' in self.clients:
                client = self.clients['capital']
            else:
                from capital_client import CapitalClient
                client = CapitalClient()
            
            if not getattr(client, 'enabled', False):
                print("   ⚪ Capital.com not authenticated - skipping")
                return 0
        except Exception as e:
            print(f"   ⚠️ Failed to initialize Capital client: {e}")
            return 0
        
        # Capital.com provides positions with entry price
        try:
            positions = client.get_positions()
            if not positions:
                print("   ⚪ No Capital.com positions found")
                return 0
        except Exception as e:
            print(f"   ⚠️ Failed to get Capital.com positions: {e}")
            return 0
        
        updated = 0
        for pos in positions:
            symbol = pos.get('market', {}).get('epic', '') or pos.get('epic', '')
            avg_entry = float(pos.get('position', {}).get('openLevel', 0) or pos.get('openLevel', 0))
            qty = float(pos.get('position', {}).get('size', 0) or pos.get('size', 0))
            
            if avg_entry > 0 and qty != 0:
                position_key = f"capital:{symbol}"

                # 🆕 Create a single trade lot for Capital positions
                if qty > 0: # Only for LONG positions
                    self.trade_lots[position_key] = [Trade(price=avg_entry, quantity=abs(qty))]

                self.positions[position_key] = {
                    'exchange': 'capital',
                    'symbol': symbol,
                    'asset': symbol,
                    'quote': 'USD',
                    'avg_entry_price': avg_entry,
                    'total_quantity': abs(qty),
                    'total_cost': avg_entry * abs(qty),
                    'total_fees': 0,  # Spread-based
                    'trade_count': 1,
                    'synced_at': time.time(),
                    'direction': 'LONG' if qty > 0 else 'SHORT'
                }
                updated += 1
                direction = '📈' if qty > 0 else '📉'
                _safe_print(f"   {direction} {position_key}: entry ${avg_entry:.4f} x {abs(qty)}")
        
        self._save()
        return updated
    
    def sync_from_exchanges(self) -> int:
        """Sync cost basis from ALL exchanges."""
        print("\n📊 SYNCING COST BASIS FROM ALL EXCHANGES...")
        print("=" * 60)
        
        total = 0
        
        print("\n🟡 Syncing from Binance...")
        total += self.sync_from_binance()
        
        print("\n🐙 Syncing from Kraken...")
        total += self.sync_from_kraken()
        
        print("\n🦙 Syncing from Alpaca...")
        total += self.sync_from_alpaca()
        
        print("\n💼 Syncing from Capital.com...")
        total += self.sync_from_capital()
        
        print(f"\n✅ Synced {total} positions with real cost basis")
        print("=" * 60)
        
        return total
    
    def _find_position(self, symbol: str, exchange: str = None) -> Optional[tuple[Dict[str, Any], str]]:
        """
        🔍 ENHANCED: 5-strategy symbol matching with quote currency swapping.
        
        Returns: (position_dict, matched_key) if found, else (None, None)
        
        Strategies:
        1. Direct match with exchange prefix (binance:SHELL/USDT)
        2. Match without exchange prefix (SHELL/USDT)
        3. Normalized format without slashes (binance:SHELLUSDT, SHELLUSDT)
        4. Quote currency swapping (SHELL/USDT → SHELLUSDC, SHELL/USD)
        5. Deep base asset match (SHELL → any SHELL-based pair)
        """
        pos = None
        matched_key = None

        def _is_open_position(candidate: Optional[Dict[str, Any]]) -> bool:
            """Ignore stale/closed snapshots so they don't shadow real open positions."""
            if not candidate:
                return False
            try:
                qty = float(candidate.get('total_quantity', 0) or 0)
            except (TypeError, ValueError):
                return False
            return qty > 0.0000001

        def _exchange_matches(candidate_key: str, candidate: Optional[Dict[str, Any]]) -> bool:
            """When exchange context is provided, don't cross-match to another venue."""
            if not exchange:
                return True
            normalized_exchange = exchange.lower()
            if candidate_key.startswith(f"{normalized_exchange}:"):
                return True
            candidate_exchange = str((candidate or {}).get('exchange', '')).lower()
            return candidate_exchange == normalized_exchange
        
        # Strategy 1: Direct match with exchange context
        if exchange:
            position_key = f"{exchange.lower()}:{symbol}"
            pos = self.positions.get(position_key)
            if _is_open_position(pos):
                return (pos, position_key)
        
        # Strategy 2: Try without exchange prefix
        pos = self.positions.get(symbol)
        if _is_open_position(pos) and _exchange_matches(symbol, pos):
            return (pos, symbol)
        
        # Strategy 3: Try normalized (no slashes)
        norm_symbol = symbol.replace('/', '')
        if exchange:
            norm_key = f"{exchange.lower()}:{norm_symbol}"
            pos = self.positions.get(norm_key)
            if _is_open_position(pos):
                return (pos, norm_key)

        pos = self.positions.get(norm_symbol)
        if _is_open_position(pos) and _exchange_matches(norm_symbol, pos):
            return (pos, norm_symbol)
        
        # Strategy 4: Try swapping quote currencies (USDT ↔ USDC ↔ USD)
        # Extract base asset
        if '/' in symbol:
            base = symbol.split('/')[0]
        else:
            base = self._strip_known_quote(symbol)
        
        # Try all quote currency combinations
        for quote_in in ['USDT', 'USDC', 'USD', 'EUR', 'GBP']:
            if symbol.endswith(quote_in) or symbol.endswith(f'/{quote_in}'):
                # Try other quotes
                for quote_out in ['USDT', 'USDC', 'USD', 'ZUSD', 'USDC.P']:
                    # Try with slash and without
                    test_symbols = [
                        f"{base}/{quote_out}",
                        f"{base}{quote_out}",
                    ]
                    
                    for test_symbol in test_symbols:
                        if exchange:
                            test_key = f"{exchange.lower()}:{test_symbol}"
                            pos = self.positions.get(test_key)
                            if _is_open_position(pos):
                                # Debug message
                                # print(f"   ✓ Matched via quote swap: {symbol} → {test_key}")
                                return (pos, test_key)

                        pos = self.positions.get(test_symbol)
                        if _is_open_position(pos) and _exchange_matches(test_symbol, pos):
                            # Debug message
                            # print(f"   ✓ Matched via quote swap: {symbol} → {test_symbol}")
                            return (pos, test_symbol)
        
        # Strategy 5: Deep base asset match
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol
        # Remove common quote assets to find base
        for quote in ['USD', 'USDT', 'USDC', 'EUR', 'GBP', 'BTC', 'ETH']:
            if base_asset.endswith(quote) and len(base_asset) > len(quote):
                base_asset = base_asset[:-len(quote)]
                break
        
        for s, p in self.positions.items():
            stored_symbol = p.get('symbol') or s
            # Strip exchange prefix (e.g., kraken:EUL -> EUL) before base matching
            symbol_part = stored_symbol.split(':', 1)[1] if ':' in stored_symbol else stored_symbol
            normalized_symbol = symbol_part.replace('/', '')
            if (
                normalized_symbol.startswith(base_asset)
                and _is_open_position(p)
                and _exchange_matches(s, p)
            ):
                return (p, s)
        
        return (None, None)
    
    def get_cost_basis(self, symbol: str, exchange: str = None) -> Optional[Dict[str, Any]]:
        """Get cost basis for a symbol, optionally scoped to an exchange."""
        pos, matched_key = self._find_position(symbol, exchange)
        return pos

    def get_entry_price(self, symbol: str, exchange: str = None) -> Optional[float]:
        """Get average entry price for a symbol using 5-strategy matching."""
        pos, matched_key = self._find_position(symbol, exchange)
        if pos:
            # Prefer verified fills when available
            if pos.get('fills_verified') and pos.get('avg_fill_price'):
                return pos.get('avg_fill_price')
            return pos.get('avg_entry_price')
        return None

    def get_verified_entry_price(self, symbol: str, exchange: str = None) -> Optional[float]:
        """Return entry price only if backed by verified fills + order_id."""
        pos, matched_key = self._find_position(symbol, exchange)
        if not pos:
            return None
        if not pos.get('fills_verified'):
            return None
        if not pos.get('last_order_id'):
            return None
        return pos.get('avg_fill_price') or pos.get('avg_entry_price')
    
    def set_entry_price(self, symbol: str, price: float, quantity: float, 
                       exchange: str = 'binance', fee: float = 0.0, order_id: str = None):
        """Manually set entry price for a position (for new trades)."""
        asset = symbol[:-4] if symbol.endswith(('USDC', 'USDT')) else symbol[:-3]
        quote = symbol[-4:] if symbol.endswith(('USDC', 'USDT')) else symbol[-3:]
        
        # Use a unique key for each position: exchange + symbol
        position_key = f"{exchange.lower()}:{symbol}"
        
        # 🆕 Also add to trade_lots for FIFO
        if position_key not in self.trade_lots:
            self.trade_lots[position_key] = []
        self.trade_lots[position_key].append(Trade(price=price, quantity=quantity, fee=fee, order_id=order_id))

        # 🔧 ALSO store normalized versions for fallback matching
        norm_symbol = symbol.replace('/', '')  # Remove slashes
        norm_key = f"{exchange.lower()}:{norm_symbol}"

        position_data = {
            'exchange': exchange,
            'symbol': symbol,
            'asset': asset,
            'quote': quote,
            'avg_entry_price': price,
            'total_quantity': quantity,
            'total_cost': price * quantity,
            'total_fees': fee,
            'trade_count': 1,
            'first_trade': int(time.time() * 1000),
            'last_trade': int(time.time() * 1000),
            'synced_at': time.time(),
            'source': 'manual',
            'order_ids': [order_id] if order_id else [],
            'last_order_id': order_id,
            'avg_fill_price': price,
            'fills_verified': True if order_id else False,
            'last_fills': []
        }
        
        # Store under BOTH keys for better matching
        self.positions[position_key] = position_data
        if norm_symbol != symbol:
            self.positions[norm_key] = position_data.copy()
            # 🆕 Copy trade lots for normalized key
            self.trade_lots[norm_key] = self.trade_lots[position_key][:]
        
        self._save()
        _safe_print(f"   💾 Logged entry: {position_key} @ ${price:.6f} x {quantity} (Order: {order_id})")
        if norm_symbol != symbol:
            _safe_print(f"      Also indexed as: {norm_key}")
    
    def record_trade(self, symbol: str, side: str, quantity: float, price: float,
                    exchange: str, fee: float = 0.0, order_id: str = None) -> Dict[str, Any]:
        """
        Record a trade using FIFO accounting for cost basis.
        
        This is the central method for all trade recording - handles both buys and sells
        with proper FIFO cost basis calculation.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDC')
            side: 'buy' or 'sell'
            quantity: Quantity traded
            price: Price per unit
            exchange: Exchange name
            fee: Transaction fee
            order_id: Order ID for verification
            
        Returns:
            Dict with trade result info including realized P&L for sells
        """
        if quantity <= 0 or price <= 0:
            return {'error': 'Invalid quantity or price'}
        
        is_buy = side.upper() == 'BUY'
        position_key = f"{exchange.lower()}:{symbol}"
        
        # Initialize position if it doesn't exist
        if position_key not in self.positions:
            self.positions[position_key] = {
                'exchange': exchange,
                'symbol': symbol,
                'asset': symbol.split('/')[0] if '/' in symbol else symbol.rstrip('USDT').rstrip('USDC').rstrip('USD'),
                'quote': symbol.split('/')[1] if '/' in symbol else symbol[-3:],
                'avg_entry_price': 0,
                'total_quantity': 0,
                'total_cost': 0,
                'total_fees': 0,
                'trade_count': 0,
                'first_trade': int(time.time() * 1000),
                'last_trade': int(time.time() * 1000),
                'synced_at': time.time(),
                'order_ids': [],
                'last_order_id': order_id,
                'avg_fill_price': price,
                'fills_verified': True if order_id else False,
                'last_fills': []
            }
            self.trade_lots[position_key] = []
        
        pos = self.positions[position_key]
        lots = self.trade_lots.get(position_key, [])
        
        result = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'exchange': exchange,
            'fee': fee,
            'order_id': order_id
        }
        
        if is_buy:
            # BUY: Add to lots
            new_lot = Trade(price=price, quantity=quantity, fee=fee, timestamp=time.time(), order_id=order_id)
            lots.append(new_lot)
            
            # Update aggregates
            pos['total_quantity'] += quantity
            pos['total_cost'] += quantity * price
            pos['total_fees'] += fee
            pos['trade_count'] += 1
            pos['avg_entry_price'] = pos['total_cost'] / pos['total_quantity'] if pos['total_quantity'] > 0 else 0
            pos['last_trade'] = int(time.time() * 1000)
            if order_id and order_id not in pos.get('order_ids', []):
                pos['order_ids'].append(order_id)
            pos['last_order_id'] = order_id
            pos['avg_fill_price'] = price
            pos['fills_verified'] = True if order_id else pos.get('fills_verified', False)
            
            result['action'] = 'bought'
            result['new_quantity'] = pos['total_quantity']
            result['new_cost_basis'] = pos['total_cost']
            
        else:
            # SELL: Use FIFO to calculate cost basis of sale
            sell_qty_remaining = quantity
            cost_basis_of_sale = 0.0
            realized_pnl = 0.0
            
            # Process lots in FIFO order (oldest first)
            lots_to_remove = []
            for i, lot in enumerate(lots):
                if sell_qty_remaining <= 0:
                    break
                
                qty_from_lot = min(lot.quantity, sell_qty_remaining)
                cost_from_lot = qty_from_lot * lot.price
                
                cost_basis_of_sale += cost_from_lot
                realized_pnl += qty_from_lot * (price - lot.price)  # Gross P&L
                
                # Reduce lot quantity
                lot.quantity -= qty_from_lot
                sell_qty_remaining -= qty_from_lot
                
                # Mark empty lots for removal
                if lot.quantity <= 0.000001:
                    lots_to_remove.append(i)
            
            # Remove empty lots (in reverse order to maintain indices)
            for i in reversed(lots_to_remove):
                lots.pop(i)
            
            # Account for fees (only exit fee since entry fees are in cost basis)
            exit_fee = quantity * price * 0.001  # Assume 0.1% fee
            realized_pnl -= exit_fee
            
            # Update aggregates
            pos['total_quantity'] -= quantity
            pos['total_cost'] -= cost_basis_of_sale
            pos['total_fees'] += fee
            pos['trade_count'] += 1
            pos['last_trade'] = int(time.time() * 1000)
            if order_id and order_id not in pos.get('order_ids', []):
                pos['order_ids'].append(order_id)
            pos['last_order_id'] = order_id
            
            # Recalculate average entry price for remaining position
            if pos['total_quantity'] > 0.000001:
                pos['avg_entry_price'] = pos['total_cost'] / pos['total_quantity']
            else:
                # Position closed
                pos['total_quantity'] = 0
                pos['total_cost'] = 0
                pos['avg_entry_price'] = 0
            
            result['action'] = 'sold'
            result['cost_basis_of_sale'] = cost_basis_of_sale
            result['realized_pnl'] = realized_pnl
            result['exit_fee'] = exit_fee
            result['remaining_quantity'] = pos['total_quantity']
            result['remaining_cost_basis'] = pos['total_cost']
        
        # Update trade lots
        self.trade_lots[position_key] = lots
        self.positions[position_key] = pos
        
        self._save()
        return result
    
    def update_position(self, symbol: str, new_qty: float, new_price: float,
                       exchange: str, is_buy: bool = True, fee: float = 0.0, order_id: str = None):
        """
        Update position after a trade.
        NOTE: For sells, this now just updates the aggregate. FIFO logic is in `record_trade`.
        """
        position_key = f"{exchange.lower()}:{symbol}"
        pos = self.positions.get(position_key, {})

        old_qty = pos.get('total_quantity', 0)
        old_cost = pos.get('total_cost', 0)
        old_fees = pos.get('total_fees', 0)
        trade_count = pos.get('trade_count', 0)
        order_ids = pos.get('order_ids', [])

        if is_buy:
            # Add to position
            new_total_qty = old_qty + new_qty
            new_total_cost = old_cost + (new_qty * new_price)
            new_avg_price = new_total_cost / new_total_qty if new_total_qty > 0 else 0
            trade_count += 1
            if order_id and order_id not in order_ids:
                order_ids.append(order_id)
        else:
            # Reduce position (keep same avg cost for remaining)
            new_total_qty = max(old_qty - new_qty, 0)
            
            # 🆕 Recalculate from remaining lots for accuracy
            remaining_lots = self.trade_lots.get(position_key, [])
            if remaining_lots:
                new_total_cost = sum(l.price * l.quantity for l in remaining_lots)
                new_total_qty_from_lots = sum(l.quantity for l in remaining_lots)
                new_avg_price = new_total_cost / new_total_qty_from_lots if new_total_qty_from_lots > 0 else 0
                new_total_qty = new_total_qty_from_lots # Ensure consistency
            else: # Fallback if lots are gone
                avg_price = old_cost / old_qty if old_qty > 0 else 0
                new_total_cost = new_total_qty * avg_price
                new_avg_price = avg_price

        if new_total_qty > 0.000001: # Use a small threshold for dust
            asset = symbol[:-4] if symbol.endswith(('USDC', 'USDT')) else symbol[:-3]
            quote = symbol[-4:] if symbol.endswith(('USDC', 'USDT')) else symbol[-3:]

            self.positions[position_key] = {
                'exchange': pos.get('exchange', exchange),
                'symbol': symbol,
                'asset': asset,
                'quote': quote,
                'avg_entry_price': new_avg_price,
                'total_quantity': new_total_qty,
                'total_cost': new_total_cost,
                'total_fees': old_fees + fee,
                'trade_count': trade_count,
                'first_trade': pos.get('first_trade', int(time.time() * 1000)),
                'last_trade': int(time.time() * 1000),
                'synced_at': time.time(),
                'order_ids': order_ids,
                'last_order_id': order_id or pos.get('last_order_id'),
                'avg_fill_price': new_price if is_buy else pos.get('avg_fill_price'),
                'fills_verified': True if order_id else pos.get('fills_verified', False),
                'last_fills': pos.get('last_fills', [])
            }
        else:
            # Position closed
            self.positions.pop(position_key, None)
            self.trade_lots.pop(position_key, None) # 🆕 Also remove lots

        self._save()

    def record_order_execution(
        self,
        *,
        exchange: str,
        symbol: str,
        side: str,
        order_id: str,
        fills: list,
        avg_fill_price: Optional[float],
        fees: float,
        executed_qty: float,
    ) -> None:
        """Record a validated execution using order_id + fills."""
        if not symbol or not exchange:
            return
        if executed_qty <= 0:
            return

        is_buy = str(side or '').upper() == 'BUY'
        price = float(avg_fill_price or 0)
        if price <= 0:
            return

        # 🆕 Use the new central trade recording method
        self.record_trade(
            symbol=symbol,
            side=side,
            quantity=executed_qty,
            price=price,
            exchange=exchange,
            fee=float(fees or 0),
            order_id=order_id
        )

        position_key = f"{exchange.lower()}:{symbol}"
        pos = self.positions.get(position_key)
        if pos:
            pos['last_order_id'] = order_id
            pos['avg_fill_price'] = price
            pos['fills_verified'] = True if fills else False
            pos['last_fills'] = fills or []
            self.positions[position_key] = pos
            self._save()
    
    def can_sell_profitably(self, symbol: str, current_price: float, 
                           exchange: str = None, quantity: float = None, 
                           fee_pct: float = 0.001) -> Tuple[bool, Dict]:
        """Check if selling would be profitable.
        
        Returns:
            (can_sell: bool, info: dict)
            
        Info contains:
            - entry_price: float
            - current_price: float
            - profit_pct: float
            - net_profit: float (after fees)
            - potential_loss: float (if negative)
            - recommendation: str
        """
        # 🔍 Use the centralized 5-strategy matching logic
        pos, matched_key = self._find_position(symbol, exchange)
        
        # 🚨 NO POSITION FOUND - Critical debugging info
        if not pos:
            _safe_print(f"   🚨 COST BASIS NOT FOUND for {symbol}")
            _safe_print(f"      Exchange: {exchange}")
            
            # Show base asset extraction for debugging
            base = symbol.split('/')[0] if '/' in symbol else symbol
            for q in ['USDT', 'USDC', 'USD']:
                base = base.rstrip(q)
            _safe_print(f"      Base asset: {base}")
            
            # Show some available positions that might be close matches
            available = list(self.positions.keys())
            matching_base = [p for p in available if base.upper() in p.upper()]
            if matching_base:
                _safe_print(f"      Possible matches: {matching_base[:5]}")
            else:
                _safe_print(f"      Available positions: {available[:5]}")
            
            # No cost basis data - DON'T SELL! We don't know if it's profitable!
            return False, {
                'entry_price': None,
                'current_price': current_price,
                'profit_pct': 0,
                'net_profit': 0,
                'cost_basis': 0,
                'recommendation': 'NO_DATA - DO NOT SELL (unknown entry price)'
            }
        
        # ✅ FOUND POSITION - Use it for P&L calculation
        avg_entry = float(pos.get('avg_entry_price', 0) or 0)
        lots = self.trade_lots.get(matched_key, [])
        has_lot_cost_data = any((lot.quantity > 0 and lot.price > 0) for lot in lots)

        # Guardrail: a zero entry price is not valid cost-basis data.
        # This previously logged as "found" and produced misleading P&L.
        if avg_entry <= 0 and not has_lot_cost_data:
            _safe_print(f"   🚨 COST BASIS INVALID for {symbol}")
            _safe_print(f"      Matched key: {matched_key}")
            _safe_print("      Stored entry price is zero and no valid trade lots were found")
            return False, {
                'entry_price': None,
                'current_price': current_price,
                'profit_pct': 0,
                'net_profit': 0,
                'cost_basis': 0,
                'recommendation': 'NO_VALID_COST_BASIS - DO NOT SELL'
            }

        _safe_print(f"   ✅ Cost basis found: {matched_key} → entry ${avg_entry:.6f}")
        
        # 🆕 Use FIFO lots to calculate cost of goods for the specific quantity to be sold
        sell_qty = quantity or pos.get('total_quantity', 0)
        cost_basis_of_sale = 0
        
        if matched_key in self.trade_lots:
            lots = sorted(self.trade_lots[matched_key], key=lambda t: t.timestamp)
            qty_to_account_for = sell_qty
            for lot in lots:
                if qty_to_account_for <= 0:
                    break
                qty_from_lot = min(lot.quantity, qty_to_account_for)
                cost_basis_of_sale += qty_from_lot * lot.price
                qty_to_account_for -= qty_from_lot
        
        # Fallback to average cost if no lots found (should not happen)
        if cost_basis_of_sale == 0:
            entry_price = pos['avg_entry_price']
            cost_basis_of_sale = sell_qty * entry_price

        # Calculate P&L
        gross_value = sell_qty * current_price
        gross_profit = gross_value - cost_basis_of_sale
        
        # Account for fees (entry fees are part of cost basis, just add exit fee)
        exit_fee = gross_value * fee_pct
        
        net_profit = gross_profit - exit_fee
        
        # Calculate NET profit percentage
        net_profit_pct = (net_profit / cost_basis_of_sale * 100) if cost_basis_of_sale > 0 else 0
        
        # 💰 PENNY PROFIT RULE: As long as we make $0.01 NET, we are good!
        # Previously required 0.2% margin, but now we align with the Penny Profit Engine.
        is_penny_profitable = net_profit >= 0.01
        
        can_sell = is_penny_profitable
        
        recommendation = ""
        if net_profit_pct >= 2.0:
            recommendation = "🟢 STRONG SELL - Good profit"
        elif net_profit_pct >= 0.5:
            recommendation = "🟡 SELL - Modest profit"
        elif is_penny_profitable:
            recommendation = "⚪ HARVEST - Penny Profit Secured"
        elif net_profit_pct >= -2.0:
            recommendation = "🔴 HOLD - Would realize loss"
        else:
            recommendation = "🔴 HOLD - Significant loss, wait for recovery"
        
        return can_sell, {
            'entry_price': pos['avg_entry_price'], # Still show average entry for info
            'current_price': current_price,
            'quantity': sell_qty,
            'cost_basis': cost_basis_of_sale,
            'gross_value': gross_value,
            'gross_profit': gross_profit,
            'total_fees': exit_fee, # Only shows exit fee as entry is in cost_basis
            'net_profit': net_profit,
            'profit_pct': net_profit_pct, # Return NET profit pct
            'potential_loss': abs(net_profit) if net_profit < 0 else 0,
            'recommendation': recommendation,
            'order_ids': pos.get('order_ids', []),
            'exchange': pos.get('exchange')
        }
    
    # ══════════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP & SELL TRACKING - FIX FOR PHANTOM POSITIONS
    # ══════════════════════════════════════════════════════════════════════════════
    
    def record_sell(self, symbol: str, sell_qty: float, sell_price: float, 
                    exchange: str = None, fee: float = 0.0) -> Dict[str, Any]:
        """
        Record a sell and reduce cost basis using FIFO accounting.
        
        This is the KEY method to fix phantom positions - it properly reduces
        cost basis when assets are sold.
        
        DEPRECATION WARNING: This method is being replaced by the more comprehensive
        `record_trade(side='sell', ...)` which uses true FIFO.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDC')
            sell_qty: Quantity sold
            sell_price: Sale price per unit
            exchange: Exchange name (optional, helps with matching)
            fee: Transaction fee paid
            
        Returns:
            Dict with realized P&L and updated position info
        """
        # 🆕 DELEGATE to the new FIFO-based method
        _safe_print("DEPRECATION WARNING: `record_sell` is now an alias for `record_trade(side='sell', ...)`")
        result = self.record_trade(symbol, 'sell', sell_qty, sell_price, exchange, fee)
        
        # Adapt old return format
        if result:
            result['status'] = 'sold' if 'realized_pnl' in result else 'no_position'
            return result
        return {'status': 'error'}
    
    def cleanup_sold_positions(self, min_value_threshold: float = 0.01) -> int:
        """
        Remove positions that have been fully sold (qty ≈ 0).
        
        This cleans up phantom positions that make the cost basis appear
        higher than reality.
        
        Args:
            min_value_threshold: Remove positions worth less than this USD value
            
        Returns:
            Number of positions removed
        """
        removed = 0
        keys_to_remove = []
        
        for key, pos in self.positions.items():
            qty = pos.get('total_quantity', 0)
            cost = pos.get('total_cost', 0)
            
            # 🆕 Also check lots
            lot_qty = sum(l.quantity for l in self.trade_lots.get(key, []))

            # Remove if:
            # 1. Quantity is effectively zero in both aggregates and lots
            # 2. Has zero cost (stale/invalid)
            # 3. Cost is below threshold (dust)
            should_remove = (
                (qty <= 0.0001 and lot_qty <= 0.0001) or
                (qty > 0 and cost == 0 and pos.get('avg_entry_price', 0) == 0) or  # Stale position
                (0 < cost < min_value_threshold)  # Dust value
            )
            
            if should_remove:
                keys_to_remove.append(key)
                _safe_print(f"🗑️ Removing sold position: {key} (qty={qty:.6f}, cost=${cost:.2f})")
        
        for key in keys_to_remove:
            del self.positions[key]
            if key in self.trade_lots:
                del self.trade_lots[key]
            removed += 1
        
        if removed > 0:
            self._save()
            _safe_print(f"✅ Cleaned up {removed} sold/dust positions")
        
        return removed
    
    def verify_against_live_balances(self, live_balances: Dict[str, float], 
                                      exchange: str = None) -> Dict[str, Any]:
        """
        Verify cost basis against actual live exchange balances.
        
        If exchange shows 0 balance but we have cost basis, the position
        was sold outside our tracking - clean it up.
        
        Args:
            live_balances: {asset: quantity} from exchange API
            exchange: Exchange name to filter positions
            
        Returns:
            Dict with verification results and corrections made
        """
        corrections = []
        removed = []
        
        for key, pos in list(self.positions.items()):
            pos_exchange = pos.get('exchange', '')
            if exchange and pos_exchange.lower() != exchange.lower():
                continue
            
            # Extract base asset from symbol
            asset = pos.get('asset', '')
            if not asset:
                # Try to parse from symbol
                symbol = pos.get('symbol', key)
                # Remove exchange prefix if present
                if ':' in symbol:
                    symbol = symbol.split(':')[1]
                # Extract base asset (before quote currency)
                for quote in ['USDC', 'USDT', 'USD', 'EUR', 'GBP', 'BTC', 'ETH']:
                    if symbol.endswith(quote):
                        asset = symbol[:-len(quote)]
                        break
                else:
                    asset = symbol
            
            tracked_qty = pos.get('total_quantity', 0)
            live_qty = live_balances.get(asset, 0)
            
            # If tracked qty > 0 but live = 0, position was sold externally
            if tracked_qty > 0.0001 and live_qty < 0.0001:
                _safe_print(f"🔄 CORRECTION: {key} tracked {tracked_qty:.6f} but live shows 0")
                pos['total_quantity'] = 0
                pos['total_cost'] = 0
                pos['closed_at'] = time.time()
                pos['correction_note'] = 'Zeroed - live balance is 0'
                self.positions[key] = pos
                if key in self.trade_lots:
                    self.trade_lots[key] = [] # 🆕 Clear lots too
                corrections.append({
                    'key': key,
                    'asset': asset,
                    'was_qty': tracked_qty,
                    'live_qty': live_qty,
                    'action': 'zeroed'
                })
            
            # If live qty is significantly different, update qty but keep cost basis ratio
            elif abs(tracked_qty - live_qty) > 0.0001 and live_qty > 0:
                ratio = live_qty / tracked_qty if tracked_qty > 0 else 0
                old_cost = pos.get('total_cost', 0)
                new_cost = old_cost * ratio
                _safe_print(f"📊 ADJUSTMENT: {key} tracked {tracked_qty:.6f} → live {live_qty:.6f}")
                pos['total_quantity'] = live_qty
                pos['total_cost'] = new_cost
                pos['last_verified'] = time.time()
                self.positions[key] = pos
                
                # 🆕 Adjust lots proportionally
                if key in self.trade_lots:
                    for lot in self.trade_lots[key]:
                        lot.quantity *= ratio

                corrections.append({
                    'key': key,
                    'asset': asset,
                    'was_qty': tracked_qty,
                    'live_qty': live_qty,
                    'action': 'adjusted'
                })
        
        if corrections:
            self._save()
        
        # Also clean up any zero positions
        removed_count = self.cleanup_sold_positions()
        
        return {
            'corrections': corrections,
            'removed_count': removed_count,
            'positions_checked': len(self.positions)
        }
    
    def sync_with_cleanup(self) -> Dict[str, Any]:
        """
        Full sync from exchanges WITH cleanup of sold positions.
        
        This is the proper way to keep cost basis accurate:
        1. Sync fresh data from exchanges (with FIFO sell tracking)
        2. Verify against live balances
        3. Clean up phantom positions
        """
        print("\n" + "=" * 60)
        print("🔄 SYNCING COST BASIS WITH CLEANUP")
        print("=" * 60)
        
        # Step 1: Sync from exchanges
        synced = self.sync_from_exchanges()
        
        # Step 2: Clean up sold positions
        cleaned = self.cleanup_sold_positions()
        
        # Step 3: Get live balances and verify
        live_balances = {}
        verification_results = {}
        
        try:
            # Binance
            if self.clients and 'binance' in self.clients:
                client = self.clients['binance']
            else:
                from binance_client import get_binance_client
                client = get_binance_client()
            
            account = client.account()
            for bal in account.get('balances', []):
                asset = bal['asset']
                qty = float(bal.get('free', 0)) + float(bal.get('locked', 0))
                if qty > 0:
                    live_balances[asset] = qty
            
            verification_results['binance'] = self.verify_against_live_balances(
                live_balances, exchange='binance'
            )
        except Exception as e:
            _safe_print(f"⚠️ Could not verify Binance balances: {e}")
        
        # Step 4: Final cleanup
        final_cleanup = self.cleanup_sold_positions()
        
        result = {
            'synced_positions': synced,
            'initial_cleanup': cleaned,
            'verification': verification_results,
            'final_cleanup': final_cleanup,
            'total_positions': len(self.positions)
        }
        
        print(f"\n✅ Sync complete: {synced} synced, {cleaned + final_cleanup} cleaned")
        print("=" * 60)
        
        return result
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked positions."""
        total_cost = 0
        total_positions = len(self.positions)
        
        for symbol, pos in self.positions.items():
            total_cost += pos.get('total_cost', 0)
        
        return {
            'total_positions': total_positions,
            'total_cost_basis': total_cost,
            'last_sync': self.last_sync,
            'positions': list(self.positions.keys())
        }
    
    def print_status(self):
        """Print current cost basis status."""
        print("\n" + "=" * 70)
        print("💰 COST BASIS TRACKER STATUS")
        print("=" * 70)
        
        if not self.positions:
            print("   No positions tracked")
            return
        
        print(f"\n{'Symbol':<25} {'Entry Price':<15} {'Quantity':<20} {'Cost Basis':<15}")
        print("-" * 75)
        
        total_cost = 0
        for symbol, pos in sorted(self.positions.items()):
            entry = pos.get('avg_entry_price', 0)
            qty = pos.get('total_quantity', 0)
            cost = pos.get('total_cost', 0)
            total_cost += cost
            print(f"{symbol:<25} ${entry:<14.6f} {qty:<20.8f} ${cost:<14.2f}")
        
        print("-" * 75)
        print(f"{'TOTAL':<25} {'':<15} {'':<20} ${total_cost:<14.2f}")
        print(f"\nLast sync: {datetime.fromtimestamp(self.last_sync).isoformat() if self.last_sync else 'Never'}")
        print("=" * 75)


# Singleton instance for ecosystem integration
_tracker_instance: Optional[CostBasisTracker] = None

def get_cost_basis_tracker() -> CostBasisTracker:
    """Get singleton cost basis tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CostBasisTracker()
    return _tracker_instance


if __name__ == "__main__":
    # Test/sync mode
    tracker = get_cost_basis_tracker()
    
    # Example of new FIFO flow
    print("--- FIFO Example ---")
    tracker.record_trade("FIFO/USD", "buy", 10, 100, "test")
    tracker.record_trade("FIFO/USD", "buy", 5, 120, "test")
    tracker.print_status()
    
    can_sell, info = tracker.can_sell_profitably("FIFO/USD", 115, "test", quantity=12)
    print(f"Can sell 12 units at $115? {can_sell}, Info: {info}")
    
    tracker.record_trade("FIFO/USD", "sell", 12, 115, "test")
    tracker.print_status()
    print("--------------------")

    tracker.sync_with_cleanup()
    tracker.print_status()
