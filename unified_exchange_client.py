import os
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

# Load environment variables from .env file FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient
from capital_client import CapitalClient

# Updated FX rates as of November 2025 (approximate mid-market)
# These are used for Capital.com equity conversion to base currency
CAPITAL_FX_RATES: Dict[Tuple[str, str], float] = {
    ('USD', 'EUR'): 0.94,
    ('USD', 'GBP'): 0.79,   # $1 = £0.79
    ('EUR', 'USD'): 1.06,
    ('EUR', 'GBP'): 0.84,   # €1 = £0.84
    ('GBP', 'USD'): 1.27,   # £1 = $1.27
    ('GBP', 'EUR'): 1.19,   # £1 = €1.19
}

logger = logging.getLogger(__name__)

class MultiExchangeClient:
    """
    Manages multiple exchange clients simultaneously.
    Aggregates data and routes orders.
    """
    def __init__(self):
        self.clients = {
            'kraken': UnifiedExchangeClient('kraken'),
            'binance': UnifiedExchangeClient('binance'),
            'alpaca': UnifiedExchangeClient('alpaca'),
            'capital': UnifiedExchangeClient('capital')
        }
        self.dry_run = any(c.dry_run for c in self.clients.values())
        logger.info(f"Initialized MultiExchangeClient with {list(self.clients.keys())}")

    def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """
        Get balances from all exchanges.
        Returns: {'kraken': {'BTC': 0.1}, 'binance': {'BTC': 0.2}}
        """
        return {
            name: client.get_all_balances()
            for name, client in self.clients.items()
        }

    def get_consolidated_equity(self, base_currency: str = 'USD') -> float:
        """Calculate total equity across all exchanges in base currency."""
        total = 0.0
        for name, client in self.clients.items():
            # This is an approximation. A real implementation would need
            # to convert each asset to base currency using that exchange's rates.
            # For now, we rely on the client's internal tracking or simple sum if possible.
            # But UnifiedExchangeClient doesn't have get_equity().
            # We'll iterate balances and convert.
            balances = client.get_all_balances()
            for asset, amount in balances.items():
                if asset == base_currency:
                    total += amount
                else:
                    total += client.convert_to_quote(asset, amount, base_currency)
        return total

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        """Get tickers from all exchanges, tagged with source."""
        all_tickers = []
        for name, client in self.clients.items():
            tickers = client.get_24h_tickers()
            for t in tickers:
                t['source'] = name
                # Ensure symbol is unique or tagged if needed, but 'source' handles it.
            all_tickers.extend(tickers)
        return all_tickers

    def place_market_order(self, exchange: str, symbol: str, side: str, quantity=None, quote_qty=None) -> Dict[str, Any]:
        if exchange not in self.clients:
            logger.error(f"Unknown exchange: {exchange}")
            return {}
        return self.clients[exchange].place_market_order(symbol, side, quantity, quote_qty)

    def get_ticker(self, exchange: str, symbol: str) -> Dict[str, float]:
        if exchange not in self.clients:
            return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}
        return self.clients[exchange].get_ticker(symbol)
    
    def convert_to_quote(self, exchange: str, asset: str, amount: float, quote: str) -> float:
        if exchange not in self.clients:
            return 0.0
        return self.clients[exchange].convert_to_quote(asset, amount, quote)

class UnifiedExchangeClient:
    """
    Unified interface for Kraken and Binance exchanges.
    Allows the Aureon ecosystem to trade on either platform seamlessly.
    """
    
    def __init__(self, exchange_id: str = "kraken"):
        self.exchange_id = exchange_id.lower()
        self.dry_run = False
        
        if self.exchange_id == "kraken":
            self.client = KrakenClient()
            self.dry_run = self.client.dry_run
        elif self.exchange_id == "binance":
            self.client = BinanceClient()
            self.dry_run = self.client.dry_run
        elif self.exchange_id == "alpaca":
            self.client = AlpacaClient()
            self.dry_run = self.client.dry_run
        elif self.exchange_id == "capital":
            self.client = CapitalClient()
            self.dry_run = self.client.dry_run
        else:
            raise ValueError(f"Unsupported exchange: {exchange_id}")
            
        logger.info(f"Initialized UnifiedExchangeClient for {self.exchange_id} (Dry Run: {self.dry_run})")

    def get_balance(self, asset: str) -> float:
        """Get free balance for a specific asset."""
        if self.exchange_id == "kraken":
            # KrakenClient doesn't have a direct get_free_balance method exposed publicly in the snippet I saw,
            # but it has _private('/0/private/Balance').
            # Let's implement a safe wrapper.
            try:
                if self.dry_run:
                    # Mock balance for dry run if needed, or rely on client's behavior
                    return 1000.0 # Default mock
                
                res = self.client._private('/0/private/Balance', {})
                # Kraken returns assets like 'ZUSD', 'XXBT'. Need to handle mapping if strictly needed,
                # but usually passing 'USD' or 'BTC' works if the client handles it or if we check keys.
                # For now, let's try direct access and some common mappings.
                
                # Map common assets to Kraken internal names if not found
                mappings = {'BTC': 'XXBT', 'ETH': 'XETH', 'USD': 'ZUSD', 'GBP': 'ZGBP', 'EUR': 'ZEUR'}
                search_keys = [asset, mappings.get(asset, asset)]
                
                for key in search_keys:
                    if key in res:
                        return float(res[key])
                return 0.0
            except Exception as e:
                logger.error(f"Error getting Kraken balance: {e}")
                return 0.0
                
        elif self.exchange_id == "binance":
            return self.client.get_free_balance(asset)
            
        elif self.exchange_id == "alpaca":
            try:
                if asset in ['USD', 'USDT']: # Cash
                    acct = self.client.get_account()
                    return float(acct.get('cash', 0.0))
                
                # Check positions
                # Alpaca positions are by symbol e.g. 'BTCUSD'
                # But we want balance of 'BTC'.
                # We need to iterate positions.
                positions = self.client.get_positions()
                for pos in positions:
                    # pos['symbol'] might be 'BTC/USD' or 'BTCUSD'
                    sym = pos.get('symbol', '').replace('/', '')
                    if sym.startswith(asset) and (sym == asset or sym == f"{asset}USD"):
                        return float(pos.get('qty', 0.0))
                return 0.0
            except Exception as e:
                logger.error(f"Error getting Alpaca balance: {e}")
                return 0.0
                
        return 0.0

    def get_all_balances(self) -> Dict[str, float]:
        """Get all non-zero balances."""
        balances = {}
        
        if self.exchange_id == 'kraken':
            try:
                # Use KrakenClient's get_account_balance if available
                if hasattr(self.client, 'get_account_balance'):
                    raw_bals = self.client.get_account_balance()
                    for asset, amount in raw_bals.items():
                        try:
                            val = float(amount)
                            if val > 0:
                                balances[asset] = val
                        except:
                            pass
                    return balances
            except Exception as e:
                logger.error(f"Error getting Kraken balances: {e}")
                return {}
        
        if self.exchange_id == 'alpaca':
            try:
                # Cash
                acct = self.client.get_account()
                cash = float(acct.get('cash', 0.0))
                if cash > 0:
                    balances['USD'] = cash
                
                # Positions
                positions = self.client.get_positions()
                for pos in positions:
                    qty = float(pos.get('qty', 0.0))
                    if qty > 0:
                        # Symbol is usually BTC/USD. We want BTC.
                        sym = pos.get('symbol', '')
                        if '/' in sym:
                            base = sym.split('/')[0]
                            balances[base] = qty
                        else:
                            balances[sym] = qty
                return balances
            except Exception as e:
                logger.error(f"Error getting Alpaca balances: {e}")
                return {}

        if self.exchange_id == 'capital':
            try:
                return self.client.get_account_balance()
            except Exception as e:
                logger.error(f"Error getting Capital.com balances: {e}")
                return {}

        try:
            acct = self.client.account()
            for bal in acct.get("balances", []):
                val = float(bal.get("free", 0))
                if val > 0:
                    balances[bal.get("asset")] = val
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
        return balances

    def account(self) -> Dict[str, Any]:
        """Return account info in Binance format."""
        return self.client.account()

    def convert_to_quote(self, asset: str, amount: float, quote: str) -> float:
        """Convert amount of asset to quote currency value."""
        # Handle Binance Earn assets (LD prefix)
        if self.exchange_id == 'binance' and asset.startswith('LD'):
            asset = asset[2:]
            
        if hasattr(self.client, 'convert_to_quote'):
            return self.client.convert_to_quote(asset, amount, quote)
            
        if self.exchange_id == 'alpaca':
            if asset == quote: return amount
            try:
                # Try to get latest quote for asset/quote
                symbol = f"{asset}/{quote}"
                quotes = self.client.get_latest_crypto_quotes([symbol])
                if symbol in quotes:
                    # Use mid price
                    bid = float(quotes[symbol].get('bp', 0))
                    ask = float(quotes[symbol].get('ap', 0))
                    if bid > 0 and ask > 0:
                        price = (bid + ask) / 2
                        return amount * price
                
                # Try reverse
                symbol_rev = f"{quote}/{asset}"
                quotes = self.client.get_latest_crypto_quotes([symbol_rev])
                if symbol_rev in quotes:
                    bid = float(quotes[symbol_rev].get('bp', 0))
                    ask = float(quotes[symbol_rev].get('ap', 0))
                    if bid > 0 and ask > 0:
                        price = (bid + ask) / 2
                        return amount / price
            except:
                pass
            return 0.0

        if self.exchange_id == 'capital':
            asset = asset.upper()
            quote = quote.upper()
            if asset == quote:
                return amount
            if amount <= 0:
                return 0.0

            direct_rate = CAPITAL_FX_RATES.get((asset, quote))
            if direct_rate:
                return amount * direct_rate

            # Try two-step conversion via common pivots
            for pivot in ('USD', 'EUR', 'GBP'):
                if pivot in (asset, quote):
                    continue
                first = CAPITAL_FX_RATES.get((asset, pivot))
                second = CAPITAL_FX_RATES.get((pivot, quote))
                if first and second:
                    return amount * first * second

            try:
                symbol = f"{asset}{quote}"
                ticker = self.get_ticker(symbol)
                price = float(ticker.get('price', 0) or 0)
                if 0 < price < 1000:  # Sanity cap for currency pairs
                    return amount * price
            except Exception:
                pass

            # Final attempt: convert via USD using static rates
            to_usd = CAPITAL_FX_RATES.get((asset, 'USD'))
            from_usd = CAPITAL_FX_RATES.get(('USD', quote))
            if to_usd and from_usd:
                return amount * to_usd * from_usd
            return 0.0
        
        # Fallback for BinanceClient if it doesn't have it (it doesn't in the snippet)
        # We can implement a basic conversion using ticker
        if asset == quote:
            return amount
        
        try:
            # Try direct pair
            print(f"DEBUG: converting {asset} to {quote}")
            ticker = self.get_ticker(f"{asset}{quote}")
            if ticker['price'] > 0:
                return amount * ticker['price']
                
            # Try reverse pair (e.g. quote/asset) - unlikely for stablecoins but possible
            ticker = self.get_ticker(f"{quote}{asset}")
            if ticker['price'] > 0:
                return amount / ticker['price']
                
            # Try via USDT if quote is not USDT
            if quote != 'USDT':
                val_usdt = self.convert_to_quote(asset, amount, 'USDT')
                if val_usdt > 0:
                    return self.convert_to_quote('USDT', val_usdt, quote)
                    
        except:
            pass
        return 0.0

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        """Get 24h ticker statistics for all symbols."""
        if self.exchange_id == 'capital':
            try:
                return self.client.get_24h_tickers()
            except Exception as e:
                logger.error(f"Capital.com get_24h_tickers error: {e}")
                return []

        if self.exchange_id == 'kraken':
            try:
                # Use the KrakenClient's get_24h_tickers which handles all pairs properly
                return self.client.get_24h_tickers()
            except Exception as e:
                logger.error(f"Kraken get_24h_tickers error: {e}")
                return []

        if self.exchange_id == 'alpaca':
            try:
                # Fetch active crypto assets
                assets = self.client.get_assets(asset_class='crypto')
                symbols = [a['symbol'] for a in assets if a['status'] == 'active']
                
                # Limit to top 50 to avoid huge requests if many assets
                # Or filter by base currency
                # Alpaca crypto symbols are like BTC/USD
                relevant_symbols = [s for s in symbols if s.endswith('/USD') or s.endswith('/USDT')]
                relevant_symbols = relevant_symbols[:50] 
                
                if not relevant_symbols:
                    return []
                    
                # Get latest bars (24h is hard, let's get latest quotes or bars)
                # Actually, get_crypto_bars with 1Day timeframe?
                # But we need 24h change.
                # Let's get 1Day bars limit 2.
                
                # For simplicity in this unified interface, let's just get latest quotes 
                # and assume 0 change if we can't easily calculate it without history.
                # OR, use get_crypto_bars for 1Day.
                
                bars = self.client.get_crypto_bars(relevant_symbols, timeframe="1D", limit=2)
                # bars response: {'bars': {'BTC/USD': [{...}, {...}]}}
                
                all_tickers = []
                for sym, data in bars.get('bars', {}).items():
                    if len(data) < 1: continue
                    latest = data[-1]
                    prev = data[-2] if len(data) > 1 else latest
                    
                    close = float(latest['c'])
                    open_p = float(latest['o']) # Open of current day, or use prev close?
                    # 24h change usually implies rolling 24h. 1D bar is 00:00 UTC.
                    # Let's use open of the day as approximation.
                    
                    change_pct = ((close - open_p) / open_p * 100) if open_p > 0 else 0
                    volume = float(latest['v']) * close # Approx quote volume
                    
                    all_tickers.append({
                        'symbol': sym,
                        'lastPrice': close,
                        'priceChangePercent': change_pct,
                        'quoteVolume': volume
                    })
                return all_tickers
            except Exception as e:
                logger.error(f"Alpaca get_24h_tickers error: {e}")
                return []

        if hasattr(self.client, 'get_24h_tickers'):
            tickers = self.client.get_24h_tickers()
            # Normalize Binance data (strings to floats)
            if self.exchange_id == 'binance':
                for t in tickers:
                    if 'priceChangePercent' in t:
                        try:
                            t['priceChangePercent'] = float(t['priceChangePercent'])
                        except:
                            t['priceChangePercent'] = 0.0
                    if 'lastPrice' in t:
                        try:
                            t['lastPrice'] = float(t['lastPrice'])
                        except:
                            t['lastPrice'] = 0.0
            return tickers
        return []

    def get_ticker(self, symbol: str) -> Dict[str, float]:
        """
        Get current ticker data (price, bid, ask).
        Returns dict with 'price', 'bid', 'ask'.
        """
        if self.exchange_id == "kraken":
            # Kraken uses pairs like 'XBTUSD'
            try:
                # Normalize to Kraken altname (no slash, upper)
                alt = symbol.replace('/', '').upper()
                # Kraken expects the internal pair name (e.g. XXBTZUSD). Map altname -> internal.
                self.client._load_asset_pairs()
                pair = self.client._alt_to_int.get(alt, alt)

                # Use KrakenClient ticker helper so mapping/format stays consistent
                result = self.client._ticker([alt])
                if not result:
                    logger.error(f"Kraken ticker empty result for {alt} (pair {pair})")
                    return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

                key, data = next(iter(result.items()))
                try:
                    price = float(data.get('c', [0])[0])
                    bid = float(data.get('b', [0])[0])
                    ask = float(data.get('a', [0])[0])
                except Exception as inner:
                    logger.error(f"Error parsing Kraken ticker for {alt} ({key}): {inner}")
                    return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

                return {'price': price, 'bid': bid, 'ask': ask}
            except Exception as e:
                logger.error(f"Error getting Kraken ticker: {e}")
                return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        elif self.exchange_id == "binance":
            try:
                # Binance has /api/v3/ticker/price and /api/v3/ticker/bookTicker
                # Let's use bookTicker for bid/ask
                res = self.client.session.get(f"{self.client.base}/api/v3/ticker/bookTicker", params={"symbol": symbol}).json()
                # {'symbol': 'BTCUSDT', 'bidPrice': '...', 'askPrice': '...'}
                if isinstance(res, dict) and 'bidPrice' in res and 'askPrice' in res:
                    bid = float(res['bidPrice'])
                    ask = float(res['askPrice'])
                    price = (bid + ask) / 2.0  # Approximation
                    return {'price': price, 'bid': bid, 'ask': ask}

                # Fallback: try ticker/price if bookTicker failed or returned error payload
                price_res = self.client.session.get(f"{self.client.base}/api/v3/ticker/price", params={"symbol": symbol}).json()
                if isinstance(price_res, dict) and 'price' in price_res:
                    try:
                        price = float(price_res['price'])
                    except Exception:
                        price = 0.0
                    return {'price': price, 'bid': price, 'ask': price}

                logger.error(f"Binance ticker unexpected payload for {symbol}: {res}")
                return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}
            except Exception as e:
                logger.error(f"Error getting Binance ticker: {e}")
                return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}
        
        elif self.exchange_id == "alpaca":
            try:
                quotes = self.client.get_latest_crypto_quotes([symbol])
                if symbol in quotes:
                    q = quotes[symbol]
                    bid = float(q.get('bp', 0))
                    ask = float(q.get('ap', 0))
                    price = (bid + ask) / 2
                    return {'price': price, 'bid': bid, 'ask': ask}
            except Exception as e:
                logger.error(f"Error getting Alpaca ticker: {e}")
                return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        elif self.exchange_id == "capital":
            try:
                return self.client.get_ticker(symbol)
            except Exception as e:
                logger.error(f"Error getting Capital.com ticker: {e}")
                return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

    def place_market_order(self, symbol: str, side: str, quantity: float = None, quote_qty: float = None) -> Dict[str, Any]:
        """
        Place a market order.
        side: 'buy' or 'sell'
        quantity: amount of base asset (e.g. BTC)
        quote_qty: amount of quote asset (e.g. USD)
        """
        side = side.lower()
        
        if self.exchange_id == "kraken":
            # Use KrakenClient's place_market_order which returns Binance-compatible format
            try:
                return self.client.place_market_order(symbol, side, quantity=quantity, quote_qty=quote_qty)
            except Exception as e:
                logger.error(f"Error placing Kraken order: {e}")
                return {}

        elif self.exchange_id == "binance":
            return self.client.place_market_order(symbol, side, quantity=quantity, quote_qty=quote_qty)
            
        elif self.exchange_id == "alpaca":
            # Alpaca uses 'qty' for base asset, 'notional' for quote asset (if supported for crypto)
            # Crypto API supports 'qty' or 'notional'.
            try:
                if quantity:
                    return self.client.place_order(symbol, quantity, side, type="market")
                elif quote_qty:
                    # Alpaca supports notional for market orders
                    # But let's check if place_order supports it.
                    # My AlpacaClient.place_order takes qty.
                    # I should update AlpacaClient or calculate qty here.
                    # Let's calculate qty.
                    ticker = self.get_ticker(symbol)
                    if ticker['price'] > 0:
                        qty = quote_qty / ticker['price']
                        return self.client.place_order(symbol, qty, side, type="market")
            except Exception as e:
                logger.error(f"Error placing Alpaca order: {e}")
                return {}

        elif self.exchange_id == "capital":
            try:
                # Capital.com uses 'size' (quantity)
                if quantity:
                    return self.client.place_market_order(symbol, side, quantity)
                elif quote_qty:
                    ticker = self.get_ticker(symbol)
                    if ticker['price'] > 0:
                        qty = quote_qty / ticker['price']
                        return self.client.place_market_order(symbol, side, qty)
            except Exception as e:
                logger.error(f"Error placing Capital.com order: {e}")
                return {}

        return {}

    def get_standardized_pair(self, base: str, quote: str) -> str:
        """Return the symbol in the format expected by the exchange."""
        base = base.upper()
        quote = quote.upper()
        
        if self.exchange_id == "kraken":
            # Kraken often uses XBT instead of BTC, but the API accepts 'BTCUSD' usually and maps it.
            # However, for consistency:
            if base == 'BTC': base = 'XBT'
            # if quote == 'BTC': quote = 'XBT' # Sometimes
            return f"{base}{quote}"
        elif self.exchange_id == "binance":
            return f"{base}{quote}"
        elif self.exchange_id == "alpaca":
            return f"{base}/{quote}"
        return f"{base}{quote}"

    def get_symbol_filters(self, symbol: str) -> Dict[str, float]:
        if hasattr(self.client, 'get_symbol_filters'):
            try:
                return self.client.get_symbol_filters(symbol)
            except Exception:
                return {}
        return {}

    def adjust_quantity(self, symbol: str, quantity: float) -> float:
        if hasattr(self.client, 'adjust_quantity'):
            try:
                return self.client.adjust_quantity(symbol, quantity)
            except Exception:
                return quantity
        return quantity
