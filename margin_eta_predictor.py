#!/usr/bin/env python3
"""
MARGIN ETA PREDICTOR - TIME-TO-PROFIT CALCULATOR
================================================

Estimates when margin positions will reach profitability based on:
1. Current position cost basis and breakeven
2. Real-time market prices from Binance/Kraken
3. Historical volatility analysis
4. Confidence scoring for ETA reliability

Usage:
    python margin_eta_predictor.py          # Analyze active margin positions
    python margin_eta_predictor.py --watch  # 60-second live update loop
"""

import json
import time
import urllib.request
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Binance free API endpoints (no auth)
BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
KRAKEN_PUBLIC_URL = "https://api.kraken.com/0/public"

@dataclass
class PositionETA:
    """ETA estimate for a single position."""
    symbol: str
    exchange: str
    leverage: float
    entry_price: float
    current_price: float
    breakeven_price: float
    volume: float
    cost_basis: float
    
    # Distance metrics
    pct_to_breakeven: float
    pct_from_entry: float
    
    # Volatility & prediction
    hourly_volatility: float
    sessions_to_breakeven: float  # Based on hourly wins
    eta_minutes: float
    confidence: float  # 0.0-1.0
    
    # Scenario analysis
    bullish_eta: float  # Time if +1σ move
    bearish_eta: float  # Time if -1σ move
    
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class MarginETAPredictor:
    """Real-time ETA calculator for margin positions."""
    
    def __init__(self):
        self.margin_state_path = '/workspaces/aureon-trading/kraken_margin_penny_state.json'
        self.positions: Dict = {}
        self.price_cache: Dict[str, float] = {}
        self.volatility_cache: Dict[str, deque] = {}
        self._load_positions()
    
    def _load_positions(self) -> None:
        """Load current margin positions from state file."""
        try:
            with open(self.margin_state_path, 'r') as f:
                state = json.load(f)
                self.positions = state.get('active_trades', {})
                logger.info(f"Loaded {len(self.positions)} active margin positions")
        except Exception as e:
            logger.error(f"Failed to load margin state: {e}")
            self.positions = {}
    
    def _get_binance_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Binance (free, no auth required)."""
        try:
            # Convert symbol: AAVEUSD -> AAVEUSDT (Binance uses USDT)
            binance_symbol = symbol.replace('USD', 'USDT')
            url = f"{BINANCE_TICKER_URL}?symbol={binance_symbol}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'MarginETA/1.0')
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                price = float(data['price'])
                self.price_cache[symbol] = price
                return price
        except Exception as e:
            logger.debug(f"Failed to fetch {symbol} from Binance: {e}")
            return None
    
    def _get_kraken_price(self, symbol: str) -> Optional[float]:
        """Fetch current price from Kraken public API."""
        try:
            # Use Kraken's public ticker
            url = f"{KRAKEN_PUBLIC_URL}/Ticker?pair={symbol}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'MarginETA/1.0')
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                result = data.get('result', {})
                if symbol in result:
                    ticker = result[symbol]
                    # c = [close_price, num_trades]
                    price = float(ticker['c'][0])
                    self.price_cache[symbol] = price
                    return price
        except Exception as e:
            logger.debug(f"Failed to fetch {symbol} from Kraken: {e}")
            return None
    
    def _get_current_price(self, symbol: str, exchange: str) -> Optional[float]:
        """Get current price from cache or API."""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        
        # Try exchange-specific API
        if exchange.lower() == 'kraken':
            return self._get_kraken_price(symbol)
        else:
            return self._get_binance_price(symbol)
    
    def _estimate_hourly_volatility(self, symbol: str) -> float:
        """
        Estimate hourly volatility from recent price history.
        Returns std dev of hourly percentage changes.
        """
        try:
            # Try to get 24 hours of 1h candles from Binance
            binance_symbol = symbol.replace('USD', 'USDT')
            url = f"{BINANCE_KLINES_URL}?symbol={binance_symbol}&interval=1h&limit=24"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'MarginETA/1.0')
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                candles = json.loads(resp.read().decode())
                
            if len(candles) < 2:
                return 0.02  # Default 2% hourly
            
            # Calculate hourly returns
            closes = [float(c[4]) for c in candles]  # Close price
            returns = []
            for i in range(1, len(closes)):
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(abs(ret))
            
            # Average absolute hourly return as volatility metric
            hourly_vol = sum(returns) / len(returns) if returns else 0.02
            return max(hourly_vol, 0.001)  # Floor at 0.1%
        except Exception as e:
            logger.debug(f"Failed to estimate volatility for {symbol}: {e}")
            return 0.02  # Default 2% hourly volatility
    
    def calculate_eta(self, symbol: str, trade_data: Dict) -> Optional[PositionETA]:
        """Calculate ETA for a single margin position."""
        try:
            entry_price = trade_data['entry_price']
            breakeven_price = trade_data['breakeven_price']
            volume = trade_data['volume']
            cost = trade_data['cost']
            leverage = trade_data['leverage']
            exchange = 'kraken'  # From margin penny trader
            
            # Get current price
            current_price = self._get_current_price(symbol, exchange)
            if current_price is None:
                logger.warning(f"Could not fetch price for {symbol}, using entry price")
                current_price = entry_price
            
            # Calculate distances
            pct_to_breakeven = ((breakeven_price - current_price) / current_price) * 100
            pct_from_entry = ((current_price - entry_price) / entry_price) * 100
            
            # If already at breakeven or past it
            if current_price >= breakeven_price:
                return PositionETA(
                    symbol=symbol,
                    exchange=exchange,
                    leverage=leverage,
                    entry_price=entry_price,
                    current_price=current_price,
                    breakeven_price=breakeven_price,
                    volume=volume,
                    cost_basis=cost,
                    pct_to_breakeven=pct_to_breakeven,
                    pct_from_entry=pct_from_entry,
                    hourly_volatility=0,
                    sessions_to_breakeven=0,
                    eta_minutes=0,
                    confidence=1.0,
                    bullish_eta=0,
                    bearish_eta=0,
                )
            
            # Estimate hourly volatility
            hourly_volatility = self._estimate_hourly_volatility(symbol)
            
            # Scenarios: How many hourly moves to reach breakeven?
            required_move = abs(pct_to_breakeven) / 100.0
            sessions_to_breakeven = required_move / hourly_volatility if hourly_volatility > 0 else 999
            
            # ETA in minutes (assume 1 session = 60 mins, but trading happens 24/7)
            # More conservative: assume 2-4 moves per day for alts
            eta_minutes = sessions_to_breakeven * 60 * 0.5  # 50% of expected sessions
            
            # Confidence decreases with:
            # - Smaller volatility (harder to predict)
            # - Larger required move
            # - Short history
            confidence = min(1.0, hourly_volatility * 15) * (1.0 - min(required_move / 0.1, 1.0))
            
            # Scenario analysis (±1σ volatility)
            bullish_move = hourly_volatility
            bearish_move = hourly_volatility
            
            bullish_sessions = max(0, (required_move - bullish_move) / hourly_volatility) if hourly_volatility > 0 else 999
            bearish_sessions = (required_move + bearish_move) / hourly_volatility if hourly_volatility > 0 else 999
            
            bullish_eta = bullish_sessions * 60 * 0.5
            bearish_eta = bearish_sessions * 60 * 0.5
            
            return PositionETA(
                symbol=symbol,
                exchange=exchange,
                leverage=leverage,
                entry_price=entry_price,
                current_price=current_price,
                breakeven_price=breakeven_price,
                volume=volume,
                cost_basis=cost,
                pct_to_breakeven=pct_to_breakeven,
                pct_from_entry=pct_from_entry,
                hourly_volatility=hourly_volatility * 100,  # As percentage
                sessions_to_breakeven=sessions_to_breakeven,
                eta_minutes=eta_minutes,
                confidence=confidence,
                bullish_eta=bullish_eta,
                bearish_eta=bearish_eta,
            )
        except Exception as e:
            logger.error(f"Failed to calculate ETA for {symbol}: {e}")
            return None
    
    def predict_all(self) -> List[PositionETA]:
        """Calculate ETA for all active margin positions."""
        self._load_positions()
        results = []
        
        for symbol, trade_data in self.positions.items():
            eta = self.calculate_eta(symbol, trade_data)
            if eta:
                results.append(eta)
        
        return results
    
    def print_report(self, etas: List[PositionETA]) -> None:
        """Print formatted ETA report."""
        print("\n" + "="*100)
        print("MARGIN ETA PREDICTION REPORT")
        print("="*100)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        if not etas:
            print("No active margin positions to analyze.")
            return
        
        for eta in etas:
            print(f"Symbol: {eta.symbol} | Exchange: {eta.exchange.upper()} | Leverage: {eta.leverage}x")
            print(f"  Entry Price: {eta.entry_price:.6f} | Current: {eta.current_price:.6f} | Breakeven: {eta.breakeven_price:.6f}")
            print(f"  Change from Entry: {eta.pct_from_entry:+.2f}% | Distance to Breakeven: {eta.pct_to_breakeven:+.2f}%")
            print()
            
            if eta.eta_minutes == 0:
                print(f"  ✅ AT PROFITABILITY: Position is already profitable!")
            else:
                print(f"  📊 Hourly Volatility: {eta.hourly_volatility:.2f}%")
                print(f"  ⏱️  ESTIMATED TIME-TO-PROFIT:")
                print(f"     Base Estimate:  {eta.eta_minutes:.0f} minutes ({eta.eta_minutes/60:.1f} hours)")
                print(f"     Bullish Case:   {eta.bullish_eta:.0f} minutes ({eta.bullish_eta/60:.1f} hours)")
                print(f"     Bearish Case:   {eta.bearish_eta:.0f} minutes ({eta.bearish_eta/60:.1f} hours)")
                print(f"  🎯 Confidence Score: {eta.confidence*100:.0f}%")
            
            print()
        
        # Summary
        total_cost = sum(e.cost_basis for e in etas)
        profitable = sum(1 for e in etas if e.eta_minutes == 0)
        avg_confidence = sum(e.confidence for e in etas) / len(etas) if etas else 0
        
        print("="*100)
        print(f"SUMMARY: {len(etas)} positions | {profitable} profitable | Total cost: ${total_cost:.2f}")
        print(f"Average ETA Confidence: {avg_confidence*100:.0f}%")
        print("="*100 + "\n")


def main():
    """Run margin ETA predictor."""
    import sys
    
    predictor = MarginETAPredictor()
    etas = predictor.predict_all()
    predictor.print_report(etas)
    
    # Optional: Save report to JSON
    try:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'positions': [asdict(eta) for eta in etas],
        }
        with open('/workspaces/aureon-trading/margin_eta_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info("ETA report saved to margin_eta_report.json")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
    
    # Watch mode (continuous monitoring)
    if '--watch' in sys.argv:
        print("\n📡 WATCH MODE - Updating every 60 seconds (Ctrl+C to exit)")
        try:
            while True:
                time.sleep(60)
                predictor = MarginETAPredictor()
                etas = predictor.predict_all()
                predictor.print_report(etas)
        except KeyboardInterrupt:
            print("\n✋ Watch mode stopped.")


if __name__ == '__main__':
    main()
