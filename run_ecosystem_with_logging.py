#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🚀 AUREON UNIFIED ECOSYSTEM + COMPREHENSIVE LOGGING 🚀                           ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                   ║
║                                                                                      ║
║     Runs the unified ecosystem with full trade logging:                              ║
║       • Every trade entry/exit captured with metadata                                ║
║       • Probability matrix predictions validated against outcomes                    ║
║       • Market sweep completeness verified                                           ║
║       • Cross-exchange data collected for ML training                                ║
║                                                                                      ║
║     Usage:                                                                           ║
║       python3 run_ecosystem_with_logging.py                                          ║
║                                                                                      ║
║     Output Files:                                                                    ║
║       /tmp/aureon_trade_logs/trades_YYYYMMDD_HHMMSS.jsonl      - All entries        ║
║       /tmp/aureon_trade_logs/exits_YYYYMMDD_HHMMSS.jsonl       - All exits          ║
║       /tmp/aureon_trade_logs/validations_YYYYMMDD_HHMMSS.jsonl - Validations        ║
║       /tmp/aureon_trade_logs/market_sweep_YYYYMMDD_HHMMSS.jsonl - Sweeps            ║
║       /tmp/aureon_trade_logs/training_data_YYYYMMDD_HHMMSS.jsonl - ML ready         ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    
    print("\n" + "="*80)
    print("🚀 AUREON UNIFIED ECOSYSTEM + COMPREHENSIVE LOGGING".center(80))
    print("="*80)
    
    # Import ecosystem
    try:
        from aureon_unified_ecosystem import AureonKrakenEcosystem, TRADE_LOGGER_AVAILABLE
        logger.info("✅ Unified Ecosystem imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import ecosystem: {e}")
        sys.exit(1)
    
    # Verify trade logger is available
    if not TRADE_LOGGER_AVAILABLE:
        logger.warning("⚠️  Trade Logger not available - install trade_logger.py in workspace")
        sys.exit(1)
    
    logger.info("📊 Trade Logger is ACTIVE")
    
    # Show output directory
    output_dir = Path('/tmp/aureon_trade_logs')
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Trade logs directory: {output_dir}")
    
    # Initialize ecosystem
    try:
        engine = AureonKrakenEcosystem()
        logger.info("🐙 Unified Ecosystem initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ecosystem: {e}")
        sys.exit(1)
    
    # Show initial status
    print("\n" + "─"*80)
    print("📊 LOGGING CONFIGURATION".center(80))
    print("─"*80)
    
    try:
        from trade_logger import get_trade_logger
        trade_logger = get_trade_logger()
        
        summary = trade_logger.get_trade_summary()
        print(f"\n✅ Trade Logger Ready:")
        print(f"   📝 Trades file: {Path(summary['trades_file']).name}")
        print(f"   📤 Exits file: {Path(summary['exits_file']).name}")
        print(f"   ✔️  Validations file: {Path(summary['validations_file']).name}")
        print(f"   🌍 Market sweep file: {Path(summary['market_sweep_file']).name}")
        
    except Exception as e:
        logger.warning(f"Trade logger info unavailable: {e}")
    
    print("\n" + "─"*80)
    print("🎯 WHAT'S BEING LOGGED".center(80))
    print("─"*80)
    
    logging_items = [
        "✅ Every trade entry (price, quantity, coherence, HNC frequency)",
        "✅ Every trade exit (P&L, fees, hold time, reason)",
        "✅ Probability matrix predictions vs actual outcomes",
        "✅ Full market sweep data (opportunities found/rejected)",
        "✅ HNC frequency harmonics during each trade",
        "✅ Node distribution and gate effectiveness",
        "✅ Cross-exchange data for complete market analysis",
        "✅ All data exported in ML-friendly JSONL format",
    ]
    
    for item in logging_items:
        print(f"   {item}")
    
    print("\n" + "─"*80)
    print("🔄 RUNNING ECOSYSTEM WITH LOGGING ACTIVE".center(80))
    print("─"*80 + "\n")
    
    # Run ecosystem with logging
    try:
        # Set parameters
        interval_seconds = 5  # Check every 5 seconds
        target_profit_gbp = 50  # Stop at £50 profit
        max_runtime_minutes = 60  # Max 1 hour
        
        logger.info(f"🚀 Starting ecosystem...")
        logger.info(f"   ├─ Interval: {interval_seconds}s per cycle")
        logger.info(f"   ├─ Target Profit: £{target_profit_gbp}")
        logger.info(f"   └─ Max Runtime: {max_runtime_minutes} minutes")
        
        # Run the engine
        engine.run(
            interval=interval_seconds,
            target_profit_gbp=target_profit_gbp,
            max_minutes=max_runtime_minutes
        )
        
    except KeyboardInterrupt:
        logger.info("\n📋 Ecosystem interrupted by user")
    except Exception as e:
        logger.error(f"❌ Ecosystem error: {e}", exc_info=True)
    finally:
        # Generate final report
        logger.info("\n" + "="*80)
        logger.info("📊 GENERATING FINAL ANALYSIS REPORT".center(80))
        logger.info("="*80)
        
        try:
            from trade_analyzer import TradeDataAnalyzer
            from trade_logger import get_trade_logger
            
            tl = get_trade_logger()
            summary = tl.get_trade_summary()
            
            if summary['trades_file'] and Path(summary['trades_file']).exists():
                logger.info(f"\n✅ Analyzing trade data...")
                
                analyzer = TradeDataAnalyzer(
                    trades_file=summary['trades_file'],
                    exits_file=summary['exits_file'],
                    validations_file=summary.get('validations_file')
                )
                
                # Print summary
                analyzer.print_summary()
                
                # Generate report
                report_file = analyzer.generate_report()
                logger.info(f"\n💾 Report generated: {report_file}")
                
                # Export training data
                training_file = tl.export_training_data()
                logger.info(f"📚 Training data exported: {training_file}")
            else:
                logger.warning("No trade data available for analysis")
                
        except Exception as e:
            logger.warning(f"Analysis failed: {e}")
        
        logger.info("\n✅ Ecosystem shutdown complete")

if __name__ == '__main__':
    main()
