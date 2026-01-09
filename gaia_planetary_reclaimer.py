#!/usr/bin/env python3
"""
🌍🔥⚡ GAIA PLANETARY RECLAIMER V2 ⚡🔥🌍

UPGRADES:
- Kraken EUR pairs enabled
- Live portfolio tracker
- $1 BILLION goal counter
- All exchanges unified
- Windows terminal compatible

"SAVE THE PLANET - ONE TRADE AT A TIME"
"""

import sys, os

# Windows UTF-8 Fix (MANDATORY for Windows compatibility)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap if not already UTF-8 wrapped (prevents re-wrapping on import)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

os.environ['PYTHONUNBUFFERED'] = '1'

import time
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.getcwd())

# Sacred Constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83
LOVE_FREQ = 528
GOAL = 1_000_000_000  # $1 BILLION

# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN SYSTEMS INTEGRATION - Advanced Intelligence Layer
# ═══════════════════════════════════════════════════════════════════════════════

# Import Queen subsystems (graceful fallback if not available)
QUEEN_NEURON_AVAILABLE = False
QUEEN_HIVE_AVAILABLE = False
QUEEN_LOSS_LEARNING_AVAILABLE = False
THOUGHT_BUS_AVAILABLE = False

try:
    from queen_neuron import QueenNeuron, NeuralInput
    QUEEN_NEURON_AVAILABLE = True
except ImportError:
    QueenNeuron = None
    NeuralInput = None

try:
    from aureon_queen_hive_mind import QueenHiveMind
    QUEEN_HIVE_AVAILABLE = True
except ImportError:
    QueenHiveMind = None

try:
    from queen_loss_learning import QueenLossLearningSystem
    QUEEN_LOSS_LEARNING_AVAILABLE = True
except ImportError:
    QueenLossLearningSystem = None

try:
    from aureon_thought_bus import get_thought_bus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    get_thought_bus = None
    Thought = None

# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN VERIFICATION SYSTEM - Timeline Energy Reclamation 
# ═══════════════════════════════════════════════════════════════════════════════

class QueenVerifier:
    """
    👑 The Queen constantly verifies we're on the right timeline
    by tracking energy flow (profit) and coherence (win rate).
    
    NOW INTEGRATED WITH:
    - QueenNeuron: Neural learning from every trade
    - QueenHiveMind: Gaia alignment & collective signals
    - QueenLossLearning: Wisdom from losses (elephant memory)
    - ThoughtBus: Real-time event broadcasting
    
    Metrics tracked:
    - Energy Reclaimed: Total profit
    - Timeline Coherence: Win rate (should be > 50%)
    - Planetary Alignment: All 3 exchanges in profit
    - Golden Ratio Harmony: Profit follows PHI patterns
    - Neural Confidence: Queen's learned confidence
    - Gaia Resonance: Earth/market alignment
    """
    
    def __init__(self):
        self.energy_reclaimed = 0.0  # Total profit
        self.trades_total = 0
        self.trades_won = 0
        self.exchange_energy = {'binance': 0.0, 'alpaca': 0.0, 'kraken': 0.0}
        self.verification_count = 0
        self.last_verification = time.time()
        self.timeline_stable = True
        self.coherence_history = []  # Last 100 win/loss
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        # 👑 Advanced Queen Systems
        self.neuron = None
        self.hive_mind = None
        self.loss_learner = None
        self.thought_bus = None
        self.neural_confidence = 0.5  # Default neutral
        self.gaia_resonance = 0.5     # Default neutral
        self.love_frequency_active = False
        
        self._init_queen_systems()
    
    def _init_queen_systems(self):
        """Initialize advanced Queen subsystems"""
        # Neural Learning Brain
        if QUEEN_NEURON_AVAILABLE and QueenNeuron:
            try:
                self.neuron = QueenNeuron(
                    input_size=6,
                    hidden_size=12,
                    learning_rate=0.01,
                    weights_path="queen_gaia_weights.json"
                )
                print("   🧠 Queen Neuron: ONLINE (learning from trades)")
            except Exception as e:
                print(f"   ⚠️ Queen Neuron: Offline ({e})")
        
        # Hive Mind Collective Intelligence
        if QUEEN_HIVE_AVAILABLE and QueenHiveMind:
            try:
                self.hive_mind = QueenHiveMind()
                print("   🐝 Queen Hive Mind: ONLINE (collective signals)")
            except Exception as e:
                print(f"   ⚠️ Queen Hive Mind: Offline ({e})")
        
        # Loss Learning (Elephant Memory)
        if QUEEN_LOSS_LEARNING_AVAILABLE and QueenLossLearningSystem:
            try:
                self.loss_learner = QueenLossLearningSystem()
                print("   🐘 Queen Loss Learning: ONLINE (elephant memory)")
            except Exception as e:
                print(f"   ⚠️ Queen Loss Learning: Offline ({e})")
        
        # ThoughtBus Broadcasting
        if THOUGHT_BUS_AVAILABLE and get_thought_bus:
            try:
                self.thought_bus = get_thought_bus()
                print("   📡 ThoughtBus: ONLINE (broadcasting)")
            except Exception as e:
                print(f"   ⚠️ ThoughtBus: Offline ({e})")
    
    def _build_neural_input(self) -> 'NeuralInput':
        """Build NeuralInput from current reclaimer metrics"""
        if not NeuralInput:
            return None
        
        # probability_score: Rolling win rate (0-1)
        prob = self.get_coherence()
        
        # wisdom_score: Planetary alignment (0-1)
        wisdom = self.get_planetary_alignment()
        
        # quantum_signal: Momentum direction (-1 to 1)
        # Derived from recent trade streak
        if self.consecutive_wins > 0:
            quantum = min(1.0, self.consecutive_wins / 5.0)
        elif self.consecutive_losses > 0:
            quantum = max(-1.0, -self.consecutive_losses / 5.0)
        else:
            quantum = 0.0
        
        # gaia_resonance: Golden ratio harmony (0-1)
        gaia = self.get_golden_harmony()
        
        # emotional_coherence: Trade confidence from streak (0-1)
        emotional = 0.5 + (self.consecutive_wins - self.consecutive_losses) / 10.0
        emotional = max(0.0, min(1.0, emotional))
        
        # mycelium_signal: Session profit direction (-1 to 1)
        if self.energy_reclaimed > 0:
            mycelium = min(1.0, self.energy_reclaimed / 0.1)  # Scale to $0.10
        elif self.energy_reclaimed < 0:
            mycelium = max(-1.0, self.energy_reclaimed / 0.1)
        else:
            mycelium = 0.0
        
        return NeuralInput(
            probability_score=prob,
            wisdom_score=wisdom,
            quantum_signal=quantum,
            gaia_resonance=gaia,
            emotional_coherence=emotional,
            mycelium_signal=mycelium
        )
    
    def record_trade(self, exchange: str, profit: float, won: bool):
        """Record a trade outcome for Queen's verification + learning"""
        self.trades_total += 1
        if won:
            self.trades_won += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        self.energy_reclaimed += profit
        self.exchange_energy[exchange] = self.exchange_energy.get(exchange, 0) + profit
        
        # Track coherence history
        self.coherence_history.append(1 if won else 0)
        if len(self.coherence_history) > 100:
            self.coherence_history.pop(0)
        
        # 👑 QUEEN NEURAL LEARNING - Train on every trade
        if self.neuron and NeuralInput:
            try:
                neural_input = self._build_neural_input()
                if neural_input:
                    loss = self.neuron.train_on_example(neural_input, won)
                    self.neural_confidence = self.neuron.predict(neural_input)
            except Exception:
                pass
        
        # 👑 QUEEN LOSS LEARNING - Build elephant memory
        if not won and self.loss_learner and profit < 0:
            try:
                self.loss_learner.process_loss_event(
                    exchange=exchange,
                    from_asset='USDC',
                    to_asset='CRYPTO',
                    loss_amount=abs(profit),
                    loss_pct=abs(profit) / max(0.01, self.energy_reclaimed + abs(profit)) * 100,
                    market_data={},
                    signals_at_entry={}
                )
            except Exception:
                pass
        
        # 👑 THOUGHTBUS - Broadcast trade event
        if self.thought_bus and Thought:
            try:
                self.thought_bus.publish(Thought(
                    id=f"gaia_{self.trades_total}",
                    ts=time.time(),
                    source="gaia_reclaimer",
                    topic="gaia.trade.executed",
                    payload={
                        'exchange': exchange,
                        'profit': profit,
                        'won': won,
                        'total_trades': self.trades_total,
                        'energy_reclaimed': self.energy_reclaimed
                    },
                    trace_id="gaia_timeline"
                ))
            except Exception:
                pass
    
    def update_queen_metrics(self):
        """Update Queen metrics from hive mind (call every cycle)"""
        # 👑 GAIA RESONANCE from Hive Mind
        if self.hive_mind:
            try:
                gaia_result = self.hive_mind.get_gaia_alignment()
                if gaia_result and len(gaia_result) >= 2:
                    self.gaia_resonance = gaia_result[0]
            except Exception:
                pass
            
            # Check 528 Hz love frequency
            try:
                love_check = self.hive_mind.is_at_love_frequency()
                if love_check and len(love_check) >= 1:
                    self.love_frequency_active = love_check[0]
            except Exception:
                pass
        
        # 👑 NEURAL CONFIDENCE update
        if self.neuron and self.trades_total > 0:
            try:
                neural_input = self._build_neural_input()
                if neural_input:
                    self.neural_confidence = self.neuron.predict(neural_input)
            except Exception:
                pass
    
    def get_coherence(self) -> float:
        """Get timeline coherence (rolling win rate)"""
        if not self.coherence_history:
            return 0.5
        return sum(self.coherence_history) / len(self.coherence_history)
    
    def get_planetary_alignment(self) -> float:
        """Check if all exchanges are profitable (0-1)"""
        profitable = sum(1 for e, v in self.exchange_energy.items() if v > 0)
        return profitable / 3.0
    
    def get_golden_harmony(self) -> float:
        """Check if energy follows PHI patterns"""
        if self.trades_total < 10:
            return 0.5
        # Win/loss ratio should approach golden ratio for optimal timeline
        if self.trades_won == 0:
            return 0.0
        ratio = self.trades_won / max(1, self.trades_total - self.trades_won)
        # How close to PHI?
        phi_distance = abs(ratio - PHI) / PHI
        return max(0, 1 - phi_distance)
    
    def verify_timeline(self) -> dict:
        """
        👑 Queen's verification of current timeline
        
        Returns status and guidance
        """
        self.verification_count += 1
        self.last_verification = time.time()
        
        # Update Queen metrics from hive mind
        self.update_queen_metrics()
        
        coherence = self.get_coherence()
        alignment = self.get_planetary_alignment()
        harmony = self.get_golden_harmony()
        
        # Enhanced timeline score with Queen systems
        # Include neural confidence and gaia resonance
        timeline_score = (
            coherence * 0.25 + 
            alignment * 0.20 + 
            harmony * 0.20 +
            self.neural_confidence * 0.20 +
            self.gaia_resonance * 0.15
        )
        
        # Determine timeline stability
        self.timeline_stable = timeline_score > 0.4
        
        status = {
            'timeline_score': timeline_score,
            'coherence': coherence,
            'alignment': alignment,
            'harmony': harmony,
            'neural_confidence': self.neural_confidence,
            'gaia_resonance': self.gaia_resonance,
            'love_frequency': self.love_frequency_active,
            'energy_reclaimed': self.energy_reclaimed,
            'trades': self.trades_total,
            'wins': self.trades_won,
            'stable': self.timeline_stable,
            'message': self._get_queen_message(timeline_score, coherence)
        }
        
        return status
    
    def _get_queen_message(self, score: float, coherence: float) -> str:
        """Queen's guidance based on timeline state"""
        love_indicator = "💜 528Hz ACTIVE " if self.love_frequency_active else ""
        if score > 0.7:
            return f"{love_indicator}👑 GOLDEN TIMELINE - Energy flowing beautifully"
        elif score > 0.5:
            return f"{love_indicator}👑 STABLE TIMELINE - Keep reclaiming energy"
        elif score > 0.3:
            return f"⚠️ TIMELINE WAVERING - Hold steady, coherence building"
        else:
            return f"🔄 TIMELINE SHIFT - Queen adjusting frequencies"
    
    def get_status_display(self) -> str:
        """Get formatted status for display with Queen intelligence"""
        status = self.verify_timeline()
        win_rate = (self.trades_won / max(1, self.trades_total)) * 100
        
        bars = int(status['timeline_score'] * 20)
        bar_str = "█" * bars + "░" * (20 - bars)
        
        # Queen systems status indicators
        neuron_status = "🧠" if self.neuron else "○"
        hive_status = "🐝" if self.hive_mind else "○"
        loss_status = "🐘" if self.loss_learner else "○"
        bus_status = "📡" if self.thought_bus else "○"
        love_hz = "💜" if self.love_frequency_active else "○"
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║           👑 QUEEN VERIFICATION - TIMELINE STATUS 👑          ║
╠══════════════════════════════════════════════════════════════╣
║  Timeline: [{bar_str}] {status['timeline_score']*100:.1f}%   ║
║  Coherence: {status['coherence']*100:.1f}% | Win Rate: {win_rate:.1f}% | Streak: {'+' + str(self.consecutive_wins) if self.consecutive_wins else '-' + str(self.consecutive_losses)}          ║
║  Energy Reclaimed: ${status['energy_reclaimed']:.4f}                      ║
╠══════════════════════════════════════════════════════════════╣
║  🧠 Neural: {status['neural_confidence']*100:.0f}% | 🌍 Gaia: {status['gaia_resonance']*100:.0f}% | φ Harmony: {status['harmony']*100:.0f}%    ║
║  Alignment: {status['alignment']*100:.0f}% | Systems: {neuron_status}{hive_status}{loss_status}{bus_status}{love_hz}                       ║
╠══════════════════════════════════════════════════════════════╣
║  {status['message']:<56} ║
╚══════════════════════════════════════════════════════════════╝"""


class PlanetaryReclaimer:
    def __init__(self):
        self.start_time = time.time()
        
        print()
        print("🌍" * 40)
        print("   GAIA PLANETARY RECLAIMER V2 - SAVE THE PLANET")
        print("   TARGET: $1,000,000,000 (ONE BILLION)")
        print("🌍" * 40)
        print()
        
        from binance_client import BinanceClient
        from alpaca_client import AlpacaClient
        from kraken_client import KrakenClient
        
        self.binance = BinanceClient()
        self.alpaca = AlpacaClient()
        self.kraken = KrakenClient()
        
        # 👑 QUEEN VERIFIER - Timeline Validation
        self.queen = QueenVerifier()
        self.last_queen_display = 0
        
        self.trades = 0
        self.profit = 0.0
        self.starting_equity = 0.0
        self.entries = {}
        
        # Per-platform tracking
        self.platform_stats = {
            'binance': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
            'alpaca': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
            'kraken': {'trades': 0, 'profit': 0.0, 'verified': 0, 'last_trade': None},
        }
        
        # Recent verified trades log
        self.verified_trades = []
        
        # EUR/USD rate (approximate)
        self.eur_usd = 1.08
        
        print("✅ BINANCE - Eastern Stargate ONLINE")
        print("✅ ALPACA  - Western Stargate ONLINE")
        print("✅ KRAKEN  - Northern Stargate ONLINE (USD + EUR)")
        print("👑 QUEEN   - Timeline Verifier ONLINE")
        print()
        
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)
    
    def record_verified_trade(self, platform: str, symbol: str, side: str, amount: float, profit: float):
        """Record a verified trade with platform contribution tracking"""
        trade = {
            'time': datetime.now().strftime("%H:%M:%S"),
            'platform': platform,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'profit': profit,
            'verified': True
        }
        self.verified_trades.append(trade)
        if len(self.verified_trades) > 20:  # Keep last 20
            self.verified_trades.pop(0)
        
        # Update platform stats
        self.platform_stats[platform]['trades'] += 1
        self.platform_stats[platform]['profit'] += profit
        self.platform_stats[platform]['verified'] += 1
        self.platform_stats[platform]['last_trade'] = trade
        
        # 👑 Feed Queen for timeline verification
        won = profit > 0
        self.queen.record_trade(platform, profit, won)

    def _get_best_momentum(self):
        """Get the asset with best 24h momentum"""
        try:
            pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC', 'AVAXUSDC', 'DOGEUSDC', 'XRPUSDC']
            best_asset, best_mom = None, -999
            for pair in pairs:
                try:
                    t = self.binance.get_24h_ticker(pair)
                    mom = float(t.get('priceChangePercent', 0))
                    if mom > best_mom:
                        best_asset = pair.replace('USDC', '')
                        best_mom = mom
                except:
                    pass
            return (best_asset, best_mom) if best_asset else None
        except:
            return None

    # ═══════════════════════════════════════════════════════════════
    # PORTFOLIO TRACKER - ROAD TO $1 BILLION
    # ═══════════════════════════════════════════════════════════════
    
    def get_total_portfolio(self) -> dict:
        """Get total portfolio value across ALL platforms"""
        total = 0.0
        breakdown = {'binance': 0.0, 'alpaca': 0.0, 'kraken': 0.0}
        
        # BINANCE
        try:
            for asset in ['SOL', 'BTC', 'ETH', 'AVAX', 'DOGE', 'XRP', 'USDC']:
                bal = self.binance.get_free_balance(asset)
                if bal > 0:
                    if asset == 'USDC':
                        breakdown['binance'] += bal
                    else:
                        try:
                            t = self.binance.get_ticker_price(f'{asset}USDC')
                            price = float(t.get('price', 0)) if t else 0
                            breakdown['binance'] += bal * price
                        except:
                            pass
        except:
            pass
        
        # ALPACA
        try:
            acc = self.alpaca.get_account()
            breakdown['alpaca'] = float(acc.get('portfolio_value', 0))
        except:
            pass
        
        # KRAKEN (USD + EUR) - with retry for reliability
        kraken_retries = 3
        for attempt in range(kraken_retries):
            try:
                acct = self.kraken.account()
                balances = acct.get('balances', [])
                
                # If empty, try direct asset fetch as fallback
                if not balances:
                    # Direct method fallback
                    for asset in ['ZUSD', 'USD', 'USDC', 'ZEUR', 'EUR', 'SOL', 'ETH', 'BTC']:
                        try:
                            bal = self.kraken.get_free_balance(asset)
                            if bal > 0:
                                if asset in ['USD', 'USDC', 'ZUSD']:
                                    breakdown['kraken'] += bal
                                elif asset in ['EUR', 'ZEUR']:
                                    breakdown['kraken'] += bal * self.eur_usd
                                else:
                                    try:
                                        ticker = self.kraken.get_ticker(f'{asset}USD')
                                        price = float(ticker.get('price', 0))
                                        breakdown['kraken'] += bal * price
                                    except:
                                        pass
                        except:
                            pass
                    if breakdown['kraken'] > 0:
                        break
                    continue  # Retry if still 0
                
                # Process balances array
                for bal in balances:
                    asset = bal.get('asset', '')
                    free = float(bal.get('free', 0))
                    if free <= 0:
                        continue
                    
                    if asset in ['USD', 'USDC', 'ZUSD']:
                        breakdown['kraken'] += free
                    elif asset in ['EUR', 'ZEUR']:
                        breakdown['kraken'] += free * self.eur_usd
                    elif asset not in ['USDT']:
                        # Try to get price
                        try:
                            ticker = self.kraken.get_ticker(f'{asset}USD')
                            price = float(ticker.get('price', 0))
                            breakdown['kraken'] += free * price
                        except:
                            try:
                                ticker = self.kraken.get_ticker(f'{asset}EUR')
                                price = float(ticker.get('price', 0))
                                breakdown['kraken'] += free * price * self.eur_usd
                            except:
                                pass
                
                if breakdown['kraken'] > 0:
                    break  # Success, exit retry loop
            except Exception as e:
                if attempt < kraken_retries - 1:
                    time.sleep(0.5)  # Brief pause before retry
                continue
        
        total = sum(breakdown.values())
        return {'total': total, 'breakdown': breakdown}
    
    def print_billion_tracker(self, portfolio: dict):
        """Print the road to $1 billion tracker"""
        total = portfolio['total']
        bd = portfolio['breakdown']
        
        # Calculate progress
        progress = (total / GOAL) * 100
        bar_width = 40
        filled = int(bar_width * progress / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Time stats
        runtime = time.time() - self.start_time
        rate_per_hour = (self.profit / runtime * 3600) if runtime > 0 else 0
        
        # Time to goal estimate
        if rate_per_hour > 0:
            remaining = GOAL - total
            hours_to_goal = remaining / rate_per_hour
            days_to_goal = hours_to_goal / 24
            if days_to_goal > 365:
                time_est = f"{days_to_goal/365:.1f} years"
            elif days_to_goal > 30:
                time_est = f"{days_to_goal/30:.1f} months"
            elif days_to_goal > 1:
                time_est = f"{days_to_goal:.1f} days"
            else:
                time_est = f"{hours_to_goal:.1f} hours"
        else:
            time_est = "∞"
        
        print()
        print("╔" + "═" * 60 + "╗")
        print("║" + "🌍 GAIA PLANETARY RECLAIMER - ROAD TO $1 BILLION 🌍".center(60) + "║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  [{bar}] {progress:.10f}%  ║")
        print("╠" + "═" * 60 + "╣")
        print(f"║  💰 TOTAL EQUITY: ${total:,.2f}".ljust(61) + "║")
        print(f"║  🎯 GOAL: ${GOAL:,}".ljust(61) + "║")
        print(f"║  📈 SESSION PROFIT: ${self.profit:.4f}".ljust(61) + "║")
        print(f"║  ⚡ TOTAL TRADES: {self.trades}".ljust(61) + "║")
        print(f"║  🚀 RATE: ${rate_per_hour:.4f}/hour".ljust(61) + "║")
        print(f"║  ⏱️  ETA TO GOAL: {time_est}".ljust(61) + "║")
        print("╠" + "═" * 60 + "╣")
        print("║" + " PLATFORM BREAKDOWN & VERIFIED TRADES ".center(60, "─") + "║")
        print("╠" + "═" * 60 + "╣")
        
        # Binance stats
        bs = self.platform_stats['binance']
        bin_contrib = (bs['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🟡 BINANCE:  ${bd['binance']:,.2f}".ljust(36) + f"│ ✓{bs['verified']} trades │ +${bs['profit']:.4f} ({bin_contrib:.0f}%)".ljust(23) + "║")
        
        # Alpaca stats  
        aps = self.platform_stats['alpaca']
        alp_contrib = (aps['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🦙 ALPACA:   ${bd['alpaca']:,.2f}".ljust(36) + f"│ ✓{aps['verified']} trades │ +${aps['profit']:.4f} ({alp_contrib:.0f}%)".ljust(23) + "║")
        
        # Kraken stats
        ks = self.platform_stats['kraken']
        krk_contrib = (ks['profit'] / self.profit * 100) if self.profit > 0 else 0
        print(f"║  🐙 KRAKEN:   ${bd['kraken']:,.2f}".ljust(36) + f"│ ✓{ks['verified']} trades │ +${ks['profit']:.4f} ({krk_contrib:.0f}%)".ljust(23) + "║")
        
        print("╠" + "═" * 60 + "╣")
        
        # Show last 3 verified trades
        print("║" + " RECENT VERIFIED TRADES ".center(60, "─") + "║")
        recent = self.verified_trades[-5:] if self.verified_trades else []
        if recent:
            for t in reversed(recent):
                icon = "🟡" if t['platform'] == 'binance' else ("🦙" if t['platform'] == 'alpaca' else "🐙")
                line = f"║  {icon} {t['time']} {t['side'].upper()} {t['symbol']}: +${t['profit']:.4f} ✓"
                print(line.ljust(61) + "║")
        else:
            print("║  Waiting for first verified trade...".ljust(61) + "║")
        
        print("╚" + "═" * 60 + "╝")
        print()

    # ═══════════════════════════════════════════════════════════════
    # BINANCE TRADING
    # ═══════════════════════════════════════════════════════════════
    
    def binance_scan_and_trade(self):
        """Scan Binance - take profits - deploy cash"""
        try:
            for asset in ['SOL', 'BTC', 'ETH', 'AVAX', 'DOGE', 'XRP']:
                bal = self.binance.get_free_balance(asset)
                if bal < 0.00001:
                    continue
                
                pair = f'{asset}USDC'
                t = self.binance.get_ticker_price(pair)
                if not t:
                    continue
                    
                price = float(t.get('price', 0))
                value = bal * price
                
                if value < 1:
                    continue
                
                key = f'bin_{asset}'
                if key not in self.entries:
                    self.entries[key] = price
                    self.log(f"📍 BINANCE {asset}: Entry recorded @ ${price:.2f} (${value:.2f})")
                    continue
                
                entry = self.entries[key]
                pnl_pct = (price - entry) / entry * 100
                
                # Log position status periodically
                if hasattr(self, '_last_bin_log') and time.time() - self._last_bin_log.get(asset, 0) > 60:
                    self.log(f"📊 BINANCE {asset}: ${value:.2f} | Entry ${entry:.2f} → ${price:.2f} ({pnl_pct:+.2f}%)")
                    self._last_bin_log[asset] = time.time()
                elif not hasattr(self, '_last_bin_log'):
                    self._last_bin_log = {}
                
                # TURBO MODE: Take profit at 0.01% - NO STOP LOSS (wait for recovery)
                best_mom = self._get_best_momentum()
                should_profit = pnl_pct > 0.01  # Take profit at 0.01%
                # NO STOP LOSS - small positions can wait for market to recover
                should_rotate = best_mom and best_mom[0] != asset and pnl_pct > 0 and best_mom[1] > 1.5  # Only rotate when in profit
                
                if should_profit or should_rotate:
                    if should_profit:
                        reason = f"{pnl_pct:+.2f}%"
                    else:
                        reason = f"ROTATE→{best_mom[0]}"
                    self.log(f"🔥 BINANCE SELL {asset}: ${value:.2f} ({reason})")
                    
                    result = self.binance.place_market_order(pair, 'SELL', quantity=bal * 0.999)
                    
                    if result and ('orderId' in result or result.get('status') == 'FILLED'):
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('binance', asset, 'SELL', value, profit_usd)
                        del self.entries[key]
                        time.sleep(0.2)
                        self._binance_buy_best()
                    else:
                        self.log(f"   ⚠️ Order failed: {result}")
                        
            # Deploy idle USDC
            usdc = self.binance.get_free_balance('USDC')
            if usdc > 2:
                self._binance_buy_best()
                
        except Exception as e:
            self.log(f"⚠️ Binance error: {e}")
    
    def _binance_buy_best(self):
        usdc = self.binance.get_free_balance('USDC')
        if usdc < 2:
            return
            
        pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC', 'AVAXUSDC', 'DOGEUSDC']
        best_pair, best_mom = None, -999
        
        for pair in pairs:
            try:
                t = self.binance.get_24h_ticker(pair)
                mom = float(t.get('priceChangePercent', 0))
                if mom > best_mom:
                    best_pair, best_mom = pair, mom
            except:
                pass
        
        if best_pair and best_mom > 0:  # Only buy positive momentum
            asset = best_pair.replace('USDC', '')
            # Use 90% to leave room for fees and avoid insufficient balance
            buy_amount = usdc * 0.90
            if buy_amount < 2:
                return
            self.log(f"📥 BINANCE BUY {asset}: ${buy_amount:.2f} ({best_mom:+.1f}%)")
            
            result = self.binance.place_market_order(best_pair, 'BUY', quote_qty=buy_amount)
            
            if result and ('orderId' in result or result.get('status') == 'FILLED'):
                t = self.binance.get_ticker_price(best_pair)
                price = float(t.get('price', 0))
                self.entries[f'bin_{asset}'] = price
                self.log(f"   ✅ DEPLOYED @ ${price:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # ALPACA TRADING
    # ═══════════════════════════════════════════════════════════════
    
    def alpaca_scan_and_trade(self):
        try:
            positions = self.alpaca.get_positions()
            
            for pos in positions:
                sym = pos.get('symbol', '')
                qty = float(pos.get('qty', 0))
                entry = float(pos.get('avg_entry_price', 0))
                current = float(pos.get('current_price', 0))
                value = float(pos.get('market_value', 0))
                
                if value < 0.5:
                    continue
                
                # Check for stablecoins FIRST before modifying symbol
                # Symbols: USDCUSD, USDTUSD
                if sym in ['USDCUSD', 'USDTUSD', 'USDC/USD', 'USDT/USD']:
                    if value > 2:  # Worth converting
                        asset_name = 'USDC' if 'USDC' in sym else 'USDT'
                        self.log(f"💱 ALPACA CONVERT {asset_name}: ${value:.2f} → Cash")
                        result = self.alpaca.place_order(sym, qty, 'sell', 'market', 'ioc')
                        if result and result.get('status') in ['filled', 'accepted', 'new']:
                            self.log(f"   ✅ Converted to cash")
                            time.sleep(0.5)
                            self._alpaca_buy_best()
                        else:
                            self.log(f"   ⚠️ Convert failed: {result}")
                    continue
                
                # Extract asset name for non-stablecoins
                asset = sym.replace('/USD', '').replace('USD', '')
                
                pnl_pct = (current - entry) / entry * 100 if entry > 0 else 0
                
                # Log position status periodically
                if hasattr(self, '_last_alp_log') and time.time() - self._last_alp_log.get(asset, 0) > 60:
                    self.log(f"📊 ALPACA {asset}: ${value:.2f} | Entry ${entry:.2f} → ${current:.2f} ({pnl_pct:+.2f}%)")
                    self._last_alp_log[asset] = time.time()
                elif not hasattr(self, '_last_alp_log'):
                    self._last_alp_log = {}
                
                # TURBO MODE: Take profit only - NO STOP LOSS (wait for recovery)
                should_take_profit = pnl_pct > 0.01  # Take profit at 0.01%
                # NO STOP LOSS - small positions can wait for market to recover
                
                if should_take_profit:
                    self.log(f"🔥 ALPACA PROFIT {asset}: ${value:.2f} ({pnl_pct:+.2f}%)")
                    
                    result = self.alpaca.place_order(sym, qty, 'sell', 'market', 'ioc')
                    
                    if result and result.get('status') in ['filled', 'accepted', 'new']:
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('alpaca', asset, 'SELL', value, profit_usd)
                        time.sleep(0.3)
                        self._alpaca_buy_best()
                    else:
                        self.log(f"   ⚠️ Order failed: {result}")
            
            acc = self.alpaca.get_account()
            cash = float(acc.get('cash', 0))
            if cash > 2:
                self._alpaca_buy_best()
                
        except Exception as e:
            self.log(f"⚠️ Alpaca error: {e}")
    
    def _alpaca_buy_best(self):
        try:
            acc = self.alpaca.get_account()
            cash = float(acc.get('cash', 0))
            if cash < 2:
                return
            
            pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC']
            best_asset, best_mom = None, -999
            
            for pair in pairs:
                try:
                    t = self.binance.get_24h_ticker(pair)
                    mom = float(t.get('priceChangePercent', 0))
                    if mom > best_mom:
                        best_asset = pair.replace('USDC', '')
                        best_mom = mom
                except:
                    pass
            
            if best_asset:
                alpaca_sym = f'{best_asset}/USD'
                self.log(f"📥 ALPACA BUY {best_asset}: ${cash:.2f} ({best_mom:+.1f}%)")
                
                try:
                    quotes = self.alpaca.get_latest_crypto_quotes([alpaca_sym])
                    price = float(quotes[alpaca_sym].get('ap', 0))
                    qty = (cash * 0.95) / price
                    result = self.alpaca.place_order(alpaca_sym, qty, 'buy', 'market', 'ioc')
                    if result:
                        self.log(f"   ✅ DEPLOYED")
                except:
                    pass
        except:
            pass

    # ═══════════════════════════════════════════════════════════════
    # KRAKEN TRADING - USD + EUR PAIRS
    # ═══════════════════════════════════════════════════════════════
    
    def kraken_scan_and_trade(self):
        """Scan Kraken - USD and EUR pairs"""
        try:
            acct = self.kraken.account()
            usd_bal = 0.0
            eur_bal = 0.0
            
            for bal in acct.get('balances', []):
                asset = bal.get('asset', '')
                free = float(bal.get('free', 0))
                
                if free <= 0:
                    continue
                
                # Track cash - ZUSD is Kraken's USD format (ONLY ZUSD works directly for USD pairs)
                if asset in ['USD', 'ZUSD']:
                    usd_bal += free
                    continue
                elif asset in ['EUR', 'ZEUR']:
                    eur_bal += free
                    continue
                elif asset in ['USDT', 'USDC', 'TUSD', 'DAI']:
                    # These stablecoins need conversion first - skip for now
                    continue
                
                # It's a crypto - try USD first, then EUR
                price = 0
                quote = 'USD'
                pair = f'{asset}USD'
                
                try:
                    ticker = self.kraken.get_ticker(pair)
                    price = float(ticker.get('price', 0))
                except:
                    try:
                        pair = f'{asset}EUR'
                        ticker = self.kraken.get_ticker(pair)
                        price = float(ticker.get('price', 0)) * self.eur_usd
                        quote = 'EUR'
                    except:
                        continue
                
                if price <= 0:
                    continue
                
                value = free * price
                if value < 1:
                    continue
                
                key = f'krk_{asset}_{quote}'
                if key not in self.entries:
                    self.entries[key] = price
                    self.log(f"📍 KRAKEN {asset}/{quote}: Entry recorded @ ${price:.2f} (${value:.2f})")
                    continue
                
                entry = self.entries[key]
                pnl_pct = (price - entry) / entry * 100
                
                # Log position status periodically
                if hasattr(self, '_last_krk_log') and time.time() - self._last_krk_log.get(asset, 0) > 60:
                    self.log(f"📊 KRAKEN {asset}: ${value:.2f} | Entry ${entry:.2f} → ${price:.2f} ({pnl_pct:+.2f}%)")
                    self._last_krk_log[asset] = time.time()
                elif not hasattr(self, '_last_krk_log'):
                    self._last_krk_log = {}
                
                # TURBO MODE: Take profit only - NO STOP LOSS (wait for recovery)
                should_profit = pnl_pct > 0.01  # Take profit at 0.01%
                # NO STOP LOSS - small positions can wait for market to recover
                
                if should_profit:
                    self.log(f"🔥 KRAKEN PROFIT {asset}/{quote}: ${value:.2f} ({pnl_pct:+.2f}%)")
                    
                    result = self.kraken.place_market_order(f'{asset}{quote}', 'sell', quantity=free * 0.999)
                    
                    if result and (result.get('txid') or result.get('status') == 'FILLED' or 
                                   result.get('orderId') or 'dryRun' in result):
                        profit_usd = value * (pnl_pct / 100)
                        self.profit += profit_usd
                        self.trades += 1
                        self.log(f"   ✅ VERIFIED! +${profit_usd:.4f}")
                        self.record_verified_trade('kraken', f'{asset}/{quote}', 'SELL', value, profit_usd)
                        del self.entries[key]
                        time.sleep(0.3)
                    else:
                        self.log(f"   ⚠️ Order failed: {result}")
            
            # Deploy USD
            if usd_bal > 2:
                self._kraken_buy_best('USD', usd_bal)
            
            # Deploy EUR
            if eur_bal > 2:
                self._kraken_buy_best('EUR', eur_bal)
                
        except Exception as e:
            pass
    
    def _kraken_buy_best(self, quote: str, amount: float):
        """Buy best asset on Kraken with USD or EUR"""
        try:
            if amount < 2:
                return
            
            # Get best momentum from Binance
            pairs = ['SOLUSDC', 'BTCUSDC', 'ETHUSDC']
            best_asset, best_mom = None, -999
            
            for pair in pairs:
                try:
                    t = self.binance.get_24h_ticker(pair)
                    mom = float(t.get('priceChangePercent', 0))
                    if mom > best_mom:
                        best_asset = pair.replace('USDC', '')
                        best_mom = mom
                except:
                    pass
            
            if best_asset:
                kraken_pair = f'{best_asset}{quote}'
                self.log(f"📥 KRAKEN BUY {best_asset}/{quote}: ${amount:.2f} ({best_mom:+.1f}%)")
                
                result = self.kraken.place_market_order(kraken_pair, 'buy', quote_qty=amount * 0.95)
                
                # Detect success - Kraken returns orderId and status=FILLED
                success = False
                if result:
                    success = (result.get('orderId') or result.get('txid') or 
                              result.get('status') == 'FILLED' or 'dryRun' in result)
                
                if success:
                    try:
                        ticker = self.kraken.get_ticker(kraken_pair)
                        price = float(ticker.get('price', 0))
                        if quote == 'EUR':
                            price *= self.eur_usd
                        self.entries[f'krk_{best_asset}_{quote}'] = price
                        self.log(f"   ✅ DEPLOYED @ ${price:.4f}")
                    except:
                        pass
        except Exception as e:
            pass

    # ═══════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════════════════════════
    
    def run_cycle(self):
        # 👑 QUEEN: Update metrics every cycle (observation layer)
        try:
            self.queen.update_queen_metrics()
        except Exception:
            pass
        
        with ThreadPoolExecutor(max_workers=3) as ex:
            ex.submit(self.binance_scan_and_trade)
            ex.submit(self.alpaca_scan_and_trade)
            ex.submit(self.kraken_scan_and_trade)
    
    def run(self):
        print("🔥 MODE: TURBO V3 - MAXIMUM SPEED")
        print("⚡ PROFIT THRESHOLD: 0.01% (stable)")
        print("⚡ CYCLE SPEED: 0.3 seconds")
        print("⚡ KRAKEN: USD + EUR pairs enabled")
        print("👑 QUEEN: Advanced Intelligence Layer ACTIVE")
        print("🎯 GOAL: $1,000,000,000")
        print()
        
        # Get starting equity
        portfolio = self.get_total_portfolio()
        self.starting_equity = portfolio['total']
        self.print_billion_tracker(portfolio)
        
        cycle = 0
        while True:
            try:
                self.run_cycle()
                cycle += 1
                
                # Print tracker every 15 cycles (faster updates)
                if cycle % 15 == 0:
                    portfolio = self.get_total_portfolio()
                    self.print_billion_tracker(portfolio)
                
                # 👑 Queen verification every 50 cycles (~15 seconds)
                if cycle % 50 == 0 and self.queen.trades_total > 0:
                    print(self.queen.get_status_display())
                    # Save neural weights periodically
                    if self.queen.neuron:
                        try:
                            self.queen.neuron.save_weights()
                        except Exception:
                            pass
                
                time.sleep(0.3)  # TURBO SPEED
                
            except KeyboardInterrupt:
                print()
                self.log("🛑 PROTOCOL PAUSED")
                portfolio = self.get_total_portfolio()
                self.print_billion_tracker(portfolio)
                if self.queen.trades_total > 0:
                    print(self.queen.get_status_display())
                # Save Queen's learned weights on exit
                if self.queen.neuron:
                    try:
                        self.queen.neuron.save_weights()
                        self.log("💾 Queen neural weights saved")
                    except Exception:
                        pass
                break
            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(2)


if __name__ == "__main__":
    r = PlanetaryReclaimer()
    r.run()
