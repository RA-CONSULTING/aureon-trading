#!/usr/bin/env python
"""Check current Batten Matrix readings from live system."""
import json

# Try to read from global state if it exists
try:
    import aureon_probability_nexus
    state = getattr(aureon_probability_nexus, 'SUBSYSTEM_STATE', {})
    
    print('\n📊 BATTEN MATRIX - COHERENCE × LAMBDA × PROBABILITY READINGS:\n')
    print('=' * 80)
    
    if not state:
        print('\n⚠️  SUBSYSTEM_STATE is empty - system may still be initializing')
        print('    The Probability Nexus collects data over time before generating metrics.')
    else:
        print(f'\n✅ Found metrics for {len(state)} symbols:\n')
        
        for symbol, metrics in list(state.items())[:10]:
            clarity = metrics.get('avg_clarity', 0)
            coherence = metrics.get('avg_coherence', 0)
            chaos = metrics.get('chaos', 0)
            chaos_trend = metrics.get('chaos_trend', 'stable')
            price = metrics.get('latest_price', 0)
            
            # Calculate confidence (same as in make_predictions)
            confidence = (clarity / 5.0) * 0.5 + coherence * 0.5
            
            # Estimate lambda (stability) - inverse of chaos
            lambda_stability = max(0, 1 - chaos) if chaos > 0 else 0.5
            
            # Batten Matrix Score
            score = coherence * lambda_stability * confidence
            
            print(f'{symbol:12s}')
            print(f'  🌊 Coherence: {coherence:.4f}')
            print(f'  ⚡ Lambda:    {lambda_stability:.4f}')
            print(f'  🎲 Confidence: {confidence:.4f}')
            print(f'  📊 SCORE:     {score:.6f} {"🟢 PASS" if score >= 0.618 else "🔴 FAIL"}')
            print(f'  💎 Clarity: {clarity:.2f} | Chaos: {chaos:.4f} ({chaos_trend})')
            print()
    
    print('=' * 80)
    print('\n💡 Note: Batten Matrix requires Score ≥ 0.618 (φ golden ratio) for 4th pass execution')
    print('   Formula: Score = Coherence × Lambda × Confidence\n')
    
except Exception as e:
    print(f'\n❌ Error accessing Probability Nexus state: {e}')
    print('\n💡 The system may need more runtime to collect coherence/lambda metrics.')
    print('   These values build up as the scanner processes market data.\n')
