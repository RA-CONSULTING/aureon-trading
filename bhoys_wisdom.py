#!/usr/bin/env python3
"""
🇮🇪 Bhoy's Wisdom - Strategic Guidance for IRA Sniper Mode 🇮🇪
==============================================================
Extracted wisdom from "Through a Bhoy's Eyes" and Irish Republican tradition.

This module provides:
- Strategic quotes for trading celebrations
- Patience and timing wisdom for entries/exits
- Resilience guidance during drawdowns
- Victory celebrations for penny profits

Integration:
    from bhoys_wisdom import get_victory_quote, get_patience_wisdom, get_resilience_message

"Every penny is a battle won, every trade a step towards freedom."
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# WISDOM CATEGORIES
# =============================================================================

class WisdomCategory(Enum):
    VICTORY = "victory"           # Celebrating wins
    PATIENCE = "patience"         # Waiting for entries
    RESILIENCE = "resilience"     # During losses/drawdowns
    STRATEGY = "strategy"         # Tactical decisions
    UNITY = "unity"               # Community/solidarity
    LEGACY = "legacy"             # Honoring the past


# =============================================================================
# THE WISDOM COLLECTION
# =============================================================================

BHOYS_WISDOM = {
    WisdomCategory.VICTORY: [
        # Bobby Sands - Hunger Striker & Martyr
        "Our revenge will be the laughter of our children. - Bobby Sands 🍀",
        "The Republic still lives! - Bobby Sands",
        "Everyone has their own particular part to play. - Bobby Sands",
        "I have no prouder boast than to say I am Irish. - Bobby Sands",
        
        # Traditional
        "Tiocfaidh ár lá! - Our day will come! ☘️",
        "Sinn Féin Amháin - Ourselves Alone, We Stand Together",
        
        # From 'Through a Bhoy's Eyes'
        "Every penny is a battle won, every trade a step towards freedom. 💰",
        "The flame ignited on Bloody Sunday burns brighter than ever.",
        "Small victories compound into liberation. Penny by penny, we rise!",
        "This is our path - freedom through financial independence.",
    ],
    
    WisdomCategory.PATIENCE: [
        # Strategic Wisdom
        "Move quietly, strike precisely, like shadows through Belfast streets.",
        "Patience is the weapon of the wise - wait for the right moment.",
        "The courier waits, watches, then delivers with precision.",
        "Every checkpoint taught patience. Every wait builds strength.",
        
        # From the Book - Michael's Journey
        "Michael learned in the shadows - observation before action.",
        "The clandestine meetings taught one lesson above all: timing is everything.",
        "Like the Falls Road murals, we watch silently before we act.",
        "The wise fighter picks battles that can be won.",
        
        # Trading Application
        "The market will present opportunities - be ready when it does.",
        "Better to miss a trade than to rush into a loss.",
        "The penny profit waits for those who wait for it.",
    ],
    
    WisdomCategory.RESILIENCE: [
        # Bobby Sands
        "Our revenge will be the laughter of our children. - Bobby Sands",
        "I was only a working-class boy from a Nationalist ghetto, but it is repression that creates the revolutionary spirit of freedom.",
        
        # From 'Through a Bhoy's Eyes'
        "The flame ignited cannot be extinguished - it only grows stronger.",
        "In the chaos, find your purpose. In the struggle, find your strength.",
        "Belfast endured. So shall we.",
        "Aoife's quiet strength held the family together through every storm.",
        "The scars of conflict made us stronger, not weaker.",
        
        # Trading Application
        "A loss is a lesson. A drawdown is a test of resolve.",
        "The hunger strikers taught us about true commitment to a cause.",
        "Ten losses mean nothing if the eleventh brings victory.",
        "Markets test us like the checkpoints tested Belfast. We endure.",
    ],
    
    WisdomCategory.STRATEGY: [
        # Sun Tzu meets Falls Road
        "Know the terrain. The streets of Belfast were our classroom.",
        "The best battles are won before they're fought.",
        "Intelligence gathering precedes every operation.",
        "Like the IRA courier, move between the checkpoints unseen.",
        
        # From the Book
        "The seasoned members spoke with conviction - learn from experience.",
        "Every mural tells a story. Every chart tells a story. Learn to read them.",
        "The clandestine network operated through trust and verification.",
        
        # Trading Application
        "Scout the market before deploying capital.",
        "Small position, precise entry, defined exit - the sniper's way.",
        "Multiple timeframes, like multiple informants, reveal the truth.",
    ],
    
    WisdomCategory.UNITY: [
        # Traditional Irish
        "Ní neart go cur le chéile - There is no strength without unity",
        "Éirinn go Brách - Ireland Forever",
        "The community stood together through raids and searches.",
        
        # From 'Through a Bhoy's Eyes'
        "Acts of kindness, like sharing food during shortages, bound us together.",
        "The camaraderie among members was a lifeline through the fear.",
        "They were more than a group - they were a family bound by purpose.",
        
        # Modern Application
        "We trade alone but we are part of something larger.",
        "Every penny profit honours the sacrifices of the community.",
    ],
    
    WisdomCategory.LEGACY: [
        # Historical
        "Patrick's tales of the 1916 Easter Rising lit the flame in Michael's heart.",
        "The weight of history guides our resolve. We fight for those who came before.",
        "Every successful trade honours those who sacrificed for us.",
        
        # From 'Through a Bhoy's Eyes'
        "These were not mere bedtime tales - they were seeds of a legacy.",
        "The blood on the streets of Derry was no different from 1916.",
        "Michael saw his father's passion reflected in his own heart.",
        
        # Application
        "We build wealth not for ourselves alone, but for generations to come.",
        "Financial freedom is the modern path to the dreams of our ancestors.",
        "They took our land, but they cannot take our determination.",
    ],
}


# =============================================================================
# WISDOM RETRIEVAL FUNCTIONS
# =============================================================================

def get_victory_quote() -> str:
    """Get a random victory celebration quote."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.VICTORY])


def get_patience_wisdom() -> str:
    """Get wisdom for waiting/patience during market conditions."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.PATIENCE])


def get_resilience_message() -> str:
    """Get a resilience message during drawdowns or losses."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.RESILIENCE])


def get_strategy_guidance() -> str:
    """Get strategic wisdom for trading decisions."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.STRATEGY])


def get_unity_message() -> str:
    """Get a message about community and solidarity."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.UNITY])


def get_legacy_reminder() -> str:
    """Get a reminder about legacy and those who came before."""
    return random.choice(BHOYS_WISDOM[WisdomCategory.LEGACY])


def get_random_wisdom(category: Optional[WisdomCategory] = None) -> str:
    """Get random wisdom, optionally from a specific category."""
    if category:
        return random.choice(BHOYS_WISDOM[category])
    else:
        all_wisdom = []
        for quotes in BHOYS_WISDOM.values():
            all_wisdom.extend(quotes)
        return random.choice(all_wisdom)


def get_contextual_wisdom(win_rate: float, current_drawdown: float, 
                          trades_today: int) -> Dict[str, str]:
    """
    Get contextual wisdom based on trading performance.
    
    Args:
        win_rate: Current win rate (0-1)
        current_drawdown: Current drawdown percentage (0-1)
        trades_today: Number of trades executed today
        
    Returns:
        Dict with 'quote', 'category', and 'guidance'
    """
    # Determine most relevant category
    if current_drawdown > 0.05:
        # In significant drawdown - need resilience
        category = WisdomCategory.RESILIENCE
        guidance = "🛡️ Hold firm. Belfast endured worse."
    elif win_rate > 0.7 and trades_today > 0:
        # Winning streak - celebrate but stay humble
        category = WisdomCategory.VICTORY
        guidance = "🎯 Well done, but stay vigilant."
    elif trades_today == 0:
        # No trades yet - patience
        category = WisdomCategory.PATIENCE
        guidance = "⏳ The right opportunity will come."
    elif win_rate < 0.4:
        # Struggling - need strategy review
        category = WisdomCategory.STRATEGY
        guidance = "📊 Review the terrain. Adapt and overcome."
    else:
        # Normal conditions - general wisdom
        category = random.choice(list(WisdomCategory))
        guidance = "☘️ Stay the course."
    
    return {
        'quote': random.choice(BHOYS_WISDOM[category]),
        'category': category.value,
        'guidance': guidance
    }


# =============================================================================
# IRA SNIPER CELEBRATION DISPLAY
# =============================================================================

def celebrate_penny_profit(pnl_usd: float, symbol: str, trade_type: str = "TRADE") -> None:
    """
    Display IRA Sniper celebration for a winning trade.
    
    Args:
        pnl_usd: Profit in USD
        symbol: Trading pair symbol
        trade_type: Type of trade (e.g., "BTC PAIRS", "KRAKEN", "BINANCE")
    """
    quote = get_victory_quote()
    
    print(f"""
🇮🇪🇮🇪🇮🇪 IRA SNIPER WIN! 🇮🇪🇮🇪🇮🇪
    💰 +${pnl_usd:.4f} on {symbol} [{trade_type}]
    📜 "{quote}"
🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪🇮🇪
""")


def display_loss_resilience(loss_usd: float, symbol: str) -> None:
    """Display resilience message after a loss."""
    quote = get_resilience_message()
    
    print(f"""
    ❌ Loss on {symbol}: -${abs(loss_usd):.4f}
    💪 "{quote}"
    ☘️ We continue the fight.
""")


# =============================================================================
# MAIN - Display Sample Wisdom
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🇮🇪 BHOY'S WISDOM - Strategic Guidance for IRA Sniper Mode 🇮🇪          ║
║                                                                          ║
║   "Through a Bhoy's Eyes" - Wisdom for the Trading Revolution            ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("=" * 60)
    print("📚 WISDOM BY CATEGORY")
    print("=" * 60)
    
    for category in WisdomCategory:
        print(f"\n🏷️  {category.value.upper()}")
        print("-" * 40)
        for quote in BHOYS_WISDOM[category][:3]:  # Show first 3
            print(f"   • {quote}")
        if len(BHOYS_WISDOM[category]) > 3:
            print(f"   ... and {len(BHOYS_WISDOM[category]) - 3} more")
    
    print("\n" + "=" * 60)
    print("🎯 SAMPLE CONTEXTUAL WISDOM")
    print("=" * 60)
    
    # Simulate different scenarios
    scenarios = [
        (0.8, 0.01, 5, "Winning streak"),
        (0.3, 0.08, 3, "In drawdown"),
        (0.5, 0.02, 0, "Waiting for entry"),
    ]
    
    for win_rate, drawdown, trades, scenario in scenarios:
        result = get_contextual_wisdom(win_rate, drawdown, trades)
        print(f"\n📊 Scenario: {scenario}")
        print(f"   Category: {result['category']}")
        print(f"   Quote: {result['quote']}")
        print(f"   Guidance: {result['guidance']}")
    
    print("\n" + "=" * 60)
    print("🎉 SAMPLE CELEBRATION")
    print("=" * 60)
    celebrate_penny_profit(0.0234, "ETH/BTC", "KRAKEN")
    
    print("\n🇮🇪 Tiocfaidh ár lá! 🇮🇪")
