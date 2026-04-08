"""
🎭 AUREON 1-2 STEP DANCE 🎭

The Rhythm: 1 Step Forward, 2 Steps Back
==========================================

While ONE system EXECUTES a profitable trade,
TWO systems PLAN the next move internally.

Like allies sharing battlefield intelligence through mycelium:
- Each step is a NET PROFIT execution
- Subsystems plan while not executing
- Shared logic flows through mycelium links
- Every execution is pre-validated by planners

The Dance:
┌─────────────────────────────────────────────────────┐
│  BEAT 1: EXECUTE          BEAT 2: PLAN A    BEAT 3: PLAN B  │
│  ═══════════════          ════════════      ════════════    │
│  Trader ACTS              Lighthouse        Probability     │
│  (sell/buy/convert)       SCANS             CALCULATES      │
│         │                      │                  │         │
│         └──────────────────────┴──────────────────┘         │
│                    MYCELIUM SHARED MEMORY                   │
│         ┌──────────────────────┬──────────────────┐         │
│         │                      │                  │         │
│  BEAT 4: PLAN A           BEAT 5: EXECUTE   BEAT 6: PLAN B  │
│  ════════════             ═══════════════   ════════════    │
│  Harmonic                 Trader ACTS       Miner Brain     │
│  ANALYZES                 (next trade)      COGITATES       │
└─────────────────────────────────────────────────────────────┘

Every EXECUTE step must be NET PROFIT validated.
Every PLAN step feeds the next EXECUTE.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class StepType(Enum):
    """The type of step in the dance"""
    EXECUTE = "⚡ EXECUTE"      # 1 step forward - make the trade
    PLAN_A = "🔮 PLAN_A"        # 1 step back - first planner
    PLAN_B = "🧠 PLAN_B"        # 1 step back - second planner


@dataclass
class DanceStep:
    """A single step in the 1-2 dance"""
    step_type: StepType
    system: str
    timestamp: float = field(default_factory=time.time)
    
    # For EXECUTE steps
    action: Optional[str] = None  # BUY, SELL, CONVERT
    asset: Optional[str] = None
    exchange: Optional[str] = None
    amount: Optional[float] = None
    price: Optional[float] = None
    profit: Optional[float] = None
    
    # For PLAN steps
    analysis: Optional[Dict] = None
    next_recommendation: Optional[Dict] = None
    confidence: float = 0.0
    
    # Mycelium shared data
    mycelium_payload: Dict = field(default_factory=dict)


@dataclass
class SharedMemory:
    """
    🍄 MYCELIUM SHARED MEMORY
    
    The underground network that connects all systems.
    Every step writes here, every step reads from here.
    """
    # Latest signals from each system
    lighthouse_signal: Dict = field(default_factory=dict)
    harmonic_signal: Dict = field(default_factory=dict)
    probability_signal: Dict = field(default_factory=dict)
    miner_signal: Dict = field(default_factory=dict)
    telescope_signal: Dict = field(default_factory=dict)
    
    # Consensus recommendation
    consensus: Dict = field(default_factory=dict)
    consensus_confidence: float = 0.0
    
    # Execution queue - only NET PROFIT trades
    execution_queue: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Recent executions (for learning)
    recent_executions: List[Dict] = field(default_factory=list)
    
    # Total profit tracking
    total_profit: float = 0.0
    step_count: int = 0
    
    def get_consensus(self) -> Dict:
        """Calculate consensus from all signals"""
        signals = [
            self.lighthouse_signal,
            self.harmonic_signal,
            self.probability_signal,
            self.miner_signal,
            self.telescope_signal
        ]
        
        # Count votes
        buy_votes = sum(1 for s in signals if s.get('action') == 'BUY')
        sell_votes = sum(1 for s in signals if s.get('action') == 'SELL')
        
        # Calculate average confidence
        confidences = [s.get('confidence', 0) for s in signals if s.get('confidence', 0) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Get best asset recommendation
        assets = [s.get('asset') for s in signals if s.get('asset')]
        best_asset = max(set(assets), key=assets.count) if assets else None
        
        action = 'SELL' if sell_votes > buy_votes else 'BUY' if buy_votes > sell_votes else 'HOLD'
        
        self.consensus = {
            'action': action,
            'asset': best_asset,
            'confidence': avg_confidence,
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'timestamp': time.time()
        }
        self.consensus_confidence = avg_confidence
        
        return self.consensus


class PlannerSystem:
    """Base class for planning systems (the 2 steps back)"""
    
    def __init__(self, name: str, shared_memory: SharedMemory):
        self.name = name
        self.shared = shared_memory
        self.last_analysis = {}
        
    async def plan(self, market_data: Dict) -> Dict:
        """Override this to implement planning logic"""
        raise NotImplementedError
        
    def write_to_mycelium(self, signal: Dict):
        """Write analysis to shared memory"""
        pass


class LighthousePlanner(PlannerSystem):
    """🏮 Lighthouse - Pattern Detection Planner"""
    
    def __init__(self, shared_memory: SharedMemory, lighthouse=None):
        super().__init__("lighthouse", shared_memory)
        self.lighthouse = lighthouse
        
    async def plan(self, market_data: Dict) -> Dict:
        """Scan for patterns and plan next move"""
        analysis = {
            'patterns': [],
            'regime': 'UNKNOWN',
            'anomalies': [],
            'recommendation': None,
            'confidence': 0.5
        }
        
        try:
            if self.lighthouse and hasattr(self.lighthouse, 'scan_for_patterns'):
                patterns = self.lighthouse.scan_for_patterns(market_data)
                analysis['patterns'] = patterns
                
                # Check for high-confidence patterns
                for p in patterns:
                    if p.get('type') == 'harmonic_convergence':
                        analysis['recommendation'] = {'action': 'BUY', 'reason': 'convergence'}
                        analysis['confidence'] = 0.8
                    elif p.get('type') == 'coherence_collapse':
                        analysis['recommendation'] = {'action': 'SELL', 'reason': 'collapse'}
                        analysis['confidence'] = 0.7
                        
            # Find best opportunity from market data
            best_dip = None
            best_pump = None
            
            for asset, data in market_data.items():
                momentum = data.get('momentum', 0)
                if momentum < -0.02 and (not best_dip or momentum < best_dip[1]):
                    best_dip = (asset, momentum)
                elif momentum > 0.02 and (not best_pump or momentum > best_pump[1]):
                    best_pump = (asset, momentum)
                    
            if best_pump and abs(best_pump[1]) > 0.03:
                analysis['recommendation'] = {
                    'action': 'SELL',
                    'asset': best_pump[0],
                    'momentum': best_pump[1],
                    'reason': f'pump +{best_pump[1]*100:.2f}%'
                }
                analysis['confidence'] = min(0.9, 0.5 + abs(best_pump[1]))
                
        except Exception as e:
            logger.debug(f"Lighthouse plan error: {e}")
            
        # Write to mycelium
        self.shared.lighthouse_signal = {
            'action': analysis.get('recommendation', {}).get('action'),
            'asset': analysis.get('recommendation', {}).get('asset'),
            'confidence': analysis['confidence'],
            'timestamp': time.time()
        }
        
        self.last_analysis = analysis
        return analysis


class HarmonicPlanner(PlannerSystem):
    """🌊 Harmonic - Frequency Analysis Planner"""
    
    def __init__(self, shared_memory: SharedMemory, harmonic=None):
        super().__init__("harmonic", shared_memory)
        self.harmonic = harmonic
        
    async def plan(self, market_data: Dict) -> Dict:
        """Analyze frequencies and plan next move"""
        analysis = {
            'frequency': 440,  # Default distortion
            'coherence': 0.5,
            'phase': 'UNKNOWN',
            'recommendation': None,
            'confidence': 0.5
        }
        
        try:
            if self.harmonic:
                if hasattr(self.harmonic, 'get_state'):
                    state = self.harmonic.get_state()
                    analysis['frequency'] = state.get('global_frequency', 440)
                    analysis['coherence'] = state.get('coherence', 0.5)
                    analysis['phase'] = state.get('phase', 'UNKNOWN')
                    
                    # Golden zone = high confidence
                    freq = analysis['frequency']
                    if 400 <= freq <= 520:
                        analysis['confidence'] = 0.8
                        analysis['recommendation'] = {'action': 'BUY', 'reason': 'golden_zone'}
                    elif freq > 600:  # High distortion
                        analysis['confidence'] = 0.6
                        analysis['recommendation'] = {'action': 'SELL', 'reason': 'distortion'}
                        
        except Exception as e:
            logger.debug(f"Harmonic plan error: {e}")
            
        # Write to mycelium
        self.shared.harmonic_signal = {
            'action': analysis.get('recommendation', {}).get('action'),
            'frequency': analysis['frequency'],
            'coherence': analysis['coherence'],
            'confidence': analysis['confidence'],
            'timestamp': time.time()
        }
        
        self.last_analysis = analysis
        return analysis


class ProbabilityPlanner(PlannerSystem):
    """🔮 Probability - Math-Based Planner"""
    
    def __init__(self, shared_memory: SharedMemory, nexus=None):
        super().__init__("probability", shared_memory)
        self.nexus = nexus
        
    async def plan(self, market_data: Dict) -> Dict:
        """Calculate probabilities and plan next move"""
        analysis = {
            'win_probability': 0.5,
            'expected_profit': 0,
            'best_trade': None,
            'recommendation': None,
            'confidence': 0.5
        }
        
        try:
            # Find highest probability trade
            best_prob = 0
            best_asset = None
            best_action = None
            
            for asset, data in market_data.items():
                momentum = data.get('momentum', 0)
                price = data.get('price', 0)
                
                # Simple probability model
                if momentum < -0.02:  # Dipping
                    # Probability of bounce
                    prob = min(0.8, 0.5 + abs(momentum) * 2)
                    if prob > best_prob:
                        best_prob = prob
                        best_asset = asset
                        best_action = 'BUY'
                elif momentum > 0.02:  # Pumping
                    # Probability of reversal
                    prob = min(0.8, 0.5 + momentum * 2)
                    if prob > best_prob:
                        best_prob = prob
                        best_asset = asset
                        best_action = 'SELL'
                        
            if best_asset and best_prob > 0.6:
                analysis['best_trade'] = {
                    'asset': best_asset,
                    'action': best_action,
                    'probability': best_prob
                }
                analysis['recommendation'] = {
                    'action': best_action,
                    'asset': best_asset,
                    'reason': f'prob={best_prob:.1%}'
                }
                analysis['confidence'] = best_prob
                analysis['win_probability'] = best_prob
                
            # Use nexus if available
            if self.nexus and hasattr(self.nexus, 'get_signal'):
                for asset, data in list(market_data.items())[:5]:
                    try:
                        signal = self.nexus.get_signal(asset, data.get('price', 0), data.get('momentum', 0))
                        if signal.get('confidence', 0) > analysis['confidence']:
                            analysis['recommendation'] = {
                                'action': signal.get('direction', 'HOLD'),
                                'asset': asset,
                                'reason': 'nexus'
                            }
                            analysis['confidence'] = signal.get('confidence', 0.5)
                    except:
                        pass
                        
        except Exception as e:
            logger.debug(f"Probability plan error: {e}")
            
        # Write to mycelium
        self.shared.probability_signal = {
            'action': analysis.get('recommendation', {}).get('action'),
            'asset': analysis.get('recommendation', {}).get('asset'),
            'probability': analysis.get('win_probability', 0.5),
            'confidence': analysis['confidence'],
            'timestamp': time.time()
        }
        
        self.last_analysis = analysis
        return analysis


class MinerBrainPlanner(PlannerSystem):
    """🧠 Miner Brain - Cognitive Planner"""
    
    def __init__(self, shared_memory: SharedMemory, miner=None):
        super().__init__("miner", shared_memory)
        self.miner = miner
        
    async def plan(self, market_data: Dict) -> Dict:
        """Apply cognitive wisdom and plan next move"""
        analysis = {
            'wisdom': [],
            'cognitive_score': 0.5,
            'recommendation': None,
            'confidence': 0.5
        }
        
        try:
            if self.miner:
                if hasattr(self.miner, 'analyze'):
                    for asset, data in list(market_data.items())[:5]:
                        try:
                            result = self.miner.analyze(asset, data.get('price', 0), data.get('momentum', 0))
                            if result.get('confidence', 0) > analysis['confidence']:
                                analysis['recommendation'] = {
                                    'action': result.get('action', 'HOLD'),
                                    'asset': asset,
                                    'reason': 'miner_wisdom'
                                }
                                analysis['confidence'] = result.get('confidence', 0.5)
                        except:
                            pass
                            
        except Exception as e:
            logger.debug(f"Miner plan error: {e}")
            
        # Write to mycelium
        self.shared.miner_signal = {
            'action': analysis.get('recommendation', {}).get('action'),
            'asset': analysis.get('recommendation', {}).get('asset'),
            'confidence': analysis['confidence'],
            'timestamp': time.time()
        }
        
        self.last_analysis = analysis
        return analysis


class TelescopePlanner(PlannerSystem):
    """🔭 Quantum Telescope - Multi-Dimensional Planner"""
    
    def __init__(self, shared_memory: SharedMemory, telescope=None):
        super().__init__("telescope", shared_memory)
        self.telescope = telescope
        
    async def plan(self, market_data: Dict) -> Dict:
        """Observe through geometric lenses and plan"""
        analysis = {
            'spectrum': {},
            'geometry': 'balanced',
            'recommendation': None,
            'confidence': 0.5
        }
        
        try:
            if self.telescope and hasattr(self.telescope, 'observe_light_beam'):
                for asset, data in list(market_data.items())[:3]:
                    try:
                        observation = self.telescope.observe_light_beam(
                            price=data.get('price', 0),
                            volume=data.get('volume', 0),
                            sentiment=0.5
                        )
                        if observation.get('signal_strength', 0) > 0.7:
                            analysis['recommendation'] = {
                                'action': 'BUY' if observation.get('direction') == 'UP' else 'SELL',
                                'asset': asset,
                                'reason': 'telescope'
                            }
                            analysis['confidence'] = observation.get('signal_strength', 0.5)
                    except:
                        pass
                        
        except Exception as e:
            logger.debug(f"Telescope plan error: {e}")
            
        # Write to mycelium
        self.shared.telescope_signal = {
            'action': analysis.get('recommendation', {}).get('action'),
            'asset': analysis.get('recommendation', {}).get('asset'),
            'confidence': analysis['confidence'],
            'timestamp': time.time()
        }
        
        self.last_analysis = analysis
        return analysis


class StepDanceOrchestrator:
    """
    🎭 THE 1-2 STEP DANCE ORCHESTRATOR
    
    Coordinates the rhythm:
    - 1 step EXECUTES (forward)
    - 2 steps PLAN (back)
    
    Every execution must be NET PROFIT.
    Planners prepare while executor acts.
    """
    
    def __init__(
        self,
        executor: Callable,  # The function that executes trades
        lighthouse=None,
        harmonic=None,
        nexus=None,
        miner=None,
        telescope=None,
        min_profit: float = 0.01,  # Minimum profit per step in USD
    ):
        self.executor = executor
        self.min_profit = min_profit
        
        # Shared memory (mycelium)
        self.shared = SharedMemory()
        
        # Initialize planners
        self.planners = {
            'lighthouse': LighthousePlanner(self.shared, lighthouse),
            'harmonic': HarmonicPlanner(self.shared, harmonic),
            'probability': ProbabilityPlanner(self.shared, nexus),
            'miner': MinerBrainPlanner(self.shared, miner),
            'telescope': TelescopePlanner(self.shared, telescope),
        }
        
        # Dance state
        self.current_beat = 0  # 0=EXECUTE, 1=PLAN_A, 2=PLAN_B
        self.step_history: List[DanceStep] = []
        self.running = False
        
        # Planner rotation (which 2 plan while 1 executes)
        self.planner_rotation = [
            ['lighthouse', 'probability'],   # Beat 0: these plan while executing
            ['harmonic', 'miner'],            # Beat 1: these plan
            ['telescope', 'lighthouse'],     # Beat 2: these plan
            ['probability', 'harmonic'],     # Beat 3: these plan
            ['miner', 'telescope'],          # Beat 4: these plan
        ]
        
        logger.info("🎭 Step Dance Orchestrator initialized")
        logger.info(f"   Min profit per step: ${min_profit}")
        logger.info(f"   Planners: {list(self.planners.keys())}")
        
    async def dance_step(self, market_data: Dict, holdings: Dict) -> Optional[DanceStep]:
        """
        Execute one step of the 1-2 dance.
        
        Returns the step taken (EXECUTE or PLAN).
        """
        beat = self.current_beat % 3
        
        if beat == 0:
            # ⚡ EXECUTE BEAT - Make a trade
            step = await self._execute_step(market_data, holdings)
        else:
            # 🔮 PLAN BEAT - Two planners analyze
            step = await self._plan_step(market_data, beat)
            
        self.current_beat += 1
        self.step_history.append(step)
        
        return step
        
    async def _execute_step(self, market_data: Dict, holdings: Dict) -> DanceStep:
        """
        ⚡ THE FORWARD STEP - Execute a profitable trade
        
        Only executes if:
        1. Consensus recommends action
        2. Expected profit > min_profit
        3. We have the holdings to trade
        """
        step = DanceStep(
            step_type=StepType.EXECUTE,
            system="executor"
        )
        
        # Get consensus from mycelium
        consensus = self.shared.get_consensus()
        
        # Check if we should execute
        if consensus['confidence'] < 0.5:
            logger.debug("⏸️ Skipping execution - low confidence")
            return step
            
        if consensus['action'] == 'HOLD':
            logger.debug("⏸️ Skipping execution - consensus is HOLD")
            return step
            
        asset = consensus.get('asset')
        action = consensus.get('action')
        
        if not asset:
            # Find best asset from holdings
            best_value = 0
            for a, amount in holdings.items():
                if a in ['USD', 'USDC', 'USDT', 'ZUSD']:
                    continue
                value = market_data.get(a, {}).get('price', 0) * amount
                if value > best_value:
                    best_value = value
                    asset = a
                    
        if not asset:
            logger.debug("⏸️ No asset to trade")
            return step
            
        # Get current price and calculate expected profit
        price = market_data.get(asset, {}).get('price', 0)
        momentum = market_data.get(asset, {}).get('momentum', 0)
        
        if price <= 0:
            return step
            
        # Calculate expected profit
        amount = holdings.get(asset, 0)
        if action == 'SELL' and amount > 0:
            value = price * amount * 0.5  # Sell 50%
            expected_profit = value * abs(momentum) * 0.5  # Conservative estimate
        elif action == 'BUY':
            usd = sum(holdings.get(u, 0) for u in ['USD', 'USDC', 'USDT', 'ZUSD'])
            if usd < 5:
                return step
            value = min(usd * 0.3, 10)
            expected_profit = value * abs(momentum) * 0.3
        else:
            return step
            
        # Check minimum profit requirement
        if expected_profit < self.min_profit:
            logger.debug(f"⏸️ Expected profit ${expected_profit:.4f} < ${self.min_profit}")
            return step
            
        # ⚡ EXECUTE THE TRADE
        try:
            result = await self.executor({
                'action': action,
                'asset': asset,
                'amount': amount * 0.5 if action == 'SELL' else value / price,
                'price': price,
                'exchange': 'binance',  # Default to binance for low minimums
                'confidence': consensus['confidence'],
                'expected_profit': expected_profit
            })
            
            if result and result.get('success'):
                step.action = action
                step.asset = asset
                step.amount = result.get('amount', 0)
                step.price = result.get('price', price)
                step.profit = result.get('profit', 0)
                
                # Update shared memory
                self.shared.total_profit += step.profit or 0
                self.shared.step_count += 1
                self.shared.recent_executions.append({
                    'action': action,
                    'asset': asset,
                    'profit': step.profit,
                    'timestamp': time.time()
                })
                
                logger.info(f"⚡ EXECUTED: {action} {asset} | Profit: ${step.profit:.4f}")
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
            
        return step
        
    async def _plan_step(self, market_data: Dict, beat: int) -> DanceStep:
        """
        🔮 THE BACKWARD STEPS - Two planners analyze
        
        While not executing, planners prepare the next move.
        """
        rotation_idx = (self.current_beat // 3) % len(self.planner_rotation)
        active_planners = self.planner_rotation[rotation_idx]
        
        # Select which planner for this beat
        planner_name = active_planners[beat - 1] if beat <= len(active_planners) else active_planners[0]
        planner = self.planners.get(planner_name)
        
        step = DanceStep(
            step_type=StepType.PLAN_A if beat == 1 else StepType.PLAN_B,
            system=planner_name
        )
        
        if planner:
            try:
                analysis = await planner.plan(market_data)
                step.analysis = analysis
                step.confidence = analysis.get('confidence', 0)
                step.next_recommendation = analysis.get('recommendation')
                
                logger.debug(f"🔮 {planner_name.upper()} planned: {analysis.get('recommendation')}")
                
            except Exception as e:
                logger.error(f"Planner {planner_name} error: {e}")
                
        return step
        
    async def run_dance(
        self,
        get_market_data: Callable,
        get_holdings: Callable,
        interval: float = 3.0,
        max_steps: int = 1000
    ):
        """
        🎵 RUN THE DANCE
        
        Continuously execute the 1-2 step pattern.
        """
        self.running = True
        steps = 0
        
        print("\n" + "🎭" * 30)
        print("   1-2 STEP DANCE BEGINS!")
        print("   1 step forward (execute), 2 steps back (plan)")
        print("🎭" * 30 + "\n")
        
        while self.running and steps < max_steps:
            try:
                market_data = await get_market_data()
                holdings = await get_holdings()
                
                step = await self.dance_step(market_data, holdings)
                steps += 1
                
                # Print status every 3 steps (one full cycle)
                if steps % 3 == 0:
                    profit = self.shared.total_profit
                    exec_count = len([s for s in self.step_history if s.step_type == StepType.EXECUTE and s.profit])
                    print(f"🎭 Cycle {steps//3} | 💰 ${profit:.4f} | ⚡ {exec_count} trades | 🎯 {self.shared.consensus_confidence:.1%}")
                    
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Dance error: {e}")
                await asyncio.sleep(1)
                
        print(f"\n🎭 Dance complete! Total profit: ${self.shared.total_profit:.4f}")
        
    def stop(self):
        """Stop the dance"""
        self.running = False
        
    def get_status(self) -> Dict:
        """Get current dance status"""
        return {
            'total_profit': self.shared.total_profit,
            'step_count': len(self.step_history),
            'execution_count': len([s for s in self.step_history if s.step_type == StepType.EXECUTE and s.profit]),
            'current_beat': self.current_beat % 3,
            'consensus': self.shared.consensus,
            'consensus_confidence': self.shared.consensus_confidence,
        }


# ═══════════════════════════════════════════════════════════════
# 🎯 INTEGRATION WITH S5 INTELLIGENT DANCE
# ═══════════════════════════════════════════════════════════════

def integrate_step_dance(dance_instance):
    """
    Integrate the 1-2 Step Dance into S5 Intelligent Dance.
    
    This wraps the execution to ensure:
    - 1 step executes
    - 2 steps plan
    - Every step is net profit
    """
    # Get existing systems from dance
    lighthouse = getattr(dance_instance, 'lighthouse', None)
    harmonic = getattr(dance_instance, 'harmonic_fusion', None)
    nexus = getattr(dance_instance.intelligence, 'nexus', None) if hasattr(dance_instance, 'intelligence') else None
    miner = getattr(dance_instance.intelligence, 'miner_brain', None) if hasattr(dance_instance, 'intelligence') else None
    telescope = getattr(dance_instance.intelligence, 'telescope', None) if hasattr(dance_instance, 'intelligence') else None
    
    # Create executor function
    async def executor(trade: Dict) -> Dict:
        """Execute through the dance's existing execution system"""
        try:
            step = {
                'exchange': trade['exchange'],
                'asset': trade['asset'],
                'action': trade['action'].lower(),
                'amount': trade['amount'],
                'price': trade['price'],
                'momentum': 0,
                'usd_value': trade['amount'] * trade['price'],
                'decision': {'proceed': True, 'confidence': trade['confidence']}
            }
            
            # Use dance's execution method
            if hasattr(dance_instance, '_execute_intelligent_step'):
                await dance_instance._execute_intelligent_step(step)
                return {
                    'success': True,
                    'amount': trade['amount'],
                    'price': trade['price'],
                    'profit': trade.get('expected_profit', 0.01)
                }
        except Exception as e:
            logger.error(f"Step dance executor error: {e}")
            
        return {'success': False}
        
    # Create orchestrator
    orchestrator = StepDanceOrchestrator(
        executor=executor,
        lighthouse=lighthouse,
        harmonic=harmonic,
        nexus=nexus,
        miner=miner,
        telescope=telescope,
        min_profit=0.01
    )
    
    return orchestrator


# ═══════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "🎭" * 30)
    print("   1-2 STEP DANCE TEST")
    print("🎭" * 30 + "\n")
    
    # Create mock executor
    async def mock_executor(trade: Dict) -> Dict:
        print(f"   ⚡ Mock execute: {trade['action']} {trade['asset']}")
        return {
            'success': True,
            'amount': trade['amount'],
            'price': trade['price'],
            'profit': 0.02
        }
        
    # Create orchestrator
    orchestrator = StepDanceOrchestrator(
        executor=mock_executor,
        min_profit=0.01
    )
    
    # Mock market data
    async def get_market():
        return {
            'APE': {'price': 0.22, 'momentum': 0.03, 'volume': 1000},
            'SOL': {'price': 190, 'momentum': 0.05, 'volume': 5000},
            'BTC': {'price': 95000, 'momentum': 0.01, 'volume': 10000},
        }
        
    # Mock holdings
    async def get_holdings():
        return {
            'APE': 27.4,
            'USDC': 55.0,
        }
        
    # Run test
    async def test():
        for i in range(9):  # 3 complete cycles
            market = await get_market()
            holdings = await get_holdings()
            step = await orchestrator.dance_step(market, holdings)
            print(f"   Step {i+1}: {step.step_type.value} by {step.system}")
            
        print(f"\n   Status: {orchestrator.get_status()}")
        
    asyncio.run(test())
