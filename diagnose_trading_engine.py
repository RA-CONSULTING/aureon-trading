#!/usr/bin/env python3
"""
🔍 TRADING ENGINE DIAGNOSTIC TOOL
Helps diagnose why micro_profit_labyrinth.py might be exiting immediately on Windows
"""

import os
import sys
import subprocess
import time

def safe_print(*args, **kwargs):
    """Safe print that ignores I/O errors."""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass

def check_environment():
    """Check environment variables and API keys"""
    safe_print("\n" + "="*80)
    safe_print("🔍 STEP 1: Checking Environment Variables")
    safe_print("="*80)
    
    env_file = ".env"
    if os.path.exists(env_file):
        safe_print(f"✅ .env file found: {os.path.abspath(env_file)}")
    else:
        safe_print(f"❌ .env file NOT found: {os.path.abspath(env_file)}")
        safe_print("   💡 This might cause issues - create a .env file with your API keys")
        return False
    
    # Check for key variables
    from dotenv import load_dotenv
    load_dotenv()
    
    keys_to_check = [
        ("KRAKEN_API_KEY", "Kraken"),
        ("BINANCE_API_KEY", "Binance"),
        ("ALPACA_API_KEY", "Alpaca"),
    ]
    
    all_ok = True
    for key, name in keys_to_check:
        value = os.getenv(key)
        if value:
            safe_print(f"✅ {name} API key loaded")
        else:
            safe_print(f"⚠️  {name} API key missing (optional)")
    
    return True

def check_imports():
    """Check if required modules can be imported"""
    safe_print("\n" + "="*80)
    safe_print("🔍 STEP 2: Checking Python Imports")
    safe_print("="*80)
    
    modules_to_check = [
        "aiohttp",
        "ccxt",
        "dotenv",
        "matplotlib",
    ]
    
    all_ok = True
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            safe_print(f"✅ {module_name} available")
        except ImportError:
            safe_print(f"❌ {module_name} NOT available")
            safe_print(f"   💡 Install with: pip install {module_name}")
            all_ok = False
    
    return all_ok

def test_trading_engine_startup():
    """Try to start the trading engine with verbose output"""
    safe_print("\n" + "="*80)
    safe_print("🔍 STEP 3: Testing Trading Engine Startup")
    safe_print("="*80)
    safe_print("   Running: python micro_profit_labyrinth.py --dry-run --multi-exchange --duration 5")
    safe_print("="*80)
    
    try:
        # Set debug environment variable
        env = os.environ.copy()
        env["AUREON_DEBUG_STARTUP"] = "1"
        
        # Run the trading engine with a 5-second timeout
        result = subprocess.run(
            [sys.executable, "micro_profit_labyrinth.py", "--dry-run", "--multi-exchange", "--duration", "5"],
            env=env,
            capture_output=False,  # Let it print to console
            timeout=30  # 30 second hard timeout
        )
        
        safe_print("\n" + "="*80)
        if result.returncode == 0:
            safe_print(f"✅ Trading engine ran successfully (exit code: {result.returncode})")
            safe_print("   💡 The issue might be specific to how the game launcher runs it")
        else:
            safe_print(f"❌ Trading engine exited with code: {result.returncode}")
            safe_print("   💡 Check the error messages above for clues")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        safe_print("⚠️  Trading engine timeout (this is actually normal for duration=5)")
        return True
    except FileNotFoundError:
        safe_print("❌ micro_profit_labyrinth.py not found in current directory")
        safe_print(f"   Current directory: {os.getcwd()}")
        return False
    except Exception as e:
        safe_print(f"❌ Error running trading engine: {e}")
        return False

def main():
    safe_print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           🔍 AUREON TRADING ENGINE DIAGNOSTIC TOOL 🔍                      ║
║                                                                            ║
║   This tool will help diagnose why the trading engine might be            ║
║   exiting immediately on Windows.                                          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)
    
    safe_print(f"📂 Working directory: {os.getcwd()}\n")
    
    # Run checks
    env_ok = check_environment()
    imports_ok = check_imports()
    
    if not env_ok or not imports_ok:
        safe_print("\n" + "="*80)
        safe_print("⚠️  PREREQUISITE ISSUES FOUND")
        safe_print("="*80)
        safe_print("   Please fix the issues above before proceeding.")
        safe_print("   After fixing, run this diagnostic again.")
        return 1
    
    # Test actual startup
    engine_ok = test_trading_engine_startup()
    
    # Final summary
    safe_print("\n" + "="*80)
    safe_print("📊 DIAGNOSTIC SUMMARY")
    safe_print("="*80)
    safe_print(f"   Environment: {'✅ OK' if env_ok else '❌ ISSUES'}")
    safe_print(f"   Imports:     {'✅ OK' if imports_ok else '❌ ISSUES'}")
    safe_print(f"   Engine:      {'✅ OK' if engine_ok else '❌ ISSUES'}")
    safe_print("="*80)
    
    if env_ok and imports_ok and engine_ok:
        safe_print("\n✅ All checks passed! The trading engine should work.")
        safe_print("   If the game launcher still has issues, try:")
        safe_print("   1. Run the trading engine directly: python micro_profit_labyrinth.py --dry-run --multi-exchange")
        safe_print("   2. Check the game launcher log files in: %TEMP%\\aureon_service_logs\\")
        return 0
    else:
        safe_print("\n❌ Some checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
