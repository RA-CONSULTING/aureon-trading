import os
import logging
import requests
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # Fallback
except ImportError:
    pass

logger = logging.getLogger(__name__)

class CapitalClient:
    """
    Client for Capital.com API.
    Handles session management and trading operations.
    """
    def __init__(self):
        self.api_key = os.getenv('CAPITAL_API_KEY')
        self.identifier = os.getenv('CAPITAL_IDENTIFIER')
        self.password = os.getenv('CAPITAL_PASSWORD')
        self.demo_mode = os.getenv('CAPITAL_DEMO', '0') == '1'
        
        # Debug: Show what's loaded
        has_key = bool(self.api_key)
        has_id = bool(self.identifier)
        has_pwd = bool(self.password)
        print(f"🌐 Capital.com: key={'✓' if has_key else '✗'}, id={'✓' if has_id else '✗'}, pwd={'✓' if has_pwd else '✗'}, demo={self.demo_mode}")
        
        if self.demo_mode:
            self.base_url = "https://demo-api-capital.backend-capital.com/api/v1"
        else:
            self.base_url = "https://api-capital.backend-capital.com/api/v1"
            
        self.cst = None
        self.x_security_token = None
        self.session_start_time = 0
        self.dry_run = False  # ALWAYS LIVE
        self.market_cache: List[Dict[str, Any]] = []
        self.market_index: Dict[str, Dict[str, Any]] = {}
        self.market_cache_time = 0.0
        self.market_cache_ttl = int(os.getenv('CAPITAL_MARKET_CACHE_TTL', '900'))  # 15 minutes
        self._rate_limit_until = 0  # Timestamp when rate limit expires
        self._rate_limit_logged = False  # Only log rate limits once
        self._session_error_logged = False  # Only log session errors once
        
        if not self.api_key or not self.identifier or not self.password:
            logger.warning("Capital.com credentials not fully set. Client will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self._create_session()

    def _create_session(self):
        """Create a new session to get CST and X-SECURITY-TOKEN."""
        if not self.enabled:
            return
        
        # Check if we're rate limited
        if time.time() < self._rate_limit_until:
            return  # Still rate limited, skip silently
        
        # Check if session is still valid (avoid unnecessary re-auth within 50 min window)
        if (self.cst and self.x_security_token and 
            (time.time() - self.session_start_time) < (50 * 60)):  # 50 min buffer
            logger.debug("Capital.com session still valid (within 50 min), skipping re-auth")
            return

        url = f"{self.base_url}/session"
        payload = {
            "identifier": self.identifier,
            "password": self.password
        }
        headers = {
            "X-CAP-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                self.cst = response.headers.get('CST')
                self.x_security_token = response.headers.get('X-SECURITY-TOKEN')
                self.session_start_time = time.time()
                self._session_error_logged = False  # Reset on success
                logger.info("Capital.com session established.")
            elif response.status_code == 429 or 'too-many.requests' in response.text.lower():
                # Rate limited - back off for 5 minutes
                self._rate_limit_until = time.time() + 300
                if not self._session_error_logged:
                    logger.warning("Capital.com rate limited - backing off for 5 minutes")
                    self._session_error_logged = True
            else:
                if not self._session_error_logged:
                    logger.error(f"Failed to create Capital.com session: {response.text}")
                    self._session_error_logged = True
                self.enabled = False
        except Exception as e:
            if not self._session_error_logged:
                logger.error(f"Capital.com connection error: {e}")
                self._session_error_logged = True
            self.enabled = False

    def _session_is_expired(self) -> bool:
        """Capital.com sessions can expire; refresh after 55 minutes or when tokens missing."""
        if not self.cst or not self.x_security_token:
            return True
        # Refresh after ~55 minutes proactively
        return (time.time() - self.session_start_time) > (55 * 60)

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Perform an API request with automatic session refresh and one retry on
        invalid session token or HTTP 401.
        """
        # Return error response if client is disabled (don't raise exception)
        if not self.enabled:
            class DisabledResponse:
                status_code = 503
                text = '{\"errorCode\":\"client.disabled\"}'
                def json(self):
                    return {"errorCode": "client.disabled"}
            return DisabledResponse()

        # Proactive refresh
        if self._session_is_expired():
            logger.debug("Capital.com session expired; refreshing")
            self._create_session()

        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        try:
            resp = requests.request(method.upper(), url, headers=headers, params=params, json=json_body, timeout=20)
        except Exception as e:
            logger.error(f"Capital.com request error ({method} {path}): {e}")
            raise

        # Rate limit handling
        rate_limit_hit = resp.status_code == 429 or ('too-many.requests' in (resp.text or '').lower())
        if rate_limit_hit:
            self._rate_limit_until = time.time() + 300
            if not self._rate_limit_logged:
                logger.warning("Capital.com rate limited - backing off for 5 minutes")
                self._rate_limit_logged = True
            return resp

        # Reset rate limit log flag on success
        if resp.status_code == 200 and self._rate_limit_logged:
            self._rate_limit_logged = False

        # Handle invalid session
        if resp.status_code in (401, 403) or ('error.invalid.session.token' in (resp.text or '').lower()):
            logger.warning("Capital.com session invalid; attempting re-login and retry")
            self._create_session()
            headers = self._get_headers()
            resp = requests.request(method.upper(), url, headers=headers, params=params, json=json_body, timeout=20)
        return resp

    def _get_headers(self):
        """Get headers for authenticated requests."""
        if not self.enabled:
            return {}  # Don't try to create session when disabled
        
        if not self.cst or not self.x_security_token:
            self._create_session()
            
        # If session creation failed, return empty headers
        if not self.cst or not self.x_security_token:
            return {}
            
        return {
            "X-CAP-API-KEY": self.api_key,
            "CST": self.cst,
            "X-SECURITY-TOKEN": self.x_security_token,
            "Content-Type": "application/json"
        }

    @staticmethod
    def _canonicalize(value: Optional[str]) -> str:
        """Normalize symbols/epics for robust matching."""
        if not value:
            return ""
        return "".join(ch for ch in str(value).upper() if ch.isalnum())

    def _update_market_index(self, markets: List[Dict[str, Any]]):
        """Build fast lookup index for epic/instrument names."""
        index: Dict[str, Dict[str, Any]] = {}
        for m in markets:
            for key in (
                self._canonicalize(m.get('epic')),
                self._canonicalize(m.get('instrumentName')),
                self._canonicalize(m.get('symbol')),
                self._canonicalize(m.get('marketId')),
            ):
                if key and key not in index:
                    index[key] = m
        self.market_index = index

    def get_all_markets(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discover all available Capital.com markets by traversing the market navigation tree.
        This ensures we can trade any listed epic instead of a small search subset.
        """
        if not self.enabled:
            return []

        if (
            not force_refresh
            and self.market_cache
            and (time.time() - self.market_cache_time) < self.market_cache_ttl
        ):
            return self.market_cache

        markets: List[Dict[str, Any]] = []
        queue: List[Optional[str]] = [None]
        visited: set = set()

        while queue:
            node_id = queue.pop(0)
            path = '/marketnavigation' if not node_id else f'/marketnavigation/{node_id}'
            try:
                response = self._request('GET', path)
                if response.status_code != 200:
                    logger.warning(f"Capital.com marketnavigation failed for {node_id}: {response.text}")
                    continue

                data = response.json() or {}
                node_markets = data.get('markets', [])
                if node_markets:
                    markets.extend(node_markets)

                for node in data.get('nodes', []):
                    nid = node.get('id') or node.get('nodeId') or node.get('identifier') or node.get('name')
                    if not nid:
                        continue
                    if nid in visited:
                        continue
                    visited.add(nid)
                    queue.append(nid)
            except Exception as e:
                logger.error(f"Capital.com navigation error at node {node_id}: {e}")
                continue

        self.market_cache = markets
        self.market_cache_time = time.time()
        self._update_market_index(markets)
        logger.info(f"Capital.com market catalogue loaded ({len(markets)} markets)")
        return markets

    def _resolve_market(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Map a user-facing symbol (e.g., BTCUSD, TSLA) to the corresponding Capital.com market entry.
        Falls back to the search endpoint if the market isn't in cache yet.
        """
        if not symbol:
            return None

        canonical = self._canonicalize(symbol)
        markets = self.get_all_markets()
        if canonical in self.market_index:
            return self.market_index[canonical]

        # Partial match on epic or instrument name
        for m in markets:
            if canonical in self._canonicalize(m.get('epic')) or canonical in self._canonicalize(m.get('instrumentName')):
                return m

        # Fallback: use search endpoint to pull the market and refresh cache
        try:
            search_resp = self._request('GET', '/markets', params={'searchTerm': symbol, 'pageSize': 50})
            if search_resp.status_code == 200:
                data = search_resp.json() or {}
                found = data.get('markets', [])
                if found:
                    markets.extend(found)
                    self._update_market_index(markets)
                    self.market_cache = markets
                    self.market_cache_time = time.time()
                    return found[0]
        except Exception as e:
            logger.error(f"Capital.com search failed for {symbol}: {e}")

        return None

    def _get_market_snapshot(self, epic: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed market info (including bid/ask) for a specific epic."""
        if time.time() < self._rate_limit_until:
            return None  # Silently skip if globally rate limited
            
        try:
            response = self._request('GET', f'/markets/{epic}')
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429 or 'too-many.requests' in (response.text or '').lower():
                return None
            logger.error(f"Capital.com market snapshot failed for {epic}: {response.text}")
        except Exception as e:
            logger.error(f"Capital.com market snapshot error for {epic}: {e}")
        return None

    def get_account_balance(self) -> Dict[str, float]:
        """Get account balances.
        
        Note: Capital.com API may report currency incorrectly (e.g. 'USD' for GBP accounts).
        We override to use the actual account currency which is GBP for UK accounts.
        """
        if not self.enabled:
            return {}
        
        # Override: Capital.com UK accounts are denominated in GBP
        # The API sometimes incorrectly reports 'USD' as the currency label
        account_currency = os.getenv('CAPITAL_ACCOUNT_CURRENCY', 'GBP').upper()
            
        try:
            response = self._request('GET', '/accounts')
            if response.status_code == 200:
                data = response.json()
                # Capital.com returns a list of accounts. We'll sum them up or take the main one.
                # Structure: {'accounts': [{'accountId': ..., 'balance': {'balance': 1000, 'currency': 'USD'}}]}
                balances = {}
                if 'accounts' in data:
                    for acc in data['accounts']:
                        # Ignore API-reported currency, use our configured account currency
                        amount = float(acc.get('balance', {}).get('balance', 0.0))
                        balances[account_currency] = balances.get(account_currency, 0.0) + amount
                return balances
            else:
                logger.error(f"Failed to get Capital.com balances: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching Capital.com balances: {e}")
            return {}
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get account information including available balance.
        Returns list of accounts with structure: [{'accountId': str, 'available': float, 'balance': float}]
        """
        if not self.enabled:
            return []
        
        try:
            response = self._request('GET', '/accounts')
            if response.status_code == 200:
                data = response.json()
                accounts = []
                for acc in data.get('accounts', []):
                    balance_data = acc.get('balance', {})
                    accounts.append({
                        'accountId': acc.get('accountId', ''),
                        'balance': float(balance_data.get('balance', 0.0)),
                        'available': float(balance_data.get('available', balance_data.get('balance', 0.0))),
                        'currency': os.getenv('CAPITAL_ACCOUNT_CURRENCY', 'GBP').upper()
                    })
                return accounts
            else:
                logger.error(f"Failed to get Capital.com accounts: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Capital.com accounts: {e}")
            return []

    def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Get current price for a symbol."""
        if not self.enabled:
            return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        # 🔥 Skip crypto symbols - Capital.com doesn't have them
        CRYPTO_PATTERNS = ('USDT', 'USDC', 'BTC', 'ETH', 'XBT', 'SOL', 'ADA', 'XRP', 
                           'DOGE', 'SHIB', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI')
        if any(p in symbol.upper() for p in CRYPTO_PATTERNS):
            return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        try:
            market = self._resolve_market(symbol) or {}
            epic = market.get('epic') or symbol
            snapshot = self._get_market_snapshot(epic) or {}
            snap = snapshot.get('snapshot', {})

            bid = float(snap.get('bid') or market.get('bid') or market.get('snapshot', {}).get('bid') or 0)
            ask = float(snap.get('offer') or market.get('offer') or market.get('snapshot', {}).get('offer') or 0)
            price = (bid + ask) / 2 if bid and ask else (bid or ask or float(snap.get('midOpen', 0) or 0))

            change_pct = float(snap.get('percentageChange', 0) or 0)
            return {
                'price': price,
                'bid': bid,
                'ask': ask,
                'epic': epic,
                'change_pct': change_pct,
            }
        except Exception as e:
            logger.error(f"Error fetching Capital.com ticker for {symbol}: {e}")
            return {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

    def get_tickers_for_symbols(self, symbols: List[str], *, max_workers: int = 8) -> Dict[str, Dict[str, float]]:
        """Fetch tickers for many symbols concurrently (best-effort).

        Returns: {symbol: {price,bid,ask,epic,change_pct}}
        """
        if not self.enabled:
            return {}
        if not symbols:
            return {}

        # Deduplicate while preserving a stable order
        seen = set()
        unique_symbols: List[str] = []
        for s in symbols:
            if not s:
                continue
            su = str(s).strip().upper()
            if not su or su in seen:
                continue
            seen.add(su)
            unique_symbols.append(su)

        results: Dict[str, Dict[str, float]] = {}
        max_workers = max(1, int(max_workers))

        def _fetch(sym: str) -> Dict[str, float]:
            return self.get_ticker(sym)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_map = {ex.submit(_fetch, sym): sym for sym in unique_symbols}
            for fut in as_completed(future_map):
                sym = future_map[fut]
                try:
                    results[sym] = fut.result() or {'price': 0.0, 'bid': 0.0, 'ask': 0.0}
                except Exception:
                    results[sym] = {'price': 0.0, 'bid': 0.0, 'ask': 0.0}

        return results

    def get_24h_tickers(self) -> List[Dict[str, Any]]:
        """
        Get top markets or a watchlist. 
        Capital.com doesn't have a simple 'all tickers' endpoint that is lightweight.
        We'll fetch a top list or specific categories if possible.
        For now, let's fetch top crypto and tech stocks if we can, or just return empty if too complex.
        Actually, let's try to fetch 'crypto' category.
        """
        if not self.enabled:
            return []
            
        max_snapshots = int(os.getenv('CAPITAL_MAX_TICKER_SNAPSHOTS', '400'))
        tickers: List[Dict[str, Any]] = []
        markets = self.get_all_markets()

        try:
            for idx, m in enumerate(markets):
                epic = m.get('epic')
                if not epic:
                    continue

                bid = ask = price = change_pct = 0.0
                if idx < max_snapshots:
                    snap = self._get_market_snapshot(epic) or {}
                    snapshot = snap.get('snapshot', {})
                    bid = float(snapshot.get('bid', 0) or 0)
                    ask = float(snapshot.get('offer', 0) or 0)
                    price = (bid + ask) / 2 if bid and ask else float(snapshot.get('midOpen', 0) or 0)
                    change_pct = float(snapshot.get('percentageChange', 0) or 0)

                tickers.append({
                    # Keep 'symbol' as epic for backward-compat with existing code.
                    'symbol': epic,
                    'epic': epic,
                    # Where available, 'ticker' is the underlying instrument symbol (e.g., AAPL).
                    'ticker': m.get('symbol') or '',
                    'instrumentName': m.get('instrumentName'),
                    'price': price,
                    'bid': bid,
                    'ask': ask,
                    'priceChangePercent': change_pct,
                    'volume': 0.0,
                    'source': 'capital'
                })
        except Exception as e:
            logger.error(f"Error fetching Capital.com tickers: {e}")

        return tickers

    def get_stock_snapshot_watchlist(self, symbols: List[str], *, max_workers: int = 8) -> List[Dict[str, Any]]:
        """Convenience: returns a ticker-like list for a list of stock symbols."""
        tmap = self.get_tickers_for_symbols(symbols, max_workers=max_workers)
        out: List[Dict[str, Any]] = []
        for sym, t in tmap.items():
            out.append({
                'symbol': t.get('epic', sym),
                'epic': t.get('epic', sym),
                'ticker': sym,
                'instrumentName': '',
                'price': float(t.get('price', 0) or 0),
                'bid': float(t.get('bid', 0) or 0),
                'ask': float(t.get('ask', 0) or 0),
                'priceChangePercent': float(t.get('change_pct', 0) or 0),
                'volume': 0.0,
                'source': 'capital'
            })
        return out

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """Place a market order."""
        if not self.enabled:
            return {'error': 'Client disabled'}
        
        # 🔥 CRYPTO GUARD: Capital.com does NOT support direct crypto trading!
        # Only CFDs (forex, indices, commodities, stocks) are supported
        CRYPTO_PATTERNS = ('USDT', 'USDC', 'BTC', 'ETH', 'XBT', 'SOL', 'ADA', 'XRP', 
                           'DOGE', 'SHIB', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI',
                           'ATOM', 'LTC', 'BCH', 'ETC', 'XLM', 'ALGO', 'FIL', 'VET')
        symbol_upper = symbol.upper()
        if any(pattern in symbol_upper for pattern in CRYPTO_PATTERNS):
            logger.warning(f"Capital.com BLOCKED crypto order for {symbol} - use Binance/Kraken instead")
            return {'error': 'Crypto not supported on Capital.com', 'rejected': True, 'reason': 'CRYPTO_NOT_SUPPORTED'}
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Capital.com {side} {quantity} {symbol}")
            return {'id': 'dry_run_id', 'status': 'filled'}

        path = '/positions'
        direction = "BUY" if side.upper() == "BUY" else "SELL"

        market = self._resolve_market(symbol) or {}
        epic = market.get('epic') or symbol

        payload = {
            "epic": epic,
            "direction": direction,
            "size": quantity,
            "orderType": "MARKET",
            "guaranteedStop": False,
            "forceOpen": True,
            "currencyCode": os.getenv('CAPITAL_ACCOUNT_CURRENCY', 'GBP').upper()
        }
        
        try:
            response = self._request('POST', path, json_body=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Capital.com order failed: {response.text}")
                return {
                    'rejected': True,
                    'error': 'http_error',
                    'status_code': response.status_code,
                    'reason': response.text,
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                }
        except Exception as e:
            logger.error(f"Capital.com order error: {e}")
            return {
                'rejected': True,
                'error': 'exception',
                'reason': str(e),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
            }

    def confirm_order(self, deal_reference: str) -> Dict[str, Any]:
        """Fetch confirmation for a previously submitted deal reference."""
        if not self.enabled:
            return {'error': 'Client disabled'}

        if not deal_reference:
            return {'error': 'Missing deal reference'}

        try:
            response = self._request('GET', f'/confirms/{deal_reference}')
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Capital.com confirm failed: {response.text}")
                return {'error': response.text}
        except Exception as e:
            logger.error(f"Capital.com confirm error: {e}")
            return {'error': str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        if not self.enabled:
            return []
            
        try:
            response = self._request('GET', '/positions')
            if response.status_code == 200:
                data = response.json()
                return data.get('positions', [])
            return []
        except Exception as e:
            logger.error(f"Capital.com positions error: {e}")
            return []

    def get_order_history(self, from_date: str = None) -> List[Dict[str, Any]]:
        """Get order/deal history."""
        if not self.enabled:
            return []
            
        path = '/history/activity'
        params = {}
        if from_date:
            params['from'] = from_date
            
        try:
            response = self._request('GET', path, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('activities', [])
            return []
        except Exception as e:
            logger.error(f"Capital.com history error: {e}")
            return []

    def compute_trade_fees(self, position: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate fees for a Capital.com position/trade.
        
        Capital.com Fee Structure (CFD/Spread Betting):
        - Spread cost: Built into bid/ask (varies by instrument, typically 0.1-0.5%)
        - Overnight financing: ~2.5% annually (charged daily on leveraged positions)
        - No commission on most instruments
        
        Returns dict with:
        - spread_cost: Estimated spread cost in account currency
        - overnight_cost: Accumulated overnight financing
        - total_fees: Total fees
        - fee_pct: Approximate fee as percentage of notional
        """
        size = float(position.get('position', {}).get('size', 0) or 0)
        level = float(position.get('position', {}).get('level', 0) or 0)  # Entry price
        notional = size * level
        
        # Get current market to estimate spread
        epic = position.get('market', {}).get('epic', '')
        market = position.get('market', {})
        bid = float(market.get('bid', 0) or 0)
        offer = float(market.get('offer', 0) or 0)
        
        # Calculate spread percentage
        if bid > 0 and offer > 0:
            spread_pct = (offer - bid) / ((offer + bid) / 2)
        else:
            spread_pct = 0.001  # Default 0.1%
            
        # Spread cost (paid on entry)
        spread_cost = notional * spread_pct
        
        # Overnight financing (calculate based on creation date if available)
        overnight_cost = 0.0
        # Note: Would need to track days held for accurate overnight cost
        # For now, estimate based on typical overnight rates
        
        total_fees = spread_cost + overnight_cost
        fee_pct = (total_fees / notional) if notional > 0 else 0
        
        return {
            'spread_cost': spread_cost,
            'spread_pct': spread_pct,
            'overnight_cost': overnight_cost,
            'total_fees': total_fees,
            'fee_pct': fee_pct,
            'notional': notional,
            'epic': epic
        }

    def get_positions_with_fees(self) -> List[Dict[str, Any]]:
        """Get all positions with computed fee metrics."""
        positions = self.get_positions()
        for pos in positions:
            fees = self.compute_trade_fees(pos)
            pos['computed_fees'] = fees
        return positions

    def compute_order_fees_in_quote(self, position: Dict[str, Any], primary_quote: str = "USD") -> float:
        """
        Calculate total fees for a position/trade in the quote currency.
        This provides a consistent interface with Binance/Kraken clients.
        
        Returns: Total fee in quote currency
        """
        fees = self.compute_trade_fees(position)
        return fees['total_fees']

    def calculate_cost_basis(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate cost basis for a symbol from order history.
        
        Capital.com uses 'epic' for symbol names (e.g., 'BTCUSD', 'AAPL').
        
        Returns dict with:
        - symbol: The symbol/epic
        - total_quantity: Net quantity held
        - total_cost: Total cost of buys
        - avg_cost: Average cost per unit
        - trades: Number of trades
        """
        history = self.get_order_history()
        
        if not history:
            return {
                "symbol": symbol,
                "total_quantity": 0.0,
                "total_cost": 0.0,
                "avg_cost": 0.0,
                "trades": 0
            }
        
        total_qty = 0.0
        buy_qty = 0.0
        buy_cost = 0.0
        trade_count = 0
        
        for activity in history:
            # Capital.com activity structure varies by type
            epic = activity.get('epic', '') or activity.get('details', {}).get('epic', '')
            if epic.upper() != symbol.upper():
                continue
            
            activity_type = activity.get('type', '')
            
            # Look for deal confirmed activities
            if 'deal' in activity_type.lower() or 'position' in activity_type.lower():
                size = float(activity.get('details', {}).get('size', 0) or 0)
                level = float(activity.get('details', {}).get('level', 0) or 0)
                direction = activity.get('details', {}).get('direction', '')
                
                if size <= 0 or level <= 0:
                    continue
                
                trade_count += 1
                
                if direction.upper() == 'BUY':
                    total_qty += size
                    buy_qty += size
                    buy_cost += size * level
                elif direction.upper() == 'SELL':
                    total_qty -= size
        
        avg_cost = buy_cost / buy_qty if buy_qty > 0 else 0.0
        
        return {
            "symbol": symbol,
            "total_quantity": total_qty,
            "total_cost": buy_cost,
            "avg_cost": avg_cost,
            "trades": trade_count
        }
