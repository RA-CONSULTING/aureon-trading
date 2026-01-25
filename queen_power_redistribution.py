#!/usr/bin/env python3
"""
Queen Power Redistribution Engine
Autonomous energy optimization and power growth across all relays.

The Queen uses her built-in intelligence to:
1. Monitor ALL nodes (positions) across ALL relays for energy state
2. Identify nodes with positive energy (unrealized profit)
3. Redistribute profit energy to feed winning nodes or create new nodes
4. KEEP original positions profitable (don't close winners)
5. Move energy between nodes for optimal compound growth
6. Execute ONLY when (gain - drain) > 0
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

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import Queen's consciousness
from aureon_queen_true_consciousness import QueenTrueConsciousnessController

# Import exchange clients
from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class EnergyNode:
    """A position/asset holding representing an energy node."""
    relay: str  # BIN, KRK, ALP, CAP
    symbol: str  # BTC/USD, ETHUSDT, AAPL, etc.
    quantity: float  # Amount held
    entry_price: float  # Average entry price
    current_price: float  # Current market price
    unrealized_pnl: float  # Unrealized profit/loss (the energy state)
    pnl_percentage: float  # PnL as percentage
    position_value_usd: float  # Current USD value
    is_positive_energy: bool  # True if profitable
    energy_available_to_redistribute: float  # Profit we can move without closing
    timestamp: float
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RedistributionOpportunity:
    """A potential energy redistribution opportunity."""
    relay: str
    source_asset: str
    target_asset: str
    idle_energy: float  # USD value available
    expected_gain_pct: float  # Expected gain percentage
    expected_gain_usd: float  # Expected gain in USD
    energy_drain: float  # Total drain from fees/slippage
    net_energy_gain: float  # Expected gain - drain
    momentum_score: float  # Asset momentum (0-1)
    confidence: float  # Queen's confidence (0-1)
    source_node: Optional['EnergyNode']  # Source node if redistributing from position
    timestamp: float
    
    def to_dict(self):
        d = asdict(self)
        if self.source_node:
            d['source_node'] = self.source_node.to_dict()
        return d


@dataclass
class RedistributionDecision:
    """Queen's decision on a redistribution opportunity."""
    opportunity: RedistributionOpportunity
    decision: str  # 'EXECUTE', 'BLOCK', 'WAIT'
    reasoning: str
    queen_confidence: float
    realms_consensus: int  # How many realms agreed (0-5)
    timestamp: float
    
    def to_dict(self):
        d = asdict(self)
        d['opportunity'] = self.opportunity.to_dict()
        return d


class QueenPowerRedistribution:
    """
    Queen's autonomous energy redistribution system.
    Connects her intelligence to active execution.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        
        # Initialize Queen consciousness
        logger.info("🐝 Initializing Queen's consciousness...")
        self.queen = QueenTrueConsciousnessController(dry_run=dry_run)
        
        # Initialize exchange clients
        self.kraken = None
        self.binance = None
        self.alpaca = None
        
        # Try to initialize exchanges (gracefully handle missing credentials)
        try:
            self.kraken = KrakenClient()
        except Exception as e:
            logger.warning(f"Kraken not available: {e}")
        
        try:
            self.binance = BinanceClient()
        except Exception as e:
            logger.warning(f"Binance not available: {e}")
        
        try:
            self.alpaca = AlpacaClient()
        except Exception as e:
            logger.warning(f"Alpaca not available: {e}")
        
        # State tracking
        self.decisions_history: List[RedistributionDecision] = []
        self.executions_history: List[Dict] = []
        self.total_net_energy_gained = 0.0
        self.total_blocked_drains_avoided = 0.0
        self.all_energy_nodes: List[EnergyNode] = []  # All positions across all relays
        
        # Load cost basis data
        self.cost_basis = self.load_state_file('cost_basis_history.json', {})
        cost_basis_positions = self.cost_basis.get('positions', {})
        logger.info(f"📊 Cost Basis Tracker: Loaded {len(cost_basis_positions)} positions from cost_basis_history.json")
        
        # Relay-specific fee profiles (from adaptive_prime_profit_gate.py)
        self.relay_fees = {
            'BIN': {'maker': 0.0010, 'taker': 0.0010, 'spread': 0.0005, 'slippage': 0.0003},  # Binance
            'KRK': {'maker': 0.0025, 'taker': 0.0040, 'spread': 0.0008, 'slippage': 0.0005},  # Kraken
            'ALP': {'maker': 0.0015, 'taker': 0.0025, 'spread': 0.0008, 'slippage': 0.0005},  # Alpaca
            'CAP': {'maker': 0.0000, 'taker': 0.0000, 'spread': 0.0020, 'slippage': 0.0008},  # Capital (spread-based)
        }
        
        # Configuration
        self.min_idle_energy_usd = 0.50  # Min USD to consider redistribution (LOWERED for small accounts)
        self.min_net_gain_usd = 0.01  # Min net gain required (LOWERED to catch micro-profits)
        self.min_positive_energy_to_redistribute = 0.10  # Min profit before we redistribute (LOWERED)
        self.profit_redistribution_percentage = 0.50  # Take 50% of profit to redistribute
        self.scan_interval_seconds = 30  # How often to scan for opportunities
        self.max_redistribution_per_relay = 0.25  # Max 25% of idle energy per cycle
        
        # Momentum scanner integration
        self.momentum_scanner = None
        try:
            from aureon_animal_momentum_scanners import AlpacaSwarmOrchestrator
            from aureon_alpaca_scanner_bridge import AlpacaScannerBridge
            # Initialize bridge and orchestrator
            bridge = AlpacaScannerBridge(self.alpaca)
            self.momentum_scanner = AlpacaSwarmOrchestrator(self.alpaca, bridge)
            logger.info("🐺 Momentum Scanner integrated - Will find real targets!")
        except Exception as e:
            logger.warning(f"Momentum scanner not available: {e}")
        
        logger.info(f"✅ Queen Power Redistribution initialized (dry_run={dry_run})")
    
    def calculate_relay_energy_drain(self, relay: str, trade_value_usd: float, is_maker: bool = True) -> Dict:
        """
        Calculate total energy drain for a trade on a specific relay.
        CRITICAL: Must be accurate to prevent energy loss!
        
        Returns:
            {
                'maker_fee': float,
                'taker_fee': float,
                'spread_cost': float,
                'slippage': float,
                'total_drain': float,
                'relay': str
            }
        """
        fees = self.relay_fees.get(relay, self.relay_fees['KRK'])  # Default to Kraken (conservative)
        
        fee_rate = fees['maker'] if is_maker else fees['taker']
        
        # Calculate components
        trading_fee = trade_value_usd * fee_rate
        spread_cost = trade_value_usd * fees['spread']
        slippage_cost = trade_value_usd * fees['slippage']
        
        # CRITICAL: We pay fees on BOTH sides of conversion (buy + sell)
        # USD → Asset: pay fee on entry
        # Asset → USD (future): pay fee on exit
        # So we double the trading fee for round-trip
        total_drain = (trading_fee * 2) + spread_cost + slippage_cost
        
        return {
            'maker_fee': trading_fee if is_maker else 0,
            'taker_fee': 0 if is_maker else trading_fee,
            'spread_cost': spread_cost,
            'slippage': slippage_cost,
            'total_drain': total_drain,
            'relay': relay,
            'fee_rate': fee_rate,
            'round_trip_factor': 2.0  # We account for entry + exit
        }
    
    def load_state_file(self, filepath: str, default: Optional[Dict] = None) -> Dict:
        """Load JSON state file with fallback."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {filepath}: {e}")
        return default or {}
    
    def get_relay_idle_energy(self, relay: str) -> Tuple[float, str]:
        """
        Get idle energy (USD/USDT balance) for a relay.
        Returns (amount_usd, asset_symbol).
        """
        if relay == 'BIN':
            # Binance: Check USDT balance
            if self.binance:
                try:
                    balances = self.binance.get_balance()
                    usdt = balances.get('USDT', 0.0)
                    return (usdt, 'USDT')
                except Exception as e:
                    logger.warning(f"BIN balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('binance_truth_tracker_state.json', {})
            usdt = state.get('balances', {}).get('USDT', {}).get('free', 0.0)
            return (usdt, 'USDT')
        
        elif relay == 'KRK':
            # Kraken: Check ZUSD balance
            if self.kraken:
                try:
                    balances = self.kraken.get_balance()
                    usd = balances.get('ZUSD', 0.0)
                    return (usd, 'ZUSD')
                except Exception as e:
                    logger.warning(f"KRK balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('aureon_kraken_state.json', {})
            usd = state.get('balances', {}).get('ZUSD', 0.0)
            return (usd, 'ZUSD')
        
        elif relay == 'ALP':
            # Alpaca: Check USD cash
            if self.alpaca:
                try:
                    account = self.alpaca.get_account()
                    cash = float(account.get('cash', 0.0))
                    return (cash, 'USD')
                except Exception as e:
                    logger.warning(f"ALP balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('alpaca_truth_tracker_state.json', {})
            cash = state.get('cash', 0.0)
            return (cash, 'USD')
        
        elif relay == 'CAP':
            # Capital.com: Use hardcoded balance for now (manual tracking)
            # TODO: Integrate with Capital.com API when available
            return (92.66, 'USD')  # Current CAP balance
        
        return (0.0, 'UNKNOWN')
    
    def scan_all_energy_nodes(self) -> List[EnergyNode]:
        """
        Scan ALL positions across ALL relays to find energy nodes.
        Returns list of all positions with their energy states.
        """
        nodes = []
        
        # Scan BIN (Binance) - Get LIVE balances from API
        try:
            if self.binance:
                logger.info("  🔍 Scanning Binance via LIVE API...")
                balances = self.binance.get_balance()
                logger.info(f"  📊 BIN: Found {len(balances)} assets")
                
                for asset, qty in balances.items():
                    # Include ALL nodes - dust is quantum entangled energy!
                    # Only skip pure quote currencies (USDT/USDC) - they are the medium, not nodes
                    if asset in ['USDT', 'USDC', 'BUSD']:
                        continue  # Skip pure quote currencies only
                    
                    # Try multiple quote currencies to find a valid pair
                    symbol = None
                    current_price = 0
                    for quote in ['USDT', 'USDC', 'BTC', 'BNB']:
                        try_symbol = f'{asset}{quote}'
                        try:
                            ticker = self.binance.get_ticker(try_symbol)
                            if ticker:
                                price = float(ticker.get('last', ticker.get('price', 0)))
                                if price > 0:
                                    symbol = try_symbol
                                    current_price = price
                                    # Convert BTC/BNB prices to USD
                                    if quote == 'BTC':
                                        btc_ticker = self.binance.get_ticker('BTCUSDT')
                                        if btc_ticker:
                                            current_price = price * float(btc_ticker.get('last', 0))
                                    elif quote == 'BNB':
                                        bnb_ticker = self.binance.get_ticker('BNBUSDT')
                                        if bnb_ticker:
                                            current_price = price * float(bnb_ticker.get('last', 0))
                                    break
                        except:
                            continue
                    
                    # Handle special cases: USD balance, Earn products
                    if not symbol and asset == 'USD':
                        symbol = 'USD'
                        current_price = 1.0  # USD = 1 USD
                    elif not symbol and asset.startswith('LD'):
                        # Binance Earn products (LDUSDC = staked USDC)
                        base_asset = asset[2:]  # Remove 'LD' prefix
                        if base_asset in ['USDC', 'USDT', 'BUSD']:
                            symbol = asset
                            current_price = 1.0  # Stablecoins = $1
                        else:
                            # Try to get price for underlying
                            try:
                                ticker = self.binance.get_ticker(f'{base_asset}USDT')
                                if ticker:
                                    symbol = asset
                                    current_price = float(ticker.get('last', 0))
                            except:
                                pass
                    
                    if not symbol or current_price <= 0:
                        # Still track as unknown quantum node
                        logger.info(f"  🌌 BIN: {asset} | {qty:.6f} units | NO PAIR FOUND (quantum orphan)")
                        continue
                    
                    try:
                        position_value = qty * current_price
                        
                        # Look up cost basis from history
                        entry_price = current_price  # Default if no basis found
                        cost_basis_positions = self.cost_basis.get('positions', {})
                        
                        # Try different key formats: ASSETUSDC, ASSETUSDT, binance:ASSETUSDC
                        for quote in ['USDC', 'USDT']:
                            basis_key = f'{asset}{quote}'
                            if basis_key in cost_basis_positions:
                                entry_price = cost_basis_positions[basis_key].get('avg_entry_price', current_price)
                                break
                            # Try with exchange prefix
                            basis_key_prefixed = f'binance:{asset}{quote}'
                            if basis_key_prefixed in cost_basis_positions:
                                entry_price = cost_basis_positions[basis_key_prefixed].get('avg_entry_price', current_price)
                                break
                        
                        # Calculate PnL
                        pnl = (current_price - entry_price) * qty
                        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
                        is_positive = pnl > self.min_positive_energy_to_redistribute
                        redistributable = (pnl * 0.5) if is_positive else 0.0  # 50% of profit
                        
                        # ALL nodes included - quantum entanglement doesn't discriminate by size!
                        node = EnergyNode(
                            relay='BIN',
                            symbol=symbol,
                            quantity=qty,
                            entry_price=entry_price,
                            current_price=current_price,
                            unrealized_pnl=pnl,
                            pnl_percentage=pnl_pct,
                            position_value_usd=position_value,
                            is_positive_energy=is_positive,
                            energy_available_to_redistribute=redistributable,
                            timestamp=time.time()
                        )
                        nodes.append(node)
                        # Show entry price + PnL in log - include dust indicator
                        dust_marker = "🌌" if position_value < 0.50 else ""  # Quantum dust marker
                        pnl_indicator = "🟢" if is_positive else ("🔴" if pnl < -0.10 else "⚪")
                        logger.info(f"  {pnl_indicator}{dust_marker} BIN: {symbol} | {qty:.6f} units | ${position_value:.4f} | Entry: ${entry_price:.6f} | PnL: ${pnl:.4f} ({pnl_pct:.1f}%)")
                    except Exception as e:
                        logger.debug(f"  ⚪ BIN {symbol}: {e}")
            else:
                logger.warning("  ⚠️ BIN: Client not available")
        except Exception as e:
            logger.warning(f"BIN node scan failed: {e}")
        
        # Scan KRK (Kraken) - Multi-source approach (adapt to data availability)
        try:
            logger.info("  🔍 Scanning Kraken (multi-source: API balance + cost basis + state)...")
            
            # Kraken symbol mapping (internal codes → standard ticker symbols)
            KRAKEN_SYMBOL_MAP = {
                'XBT': 'BTC', 'BT': 'XBT',  # Bitcoin variants
                'XRP': 'XRP', 'RP': 'XRP',  # Ripple
                'XDG': 'DOGE', 'DG': 'XDG', # Dogecoin
                'XXBT': 'XBT', 'XXRP': 'XRP', 'XETH': 'ETH', 'XLTC': 'LTC',
                'ZUSD': 'USD', 'ZEUR': 'EUR', 'ZGBP': 'GBP',
            }
            
            def get_kraken_ticker_symbol(asset: str, quote: str) -> list:
                """Generate possible Kraken ticker symbols to try."""
                # Map internal codes to standard
                mapped_asset = KRAKEN_SYMBOL_MAP.get(asset, asset)
                mapped_quote = KRAKEN_SYMBOL_MAP.get(quote, quote)
                
                # Generate variants to try
                variants = [
                    f'{mapped_asset}{mapped_quote}',
                    f'{asset}{quote}',
                    f'X{mapped_asset}Z{mapped_quote}',  # Kraken format: XXBTZUSD
                    f'X{mapped_asset}{mapped_quote}',
                    f'{mapped_asset}Z{mapped_quote}',
                ]
                # For BTC specifically
                if asset in ['BT', 'XBT', 'BTC']:
                    variants.extend(['XBTUSD', 'XXBTZUSD', 'BTCUSD'])
                # For XRP
                if asset in ['RP', 'XRP']:
                    variants.extend(['XRPUSD', 'XXRPZUSD'])
                # For DOGE
                if asset in ['DG', 'XDG', 'DOGE']:
                    variants.extend(['XDGUSD', 'DOGEUSD'])
                return variants
            
            # Source 1: Try live API balance first
            api_balances = {}
            if self.kraken:
                try:
                    api_balances = self.kraken.get_balance()
                    if api_balances:
                        logger.info(f"  📡 KRK API: Found {len(api_balances)} live balances")
                except Exception as e:
                    logger.debug(f"  ⚠️ KRK API balance failed: {e}")
            
            # Source 2: Cost basis history (most reliable for quantity + entry price)
            cost_basis_positions = self.cost_basis.get('positions', {})
            kraken_cost_basis = {k: v for k, v in cost_basis_positions.items() 
                                if v.get('exchange') == 'kraken'}
            
            # Source 3: State file (fallback for active positions)
            krk_state = self.load_state_file('aureon_kraken_state.json', {})
            krk_state_positions = krk_state.get('positions', {})
            
            # CRITICAL: Only count positions that ACTUALLY EXIST
            # Cost basis may contain SOLD positions - use it only for entry price lookup!
            # Priority: 1) State file (local truth), 2) API (live, but may be rate-limited)
            # Cost basis is used ONLY to get entry prices for positions confirmed elsewhere
            
            # Get symbols from live sources ONLY (not cost_basis which may have sold positions)
            all_kraken_symbols = set(api_balances.keys()) | set(krk_state_positions.keys())
            
            # If API returned nothing (rate limited or error), rely solely on state file
            if not api_balances:
                logger.info(f"  ⚠️ KRK API returned empty (rate limited?) - using state file as truth")
                all_kraken_symbols = set(krk_state_positions.keys())
            
            logger.info(f"  📊 KRK: Scanning {len(all_kraken_symbols)} ACTIVE positions")
            
            for symbol in all_kraken_symbols:
                # Get quantity from best source
                qty = 0.0
                entry_price = 0.0
                asset = symbol
                quote = 'USD'
                
                # Priority 1: State file (local tracked positions)
                if symbol in krk_state_positions:
                    state_pos = krk_state_positions[symbol]
                    qty = state_pos.get('quantity', 0.0)
                    entry_price = state_pos.get('entry_price', 0.0)
                    # Get entry from cost_basis if available (more accurate)
                    if symbol in kraken_cost_basis:
                        cb_data = kraken_cost_basis[symbol]
                        entry_price = cb_data.get('avg_entry_price', entry_price)
                        asset = cb_data.get('asset', symbol)
                        quote = cb_data.get('quote', 'USD')
                
                # Priority 2: API balance (live data)
                elif symbol in api_balances:
                    qty = api_balances[symbol]
                    # Look up entry price from cost_basis
                    if symbol in kraken_cost_basis:
                        cb_data = kraken_cost_basis[symbol]
                        entry_price = cb_data.get('avg_entry_price', 0.0)
                        asset = cb_data.get('asset', symbol)
                        quote = cb_data.get('quote', 'USD')
                
                if qty < 0.00001:
                    continue
                
                # Get current price using symbol mapping
                current_price = 0  # Don't fallback to entry_price - we need real price!
                
                if self.kraken:
                    # Use the mapping function to get all possible ticker symbols
                    symbols_to_try = get_kraken_ticker_symbol(asset, quote)
                    # Also try the original symbol and common variants
                    symbols_to_try.extend([symbol, f'{asset}USD', f'{asset}USDT'])
                    
                    for try_symbol in symbols_to_try:
                        try:
                            ticker = self.kraken.get_ticker(try_symbol)
                            # Kraken returns 'price' field, not 'last'
                            fetched_price = float(ticker.get('price', ticker.get('last', 0)))
                            if fetched_price > 0:
                                current_price = fetched_price
                                logger.debug(f"  📡 KRK: {symbol} → {try_symbol} = ${fetched_price:.6f}")
                                break
                        except:
                            continue
                
                # If still no price, log and use entry as fallback (but flag it)
                if current_price <= 0:
                    current_price = entry_price  # Fallback
                    if entry_price > 0:
                        logger.debug(f"  ⚠️ KRK: {symbol} no live price, using entry ${entry_price:.6f}")
                
                position_value = qty * current_price
                
                # Calculate PnL
                pnl = (current_price - entry_price) * qty
                pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0
                is_positive = pnl > self.min_positive_energy_to_redistribute
                redistributable = (pnl * 0.5) if is_positive else 0.0  # 50% of profit
                
                if position_value > 0.50:  # Min $0.50 position
                    node = EnergyNode(
                        relay='KRK',
                        symbol=symbol,
                        quantity=qty,
                        entry_price=entry_price,
                        current_price=current_price,
                        unrealized_pnl=pnl,
                        pnl_percentage=pnl_pct,
                        position_value_usd=position_value,
                        is_positive_energy=is_positive,
                        energy_available_to_redistribute=redistributable,
                        timestamp=time.time()
                    )
                    nodes.append(node)
                    # Show entry price + PnL in log
                    pnl_indicator = "🟢" if is_positive else ("🔴" if pnl < -0.10 else "⚪")
                    logger.info(f"  {pnl_indicator} KRK: {symbol} | {qty:.4f} units | ${position_value:.2f} | Entry: ${entry_price:.4f} | PnL: ${pnl:.2f} ({pnl_pct:.1f}%)")
        except Exception as e:
            logger.warning(f"KRK node scan failed: {e}")
        
        # Scan ALP (Alpaca)
        try:
            alp_state = self.load_state_file('alpaca_truth_tracker_state.json', {})
            positions = alp_state.get('positions', [])
            for pos in positions:
                if isinstance(pos, dict):
                    symbol = pos.get('symbol', 'UNKNOWN')
                    qty = float(pos.get('qty', 0.0))
                    entry = float(pos.get('avg_entry_price', 0.0))
                    current = float(pos.get('current_price', entry))
                    pnl = float(pos.get('unrealized_pl', 0.0))
                    pnl_pct = float(pos.get('unrealized_plpc', 0.0)) * 100
                    position_value = float(pos.get('market_value', 0.0))
                    
                    # Include ANY position with non-zero quantity (even small micro-positions)
                    if abs(qty) > 0 and position_value > 0.01:
                        node = EnergyNode(
                            relay='ALP',
                            symbol=symbol,
                            quantity=qty,
                            entry_price=entry,
                            current_price=current,
                            unrealized_pnl=pnl,
                            pnl_percentage=pnl_pct,
                            position_value_usd=position_value,
                            is_positive_energy=pnl > 0,
                            energy_available_to_redistribute=max(0, pnl * self.profit_redistribution_percentage) if pnl > self.min_positive_energy_to_redistribute else 0.0,
                            timestamp=time.time()
                        )
                        nodes.append(node)
                        if node.is_positive_energy:
                            logger.info(f"  🟢 ALP node: {symbol} | +${pnl:.4f} ({pnl_pct:.2f}%) | Redistributable: ${node.energy_available_to_redistribute:.4f}")
        except Exception as e:
            logger.warning(f"ALP node scan failed: {e}")
        
        # Scan CAP (Capital.com) - manual for now
        # TODO: Add Capital.com API integration
        
        self.all_energy_nodes = nodes
        
        positive_nodes = [n for n in nodes if n.is_positive_energy]
        total_positive_energy = sum(n.unrealized_pnl for n in positive_nodes)
        total_redistributable = sum(n.energy_available_to_redistribute for n in positive_nodes)
        
        logger.info(f"📊 Node Scan Complete: {len(nodes)} total nodes, {len(positive_nodes)} with positive energy")
        logger.info(f"💎 Total Positive Energy: ${total_positive_energy:.2f} | Redistributable: ${total_redistributable:.2f}")
        
        return nodes
    
    def find_best_conversion(self, relay: str, idle_usd: float) -> Optional[Tuple[str, float, float]]:
        """
        Find best asset to convert idle energy into.
        Returns (target_asset, expected_gain_pct, momentum_score) or None.
        
        Uses momentum scanner to find high-momentum assets from REAL order books.
        CRITICAL: Only recommend targets where expected_gain > energy_drain!
        """
        # Calculate minimum required gain to cover fees (relay-specific)
        drain_info = self.calculate_relay_energy_drain(relay, idle_usd, is_maker=True)
        min_gain_pct_required = (drain_info['total_drain'] / idle_usd * 100) + 0.5  # +0.5% buffer
        
        logger.debug(f"  {relay}: Min gain required: {min_gain_pct_required:.2f}% to cover ${drain_info['total_drain']:.4f} drain")
        # Use momentum scanner if available
        if self.momentum_scanner and relay == 'ALP':
            try:
                # Get best opportunity from momentum scanner
                best_opp = self.momentum_scanner.get_best_opportunity()
                if best_opp:
                    symbol = best_opp.symbol
                    expected_gain = best_opp.net_pct  # Net after fees
                    momentum = best_opp.volume / 1000  # Normalize volume as momentum score
                    
                    logger.info(f"🎯 Momentum scanner found: {symbol} | {expected_gain:.2f}% net gain | {best_opp.side} signal | {best_opp.reason}")
                    return (symbol, expected_gain, momentum)
            except Exception as e:
                logger.warning(f"Momentum scanner query failed: {e}")
        
        # Fallback: Load scanning system metrics
        scan_metrics = self.load_state_file('power_station_state.json', {})
        
        # Relay-specific asset selection
        if relay == 'BIN':
            # Binance: Look at our WINNING positions as potential targets
            # Strategy: Feed the winners - add more to profitable positions
            winning_bins = [n for n in self.all_energy_nodes 
                          if n.relay == 'BIN' and n.is_positive_energy and n.pnl_percentage > min_gain_pct_required]
            
            if winning_bins:
                # Pick the best performer
                best = max(winning_bins, key=lambda n: n.pnl_percentage)
                logger.info(f"  🎯 BIN: Feed the winner - {best.symbol} is up {best.pnl_percentage:.1f}%")
                return (best.symbol, best.pnl_percentage * 0.5, 0.8)  # Conservative: expect 50% of current gain
            
            # Fallback: No winners to feed, skip
            logger.debug(f"  BIN: No winning positions above {min_gain_pct_required:.2f}% threshold")
            return None
        
        elif relay == 'KRK':
            # Kraken: Look at our WINNING positions as potential targets
            # Strategy: Feed the winners - add more to profitable positions
            winning_krks = [n for n in self.all_energy_nodes 
                          if n.relay == 'KRK' and n.is_positive_energy and n.pnl_percentage > min_gain_pct_required]
            
            if winning_krks:
                # Pick the best performer
                best = max(winning_krks, key=lambda n: n.pnl_percentage)
                logger.info(f"  🎯 KRK: Feed the winner - {best.symbol} is up {best.pnl_percentage:.1f}%")
                return (best.symbol, best.pnl_percentage * 0.5, 0.8)  # Conservative: expect 50% of current gain
            
            # Fallback: Check for validated branches from 7-day system
            validations_data = self.load_state_file('7day_pending_validations.json', {})
            
            # Handle both dict and list formats
            if isinstance(validations_data, list):
                validations = {f"branch_{i}": v for i, v in enumerate(validations_data)}
            else:
                validations = validations_data
            
            # Find branches ready for 4th decision
            for branch_id, branch in validations.items():
                if not isinstance(branch, dict):
                    continue
                if branch.get('relay') == 'KRK' and branch.get('coherence', 0) > 0.618:
                    symbol = branch.get('symbol', '')
                    expected_gain = branch.get('expected_pip_profit_pct', 0.0)
                    momentum = branch.get('coherence', 0.0)
                    
                    if expected_gain > min_gain_pct_required:
                        return (symbol, expected_gain, momentum)
            
            logger.debug(f"  KRK: No winning positions above {min_gain_pct_required:.2f}% threshold")
            return None
        
        elif relay == 'ALP':
            # Alpaca: Check high-momentum stocks
            watchlist = ['TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMD']
            # TODO: Integrate with real scanning data
            return None
        
        return None
    
    async def analyze_redistribution_opportunities(self) -> List[RedistributionOpportunity]:
        """
        Scan all relays for energy redistribution opportunities.
        Queen's first step: Perceive the energy landscape.
        
        TWO SOURCES OF ENERGY:
        1. Idle cash (USD/USDT) in relay accounts
        2. Profit from positive energy nodes (winning positions)
        """
        opportunities = []
        
        # STEP 1: Scan all energy nodes (positions)
        logger.info("🔍 Scanning all energy nodes across relays...")
        all_nodes = self.scan_all_energy_nodes()
        
        # STEP 2: Find opportunities from IDLE CASH
        logger.info("💰 Checking idle cash opportunities...")
        for relay in ['BIN', 'KRK', 'ALP']:
            # Get idle energy
            idle_usd, source_asset = self.get_relay_idle_energy(relay)
            
            if idle_usd < self.min_idle_energy_usd:
                logger.debug(f"{relay}: Idle cash too low (${idle_usd:.2f} < ${self.min_idle_energy_usd})")
                continue
            
            # Cap at max redistribution per cycle
            max_deploy = idle_usd * self.max_redistribution_per_relay
            
            # Find best conversion target
            conversion = self.find_best_conversion(relay, max_deploy)
            if not conversion:
                logger.debug(f"{relay}: No profitable conversions found for idle cash")
                continue
            
            target_asset, expected_gain_pct, momentum_score = conversion
            
            # Calculate expected gain and drain
            expected_gain_usd = max_deploy * (expected_gain_pct / 100.0)
            
            # Calculate energy drain using relay-specific fees
            drain_info = self.calculate_relay_energy_drain(relay, max_deploy, is_maker=True)
            energy_drain = drain_info['total_drain']
            
            # Calculate net energy gain
            net_energy_gain = expected_gain_usd - energy_drain
            
            # Only consider if net positive
            if net_energy_gain > self.min_net_gain_usd:
                opp = RedistributionOpportunity(
                    relay=relay,
                    source_asset=source_asset,
                    target_asset=target_asset,
                    idle_energy=max_deploy,
                    expected_gain_pct=expected_gain_pct,
                    expected_gain_usd=expected_gain_usd,
                    energy_drain=energy_drain,
                    net_energy_gain=net_energy_gain,
                    momentum_score=momentum_score,
                    confidence=0.7,  # Base confidence
                    source_node=None,  # From idle cash
                    timestamp=time.time()
                )
                opportunities.append(opp)
                logger.info(f"✨ {relay} idle cash opportunity: {target_asset}, net gain ${net_energy_gain:.4f}")
            else:
                logger.debug(f"{relay}: Net gain too low (${net_energy_gain:.4f})")
        
        # STEP 3: Find opportunities from POSITIVE ENERGY NODES
        logger.info("🌱 Checking profit redistribution opportunities...")
        positive_nodes = [n for n in all_nodes if n.is_positive_energy and n.energy_available_to_redistribute > 0]
        
        for node in positive_nodes:
            # This node has profit we can redistribute
            redistributable = node.energy_available_to_redistribute
            
            if redistributable < self.min_idle_energy_usd:
                continue
            
            # Find best target in SAME relay (internal redistribution)
            conversion = self.find_best_conversion(node.relay, redistributable)
            if not conversion:
                logger.debug(f"{node.relay} {node.symbol}: No target for profit redistribution")
                continue
            
            target_asset, expected_gain_pct, momentum_score = conversion
            
            # Calculate expected gain and drain
            expected_gain_usd = redistributable * (expected_gain_pct / 100.0)
            
            # Calculate energy drain using relay-specific fees
            drain_info = self.calculate_relay_energy_drain(node.relay, redistributable, is_maker=True)
            energy_drain = drain_info['total_drain']
            
            # Calculate net energy gain
            net_energy_gain = expected_gain_usd - energy_drain
            
            # Only consider if net positive
            if net_energy_gain > self.min_net_gain_usd:
                opp = RedistributionOpportunity(
                    relay=node.relay,
                    source_asset=node.symbol,
                    target_asset=target_asset,
                    idle_energy=redistributable,
                    expected_gain_pct=expected_gain_pct,
                    expected_gain_usd=expected_gain_usd,
                    energy_drain=energy_drain,
                    net_energy_gain=net_energy_gain,
                    momentum_score=momentum_score,
                    confidence=0.8,  # Higher confidence (from winning position)
                    source_node=node,  # From profitable node
                    timestamp=time.time()
                )
                opportunities.append(opp)
                logger.info(f"✨ {node.relay} node profit opportunity: {node.symbol} → {target_asset}, net gain ${net_energy_gain:.4f}")
            else:
                logger.debug(f"{node.relay} {node.symbol}: Net gain too low (${net_energy_gain:.4f})")
        
        return opportunities
    
    async def queen_analyze_and_decide(self, opportunity: RedistributionOpportunity) -> RedistributionDecision:
        """
        Queen analyzes opportunity and makes decision.
        Uses her consciousness to validate across all realms.
        """
        # Ask Queen if trade will be profitable
        is_profitable, reasoning, drain_details = self.queen.will_trade_be_profitable(
            relay=opportunity.relay,
            trade_value=opportunity.idle_energy,
            expected_gain_pct=opportunity.expected_gain_pct
        )
        
        if not is_profitable:
            decision = RedistributionDecision(
                opportunity=opportunity,
                decision='BLOCK',
                reasoning=reasoning,
                queen_confidence=0.0,
                realms_consensus=0,
                timestamp=time.time()
            )
            logger.warning(f"🚫 Queen BLOCKED {opportunity.relay} {opportunity.target_asset}: {reasoning}")
            return decision
        
        # Check if opportunity meets Queen's standards
        if opportunity.net_energy_gain < self.min_net_gain_usd:
            decision = RedistributionDecision(
                opportunity=opportunity,
                decision='BLOCK',
                reasoning=f"Net gain ${opportunity.net_energy_gain:.4f} below minimum ${self.min_net_gain_usd}",
                queen_confidence=0.0,
                realms_consensus=0,
                timestamp=time.time()
            )
            logger.warning(f"🚫 Queen BLOCKED {opportunity.relay} {opportunity.target_asset}: Net gain too low")
            return decision
        
        # Queen approves
        decision = RedistributionDecision(
            opportunity=opportunity,
            decision='EXECUTE',
            reasoning=reasoning,
            queen_confidence=opportunity.confidence,
            realms_consensus=5,  # All realms agree (simplified for now)
            timestamp=time.time()
        )
        
        logger.info(f"✅ Queen APPROVED {opportunity.relay} {opportunity.target_asset}: {reasoning}")
        return decision
    
    async def execute_redistribution(self, decision: RedistributionDecision) -> Dict:
        """
        Execute Queen's decision to redistribute energy.
        """
        opp = decision.opportunity
        
        if decision.decision != 'EXECUTE':
            logger.info(f"⏸️ Skipping execution for {opp.relay} {opp.target_asset} (decision: {decision.decision})")
            return {
                'success': False,
                'reason': decision.reasoning,
                'decision': decision.decision
            }
        
        if self.dry_run:
            logger.info(f"🔶 DRY-RUN: Would execute {opp.relay} {opp.target_asset} with ${opp.idle_energy:.2f}")
            # Simulate success
            result = {
                'success': True,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'deployed_usd': opp.idle_energy,
                'expected_gain_usd': opp.expected_gain_usd,
                'net_energy_gain': opp.net_energy_gain,
                'energy_drain': opp.energy_drain,
                'timestamp': time.time(),
                'dry_run': True
            }
            
            # Track simulated gains
            self.total_net_energy_gained += opp.net_energy_gain
            self.executions_history.append(result)
            
            return result
        
        # LIVE EXECUTION (when dry_run=False)
        logger.info(f"⚡ LIVE: Executing {opp.relay} {opp.target_asset} with ${opp.idle_energy:.2f}")
        
        try:
            # Execute via appropriate exchange client
            if opp.relay == 'BIN' and self.binance:
                # Binance execution
                order = self.binance.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy  # Will convert to asset quantity
                )
                logger.info(f"✅ Binance order executed: {order}")
            
            elif opp.relay == 'KRK' and self.kraken:
                # Kraken execution
                order = self.kraken.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy
                )
                logger.info(f"✅ Kraken order executed: {order}")
            
            elif opp.relay == 'ALP' and self.alpaca:
                # Alpaca execution
                order = self.alpaca.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy
                )
                logger.info(f"✅ Alpaca order executed: {order}")
            
            else:
                raise Exception(f"Exchange client not available for {opp.relay}")
            
            result = {
                'success': True,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'deployed_usd': opp.idle_energy,
                'expected_gain_usd': opp.expected_gain_usd,
                'net_energy_gain': opp.net_energy_gain,
                'energy_drain': opp.energy_drain,
                'order': order,
                'timestamp': time.time(),
                'dry_run': False
            }
            
            self.total_net_energy_gained += opp.net_energy_gain
            self.executions_history.append(result)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Execution failed for {opp.relay} {opp.target_asset}: {e}")
            result = {
                'success': False,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'error': str(e),
                'timestamp': time.time()
            }
            self.executions_history.append(result)
            return result
    
    async def run_redistribution_cycle(self) -> Dict:
        """
        Run one complete redistribution cycle.
        Queen's full intelligence in action.
        """
        cycle_start = time.time()
        
        logger.info("=" * 60)
        logger.info("🐝 QUEEN POWER REDISTRIBUTION CYCLE STARTING")
        logger.info("=" * 60)
        
        # Calculate and update total system energy FIRST
        total_energy = 0.0
        for relay in ['BIN', 'KRK', 'ALP', 'CAP']:
            idle, _ = self.get_relay_idle_energy(relay)
            total_energy += idle
            logger.info(f"  {relay}: ${idle:.2f} idle energy")
        
        logger.info(f"💎 Total System Energy: ${total_energy:.2f}")
        
        # Update power station state
        power_state = self.load_state_file('power_station_state.json', {})
        power_state['status'] = 'RUNNING'
        power_state['cycles_run'] = power_state.get('cycles_run', 0) + 1
        power_state['total_energy_now'] = total_energy
        power_state['energy_deployed'] = 0.0  # TODO: Calculate from positions
        power_state['net_flow'] = self.total_net_energy_gained
        power_state['efficiency'] = 0.0  # TODO: Calculate
        power_state['last_update'] = time.time()
        
        with open('power_station_state.json', 'w') as f:
            json.dump(power_state, f, indent=2)
        
        # Step 1: Analyze opportunities
        logger.info("🔍 Step 1: Analyzing opportunities across all relays...")
        opportunities = await self.analyze_redistribution_opportunities()
        logger.info(f"Found {len(opportunities)} potential opportunities")
        
        if not opportunities:
            logger.info("No opportunities found this cycle.")
            return {
                'cycle_duration': time.time() - cycle_start,
                'opportunities_found': 0,
                'decisions_made': 0,
                'executions_attempted': 0,
                'executions_successful': 0,
                'net_energy_gained': 0.0
            }
        
        # Step 2: Queen analyzes and decides
        logger.info("🐝 Step 2: Queen analyzing and making decisions...")
        decisions = []
        for opp in opportunities:
            decision = await self.queen_analyze_and_decide(opp)
            decisions.append(decision)
            self.decisions_history.append(decision)
        
        # Step 3: Execute approved decisions
        logger.info("⚡ Step 3: Executing approved redistributions...")
        executions = []
        for decision in decisions:
            if decision.decision == 'EXECUTE':
                result = await self.execute_redistribution(decision)
                executions.append(result)
            else:
                # Track blocked drains
                self.total_blocked_drains_avoided += decision.opportunity.energy_drain
        
        # Summary
        successful_executions = sum(1 for e in executions if e.get('success'))
        net_energy_this_cycle = sum(e.get('net_energy_gain', 0.0) for e in executions if e.get('success'))
        
        cycle_summary = {
            'cycle_duration': time.time() - cycle_start,
            'opportunities_found': len(opportunities),
            'decisions_made': len(decisions),
            'executions_attempted': len(executions),
            'executions_successful': successful_executions,
            'net_energy_gained_this_cycle': net_energy_this_cycle,
            'total_net_energy_gained': self.total_net_energy_gained,
            'total_blocked_drains_avoided': self.total_blocked_drains_avoided
        }
        
        logger.info("=" * 60)
        logger.info("🐝 QUEEN POWER REDISTRIBUTION CYCLE COMPLETE")
        logger.info(f"Duration: {cycle_summary['cycle_duration']:.2f}s")
        logger.info(f"Opportunities: {cycle_summary['opportunities_found']}")
        logger.info(f"Executions: {cycle_summary['executions_successful']}/{cycle_summary['executions_attempted']}")
        logger.info(f"Net Energy Gained This Cycle: ${cycle_summary['net_energy_gained_this_cycle']:.4f}")
        logger.info(f"Total Net Energy Gained: ${cycle_summary['total_net_energy_gained']:.4f}")
        logger.info(f"Total Blocked Drains Avoided: ${cycle_summary['total_blocked_drains_avoided']:.4f}")
        logger.info("=" * 60)
        
        return cycle_summary
    
    async def run_continuous(self):
        """
        Run continuous redistribution cycles.
        Queen's eternal vigilance.
        """
        logger.info("🐝 Queen Power Redistribution: STARTING CONTINUOUS MODE")
        logger.info(f"Scan interval: {self.scan_interval_seconds}s")
        logger.info(f"Dry run: {self.dry_run}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n📊 CYCLE {cycle_count} @ {datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    summary = await self.run_redistribution_cycle()
                    
                    # Save state
                    self.save_state()
                    
                except Exception as e:
                    logger.error(f"❌ Cycle {cycle_count} failed: {e}", exc_info=True)
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {self.scan_interval_seconds}s for next cycle...")
                await asyncio.sleep(self.scan_interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Queen Power Redistribution: STOPPED BY USER")
            self.save_state()
    
    def save_state(self):
        """Save redistribution state to file."""
        state = {
            'last_update': time.time(),
            'total_net_energy_gained': self.total_net_energy_gained,
            'total_blocked_drains_avoided': self.total_blocked_drains_avoided,
            'decisions_count': len(self.decisions_history),
            'executions_count': len(self.executions_history),
            'recent_decisions': [d.to_dict() for d in self.decisions_history[-10:]],
            'recent_executions': self.executions_history[-10:]
        }
        
        try:
            with open('queen_redistribution_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("💾 State saved to queen_redistribution_state.json")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Queen Power Redistribution Engine")
    parser.add_argument('--live', action='store_true', help='Run in LIVE mode (default: dry-run)')
    parser.add_argument('--once', action='store_true', help='Run one cycle then exit')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval in seconds (default: 30)')
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("=" * 60)
    print("🐝 QUEEN POWER REDISTRIBUTION ENGINE")
    print("=" * 60)
    print(f"Mode: {'🔶 DRY-RUN' if dry_run else '⚡ LIVE'}")
    print(f"Interval: {args.interval}s")
    print("=" * 60)
    
    # Initialize system
    system = QueenPowerRedistribution(dry_run=dry_run)
    system.scan_interval_seconds = args.interval
    
    if args.once:
        # Run one cycle
        summary = await system.run_redistribution_cycle()
        system.save_state()
        
        print("\n" + "=" * 60)
        print("📊 SINGLE CYCLE COMPLETE")
        print(json.dumps(summary, indent=2))
        print("=" * 60)
    else:
        # Run continuously
        await system.run_continuous()


if __name__ == '__main__':
    asyncio.run(main())
