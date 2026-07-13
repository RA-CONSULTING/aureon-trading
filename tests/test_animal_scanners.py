#!/usr/bin/env python3
"""Quick test of animal momentum scanners."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
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
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

from aureon_animal_momentum_scanners import (
    AlpacaSwarmOrchestrator,
    AlpacaLoneWolf,
    AlpacaLionHunt,
    AlpacaArmyAnts,
    AlpacaHummingbird
)
from aureon_alpaca_scanner_bridge import AlpacaScannerBridge
from alpaca_client import AlpacaClient

def main():
    print("🧪 Testing Animal Momentum Scanners\n")
    
    # Initialize clients
    print("1️⃣ Initializing Alpaca client...")
    alpaca = AlpacaClient()
    
    print("2️⃣ Initializing scanner bridge...")
    bridge = AlpacaScannerBridge(
        alpaca_client=alpaca,
        fee_tracker=None,
        enable_sse=False,
        enable_stocks=False
    )
    
    print("3️⃣ Creating animal scanners...\n")
    
    # Test Wolf
    print("🐺 WOLF (Momentum Sniper)")
    wolf = AlpacaLoneWolf(alpaca, bridge)
    wolf_targets = wolf.find_targets(limit=3)
    print(f"   Found {len(wolf_targets)} targets")
    for t in wolf_targets[:3]:
        print(f"   - {t.symbol} {t.side}: move={t.move_pct:+.2f}% net={t.net_pct:.3f}% ({t.reason})")
    
    # Test Lion
    print("\n🦁 LION (Multi-Target Hunter)")
    lion = AlpacaLionHunt(alpaca, bridge)
    lion_targets = lion.hunt(limit=3)
    print(f"   Found {len(lion_targets)} targets")
    for t in lion_targets[:3]:
        print(f"   - {t.symbol} {t.side}: move={t.move_pct:+.2f}% net={t.net_pct:.3f}% ({t.reason})")
    
    # Test Ants
    print("\n🐜 ANTS (Small-Profit Foragers)")
    ants = AlpacaArmyAnts(alpaca, bridge)
    ants_targets = ants.forage(max_targets=3)
    print(f"   Found {len(ants_targets)} targets")
    for t in ants_targets[:3]:
        print(f"   - {t.symbol} {t.side}: move={t.move_pct:+.2f}% net={t.net_pct:.3f}% ({t.reason})")
    
    # Test Hummingbird
    print("\n🐦 HUMMINGBIRD (Micro-Rotation)")
    hummingbird = AlpacaHummingbird(alpaca, bridge)
    hummingbird_targets = hummingbird.pollinate(limit=3)
    print(f"   Found {len(hummingbird_targets)} targets")
    for t in hummingbird_targets[:3]:
        print(f"   - {t.symbol} {t.side}: move={t.move_pct:+.2f}% net={t.net_pct:.3f}% ({t.reason})")
    
    # Test Orchestrator
    print("\n🎯 SWARM ORCHESTRATOR")
    swarm = AlpacaSwarmOrchestrator(alpaca, bridge)
    swarm.dry_run = True
    
    print("   Running orchestration cycle...")
    results = swarm.run_once()
    total = sum(len(v) for v in results.values())
    print(f"   Total opportunities: {total}")
    
    best = swarm.get_best_opportunity()
    if best:
        print(f"\n✨ BEST OPPORTUNITY:")
        print(f"   {best.symbol} {best.side} ({best.agent})")
        print(f"   Move: {best.move_pct:+.2f}% → Net: {best.net_pct:.3f}%")
        print(f"   Score: {best.score:.4f}")
        print(f"   Volume: {best.volume:,.0f}")
    else:
        print("\n   No opportunities above threshold")
    
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    main()
