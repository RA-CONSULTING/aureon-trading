#!/usr/bin/env python3
"""
🧪 Simplified Sero Decision Flow Test
Demonstrates: Queen asks Sero → Gets recommendation → Applies to decision logic

This test bypasses full Orca initialization to focus on Sero integration.
"""

import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

from aureon_sero_client import SeroClient, SeroAdvice
from kraken_client import KrakenClient
import requests

@dataclass
class MockQueenDecision:
    """Simulates Queen neural gate decision"""
    base_confidence: float  # Queen's initial confidence (0.0-1.0)
    sero_advice: SeroAdvice  # Sero's recommendation
    final_confidence: float  # After blending Sero input
    decision: str  # EXECUTE or REJECT
    reasoning: str  # Why the decision was made

def apply_sero_to_queen_confidence(
    queen_base_confidence: float,
    sero_advice: Optional[SeroAdvice]
) -> tuple[float, str]:
    """
    This is the ACTUAL logic from orca_complete_kill_cycle.py _queen_gate_order()
    
    Blends Sero's AI recommendation into Queen's neural confidence score.
    
    Returns: (final_confidence, reasoning)
    """
    
    if not sero_advice:
        return queen_base_confidence, "⚠️ Sero unavailable - no modification"

    if sero_advice.recommendation == "ABORT":
        # Sero says DON'T DO IT - cut confidence in half
        final = queen_base_confidence * 0.5
        reason = f"❌ Sero ABORT penalty: {queen_base_confidence:.3f} → {final:.3f}"
        
    elif sero_advice.recommendation == "PROCEED" and sero_advice.confidence > 0.7:
        # Sero says GO with high confidence - boost Queen's confidence
        final = queen_base_confidence * 1.1
        reason = f"✅ Sero PROCEED boost: {queen_base_confidence:.3f} → {final:.3f} (+10%)"
        
    elif sero_advice.recommendation == "PROCEED":
        # Sero says GO but low confidence - no modification
        final = queen_base_confidence
        reason = f"⚠️ Sero PROCEED (low conf {sero_advice.confidence:.2f}) - no boost"
        
    else:  # CAUTION
        # Sero says be careful - no modification
        final = queen_base_confidence
        reason = f"⚠️ Sero CAUTION - no modification"
    
    return final, reason

def _live_eth_context() -> Dict[str, Any]:
    """Fetch live ETH/USD data from Kraken and build real-data context."""
    client = KrakenClient()
    symbols = ["ETH/USD", "ETHUSD", "XETHZUSD", "ETHUSDT"]
    ticker = None
    for sym in symbols:
        t = client.get_ticker(sym)
        price = float(t.get("price", 0.0) or 0.0)
        bid = float(t.get("bid", 0.0) or 0.0)
        ask = float(t.get("ask", 0.0) or 0.0)
        if price > 0 and bid > 0 and ask > 0:
            ticker = t
            break

    # Fallback: direct Kraken public API (real data only)
    if not ticker:
        try:
            url = "https://api.kraken.com/0/public/Ticker"
            params = {"pair": "ETHUSD,XETHZUSD,ETHUSDT"}
            res = requests.get(url, params=params, timeout=15)
            res.raise_for_status()
            payload = res.json()
            result = payload.get("result", {}) if isinstance(payload, dict) else {}
            for _, t in result.items():
                last = float(t.get("c", [0])[0] or 0.0)
                bid = float(t.get("b", [0])[0] or 0.0)
                ask = float(t.get("a", [0])[0] or 0.0)
                if last > 0 and bid > 0 and ask > 0:
                    ticker = {"symbol": "ETH/USD", "price": last, "bid": bid, "ask": ask}
                    break
        except Exception:
            ticker = None

    if not ticker:
        raise RuntimeError("Live ETH/USD price unavailable from Kraken")

    price = float(ticker.get("price", 0.0) or 0.0)
    bid = float(ticker.get("bid", 0.0) or 0.0)
    ask = float(ticker.get("ask", 0.0) or 0.0)

    spread = max(0.0, ask - bid)
    spread_pct = spread / price if price > 0 else 0.0

    # Derived metrics from live data (no simulations)
    coherence = max(0.0, min(1.0, 1.0 - spread_pct * 10.0))
    fusion_bias = (price - ((bid + ask) / 2.0)) / price
    threat_level = max(0.0, min(1.0, spread_pct * 50.0))

    return {
        "symbol": "ETH/USD",
        "price": price,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "spread_pct": round(spread_pct, 6),
        "coherence": round(coherence, 4),
        "fusion_bias": round(fusion_bias, 6),
        "threat_level": round(threat_level, 4),
    }

async def _validate_move_after_wait(start_price: float, move_pct: float, horizon_min: int) -> Dict[str, Any]:
    """Wait and validate whether price moved by target percent (real data only)."""
    wait_seconds = max(1, int(horizon_min * 60))
    print(f"\n⏱️ Waiting {wait_seconds}s to validate ETH move...")
    await asyncio.sleep(wait_seconds)
    end_ctx = _live_eth_context()
    end_price = float(end_ctx.get("price", 0.0) or 0.0)
    if end_price <= 0:
        return {"validated": False, "reason": "End price unavailable"}

    delta_pct = ((end_price - start_price) / start_price) * 100.0 if start_price > 0 else 0.0
    moved_up = delta_pct >= move_pct
    moved_down = delta_pct <= -move_pct
    return {
        "validated": True,
        "start_price": round(start_price, 4),
        "end_price": round(end_price, 4),
        "delta_pct": round(delta_pct, 4),
        "moved_up": moved_up,
        "moved_down": moved_down,
    }


async def test_decision_scenario(
    scenario_name: str,
    symbol: str,
    side: str,
    queen_base_confidence: float,
    context: Dict[str, Any]
) -> MockQueenDecision:
    """
    Test a single decision scenario showing Sero's influence on Queen
    """
    
    print(f"\n{'='*80}")
    print(f"📋 SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    print(f"Symbol: {symbol} | Side: {side}")
    print(f"Queen Base Confidence: {queen_base_confidence:.3f}")
    print(f"\nContext:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    # Step 1: Queen asks Sero for validation
    print(f"\n🤖 Queen asks Sero: 'Should I execute {side} on {symbol}?'")
    
    sero = SeroClient()
    sero_advice = await sero.ask_trading_decision(
        symbol=symbol,
        side=side,
        context=context,
        queen_confidence=queen_base_confidence
    )
    
    # Step 2: Display Sero's response
    print(f"\n🧠 Sero responds:")
    if sero_advice:
        print(f"  Recommendation: {sero_advice.recommendation}")
        print(f"  Confidence: {sero_advice.confidence:.3f}")
        print(f"  Reasoning: {sero_advice.reasoning}")
        if sero_advice.risk_flags:
            print(f"  Risk Flags: {', '.join(sero_advice.risk_flags)}")
    else:
        print("  ⚠️ No response (Sero unavailable)")
    
    # Step 3: Apply Sero's advice to Queen's decision logic
    final_confidence, blend_reasoning = apply_sero_to_queen_confidence(
        queen_base_confidence, sero_advice
    )
    
    print(f"\n👑 Queen applies Sero's advice to neural network:")
    print(f"  {blend_reasoning}")
    
    # Step 4: Final decision (threshold = 0.618, golden ratio)
    EXECUTION_THRESHOLD = 0.618
    if final_confidence >= EXECUTION_THRESHOLD:
        decision = "EXECUTE"
        decision_icon = "✅"
    else:
        decision = "REJECT"
        decision_icon = "❌"
    
    print(f"\n{decision_icon} FINAL DECISION: {decision}")
    print(f"  Final Confidence: {final_confidence:.3f}")
    print(f"  Threshold: {EXECUTION_THRESHOLD:.3f}")
    print(f"  Above threshold: {final_confidence >= EXECUTION_THRESHOLD}")
    
    return MockQueenDecision(
        base_confidence=queen_base_confidence,
        sero_advice=sero_advice,
        final_confidence=final_confidence,
        decision=decision,
        reasoning=blend_reasoning
    )

async def main():
    """
    Test multiple scenarios showing how Sero's AI affects Queen's decisions
    """
    
    print("\n" + "="*80)
    print("🤖👑 QUEEN + SERO AI - DECISION FLOW TEST")
    print("="*80)
    print("Demonstrates: Queen queries Sero → Sero validates → Queen applies advice")
    print("="*80)
    
    scenarios = []

    # Live ETH/USD scenario (real data only)
    live_ctx = _live_eth_context()
    move_pct = float(os.getenv("AUREON_SERO_TEST_MOVE_PCT", "1.0"))
    horizon_min = int(os.getenv("AUREON_SERO_TEST_HORIZON_MIN", "1"))
    validate_after_wait = os.getenv("AUREON_SERO_TEST_VALIDATE", "true").lower() == "true"
    price = live_ctx["price"]
    target_up = price * (1 + move_pct / 100.0)
    target_down = price * (1 - move_pct / 100.0)

    sero = SeroClient()
    question = (
        f"Given live ETH/USD price ${price:,.2f}, do you expect ETH to move "
        f"UP or DOWN by at least {move_pct:.2f}% within {horizon_min} minutes? "
        f"Reply with UP or DOWN and confidence."
    )
    print("\n🗣️ Queen asks Sero (market direction question):")
    print(f"  {question}")
    intel = await sero.ask_market_intelligence(question)
    print("\n💬 Sero response (direction):")
    print(f"  {intel or 'No response'}")

    direction = "BUY"
    if intel:
        upper = intel.upper()
        if "DOWN" in upper and "UP" not in upper:
            direction = "SELL"
        elif "UP" in upper:
            direction = "BUY"

    live_ctx.update({
        "target_move_pct": move_pct,
        "horizon_min": horizon_min,
        "target_up": round(target_up, 4),
        "target_down": round(target_down, 4),
    })

    validation = None
    if validate_after_wait:
        validation = await _validate_move_after_wait(price, move_pct, horizon_min)
        print("\n🔍 Move validation:")
        if validation.get("validated"):
            print(f"  Start: ${validation['start_price']:.2f} → End: ${validation['end_price']:.2f}")
            print(f"  Δ%: {validation['delta_pct']:.2f}%")
            print(f"  Moved UP by ≥{move_pct:.2f}%: {validation['moved_up']}")
            print(f"  Moved DOWN by ≥{move_pct:.2f}%: {validation['moved_down']}")
        else:
            print(f"  Validation skipped: {validation.get('reason')}")

    scenarios.append(await test_decision_scenario(
        scenario_name="Live ETH Direction + Validation",
        symbol="ETH/USD",
        side=direction,
        queen_base_confidence=0.64,
        context=live_ctx
    ))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Base: {scenario.base_confidence:.3f} → "
              f"Sero: {scenario.sero_advice.recommendation} ({scenario.sero_advice.confidence:.3f}) → "
              f"Final: {scenario.final_confidence:.3f} → "
              f"{scenario.decision}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE - Sero AI successfully integrated into Queen decision logic")
    print("="*80)
    print("\nKey Findings:")
    print("  • Sero ABORT cuts Queen confidence by 50%")
    print("  • Sero PROCEED (>0.7 conf) boosts Queen confidence by 10%")
    print("  • Sero CAUTION/low-conf PROCEED → no modification")
    print("  • Final decision: confidence >= 0.618 (golden ratio) → EXECUTE")
    print("\n🌌 Sero AI Oracle now powers Queen Hive Mind decision gates! 🐝👑")

if __name__ == "__main__":
    asyncio.run(main())
