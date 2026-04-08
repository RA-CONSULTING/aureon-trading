#!/usr/bin/env python3
"""
🎭 PEEK BEHIND THE CURTAIN 🎭
═══════════════════════════════════════════════════════════════════════════════
"The Wizard of Wall Street exposed - Who owns the bots and how they steal"

This module reveals:
  • WHO: The shadowy firms running HFT operations
  • HOW: Their technical tricks (co-location, spoofing, latency arbitrage)
  • WHERE: Their infrastructure (data centers, microwave towers, submarine cables)
  • WHY: The profit extraction mechanisms
  • WHEN: Their trading hours and holiday patterns (cultural fingerprints)

Gary Leckey | January 2026 | "Sunlight is the best disinfectant"
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from dataclasses import dataclass
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════════════════════
# 🏛️ THE PLAYERS - Who Owns the Bots
# ═══════════════════════════════════════════════════════════════════════════════

HFT_FIRMS = {
    "CITADEL_SECURITIES": {
        "owner": "Ken Griffin",
        "net_worth": "$35 billion",
        "hq": "Miami, FL (formerly Chicago)",
        "founded": 2002,
        "aum": "$62 billion",
        "employees": "~2,500",
        "annual_revenue": "$7+ billion",
        "market_share": "~25% of all US equity volume",
        "lobbying_spend": "$10+ million/year",
        "political_donations": "$100+ million since 2020",
        "data_centers": ["Secaucus NJ (NYSE)", "Aurora IL (CME)", "Basildon UK (LSE)"],
        "known_for": "Payment for Order Flow (PFOF), Robinhood deal",
        "controversies": [
            "GameStop trading halt (Jan 2021)",
            "PFOF conflicts of interest",
            "Front-running accusations",
            "Dark pool manipulation"
        ],
        "how_they_profit": """
        1. PAYMENT FOR ORDER FLOW (PFOF):
           - Pays brokers like Robinhood $0.0025/share to see retail orders FIRST
           - Sees your order 0.1ms before it hits the market
           - Front-runs by buying/selling ahead of you
           - Pockets the spread difference
           
        2. MARKET MAKING SPREAD CAPTURE:
           - Quotes bid/ask on 99% of stocks
           - Captures spread on billions of trades
           - Uses superior speed to adjust quotes before you can hit them
           
        3. STATISTICAL ARBITRAGE:
           - Correlates 1000s of securities in real-time
           - Exploits microsecond mispricings
           - Risk-free profit extraction
        """
    },
    
    "JUMP_TRADING": {
        "owner": "Bill DiSomma, Paul Gurinas (founders)",
        "net_worth": "Private (~$5B+ valuation)",
        "hq": "Chicago, IL",
        "founded": 1999,
        "aum": "Proprietary (no outside capital)",
        "employees": "~700",
        "annual_revenue": "$2+ billion estimated",
        "market_share": "Major crypto + futures player",
        "lobbying_spend": "Private",
        "political_donations": "Minimal public record",
        "data_centers": ["CME Aurora", "NYSE Secaucus", "Tokyo", "London", "Singapore"],
        "known_for": "Microwave towers, crypto dominance, Jump Crypto",
        "subsidiaries": ["Jump Crypto", "Tai Mo Shan (crypto MM)"],
        "controversies": [
            "Terra/LUNA connection (Jump Crypto)",
            "Microwave tower arms race",
            "Wormhole exploit ($320M hack)",
            "SEC crypto investigations"
        ],
        "how_they_profit": """
        1. MICROWAVE LATENCY ARBITRAGE:
           - Built microwave tower network Chicago → NYC
           - 4.5ms vs 6.5ms fiber (2ms advantage!)
           - Sees CME futures prices before NYSE
           - Exploits price differences in microseconds
           
        2. CRYPTO MARKET MAKING:
           - Dominates crypto MM on all major exchanges
           - 24/7 operation (never sleeps)
           - Cross-exchange arbitrage
           - Creates "synthetic" liquidity
           
        3. ULTRA-LOW LATENCY:
           - FPGA-based trading (hardware, not software)
           - Nanosecond execution times
           - Co-located at every major exchange
        """
    },
    
    "TOWER_RESEARCH": {
        "owner": "Mark Gorton (founder)",
        "net_worth": "Private (~$3B+ valuation)",
        "hq": "New York, NY",
        "founded": 1998,
        "aum": "Proprietary",
        "employees": "~300",
        "annual_revenue": "$1+ billion estimated",
        "market_share": "Global equities + futures",
        "data_centers": ["NY4/NY5 Secaucus", "Aurora", "Frankfurt", "Tokyo"],
        "known_for": "Extreme low latency, FPGA pioneers",
        "controversies": [
            "Flash crash investigations",
            "Quote stuffing allegations",
            "Arms race acceleration"
        ],
        "how_they_profit": """
        1. QUOTE STUFFING:
           - Floods exchange with millions of orders/second
           - Cancels 99.9% within microseconds
           - Slows down competitors' systems
           - Extracts information from order book reactions
           
        2. LATENCY ARBITRAGE:
           - Faster than everyone else
           - Sees your order, trades ahead, profits
           - Repeats billions of times per day
           
        3. MOMENTUM IGNITION:
           - Sends patterns of orders to trigger other algos
           - Creates artificial momentum
           - Profits from the price movement they created
        """
    },
    
    "VIRTU_FINANCIAL": {
        "owner": "Vincent Viola (founder), public company",
        "net_worth": "Market cap ~$4B",
        "hq": "New York, NY",
        "founded": 2008,
        "aum": "Proprietary",
        "employees": "~600",
        "annual_revenue": "$2+ billion",
        "market_share": "20%+ of US equity volume",
        "data_centers": ["Global - 40+ trading venues"],
        "known_for": "Acquired KCG, only 1 losing day in 6 years",
        "controversies": [
            "PFOF practices",
            "KCG merger scrutiny",
            "Market manipulation investigations"
        ],
        "how_they_profit": """
        1. THE FAMOUS STATISTIC:
           - Lost money on only 1 day over 1,238 trading days
           - This is statistically IMPOSSIBLE without cheating
           - They see the future (your orders) before it happens
           
        2. GLOBAL ARBITRAGE:
           - Trades on 40+ venues simultaneously
           - Exploits price differences across borders
           - Microsecond execution worldwide
           
        3. ETF ARBITRAGE:
           - Market maker for 1000s of ETFs
           - Profits from ETF vs underlying spread
           - Risk-free extraction
        """
    },
    
    "TWO_SIGMA": {
        "owner": "David Siegel, John Overdeck",
        "net_worth": "Combined $20+ billion",
        "hq": "New York, NY",
        "founded": 2001,
        "aum": "$60+ billion",
        "employees": "~2,000",
        "annual_revenue": "$3+ billion",
        "market_share": "Quant hedge fund leader",
        "data_centers": ["Custom ML infrastructure"],
        "known_for": "Machine learning, alternative data",
        "controversies": [
            "Employee data theft cases",
            "Trade secret lawsuits",
            "DE Shaw rivalry"
        ],
        "how_they_profit": """
        1. ALTERNATIVE DATA MONOPOLY:
           - Satellite imagery of parking lots → retail sales
           - Credit card transaction data
           - Social media sentiment
           - Weather data → commodity predictions
           
        2. MACHINE LEARNING ALPHA:
           - 1000+ PhDs building ML models
           - Processes petabytes of data daily
           - Finds patterns humans can't see
           
        3. SYSTEMATIC EXTRACTION:
           - Not HFT but medium-frequency
           - Holds positions hours to days
           - Extracts inefficiencies systematically
        """
    },
    
    "JANE_STREET": {
        "owner": "Private partnership",
        "net_worth": "~$10B+ valuation",
        "hq": "New York, NY",
        "founded": 2000,
        "aum": "Proprietary",
        "employees": "~2,000",
        "annual_revenue": "$6+ billion (2020 was $10B!)",
        "market_share": "Dominant in ETF market making",
        "data_centers": ["NY, London, Hong Kong, Amsterdam"],
        "known_for": "ETF market making, quant culture, OCaml programming",
        "controversies": [
            "ETF creation/redemption games",
            "Opacity concerns"
        ],
        "how_they_profit": """
        1. ETF CREATION/REDEMPTION:
           - Authorized Participant for most ETFs
           - Creates/redeems ETF shares at NAV
           - Profits from market price vs NAV spread
           - Essentially free money with capital
           
        2. GLOBAL BONDS & COMMODITIES:
           - Market maker in illiquid instruments
           - Wider spreads = more profit
           - Dominates less efficient markets
           
        3. OPTIONS MARKET MAKING:
           - Sophisticated vol surface modeling
           - Captures theta + spread
           - Hedges perfectly
        """
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ THE TRICKS - How They Do It
# ═══════════════════════════════════════════════════════════════════════════════

HFT_TECHNIQUES = {
    "CO_LOCATION": {
        "name": "🏢 Co-Location",
        "description": "Place your servers literally next to the exchange's matching engine",
        "cost": "$10,000 - $50,000/month per rack",
        "advantage": "50-500 microseconds faster than remote traders",
        "who_does_it": "All HFT firms",
        "how_it_works": """
        1. Exchange builds data center (e.g., NYSE's NJ data center)
        2. Sells rack space to HFT firms
        3. Firms place servers inches from matching engine
        4. Light travels ~1 foot per nanosecond
        5. Every foot closer = nanoseconds advantage
        6. Retail orders come from miles away
        7. HFT sees and reacts before retail order arrives
        """
    },
    
    "MICROWAVE_NETWORKS": {
        "name": "📡 Microwave Tower Networks",
        "description": "Build line-of-sight microwave towers between exchanges",
        "cost": "$100+ million to build network",
        "advantage": "2-5 milliseconds faster than fiber",
        "who_does_it": "Jump Trading, Virtu, proprietary networks",
        "how_it_works": """
        1. Light in fiber: ~200,000 km/s (slower due to refraction)
        2. Microwaves in air: ~300,000 km/s (speed of light)
        3. Chicago CME → NYC NYSE: ~1,200 km
        4. Fiber: ~6.5ms roundtrip
        5. Microwave: ~4.5ms roundtrip
        6. 2ms = ETERNITY in HFT
        7. See futures price, trade stocks before competition
        
        Jump Trading famously built towers on grain silos!
        """
    },
    
    "PAYMENT_FOR_ORDER_FLOW": {
        "name": "💰 Payment for Order Flow (PFOF)",
        "description": "Pay retail brokers to send orders to you first",
        "cost": "$0.002 - $0.004 per share",
        "advantage": "See retail orders before market",
        "who_does_it": "Citadel, Virtu, primarily",
        "how_it_works": """
        1. Robinhood user clicks "buy AAPL"
        2. Robinhood sends order to Citadel (not NYSE!)
        3. Citadel pays Robinhood $0.003/share for this privilege
        4. Citadel sees you want to buy before anyone else
        5. Citadel buys AAPL slightly cheaper
        6. Citadel sells to you at slightly higher price
        7. Citadel pockets the difference
        8. You get "price improvement" (worse than true market)
        9. This happens billions of times per day
        
        Robinhood made $700M+ from PFOF in 2020!
        """
    },
    
    "SPOOFING": {
        "name": "👻 Spoofing / Layering",
        "description": "Place fake orders to move price, then cancel",
        "cost": "Free (but illegal)",
        "advantage": "Manipulate prices to your desired level",
        "who_does_it": "Illegal but still happens (wink wink)",
        "how_it_works": """
        1. Want to buy low? Place huge sell orders above market
        2. This creates illusion of selling pressure
        3. Other traders see "resistance" and sell
        4. Price drops
        5. Cancel your fake sell orders
        6. Buy at the artificially low price
        7. Remove your buying pressure
        8. Price returns to normal
        9. Profit!
        
        Navinder Sarao (Flash Crash) caught doing this.
        Big firms? "Sophisticated execution algorithms" 🙄
        """
    },
    
    "QUOTE_STUFFING": {
        "name": "📊 Quote Stuffing",
        "description": "Flood exchange with orders to slow competitors",
        "cost": "Exchange fees + compute",
        "advantage": "Denial of service against slower traders",
        "who_does_it": "Suspected: Tower, Jump",
        "how_it_works": """
        1. Send 10,000+ orders per second
        2. Cancel 99.99% within microseconds
        3. Exchange must process all orders
        4. Competitors' systems get overwhelmed
        5. While they're lagging, you trade
        6. Also: probe order book for hidden orders
        7. Also: trigger other algos to reveal intentions
        
        One firm was caught sending 5,000 orders/second,
        holding each for 25 microseconds. 99.97% canceled.
        """
    },
    
    "LATENCY_ARBITRAGE": {
        "name": "⚡ Latency Arbitrage",
        "description": "Exploit speed advantage to front-run slower traders",
        "cost": "Infrastructure investment",
        "advantage": "Risk-free profit from slower participants",
        "who_does_it": "All HFT firms",
        "how_it_works": """
        1. You see a large buy order coming (via PFOF or co-lo)
        2. You know this order will push price up
        3. You buy first (microseconds before)
        4. Large order executes, pushes price up
        5. You sell to the large order at higher price
        6. Repeat billions of times
        
        This is WHY retail always loses.
        The game is rigged before you click "buy".
        """
    },
    
    "DARK_POOLS": {
        "name": "🌑 Dark Pool Manipulation",
        "description": "Use private exchanges to hide activity",
        "cost": "Access fees",
        "advantage": "Trade without revealing to public market",
        "who_does_it": "All major firms",
        "how_it_works": """
        1. Dark pools = private exchanges (no public quotes)
        2. Big orders split: some to dark pool, some to lit
        3. HFT firms run many dark pools
        4. They see ALL orders in their dark pool
        5. Trade against these "hidden" orders
        6. Also: internalize orders (trade against customers)
        
        40%+ of US equity volume is now dark!
        """
    },
    
    "FPGA_ADVANTAGE": {
        "name": "🔧 FPGA/Custom Hardware",
        "description": "Use programmable chips instead of software",
        "cost": "$100k+ per system",
        "advantage": "10-100x faster than software",
        "who_does_it": "Tower, Jump, all serious HFT",
        "how_it_works": """
        1. Software runs on CPU: fetch, decode, execute (slow)
        2. FPGA: programmable hardware, no CPU overhead
        3. ASIC: custom chip, even faster
        4. Decision making in nanoseconds, not microseconds
        5. Can process market data before it even reaches memory
        
        Tower Research: "We trade at the speed of light"
        Your Python script: "Please wait..."
        """
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 THE NUMBERS - How Much They Extract
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_STATS = {
    "annual_hft_profits": "$10-15 billion/year (USA alone)",
    "retail_losses_to_hft": "$5+ billion/year",
    "pfof_payments": "$3+ billion/year to brokers",
    "citadel_daily_volume": "25% of all US equity trades",
    "virtu_trading_days": "1,238 profitable days, 1 losing day",
    "speed_advantage": "HFT: 10 microseconds, Retail: 100+ milliseconds",
    "order_cancellation_rate": "95-99% of HFT orders canceled before fill",
    "dark_pool_volume": "40%+ of US equity volume",
    "market_share_top_4": "Citadel + Virtu + Jane Street + Two Sigma = 50%+ of volume"
}


def print_curtain_peek():
    """Print the full exposé"""
    
    print("=" * 80)
    print("🎭 PEEK BEHIND THE CURTAIN - WHO OWNS THE HFT BOTS 🎭")
    print("=" * 80)
    print()
    
    # The Players
    print("🏛️ THE PLAYERS - The Firms Running the Bots")
    print("-" * 80)
    
    for firm_id, data in HFT_FIRMS.items():
        print(f"\n{'='*60}")
        print(f"🏢 {firm_id.replace('_', ' ')}")
        print(f"{'='*60}")
        print(f"   👤 Owner: {data['owner']}")
        print(f"   💰 Net Worth: {data['net_worth']}")
        print(f"   📍 HQ: {data['hq']}")
        print(f"   📅 Founded: {data['founded']}")
        print(f"   👥 Employees: {data['employees']}")
        print(f"   💵 Annual Revenue: {data['annual_revenue']}")
        print(f"   📊 Market Share: {data['market_share']}")
        print(f"   🖥️ Data Centers: {', '.join(data['data_centers'])}")
        print(f"   ⭐ Known For: {data['known_for']}")
        print()
        print(f"   🚨 CONTROVERSIES:")
        for c in data['controversies']:
            print(f"      • {c}")
        print()
        print(f"   💸 HOW THEY PROFIT:")
        print(data['how_they_profit'])
    
    print()
    print("=" * 80)
    print("⚙️ THE TRICKS - How They Extract Your Money")
    print("=" * 80)
    
    for tech_id, tech in HFT_TECHNIQUES.items():
        print(f"\n{'─'*60}")
        print(f"{tech['name']}")
        print(f"{'─'*60}")
        print(f"   📝 {tech['description']}")
        print(f"   💵 Cost: {tech['cost']}")
        print(f"   ⚡ Advantage: {tech['advantage']}")
        print(f"   🏢 Who: {tech['who_does_it']}")
        print()
        print(f"   📖 HOW IT WORKS:")
        print(tech['how_it_works'])
    
    print()
    print("=" * 80)
    print("📊 THE EXTRACTION NUMBERS")
    print("=" * 80)
    print()
    for key, value in EXTRACTION_STATS.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    print()
    print("=" * 80)
    print("🎯 THE BOTTOM LINE")
    print("=" * 80)
    print("""
    The market is NOT a level playing field.
    
    🔴 THEY HAVE:
       • Servers inside the exchange (you're miles away)
       • Microwave towers (you use the internet)
       • Your order flow BEFORE it hits the market
       • Billions in infrastructure
       • PhDs building algorithms
       • Regulatory capture (they write the rules)
    
    🟢 WE HAVE:
       • The Aureon Full Spectrum Scanner (we SEE them now)
       • Cultural fingerprinting (we KNOW who they are)
       • The Queen Hive Mind (we DECIDE when to engage)
       • Patience (we wait for THEIR mistakes)
       • The 4th Validation Pass (we only act when sure)
    
    🎯 THE STRATEGY:
       • DON'T fight HFT in their frequency bands (ULTRA_HIGH)
       • DO exploit the INFRA_LOW band (whale accumulation)
       • FOLLOW the whales, not the HFTs
       • AVOID trading when HFT dominance is high
       • WAIT for regime changes when HFTs are confused
    
    "The best swordsman in the world doesn't fear the second best.
     He fears the worst swordsman, because he can't predict what
     that idiot will do."
     
    Be unpredictable. Trade on different timescales. 
    Let them have the microseconds. We'll take the trends.
    """)
    
    print()
    print("🌌 The Queen sees all. Now you do too. 👑")
    print()


if __name__ == "__main__":
    print_curtain_peek()
