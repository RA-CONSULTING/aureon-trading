#!/usr/bin/env python3
"""
Debug why the frog isn't leaping - check leap opportunities.
"""

import sys
import os
import logging
from datetime import datetime

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

from queen_eternal_machine import QueenEternalMachine, MainPosition

# Initialize with XRP
frog = QueenEternalMachine(initial_vault=100.0)
frog.fetch_market_data()

if 'XRP' in frog.market_data:
    xrp_coin = frog.market_data['XRP']
    xrp_qty = 100.0 / xrp_coin.price
    frog.main_position = MainPosition(
        symbol='XRP',
        quantity=xrp_qty,
        cost_basis=100.0,
        entry_price=xrp_coin.price,
        entry_time=datetime.now()
    )
    frog.available_cash = 0.0
    
    logger.info(f"🐸 Starting position: {xrp_qty:.2f} XRP @ ${xrp_coin.price:.4f}")
    logger.info(f"   XRP 24h change: {xrp_coin.change_24h:+.2f}%")
    
    # Find leap opportunities
    opportunities = frog.find_leap_opportunities()
    
    logger.info(f"\n📊 Found {len(opportunities)} leap opportunities:")
    for i, opp in enumerate(opportunities[:10], 1):  # Show top 10
        logger.info(f"\n   #{i}: {opp.from_symbol} → {opp.to_symbol}")
        logger.info(f"      Dip advantage: {opp.dip_advantage:+.2f}%")
        logger.info(f"      From {opp.from_symbol} ({opp.from_change:+.2f}%) to {opp.to_symbol} ({opp.to_change:+.2f}%)")
        logger.info(f"      Quantity multiplier: {opp.quantity_multiplier:.4f}x")
        logger.info(f"      Fee-adjusted multiplier: {opp.fee_adjusted_multiplier:.4f}x")
        logger.info(f"      Total fees: ${opp.total_fees:.4f}")
        logger.info(f"      Is profitable: {opp.is_profitable_after_fees}")
else:
    logger.error("❌ XRP not found in market")
