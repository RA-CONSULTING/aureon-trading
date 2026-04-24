#!/usr/bin/env python3
"""
👑 QUEEN OPTIONS SCANNER - INTELLIGENT OPTIONS DISCOVERY 👑
═══════════════════════════════════════════════════════════════════════════════

Scans for optimal options opportunities using:
  - Premium vs risk analysis
  - Greeks-based filtering (delta, theta, IV)
  - Queen Hive confidence scoring
  - Covered call income strategies
  - Cash-secured put entries

Gary Leckey | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

from alpaca_options_client import (
    AlpacaOptionsClient, get_options_client, 
    OptionContract, OptionQuote, OptionType, TradingLevel
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# OPTIONS OPPORTUNITY
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OptionsOpportunity:
    """Represents a scored options opportunity."""
    contract: OptionContract
    quote: OptionQuote
    strategy: str                  # "covered_call", "cash_secured_put", "buy_call", "buy_put"
    
    # Scoring
    premium_score: float           # Premium as % of strike
    spread_score: float            # Tight spread = higher score
    volume_score: float            # Higher volume = higher score
    theta_score: float             # Daily decay value
    
    # Final score
    queen_confidence: float = 0.0
    total_score: float = 0.0
    
    # Analysis
    max_profit: float = 0.0
    max_risk: float = 0.0
    breakeven: float = 0.0
    days_to_expiry: int = 0
    annualized_return: float = 0.0
    
    def calculate_scores(self, underlying_price: float):
        """Calculate opportunity scores."""
        # Premium score: premium as % of collateral
        premium = self.quote.mid_price * 100  # Contract = 100 shares
        
        if self.strategy == "covered_call":
            collateral = underlying_price * 100
            self.max_profit = premium
            self.max_risk = underlying_price * 100  # If stock goes to 0
            self.breakeven = underlying_price - self.quote.mid_price
            
        elif self.strategy == "cash_secured_put":
            collateral = self.contract.strike_price * 100
            self.max_profit = premium
            self.max_risk = collateral - premium  # If stock goes to 0
            self.breakeven = self.contract.strike_price - self.quote.mid_price
            
        elif self.strategy == "buy_call":
            collateral = premium
            self.max_profit = float('inf')  # Unlimited upside
            self.max_risk = premium
            self.breakeven = self.contract.strike_price + self.quote.mid_price
            
        elif self.strategy == "buy_put":
            collateral = premium
            self.max_profit = self.contract.strike_price * 100 - premium
            self.max_risk = premium
            self.breakeven = self.contract.strike_price - self.quote.mid_price
        
        # Premium score (0-1, higher = better premium)
        if collateral > 0:
            self.premium_score = min(1.0, (premium / collateral) * 10)  # 10% = 1.0
        else:
            self.premium_score = 0
        
        # Spread score (0-1, tighter = better)
        if self.quote.spread_pct < 1:
            self.spread_score = 1.0
        elif self.quote.spread_pct < 5:
            self.spread_score = 0.8
        elif self.quote.spread_pct < 10:
            self.spread_score = 0.5
        else:
            self.spread_score = 0.2
        
        # Volume score (0-1, higher = better)
        if self.quote.volume > 1000:
            self.volume_score = 1.0
        elif self.quote.volume > 100:
            self.volume_score = 0.7
        elif self.quote.volume > 10:
            self.volume_score = 0.4
        else:
            self.volume_score = 0.2
        
        # Days to expiry
        try:
            exp_date = datetime.strptime(self.contract.expiration_date, '%Y-%m-%d')
            self.days_to_expiry = (exp_date - datetime.now()).days
        except:
            self.days_to_expiry = 30
        
        # Theta score (daily decay as % of premium, for selling strategies)
        if self.strategy in ["covered_call", "cash_secured_put"]:
            if self.days_to_expiry > 0:
                daily_decay_pct = (self.quote.mid_price / self.days_to_expiry) / self.quote.mid_price * 100
                self.theta_score = min(1.0, daily_decay_pct * 10)  # 10% daily = 1.0
            else:
                self.theta_score = 0.5
        else:
            # For buying strategies, lower theta is better
            self.theta_score = 0.5
        
        # Annualized return
        if self.days_to_expiry > 0 and collateral > 0:
            period_return = self.max_profit / collateral
            self.annualized_return = (1 + period_return) ** (365 / self.days_to_expiry) - 1
        
        # Total score (weighted)
        self.total_score = (
            self.premium_score * 0.35 +
            self.spread_score * 0.25 +
            self.volume_score * 0.20 +
            self.theta_score * 0.20
        )


# ═══════════════════════════════════════════════════════════════════════════════
# QUEEN OPTIONS SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class QueenOptionsScanner:
    """
    👑 Intelligent Options Scanner
    
    Scans for optimal options opportunities based on:
    - Trading level (Level 1: covered calls, cash-secured puts)
    - Premium yield analysis
    - Spread/liquidity scoring
    - Queen Hive confidence
    """
    
    def __init__(self):
        self.client = get_options_client()
        self.trading_level = self.client.get_trading_level()
        
        # Try to connect to Queen Hive
        self.queen = None
        try:
            from aureon_queen_hive_mind import get_queen_hive
            self.queen = get_queen_hive()
            logger.info("👑 Queen Hive connected to Options Scanner")
        except Exception as e:
            logger.warning(f"Queen Hive not available: {e}")
        
        logger.info(f"👑 Queen Options Scanner initialized")
        logger.info(f"   Trading Level: {self.trading_level.name}")
    
    def scan_covered_calls(
        self,
        underlying: str,
        current_price: float,
        min_otm_pct: float = 0.03,    # 3% out of the money minimum
        max_otm_pct: float = 0.15,    # 15% out of the money maximum
        min_days_expiry: int = 7,
        max_days_expiry: int = 45,
        shares_owned: int = 100
    ) -> List[OptionsOpportunity]:
        """
        Scan for covered call opportunities.
        
        Args:
            underlying: Stock symbol
            current_price: Current stock price
            min_otm_pct: Minimum OTM percentage (strike > price by this %)
            max_otm_pct: Maximum OTM percentage
            min_days_expiry: Minimum days to expiration
            max_days_expiry: Maximum days to expiration
            shares_owned: Shares owned for covered calls
            
        Returns:
            List of scored OptionsOpportunity
        """
        if self.trading_level.value < TradingLevel.COVERED.value:
            logger.warning("❌ Trading level too low for covered calls")
            return []
        
        opportunities = []
        
        # Calculate strike range
        min_strike = current_price * (1 + min_otm_pct)
        max_strike = current_price * (1 + max_otm_pct)
        
        # Calculate date range
        min_date = (datetime.now() + timedelta(days=min_days_expiry)).strftime('%Y-%m-%d')
        max_date = (datetime.now() + timedelta(days=max_days_expiry)).strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Scanning covered calls for {underlying}")
        logger.info(f"   Price: ${current_price:.2f}")
        logger.info(f"   Strike range: ${min_strike:.2f} - ${max_strike:.2f}")
        logger.info(f"   Expiry range: {min_date} - {max_date}")
        
        # Get contracts
        contracts = self.client.get_contracts(
            underlying_symbol=underlying,
            expiration_date_gte=min_date,
            expiration_date_lte=max_date,
            option_type=OptionType.CALL,
            strike_price_gte=min_strike,
            strike_price_lte=max_strike,
            limit=50
        )
        
        if not contracts:
            logger.info(f"   No contracts found")
            return []
        
        # Get quotes for all contracts
        symbols = [c.symbol for c in contracts]
        quotes = self.client.get_quotes(symbols)
        
        for contract in contracts:
            quote = quotes.get(contract.symbol)
            if not quote or quote.bid <= 0:
                continue
            
            opp = OptionsOpportunity(
                contract=contract,
                quote=quote,
                strategy="covered_call",
                premium_score=0,
                spread_score=0,
                volume_score=0,
                theta_score=0,
            )
            
            opp.calculate_scores(current_price)
            
            # Get Queen confidence if available
            if self.queen:
                try:
                    guidance = self.queen.ask_queen_will_we_win(
                        asset=underlying,
                        exchange="alpaca",
                        opportunity_score=opp.total_score * 100,
                        context={
                            "strategy": "covered_call",
                            "strike": contract.strike_price,
                            "expiry": contract.expiration_date,
                            "premium": quote.mid_price,
                        }
                    )
                    opp.queen_confidence = guidance.get('confidence', 0.5)
                except:
                    opp.queen_confidence = 0.5
            
            opportunities.append(opp)
        
        # Sort by total score
        opportunities.sort(key=lambda x: x.total_score, reverse=True)
        
        logger.info(f"   Found {len(opportunities)} opportunities")
        
        return opportunities
    
    def scan_cash_secured_puts(
        self,
        underlying: str,
        current_price: float,
        min_otm_pct: float = 0.03,    # 3% out of the money minimum
        max_otm_pct: float = 0.15,    # 15% out of the money maximum  
        min_days_expiry: int = 7,
        max_days_expiry: int = 45,
        max_collateral: float = 10000
    ) -> List[OptionsOpportunity]:
        """
        Scan for cash-secured put opportunities.
        
        These are bullish trades where you collect premium and
        agree to buy the stock at strike price if assigned.
        """
        if self.trading_level.value < TradingLevel.COVERED.value:
            logger.warning("❌ Trading level too low for cash-secured puts")
            return []
        
        opportunities = []
        
        # Calculate strike range (OTM means below current price for puts)
        min_strike = current_price * (1 - max_otm_pct)
        max_strike = current_price * (1 - min_otm_pct)
        
        # Filter by collateral requirement
        max_affordable_strike = max_collateral / 100  # 1 contract = 100 shares
        max_strike = min(max_strike, max_affordable_strike)
        
        # Calculate date range
        min_date = (datetime.now() + timedelta(days=min_days_expiry)).strftime('%Y-%m-%d')
        max_date = (datetime.now() + timedelta(days=max_days_expiry)).strftime('%Y-%m-%d')
        
        logger.info(f"🔍 Scanning cash-secured puts for {underlying}")
        logger.info(f"   Price: ${current_price:.2f}")
        logger.info(f"   Strike range: ${min_strike:.2f} - ${max_strike:.2f}")
        logger.info(f"   Max collateral: ${max_collateral:.2f}")
        
        # Get contracts
        contracts = self.client.get_contracts(
            underlying_symbol=underlying,
            expiration_date_gte=min_date,
            expiration_date_lte=max_date,
            option_type=OptionType.PUT,
            strike_price_gte=min_strike,
            strike_price_lte=max_strike,
            limit=50
        )
        
        if not contracts:
            logger.info(f"   No contracts found")
            return []
        
        # Get quotes
        symbols = [c.symbol for c in contracts]
        quotes = self.client.get_quotes(symbols)
        
        for contract in contracts:
            quote = quotes.get(contract.symbol)
            if not quote or quote.bid <= 0:
                continue
            
            opp = OptionsOpportunity(
                contract=contract,
                quote=quote,
                strategy="cash_secured_put",
                premium_score=0,
                spread_score=0,
                volume_score=0,
                theta_score=0,
            )
            
            opp.calculate_scores(current_price)
            
            # Get Queen confidence
            if self.queen:
                try:
                    guidance = self.queen.ask_queen_will_we_win(
                        asset=underlying,
                        exchange="alpaca",
                        opportunity_score=opp.total_score * 100,
                        context={
                            "strategy": "cash_secured_put",
                            "strike": contract.strike_price,
                            "expiry": contract.expiration_date,
                            "premium": quote.mid_price,
                        }
                    )
                    opp.queen_confidence = guidance.get('confidence', 0.5)
                except:
                    opp.queen_confidence = 0.5
            
            opportunities.append(opp)
        
        opportunities.sort(key=lambda x: x.total_score, reverse=True)
        logger.info(f"   Found {len(opportunities)} opportunities")
        
        return opportunities
    
    def display_opportunities(self, opportunities: List[OptionsOpportunity], top_n: int = 5):
        """Display top opportunities in a formatted table."""
        if not opportunities:
            print("\n❌ No opportunities found")
            return
        
        print(f"\n{'='*90}")
        print(f"{'👑 TOP OPTIONS OPPORTUNITIES':^90}")
        print(f"{'='*90}")
        
        print(f"\n{'Symbol':<25} {'Strike':<10} {'Exp':<12} {'Bid/Ask':<15} {'Score':<8} {'Ann.Ret':<10}")
        print("-" * 90)
        
        for opp in opportunities[:top_n]:
            c = opp.contract
            q = opp.quote
            
            bid_ask = f"${q.bid:.2f}/${q.ask:.2f}"
            ann_ret = f"{opp.annualized_return*100:.1f}%" if opp.annualized_return > 0 else "N/A"
            
            print(f"{c.symbol:<25} ${c.strike_price:<9.2f} {c.expiration_date:<12} {bid_ask:<15} {opp.total_score:.2f}    {ann_ret:<10}")
        
        # Show best opportunity details
        if opportunities:
            best = opportunities[0]
            print(f"\n{'='*90}")
            print(f"{'🏆 BEST OPPORTUNITY':^90}")
            print(f"{'='*90}")
            print(f"\n📊 {best.contract.symbol}")
            print(f"   Strategy: {best.strategy.upper()}")
            print(f"   Strike: ${best.contract.strike_price:.2f}")
            print(f"   Expiration: {best.contract.expiration_date} ({best.days_to_expiry} days)")
            print(f"   Premium: ${best.quote.mid_price:.2f} per share (${best.quote.mid_price*100:.2f} per contract)")
            print(f"\n   Max Profit: ${best.max_profit:.2f}")
            print(f"   Max Risk: ${best.max_risk:.2f}")
            print(f"   Breakeven: ${best.breakeven:.2f}")
            print(f"   Annualized Return: {best.annualized_return*100:.1f}%")
            print(f"\n   📈 Scores:")
            print(f"      Premium Score: {best.premium_score:.2f}")
            print(f"      Spread Score: {best.spread_score:.2f}")
            print(f"      Volume Score: {best.volume_score:.2f}")
            print(f"      Theta Score: {best.theta_score:.2f}")
            print(f"      TOTAL SCORE: {best.total_score:.2f}")
            if best.queen_confidence > 0:
                print(f"      👑 Queen Confidence: {best.queen_confidence:.1%}")


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

def scan_options(symbol: str, strategy: str = "all") -> List[OptionsOpportunity]:
    """
    Quick scan for options opportunities.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL")
        strategy: "covered_call", "cash_secured_put", or "all"
    """
    scanner = QueenOptionsScanner()
    
    # Get current price from Alpaca
    from alpaca_client import get_alpaca_client
    client = get_alpaca_client()
    quote = client.get_stock_quote(symbol)
    
    if not quote:
        logger.error(f"Could not get price for {symbol}")
        return []
    
    current_price = (quote.get('bid', 0) + quote.get('ask', 0)) / 2
    
    opportunities = []
    
    if strategy in ["all", "covered_call"]:
        opportunities.extend(scanner.scan_covered_calls(symbol, current_price))
    
    if strategy in ["all", "cash_secured_put"]:
        opportunities.extend(scanner.scan_cash_secured_puts(symbol, current_price))
    
    # Sort all by score
    opportunities.sort(key=lambda x: x.total_score, reverse=True)
    
    return opportunities


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    parser = argparse.ArgumentParser(description="Queen Options Scanner")
    parser.add_argument("symbol", nargs="?", default="AAPL", help="Stock symbol to scan")
    parser.add_argument("--strategy", choices=["covered_call", "cash_secured_put", "all"], default="all")
    parser.add_argument("--price", type=float, help="Override current price")
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("👑 QUEEN OPTIONS SCANNER")
    print("=" * 70)
    
    scanner = QueenOptionsScanner()
    
    # Get current price
    if args.price:
        current_price = args.price
    else:
        try:
            from alpaca_client import get_alpaca_client
            client = get_alpaca_client()
            quote = client.get_stock_quote(args.symbol)
            if quote:
                current_price = (quote.get('bid', 0) + quote.get('ask', 0)) / 2
            else:
                print(f"❌ Could not get price for {args.symbol}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error getting price: {e}")
            print(f"   Use --price to specify manually")
            sys.exit(1)
    
    print(f"\n📊 {args.symbol} @ ${current_price:.2f}")
    
    opportunities = []
    
    if args.strategy in ["all", "covered_call"]:
        print(f"\n🔍 Scanning covered calls...")
        cc = scanner.scan_covered_calls(args.symbol, current_price)
        opportunities.extend(cc)
    
    if args.strategy in ["all", "cash_secured_put"]:
        print(f"\n🔍 Scanning cash-secured puts...")
        csp = scanner.scan_cash_secured_puts(args.symbol, current_price)
        opportunities.extend(csp)
    
    # Sort and display
    opportunities.sort(key=lambda x: x.total_score, reverse=True)
    scanner.display_opportunities(opportunities, top_n=10)
    
    print("\n" + "=" * 70)
    print("✅ Scan complete!")
    print("=" * 70)
