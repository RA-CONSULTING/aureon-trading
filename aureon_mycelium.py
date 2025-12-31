#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     🍄 AUREON MYCELIUM NEURAL NETWORK 🍄                                      ║
║                                                                               ║
║     "The underground network where everything connects"                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

MYCELIUM ARCHITECTURE:
======================

Just like how fungal mycelium networks connect trees in a forest,
this system connects all trading agents in a distributed intelligence network.

┌─────────────────────────────────────────────────────────────────────────────┐
│                         MYCELIUM NEURAL NETWORK                             │
│                                                                             │
│   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐                          │
│   │Agent│───│Agent│───│Agent│───│Agent│───│Agent│   ← HIVE 0 (Gen 0)       │
│   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘                          │
│      │         │         │         │         │                              │
│      └─────────┼─────────┼─────────┼─────────┘                              │
│                │    SYNAPSES       │                                        │
│         ┌──────┴──────┐     ┌──────┴──────┐                                 │
│         │   NEURON    │─────│   NEURON    │    ← HIDDEN LAYER               │
│         └──────┬──────┘     └──────┬──────┘                                 │
│                │                   │                                        │
│                └─────────┬─────────┘                                        │
│                          │                                                  │
│                    ┌─────┴─────┐                                            │
│                    │  QUEEN    │    ← DECISION NODE                         │
│                    │  NEURON   │                                            │
│                    └─────┬─────┘                                            │
│                          │                                                  │
│                    ┌─────┴─────┐                                            │
│                    │  SIGNAL   │    ← BUY / SELL / HOLD                     │
│                    └───────────┘                                            │
│                                                                             │
│   When profit > threshold → SPAWN NEW HIVE (budding reproduction)           │
│   90% compounds → 10% harvests for new hive                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

NEURAL COMPONENTS:
- Agent: Individual trading entity with its own strategy bias
- Synapse: Connection between agents that carries signal weight
- Neuron: Processing node that aggregates signals
- Queen Neuron: Final decision maker

MYCELIUM FEATURES:
- Distributed intelligence (no single point of failure)
- Signal propagation through network
- Adaptive weights (learning from successful trades)
- Spawning new hives (network growth)

Gary Leckey & GitHub Copilot | November 2025
"""

import math
import time
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from aureon_memory_core import memory  # 🧠 MEMORY CORE INTEGRATION

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SYNAPSE - Connection between nodes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Synapse:
    """
    A synapse connects two nodes in the network.
    Weight determines signal strength (learning happens here).
    """
    source_id: str
    target_id: str
    weight: float = 1.0
    plasticity: float = 0.1  # How fast the synapse learns
    last_signal: float = 0.0
    activation_count: int = 0
    
    def transmit(self, signal: float) -> float:
        """Transmit signal through synapse with weight modulation"""
        self.last_signal = signal
        self.activation_count += 1
        return signal * self.weight
    
    def strengthen(self, reward: float):
        """Hebbian learning: strengthen successful connections"""
        delta = self.plasticity * reward * self.last_signal
        self.weight = max(0.1, min(2.0, self.weight + delta))
    
    def weaken(self, penalty: float):
        """Weaken unsuccessful connections"""
        delta = self.plasticity * penalty * self.last_signal
        self.weight = max(0.1, self.weight - delta)

# ═══════════════════════════════════════════════════════════════════════════════
# NEURON - Processing node
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Neuron:
    """
    A neuron aggregates signals from synapses and produces output.
    """
    id: str
    bias: float = 0.0
    activation: float = 0.0
    inputs: List[float] = field(default_factory=list)
    
    def activate(self, inputs: List[float]) -> float:
        """
        Activation function: tanh for bounded output [-1, 1]
        Positive = BUY bias, Negative = SELL bias
        """
        self.inputs = inputs
        total = sum(inputs) + self.bias
        self.activation = math.tanh(total)
        return self.activation
    
    def sigmoid(self, x: float) -> float:
        """Sigmoid activation for probability output [0, 1]"""
        return 1 / (1 + math.exp(-x))

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT - Trading entity
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Agent:
    """
    An individual trading agent within a hive.
    Each agent has its own equity and strategy bias.
    """
    id: int
    hive_id: str
    equity: float
    start_equity: float
    trades: int = 0
    wins: int = 0
    prime_idx: int = 0
    symbol: str = "BTCUSDT"
    position_open: bool = False
    last_signal: float = 0.0
    
    def __post_init__(self):
        self.prime_idx = self.id % len(PRIMES)
    
    def compute_signal(self, market_data: Dict[str, float], probability_bias: float = 0.0) -> float:
        """
        Compute trading signal based on market data.
        Returns value in [-1, 1]: negative = SELL, positive = BUY
        """
        # Each agent has a unique perspective based on prime number
        prime = PRIMES[self.prime_idx]
        
        # Factors
        momentum = market_data.get("momentum", 0)
        volatility = market_data.get("volatility", 0.5)
        trend = market_data.get("trend", 0)
        
        # Unique bias per agent
        bias = math.sin(prime * 0.1) * 0.3
        
        # Combine factors - NOW WITH PROBABILITY BIAS!
        # If probability is high, we trust momentum more and ignore volatility
        signal = momentum * 0.4 + trend * 0.3 + bias + (1 - volatility) * 0.2
        
        # 🎯 ONE GOAL INJECTION: If probability is validated, boost signal!
        if probability_bias != 0:
            signal += probability_bias * 0.5
            
        self.last_signal = max(-1, min(1, signal))
        
        return self.last_signal
    
    def execute_trade(self, signal: float, price: float) -> Dict[str, Any]:
        """
        Execute a trade based on signal.
        Returns trade result.
        """
        self.trades += 1
        
        # Position sizing based on prime number (0.02 to 0.97% of equity)
        prime = PRIMES[self.prime_idx]
        self.prime_idx = (self.prime_idx + 1) % len(PRIMES)
        position_pct = prime * 0.01
        
        # Simulate trade (in real system, would call Binance)
        # For now, use signal as proxy for return direction
        expected_return = signal * 0.002  # ±0.2% expected move
        noise = (random.random() - 0.5) * 0.001  # ±0.05% noise
        actual_return = expected_return + noise
        
        pnl = self.equity * position_pct * actual_return
        self.equity += pnl
        
        if pnl > 0:
            self.wins += 1
        
        return {
            "agent_id": self.id,
            "signal": signal,
            "position_pct": position_pct,
            "pnl": pnl,
            "new_equity": self.equity,
            "win": pnl > 0
        }
    
    def get_profit(self) -> float:
        """Get profit since start"""
        return self.equity - self.start_equity
    
    def get_win_rate(self) -> float:
        """Get win rate"""
        return self.wins / self.trades if self.trades > 0 else 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# HIVE - Collection of agents
# ═══════════════════════════════════════════════════════════════════════════════

class Hive:
    """
    A hive contains multiple agents working together.
    Implements the 10-9-1 revenue model.
    """
    
    def __init__(self, hive_id: str, generation: int, agent_count: int, 
                 equity_per_agent: float, target_per_agent: float):
        self.id = hive_id
        self.generation = generation
        self.agent_count = agent_count
        self.start_equity_per_agent = equity_per_agent
        self.target_per_agent = target_per_agent
        
        # Create agents
        self.agents: List[Agent] = []
        for i in range(agent_count):
            agent = Agent(
                id=i,
                hive_id=hive_id,
                equity=equity_per_agent,
                start_equity=equity_per_agent
            )
            self.agents.append(agent)
        
        # Metrics
        self.trades = 0
        self.harvested_capital = 0.0
        self.age = 0
        self.successful_agents = 0
        
        # Neural components
        self.neuron = Neuron(id=f"hive_{hive_id}_neuron")
        self.synapses: List[Synapse] = []
        self._create_synapses()
    
    def _create_synapses(self):
        """Create synapses between agents and hive neuron"""
        for agent in self.agents:
            synapse = Synapse(
                source_id=f"agent_{agent.id}",
                target_id=self.neuron.id,
                weight=1.0 / len(self.agents)  # Equal initial weights
            )
            self.synapses.append(synapse)
    
    def step(self, market_data: Dict[str, float], probability_bias: float = 0.0) -> Dict[str, Any]:
        """
        Execute one trading step for all agents.
        """
        self.age += 1
        
        # Collect signals from all agents
        signals = []
        for agent in self.agents:
            if agent.equity > 0:
                signal = agent.compute_signal(market_data, probability_bias)
                signals.append(signal)
        
        # Transmit through synapses
        transmitted = []
        for i, synapse in enumerate(self.synapses):
            if i < len(signals):
                transmitted.append(synapse.transmit(signals[i]))
        
        # Aggregate in neuron
        hive_signal = self.neuron.activate(transmitted)
        
        # Execute trades for agents with strong signals
        results = []
        for agent in self.agents:
            if agent.equity > 0 and agent.equity < self.target_per_agent:
                price = market_data.get("price", 95000)
                result = agent.execute_trade(hive_signal, price)
                results.append(result)
                self.trades += 1
                
                # Update synapse weights based on result
                synapse = self.synapses[agent.id] if agent.id < len(self.synapses) else None
                if synapse:
                    if result["win"]:
                        synapse.strengthen(0.1)
                    else:
                        synapse.weaken(0.05)
                
                # Check if agent reached target
                if agent.equity >= self.target_per_agent:
                    self.successful_agents += 1
        
        return {
            "hive_id": self.id,
            "hive_signal": hive_signal,
            "trades": len(results),
            "results": results
        }
    
    def harvest_capital(self) -> float:
        """
        10-9-1 model: Extract 10% of profit for new hive spawning.
        """
        total_equity = self.get_total_equity()
        start_total = self.start_equity_per_agent * self.agent_count
        total_profit = max(0, total_equity - start_total)
        
        harvest_amount = total_profit * 0.10  # 10% harvest
        self.harvested_capital += harvest_amount
        
        # Deduct harvest from agents proportionally
        for agent in self.agents:
            agent_profit = agent.get_profit()
            if agent_profit > 0:
                agent_harvest = agent_profit * 0.10
                agent.equity -= agent_harvest
        
        return harvest_amount
    
    def get_total_equity(self) -> float:
        """Get total equity across all agents"""
        return sum(agent.equity for agent in self.agents)
    
    def get_profit_multiplier(self) -> float:
        """Get profit multiplier (current / start)"""
        start_total = self.start_equity_per_agent * self.agent_count
        return self.get_total_equity() / start_total if start_total > 0 else 1.0
    
    def can_split(self) -> bool:
        """Check if hive is ready to spawn a new hive"""
        return self.successful_agents >= self.agent_count * 0.5
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get hive metrics"""
        stage = "mature" if self.successful_agents == self.agent_count else \
                "ready_to_split" if self.can_split() else "growing"
        
        return {
            "id": self.id,
            "generation": self.generation,
            "agents": self.agent_count,
            "equity": self.get_total_equity(),
            "harvested_capital": self.harvested_capital,
            "trades": self.trades,
            "successful_agents": self.successful_agents,
            "stage": stage,
            "age": self.age,
            "profit_multiplier": self.get_profit_multiplier()
        }

# ═══════════════════════════════════════════════════════════════════════════════
# MYCELIUM NETWORK - The full neural network
# ═══════════════════════════════════════════════════════════════════════════════

class MyceliumNetwork:
    """
    The Mycelium Neural Network - connects all hives in a distributed intelligence.
    
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║  🎯 ONE GOAL: GROW NET PROFIT - FAST! 🎯                                      ║
    ║                                                                               ║
    ║  Every decision, every signal, every spawn - serves ONE purpose:             ║
    ║  MAXIMIZE NET PROFIT GROWTH AS FAST AS POSSIBLE                               ║
    ║                                                                               ║
    ║  The Mycelium doesn't care about:                                             ║
    ║  - Being "safe" (we have other systems for risk)                              ║
    ║  - Waiting around (time = money)                                              ║
    ║  - Small gains (we compound AGGRESSIVELY)                                     ║
    ║                                                                               ║
    ║  The Mycelium ONLY cares about:                                               ║
    ║  - NET PROFIT (after ALL fees)                                                ║
    ║  - GROWTH RATE (faster is better)                                             ║
    ║  - COMPOUNDING (every penny back in)                                          ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    
    Like fungal mycelium in a forest, this network:
    - Distributes resources (capital) where needed
    - Shares information (market signals)
    - Enables collective decision making
    - Grows through spawning new hives
    """
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 THE ONE GOAL - ENCODED INTO EVERY FIBER
    # ═══════════════════════════════════════════════════════════════════════════════
    ONE_GOAL = "GROW_NET_PROFIT_FAST"

    def acknowledge_war_band(self):
        """
        Connects the Apache War Band to the Mycelium Network.
        The War Band acts as an autonomous special forces unit.
        """
        logger.info("🍄 Mycelium Network: Connected to Apache War Band (Autonomous Unit)")
        # The War Band operates as a specialized hunter-killer node
        # It feeds profit back into the ecosystem, fueling the mycelial growth.
    GROWTH_AGGRESSION = 0.9  # 90% aggressive growth mode
    COMPOUND_RATE = 0.95     # 95% of profits compound back
    MIN_PROFIT_TARGET = 0.03 # Minimum $0.03 net profit per trade
    
    def __init__(self, initial_capital: float, agents_per_hive: int = 5,
                 target_multiplier: float = 2.0):
        self.initial_capital = initial_capital
        self.agents_per_hive = agents_per_hive
        self.target_multiplier = target_multiplier
        
        # 🎯 THE GOAL - Track it obsessively
        self.starting_equity = initial_capital
        self.peak_equity = initial_capital
        self.net_profit_total = 0.0
        self.profit_rate_per_hour = 0.0
        self.start_time = time.time()
        
        # Network state
        self.hives: List[Hive] = []
        self.generation = 0
        self.total_harvested = 0.0
        self.split_events: List[Dict] = []
        self.step_count = 0
        
        # Queen neuron - final decision aggregator
        self.queen_neuron = Neuron(id="queen", bias=0.0)
        self.hive_synapses: List[Synapse] = []
        
        # Create root hive
        self._spawn_hive(initial_capital)
        
        logger.info(f"🍄 Mycelium Network initialized with ${initial_capital:.2f}")
        logger.info(f"🎯 ONE GOAL ACTIVE: {self.ONE_GOAL} | Aggression: {self.GROWTH_AGGRESSION*100}%")
    
    def _spawn_hive(self, capital: float, parent_generation: int = -1) -> Hive:
        """Spawn a new hive with given capital"""
        new_generation = parent_generation + 1
        hive_id = f"hive_{new_generation}_{len(self.hives)}"
        
        equity_per_agent = capital / self.agents_per_hive
        target_per_agent = equity_per_agent * self.target_multiplier
        
        hive = Hive(
            hive_id=hive_id,
            generation=new_generation,
            agent_count=self.agents_per_hive,
            equity_per_agent=equity_per_agent,
            target_per_agent=target_per_agent
        )
        
        self.hives.append(hive)
        
        # Create synapse from hive to queen
        synapse = Synapse(
            source_id=hive_id,
            target_id="queen",
            weight=1.0 / (len(self.hives) + 1)
        )
        self.hive_synapses.append(synapse)
        
        # Update all synapse weights for balance
        for syn in self.hive_synapses:
            syn.weight = 1.0 / len(self.hive_synapses)
        
        self.generation = max(self.generation, new_generation)
        
        logger.info(f"🐝 Spawned {hive_id} (Gen {new_generation}) with ${capital:.4f}")
        
        return hive
    
    def step(self, market_data: Dict[str, float], probability_map: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Execute one step of the mycelium network.
        All hives process market data and contribute to collective decision.
        """
        self.step_count += 1
        
        # 🌊 SURGE WINDOW CHECK
        # If we are in a surge window, we boost the signal transmission
        surge_active = memory.is_surge_window_active()
        
        # Extract probability bias from map (average of all validated signals)
        prob_bias = 0.0
        if probability_map:
            # Use the average probability of high-confidence signals as a global bias
            high_conf_probs = [p for p in probability_map.values() if p > 0.7]
            if high_conf_probs:
                prob_bias = (sum(high_conf_probs) / len(high_conf_probs)) * 2 - 1 # Map [0.7, 1.0] to [0.4, 1.0] approx
        
        # Step all hives and collect signals
        hive_signals = []
        all_results = []
        
        for hive in self.hives:
            result = hive.step(market_data, probability_bias=prob_bias)
            signal = result["hive_signal"]
            
            # Boost signal during surge
            if surge_active:
                signal *= 1.5
                
            hive_signals.append(signal)
            all_results.append(result)
        
        # Transmit through hive synapses to queen
        transmitted = []
        for i, synapse in enumerate(self.hive_synapses):
            if i < len(hive_signals):
                # Synapses learn faster during surge
                if surge_active:
                    synapse.plasticity = 0.2 # Double learning rate
                else:
                    synapse.plasticity = 0.1
                    
                transmitted.append(synapse.transmit(hive_signals[i]))
        
        # Queen neuron makes final decision
        queen_signal = self.queen_neuron.activate(transmitted)
        
        # Check for hive splitting (ONLY during surge or high profit)
        if surge_active or self.get_profit_multiplier() > 1.1:
            self._check_splits()
        
        # Periodic harvesting
        if self.step_count % 10 == 0:
            self._harvest_all()
        
        return {
            "step": self.step_count,
            "queen_signal": queen_signal,
            "hive_count": len(self.hives),
            "total_equity": self.get_total_equity(),
            "generation": self.generation,
            "results": all_results,
            "surge_active": surge_active
        }
    
    def _check_splits(self):
        """Check if any hives are ready to split"""
        for hive in self.hives:
            if hive.can_split() and hive.harvested_capital > 0:
                # Spawn new hive with harvested capital
                spawn_capital = hive.harvested_capital
                hive.harvested_capital = 0
                
                new_hive = self._spawn_hive(spawn_capital, hive.generation)
                
                self.split_events.append({
                    "step": self.step_count,
                    "parent_hive": hive.id,
                    "new_hive": new_hive.id,
                    "spawn_capital": spawn_capital
                })
    
    def _harvest_all(self):
        """Harvest capital from all hives"""
        for hive in self.hives:
            harvested = hive.harvest_capital()
            self.total_harvested += harvested
    
    def get_total_equity(self) -> float:
        """Get total equity across all hives"""
        return sum(hive.get_total_equity() for hive in self.hives)
    
    def get_total_agents(self) -> int:
        """Get total agent count"""
        return sum(hive.agent_count for hive in self.hives)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 THE ONE GOAL - PROFIT TRACKING & ACCELERATION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def record_trade_profit(self, net_profit: float, trade_data: Dict = None):
        """
        Record a trade profit - THE MOST IMPORTANT METHOD!
        Every penny of net profit gets tracked and compounds.
        """
        self.net_profit_total += net_profit
        
        # Update equity tracking
        current_equity = self.get_total_equity()
        self.peak_equity = max(self.peak_equity, current_equity)
        
        # Calculate profit rate ($ per hour)
        elapsed_hours = max((time.time() - self.start_time) / 3600, 0.001)
        self.profit_rate_per_hour = self.net_profit_total / elapsed_hours
        
        # Compound profits back into the network (95%)
        compound_amount = net_profit * self.COMPOUND_RATE
        if compound_amount > 0 and self.hives:
            # Distribute to strongest performing hive's agents
            best_hive = max(self.hives, key=lambda h: h.get_profit_multiplier())
            for agent in best_hive.agents:
                agent.equity += compound_amount / len(best_hive.agents)
        
        logger.info(f"🎯 NET PROFIT: ${net_profit:+.4f} | Total: ${self.net_profit_total:.2f} | Rate: ${self.profit_rate_per_hour:.2f}/hr")
    
    def get_growth_stats(self) -> Dict[str, Any]:
        """
        Get growth statistics - how fast are we achieving THE GOAL?
        """
        current_equity = self.get_total_equity()
        elapsed_hours = max((time.time() - self.start_time) / 3600, 0.001)
        elapsed_days = elapsed_hours / 24
        
        return {
            "one_goal": self.ONE_GOAL,
            "starting_equity": self.starting_equity,
            "current_equity": current_equity,
            "net_profit_total": self.net_profit_total,
            "profit_rate_per_hour": self.profit_rate_per_hour,
            "profit_rate_per_day": self.profit_rate_per_hour * 24,
            "growth_percentage": ((current_equity - self.starting_equity) / max(self.starting_equity, 1)) * 100,
            "elapsed_hours": elapsed_hours,
            "elapsed_days": elapsed_days,
            "peak_equity": self.peak_equity,
            "compound_rate": self.COMPOUND_RATE,
            "aggression": self.GROWTH_AGGRESSION
        }
    
    def boost_signal_for_profit(self, base_signal: float, expected_profit: float) -> float:
        """
        Boost signals that lead to more profit.
        THE GOAL: If it makes money, DO MORE OF IT!
        """
        if expected_profit <= 0:
            return base_signal * 0.5  # Reduce signals that don't make money
        
        # Boost proportional to expected profit
        profit_boost = min(expected_profit / self.MIN_PROFIT_TARGET, 3.0)
        boosted = base_signal * (1 + (profit_boost * self.GROWTH_AGGRESSION))
        
        return min(boosted, 1.0)  # Cap at 1.0
    
    def should_take_trade(self, expected_net_profit: float, confidence: float) -> bool:
        """
        Simple decision: Does this trade grow net profit?
        If yes → TAKE IT. If no → SKIP IT.
        
        THE LOGIC:
        - Below $0.03 target → NEVER take (not worth fees)
        - At $0.03 → Need 70% confidence
        - At $0.05 → Need 60% confidence (profit justifies risk)
        - At $0.10+ → Need only 50% confidence (big profit = GO!)
        """
        # Must meet minimum profit target
        if expected_net_profit < self.MIN_PROFIT_TARGET:
            return False
        
        # Higher profit = lower confidence needed (more aggressive scaling)
        # Every $0.01 above min target reduces required confidence by 5%
        profit_above_min = expected_net_profit - self.MIN_PROFIT_TARGET
        confidence_reduction = profit_above_min * 5  # 5% per $0.01
        
        required_confidence = 0.7 - confidence_reduction
        required_confidence = max(required_confidence, 0.5)  # Never go below 50%
        
        return confidence >= required_confidence
    
    def get_state(self) -> Dict[str, Any]:
        """Get full network state - INCLUDING THE GOAL METRICS!"""
        growth = self.get_growth_stats()
        return {
            "timestamp": time.time(),
            "step": self.step_count,
            "one_goal": self.ONE_GOAL,
            "net_profit_total": growth["net_profit_total"],
            "profit_rate_per_day": growth["profit_rate_per_day"],
            "growth_percentage": growth["growth_percentage"],
            "total_hives": len(self.hives),
            "total_agents": self.get_total_agents(),
            "total_equity": self.get_total_equity(),
            "total_harvested": self.total_harvested,
            "generation": self.generation,
            "hives": [hive.get_metrics() for hive in self.hives],
            "split_events": self.split_events[-10:]  # Last 10 splits
        }
    
    def display(self):
        """Display network status - ALWAYS SHOW THE GOAL!"""
        state = self.get_state()
        growth = self.get_growth_stats()
        
        print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🎯 ONE GOAL: {self.ONE_GOAL:^55} 🎯  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  💰 NET PROFIT: ${growth['net_profit_total']:>12.2f}  |  📈 Rate: ${growth['profit_rate_per_day']:>8.2f}/day          ║
║  📊 Growth: {growth['growth_percentage']:>6.1f}%  |  Peak: ${growth['peak_equity']:>10.2f}                          ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                        🍄 MYCELIUM NEURAL NETWORK 🍄                          ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Step: {state['step']:<10}  Generation: {state['generation']:<5}                                ║
║  Hives: {state['total_hives']:<10} Agents: {state['total_agents']:<5}                                    ║
║  Total Equity: ${state['total_equity']:<15.4f}                                      ║
║  Harvested: ${state['total_harvested']:<15.4f}                                         ║
╠═══════════════════════════════════════════════════════════════════════════════╣""")
        
        for hive in state['hives'][:5]:  # Show first 5 hives
            stage_emoji = "🌱" if hive['stage'] == 'growing' else \
                         "🔄" if hive['stage'] == 'ready_to_split' else "🏆"
            print(f"║  {stage_emoji} {hive['id']}: ${hive['equity']:.4f} ({hive['profit_multiplier']:.2f}x) [{hive['stage']}]")
        
        if len(state['hives']) > 5:
            print(f"║  ... and {len(state['hives']) - 5} more hives")
        
        print("╚═══════════════════════════════════════════════════════════════════════════════╝")


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH AUREON NEXUS
# ═══════════════════════════════════════════════════════════════════════════════

def create_mycelium_for_nexus(initial_capital: float = 100.0) -> MyceliumNetwork:
    """
    Factory function to create a Mycelium Network integrated with Aureon Nexus.
    """
    return MyceliumNetwork(
        initial_capital=initial_capital,
        agents_per_hive=5,
        target_multiplier=2.0
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN - Demo
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     🍄 AUREON MYCELIUM NEURAL NETWORK - DEMO 🍄                               ║
║                                                                               ║
║     "The underground network where everything connects"                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create network with $100 initial capital
    network = MyceliumNetwork(initial_capital=100.0, agents_per_hive=5)
    
    # Simulate 50 trading steps
    for i in range(50):
        # Simulated market data
        market_data = {
            "price": 95000 + random.uniform(-500, 500),
            "momentum": random.uniform(-0.5, 0.5),
            "volatility": random.uniform(0.2, 0.8),
            "trend": random.uniform(-0.3, 0.3)
        }
        
        result = network.step(market_data)
        
        if i % 10 == 0:
            network.display()
    
    # Final state
    print("\n📊 FINAL STATE:")
    network.display()
    
    state = network.get_state()
    print(f"\n✅ Simulation complete!")
    print(f"   Steps: {state['step']}")
    print(f"   Final Equity: ${state['total_equity']:.2f}")
    print(f"   ROI: {((state['total_equity'] - 100) / 100 * 100):.2f}%")
    print(f"   Hive Spawns: {len(state['split_events'])}")
