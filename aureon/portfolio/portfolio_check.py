#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Windows UTF-8 wrapper

from aureon.queen.queen_eternal_machine import QueenEternalMachine

queen = QueenEternalMachine(dry_run=True)

print("🎯 PORTFOLIO VALUATION VERIFICATION")
print("=" * 50)
print(f'Total vault: ${queen.total_portfolio_value:.2f}')
print(f'Total position value: ${sum(f.current_value for f in queen.friends.values()):.2f}')
print(f'Total baggage: ${sum(f.baggage for f in queen.friends.values()):.2f}')
print(f'Cash balance: ${queen.cash_balance:.2f}')
print(f'Clear friends: {sum(1 for f in queen.friends.values() if f.is_clear)}/{len(queen.friends)}')

print("\n📊 SAMPLE FRIENDS WITH REAL COST BASIS:")
for symbol, friend in list(queen.friends.items())[:5]:
    if friend.cost_basis > 0 and friend.entry_price != 1.0:
        print(f"  {symbol}: {friend.quantity:.6f} @ ${friend.entry_price:.4f} = ${friend.cost_basis:.2f} → ${friend.current_value:.2f}")