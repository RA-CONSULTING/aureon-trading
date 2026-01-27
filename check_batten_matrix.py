#!/usr/bin/env python
"""Check Batten Matrix coherence × lambda × probability readings."""
from aureon_probability_nexus import EnhancedProbabilityNexus
import asyncio

async def check_nexus():
    nexus = EnhancedProbabilityNexus()
    
    # Check current state
    state = nexus.get_current_state()
    
    print('\n📊 PROBABILITY NEXUS - COHERENCE × LAMBDA × PROBABILITY:\n')
    print('=' * 70)
    print(f'\n🎯 Win rate: {state.get("win_rate", 0):.2%}')
    print(f'🎲 Confidence: {state.get("confidence", 0):.4f}')
    print(f'🌊 Avg Coherence: {state.get("avg_coherence", 0):.4f}')
    print(f'⚡ Lambda (stability): {state.get("lambda", 0):.4f}')
    print(f'💎 Clarity: {state.get("clarity", 0):.4f}')
    print(f'📈 Chaos: {state.get("chaos", 0):.4f}')
    print(f'\n📊 Total predictions: {state.get("total_predictions", 0)}')
    print(f'✅ Correct predictions: {state.get("correct_predictions", 0)}')
    
    print(f'\n🔢 BATTEN MATRIX FORMULA:')
    print(f'   Score = Coherence × Lambda × Confidence')
    coherence = state.get("avg_coherence", 0)
    lambda_val = state.get("lambda", 0)
    conf = state.get("confidence", 0)
    score = coherence * lambda_val * conf
    print(f'   Score = {coherence:.4f} × {lambda_val:.4f} × {conf:.4f} = {score:.6f}')
    print(f'\n   Threshold for execution: 0.618 (Golden Ratio)')
    print(f'   Current score: {"🟢 PASS" if score >= 0.618 else "🔴 FAIL"} ({score:.4f})')
    
    print(f'\n{"=" * 70}\n')
    return state

if __name__ == "__main__":
    result = asyncio.run(check_nexus())
