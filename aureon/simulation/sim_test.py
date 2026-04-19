#!/usr/bin/env python3
"""Quick simulation to test MIN_TRADE_USD = $1.44 before restarting live"""
from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
sys.path.insert(0, '.')

print('='*60)
print('🧪 SIMULATION: Testing MIN_TRADE_USD = $1.44')
print('='*60)

from aureon.trading.aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

print(f'\n📊 CONFIG VALUES:')
print(f'   MIN_TRADE_USD: ${CONFIG["MIN_TRADE_USD"]}')
print(f'   BINANCE_MIN_NOTIONAL: ${CONFIG["BINANCE_MIN_NOTIONAL"]}')
print(f'   KRAKEN_MIN_NOTIONAL: ${CONFIG["KRAKEN_MIN_NOTIONAL"]}')
print(f'   BASE_POSITION_SIZE: {CONFIG["BASE_POSITION_SIZE"]*100}%')
print(f'   MAX_POSITION_SIZE: {CONFIG["MAX_POSITION_SIZE"]*100}%')

# Initialize in dry run
print('\n🔄 Initializing ecosystem (DRY RUN)...')
eco = AureonKrakenEcosystem(initial_balance=160.0, dry_run=True)

print(f'\n💰 BALANCE SIMULATION (£160 starting):')
print(f'   Starting Balance: £{eco.tracker.balance:.2f}')

# Calculate position sizes at different % allocations
print('\n📐 POSITION SIZE vs MINIMUMS:')
for pct in [0.01, 0.02, 0.05, 0.10, 0.15]:
    size = eco.tracker.balance * pct
    binance_ok = '✅' if size >= CONFIG['BINANCE_MIN_NOTIONAL'] else '❌'
    kraken_ok = '✅' if size >= CONFIG['KRAKEN_MIN_NOTIONAL'] else '❌'
    min_ok = '✅' if size >= CONFIG['MIN_TRADE_USD'] else '❌'
    print(f'   {pct*100:5.1f}% = £{size:6.2f} | Min:{min_ok} Binance:{binance_ok} Kraken:{kraken_ok}')

# Find opportunities
print('\n🔍 Finding opportunities (this may take a moment)...')
try:
    eco.refresh_tickers()
    opps = eco.find_opportunities()
    print(f'   Found: {len(opps)} opportunities')

    if opps:
        print('\n🎯 TOP 10 OPPORTUNITIES:')
        for i, opp in enumerate(opps[:10], 1):
            sym = opp['symbol']
            score = opp['score']
            price = opp['price']
            exchange = opp.get('source', 'binance').lower()
            
            # Calculate what position size would be
            coh = opp.get('coherence', 0.5)
            pos_size = eco.tracker.balance * CONFIG['BASE_POSITION_SIZE'] * coh
            
            min_notional = CONFIG['BINANCE_MIN_NOTIONAL'] if 'binance' in exchange else CONFIG['KRAKEN_MIN_NOTIONAL']
            can_trade = '✅' if pos_size >= min_notional else f'❌ Need ${min_notional}'
            
            print(f'   {i:2}. {sym:12} | Score:{score:3.0f} | Coh:{coh:.2f} | Size:£{pos_size:5.2f} | {can_trade}')
    else:
        print('   ⚠️ No opportunities found')
    
    # Simple net profit sanity check for Binance taker fees/slippage
    print('\n🧮 NET PROFIT CHECK (Binance, taker):')
    tp = CONFIG['TAKE_PROFIT_PCT'] / 100.0
    fee = CONFIG['BINANCE_FEE_TAKER']
    slip = CONFIG['SLIPPAGE_PCT']
    spread = CONFIG['SPREAD_COST_PCT']
    round_trip_cost = (fee*2) + slip + spread
    net = tp - round_trip_cost
    print(f"   TP: {tp*100:.2f}% | Fees RT: {(fee*2)*100:.2f}% | Slippage: {slip*100:.2f}% | Spread: {spread*100:.2f}%")
    print(f"   ➜ Net expected: {net*100:.2f}% {'✅' if net>0 else '❌'}")
        
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n' + '='*60)
print('🏁 SIMULATION COMPLETE')
print('='*60)
print('\n💡 With $1.44 min, Binance trades should work at 1%+ position size')
print('   Kraken needs 3.3%+ position size ($5.25 min)')
