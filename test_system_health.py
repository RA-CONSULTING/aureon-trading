#!/usr/bin/env python3
"""
🏥 AUREON SYSTEM HEALTH CHECK
==============================
Quick validation that all core modules load and configs are valid.

Run: python test_system_health.py
"""

import sys
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# TEST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

CORE_MODULES = [
    "aureon_unified_ecosystem",
    "aureon_brain",
    "aureon_miner_brain",
    "aureon_mycelium",
    "aureon_harmonic_underlay",
    "aureon_probability_nexus",
    "irish_patriot_scouts",
    "ira_sniper_mode",
]

CLIENT_MODULES = [
    ("binance_client", "BinanceClient"),
    ("kraken_client", "KrakenClient"),
    ("capital_client", "CapitalClient"),
    ("alpaca_client", "AlpacaClient"),
]

REQUIRED_ENV_VARS = [
    "BINANCE_API_KEY",
    "BINANCE_SECRET_KEY",
    "KRAKEN_API_KEY",
    "KRAKEN_API_SECRET",
]

# ═══════════════════════════════════════════════════════════════════════════
# TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def test_core_imports():
    """Test that all core modules import without error."""
    print("\n📦 CORE MODULE IMPORTS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for module in CORE_MODULES:
        try:
            __import__(module)
            print(f"  ✅ {module}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            failed += 1
    
    return passed, failed


def test_client_imports():
    """Test that exchange clients import and have expected classes."""
    print("\n🔌 EXCHANGE CLIENT IMPORTS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for module_name, class_name in CLIENT_MODULES:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"  ✅ {module_name}.{class_name}")
                passed += 1
            else:
                print(f"  ⚠️  {module_name} imported but {class_name} not found")
                failed += 1
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed += 1
    
    return passed, failed


def test_env_vars():
    """Check that required environment variables are set."""
    print("\n🔐 ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    # Load .env if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    passed = 0
    failed = 0
    
    for var in REQUIRED_ENV_VARS:
        value = os.environ.get(var)
        if value:
            # Show first/last 4 chars only for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            print(f"  ✅ {var} = {masked}")
            passed += 1
        else:
            print(f"  ❌ {var} not set")
            failed += 1
    
    return passed, failed


def test_battlefield_config():
    """Verify BATTLEFIELDS configuration is valid."""
    print("\n⚔️  BATTLEFIELD CONFIGURATION")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    try:
        from aureon_unified_ecosystem import CONFIG
        
        battlefields = CONFIG.get('BATTLEFIELDS', {})
        multi_mode = CONFIG.get('MULTI_BATTLEFIELD_MODE', False)
        
        print(f"  MULTI_BATTLEFIELD_MODE: {multi_mode}")
        
        if not battlefields:
            print("  ⚠️  BATTLEFIELDS not configured")
            return 0, 1
        
        required_keys = ["enabled", "sniper_active", "harvester_active"]
        
        for exchange, config in battlefields.items():
            missing = [k for k in required_keys if k not in config]
            if missing:
                print(f"  ❌ {exchange}: missing keys {missing}")
                failed += 1
            else:
                status = "🟢" if config.get("enabled") else "⚪"
                scouts = config.get("scouts_per_exchange", 0)
                sniper = "N" if config.get("sniper_active") else "-"
                harvester = "H" if config.get("harvester_active") else "-"
                print(f"  {status} {exchange:12} [S:{scouts} {sniper}{harvester}]")
                passed += 1
                
    except ImportError as e:
        print(f"  ❌ Could not import CONFIG: {e}")
        failed += 1
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        failed += 1
    
    return passed, failed


def test_version():
    """Check version is defined."""
    print("\n📌 VERSION INFO")
    print("=" * 50)
    
    try:
        # Read version from file
        with open("aureon_unified_ecosystem.py", "r") as f:
            content = f.read(500)
            if "Version:" in content:
                # Extract version line
                for line in content.split("\n"):
                    if "Version:" in line:
                        print(f"  ✅ {line.strip()}")
                        return 1, 0
        print("  ⚠️  No version found in module")
        return 0, 1
    except Exception as e:
        print(f"  ❌ {e}")
        return 0, 1


def test_json_configs():
    """Check that JSON config files are valid."""
    print("\n📄 JSON CONFIG FILES")
    print("=" * 50)
    
    import json
    
    json_files = [
        "auris_runtime.json",
        "aureon_kraken_state.json",
        "calibration_trades.json",
    ]
    
    passed = 0
    failed = 0
    
    for filename in json_files:
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    json.load(f)
                print(f"  ✅ {filename}")
                passed += 1
            except json.JSONDecodeError as e:
                print(f"  ❌ {filename}: Invalid JSON - {e}")
                failed += 1
        else:
            print(f"  ⚪ {filename} (not found, optional)")
    
    return passed, failed


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("🏥 AUREON SYSTEM HEALTH CHECK")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    tests = [
        test_version,
        test_core_imports,
        test_client_imports,
        test_env_vars,
        test_battlefield_config,
        test_json_configs,
    ]
    
    for test in tests:
        passed, failed = test()
        total_passed += passed
        total_failed += failed
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"  ✅ Passed: {total_passed}")
    print(f"  ❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL CHECKS PASSED - System ready for beta testing!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} issues found - review before going live")
        return 1


if __name__ == "__main__":
    sys.exit(main())
