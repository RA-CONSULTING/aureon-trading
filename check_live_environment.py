#!/usr/bin/env python3
"""Quick validation script to ensure Aureon live trading environment is ready."""
import os, sys, json

def check(label, condition, required=True):
    status = "✅" if condition else ("❌" if required else "⚠️ ")
    print(f"{status} {label}")
    return condition

def main():
    print("\n" + "="*80)
    print("AUREON LIVE TRADING - ENVIRONMENT CHECK")
    print("="*80 + "\n")
    
    all_ok = True
    
    # 1. Python version
    print("📦 Python Environment")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    all_ok &= check(f"  Python {py_ver}", sys.version_info >= (3, 8))
    
    # 2. Required packages
    print("\n📚 Dependencies")
    try:
        import requests
        all_ok &= check("  requests", True)
    except ImportError:
        all_ok &= check("  requests", False)
    
    try:
        import dotenv
        all_ok &= check("  python-dotenv", True)
    except ImportError:
        all_ok &= check("  python-dotenv", False)
    
    # 3. Environment files
    print("\n📄 Configuration Files")
    all_ok &= check("  .env.example exists", os.path.exists('.env.example'))
    env_exists = os.path.exists('.env')
    all_ok &= check("  .env exists", env_exists, required=False)
    
    # 4. Module files
    print("\n🔧 Aureon Modules")
    all_ok &= check("  binance_client.py", os.path.exists('binance_client.py'))
    all_ok &= check("  binance_trade_sample.py", os.path.exists('binance_trade_sample.py'))
    all_ok &= check("  binance_get_address.py", os.path.exists('binance_get_address.py'))
    all_ok &= check("  aureon_live.py", os.path.exists('aureon_live.py'))
    
    # 5. Documentation
    print("\n📖 Documentation")
    all_ok &= check("  SECURITY_TRADING.md", os.path.exists('SECURITY_TRADING.md'))
    all_ok &= check("  LIVE_TRADING_RUNBOOK.md", os.path.exists('LIVE_TRADING_RUNBOOK.md'))
    
    # 6. Environment variables (if .env exists)
    if env_exists:
        print("\n🔐 Environment Variables (.env)")
        from dotenv import dotenv_values
        env = dotenv_values('.env')
        has_key = 'BINANCE_API_KEY' in env and env['BINANCE_API_KEY'] and len(env['BINANCE_API_KEY']) > 0
        has_secret = 'BINANCE_API_SECRET' in env and env['BINANCE_API_SECRET'] and len(env['BINANCE_API_SECRET']) > 0
        check("  BINANCE_API_KEY set", has_key, required=False)
        check("  BINANCE_API_SECRET set", has_secret, required=False)
        testnet = env.get('BINANCE_USE_TESTNET', 'true').lower() == 'true'
        dry_run = env.get('BINANCE_DRY_RUN', 'true').lower() == 'true'
        print(f"  Testnet mode: {testnet}")
        print(f"  Dry-run mode: {dry_run}")
    else:
        print("\n⚠️  .env file not found. Copy from .env.example:")
        print("  cp .env.example .env")
        print("  # Edit .env and add your Binance API credentials")
    
    # 7. Git safety
    print("\n🔒 Security (.gitignore)")
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
            check("  .env in .gitignore", '.env' in gitignore)
            check("  *.env in .gitignore", '*.env' in gitignore)
    
    # Summary
    print("\n" + "="*80)
    if all_ok:
        print("✅ All required checks passed! Ready for Stage 0.")
        print("\nNext steps:")
        print("  1. Edit .env with NEW Binance API keys (not the exposed ones)")
        print("  2. python aureon_live.py --stage 0 --symbol BTCUSDT")
        print("\nFor details, see LIVE_TRADING_RUNBOOK.md")
    else:
        print("❌ Some checks failed. Fix issues above before proceeding.")
        print("\nCommon fixes:")
        print("  pip install -r requirements.txt")
        print("  cp .env.example .env")
        sys.exit(1)
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
