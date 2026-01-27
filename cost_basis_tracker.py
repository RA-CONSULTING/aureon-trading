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


class CostBasisTracker:
    """Track real cost basis for all positions."""
    
    def __init__(self, filepath: str = COST_BASIS_FILE):
        self.filepath = filepath
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.last_sync: float = 0
        self._load()
    
    def _load(self):
        """Load cost basis data from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self.positions = data.get('positions', {})
                    self.last_sync = data.get('last_sync', 0)
                    _safe_print(f"📊 Cost Basis Tracker: Loaded {len(self.positions)} positions from {self.filepath}")
            except Exception as e:
                _safe_print(f"⚠️ Failed to load cost basis file: {e}")
                self.positions = {}
        
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
            data = {
                'positions': self.positions,
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
            from binance_client import BinanceClient
            client = BinanceClient()
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
            from kraken_client import KrakenClient
            client = KrakenClient()
            if client.dry_run:
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
                    total_qty += qty
                    total_cost += qty * price
                    total_fees += fee
                    buy_trades += 1
                elif trade_type == 'sell':
                    total_qty -= qty
                    if total_qty > 0:
                        avg_price = total_cost / (total_qty + qty) if (total_qty + qty) > 0 else 0
                        total_cost = total_qty * avg_price
                
                if first_trade is None or timestamp < first_trade:
                    first_trade = timestamp
                if last_trade is None or timestamp > last_trade:
                    last_trade = timestamp
            
            if total_qty > 0 and buy_trades > 0:
                avg_entry = total_cost / total_qty
                # Normalize pair name
                symbol = pair.replace('X', '').replace('Z', '')  # Remove Kraken prefixes
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
            from capital_client import CapitalClient
            client = CapitalClient()
            if not client.enabled:
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
        
        # Strategy 1: Direct match with exchange context
        if exchange:
            position_key = f"{exchange.lower()}:{symbol}"
            pos = self.positions.get(position_key)
            if pos:
                return (pos, position_key)
        
        # Strategy 2: Try without exchange prefix
        pos = self.positions.get(symbol)
        if pos:
            return (pos, symbol)
        
        # Strategy 3: Try normalized (no slashes)
        norm_symbol = symbol.replace('/', '')
        if exchange:
            norm_key = f"{exchange.lower()}:{norm_symbol}"
            pos = self.positions.get(norm_key)
            if pos:
                return (pos, norm_key)
        
        pos = self.positions.get(norm_symbol)
        if pos:
            return (pos, norm_symbol)
        
        # Strategy 4: Try swapping quote currencies (USDT ↔ USDC ↔ USD)
        # Extract base asset
        if '/' in symbol:
            base = symbol.split('/')[0]
        else:
            base = symbol.rstrip('USDT').rstrip('USDC').rstrip('USD').rstrip('EUR').rstrip('GBP')
        
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
                            if pos:
                                # Debug message
                                # print(f"   ✓ Matched via quote swap: {symbol} → {test_key}")
                                return (pos, test_key)
                        
                        pos = self.positions.get(test_symbol)
                        if pos:
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
            stored_symbol = p.get('symbol', s)
            if stored_symbol.startswith(base_asset):
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
        
        self._save()
        _safe_print(f"   💾 Logged entry: {position_key} @ ${price:.6f} x {quantity} (Order: {order_id})")
        if norm_symbol != symbol:
            _safe_print(f"      Also indexed as: {norm_key}")
    
    def update_position(self, symbol: str, new_qty: float, new_price: float,
                       exchange: str, is_buy: bool = True, fee: float = 0.0, order_id: str = None):
        """Update position after a trade (FIFO cost basis)."""
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
            avg_price = old_cost / old_qty if old_qty > 0 else 0
            new_total_cost = new_total_qty * avg_price
            new_avg_price = avg_price

        if new_total_qty > 0:
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

        self.update_position(
            symbol=symbol,
            new_qty=executed_qty,
            new_price=price,
            exchange=exchange,
            is_buy=is_buy,
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
        _safe_print(f"   ✅ Cost basis found: {matched_key} → entry ${pos['avg_entry_price']:.6f}")
        
        entry_price = pos['avg_entry_price']
        qty = quantity or pos['total_quantity']
        
        # Calculate P&L
        gross_value = qty * current_price
        cost_basis = qty * entry_price
        gross_profit = gross_value - cost_basis
        
        # Account for fees (entry + exit)
        # Use historical fees for entry (pro-rated)
        total_pos_qty = pos.get('total_quantity', 0)
        fraction = qty / total_pos_qty if total_pos_qty > 0 else 1.0
        historical_fees = pos.get('total_fees', 0) * fraction
        
        # Estimate exit fee
        exit_fee = gross_value * fee_pct
        
        total_fees = historical_fees + exit_fee
        
        net_profit = gross_profit - total_fees
        
        # Calculate NET profit percentage
        net_profit_pct = (net_profit / cost_basis * 100) if cost_basis > 0 else 0
        
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
            'entry_price': entry_price,
            'current_price': current_price,
            'quantity': qty,
            'cost_basis': cost_basis,
            'gross_value': gross_value,
            'gross_profit': gross_profit,
            'total_fees': total_fees,
            'net_profit': net_profit,
            'profit_pct': net_profit_pct, # Return NET profit pct
            'potential_loss': abs(net_profit) if net_profit < 0 else 0,
            'recommendation': recommendation,
            'order_ids': pos.get('order_ids', []),
            'exchange': pos.get('exchange')
        }
    
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
        
        print(f"\n{'Symbol':<15} {'Entry Price':<15} {'Quantity':<15} {'Cost Basis':<15}")
        print("-" * 60)
        
        total_cost = 0
        for symbol, pos in sorted(self.positions.items()):
            entry = pos.get('avg_entry_price', 0)
            qty = pos.get('total_quantity', 0)
            cost = pos.get('total_cost', 0)
            total_cost += cost
            print(f"{symbol:<15} ${entry:<14.6f} {qty:<15.6f} ${cost:<14.2f}")
        
        print("-" * 60)
        print(f"{'TOTAL':<15} {'':<15} {'':<15} ${total_cost:<14.2f}")
        print(f"\nLast sync: {datetime.fromtimestamp(self.last_sync).isoformat() if self.last_sync else 'Never'}")
        print("=" * 70)


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
    tracker = CostBasisTracker()
    tracker.sync_from_exchanges()
    tracker.print_status()
