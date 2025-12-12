#!/usr/bin/env python3
"""
Test Binance Pool API earnings validation
"""
import os
from binance_client import BinancePoolAPI

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       BINANCE POOL EARNINGS TEST - LIVE VALIDATION        ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Initialize API
    try:
        pool_api = BinancePoolAPI()
        print("✅ Binance Pool API initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\n💡 Set these environment variables:")
        print("   BINANCE_API_KEY=your_key")
        print("   BINANCE_API_SECRET=your_secret")
        return
    
    # Test coins and algorithms
    test_configs = [
        ("sha256", "BTC"),
        ("sha256", "BCH"),
        ("ethash", "ETHW"),
        ("equihash", "ZEC"),
        ("etchash", "ETC"),
        ("x11", "DASH"),
        ("kheavyhash", "KAS"),
    ]
    
    print("\n📊 FETCHING EARNINGS FOR ALL COINS...")
    print("=" * 70)
    
    for algo, coin in test_configs:
        print(f"\n🪙 {coin} ({algo})")
        print("-" * 70)
        
        try:
            # Get earnings
            earnings = pool_api.get_total_earnings(algo, coin)
            
            if 'error' in earnings:
                print(f"   ⚠️  Error: {earnings['error']}")
                continue
            
            # Get wallet balance
            wallet = pool_api.get_wallet_balance(coin)
            
            # Display
            print(f"   Today's Mining:  {earnings['today']:.8f} {coin}")
            print(f"   Yesterday:       {earnings['yesterday']:.8f} {coin}")
            print(f"   Wallet Balance:  {wallet:.8f} {coin}")
            print(f"   Hashrate (15m):  {earnings['hashrate_15m']:.2f} {earnings['unit']}")
            print(f"   Hashrate (24h):  {earnings['hashrate_24h']:.2f} {earnings['unit']}")
            print(f"   Active Workers:  {earnings['valid_workers']}")
            print(f"   Inactive:        {earnings['invalid_workers']}")
            
            # Estimate USD value (rough)
            btc_price = float(os.getenv('BTC_PRICE_USD', '100000'))
            if coin == "BTC":
                usd_value = earnings['today'] * btc_price
                print(f"   ~USD Value:      ${usd_value:.2f}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 70)
    print("\n✅ Test complete!")
    print("\n💡 To use with miner, set:")
    print("   MINING_WORKER=your_wallet_address.worker_name")
    print("   MINING_PLATFORM=binance  # or binance-bch, binance-ethw, etc.")

if __name__ == "__main__":
    main()
