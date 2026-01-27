"""
🎯 AUREON TURN-BASED STRATEGY 🎯

Chess & Checkers style trading:
- Stablecoins are CHECKPOINTS (safe squares)
- Each move must COMPOUND profit
- Plan sequences: BUY → CONVERT → BUY → SELL
- Probability Matrix decides the moves
- Mycelium coordinates all systems

THE BOARD:
┌─────────────────────────────────────────────────────────┐
│  STABLECOINS (Checkpoints)     ASSETS (Pieces)         │
│  ═══════════════════════       ══════════════════      │
│  USDC, USDT, ZUSD, TUSD        BTC, ETH, SOL, APE...   │
│                                                         │
│  Safe squares to rest          Pieces that move/grow   │
│  No loss when holding          Risk but reward         │
└─────────────────────────────────────────────────────────┘

MOVE TYPES:
1. BUY    = Move from checkpoint → asset (plant seed)
2. SELL   = Move from asset → checkpoint (harvest profit)
3. CONVERT = Move asset → asset (compound position)

STRATEGY:
- Only BUY when dip detected AND probability > 70%
- Only SELL when price > buy_price + fees (PROFIT GUARANTEED)
- Only CONVERT when target momentum > source momentum
- Use CHECKPOINTS to secure gains before next move
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Stablecoins = CHECKPOINTS (safe squares)
CHECKPOINTS = {'USDC', 'USDT', 'ZUSD', 'TUSD', 'USD', 'BUSD', 'DAI'}


class MoveType(Enum):
    BUY = "🌱 BUY"           # Checkpoint → Asset (plant)
    SELL = "🌾 SELL"         # Asset → Checkpoint (harvest)
    CONVERT = "🔄 CONVERT"   # Asset → Asset (compound)
    HOLD = "⏸️ HOLD"         # Wait for better opportunity


@dataclass
class Position:
    """A piece on the board"""
    asset: str
    amount: float
    buy_price: float
    buy_time: float
    exchange: str
    
    @property
    def is_checkpoint(self) -> bool:
        return self.asset.upper() in CHECKPOINTS
    
    def profit_at_price(self, current_price: float, fee_rate: float = 0.001) -> float:
        """Calculate profit if sold at current price"""
        if self.is_checkpoint:
            return 0  # Checkpoints don't profit/loss
        gross = (current_price - self.buy_price) * self.amount
        fees = current_price * self.amount * fee_rate * 2  # Buy + sell fees
        return gross - fees
    
    def min_sell_price(self, fee_rate: float = 0.001) -> float:
        """Minimum price to sell for profit"""
        # sell_price * amount - fees > buy_price * amount + fees
        # sell_price > buy_price * (1 + 2*fee_rate) / (1 - fee_rate)
        return self.buy_price * (1 + 2 * fee_rate) / (1 - fee_rate)


@dataclass
class PlannedMove:
    """A planned chess move"""
    move_type: MoveType
    from_asset: str
    to_asset: str
    amount: float
    exchange: str
    expected_profit: float
    probability: float
    reason: str
    sequence_id: int = 0  # Which move in the sequence


@dataclass
class MoveSequence:
    """A planned sequence of moves (like chess notation)"""
    moves: List[PlannedMove] = field(default_factory=list)
    total_expected_profit: float = 0.0
    probability: float = 0.0
    start_time: float = field(default_factory=time.time)
    
    def add_move(self, move: PlannedMove):
        move.sequence_id = len(self.moves)
        self.moves.append(move)
        self.total_expected_profit += move.expected_profit
        # Combined probability
        self.probability = self.probability * move.probability if self.probability > 0 else move.probability


class TurnBasedStrategy:
    """
    🎯 THE CHESS MASTER
    
    Plans multi-step sequences that COMPOUND profit.
    Uses probability matrix to decide moves.
    Treats stablecoins as checkpoints.
    """
    
    def __init__(
        self,
        mycelium=None,
        probability_matrix=None,
        trade_tracker=None,
        min_profit: float = 0.02,  # Minimum profit per trade
        fee_rate: float = 0.001,   # 0.1% per trade
    ):
        self.mycelium = mycelium
        self.probability_matrix = probability_matrix
        self.trade_tracker = trade_tracker
        self.min_profit = min_profit
        self.fee_rate = fee_rate
        
        # Board state
        self.positions: Dict[str, Position] = {}  # asset -> Position
        self.checkpoint_balance: Dict[str, float] = {}  # checkpoint -> amount
        
        # Move history
        self.move_history: List[PlannedMove] = []
        self.current_sequence: Optional[MoveSequence] = None
        
        # Strategy state
        self.turn_number = 0
        self.total_profit = 0.0
        self.wins = 0
        self.losses = 0
        
        logger.info("♟️ Turn-Based Strategy initialized")
        logger.info(f"   Min profit: ${min_profit}")
        logger.info(f"   Fee rate: {fee_rate*100:.2f}%")
        logger.info(f"   Checkpoints: {CHECKPOINTS}")
    
    def update_board(self, holdings: Dict[str, Dict[str, float]], prices: Dict[str, Dict[str, float]]):
        """Update board state from current holdings"""
        for exchange, assets in holdings.items():
            for asset, amount in assets.items():
                if amount < 0.001:
                    continue
                    
                key = f"{exchange}:{asset}"
                price = prices.get(asset, {}).get(exchange, 0)
                
                if asset.upper() in CHECKPOINTS:
                    self.checkpoint_balance[key] = amount
                elif key not in self.positions:
                    # New position - record at current price as cost basis
                    self.positions[key] = Position(
                        asset=asset,
                        amount=amount,
                        buy_price=price,
                        buy_time=time.time(),
                        exchange=exchange
                    )
                else:
                    # Update amount
                    self.positions[key].amount = amount
    
    def get_best_move(
        self,
        prices: Dict[str, Dict[str, float]],
        momentum: Dict[str, float],
        cost_basis: Dict[str, List[Dict]]
    ) -> Optional[PlannedMove]:
        """
        🎯 THE BRAIN - Decide the best move
        
        Uses probability matrix + mycelium consensus
        to find the GUARANTEED PROFIT move.
        """
        candidates: List[PlannedMove] = []
        
        # 1. CHECK SELLS - Can we harvest any profits?
        for key, position in self.positions.items():
            if position.is_checkpoint:
                continue
                
            asset = position.asset
            exchange = position.exchange
            current_price = prices.get(asset, {}).get(exchange, 0)
            
            if current_price <= 0:
                continue
            
            # Get TRUE cost basis
            true_buy_price = position.buy_price
            if asset in cost_basis and cost_basis[asset]:
                # Use FIFO cost basis
                true_buy_price = cost_basis[asset][0].get('price', position.buy_price)
            
            # Calculate REAL profit
            min_sell = true_buy_price * (1 + 2 * self.fee_rate) / (1 - self.fee_rate)
            profit = (current_price - true_buy_price) * position.amount - (current_price * position.amount * self.fee_rate * 2)
            
            # Only sell if PROFITABLE
            if current_price >= min_sell and profit >= self.min_profit:
                # Get probability from matrix
                prob = self._get_sell_probability(asset, current_price, momentum.get(asset, 0))
                
                candidates.append(PlannedMove(
                    move_type=MoveType.SELL,
                    from_asset=asset,
                    to_asset='USDC',  # Sell to checkpoint
                    amount=position.amount,
                    exchange=exchange,
                    expected_profit=profit,
                    probability=prob,
                    reason=f"🌾 HARVEST: {asset} profit ${profit:.4f} (price ${current_price:.4f} > min ${min_sell:.4f})"
                ))
        
        # 2. CHECK CONVERTS - Can we compound into better momentum?
        for key, position in self.positions.items():
            if position.is_checkpoint:
                continue
                
            asset = position.asset
            exchange = position.exchange
            current_price = prices.get(asset, {}).get(exchange, 0)
            from_momentum = momentum.get(asset, 0)
            
            if current_price <= 0:
                continue
            
            # Find better momentum targets
            for target_asset, target_mom in momentum.items():
                if target_asset == asset or target_asset.upper() in CHECKPOINTS:
                    continue
                    
                target_price = prices.get(target_asset, {}).get(exchange, 0)
                if target_price <= 0:
                    continue
                
                # Convert if target momentum is SIGNIFICANTLY better
                mom_diff = target_mom - from_momentum
                if mom_diff > 0.02:  # 2% momentum advantage
                    value = position.amount * current_price
                    expected_gain = value * mom_diff * 0.5  # Conservative estimate
                    
                    if expected_gain > self.min_profit:
                        prob = self._get_convert_probability(asset, target_asset, from_momentum, target_mom)
                        
                        candidates.append(PlannedMove(
                            move_type=MoveType.CONVERT,
                            from_asset=asset,
                            to_asset=target_asset,
                            amount=position.amount,
                            exchange=exchange,
                            expected_profit=expected_gain,
                            probability=prob,
                            reason=f"🔄 COMPOUND: {asset}→{target_asset} (mom {from_momentum*100:+.2f}%→{target_mom*100:+.2f}%)"
                        ))
        
        # 3. CHECK BUYS - Can we plant seeds on dips?
        total_checkpoints = sum(self.checkpoint_balance.values())
        if total_checkpoints >= 5.0:  # Have checkpoint funds
            for asset, mom in momentum.items():
                if asset.upper() in CHECKPOINTS:
                    continue
                    
                # Buy on significant dips
                if mom < -0.03:  # 3% dip
                    for exchange in ['binance', 'kraken', 'alpaca']:
                        price = prices.get(asset, {}).get(exchange, 0)
                        if price <= 0:
                            continue
                        
                        # Check we have checkpoint on this exchange
                        checkpoint_key = None
                        for ck in ['USDC', 'USDT', 'ZUSD', 'USD']:
                            key = f"{exchange}:{ck}"
                            if key in self.checkpoint_balance and self.checkpoint_balance[key] >= 5:
                                checkpoint_key = key
                                break
                        
                        if not checkpoint_key:
                            continue
                        
                        spend = min(self.checkpoint_balance[checkpoint_key] * 0.3, 15.0)
                        if spend < 5:
                            continue
                        
                        # Expected recovery
                        expected_recovery = spend * abs(mom) * 0.5  # Conservative
                        
                        if expected_recovery > self.min_profit:
                            prob = self._get_buy_probability(asset, price, mom)
                            
                            candidates.append(PlannedMove(
                                move_type=MoveType.BUY,
                                from_asset=checkpoint_key.split(':')[1],
                                to_asset=asset,
                                amount=spend / price,
                                exchange=exchange,
                                expected_profit=expected_recovery,
                                probability=prob,
                                reason=f"🌱 PLANT: {asset} on {mom*100:.2f}% dip"
                            ))
        
        # 4. SELECT BEST MOVE
        if not candidates:
            return None
        
        # Score by: profit × probability
        candidates.sort(key=lambda m: m.expected_profit * m.probability, reverse=True)
        best = candidates[0]
        
        # Only execute if probability > 60%
        if best.probability < 0.6:
            return None
        
        return best
    
    def _get_sell_probability(self, asset: str, price: float, momentum: float) -> float:
        """Get probability of successful sell from matrix/mycelium"""
        base_prob = 0.7
        
        # Boost if momentum positive (price likely to drop after selling)
        if momentum > 0:
            base_prob += min(0.2, momentum * 2)
        
        # Get mycelium consensus
        if self.mycelium and hasattr(self.mycelium, 'get_consensus'):
            try:
                consensus = self.mycelium.get_consensus(asset)
                if consensus.get('direction') == 'BEARISH':
                    base_prob += 0.1  # Good time to sell
            except:
                pass
        
        # Get probability matrix prediction
        if self.probability_matrix and hasattr(self.probability_matrix, 'get_prediction'):
            try:
                pred = self.probability_matrix.get_prediction(asset)
                if pred.get('direction') == 'DOWN':
                    base_prob += 0.1
            except:
                pass
        
        return min(0.95, base_prob)
    
    def _get_buy_probability(self, asset: str, price: float, momentum: float) -> float:
        """Get probability of successful buy (bounce from dip)"""
        base_prob = 0.5
        
        # Stronger dip = higher bounce probability
        if momentum < -0.03:
            base_prob += min(0.3, abs(momentum) * 3)
        
        # Get mycelium consensus
        if self.mycelium and hasattr(self.mycelium, 'get_consensus'):
            try:
                consensus = self.mycelium.get_consensus(asset)
                if consensus.get('direction') == 'BULLISH':
                    base_prob += 0.15
            except:
                pass
        
        return min(0.9, base_prob)
    
    def _get_convert_probability(self, from_asset: str, to_asset: str, from_mom: float, to_mom: float) -> float:
        """Get probability of successful conversion"""
        base_prob = 0.6
        
        # Higher momentum difference = higher probability
        mom_diff = to_mom - from_mom
        base_prob += min(0.3, mom_diff * 3)
        
        return min(0.9, base_prob)
    
    def record_move(self, move: PlannedMove, actual_profit: float):
        """Record completed move and update stats"""
        self.move_history.append(move)
        self.total_profit += actual_profit
        self.turn_number += 1
        
        if actual_profit > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        # Broadcast to mycelium
        if self.mycelium and hasattr(self.mycelium, 'broadcast_signal'):
            try:
                self.mycelium.broadcast_signal('turn_complete', {
                    'turn': self.turn_number,
                    'move_type': move.move_type.name,
                    'from': move.from_asset,
                    'to': move.to_asset,
                    'profit': actual_profit,
                    'total_profit': self.total_profit,
                    'win_rate': self.wins / max(1, self.wins + self.losses)
                })
            except:
                pass
    
    def get_status(self) -> Dict:
        """Get current strategy status"""
        return {
            'turn': self.turn_number,
            'total_profit': self.total_profit,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': self.wins / max(1, self.wins + self.losses),
            'positions': len(self.positions),
            'checkpoints': sum(self.checkpoint_balance.values()),
        }
    
    def print_board(self):
        """Print current board state"""
        print("\n" + "♟️" * 30)
        print("   TURN-BASED STRATEGY BOARD")
        print("♟️" * 30)
        
        print(f"\n   🎯 Turn: {self.turn_number}")
        print(f"   💰 Total Profit: ${self.total_profit:.4f}")
        print(f"   📊 Win Rate: {self.wins}/{self.wins + self.losses}")
        
        print("\n   📍 CHECKPOINTS (Safe Squares):")
        for key, amount in self.checkpoint_balance.items():
            if amount > 0.01:
                print(f"      {key}: ${amount:.2f}")
        
        print("\n   ♟️ POSITIONS (Pieces):")
        for key, pos in self.positions.items():
            if not pos.is_checkpoint and pos.amount > 0.001:
                print(f"      {key}: {pos.amount:.4f} @ ${pos.buy_price:.4f}")
        
        print("\n" + "♟️" * 30)


# ═══════════════════════════════════════════════════════════════
# 🎯 PROFIT GATE - Only allow moves that GUARANTEE profit
# ═══════════════════════════════════════════════════════════════

class ProfitGate:
    """
    🚦 THE GATE KEEPER
    
    Blocks any move that won't profit.
    Uses cost basis to calculate TRUE profit.
    """
    
    def __init__(self, trade_tracker, min_profit: float = 0.01, fee_rate: float = 0.001):
        self.trade_tracker = trade_tracker
        self.min_profit = min_profit
        self.fee_rate = fee_rate
    
    def can_sell(self, asset: str, amount: float, current_price: float, exchange: str) -> Tuple[bool, float, str]:
        """
        Check if selling would be profitable.
        Returns: (allowed, expected_profit, reason)
        """
        if not self.trade_tracker or asset not in self.trade_tracker.cost_basis:
            return False, 0, "No cost basis - can't calculate profit"
        
        cost_basis = self.trade_tracker.cost_basis.get(asset, [])
        if not cost_basis:
            return False, 0, "Empty cost basis"
        
        # Calculate TRUE profit using FIFO
        remaining = amount
        total_cost = 0
        
        for lot in cost_basis:
            if remaining <= 0:
                break
            use_qty = min(remaining, lot['qty'])
            total_cost += use_qty * lot['price']
            remaining -= use_qty
        
        if remaining > 0:
            return False, 0, f"Not enough cost basis for {amount} {asset}"
        
        # Calculate profit
        gross_revenue = amount * current_price
        total_fees = gross_revenue * self.fee_rate + total_cost * self.fee_rate
        net_profit = gross_revenue - total_cost - total_fees
        
        if net_profit < self.min_profit:
            min_price = (total_cost + self.min_profit + total_fees) / amount
            return False, net_profit, f"Would lose ${-net_profit:.4f} - need price ${min_price:.4f}"
        
        return True, net_profit, f"✅ PROFIT: ${net_profit:.4f}"
    
    def can_convert(self, from_asset: str, to_asset: str, amount: float, 
                    from_price: float, to_price: float, 
                    from_momentum: float, to_momentum: float) -> Tuple[bool, float, str]:
        """
        Check if conversion would be beneficial.
        """
        # Conversion is allowed if target momentum is significantly better
        mom_diff = to_momentum - from_momentum
        
        if mom_diff < 0.01:  # Need at least 1% momentum advantage
            return False, 0, f"Momentum diff {mom_diff*100:.2f}% too small"
        
        value = amount * from_price
        expected_gain = value * mom_diff * 0.3  # Conservative
        conversion_cost = value * self.fee_rate * 2  # Two trades
        
        net_expected = expected_gain - conversion_cost
        
        if net_expected < self.min_profit:
            return False, net_expected, f"Expected gain ${net_expected:.4f} < min ${self.min_profit}"
        
        return True, net_expected, f"✅ Expected: ${net_expected:.4f} from momentum shift"
    
    def can_buy(self, asset: str, spend_amount: float, price: float, 
                momentum: float) -> Tuple[bool, float, str]:
        """
        Check if buying on dip is likely to profit.
        """
        # Only buy on significant dips
        if momentum > -0.02:
            return False, 0, f"Momentum {momentum*100:.2f}% not a dip"
        
        # Expected recovery
        expected_recovery = spend_amount * abs(momentum) * 0.3  # Conservative
        buy_cost = spend_amount * self.fee_rate
        
        net_expected = expected_recovery - buy_cost
        
        if net_expected < self.min_profit:
            return False, net_expected, f"Expected recovery ${net_expected:.4f} < min ${self.min_profit}"
        
        return True, net_expected, f"✅ Expected recovery: ${net_expected:.4f} from {momentum*100:.2f}% dip"


# ═══════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    strategy = TurnBasedStrategy(min_profit=0.02)
    
    # Simulate some positions
    strategy.checkpoint_balance = {
        'binance:USDC': 50.0,
        'kraken:ZUSD': 10.0
    }
    
    strategy.positions = {
        'binance:APE': Position('APE', 27.0, 0.22, time.time(), 'binance'),
        'binance:CRV': Position('CRV', 10.0, 0.43, time.time(), 'binance'),
    }
    
    strategy.print_board()
    
    # Get best move
    prices = {
        'APE': {'binance': 0.23, 'kraken': 0.23},
        'CRV': {'binance': 0.44, 'kraken': 0.44},
        'SOL': {'binance': 190.0, 'kraken': 190.0},
    }
    momentum = {
        'APE': 0.02,
        'CRV': -0.01,
        'SOL': 0.05,
    }
    
    move = strategy.get_best_move(prices, momentum, {})
    if move:
        print(f"\n🎯 BEST MOVE: {move.move_type.value}")
        print(f"   {move.from_asset} → {move.to_asset}")
        print(f"   Expected: ${move.expected_profit:.4f}")
        print(f"   Probability: {move.probability:.1%}")
        print(f"   Reason: {move.reason}")
    else:
        print("\n⏸️ HOLD - No profitable move found")
