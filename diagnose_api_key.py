#!/usr/bin/env python3
"""Diagnose Binance API key issues and check permissions."""
import os, requests, time, hmac, hashlib
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_KEY")
api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_SECRET")
base_url = "https://api.binance.com"

print("\n" + "="*80)
print("BINANCE API KEY DIAGNOSTICS")
print("="*80)
print(f"API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'MISSING'}")
print(f"Secret: {'SET' if api_secret else 'MISSING'}")
print("="*80 + "\n")

if not api_key or not api_secret:
    print("❌ Missing credentials in .env")
    exit(1)

# Test 1: Public endpoint (no auth)
print("1️⃣  Testing public endpoint (no auth required)...")
try:
    r = requests.get(f"{base_url}/api/v3/ping", timeout=5)
    print(f"   ✅ Binance API reachable: {r.status_code}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 2: Server time
print("\n2️⃣  Testing server time...")
try:
    r = requests.get(f"{base_url}/api/v3/time")
    server_time = r.json()['serverTime']
    local_time = int(time.time() * 1000)
    drift = abs(server_time - local_time)
    print(f"   Server: {server_time}, Local: {local_time}, Drift: {drift}ms")
    if drift > 5000:
        print(f"   ⚠️  Time drift > 5s may cause signature issues")
    else:
        print(f"   ✅ Time sync OK")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# Test 3: API key permissions (simple call)
print("\n3️⃣  Testing API key with signed request (account endpoint)...")
try:
    timestamp = int(time.time() * 1000)
    params = f"timestamp={timestamp}"
    signature = hmac.new(api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
    
    headers = {"X-MBX-APIKEY": api_key}
    url = f"{base_url}/api/v3/account?{params}&signature={signature}"
    
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ API key valid and authorized")
        print(f"   Can Trade: {data.get('canTrade')}")
        print(f"   Can Withdraw: {data.get('canWithdraw')}")
        print(f"   Can Deposit: {data.get('canDeposit')}")
        
        # Show balances
        balances = [b for b in data.get('balances', []) if float(b['free']) > 0 or float(b['locked']) > 0]
        print(f"\n   💰 Assets with balance: {len(balances)}")
        for bal in balances[:10]:
            free = float(bal['free'])
            locked = float(bal['locked'])
            total = free + locked
            print(f"      {bal['asset']:<10} Free: {free:<15.8f} Locked: {locked:<15.8f} Total: {total:<15.8f}")
        if len(balances) > 10:
            print(f"      ... and {len(balances) - 10} more")
            
    elif r.status_code == 401:
        error = r.json()
        code = error.get('code')
        msg = error.get('msg')
        print(f"   ❌ Authentication failed (401)")
        print(f"   Code: {code}")
        print(f"   Message: {msg}")
        
        if code == -2015:
            print("\n   🔧 LIKELY CAUSES:")
            print("      1. IP restriction - your IP not whitelisted")
            print("      2. API key permissions insufficient")
            print("      3. API key disabled or deleted")
            print("\n   💡 SOLUTIONS:")
            print("      1. Binance.com → Account → API Management")
            print("      2. Edit your API key → Add current IP to whitelist")
            print("      3. Or unrestrict IP (less secure but easier)")
            print("      4. Ensure 'Enable Spot & Margin Trading' is checked")
    else:
        print(f"   ❌ Unexpected status: {r.status_code}")
        print(f"   Response: {r.text}")
        
except Exception as e:
    print(f"   ❌ Request failed: {e}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80 + "\n")
