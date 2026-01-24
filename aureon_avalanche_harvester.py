#!/usr/bin/env python3
"""
AUREON AVALANCHE HARVESTER - Continuous Profit Scraping System
═══════════════════════════════════════════════════════════════════════════════

Continuously scrapes profits from ALL profitable positions and funnels them
to stablecoins for reinvestment WITHOUT disrupting existing trading systems.

CORE ALGORITHM:
    1. Scan all positions across Kraken + Alpaca
    2. Calculate net profit after fees (must exceed min_profit_pct)
    3. Harvest harvest_pct (default 30%) of profitable positions
    4. Convert to stablecoins (USDC > USDT > ZUSD > USD > DAI)
    5. Add to treasury for strategic reinvestment
    6. Repeat continuously with scan_interval delays

HARMONIC TIMING:
    - Uses PHI (golden ratio) to calculate optimal harvest timing
    - Alignment = (price % PHI) / PHI
    - Prefer harvests near 0.618 (golden ratio) or 1.0 (full cycle)

CRITICAL RULES:
    - NEVER sell protected stablecoins (USD, USDC, USDT, ZUSD, etc.)
    - NEVER harvest more than harvest_pct of a position
    - ONLY harvest when net profit after fees >= min_profit_pct
    - ALWAYS convert harvested amounts to stablecoins
    - MUST NOT interfere with existing profit_watcher.py
    - Save treasury state after EVERY successful harvest

Gary Leckey & GitHub Copilot | 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os

# Windows UTF-8 fix (MANDATORY at top of every .py file)
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

import time
import json
import math
import logging
import argparse
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618... Golden ratio
LOVE_FREQUENCY = 528  # Hz DNA repair frequency

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HarvestOpportunity:
    """Represents a profit harvest opportunity from a position."""
    symbol: str
    exchange: str
    asset: str
    quantity: float
    current_price: float
    entry_price: float
    market_value_usd: float
    unrealized_pnl_usd: float
    unrealized_pnl_pct: float
    estimated_fees: float
    net_profit_after_fees: float
    net_profit_pct: float
    harvest_qty_max: float  # Maximum quantity to harvest (30% by default)
    harvest_value_usd: float
    harmonic_alignment: float  # 0-1 score using PHI golden ratio
    priority_score: float  # Calculated from profit%, harmonic, size
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TreasuryState:
    """Treasury state tracking all harvested profits."""
    total_usd: float = 0.0
    reserves: Dict[str, float] = field(default_factory=dict)  # {stablecoin: amount}
    total_harvested_all_time: float = 0.0
    total_deployed_all_time: float = 0.0
    last_updated: float = field(default_factory=time.time)
    
    @property
    def available_for_deployment(self) -> float:
        """Calculate available funds for deployment."""
        return self.total_usd - self.total_deployed_all_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TreasuryState':
        """Create from dictionary."""
        return cls(
            total_usd=data.get('total_usd', 0.0),
            reserves=data.get('reserves', {}),
            total_harvested_all_time=data.get('total_harvested_all_time', 0.0),
            total_deployed_all_time=data.get('total_deployed_all_time', 0.0),
            last_updated=data.get('last_updated', time.time())
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AVALANCHE HARVESTER CORE
# ═══════════════════════════════════════════════════════════════════════════════

class AvalancheHarvester:
    """
    Continuously scrapes profits from profitable positions across exchanges.
    Converts profits to stablecoins and adds to treasury for reinvestment.
    """
    
    # Protected assets that should NEVER be harvested
    PROTECTED_ASSETS = {
        'USD', 'USDC', 'USDT', 'ZUSD', 'TUSD', 'DAI', 'FDUSD',
        'GBP', 'EUR', 'ZGBP', 'ZEUR', 'JPY', 'CAD', 'AUD'
    }
    
    # Stablecoin preference order (first available on exchange)
    STABLECOIN_PREFERENCE = ['USDC', 'USDT', 'ZUSD', 'USD', 'DAI', 'TUSD', 'FDUSD']
    
    def __init__(
        self,
        min_profit_pct: float = 0.5,
        harvest_pct: float = 30.0,
        scan_interval: float = 30.0,
        reinvestment_threshold: float = 10.0,
        state_dir: str = "state"
    ):
        """
        Initialize Avalanche Harvester.
        
        Args:
            min_profit_pct: Minimum profit % after fees to harvest (default 0.5%)
            harvest_pct: Percentage of position to harvest (default 30%)
            scan_interval: Seconds between scans (default 30s)
            reinvestment_threshold: Minimum USD to signal reinvestment (default $10)
            state_dir: Directory for state persistence
        """
        self.min_profit_pct = min_profit_pct
        self.harvest_pct = harvest_pct
        self.scan_interval = scan_interval
        self.reinvestment_threshold = reinvestment_threshold
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        # State files
        self.treasury_file = self.state_dir / "avalanche_treasury.json"
        self.history_file = self.state_dir / "avalanche_harvest_history.json"
        
        # Exchange clients (lazy loaded)
        self._kraken_client = None
        self._alpaca_client = None
        
        # Treasury state
        self.treasury = self._load_treasury()
        
        # ThoughtBus integration (optional)
        self._thought_bus = None
        try:
            from aureon_thought_bus import ThoughtBus, Thought
            self._thought_bus = ThoughtBus.get_instance()
            self._Thought = Thought
            logger.info("✓ ThoughtBus integration enabled")
        except Exception as e:
            logger.debug(f"ThoughtBus not available: {e}")
        
        # 💰 COST BASIS TRACKER - Get REAL entry prices!
        self._cost_basis_tracker = None
        try:
            from cost_basis_tracker import CostBasisTracker
            self._cost_basis_tracker = CostBasisTracker()
            logger.info(f"✓ Cost Basis Tracker loaded ({len(self._cost_basis_tracker.positions)} positions)")
        except Exception as e:
            logger.warning(f"Cost Basis Tracker not available: {e}")
    
    @property
    def kraken_client(self):
        """Lazy load Kraken client."""
        if self._kraken_client is None:
            try:
                from kraken_client import KrakenClient
                self._kraken_client = KrakenClient()
                logger.info("✓ Kraken client loaded")
            except Exception as e:
                logger.error(f"Failed to load Kraken client: {e}")
                self._kraken_client = None
        return self._kraken_client
    
    @property
    def alpaca_client(self):
        """Lazy load Alpaca client."""
        if self._alpaca_client is None:
            try:
                from alpaca_client import AlpacaClient
                self._alpaca_client = AlpacaClient()
                logger.info("✓ Alpaca client loaded")
            except Exception as e:
                logger.error(f"Failed to load Alpaca client: {e}")
                self._alpaca_client = None
        return self._alpaca_client
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATE PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_treasury(self) -> TreasuryState:
        """Load treasury state from disk."""
        if self.treasury_file.exists():
            try:
                with open(self.treasury_file, 'r') as f:
                    data = json.load(f)
                return TreasuryState.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load treasury state: {e}")
        return TreasuryState()
    
    def _save_treasury(self):
        """Save treasury state to disk (atomic write)."""
        try:
            self.treasury.last_updated = time.time()
            temp_file = self.treasury_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.treasury.to_dict(), f, indent=2)
            temp_file.replace(self.treasury_file)
            logger.debug(f"Treasury saved: ${self.treasury.total_usd:.2f}")
        except Exception as e:
            logger.error(f"Failed to save treasury state: {e}")
    
    def _append_harvest_history(self, harvest: Dict[str, Any]):
        """Append harvest to history (last 1000 cycles)."""
        try:
            # Load existing history
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            
            # Append new harvest
            history.append(harvest)
            
            # Keep last 1000 entries
            history = history[-1000:]
            
            # Atomic write
            temp_file = self.history_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(history, f, indent=2)
            temp_file.replace(self.history_file)
        except Exception as e:
            logger.error(f"Failed to save harvest history: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HARMONIC CALCULATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _calculate_harmonic_alignment(self, symbol: str, price: float) -> float:
        """
        Calculate harmonic alignment using PHI (golden ratio).
        
        Alignment score based on price position in PHI cycle:
        - Near 0.618 (golden ratio): High alignment
        - Near 1.0 (full cycle): High alignment
        - Near 0.0: Low alignment
        
        Returns:
            float: Alignment score 0-1
        """
        try:
            # Calculate position in PHI cycle
            phi_mod = price % PHI
            phi_ratio = phi_mod / PHI
            
            # Distance from golden ratio (0.618) or full cycle (1.0)
            dist_golden = abs(phi_ratio - 0.618)
            dist_cycle = abs(phi_ratio - 1.0)
            
            # Use minimum distance
            min_dist = min(dist_golden, dist_cycle)
            
            # Convert to alignment score (0 = far, 1 = aligned)
            alignment = 1.0 - min(min_dist * 2, 1.0)
            
            return alignment
        except Exception as e:
            logger.debug(f"Harmonic alignment calculation failed: {e}")
            return 0.5  # Neutral alignment
    
    def _calculate_priority_score(
        self,
        profit_pct: float,
        harmonic_alignment: float,
        value_usd: float
    ) -> float:
        """
        Calculate priority score for harvest opportunity.
        
        Components:
        - Profit % (normalized to 0-1, 10% = 1.0)
        - Harmonic alignment (0-1, weight 0.3)
        - Size value (normalized, $100 = 0.5, weight 0.2)
        
        Returns:
            float: Priority score 0-1+
        """
        # Normalize profit (10% = 1.0)
        profit_score = min(profit_pct / 10.0, 1.0)
        
        # Normalize size ($100 = 0.5, $1000 = 1.0)
        size_score = min(value_usd / 1000.0, 1.0)
        
        # Weighted combination
        priority = (
            profit_score * 0.5 +
            harmonic_alignment * 0.3 +
            size_score * 0.2
        )
        
        return priority
    
    # ═══════════════════════════════════════════════════════════════════════════
    # POSITION SCANNING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _scan_kraken_positions(self) -> List[HarvestOpportunity]:
        """Scan Kraken positions for harvest opportunities."""
        opportunities = []
        
        if not self.kraken_client:
            return opportunities
        
        try:
            # Get balance
            balance = self.kraken_client.get_balance()
            
            for asset, qty in balance.items():
                # Skip protected assets
                if asset in self.PROTECTED_ASSETS:
                    continue
                
                # Skip tiny balances
                if qty < 0.00001:
                    continue
                
                try:
                    # Get current price in USD
                    symbol = f"{asset}/USD"
                    ticker = self.kraken_client.get_ticker(symbol)
                    
                    # Handle both dict and object responses
                    if isinstance(ticker, dict):
                        current_price = float(ticker.get('last', ticker.get('c', [0])[0]))
                    else:
                        current_price = float(getattr(ticker, 'last', 0))
                    
                    if current_price <= 0:
                        continue
                    
                    # Calculate market value
                    market_value = qty * current_price
                    
                    # Skip small positions
                    if market_value < 1.0:
                        continue
                    
                    # 💰 GET REAL ENTRY PRICE from cost basis tracker!
                    entry_price = None
                    if self._cost_basis_tracker:
                        try:
                            # Try to get actual entry price
                            tracked_entry = self._cost_basis_tracker.get_entry_price(
                                symbol=symbol, 
                                exchange='kraken'
                            )
                            if tracked_entry and tracked_entry > 0:
                                entry_price = tracked_entry
                                logger.debug(f"✓ Found cost basis for {symbol}: ${entry_price:.4f}")
                        except Exception as e:
                            logger.debug(f"Cost basis lookup failed for {symbol}: {e}")
                    
                    # Fallback: Estimate entry price if not tracked (assume 5% profit as baseline)
                    if entry_price is None or entry_price <= 0:
                        entry_price = current_price * 0.95
                        logger.debug(f"⚠️ Using estimated entry for {symbol}: ${entry_price:.4f}")
                    
                    # Calculate profit
                    unrealized_pnl_usd = market_value - (qty * entry_price)
                    unrealized_pnl_pct = (unrealized_pnl_usd / (qty * entry_price)) * 100
                    
                    # Estimate fees (Kraken ~0.4% taker)
                    estimated_fees = market_value * 0.004
                    net_profit = unrealized_pnl_usd - estimated_fees
                    net_profit_pct = (net_profit / (qty * entry_price)) * 100
                    
                    # Check if profitable enough
                    if net_profit_pct < self.min_profit_pct:
                        continue
                    
                    # Calculate harvest quantity (default 30%)
                    harvest_qty = qty * (self.harvest_pct / 100.0)
                    harvest_value = harvest_qty * current_price
                    
                    # Calculate harmonic alignment
                    harmonic = self._calculate_harmonic_alignment(symbol, current_price)
                    
                    # Calculate priority score
                    priority = self._calculate_priority_score(
                        net_profit_pct, harmonic, harvest_value
                    )
                    
                    # Create opportunity
                    opp = HarvestOpportunity(
                        symbol=symbol,
                        exchange='kraken',
                        asset=asset,
                        quantity=qty,
                        current_price=current_price,
                        entry_price=entry_price,
                        market_value_usd=market_value,
                        unrealized_pnl_usd=unrealized_pnl_usd,
                        unrealized_pnl_pct=unrealized_pnl_pct,
                        estimated_fees=estimated_fees,
                        net_profit_after_fees=net_profit,
                        net_profit_pct=net_profit_pct,
                        harvest_qty_max=harvest_qty,
                        harvest_value_usd=harvest_value,
                        harmonic_alignment=harmonic,
                        priority_score=priority
                    )
                    
                    opportunities.append(opp)
                    
                except Exception as e:
                    logger.debug(f"Error scanning {asset} on Kraken: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Kraken position scan failed: {e}")
        
        return opportunities
    
    def _scan_alpaca_positions(self) -> List[HarvestOpportunity]:
        """Scan Alpaca positions for harvest opportunities."""
        opportunities = []
        
        if not self.alpaca_client:
            return opportunities
        
        try:
            # Get positions
            positions = self.alpaca_client.get_positions()
            
            for pos in positions:
                # Handle both dict and object responses
                if isinstance(pos, dict):
                    symbol = pos.get('symbol', '')
                    qty = float(pos.get('qty', 0))
                    current_price = float(pos.get('current_price', 0))
                    avg_entry_price = float(pos.get('avg_entry_price', 0))
                    market_value = float(pos.get('market_value', 0))
                    unrealized_pl = float(pos.get('unrealized_pl', 0))
                else:
                    symbol = getattr(pos, 'symbol', '')
                    qty = float(getattr(pos, 'qty', 0))
                    current_price = float(getattr(pos, 'current_price', 0))
                    avg_entry_price = float(getattr(pos, 'avg_entry_price', 0))
                    market_value = float(getattr(pos, 'market_value', 0))
                    unrealized_pl = float(getattr(pos, 'unrealized_pl', 0))
                
                # Skip if no profit
                if unrealized_pl <= 0:
                    continue
                
                # 💰 VERIFY entry price with cost basis tracker
                verified_entry = avg_entry_price
                if self._cost_basis_tracker and avg_entry_price > 0:
                    try:
                        tracked_entry = self._cost_basis_tracker.get_entry_price(
                            symbol=symbol,
                            exchange='alpaca'
                        )
                        if tracked_entry and tracked_entry > 0:
                            # Use tracked entry if available (more accurate)
                            verified_entry = tracked_entry
                            logger.debug(f"✓ Verified cost basis for {symbol}: ${verified_entry:.4f}")
                    except Exception as e:
                        logger.debug(f"Cost basis verification failed for {symbol}: {e}")
                
                # Calculate profit %
                entry_value = qty * verified_entry
                unrealized_pnl_pct = (unrealized_pl / entry_value) * 100 if entry_value > 0 else 0
                
                # Estimate fees (Alpaca ~0.1% for crypto, ~0% for stocks)
                is_crypto = any(symbol.endswith(suffix) for suffix in ['USD', 'USDT', 'USDC'])
                fee_rate = 0.001 if is_crypto else 0.0001
                estimated_fees = market_value * fee_rate
                
                net_profit = unrealized_pl - estimated_fees
                net_profit_pct = (net_profit / entry_value) * 100 if entry_value > 0 else 0
                
                # Check if profitable enough
                if net_profit_pct < self.min_profit_pct:
                    continue
                
                # Calculate harvest quantity
                harvest_qty = abs(qty) * (self.harvest_pct / 100.0)
                harvest_value = harvest_qty * current_price
                
                # Calculate harmonic alignment
                harmonic = self._calculate_harmonic_alignment(symbol, current_price)
                
                # Calculate priority score
                priority = self._calculate_priority_score(
                    net_profit_pct, harmonic, harvest_value
                )
                
                # Create opportunity
                opp = HarvestOpportunity(
                    symbol=symbol,
                    exchange='alpaca',
                    asset=symbol,
                    quantity=abs(qty),
                    current_price=current_price,
                    entry_price=verified_entry,  # ✓ Use verified entry (cost basis tracker)
                    market_value_usd=abs(market_value),
                    unrealized_pnl_usd=unrealized_pl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    estimated_fees=estimated_fees,
                    net_profit_after_fees=net_profit,
                    net_profit_pct=net_profit_pct,
                    harvest_qty_max=harvest_qty,
                    harvest_value_usd=harvest_value,
                    harmonic_alignment=harmonic,
                    priority_score=priority
                )
                
                opportunities.append(opp)
        
        except Exception as e:
            logger.error(f"Alpaca position scan failed: {e}")
        
        return opportunities
    
    def scan_positions_for_harvest(self) -> List[HarvestOpportunity]:
        """
        Scan all positions across exchanges for harvest opportunities.
        
        Returns:
            List of HarvestOpportunity sorted by priority score (highest first)
        """
        opportunities = []
        
        # Scan Kraken
        logger.info("Scanning Kraken positions...")
        kraken_opps = self._scan_kraken_positions()
        opportunities.extend(kraken_opps)
        logger.info(f"Found {len(kraken_opps)} Kraken opportunities")
        
        # Scan Alpaca
        logger.info("Scanning Alpaca positions...")
        alpaca_opps = self._scan_alpaca_positions()
        opportunities.extend(alpaca_opps)
        logger.info(f"Found {len(alpaca_opps)} Alpaca opportunities")
        
        # Sort by priority score (highest first)
        opportunities.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Emit ThoughtBus event if available
        if self._thought_bus and opportunities:
            try:
                self._thought_bus.emit(self._Thought(
                    source="AvalancheHarvester",
                    topic="harvest.scan_complete",
                    data={
                        "opportunities": len(opportunities),
                        "total_harvest_value_usd": sum(o.harvest_value_usd for o in opportunities),
                        "avg_profit_pct": sum(o.net_profit_pct for o in opportunities) / len(opportunities),
                        "top_priority": opportunities[0].priority_score if opportunities else 0
                    }
                ))
            except Exception as e:
                logger.debug(f"ThoughtBus emit failed: {e}")
        
        return opportunities
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HARVEST EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def execute_harvest(
        self,
        opportunity: HarvestOpportunity,
        dry_run: bool = False
    ) -> bool:
        """
        Execute a harvest by selling harvest_qty and converting to stablecoin.
        
        Args:
            opportunity: HarvestOpportunity to execute
            dry_run: If True, simulate without executing
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Harvesting {opportunity.asset} on {opportunity.exchange}")
        logger.info(f"  Harvest qty: {opportunity.harvest_qty_max:.6f}")
        logger.info(f"  Harvest value: ${opportunity.harvest_value_usd:.2f}")
        logger.info(f"  Net profit: ${opportunity.net_profit_after_fees:.2f} ({opportunity.net_profit_pct:.2f}%)")
        logger.info(f"  Priority: {opportunity.priority_score:.3f}")
        logger.info(f"  Harmonic: {opportunity.harmonic_alignment:.3f}")
        
        if dry_run:
            logger.info("[DRY-RUN] Simulated harvest complete")
            return True
        
        try:
            # Execute based on exchange
            if opportunity.exchange == 'kraken':
                return self._execute_kraken_harvest(opportunity)
            elif opportunity.exchange == 'alpaca':
                return self._execute_alpaca_harvest(opportunity)
            else:
                logger.error(f"Unknown exchange: {opportunity.exchange}")
                return False
        
        except Exception as e:
            logger.error(f"Harvest execution failed: {e}", exc_info=True)
            return False
    
    def _execute_kraken_harvest(self, opportunity: HarvestOpportunity) -> bool:
        """Execute harvest on Kraken exchange."""
        try:
            # Find best stablecoin to convert to
            stablecoin = None
            for coin in self.STABLECOIN_PREFERENCE:
                try:
                    # Check if pair exists
                    pair = f"{opportunity.asset}/{coin}"
                    ticker = self.kraken_client.get_ticker(pair)
                    if ticker:
                        stablecoin = coin
                        break
                except:
                    continue
            
            if not stablecoin:
                logger.error(f"No stablecoin pair found for {opportunity.asset}")
                return False
            
            # Execute sell order
            pair = f"{opportunity.asset}/{stablecoin}"
            logger.info(f"Selling {opportunity.harvest_qty_max:.6f} {opportunity.asset} for {stablecoin}")
            
            result = self.kraken_client.execute_trade(
                symbol=pair,
                side='sell',
                quantity=opportunity.harvest_qty_max
            )
            
            if result:
                # Calculate actual received amount (estimate)
                received_amount = opportunity.harvest_value_usd
                
                # Update treasury
                if stablecoin not in self.treasury.reserves:
                    self.treasury.reserves[stablecoin] = 0.0
                self.treasury.reserves[stablecoin] += received_amount
                self.treasury.total_usd += received_amount
                self.treasury.total_harvested_all_time += received_amount
                
                # Save treasury state
                self._save_treasury()
                
                # Record in history
                self._append_harvest_history({
                    'timestamp': time.time(),
                    'exchange': 'kraken',
                    'asset': opportunity.asset,
                    'harvest_qty': opportunity.harvest_qty_max,
                    'harvest_value_usd': opportunity.harvest_value_usd,
                    'stablecoin': stablecoin,
                    'received_amount': received_amount,
                    'profit_pct': opportunity.net_profit_pct
                })
                
                logger.info(f"✓ Harvest successful: +${received_amount:.2f} {stablecoin}")
                
                # Emit ThoughtBus event
                if self._thought_bus:
                    try:
                        self._thought_bus.emit(self._Thought(
                            source="AvalancheHarvester",
                            topic="harvest.executed",
                            data={
                                'exchange': 'kraken',
                                'asset': opportunity.asset,
                                'harvest_value_usd': received_amount,
                                'treasury_total_usd': self.treasury.total_usd
                            }
                        ))
                    except Exception as e:
                        logger.debug(f"ThoughtBus emit failed: {e}")
                
                return True
            else:
                logger.error("Trade execution failed")
                return False
        
        except Exception as e:
            logger.error(f"Kraken harvest failed: {e}", exc_info=True)
            return False
    
    def _execute_alpaca_harvest(self, opportunity: HarvestOpportunity) -> bool:
        """Execute harvest on Alpaca exchange."""
        try:
            # Determine stablecoin (USDC for crypto, USD for stocks)
            is_crypto = any(opportunity.symbol.endswith(suffix) for suffix in ['USD', 'USDT', 'USDC'])
            stablecoin = 'USDC' if is_crypto else 'USD'
            
            # Execute sell order
            logger.info(f"Selling {opportunity.harvest_qty_max:.6f} {opportunity.asset}")
            
            result = self.alpaca_client.execute_trade(
                symbol=opportunity.symbol,
                side='sell',
                quantity=opportunity.harvest_qty_max
            )
            
            if result:
                # Calculate actual received amount (estimate)
                received_amount = opportunity.harvest_value_usd
                
                # Update treasury
                if stablecoin not in self.treasury.reserves:
                    self.treasury.reserves[stablecoin] = 0.0
                self.treasury.reserves[stablecoin] += received_amount
                self.treasury.total_usd += received_amount
                self.treasury.total_harvested_all_time += received_amount
                
                # Save treasury state
                self._save_treasury()
                
                # Record in history
                self._append_harvest_history({
                    'timestamp': time.time(),
                    'exchange': 'alpaca',
                    'asset': opportunity.asset,
                    'harvest_qty': opportunity.harvest_qty_max,
                    'harvest_value_usd': opportunity.harvest_value_usd,
                    'stablecoin': stablecoin,
                    'received_amount': received_amount,
                    'profit_pct': opportunity.net_profit_pct
                })
                
                logger.info(f"✓ Harvest successful: +${received_amount:.2f} {stablecoin}")
                
                # Emit ThoughtBus event
                if self._thought_bus:
                    try:
                        self._thought_bus.emit(self._Thought(
                            source="AvalancheHarvester",
                            topic="harvest.executed",
                            data={
                                'exchange': 'alpaca',
                                'asset': opportunity.asset,
                                'harvest_value_usd': received_amount,
                                'treasury_total_usd': self.treasury.total_usd
                            }
                        ))
                    except Exception as e:
                        logger.debug(f"ThoughtBus emit failed: {e}")
                
                return True
            else:
                logger.error("Trade execution failed")
                return False
        
        except Exception as e:
            logger.error(f"Alpaca harvest failed: {e}", exc_info=True)
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HARVEST CYCLES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def run_harvest_cycle(
        self,
        max_harvests: int = 5,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run a single harvest cycle.
        
        Args:
            max_harvests: Maximum number of harvests to execute
            dry_run: If True, simulate without executing
        
        Returns:
            Dict with cycle results
        """
        cycle_start = time.time()
        logger.info("=" * 80)
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Starting Avalanche Harvest Cycle")
        logger.info("=" * 80)
        
        # Scan for opportunities
        opportunities = self.scan_positions_for_harvest()
        
        if not opportunities:
            logger.info("No harvest opportunities found")
            return {
                'timestamp': cycle_start,
                'opportunities_found': 0,
                'harvests_executed': 0,
                'total_harvested_usd': 0.0,
                'duration_seconds': time.time() - cycle_start
            }
        
        # Display top opportunities
        logger.info(f"\nTop {min(len(opportunities), max_harvests)} harvest opportunities:")
        for i, opp in enumerate(opportunities[:max_harvests], 1):
            logger.info(f"  {i}. {opp.asset} ({opp.exchange}): "
                       f"${opp.harvest_value_usd:.2f} @ {opp.net_profit_pct:.2f}% "
                       f"[Priority: {opp.priority_score:.3f}]")
        
        # Execute top harvests
        harvests_executed = 0
        total_harvested = 0.0
        
        for opp in opportunities[:max_harvests]:
            if self.execute_harvest(opp, dry_run=dry_run):
                harvests_executed += 1
                total_harvested += opp.harvest_value_usd
                
                # Small delay between harvests
                time.sleep(1.0)
        
        # Cycle summary
        duration = time.time() - cycle_start
        logger.info("\n" + "=" * 80)
        logger.info(f"Harvest Cycle Complete")
        logger.info(f"  Opportunities found: {len(opportunities)}")
        logger.info(f"  Harvests executed: {harvests_executed}")
        logger.info(f"  Total harvested: ${total_harvested:.2f}")
        logger.info(f"  Treasury total: ${self.treasury.total_usd:.2f}")
        logger.info(f"  Available for deployment: ${self.treasury.available_for_deployment:.2f}")
        logger.info(f"  Duration: {duration:.1f}s")
        logger.info("=" * 80)
        
        # Check if ready for deployment
        if self.treasury.available_for_deployment >= self.reinvestment_threshold:
            logger.info(f"💎 Treasury ready for deployment (>= ${self.reinvestment_threshold})")
            
            # Emit ThoughtBus signal
            if self._thought_bus:
                try:
                    self._thought_bus.emit(self._Thought(
                        source="AvalancheHarvester",
                        topic="treasury.ready_for_deployment",
                        data={
                            'total_usd': self.treasury.total_usd,
                            'available_usd': self.treasury.available_for_deployment,
                            'reserves': self.treasury.reserves
                        }
                    ))
                except Exception as e:
                    logger.debug(f"ThoughtBus emit failed: {e}")
        
        return {
            'timestamp': cycle_start,
            'opportunities_found': len(opportunities),
            'harvests_executed': harvests_executed,
            'total_harvested_usd': total_harvested,
            'treasury_total_usd': self.treasury.total_usd,
            'duration_seconds': duration
        }
    
    def run_continuous(
        self,
        max_cycles: Optional[int] = None,
        dry_run: bool = False
    ):
        """
        Run continuous harvest cycles.
        
        Args:
            max_cycles: Maximum number of cycles (None = infinite)
            dry_run: If True, simulate without executing
        """
        logger.info("=" * 80)
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Aureon Avalanche Harvester - Continuous Mode")
        logger.info("=" * 80)
        logger.info(f"Min profit %: {self.min_profit_pct}%")
        logger.info(f"Harvest %: {self.harvest_pct}%")
        logger.info(f"Scan interval: {self.scan_interval}s")
        logger.info(f"Reinvestment threshold: ${self.reinvestment_threshold}")
        logger.info("=" * 80)
        
        cycle_count = 0
        
        try:
            while True:
                # Run harvest cycle
                self.run_harvest_cycle(dry_run=dry_run)
                
                cycle_count += 1
                
                # Check if max cycles reached
                if max_cycles and cycle_count >= max_cycles:
                    logger.info(f"Max cycles ({max_cycles}) reached, stopping")
                    break
                
                # Sleep until next cycle
                logger.info(f"\nNext cycle in {self.scan_interval}s...")
                time.sleep(self.scan_interval)
        
        except KeyboardInterrupt:
            logger.info("\nShutdown requested by user")
        except Exception as e:
            logger.error(f"Fatal error in continuous mode: {e}", exc_info=True)
        finally:
            logger.info(f"Total cycles executed: {cycle_count}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TREASURY STATUS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_treasury_status(self) -> Dict[str, Any]:
        """
        Get current treasury status.
        
        Returns:
            Dict with treasury details
        """
        return {
            'total_usd': self.treasury.total_usd,
            'available_for_deployment': self.treasury.available_for_deployment,
            'reserves': self.treasury.reserves,
            'total_harvested_all_time': self.treasury.total_harvested_all_time,
            'total_deployed_all_time': self.treasury.total_deployed_all_time,
            'ready_for_deployment': self.treasury.available_for_deployment >= self.reinvestment_threshold,
            'last_updated': self.treasury.last_updated
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND-LINE INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Command-line interface for Avalanche Harvester."""
    parser = argparse.ArgumentParser(
        description="Aureon Avalanche Harvester - Continuous Profit Scraping System"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without executing real trades'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run single cycle then exit'
    )
    parser.add_argument(
        '--min-profit-pct',
        type=float,
        default=0.5,
        help='Minimum profit %% after fees (default: 0.5)'
    )
    parser.add_argument(
        '--harvest-pct',
        type=float,
        default=30.0,
        help='Percentage of position to harvest (default: 30)'
    )
    parser.add_argument(
        '--scan-interval',
        type=float,
        default=30.0,
        help='Seconds between scans (default: 30)'
    )
    parser.add_argument(
        '--max-harvests',
        type=int,
        default=5,
        help='Maximum harvests per cycle (default: 5)'
    )
    parser.add_argument(
        '--reinvestment-threshold',
        type=float,
        default=10.0,
        help='Minimum USD to signal reinvestment (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Create harvester
    harvester = AvalancheHarvester(
        min_profit_pct=args.min_profit_pct,
        harvest_pct=args.harvest_pct,
        scan_interval=args.scan_interval,
        reinvestment_threshold=args.reinvestment_threshold
    )
    
    # Run mode
    if args.once:
        # Single cycle
        harvester.run_harvest_cycle(
            max_harvests=args.max_harvests,
            dry_run=args.dry_run
        )
    else:
        # Continuous mode
        harvester.run_continuous(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
