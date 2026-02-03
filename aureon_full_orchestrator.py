#!/usr/bin/env python3
"""
🌍 AUREON FULL ORCHESTRATOR 🌍
================================
Hooks up ALL systems:
- Stargate Protocol (12 planetary nodes)
- Quantum Mirror Scanner (timeline detection)
- Timeline Anchor Validator (7-day validation)
- Probability Nexus (3-pass Batten Matrix)
- Queen Hive Mind (execution gate)
- Planet Saver (trade execution & compounding)

ONE SYSTEM TO RULE THEM ALL
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json
import asyncio
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import math

# Sacred constants
PHI = 1.618033988749895
SCHUMANN = 7.83
LOVE_FREQ = 528

@dataclass
class Opportunity:
    """Trading opportunity with full validation"""
    symbol: str
    exchange: str
    price: float
    momentum: float  # 24h change %
    volume: float
    
    # Validation scores
    stargate_resonance: float = 0.0
    quantum_coherence: float = 0.0
    timeline_anchor_strength: float = 0.0
    p1_harmonic: float = 0.0
    p2_coherence: float = 0.0
    p3_stability: float = 0.0
    
    # Final scores
    batten_score: float = 0.0
    queen_confidence: float = 0.0
    final_score: float = 0.0
    
    ready_for_4th: bool = False
    timestamp: str = ""

@dataclass
class SystemState:
    """Full system state"""
    opportunities_scanned: int = 0
    opportunities_validated: int = 0
    trades_executed: int = 0
    trades_won: int = 0
    total_profit: float = 0.0
    active_position: Optional[Dict] = None
    last_scan: str = ""
    stargate_active: bool = False
    quantum_mirror_active: bool = False
    timeline_validator_active: bool = False
    last_gamma_sync: Optional[str] = None

class AureonFullOrchestrator:
    """
    Master orchestrator connecting all Aureon systems
    """
    
    def __init__(self):
        self.state = self._load_state()
        self.client = None
        self.stargate = None
        self.quantum_mirror = None
        self.timeline_validator = None
        self.queen = None
        
    def _load_state(self) -> SystemState:
        try:
            with open('orchestrator_state.json', 'r') as f:
                data = json.load(f)
                return SystemState(**data)
        except:
            return SystemState()
    
    def _save_state(self):
        with open('orchestrator_state.json', 'w') as f:
            json.dump(asdict(self.state), f, indent=2)
    
    def initialize_systems(self):
        """Initialize all subsystems"""
        print("\n" + "="*60)
        print("🌍 AUREON FULL ORCHESTRATOR - INITIALIZING ALL SYSTEMS")
        print("="*60)
        
        # 1. Kraken Client
        print("\n📡 Loading Kraken Client...")
        try:
            from kraken_client import KrakenClient, get_kraken_client
            self.client = get_kraken_client()
            print("   ✅ Kraken connected")
        except Exception as e:
            print(f"   ❌ Kraken failed: {e}")
            return False
        
        # 2. Stargate Protocol
        print("\n🌌 Loading Stargate Protocol...")
        try:
            from aureon_stargate_protocol import create_stargate_engine
            self.stargate = create_stargate_engine(with_integrations=False)
            self.state.stargate_active = True
            print(f"   ✅ {len(self.stargate.stargates)} planetary nodes active")
        except Exception as e:
            print(f"   ⚠️ Stargate not available: {e}")
            self.state.stargate_active = False
        
        # 3. Quantum Mirror Scanner
        print("\n🔮 Loading Quantum Mirror Scanner...")
        try:
            from aureon_quantum_mirror_scanner import QuantumMirrorScanner
            self.quantum_mirror = QuantumMirrorScanner()
            self.state.quantum_mirror_active = True
            print("   ✅ Quantum mirrors initialized")
        except Exception as e:
            print(f"   ⚠️ Quantum Mirror not available: {e}")
            self.state.quantum_mirror_active = False
        
        # 4. Timeline Anchor Validator
        print("\n⚓ Loading Timeline Anchor Validator...")
        try:
            from aureon_timeline_anchor_validator import TimelineAnchorValidator
            self.timeline_validator = TimelineAnchorValidator()
            self.state.timeline_validator_active = True
            print("   ✅ Timeline validator ready")
        except Exception as e:
            print(f"   ⚠️ Timeline Validator not available: {e}")
            self.state.timeline_validator_active = False
        
        # 5. Queen Hive Mind
        print("\n👑 Loading Queen Hive Mind...")
        try:
            from aureon_queen_hive_mind import QueenHiveMind
            self.queen = QueenHiveMind()
            print("   ✅ Queen awakened")
        except Exception as e:
            print(f"   ⚠️ Queen not available: {e}")
        
        print("\n" + "="*60)
        print("✅ SYSTEM INITIALIZATION COMPLETE")
        print(f"   Stargate:    {'🟢' if self.state.stargate_active else '🔴'}")
        print(f"   Quantum:     {'🟢' if self.state.quantum_mirror_active else '🔴'}")
        print(f"   Timeline:    {'🟢' if self.state.timeline_validator_active else '🔴'}")
        print("="*60)
        
        return True
    
    def scan_opportunities(self) -> List[Opportunity]:
        """Scan all markets for opportunities"""
        print("\n🔍 SCANNING MARKETS...")
        
        opportunities = []
        tickers = self.client.get_24h_tickers()
        
        # Focus on USDC pairs (what we can trade)
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if not symbol.endswith('USDC'):
                continue
            
            change = float(ticker.get('priceChangePercent', 0))
            volume = float(ticker.get('quoteVolume', 0))
            price = float(ticker.get('lastPrice', 0))
            
            # Filter: positive momentum, decent volume
            if change > 0.5 and volume > 500:
                opp = Opportunity(
                    symbol=symbol,
                    exchange='kraken',
                    price=price,
                    momentum=change,
                    volume=volume,
                    timestamp=datetime.now().isoformat()
                )
                opportunities.append(opp)
        
        self.state.opportunities_scanned = len(opportunities)
        print(f"   Found {len(opportunities)} raw opportunities")
        
        return opportunities
    
    def validate_with_stargate(self, opp: Opportunity) -> float:
        """Validate opportunity with Stargate resonance"""
        if not self.state.stargate_active or not self.stargate:
            return 0.5  # Neutral if not available
        
        try:
            # Use stargate to compute resonance
            # The symbol's hash creates a unique frequency
            symbol_hash = sum(ord(c) for c in opp.symbol)
            base_freq = (symbol_hash % 144) + 396  # Solfeggio range
            
            # Check resonance with active nodes
            resonance = 0.0
            for node_id, node in self.stargate.stargates.items():
                node_freq = node.frequency
                # Harmonic alignment
                ratio = base_freq / node_freq
                harmonic_match = abs(ratio - round(ratio))
                if harmonic_match < 0.1:
                    resonance += node.casimir_coupling * 0.2
            
            return min(resonance, 1.0)
        except:
            return 0.5
    
    def validate_with_quantum_mirror(self, opp: Opportunity) -> float:
        """Validate opportunity with Quantum Mirror coherence"""
        if not self.state.quantum_mirror_active or not self.quantum_mirror:
            return 0.5
        
        try:
            # Check if this symbol aligns with beneficial timelines
            coherence = 0.5 + (opp.momentum / 100) * PHI
            
            # Volume adds stability
            if opp.volume > 10000:
                coherence += 0.1
            
            return min(coherence, 1.0)
        except:
            return 0.5
    
    def validate_with_timeline_anchor(self, opp: Opportunity) -> float:
        """Check timeline anchor strength"""
        if not self.state.timeline_validator_active or not self.timeline_validator:
            return 0.5
        
        try:
            # Check pending validations for this symbol
            base_symbol = opp.symbol.replace('USDC', '').replace('USD', '')
            
            # Look for related anchors
            anchor_strength = 0.5
            if hasattr(self.timeline_validator, 'pending_validations'):
                for anchor_id, anchor in self.timeline_validator.pending_validations.items():
                    if base_symbol in anchor_id:
                        anchor_strength = max(anchor_strength, anchor.get('anchor_strength', 0.5))
            
            return anchor_strength
        except:
            return 0.5
    
    def compute_batten_matrix(self, opp: Opportunity) -> float:
        """
        Compute 3-pass Batten Matrix validation
        P1: Harmonic validation
        P2: Coherence validation
        P3: Stability validation
        """
        # P1: Harmonic - based on momentum and golden ratio
        p1 = min(opp.momentum / (100 / PHI), 1.0)
        opp.p1_harmonic = p1
        
        # P2: Coherence - how aligned are all signals
        signals = [opp.stargate_resonance, opp.quantum_coherence, opp.timeline_anchor_strength]
        mean_signal = sum(signals) / len(signals)
        variance = sum((s - mean_signal)**2 for s in signals) / len(signals)
        p2 = 1.0 - min(variance * 2, 1.0)  # Low variance = high coherence
        opp.p2_coherence = p2
        
        # P3: Stability - volume and price stability
        p3 = min(math.log10(opp.volume + 1) / 5, 1.0)
        opp.p3_stability = p3
        
        # Batten Score: geometric mean
        batten = (p1 * p2 * p3) ** (1/3)
        opp.batten_score = batten
        
        # Check if ready for 4th decision
        # All passes must be > 0.5 and coherence must be high
        coherence = 1 - (max(p1, p2, p3) - min(p1, p2, p3))
        opp.ready_for_4th = (p1 > 0.5 and p2 > 0.5 and p3 > 0.5 and coherence > PHI - 1)
        
        return batten
    
    def ask_queen(self, opp: Opportunity) -> float:
        """Get Queen's confidence on this opportunity"""
        if not self.queen:
            return opp.batten_score
        
        try:
            # Ask Queen for guidance
            guidance = self.queen.ask_queen_will_we_win(
                asset=opp.symbol,
                exchange=opp.exchange,
                opportunity_score=opp.batten_score,
                context={
                    'momentum': opp.momentum,
                    'stargate': opp.stargate_resonance,
                    'quantum': opp.quantum_coherence,
                    'timeline': opp.timeline_anchor_strength
                }
            )
            return guidance.get('confidence', opp.batten_score)
        except:
            return opp.batten_score
    
    def validate_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """Run full validation pipeline on all opportunities"""
        print("\n🔬 VALIDATING OPPORTUNITIES...")
        print("   Running: Stargate → Quantum Mirror → Timeline Anchor → Batten Matrix → Queen")
        
        validated = []
        for opp in opportunities:
            # Layer 1: Stargate Resonance
            opp.stargate_resonance = self.validate_with_stargate(opp)
            
            # Layer 2: Quantum Mirror Coherence
            opp.quantum_coherence = self.validate_with_quantum_mirror(opp)
            
            # Layer 3: Timeline Anchor Strength
            opp.timeline_anchor_strength = self.validate_with_timeline_anchor(opp)
            
            # Layer 4: Batten Matrix (3-pass)
            opp.batten_score = self.compute_batten_matrix(opp)
            
            # Layer 5: Queen Confidence
            opp.queen_confidence = self.ask_queen(opp)
            
            # Final Score
            opp.final_score = (
                opp.batten_score * 0.4 +
                opp.queen_confidence * 0.3 +
                opp.stargate_resonance * 0.1 +
                opp.quantum_coherence * 0.1 +
                opp.timeline_anchor_strength * 0.1
            )
            
            if opp.final_score > 0.5:
                validated.append(opp)
        
        # Sort by final score
        validated.sort(key=lambda x: -x.final_score)
        
        self.state.opportunities_validated = len(validated)
        print(f"   ✅ {len(validated)} opportunities passed validation")
        
        return validated
    
    def display_opportunities(self, opportunities: List[Opportunity], top_n: int = 10):
        """Display top opportunities with full validation details"""
        print(f"\n📊 TOP {min(top_n, len(opportunities))} VALIDATED OPPORTUNITIES:")
        print("-" * 80)
        print(f"{'Symbol':<12} {'Mom%':>6} {'P1':>5} {'P2':>5} {'P3':>5} {'Batten':>7} {'Queen':>6} {'Final':>6} {'4th?'}")
        print("-" * 80)
        
        for opp in opportunities[:top_n]:
            fourth = "✅" if opp.ready_for_4th else "⏳"
            print(f"{opp.symbol:<12} {opp.momentum:>6.1f} {opp.p1_harmonic:>5.2f} {opp.p2_coherence:>5.2f} {opp.p3_stability:>5.2f} {opp.batten_score:>7.3f} {opp.queen_confidence:>6.2f} {opp.final_score:>6.3f} {fourth}")
        
        print("-" * 80)
    
    def execute_trade(self, opp: Opportunity, live: bool = False) -> bool:
        """Execute trade if opportunity passes 4th gate"""
        if not opp.ready_for_4th:
            print(f"   ⏳ {opp.symbol} not ready for 4th decision")
            return False
        
        # Get available balance
        balances = self.client.get_account_balance()
        usdc = balances.get('USDC', 0)
        
        if usdc < 5:
            print(f"   ⚠️ Insufficient USDC: ${usdc:.2f}")
            return False
        
        trade_amount = usdc * 0.90  # Use 90%
        
        print(f"\n🎯 4TH DECISION - EXECUTING TRADE")
        print(f"   Symbol: {opp.symbol}")
        print(f"   Amount: ${trade_amount:.2f}")
        print(f"   Score: {opp.final_score:.3f}")
        
        if live:
            try:
                result = self.client.place_market_order(
                    opp.symbol, 'buy', quote_qty=trade_amount
                )
                
                if result and result.get('status') == 'FILLED':
                    print(f"   ✅ FILLED @ ${result.get('price')}")
                    
                    self.state.trades_executed += 1
                    self.state.active_position = {
                        'symbol': opp.symbol,
                        'entry_price': float(result.get('price', 0)),
                        'quantity': float(result.get('executedQty', 0)),
                        'entry_cost': float(result.get('cummulativeQuoteQty', 0)),
                        'entry_time': datetime.now().isoformat(),
                        'validation_score': opp.final_score
                    }
                    self._save_state()
                    return True
                else:
                    print(f"   ❌ Order failed: {result}")
            except Exception as e:
                print(f"   ❌ Execution error: {e}")
        else:
            print("   [DRY-RUN] Would execute here")
        
        return False
    
    def check_active_position(self, target_profit: float = 1.0, live: bool = False) -> Optional[float]:
        """Check active position for profit target"""
        if not self.state.active_position:
            # Check for MELANIA (our first trade)
            balances = self.client.get_account_balance()
            melania = balances.get('MELANIA', 0)
            
            if melania > 1:
                self.state.active_position = {
                    'symbol': 'MELANIAUSDC',
                    'entry_price': 0.1515,
                    'quantity': melania,
                    'entry_cost': 13.75,
                    'entry_time': datetime.now().isoformat()
                }
        
        if not self.state.active_position:
            return None
        
        pos = self.state.active_position
        ticker = None
        for t in self.client.get_24h_tickers():
            if t.get('symbol') == pos['symbol']:
                ticker = t
                break
        
        if not ticker:
            return None
        
        current_price = float(ticker.get('lastPrice', 0))
        current_value = pos['quantity'] * current_price
        pnl = current_value - pos['entry_cost']
        pnl_pct = (pnl / pos['entry_cost']) * 100
        
        print(f"\n📈 ACTIVE POSITION: {pos['symbol']}")
        print(f"   Entry: ${pos['entry_price']:.4f} → Current: ${current_price:.4f}")
        print(f"   Value: ${current_value:.2f}")
        print(f"   P&L: {'+'if pnl>=0 else ''}{pnl:.2f} ({pnl_pct:+.2f}%) {'🟢' if pnl>=0 else '🔴'}")
        
        if pnl_pct >= target_profit:
            print(f"\n🎯 TARGET HIT! +{pnl_pct:.2f}% >= {target_profit}%")
            
            if live:
                try:
                    result = self.client.place_market_order(
                        pos['symbol'], 'sell', qty=pos['quantity']
                    )
                    
                    if result and result.get('status') == 'FILLED':
                        sell_value = float(result.get('cummulativeQuoteQty', 0))
                        profit = sell_value - pos['entry_cost']
                        
                        print(f"   ✅ SOLD @ ${result.get('price')}")
                        print(f"   💰 PROFIT: ${profit:.2f}")
                        
                        self.state.trades_won += 1
                        self.state.total_profit += profit
                        self.state.active_position = None
                        self._save_state()
                        
                        return profit
                except Exception as e:
                    print(f"   ❌ Sell error: {e}")
            else:
                print("   [DRY-RUN] Would sell here")
        
        return pnl

    def _trigger_gamma_sync(self):
        """Triggers the gammaSync.ts script if enough time has passed."""
        now = datetime.now()
        sync_needed = False
        
        if self.state.last_gamma_sync:
            last_sync_time = datetime.fromisoformat(self.state.last_gamma_sync)
            if (now - last_sync_time) > timedelta(minutes=30):
                sync_needed = True
        else:
            # First time running
            sync_needed = True

        if sync_needed:
            print("\n🔄 Triggering Gamma.io Sync...")
            try:
                # Assumes npx and ts-node are in the environment PATH
                command = ["npx", "ts-node", "scripts/gammaSync.ts"]
                subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.state.last_gamma_sync = now.isoformat()
                print("   ✅ Gamma sync process started in background.")
            except Exception as e:
                print(f"   ❌ Failed to start Gamma sync: {e}")

    def run_cycle(self, live: bool = False, target_profit: float = 1.0):
        """Run one complete orchestration cycle"""
        print("\n" + "="*70)
        print(f"🌍 AUREON ORCHESTRATOR CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 0. Trigger background syncs
        self._trigger_gamma_sync()

        # 1. Check active position first
        pnl = self.check_active_position(target_profit=target_profit, live=live)
        
        # 2. If no position or sold, find new opportunities
        if not self.state.active_position:
            # Scan
            opportunities = self.scan_opportunities()
            
            # Validate
            validated = self.validate_opportunities(opportunities)
            
            # Display
            if validated:
                self.display_opportunities(validated)
                
                # Execute best if ready
                best = validated[0]
                if best.ready_for_4th:
                    self.execute_trade(best, live=live)
            else:
                print("\n⏳ No validated opportunities right now")
        
        # 3. Summary
        print(f"\n📊 SESSION SUMMARY:")
        print(f"   Scanned: {self.state.opportunities_scanned}")
        print(f"   Validated: {self.state.opportunities_validated}")
        print(f"   Trades: {self.state.trades_executed}")
        print(f"   Wins: {self.state.trades_won}")
        print(f"   Profit: ${self.state.total_profit:.2f}")
        
        self.state.last_scan = datetime.now().isoformat()
        self._save_state()
    
    def run_continuous(self, live: bool = False, interval: int = 60, target: float = 1.0):
        """Run continuous orchestration loop"""
        print(f"\n🔄 CONTINUOUS MODE - Every {interval}s | Target: {target}%")
        print("   Press Ctrl+C to stop\n")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                self.run_cycle(live=live, target_profit=target)
                
                print(f"\n⏳ Next cycle in {interval}s...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Stopped by user")
                print(f"Final: {self.state.trades_won} wins, ${self.state.total_profit:.2f} profit")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(interval)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Aureon Full Orchestrator')
    parser.add_argument('--live', action='store_true', help='Enable live trading')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval')
    parser.add_argument('--target', type=float, default=1.0, help='Target profit %')
    
    args = parser.parse_args()
    
    orchestrator = AureonFullOrchestrator()
    
    if not orchestrator.initialize_systems():
        print("❌ Failed to initialize systems")
        return
    
    if args.continuous:
        orchestrator.run_continuous(
            live=args.live, 
            interval=args.interval, 
            target=args.target
        )
    else:
        orchestrator.run_cycle(live=args.live, target_profit=args.target)


if __name__ == '__main__':
    main()
