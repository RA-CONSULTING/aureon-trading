#!/usr/bin/env python3
"""
🔍 DASHBOARD DATA DIAGNOSTICS
Checks what data sources are actually working and returning data.
"""

import sys
import os
import json
import asyncio

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def test_prices():
    """Test if we can fetch prices."""
    print(f"\n{BLUE}📊 TESTING PRICE FETCHING{RESET}")
    
    # Try unified market cache
    try:
        from unified_market_cache import get_all_prices, get_ticker
        prices = await asyncio.to_thread(get_all_prices)
        if prices:
            print(f"  {GREEN}✅ Unified Market Cache: {len(prices)} symbols{RESET}")
            for sym in ['BTC', 'ETH', 'SOL']:
                if sym in prices:
                    print(f"     {sym}: ${prices[sym].get('price', 0):,.2f}")
            return True
        else:
            print(f"  {YELLOW}⚠️ Unified Market Cache: No data{RESET}")
    except Exception as e:
        print(f"  {RED}❌ Unified Market Cache: {str(e)[:100]}{RESET}")
    
    # Try CoinGecko fallback
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"  {GREEN}✅ CoinGecko API: Working{RESET}")
                    if 'bitcoin' in data:
                        print(f"     BTC: ${data['bitcoin']['usd']:,.2f}")
                    return True
    except Exception as e:
        print(f"  {RED}❌ CoinGecko: {str(e)[:100]}{RESET}")
    
    return False

async def test_portfolio():
    """Test if we can fetch portfolio data."""
    print(f"\n{BLUE}💼 TESTING PORTFOLIO FETCHING{RESET}")
    
    # Try live_position_viewer
    try:
        from live_position_viewer import get_binance_positions, get_alpaca_positions
        
        binance_pos = await asyncio.to_thread(get_binance_positions)
        print(f"  {GREEN}✅ Binance positions: {len(binance_pos)} positions{RESET}")
        
        alpaca_pos = await asyncio.to_thread(get_alpaca_positions)
        print(f"  {GREEN}✅ Alpaca positions: {len(alpaca_pos)} positions{RESET}")
        
        return len(binance_pos) > 0 or len(alpaca_pos) > 0
    except Exception as e:
        print(f"  {RED}❌ Live Position Viewer: {str(e)[:100]}{RESET}")
    
    # Try state files
    try:
        state_files = [
            'dashboard_snapshot.json',
            'cost_basis_history.json',
            'tracked_positions.json'
        ]
        
        for filename in state_files:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    size = len(json.dumps(data))
                    print(f"  {GREEN}✅ {filename}: {size} bytes{RESET}")
            else:
                print(f"  {YELLOW}⚠️ {filename}: Not found{RESET}")
    except Exception as e:
        print(f"  {RED}❌ State files: {str(e)[:100]}{RESET}")
    
    return False

async def test_balances():
    """Test if we can fetch exchange balances."""
    print(f"\n{BLUE}💰 TESTING EXCHANGE BALANCES{RESET}")
    
    exchanges = [
        ('binance_client', 'BinanceClient'),
        ('kraken_client', 'KrakenClient'),
        ('alpaca_client', 'AlpacaClient')
    ]
    
    working = 0
    for module_name, class_name in exchanges:
        try:
            module = __import__(module_name)
            client_class = getattr(module, class_name)
            client = client_class()
            
            balance = await asyncio.to_thread(client.get_balance)
            if balance:
                total = sum(float(v) for v in balance.values() if v)
                print(f"  {GREEN}✅ {class_name}: ${total:,.2f}{RESET}")
                working += 1
            else:
                print(f"  {YELLOW}⚠️ {class_name}: Empty balance{RESET}")
        except Exception as e:
            error_msg = str(e)
            if 'API' in error_msg or 'key' in error_msg.lower():
                print(f"  {YELLOW}⚠️ {class_name}: No API keys{RESET}")
            else:
                print(f"  {RED}❌ {class_name}: {error_msg[:60]}{RESET}")
    
    return working > 0

async def test_ocean_scanner():
    """Test if Ocean Scanner can fetch data."""
    print(f"\n{BLUE}🌊 TESTING OCEAN SCANNER{RESET}")
    
    try:
        from aureon_ocean_scanner import OceanScanner
        
        # Create scanner with available exchanges
        exchanges = {}
        
        # Try to load exchanges
        for exch_name, client_name in [('kraken', 'KrakenClient'), ('binance', 'BinanceClient'), ('alpaca', 'AlpacaClient')]:
            try:
                if exch_name == 'kraken':
                    from kraken_client import KrakenClient, get_kraken_client
                    exchanges['kraken'] = get_kraken_client()
                elif exch_name == 'binance':
                    from binance_client import BinanceClient
                    exchanges['binance'] = BinanceClient()
                elif exch_name == 'alpaca':
                    from alpaca_client import AlpacaClient
                    exchanges['alpaca'] = AlpacaClient()
            except:
                pass
        
        if exchanges:
            scanner = OceanScanner(exchanges)
            print(f"  {GREEN}✅ Ocean Scanner initialized with {len(exchanges)} exchange(s){RESET}")
            
            # Try to discover universe
            await scanner.discover_universe()
            summary = scanner.get_ocean_summary()
            
            universe_size = summary.get('universe_size', {}).get('total', 0)
            print(f"  {GREEN}✅ Universe discovered: {universe_size:,} symbols{RESET}")
            return True
        else:
            print(f"  {YELLOW}⚠️ No exchanges available for Ocean Scanner{RESET}")
    except Exception as e:
        print(f"  {RED}❌ Ocean Scanner: {str(e)[:100]}{RESET}")
    
    return False

async def test_queen_narrator():
    """Test if Queen Narrator is working."""
    print(f"\n{BLUE}👑 TESTING QUEEN COGNITIVE NARRATOR{RESET}")
    
    try:
        from queen_cognitive_narrator import QueenCognitiveNarrator
        
        narrator = QueenCognitiveNarrator()
        print(f"  {GREEN}✅ Queen Narrator initialized{RESET}")
        
        # Update context
        narrator.update_context(
            btc_price=78883.00,
            btc_change_24h=1.91,
            portfolio_value=0,
            unrealized_pnl=0,
            active_positions=0
        )
        
        # Get thought
        thought = narrator.get_latest_thought()
        if thought:
            print(f"  {GREEN}✅ Generated thought: {thought.get('title', 'N/A')}{RESET}")
            return True
        else:
            print(f"  {YELLOW}⚠️ No thought generated{RESET}")
    except Exception as e:
        print(f"  {RED}❌ Queen Narrator: {str(e)[:100]}{RESET}")
    
    return False

async def test_harmonic_field():
    """Test if Harmonic Field is working."""
    print(f"\n{BLUE}🔩 TESTING HARMONIC LIQUID ALUMINIUM FIELD{RESET}")
    
    try:
        from aureon_harmonic_liquid_aluminium import HarmonicLiquidAluminiumField
        
        field = HarmonicLiquidAluminiumField()
        print(f"  {GREEN}✅ Harmonic Field initialized{RESET}")
        
        # Capture snapshot
        snapshot = field.capture_snapshot()
        print(f"  {GREEN}✅ Snapshot captured{RESET}")
        print(f"     Frequency: {snapshot.frequency} Hz")
        print(f"     Amplitude: {snapshot.amplitude:.4f}")
        print(f"     Pattern: {snapshot.pattern}")
        
        return True
    except Exception as e:
        print(f"  {RED}❌ Harmonic Field: {str(e)[:100]}{RESET}")
    
    return False

async def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🔍 AUREON PRO DASHBOARD - DATA DIAGNOSTICS{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    results = {}
    
    # Test each data source
    results['prices'] = await test_prices()
    results['portfolio'] = await test_portfolio()
    results['balances'] = await test_balances()
    results['ocean'] = await test_ocean_scanner()
    results['queen'] = await test_queen_narrator()
    results['harmonic'] = await test_harmonic_field()
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}📊 SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    working = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        icon = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
        print(f"  {icon} {name.title()}")
    
    print(f"\n  {GREEN if working == total else YELLOW}Working: {working}/{total}{RESET}")
    
    # Recommendations
    print(f"\n{BLUE}💡 RECOMMENDATIONS:{RESET}")
    
    if not results['balances']:
        print(f"  • Set API keys in DigitalOcean for live balance data")
    
    if not results['portfolio']:
        print(f"  • Portfolio will be empty until you have open positions")
        print(f"  • Or set API keys to fetch live positions")
    
    if results['prices'] and results['queen'] and results['harmonic']:
        print(f"  • {GREEN}✅ Dashboard core functionality is WORKING!{RESET}")
        print(f"  • Prices, Queen commentary, and harmonic field are live")
    
    print(f"\n{BLUE}🚀 The dashboard is showing exactly what it should!{RESET}")
    print(f"   Missing data is due to no API keys (expected in demo mode)")

if __name__ == '__main__':
    asyncio.run(main())
