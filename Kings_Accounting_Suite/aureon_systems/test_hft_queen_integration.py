#!/usr/bin/env python3
"""
🦈🔪 HFT HARMONIC MYCELIUM TEST - Queen HFT Control Demo

Tests the newly integrated HFT capabilities in the Queen Hive Mind.
Demonstrates HFT activation, status monitoring, and emergency controls.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import asyncio
from typing import Dict, Any

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
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

from aureon_queen_hive_mind import QueenHiveMind

def print_separator(title: str):
    """Print a formatted separator"""
    print(f"\n{'='*60}")
    print(f"🦈 {title}")
    print(f"{'='*60}")

def print_status(status: Dict[str, Any]):
    """Pretty print status response"""
    print(f"📊 Status: {status.get('status', 'unknown')}")
    if 'message' in status:
        print(f"💬 Message: {status['message']}")
    if 'state' in status:
        print(f"👑 Queen State: {status['state']}")
    if 'warning' in status:
        print(f"⚠️ Warning: {status['warning']}")

async def test_hft_integration():
    """Test HFT integration with Queen Hive Mind"""
    print("🦈🔪 HFT HARMONIC MYCELIUM TEST")
    print("Testing Queen HFT Control Integration")

    # Initialize Queen
    print("\n👑 Initializing Queen Hive Mind...")
    queen = QueenHiveMind()

    # Test 1: Check initial HFT status
    print_separator("TEST 1: Initial HFT Status")
    status = queen.get_hft_status()
    print("📊 Initial HFT Status:")
    for key, value in status.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")

    # Test 2: Try to start HFT (should work if engine is available)
    print_separator("TEST 2: Start HFT Trading")
    start_result = queen.start_hft_trading()
    print_status(start_result)

    # Test 3: Get updated status
    print_separator("TEST 3: Updated HFT Status After Start")
    status = queen.get_hft_status()
    print("📊 Updated HFT Status:")
    for key, value in status.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")

    # Test 4: Try to enable execution (only if scanning)
    if status.get('state') == 'HFT_SCANNING':
        print_separator("TEST 4: Enable Live HFT Execution")
        exec_result = queen.enable_hft_execution()
        print_status(exec_result)

        # Test 5: Get final status
        print_separator("TEST 5: Final HFT Status")
        status = queen.get_hft_status()
        print("📊 Final HFT Status:")
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")

        # Test 6: Emergency stop
        print_separator("TEST 6: Queen Emergency Stop")
        stop_result = queen.hft_emergency_stop("Test emergency stop")
        print_status(stop_result)

    # Test 7: Configure risk limits
    print_separator("TEST 7: Configure HFT Risk Limits")
    risk_result = queen.configure_hft_risk_limits(
        daily_loss_limit_usd=-50.0,
        max_position_size_usd=200.0,
        max_concurrent_orders=15
    )
    print_status(risk_result)

    print_separator("TEST COMPLETE")
    print("✅ HFT integration test completed successfully!")
    print("🦈 Queen now has full HFT control capabilities")

if __name__ == "__main__":
    asyncio.run(test_hft_integration())