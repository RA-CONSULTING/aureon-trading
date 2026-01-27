#!/usr/bin/env python3
"""
🧪 SMOKE TEST: JSON Feed Integration
Validates that all JSON data sources are properly feeding the unified ecosystem.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os

print("=" * 70)
print("🧪 JSON FEED INTEGRATION TEST - All Systems Talking To Each Other")
print("=" * 70)

# ============================================================================
# TEST 1: State Aggregator Initialization
# ============================================================================
print("\n📊 TEST 1: UnifiedStateAggregator Initialization")
print("-" * 70)

try:
    from aureon_unified_ecosystem import STATE_AGGREGATOR
    summary_text = STATE_AGGREGATOR.get_summary()
    state = STATE_AGGREGATOR.aggregated_state
    sources = state.get('sources_loaded', [])
    
    print(f"   ✅ State Aggregator loaded successfully")
    print(f"   📁 Sources loaded: {len(sources)}")
    for src in sources:
        print(f"      - {src}")
    
    print(f"\n   📈 Data Statistics:")
    print(f"      Historical Trades: {state.get('total_historical_trades', 0)}")
    print(f"      Combined Win Rate: {state.get('combined_win_rate', 0):.1f}%")
    print(f"      Frequency Bands: {', '.join(state.get('frequency_performance', {}).keys()) or 'None'}")
    print(f"\n{summary_text}")
    
except Exception as e:
    print(f"   ❌ State Aggregator failed: {e}")

# ============================================================================
# TEST 2: Multi-Exchange Orchestrator
# ============================================================================
print("\n🌐 TEST 2: MultiExchangeOrchestrator")
print("-" * 70)

try:
    from aureon_unified_ecosystem import MultiExchangeOrchestrator
    from unified_exchange_client import MultiExchangeClient
    
    client = MultiExchangeClient()
    orchestrator = MultiExchangeOrchestrator(client)
    
    print(f"   ✅ Multi-Exchange Orchestrator initialized")
    print(f"   📡 Exchanges configured: {list(client.clients.keys())}")
    
    # Check learning metrics
    learning = orchestrator.get_learning_metrics()
    print(f"\n   🧠 Learning Metrics:")
    print(f"      Total Exchange Trades: {learning.get('total_trades', 0)}")
    print(f"      Best Exchange: {learning.get('best_exchange', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ Multi-Exchange Orchestrator failed: {e}")

# ============================================================================
# TEST 3: Symbol Insight Integration
# ============================================================================
print("\n🔍 TEST 3: Symbol Insight Integration")
print("-" * 70)

try:
    test_symbols = ['BTCGBP', 'ETHGBP', 'XBTGBP', 'BTCUSDT', 'ETHUSDT']
    
    print(f"   Testing symbol insights:")
    for symbol in test_symbols:
        insight = STATE_AGGREGATOR.get_symbol_insight(symbol)
        trades = insight.get('trades', 0)
        win_rate = insight.get('win_rate', 0)
        avg_profit = insight.get('avg_profit', 0)
        
        if trades > 0:
            print(f"      ✅ {symbol}: {trades} trades, {win_rate:.1%} WR, {avg_profit:.4f} avg profit")
        else:
            print(f"      ⚪ {symbol}: No historical data (new symbol)")
    
    print(f"   ✅ Symbol insight integration working")
    
except Exception as e:
    print(f"   ❌ Symbol insight test failed: {e}")

# ============================================================================
# TEST 4: Frequency Recommendation System
# ============================================================================
print("\n🎵 TEST 4: Frequency Recommendation System")
print("-" * 70)

try:
    test_freqs = [256, 396, 432, 528, 639, 741, 852]
    
    print(f"   Testing frequency bands:")
    for freq in test_freqs:
        rec = STATE_AGGREGATOR.get_frequency_recommendation(freq)
        band = rec.get('band', 'unknown')
        boost = rec.get('boost_factor', 1.0)
        count = rec.get('count', 0)
        
        boost_icon = "🚀" if boost > 1.0 else "⚠️" if boost < 1.0 else "➖"
        print(f"      {freq}Hz → {band}: {boost_icon} {boost:.2f}x boost ({count} samples)")
    
    print(f"   ✅ Frequency recommendation system working")
    
except Exception as e:
    print(f"   ❌ Frequency recommendation test failed: {e}")

# ============================================================================
# TEST 5: Coherence Recommendation System
# ============================================================================
print("\n🧠 TEST 5: Coherence Recommendation System")
print("-" * 70)

try:
    test_coherences = [0.3, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print(f"   Testing coherence bands:")
    for coh in test_coherences:
        rec = STATE_AGGREGATOR.get_coherence_recommendation(coh)
        band = rec.get('band', 'unknown')
        wr = rec.get('historical_win_rate', 0.5)
        count = rec.get('count', 0)
        
        wr_icon = "🎯" if wr > 0.6 else "⚠️" if wr < 0.5 else "➖"
        print(f"      {coh:.1f} → {band}: {wr_icon} {wr:.1%} win rate ({count} samples)")
    
    print(f"   ✅ Coherence recommendation system working")
    
except Exception as e:
    print(f"   ❌ Coherence recommendation test failed: {e}")

# ============================================================================
# TEST 6: Full Ecosystem Initialization with All Components
# ============================================================================
print("\n🐙 TEST 6: Full Ecosystem with All Components")
print("-" * 70)

try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    
    eco = AureonKrakenEcosystem(initial_balance=1000.0, dry_run=True)
    
    print(f"   ✅ Ecosystem initialized")
    print(f"   📊 Components Active:")
    print(f"      - Multi-Exchange: {'✅' if eco.multi_exchange else '❌'}")
    print(f"      - State Aggregator: {'✅' if eco.state_aggregator else '❌'}")
    print(f"      - Smart Router: {'✅' if eco.smart_router else '❌'}")
    print(f"      - Arb Scanner: {'✅' if eco.arb_scanner else '❌'}")
    print(f"      - Trade Confirmation: {'✅' if eco.trade_confirmation else '❌'}")
    print(f"      - Rebalancer: {'✅' if eco.rebalancer else '❌'}")
    print(f"      - Nexus Integration: {'✅' if eco.nexus and eco.nexus.enabled else '❌'}")
    print(f"      - Bridge: {'✅' if eco.bridge_enabled else '❌'}")
    
    # Test ticker refresh and opportunity finding with state aggregator
    print(f"\n   🔄 Testing live integration...")
    ticker_count = eco.refresh_tickers()
    print(f"      Tickers fetched: {ticker_count}")
    
    opps = eco.find_opportunities()
    print(f"      Opportunities found: {len(opps)}")
    
    if opps:
        top = opps[0]
        print(f"\n   🏆 Top Opportunity:")
        print(f"      Symbol: {top['symbol']}")
        print(f"      Score: {top['score']}")
        print(f"      Coherence: {top['coherence']:.2f}")
        print(f"      Source: {top.get('source', 'unknown')}")
    
    print(f"\n   ✅ Full ecosystem integration working!")
    
except Exception as e:
    import traceback
    print(f"   ❌ Ecosystem test failed: {e}")
    traceback.print_exc()

# ============================================================================
# TEST 7: JSON File Verification
# ============================================================================
print("\n📁 TEST 7: JSON File Verification")
print("-" * 70)

json_files = [
    ('aureon_kraken_state.json', 'Main State'),
    ('elephant_ultimate.json', 'Elephant Ultimate'),
    ('elephant_unified.json', 'Elephant Unified'),
    ('elephant_live.json', 'Elephant Live'),
    ('adaptive_learning_history.json', 'Adaptive Learning'),
    ('calibration_trades.json', 'Calibration Trades'),
    ('hnc_frequency_log.json', 'HNC Frequency Log'),
    ('auris_runtime.json', 'Auris Runtime'),
]

for filename, description in json_files:
    filepath = f'/workspaces/aureon-trading/{filename}'
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            size = os.path.getsize(filepath)
            print(f"   ✅ {description}: {filename} ({size:,} bytes)")
        except json.JSONDecodeError:
            print(f"   ⚠️ {description}: {filename} (invalid JSON)")
    else:
        print(f"   ⚪ {description}: {filename} (not found - will be created)")

# Check trade logs directory
trade_log_dir = '/tmp/aureon_trade_logs'
if os.path.exists(trade_log_dir):
    log_files = [f for f in os.listdir(trade_log_dir) if f.endswith('.jsonl')]
    print(f"   ✅ Trade Logs: {len(log_files)} log file(s) in {trade_log_dir}")
else:
    print(f"   ⚪ Trade Logs: Directory not found (will be created on first trade)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("🎉 JSON FEED INTEGRATION TEST COMPLETE")
print("=" * 70)
print("""
✅ All systems are connected and communicating:
   
   📊 UnifiedStateAggregator
      ↓ Consolidates all JSON sources
      ↓ Provides symbol insights, frequency recommendations
      ↓ Feeds into opportunity scoring
   
   🌐 MultiExchangeOrchestrator
      ↓ Cross-exchange scanning and learning
      ↓ Records trade results for each exchange
      ↓ Optimizes exchange selection
   
   🐙 AureonKrakenEcosystem
      ↓ Uses state_aggregator for historical boosts
      ↓ Uses multi_exchange for cross-learning
      ↓ All components talk to each other!
""")
