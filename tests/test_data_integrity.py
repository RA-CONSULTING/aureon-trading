#!/usr/bin/env python3
"""
Test data integrity for quantum frog system.
"""
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from queen_eternal_machine import QueenEternalMachine

def test_data_integrity():
    # Initialize the quantum frog system
    queen = QueenEternalMachine(dry_run=True)

    print('🔍 TESTING DATA INTEGRITY')
    print('=' * 50)

    # Check if friends loaded correctly with real cost basis
    print('👥 FRIEND COST BASIS VERIFICATION:')
    for symbol, friend in list(queen.friends.items())[:5]:  # Show first 5
        print(f'   {symbol}:')
        print(f'     Quantity: {friend.quantity:.6f}')
        print(f'     Cost Basis: ${friend.cost_basis:.4f}')
        print(f'     Entry Price: ${friend.entry_price:.4f}')
        print(f'     Current Value: ${friend.current_value:.2f}')
        print(f'     Baggage: ${friend.baggage:.2f}')
        print(f'     Is Clear: {friend.is_clear}')
        print()

    # Test market data fetching
    print('📊 MARKET DATA TEST:')
    queen.fetch_market_data()
    if 'ADA' in queen.market_data:
        ada = queen.market_data['ADA']
        print(f'   ADA: ${ada.price:.4f} ({ada.change_24h:+.2f}%)')
    if 'SOL' in queen.market_data:
        sol = queen.market_data['SOL']
        print(f'   SOL: ${sol.price:.4f} ({sol.change_24h:+.2f}%)')
    if 'SHIB' in queen.market_data:
        shib = queen.market_data['SHIB']
        print(f'   SHIB: ${shib.price:.6f} ({shib.change_24h:+.2f}%)')
    print()

    # Test leap opportunity detection with a small sample
    print('🎯 LEAP OPPORTUNITY DETECTION TEST:')
    opportunities = queen.find_leap_opportunities()
    print(f'   Found {len(opportunities)} opportunities')

    if opportunities:
        # Show details of first opportunity
        opp = opportunities[0]
        print(f'   Sample Opportunity:')
        print(f'     {opp.from_symbol} → {opp.to_symbol}')
        print(f'     Gross Value: ${opp.gross_value:.2f}')
        print(f'     Fee-adjusted Multiplier: {opp.fee_adjusted_multiplier:.3f}x')
        print(f'     Dip Advantage: {opp.dip_advantage:.1f}%')
        print(f'     Total Fees: ${opp.total_fees:.4f}')
        print(f'     Net Value After Fees: ${opp.net_value_after_fees:.2f}')
        print(f'     Profitable: {opp.is_profitable_after_fees}')

if __name__ == "__main__":
    test_data_integrity()