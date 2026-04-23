#!/usr/bin/env python3
"""
Test the Quantum Frog with XRP - Force active trading to demonstrate leaps.
"""

import sys
import os
import json
import logging
from datetime import datetime

# UTF-8 Windows fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-5s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

from queen_eternal_machine import QueenEternalMachine, MainPosition
import asyncio

async def test_xrp_frog():
    """Test the quantum frog with XRP."""
    
    logger.info("🐸 QUANTUM FROG XRP TEST")
    logger.info("=" * 70)
    
    # Initialize with fresh state
    frog = QueenEternalMachine(initial_vault=100.0)
    frog.dry_run = False  # LIVE MODE (but we won't execute, just simulate)
    frog.demo_mode = True
    
    logger.info(f"💰 Starting vault: ${frog.initial_vault:.2f}")
    logger.info(f"📊 Bread crumb: {frog.breadcrumb_percent*100:.1f}%")
    logger.info(f"🔀 Min dip advantage: {frog.min_dip_advantage*100:.2f}%")
    
    # START WITH XRP to trigger leaps
    frog.fetch_market_data()
    if 'XRP' in frog.market_data:
        xrp_coin = frog.market_data['XRP']
        xrp_qty = 100.0 / xrp_coin.price  # Spend all $100 on XRP
        frog.main_position = MainPosition(
            symbol='XRP',
            quantity=xrp_qty,
            cost_basis=100.0,
            entry_price=xrp_coin.price,
            entry_time=datetime.now()
        )
        frog.available_cash = 0.0
        logger.info(f"\n✅ Started with {xrp_qty:.2f} XRP @ ${xrp_coin.price:.4f}")
    else:
        logger.warning("❌ XRP not found in market data!")
        return False
    
    logger.info("\n🔄 Running 10 aggressive leap cycles...")
    logger.info("=" * 70)
    
    leap_count = 0
    for cycle in range(10):
        stats = await frog.run_cycle()
        
        # Count leaps
        if frog.total_leaps > leap_count:
            leap_count = frog.total_leaps
            logger.info(f"\n✨ LEAP #{leap_count} EXECUTED!")
        
        # Show every cycle
        if frog.main_position:
            logger.info(f"   Main: {frog.main_position.symbol} | Qty: {frog.main_position.quantity:.2f} | Value: ${frog.main_position.current_value:.2f}")
        
        if frog.breadcrumbs:
            crumb_val = sum(c.current_value for c in frog.breadcrumbs.values())
            logger.info(f"   Breadcrumbs: {len(frog.breadcrumbs)} positions | Total: ${crumb_val:.2f}")
        
        # Await between cycles
        await asyncio.sleep(2)
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 FINAL REPORT:")
    logger.info("=" * 70)
    
    report = frog.get_full_report()
    logger.info(f"Total Vault Value: ${report['total_value']:.2f}")
    logger.info(f"Total P&L: ${report['total_pnl']:+.2f} ({report['total_pnl_percent']:+.2f}%)")
    logger.info(f"Total Leaps Made: {report['statistics']['total_leaps']}")
    logger.info(f"Total Breadcrumbs: {report['statistics']['total_breadcrumbs']}")
    logger.info(f"Total Cycles: {report['statistics']['total_cycles']}")
    
    if report['statistics']['total_leaps'] >= 5:
        logger.info("\n✅ SUCCESS! Frog is leaping actively!")
        return True
    else:
        logger.warning(f"\n⚠️ Only {report['statistics']['total_leaps']} leaps in 10 cycles - market may be flat")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_xrp_frog())
    sys.exit(0 if success else 1)
