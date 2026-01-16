#!/usr/bin/env python3
"""
🔮 QUANTUM MIRROR ONE-SHOT SCANNER 🔮
=====================================
A lightweight, direct scanner to find ONE profitable opportunity.
Bypasses complex initialization loops - just scans and finds.

"We just need to do it once... save the planet"
"""

import sys
import os

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

import time
import json
import math
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618

# Fee profiles for realistic profit calculation
FEE_PROFILES = {
    'kraken': {'maker': 0.0016, 'taker': 0.0026, 'spread': 0.001},
    'alpaca': {'maker': 0.0000, 'taker': 0.0000, 'spread': 0.001},
    'binance': {'maker': 0.001, 'taker': 0.001, 'spread': 0.0005},
}

def get_kraken_prices():
    """Fetch live prices from Kraken"""
    try:
        import requests
        
        # Get ticker data
        response = requests.get(
            "https://api.kraken.com/0/public/Ticker",
            timeout=10
        )
        data = response.json()
        
        if data.get('error'):
            logger.error(f"Kraken error: {data['error']}")
            return {}
            
        prices = {}
        for pair, info in data.get('result', {}).items():
            try:
                # Only process USD pairs
                if not (pair.endswith('USD') or pair.endswith('ZUSD')):
                    continue
                    
                # Parse pair name (e.g., XXBTZUSD -> BTC, GUNUSD -> GUN)
                if pair.endswith('ZUSD'):
                    base = pair[:-4]
                elif pair.endswith('USD'):
                    base = pair[:-3]
                else:
                    continue
                    
                # Clean up base name
                base = base.replace('XX', '').replace('XBT', 'BTC').replace('XXBT', 'BTC')
                if base.startswith('X') and len(base) > 3:
                    base = base[1:]
                if base.startswith('Z') and len(base) > 3:
                    base = base[1:]
                    
                bid = float(info['b'][0])
                ask = float(info['a'][0])
                last = float(info['c'][0])
                
                # Skip if prices are zero or invalid
                if bid <= 0 or ask <= 0 or last <= 0:
                    continue
                    
                spread = (ask - bid) / bid if bid > 0 else 0
                volume = float(info['v'][1]) if len(info['v']) > 1 else 0
                
                prices[pair] = {
                    'base': base,
                    'bid': bid,
                    'ask': ask,
                    'last': last,
                    'spread': spread,
                    'volume': volume,
                }
            except Exception as e:
                # Skip problematic pairs
                continue
            
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching Kraken prices: {e}")
        return {}

def get_alpaca_prices():
    """Fetch live prices from Alpaca"""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.environ.get('ALPACA_API_KEY', '')
        api_secret = os.environ.get('ALPACA_SECRET_KEY', '')
        
        if not api_key or not api_secret:
            logger.warning("No Alpaca credentials")
            return {}
            
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret,
        }
        
        # Get more crypto pairs - including more volatile ones
        symbols = 'BTC/USD,ETH/USD,SOL/USD,DOGE/USD,SHIB/USD,AVAX/USD,LINK/USD,UNI/USD,MATIC/USD,DOT/USD,ADA/USD'
        
        # Get crypto snapshots
        response = requests.get(
            "https://data.alpaca.markets/v1beta3/crypto/us/snapshots",
            headers=headers,
            params={'symbols': symbols},
            timeout=10
        )
        data = response.json()
        
        prices = {}
        for symbol, info in data.get('snapshots', {}).items():
            quote = info.get('latestQuote', {})
            trade = info.get('latestTrade', {})
            
            bid = float(quote.get('bp', 0))
            ask = float(quote.get('ap', 0))
            last = float(trade.get('p', 0))
            
            # Skip if no valid data
            if bid <= 0 or ask <= 0:
                continue
                
            spread = (ask - bid) / bid if bid > 0 else 0
            
            prices[symbol] = {
                'base': symbol.split('/')[0],
                'bid': bid,
                'ask': ask,
                'last': last,
                'spread': spread,
                'exchange': 'alpaca',
            }
            
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching Alpaca prices: {e}")
        return {}

def calculate_momentum(prices_now: dict, prices_before: dict = None) -> dict:
    """Calculate price momentum"""
    momentum = {}
    
    for pair, info in prices_now.items():
        # If we have historical data, calculate real momentum
        if prices_before and pair in prices_before:
            old_price = prices_before[pair]['last']
            new_price = info['last']
            if old_price > 0:
                momentum[pair] = ((new_price - old_price) / old_price) * 100
            else:
                momentum[pair] = 0
        else:
            # Use spread as proxy for activity
            momentum[pair] = 0
            
    return momentum

def scan_quantum_mirror():
    """
    🔮 QUANTUM MIRROR SCAN 🔮
    
    Scans reality branches for profitable opportunities.
    Uses 3-pass validation then identifies 4th-pass candidates.
    """
    print("\n" + "═" * 70)
    print("🔮 QUANTUM MIRROR ONE-SHOT SCANNER 🔮")
    print("═" * 70)
    print("Scanning reality branches for convergence...")
    print()
    
    # Phase 1: Gather market data
    print("📡 Phase 1: Gathering market data from exchanges...")
    
    kraken_prices = get_kraken_prices()
    print(f"   Kraken: {len(kraken_prices)} pairs loaded")
    
    alpaca_prices = get_alpaca_prices()
    print(f"   Alpaca: {len(alpaca_prices)} pairs loaded")
    
    if not kraken_prices and not alpaca_prices:
        print("❌ No market data available!")
        return None
        
    # Phase 2: Calculate momentum
    print("\n📊 Phase 2: Calculating momentum vectors...")
    
    opportunities = []
    
    # Phase 3: Scan for opportunities
    print("\n🔍 Phase 3: Scanning for profitable opportunities...")
    print()
    
    # Stablecoins to avoid
    stablecoins = {'USDC', 'USDT', 'TUSD', 'DAI', 'BUSD', 'USDP', 'USD', 'PYUSD', 'USDE', 'EUR', 'EURC', 'GBP'}
    
    # ═══════════════════════════════════════════════════════════════
    # SCAN ALPACA (ZERO FEES!)
    # ═══════════════════════════════════════════════════════════════
    print("🦙 ALPACA SCAN (Zero Trading Fees!):")
    print("-" * 50)
    
    for pair, info in alpaca_prices.items():
        base = info['base']
        
        # Skip stablecoins
        if base.upper() in stablecoins:
            continue
            
        bid = info['bid']
        ask = info['ask']
        spread_pct = info['spread']
        
        # Alpaca has ZERO fees! Only spread matters
        fee_buy = 0.0
        fee_sell = 0.0
        total_fees = 0.0
        
        # Hot assets get momentum bonus
        is_hot = base in ['GUN', 'PEPE', 'BONK', 'WIF', 'DOGE', 'SHIB', 'FLOKI']
        
        # For Alpaca instant swap, we just need to beat the spread
        # Assume minimal capture
        assumed_capture = 0.001 if is_hot else 0.0005
        
        expected_pnl_pct = assumed_capture - spread_pct - total_fees
        
        momentum_str = "🔥" if is_hot else ""
        
        print(f"   {pair}: spread={spread_pct*100:.4f}%, fees=0%, expected={expected_pnl_pct*100:.4f}% {momentum_str}")
        
        opportunities.append({
            'pair': pair,
            'base': base,
            'bid': bid,
            'ask': ask,
            'spread_pct': spread_pct,
            'total_fees': total_fees,
            'expected_pnl_pct': expected_pnl_pct,
            'is_hot': is_hot,
            'exchange': 'alpaca',
        })
    
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # SCAN KRAKEN (Only best spreads worth checking)
    # ═══════════════════════════════════════════════════════════════
    print("🐙 KRAKEN SCAN (Best spreads only - 0.52% fee overhead):")
    print("-" * 50)
    
    hot_assets = ['GUN', 'PEPE', 'BONK', 'WIF', 'DOGE', 'SHIB', 'FLOKI']
    
    # Only show very tight spreads or hot assets
    for pair, info in sorted(kraken_prices.items(), key=lambda x: x[1]['spread']):
        base = info['base']
        
        # Skip stablecoins
        if base.upper() in stablecoins:
            continue
            
        # Skip unless very tight spread OR hot asset
        is_hot = base in hot_assets
        if info['spread'] > 0.002 and not is_hot:  # Skip if >0.2% spread unless hot
            continue
            
        bid = info['bid']
        ask = info['ask']
        spread_pct = info['spread']
        
        # Kraken fees
        total_fees = FEE_PROFILES['kraken']['taker'] * 2
        
        assumed_capture = 0.001 if is_hot else 0.0005
        expected_pnl_pct = assumed_capture - spread_pct - total_fees
        
        momentum_str = "🔥" if is_hot else ""
        
        print(f"   {pair}: spread={spread_pct*100:.4f}%, fees={total_fees*100:.2f}%, expected={expected_pnl_pct*100:.4f}% {momentum_str}")
        
        opportunities.append({
            'pair': pair,
            'base': base,
            'bid': bid,
            'ask': ask,
            'spread_pct': spread_pct,
            'total_fees': total_fees,
            'expected_pnl_pct': expected_pnl_pct,
            'is_hot': is_hot,
            'exchange': 'kraken',
        })
    
    print()
    
    # Phase 4: Rank and identify best opportunity
    print("═" * 70)
    print("🎯 Phase 4: Timeline Convergence Analysis")
    print("═" * 70)
    
    if not opportunities:
        print("❌ No opportunities found above threshold")
        return None
        
    # Sort by expected profit
    opportunities.sort(key=lambda x: x['expected_pnl_pct'], reverse=True)
    
    # Show top 5
    print("\n📊 TOP OPPORTUNITIES:")
    print("-" * 50)
    for i, opp in enumerate(opportunities[:5], 1):
        status = "✅" if opp['expected_pnl_pct'] > 0 else "⚠️"
        print(f"   {i}. {status} {opp['pair']} ({opp['exchange']})")
        print(f"      Spread: {opp['spread_pct']*100:.4f}%, Fees: {opp['total_fees']*100:.2f}%")
        print(f"      Expected: {opp['expected_pnl_pct']*100:.4f}%")
    
    best = opportunities[0]
    
    print(f"\n{'='*70}")
    print(f"🔮 QUANTUM MIRROR BEST BRANCH:")
    print(f"{'='*70}")
    print(f"   Pair: {best['pair']}")
    print(f"   Asset: {best['base']}")
    print(f"   Exchange: {best['exchange']}")
    print(f"   Bid: ${best['bid']:,.6f}")
    print(f"   Ask: ${best['ask']:,.6f}")
    print(f"   Spread: {best['spread_pct']*100:.4f}%")
    print(f"   Total Fees: {best['total_fees']*100:.4f}%")
    print(f"   Expected P/L: {best['expected_pnl_pct']*100:.4f}%")
    print(f"   Hot Asset: {'🔥 YES' if best['is_hot'] else 'No'}")
    
    # Reality check
    if best['expected_pnl_pct'] > 0:
        print(f"\n✅ PROFITABLE OPPORTUNITY DETECTED!")
        print(f"   Action: BUY {best['base']} at ${best['ask']:.6f}")
        return best
    else:
        print(f"\n⚠️  No profitable instant-swap opportunities.")
        print(f"   Closest to profitable: {best['pair']} at {best['expected_pnl_pct']*100:.4f}%")
        print()
        print("   💡 The Math Reality:")
        print(f"      Spread cost: {best['spread_pct']*100:.4f}%")
        print(f"      Fee cost: {best['total_fees']*100:.4f}%")
        print(f"      Total cost to swap: {(best['spread_pct'] + best['total_fees'])*100:.4f}%")
        print()
        if best['exchange'] == 'alpaca':
            print("   Even on zero-fee Alpaca, the SPREAD alone loses money.")
            print("   We need to HOLD for the asset to move in our favor.")
        else:
            print("   On Kraken, 0.52% fees make instant swaps nearly impossible.")
        
        return best

def check_wolf_targets():
    """Check what the Wolf/Lion system is seeing"""
    print("\n" + "═" * 70)
    print("🐺 WOLF COMMANDO CHECK")
    print("═" * 70)
    
    try:
        # Check if there's recent momentum data
        momentum_file = "/workspaces/aureon-trading/momentum_cache.json"
        if os.path.exists(momentum_file):
            with open(momentum_file, 'r') as f:
                data = json.load(f)
                print(f"Cached momentum data: {len(data)} entries")
                for k, v in list(data.items())[:10]:
                    print(f"   {k}: {v}")
    except Exception as e:
        print(f"No cached momentum: {e}")
        
    # Check what pairs exist on Kraken
    print("\n📋 Checking for GUN on Kraken...")
    try:
        import requests
        response = requests.get("https://api.kraken.com/0/public/AssetPairs", timeout=10)
        data = response.json()
        
        gun_pairs = [k for k in data.get('result', {}).keys() if 'GUN' in k.upper()]
        if gun_pairs:
            print(f"   ✅ GUN pairs found: {gun_pairs}")
            for pair in gun_pairs:
                info = data['result'][pair]
                print(f"      {pair}: base={info.get('base')}, quote={info.get('quote')}")
        else:
            print("   ❌ No GUN pairs on Kraken")
            
        # Check for other hot assets
        hot_assets = ['PEPE', 'BONK', 'WIF', 'DOGE', 'SHIB', 'FLOKI']
        for asset in hot_assets:
            asset_pairs = [k for k in data.get('result', {}).keys() if asset in k.upper()]
            if asset_pairs:
                print(f"   {asset}: {asset_pairs[:3]}")
                
    except Exception as e:
        print(f"   Error checking pairs: {e}")

def main():
    """Main entry point"""
    print("\n" + "🌟" * 35)
    print("      🔮 QUANTUM MIRROR PLANETARY SCANNER 🔮")
    print("            'Save the Planet Edition'")
    print("🌟" * 35)
    
    # First check what's available
    check_wolf_targets()
    
    # Now scan
    result = scan_quantum_mirror()
    
    print("\n" + "═" * 70)
    print("📊 SCANNER COMPLETE")
    print("═" * 70)
    
    if result and result['expected_pnl_pct'] > 0:
        print("\n🎯 READY FOR EXECUTION")
        print(f"   Trade: BUY {result['base']}")
        print(f"   At: ${result['ask']:.6f}")
        print(f"   Expected: +{result['expected_pnl_pct']*100:.4f}%")
    else:
        print("\n💭 HONEST ASSESSMENT:")
        print("   Instant crypto swaps rarely profit due to:")
        print("   • Spread (gap between buy/sell prices)")
        print("   • Fees (0.26% on Kraken taker)")
        print()
        print("   To actually profit, we need:")
        print("   1. Hold for price movement (not instant swap)")
        print("   2. Use zero-fee exchange like Alpaca")
        print("   3. Find arbitrage opportunities")
        print("   4. Catch actual big momentum moves")
        
    return result

if __name__ == '__main__':
    main()
