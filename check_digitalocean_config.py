#!/usr/bin/env python3
"""
🩺 DIGITALOCEAN DEPLOYMENT DIAGNOSTICS

Checks configuration and data availability for dashboard deployment.
Run this to diagnose why the dashboard isn't showing data.

Usage:
    python check_digitalocean_config.py
"""

import os
import sys
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_env_vars():
    """Check if required environment variables are set."""
    logger.info("\n" + "="*70)
    logger.info("🔐 ENVIRONMENT VARIABLES CHECK")
    logger.info("="*70)
    
    required = {
        'BINANCE_API_KEY': 'Binance API Key',
        'BINANCE_API_SECRET': 'Binance API Secret',
        'ALPACA_API_KEY': 'Alpaca API Key',
        'ALPACA_SECRET_KEY': 'Alpaca Secret Key',
        'KRAKEN_API_KEY': 'Kraken API Key',
        'KRAKEN_API_SECRET': 'Kraken API Secret',
        'SUPABASE_URL': 'Supabase URL for realtime dashboard/audit data',
        'SUPABASE_ANON_KEY': 'Supabase anon key for realtime dashboard/audit data',
    }
    
    missing = []
    for var, desc in required.items():
        value = os.getenv(var)
        if value:
            masked = f"{value[:8]}..." if len(value) > 8 else "***"
            logger.info(f"  ✅ {var:<25} = {masked}")
        else:
            logger.error(f"  ❌ {var:<25} = MISSING")
            missing.append(var)
    
    optional = {
        'PORT': 'HTTP Port (default: 8080)',
        'AUREON_STATE_DIR': 'State directory',
        'LIVE': 'Live trading mode',
        'AUREON_REQUIRE_ALL_EXCHANGES': 'Strict startup exchange validation',
        'AUREON_REDIS_URL': 'Redis ThoughtBus URL (optional)',
        'VITE_SUPABASE_URL': 'Frontend build/runtime Supabase URL',
        'VITE_SUPABASE_PUBLISHABLE_KEY': 'Frontend build/runtime Supabase key',
    }
    
    logger.info("\n📝 Optional Variables:")
    for var, desc in optional.items():
        value = os.getenv(var, 'NOT SET')
        logger.info(f"  {var:<25} = {value}")
    
    if missing:
        logger.error(f"\n⚠️  {len(missing)} CRITICAL variables missing!")
        logger.error("Dashboard will NOT show portfolio data without these!")
        return False
    else:
        logger.info("\n✅ All critical environment variables configured")
        return True

def check_modules():
    """Check if required Python modules can be imported."""
    logger.info("\n" + "="*70)
    logger.info("📦 MODULE AVAILABILITY CHECK")
    logger.info("="*70)
    
    modules = {
        'aiohttp': 'Web framework',
        'binance_ws_client': 'Binance WebSocket',
        'live_position_viewer': 'Position tracker',
        'queen_cognitive_narrator': 'Queen narrator',
        'aureon_harmonic_liquid_aluminium': 'Harmonic field',
        'aureon_unified_market_cache': 'Market cache',
    }
    
    all_ok = True
    for module, desc in modules.items():
        try:
            __import__(module)
            logger.info(f"  ✅ {module:<35} - {desc}")
        except ImportError as e:
            logger.error(f"  ❌ {module:<35} - {desc} (MISSING: {e})")
            all_ok = False
    
    return all_ok

def check_data_files():
    """Check if state files exist."""
    logger.info("\n" + "="*70)
    logger.info("💾 STATE FILES CHECK")
    logger.info("="*70)
    
    files = [
        'aureon_kraken_state.json',
        'binance_truth_tracker_state.json',
        'alpaca_truth_tracker_state.json',
        'cost_basis_history.json',
        'active_position.json',
        '7day_pending_validations.json',
        '7day_anchored_timelines.json',
    ]
    
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"  ✅ {f:<40} ({size:,} bytes, modified: {mtime})")
        else:
            logger.warning(f"  ⚠️  {f:<40} (not found)")

def test_api_connectivity():
    """Test if we can reach exchange APIs."""
    logger.info("\n" + "="*70)
    logger.info("🌐 API CONNECTIVITY CHECK")
    logger.info("="*70)
    
    import requests
    
    apis = {
        'CoinGecko (prices)': 'https://api.coingecko.com/api/v3/ping',
        'Binance Public': 'https://api.binance.com/api/v3/ping',
        'Kraken Public': 'https://api.kraken.com/0/public/Time',
    }
    
    for name, url in apis.items():
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                logger.info(f"  ✅ {name:<30} - Reachable (HTTP {resp.status_code})")
            else:
                logger.warning(f"  ⚠️  {name:<30} - HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"  ❌ {name:<30} - {e}")

def test_binance_auth():
    """Test Binance API authentication."""
    logger.info("\n" + "="*70)
    logger.info("🔑 BINANCE AUTHENTICATION TEST")
    logger.info("="*70)
    
    key = os.getenv('BINANCE_API_KEY')
    secret = os.getenv('BINANCE_API_SECRET')
    
    if not key or not secret:
        logger.error("  ❌ Cannot test - API keys not set")
        return False
    
    try:
        import time
        import hmac
        import hashlib
        import requests
        from urllib.parse import urlencode
        
        timestamp = int(time.time() * 1000)
        params = {'timestamp': timestamp}
        query = urlencode(params)
        signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        
        url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
        headers = {'X-MBX-APIKEY': key}
        
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"  ✅ Authentication successful!")
            logger.info(f"  📊 Account has {len(data.get('balances', []))} assets")
            
            # Show non-zero balances
            balances = [(b['asset'], float(b['free']) + float(b['locked'])) 
                       for b in data.get('balances', []) 
                       if float(b['free']) + float(b['locked']) > 0]
            
            if balances:
                logger.info(f"  💰 Non-zero balances: {len(balances)}")
                for asset, amount in balances[:5]:  # Show first 5
                    logger.info(f"     • {asset}: {amount}")
            
            return True
        else:
            logger.error(f"  ❌ Authentication failed: HTTP {resp.status_code}")
            logger.error(f"     {resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Test failed: {e}")
        return False



def validate_app_yaml():
    """Validate app.yaml includes critical DigitalOcean runtime wiring."""
    logger.info("\n" + "="*70)
    logger.info("📄 app.yaml RUNTIME WIRING CHECK")
    logger.info("="*70)

    try:
        import yaml
    except ImportError:
        logger.warning("  ⚠️  PyYAML not installed - skipping app.yaml validation")
        return False

    path = 'app.yaml'
    if not os.path.exists(path):
        logger.error("  ❌ app.yaml not found")
        return False

    with open(path, 'r', encoding='utf-8') as fh:
        spec = yaml.safe_load(fh) or {}

    services = spec.get('services') or []
    if not services:
        logger.error("  ❌ app.yaml has no services")
        return False

    svc = services[0]
    ok = True

    if str(svc.get('http_port')) != '8080':
        logger.error(f"  ❌ http_port should be 8080, found {svc.get('http_port')}")
        ok = False
    else:
        logger.info("  ✅ http_port is 8080")

    run_command = svc.get('run_command', '')
    if 'supervisord' not in str(run_command):
        logger.error("  ❌ run_command does not start supervisord")
        ok = False
    else:
        logger.info("  ✅ run_command starts supervisord")

    env_keys = {e.get('key') for e in svc.get('envs', []) if isinstance(e, dict)}
    critical_env_keys = {
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'AUREON_STATE_DIR',
        'AUREON_REQUIRE_ALL_EXCHANGES',
    }

    missing = sorted(critical_env_keys - env_keys)
    if missing:
        logger.error(f"  ❌ Missing app.yaml env keys: {', '.join(missing)}")
        ok = False
    else:
        logger.info("  ✅ app.yaml includes critical env keys for dashboard systems")

    return ok


def main():
    """Run all diagnostics."""
    logger.info("\n" + "="*70)
    logger.info("🩺 AUREON DIGITALOCEAN DEPLOYMENT DIAGNOSTICS")
    logger.info("="*70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    results = {
        'env_vars': check_env_vars(),
        'modules': check_modules(),
        'api_connectivity': True,  # Will check below
        'app_yaml': validate_app_yaml(),
        'binance_auth': False,
    }
    
    check_data_files()
    test_api_connectivity()
    results['binance_auth'] = test_binance_auth()
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    logger.info("="*70)
    
    if results['env_vars']:
        logger.info("  ✅ Environment variables configured")
    else:
        logger.error("  ❌ Missing critical environment variables")
    
    if results['modules']:
        logger.info("  ✅ All modules available")
    else:
        logger.warning("  ⚠️  Some modules missing (may work anyway)")

    if results['app_yaml']:
        logger.info("  ✅ app.yaml wiring looks correct")
    else:
        logger.error("  ❌ app.yaml wiring needs fixes")
    
    if results['binance_auth']:
        logger.info("  ✅ Binance authentication working")
    else:
        logger.error("  ❌ Binance authentication failed")
    
    logger.info("\n" + "="*70)
    
    if all([results['env_vars'], results['app_yaml'], results['binance_auth']]):
        logger.info("✅ System should be working! Check dashboard logs for runtime issues.")
        logger.info("\nNext steps:")
        logger.info("  1. Access dashboard at: https://your-app.ondigitalocean.app")
        logger.info("  2. Check status endpoint: https://your-app.ondigitalocean.app/api/status")
        logger.info("  3. View logs: doctl apps logs YOUR_APP_ID --follow")
        return 0
    else:
        logger.error("❌ Critical issues found - dashboard will have NO DATA")
        logger.error("\nFix these issues:")
        if not results['env_vars']:
            logger.error("  1. Set missing API keys in DigitalOcean App Settings")
        if not results['app_yaml']:
            logger.error("  2. Fix app.yaml service wiring/env vars before redeploy")
        if not results['binance_auth']:
            logger.error("  3. Verify API keys are correct and have required permissions")
        logger.error("\nAfter fixing, redeploy the app.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
