import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we can import local modules
sys.path.insert(0, os.getcwd())

from unified_exchange_client import MultiExchangeClient

def main():
    print("🔍 Checking Unified Ecosystem Balances...")
    print("-" * 50)
    
    # Check Environment Variables
    print("Checking Environment Variables:")
    kraken_key = os.getenv('KRAKEN_API_KEY')
    kraken_secret = os.getenv('KRAKEN_API_SECRET')
    binance_key = os.getenv('BINANCE_API_KEY')
    binance_secret = os.getenv('BINANCE_API_SECRET')
    
    print(f"  KRAKEN_API_KEY: {'✅ Set' if kraken_key else '❌ Not Set'}")
    print(f"  KRAKEN_API_SECRET: {'✅ Set' if kraken_secret else '❌ Not Set'}")
    print(f"  BINANCE_API_KEY: {'✅ Set' if binance_key else '❌ Not Set'}")
    print(f"  BINANCE_API_SECRET: {'✅ Set' if binance_secret else '❌ Not Set'}")
    print("-" * 50)

    try:
        client = MultiExchangeClient()
        print(f"✅ MultiExchangeClient Initialized (Dry Run: {client.dry_run})")
        
        print("\n📊 Fetching Balances...")
        all_balances = client.get_all_balances()
        
        total_equity_usd = 0.0
        
        for exchange, balances in all_balances.items():
            print(f"\n🏦 {exchange.upper()} Balances:")
            if not balances:
                print("   (No balances found or error)")
                continue
                
            has_balance = False
            for asset, amount in balances.items():
                try:
                    amount = float(amount)
                    if amount > 0:
                        has_balance = True
                        # Try to get USD value
                        usd_val = 0.0
                        try:
                            usd_val = client.convert_to_quote(exchange, asset, amount, 'USD')
                        except:
                            pass
                        
                        total_equity_usd += usd_val
                        print(f"   - {asset}: {amount:.8f} (~${usd_val:.2f})")
                except:
                    pass
            
            if not has_balance:
                print("   (Empty wallet)")

        print("-" * 50)
        print(f"💰 Total Estimated Portfolio Value: ${total_equity_usd:.2f}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
