import logging
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class MarketPulse:
    """
    Global Market Analysis Engine.
    Aggregates data from Kraken, Binance, and Alpaca to provide a holistic view of financial markets.
    """
    def __init__(self, client):
        self.client = client

    def analyze_market(self) -> Dict[str, Any]:
        """
        Perform a full market scan and return high-level metrics.
        """
        tickers = self.client.get_24h_tickers()
        if not tickers:
            return {"status": "No Data"}

        # 1. Global Sentiment (Crypto vs Stocks)
        crypto_tickers = [t for t in tickers if t.get('source') in ['kraken', 'binance']]
        # Treat Alpaca and Capital.com as "Traditional/Stocks" (though they have crypto too, this is a rough split)
        stock_tickers = [t for t in tickers if t.get('source') in ['alpaca', 'capital']]

        crypto_sentiment = self._calculate_sentiment(crypto_tickers)
        stock_sentiment = self._calculate_sentiment(stock_tickers)

        # 2. Arbitrage / Cross-Exchange Comparison
        arb_opps = self._find_arbitrage(tickers)

        # 3. Top Movers
        def safe_pct(t):
            try:
                return float(t.get('priceChangePercent', 0))
            except (ValueError, TypeError):
                return 0.0

        top_gainers = sorted(tickers, key=safe_pct, reverse=True)[:5]
        top_losers = sorted(tickers, key=safe_pct)[:5]

        return {
            "crypto_sentiment": crypto_sentiment,
            "stock_sentiment": stock_sentiment,
            "arbitrage_opportunities": arb_opps,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "total_assets_scanned": len(tickers)
        }

    def _calculate_sentiment(self, tickers: List[Dict]) -> Dict[str, float]:
        if not tickers:
            return {"score": 0.0, "label": "Neutral"}
        
        # Simple average of 24h change
        changes = [float(t.get('priceChangePercent', 0)) for t in tickers]
        avg_change = sum(changes) / len(changes)
        
        # Advance/Decline Ratio
        advancers = len([c for c in changes if c > 0])
        decliners = len([c for c in changes if c < 0])
        ratio = advancers / decliners if decliners > 0 else float('inf')

        label = "Neutral"
        if avg_change > 2.0: label = "Bullish"
        elif avg_change > 5.0: label = "Very Bullish"
        elif avg_change < -2.0: label = "Bearish"
        elif avg_change < -5.0: label = "Very Bearish"

        return {
            "avg_change_24h": avg_change,
            "advance_decline_ratio": ratio,
            "label": label
        }

    def _find_arbitrage(self, tickers: List[Dict]) -> List[Dict]:
        """
        Find assets listed on multiple exchanges with price divergence.
        """
        # Group by symbol (normalized)
        assets = defaultdict(list)
        for t in tickers:
            # Normalize symbol: remove USDT, USD, etc.
            raw_sym = t.get('symbol', '').upper()
            norm_sym = raw_sym.replace('USDT', '').replace('USD', '').replace('XBT', 'BTC').replace('XXBT', 'BTC').replace('ZUSD', '').replace('/', '')
            
            # Filter out weird ones or too short
            if len(norm_sym) < 2: continue
            
            assets[norm_sym].append(t)

        opportunities = []
        for sym, listings in assets.items():
            if len(listings) < 2: continue
            
            # Compare prices
            prices = []
            for l in listings:
                p = float(l.get('lastPrice', 0))
                if p > 0:
                    prices.append({
                        'source': l.get('source'),
                        'price': p,
                        'symbol': l.get('symbol')
                    })
            
            if len(prices) < 2: continue
            
            # Find max divergence
            prices.sort(key=lambda x: x['price'])
            min_p = prices[0]
            max_p = prices[-1]
            
            diff_pct = (max_p['price'] - min_p['price']) / min_p['price'] * 100
            
            if diff_pct > 1.5: # 1.5% threshold
                opportunities.append({
                    'asset': sym,
                    'spread_pct': diff_pct,
                    'buy_at': min_p,
                    'sell_at': max_p
                })
                
        return sorted(opportunities, key=lambda x: x['spread_pct'], reverse=True)
