#!/usr/bin/env python3
"""
🧪 FULL SPECTRUM BOT DETECTION FLOW TEST 🧪
═══════════════════════════════════════════════════════════════════════════════
Tests the complete pipeline:
  1. Bot Shape Scanner (0.001Hz - 10MHz spectrum)
  2. Cultural Attribution (Firm fingerprinting)
  3. Bot Census Registry (Storage & tracking)
  4. Deep Money Flow (Historical manipulation evidence)
  5. Queen Hive Mind (Decision integration)
  6. Orca/Whale Detection (Big player awareness)

Gary Leckey | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = sys.stdout if 'pytest' in sys.modules else io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import time
import json
import random
import hashlib
from datetime import datetime
from dataclasses import asdict

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS - Load all the systems
# ═══════════════════════════════════════════════════════════════════════════════

print("🔌 Loading Aureon Systems...")

# Bot Shape Scanner
try:
    from aureon_bot_shape_scanner import (
        SPECTRUM_BANDS, SpectralBandResult, BotShapeFingerprint
    )
    SCANNER_OK = True
    print("  ✅ Bot Shape Scanner (Full Spectrum)")
except ImportError as e:
    SCANNER_OK = False
    print(f"  ❌ Bot Shape Scanner: {e}")

# Firm Intelligence & Bot Census
try:
    from aureon_firm_intelligence_catalog import (
        get_bot_census, BotCensusEntry, BotCensusRegistry
    )
    CENSUS_OK = True
    print("  ✅ Bot Census Registry")
except ImportError as e:
    CENSUS_OK = False
    print(f"  ❌ Bot Census: {e}")

# Cultural Fingerprinting
try:
    from aureon_cultural_bot_fingerprinting import CULTURAL_ENTITIES
    CULTURAL_OK = True
    print("  ✅ Cultural Bot Fingerprinting")
except ImportError as e:
    CULTURAL_OK = False
    print(f"  ❌ Cultural Fingerprinting: {e}")

# Deep Money Flow
try:
    from aureon_deep_money_flow_analyzer import (
        get_money_flow_vault, MoneyFlowEvent, DeepMoneyFlowVault
    )
    VAULT_OK = True
    print("  ✅ Deep Money Flow Vault")
except ImportError as e:
    VAULT_OK = False
    print(f"  ❌ Deep Money Flow: {e}")

# Queen Hive Mind
try:
    from aureon_queen_hive_mind import QueenHiveMind
    QUEEN_OK = True
    print("  ✅ Queen Hive Mind")
except ImportError as e:
    QUEEN_OK = False
    print(f"  ❌ Queen Hive Mind: {e}")

# ThoughtBus
try:
    from aureon_thought_bus import ThoughtBus, Thought
    BUS_OK = True
    print("  ✅ ThoughtBus")
except ImportError as e:
    BUS_OK = False
    print(f"  ❌ ThoughtBus: {e}")

# Stargate Protocol (Planetary Harmonic Network)
try:
    from aureon_stargate_protocol import SCHUMANN_BASE, PHI, StargateNode
    STARGATE_OK = True
    print("  ✅ Stargate Protocol (Planetary Harmonics)")
except ImportError as e:
    STARGATE_OK = False
    print(f"  ❌ Stargate Protocol: {e}")

print()

# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATED DATA GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_mock_spectrum_results():
    """Simulate full spectrum scan results"""
    bands = [
        ("INFRA_LOW", 0.003, 0.12, "Deep Ocean Pulse 🌊"),
        ("MID_RANGE", 2.5, 0.45, "Surface Wave Active 🏄"),
        ("HIGH_FREQ", 85.0, 0.78, "Heavy Rain 🌧️"),
        ("ULTRA_HIGH", 5500.0, 0.91, "SINGULARITY ⚛️"),
    ]
    
    results = []
    for name, freq, amp, state in bands:
        # Add some randomness
        freq_jitter = freq * (1 + random.uniform(-0.1, 0.1))
        amp_jitter = min(1.0, amp * (1 + random.uniform(-0.2, 0.2)))
        
        results.append(SpectralBandResult(
            band_name=name,
            dominant_freq=freq_jitter,
            amplitude=amp_jitter,
            activity_score=amp_jitter,
            state_description=state
        ))
    return results

def generate_mock_fingerprint(symbol: str) -> BotShapeFingerprint:
    """Generate a mock bot fingerprint for testing"""
    spectrum = generate_mock_spectrum_results()
    
    # Pick strongest band for classification
    strongest = max(spectrum, key=lambda x: x.amplitude)
    
    class_map = {
        "ULTRA_HIGH": "QUANTUM_HFT",
        "HIGH_FREQ": "SCALPER_BOT",
        "MID_RANGE": "MARKET_MAKER",
        "INFRA_LOW": "WHALE_ACCUMULATOR"
    }
    
    return BotShapeFingerprint(
        symbol=symbol,
        timestamp=time.time(),
        spectrum_results=spectrum,
        volume_profile=[],
        layering_score=random.uniform(0.3, 0.9),
        bot_class=class_map.get(strongest.band_name, "UNKNOWN"),
        confidence=random.uniform(0.7, 0.95)
    )

def attribute_to_firm(fingerprint: BotShapeFingerprint) -> str:
    """Attribute bot fingerprint to a known firm based on spectrum"""
    # Find strongest band
    strongest = max(fingerprint.spectrum_results, key=lambda x: x.amplitude)
    
    # Match to cultural entities
    for firm_id, data in CULTURAL_ENTITIES.items():
        if data.get("spectrum_preference") == strongest.band_name:
            return firm_id
    
    return "UNKNOWN_ENTITY"

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TEST FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("🔭 FULL SPECTRUM BOT DETECTION FLOW TEST 🔭")
    print("=" * 70)
    print()
    
    # Initialize systems
    bus = ThoughtBus() if BUS_OK else None
    census = get_bot_census() if CENSUS_OK else None
    vault = get_money_flow_vault() if VAULT_OK else None
    
    # Test symbols
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    
    print("📡 PHASE 1: Scanning Full Spectrum (0.001Hz - 10MHz)...")
    print("-" * 70)
    
    detected_bots = []
    
    for symbol in symbols:
        # Generate mock fingerprint (in production, this comes from live data)
        fingerprint = generate_mock_fingerprint(symbol)
        
        # Display spectrum breakdown
        print(f"\n🎯 {symbol}")
        print(f"   Bot Class: {fingerprint.bot_class}")
        print(f"   Confidence: {fingerprint.confidence:.2%}")
        print(f"   Layering Score: {fingerprint.layering_score:.2f}")
        print(f"   Spectrum Breakdown:")
        
        for band in fingerprint.spectrum_results:
            bar_len = int(band.amplitude * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"      {band.band_name:<12} [{bar}] {band.dominant_freq:>10.3f} Hz  {band.state_description}")
        
        detected_bots.append(fingerprint)
        
        # Emit to ThoughtBus
        if bus:
            bus.think(
                f"Full Spectrum Scan: {symbol} = {fingerprint.bot_class}",
                topic="spectrum.scan",
                priority="high" if "HFT" in fingerprint.bot_class else "normal",
                metadata={"symbol": symbol, "class": fingerprint.bot_class}
            )
    
    print()
    print("🌍 PHASE 2: Cultural Attribution & Census Registration...")
    print("-" * 70)
    
    for fingerprint in detected_bots:
        # Attribute to firm
        firm_id = attribute_to_firm(fingerprint)
        
        # Generate bot UUID
        bot_uuid = hashlib.md5(
            f"{fingerprint.symbol}_{fingerprint.bot_class}_{firm_id}".encode()
        ).hexdigest()[:16]
        
        # Get strongest band
        strongest = max(fingerprint.spectrum_results, key=lambda x: x.amplitude)
        
        print(f"\n🤖 Bot Detected: {bot_uuid}")
        print(f"   Symbol: {fingerprint.symbol}")
        print(f"   Attributed Firm: {firm_id}")
        print(f"   Cultural Origin: {CULTURAL_ENTITIES.get(firm_id, {}).get('country', 'Unknown')}")
        print(f"   Spectrum Band: {strongest.band_name}")
        print(f"   Manipulation Risk: {'⚠️ HIGH' if fingerprint.layering_score > 0.7 else '✅ LOW'}")
        
        # Register in Census
        if census:
            entry = BotCensusEntry(
                bot_uuid=bot_uuid,
                firm_id=firm_id,
                cultural_origin=CULTURAL_ENTITIES.get(firm_id, {}).get('country', 'Unknown'),
                primary_spectrum_band=strongest.band_name,
                first_seen=time.time(),
                last_seen=time.time(),
                frequency_fingerprint=[b.dominant_freq for b in fingerprint.spectrum_results],
                shape_class=fingerprint.bot_class,
                manipulation_score=fingerprint.layering_score,
                status="ACTIVE"
            )
            census.register_or_update(entry)
            print(f"   📒 Registered in Bot Census")
    
    print()
    print("🏛️ PHASE 3: Deep Money Flow Evidence Check...")
    print("-" * 70)
    
    # Check vault for related historical events
    if vault:
        print(f"\n   Vault contains {len(vault.events)} historical manipulation events")
        
        # Add a sample event for demonstration
        sample_event = MoneyFlowEvent(
            event_id=f"EVT_{int(time.time())}",
            date=datetime.now().strftime("%Y-%m-%d"),
            event_name="Detected HFT Spoofing Pattern",
            perpetrators=["UNKNOWN_HFT"],
            beneficiaries=["Market Makers"],
            victims=["Retail Traders"],
            attributed_bots=[detected_bots[0].bot_class if detected_bots else "N/A"],
            manipulation_vector="SPOOFING",
            amount_extracted_usd=random.uniform(10000, 100000),
            extraction_method="Layered Order Book Manipulation",
            flow_direction="retail_to_institution",
            source_location="Global Retail",
            destination_location="Institutional Accounts",
            intermediaries=["Exchange"],
            stated_reason="Liquidity Provision",
            actual_reason="Price Manipulation",
            short_term_effects=["Price Spike", "Retail Liquidations"],
            long_term_effects=["Market Distrust"],
            planetary_effects=["wealth_concentration"],
            evidence_sources=["Full Spectrum Scan", "Order Book Analysis"],
            confidence=0.85
        )
        vault.add_event(sample_event)
        print(f"   📜 Logged new manipulation evidence: {sample_event.event_id}")
    
    print()
    print("👑 PHASE 4: Queen Hive Mind Integration...")
    print("-" * 70)
    
    # Summarize for Queen
    if QUEEN_OK:
        print("\n   🐝 Preparing intelligence briefing for Queen...")
        
        for fingerprint in detected_bots:
            strongest = max(fingerprint.spectrum_results, key=lambda x: x.amplitude)
            firm_id = attribute_to_firm(fingerprint)
            
            # Decision logic
            if strongest.band_name == "ULTRA_HIGH" and fingerprint.layering_score > 0.7:
                action = "🚫 AVOID - Quantum HFT territory, too fast for us"
            elif strongest.band_name == "INFRA_LOW":
                action = "🐋 FOLLOW THE WHALE - Accumulation detected"
            elif fingerprint.layering_score < 0.5:
                action = "✅ SAFE ENTRY - Low manipulation risk"
            else:
                action = "⚠️ CAUTION - Monitor before entry"
            
            print(f"\n   📋 {fingerprint.symbol}")
            print(f"      Detected: {fingerprint.bot_class} ({firm_id})")
            print(f"      Queen's Guidance: {action}")
            
            # Emit to ThoughtBus for Queen
            if bus:
                bus.think(
                    f"Queen Guidance: {fingerprint.symbol} -> {action}",
                    topic="queen.guidance",
                    priority="critical",
                    metadata={
                        "symbol": fingerprint.symbol,
                        "action": action,
                        "firm": firm_id,
                        "bot_class": fingerprint.bot_class
                    }
                )
    
    print()
    print("🐋 PHASE 5: Orca/Whale Detection Summary...")
    print("-" * 70)
    
    whale_bots = [f for f in detected_bots if f.bot_class == "WHALE_ACCUMULATOR"]
    hft_bots = [f for f in detected_bots if "HFT" in f.bot_class or "QUANTUM" in f.bot_class]
    mm_bots = [f for f in detected_bots if "MAKER" in f.bot_class]
    
    print(f"\n   🐋 Whales Detected (INFRA_LOW): {len(whale_bots)}")
    for w in whale_bots:
        print(f"      - {w.symbol}: Deep Ocean accumulation pattern")
    
    print(f"\n   ⚡ HFT/Quantum Bots (ULTRA_HIGH): {len(hft_bots)}")
    for h in hft_bots:
        print(f"      - {h.symbol}: Operating at {max(h.spectrum_results, key=lambda x: x.amplitude).dominant_freq:.0f} Hz")
    
    print(f"\n   🏄 Market Makers (MID_RANGE): {len(mm_bots)}")
    for m in mm_bots:
        print(f"      - {m.symbol}: Surface wave pattern")
    
    print()
    print("=" * 70)
    print("🎯 TRADE SETUP RECOMMENDATIONS")
    print("=" * 70)
    
    for fingerprint in detected_bots:
        strongest = max(fingerprint.spectrum_results, key=lambda x: x.amplitude)
        firm = attribute_to_firm(fingerprint)
        
        print(f"\n📊 {fingerprint.symbol}")
        print(f"   Dominant Actor: {firm}")
        print(f"   Operating Band: {strongest.band_name} ({strongest.dominant_freq:.3f} Hz)")
        
        # Trade setup logic
        if fingerprint.bot_class == "WHALE_ACCUMULATOR":
            print(f"   🎯 SETUP: LONG - Follow whale accumulation")
            print(f"      Entry: Market order on pullback")
            print(f"      Size: Small (piggyback, don't front-run)")
            print(f"      Timing: Wait for 3rd validation pass")
        elif "HFT" in fingerprint.bot_class or "QUANTUM" in fingerprint.bot_class:
            print(f"   🎯 SETUP: AVOID - HFT dominance")
            print(f"      Reason: Latency disadvantage")
            print(f"      Alternative: Wait for regime change")
        elif fingerprint.bot_class == "MARKET_MAKER":
            print(f"   🎯 SETUP: RANGE TRADE - MM territory")
            print(f"      Entry: Buy support, sell resistance")
            print(f"      Size: Medium")
            print(f"      Timing: Use limit orders only")
        else:
            print(f"   🎯 SETUP: NEUTRAL - Gather more data")
    
    print()
    print("=" * 70)
    print("✅ FULL SPECTRUM FLOW TEST COMPLETE")
    print("=" * 70)
    
    # Final stats
    if census:
        print(f"\n📊 Bot Census: {len(census.registry)} bots registered")
    if vault:
        print(f"📜 Money Flow Vault: {len(vault.events)} events logged")
    if bus:
        print(f"🧠 ThoughtBus: Active and flowing")
    
    print("\n🌌 The Queen sees all. No stone unturned. 👑")

if __name__ == "__main__":
    main()
