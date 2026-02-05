#!/usr/bin/env python3
"""
👑💰🎮 QUEEN ASSET COMMAND CENTER 🎮💰👑

Full Autonomous Control of ALL Assets Across ALL Exchanges

Queen Sero takes command of:
- 🐙 Kraken (Crypto)
- 🟡 Binance (Crypto)
- 🦙 Alpaca (Stocks & Crypto)
- 💷 Capital.com (CFDs)
- 📊 All persisted state files

Gary Leckey | The Math Works | February 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
import time
import logging
import requests
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COINGECKO PRICE FETCHER (FREE, NO API KEY)
# ═══════════════════════════════════════════════════════════════════════════════

# Symbol to CoinGecko ID mapping for common assets
COINGECKO_IDS = {
    # Major coins
    'BTC': 'bitcoin', 'XBT': 'bitcoin', 'XXBT': 'bitcoin',
    'ETH': 'ethereum', 'XETH': 'ethereum',
    'USDT': 'tether', 'USDC': 'usd-coin',
    'BNB': 'binancecoin',
    'XRP': 'ripple', 'XXRP': 'ripple',
    'ADA': 'cardano',
    'SOL': 'solana',
    'DOGE': 'dogecoin', 'XXDG': 'dogecoin',
    'DOT': 'polkadot',
    'MATIC': 'matic-network', 'POL': 'matic-network',
    'SHIB': 'shiba-inu', 'SHIBUSD': 'shiba-inu',
    'LTC': 'litecoin', 'XLTC': 'litecoin',
    'TRX': 'tron', 'TRX.B': 'tron',  # TRX.B is Tron on Kraken
    'AVAX': 'avalanche-2',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'ATOM': 'cosmos',
    'XMR': 'monero', 'XXMR': 'monero',
    'ETC': 'ethereum-classic',
    'XLM': 'stellar', 'XXLM': 'stellar',
    'ALGO': 'algorand',
    'FIL': 'filecoin',
    'NEAR': 'near',
    'APT': 'aptos',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'INJ': 'injective-protocol',
    'IMX': 'immutable-x',
    'SAND': 'the-sandbox',
    'MANA': 'decentraland',
    'AXS': 'axie-infinity',
    'AAVE': 'aave',
    'MKR': 'maker',
    'SNX': 'havven',
    'CRV': 'curve-dao-token',
    'COMP': 'compound-governance-token',
    'LDO': 'lido-dao',
    'RPL': 'rocket-pool',
    'ENS': 'ethereum-name-service',
    'CRO': 'crypto-com-chain',
    'FTM': 'fantom',
    'ROSE': 'oasis-network',
    'ZEC': 'zcash',
    'DASH': 'dash',
    'EOS': 'eos',
    'XTZ': 'tezos',
    'THETA': 'theta-token',
    'KAVA': 'kava',
    'RUNE': 'thorchain',
    'ZRX': '0x',
    'BAT': 'basic-attention-token',
    'ENJ': 'enjincoin',
    'GRT': 'the-graph',
    'SUSHI': 'sushi',
    '1INCH': '1inch',
    'ANKR': 'ankr',
    'CHZ': 'chiliz',
    'GALA': 'gala',
    'FLOW': 'flow',
    'HBAR': 'hedera-hashgraph',
    'EGLD': 'elrond-erd-2',
    'NEO': 'neo',
    'WAVES': 'waves',
    'QTUM': 'qtum',
    'ICX': 'icon',
    'ZIL': 'zilliqa',
    'ONT': 'ontology',
    'VET': 'vechain',
    'OMG': 'omisego',
    'STORJ': 'storj',
    'REN': 'republic-protocol',
    'NMR': 'numeraire',
    'LPT': 'livepeer',
    'SSV': 'ssv-network',
    'EUL': 'euler',
    'BSX': 'basilisk',
    'PAXG': 'pax-gold',
    'PEPE': 'pepe',
    'WIF': 'dogwifcoin',
    'BONK': 'bonk',
    'FLOKI': 'floki',
    'MEME': 'memecoin',
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TOKENS FROM YOUR PORTFOLIO (THE 29 UNPRICED ONES)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Kraken tokens
    'GHIBLI': 'ghibli',  # Studio Ghibli meme
    'MXC': 'mxc',  # MXC Protocol
    'SAHARA': 'sahara-ai',  # Sahara AI
    'SKR': 'sakura-bloom',  # or sekuritance
    'FIGHT': 'fight-night',  # Fight Night
    'IN': 'inex-project',  # INEX Project  
    'FIS': 'stafi',  # StaFi Protocol
    'ICNT': 'icent',  # Icent
    'TUSD': 'true-usd',  # TrueUSD stablecoin
    'OPEN': 'open-platform',  # Open Platform
    'ZGBP': 'pound-sterling',  # GBP stablecoin (treat as 1.27 USD)
    'SCRT': 'secret',  # Secret Network
    'KTA': 'kasta',  # Kasta
    'BABY': 'baby-doge-coin',  # Baby Doge
    
    # Binance tokens  
    'BEAMX': 'beam-2',  # Beam gaming (BEAMX on Binance)
    'BEAM': 'beam-2',  # Beam gaming
    'PENGU': 'pudgy-penguins',  # Pudgy Penguins
    'F': 'forta',  # Forta Network (or could be other F token)
    'NOM': 'onomy-protocol',  # Onomy Protocol
    'TURTLE': 'turtlecoin',  # TurtleCoin
    'BREV': 'brevity',  # Brevity Protocol
    'STO': 'stobox-token',  # Stobox
    'SHELL': 'shell-protocol',  # Shell Protocol
    'AVNT': 'avantage',  # Avantage
    'RESOLV': 'resolv',  # Resolv
    'SOMI': 'sominium',  # Sominium
    'KAIA': 'kaia',  # Kaia (formerly Klaytn)
    'ZRO': 'layerzero',  # LayerZero
    'ENSO': 'enso-finance',  # Enso Finance
    
    # More popular tokens
    'SUI': 'sui',
    'SEI': 'sei-network',
    'TIA': 'celestia',
    'JUP': 'jupiter-exchange-solana',
    'PYTH': 'pyth-network',
    'JTO': 'jito-governance-token',
    'STRK': 'starknet',
    'DYM': 'dymension',
    'MANTA': 'manta-network',
    'ALT': 'altlayer',
    'PIXEL': 'pixels',
    'PORTAL': 'portal-2',
    'AEVO': 'aevo-exchange',
    'W': 'wormhole',
    'ENA': 'ethena',
    'ONDO': 'ondo-finance',
    'NOT': 'notcoin',
    'IO': 'io-net',
    'ZK': 'zksync',
    'LISTA': 'lista-dao',
    'BLAST': 'blast',
    'BOME': 'book-of-meme',
    'MEW': 'cat-in-a-dogs-world',
    'POPCAT': 'popcat',
    'DOGS': 'dogs-2',
    'NEIRO': 'first-neiro-on-ethereum',
    'TURBO': 'turbo',
    'MOTHER': 'mother-iggy',
    'BRETT': 'brett',
    'MOG': 'mog-coin',
    'SPX': 'spx6900',
    'GOAT': 'goatseus-maximus',
    'PNUT': 'peanut-the-squirrel',
    'ACT': 'act-i-the-ai-prophecy',
    'AI16Z': 'ai16z',
    'VIRTUAL': 'virtual-protocol',
    'GRIFFAIN': 'griffain',
    'FARTCOIN': 'fartcoin',
    'AIXBT': 'aixbt',
    'ARC': 'arc-agents',
    'SWARMS': 'swarms',
    'ZEREBRO': 'zerebro',
    'ELIZA': 'eliza',
    'AVAAI': 'avabots',
    'GAME': 'game-by-virtuals',
    'CGPT': 'chaingpt',
    'TAO': 'bittensor',
    'RENDER': 'render-token',
    'FET': 'fetch-ai',
    'AGIX': 'singularitynet',
    'OCEAN': 'ocean-protocol',
    'RNDR': 'render-token',
    'WLD': 'worldcoin-wld',
    'ARKM': 'arkham',
    'AIOZ': 'aioz-network',
}

class CoinGeckoPriceFetcher:
    """Fetch REAL prices from CoinGecko (FREE API)."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
        self.last_fetch = 0
        self.base_url = "https://api.coingecko.com/api/v3"
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get REAL prices for a list of symbols.
        Returns {symbol: price_usd}
        """
        # Handle fiat/stablecoins directly
        FIAT_PRICES = {
            'ZGBP': 1.27,  # GBP to USD
            'GBP': 1.27,
            'EUR': 1.08,
            'ZEUR': 1.08,
            'TUSD': 1.0,  # TrueUSD stablecoin
            'USDT': 1.0,
            'USDC': 1.0,
            'BUSD': 1.0,
            'DAI': 1.0,
            'FDUSD': 1.0,
        }
        
        result = {}
        symbols_to_fetch = []
        
        for symbol in symbols:
            clean_symbol = symbol.upper().replace('USD', '').replace('USDT', '').replace('USDC', '')
            if symbol.upper() in FIAT_PRICES:
                result[symbol] = FIAT_PRICES[symbol.upper()]
            elif clean_symbol in FIAT_PRICES:
                result[symbol] = FIAT_PRICES[clean_symbol]
            else:
                symbols_to_fetch.append(symbol)
        
        if not symbols_to_fetch:
            return result
        
        # Map symbols to CoinGecko IDs
        ids_to_fetch = []
        symbol_to_id = {}
        unmapped_symbols = []
        
        for symbol in symbols_to_fetch:
            clean_symbol = symbol.upper().replace('USD', '').replace('USDT', '').replace('USDC', '')
            # Try both original and cleaned versions
            cg_id = COINGECKO_IDS.get(symbol.upper()) or COINGECKO_IDS.get(clean_symbol)
            if cg_id:
                ids_to_fetch.append(cg_id)
                symbol_to_id[cg_id] = symbol
            else:
                unmapped_symbols.append(symbol)
        
        # Check cache for CoinGecko results
        now = time.time()
        if now - self.last_fetch < self.cache_ttl and self.cache:
            for cg_id, sym in symbol_to_id.items():
                if cg_id in self.cache:
                    result[sym] = self.cache[cg_id]
                    ids_to_fetch = [i for i in ids_to_fetch if i != cg_id]
        
        # Fetch remaining from CoinGecko
        if ids_to_fetch:
            try:
                ids_str = ','.join(set(ids_to_fetch))
                url = f"{self.base_url}/simple/price?ids={ids_str}&vs_currencies=usd"
                resp = requests.get(url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    self.last_fetch = now
                    
                    for cg_id, sym in symbol_to_id.items():
                        if cg_id in data and 'usd' in data[cg_id]:
                            price = data[cg_id]['usd']
                            self.cache[cg_id] = price
                            result[sym] = price
            except Exception as e:
                logger.debug(f"CoinGecko fetch error: {e}")
        
        # For unmapped symbols, try Binance public API (no auth needed)
        for symbol in unmapped_symbols:
            if symbol not in result:
                try:
                    # Try USDT pair
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'price' in data:
                            result[symbol] = float(data['price'])
                            continue
                    # Try USDC pair
                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDC"
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'price' in data:
                            result[symbol] = float(data['price'])
                except Exception:
                    pass
        
        return result
    
    def get_price(self, symbol: str) -> float:
        """Get price for single symbol."""
        prices = self.get_prices([symbol])
        return prices.get(symbol, 0.0)


# Global price fetcher instance
_price_fetcher: Optional['CoinGeckoPriceFetcher'] = None

def get_price_fetcher() -> CoinGeckoPriceFetcher:
    """Get singleton price fetcher."""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = CoinGeckoPriceFetcher()
    return _price_fetcher

# ═══════════════════════════════════════════════════════════════════════════════
# ASSET DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AssetPosition:
    """Single asset position across any exchange."""
    symbol: str
    exchange: str
    quantity: float
    entry_price: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    realized_pnl: float = 0.0
    cost_basis: float = 0.0
    last_updated: float = 0.0
    source: str = "unknown"  # api, state_file, cost_basis
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExchangeSummary:
    """Summary for one exchange."""
    name: str
    connected: bool = False
    total_value: float = 0.0
    total_pnl: float = 0.0
    cash_balance: float = 0.0
    positions_count: int = 0
    positions: List[AssetPosition] = field(default_factory=list)
    error: str = ""
    last_updated: float = 0.0


@dataclass 
class QueenAssetInventory:
    """Complete inventory across all exchanges."""
    timestamp: float = 0.0
    total_portfolio_value: float = 0.0
    total_cash: float = 0.0
    total_invested: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0
    total_positions: int = 0
    exchanges: Dict[str, ExchangeSummary] = field(default_factory=dict)
    all_positions: List[AssetPosition] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['exchanges'] = {k: asdict(v) for k, v in self.exchanges.items()}
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# QUEEN ASSET COMMAND CENTER
# ═══════════════════════════════════════════════════════════════════════════════

class QueenAssetCommandCenter:
    """
    👑💰🎮 QUEEN'S FULL AUTONOMOUS CONTROL OVER ALL ASSETS 🎮💰👑
    
    She sees EVERYTHING. She controls EVERYTHING.
    Real data only - NO SIMULATIONS!
    """
    
    def __init__(self):
        """Initialize the Asset Command Center."""
        self.kraken = None
        self.binance = None
        self.alpaca = None
        self.capital = None
        
        self.last_inventory: Optional[QueenAssetInventory] = None
        self.inventory_cache_ttl = 30.0  # Refresh every 30 seconds
        
        # State file paths
        self.state_files = {
            'cost_basis': Path('cost_basis_history.json'),
            'kraken_state': Path('aureon_kraken_state.json'),
            'alpaca_truth': Path('alpaca_truth_tracker_state.json'),
            'active_position': Path('active_position.json'),
            'elephant_memory': Path('elephant_memory.json'),
            'unified_pnl': Path('unified_pnl_state.json'),
        }
        
        self._connect_exchanges()
        
        logger.info("👑💰🎮 QUEEN ASSET COMMAND CENTER INITIALIZED!")
    
    def _connect_exchanges(self):
        """Connect to all available exchanges."""
        # Kraken
        try:
            from kraken_client import get_kraken_client
            self.kraken = get_kraken_client()
            logger.info("   🐙 Kraken: CONNECTED")
        except Exception as e:
            logger.debug(f"   🐙 Kraken: {e}")
        
        # Binance
        try:
            from binance_client import get_binance_client
            self.binance = get_binance_client()
            logger.info("   🟡 Binance: CONNECTED")
        except Exception as e:
            logger.debug(f"   🟡 Binance: {e}")
        
        # Alpaca
        try:
            from alpaca_client import AlpacaClient
            self.alpaca = AlpacaClient()
            logger.info("   🦙 Alpaca: CONNECTED")
        except Exception as e:
            logger.debug(f"   🦙 Alpaca: {e}")
        
        # Capital.com
        try:
            from capital_client import CapitalClient
            self.capital = CapitalClient()
            logger.info("   💷 Capital.com: CONNECTED")
        except Exception as e:
            logger.debug(f"   💷 Capital.com: {e}")
    
    def _load_json_file(self, path: Path, default: Any = None) -> Any:
        """Safely load a JSON file."""
        try:
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load {path}: {e}")
        return default if default is not None else {}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXCHANGE SCANNERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_kraken(self) -> ExchangeSummary:
        """🐙 Scan Kraken for all assets with REAL prices from Kraken API."""
        summary = ExchangeSummary(name="kraken", last_updated=time.time())
        
        if not self.kraken:
            summary.error = "Not connected"
            return summary
        
        try:
            # Get balance from API
            balances = self.kraken.get_balance()
            if balances:
                summary.connected = True
                
                for asset, qty in balances.items():
                    qty = float(qty)
                    if qty > 0.000001:
                        if asset in ['USD', 'ZUSD', 'USDT', 'USDC']:
                            summary.cash_balance += qty
                        elif asset in ['ZGBP', 'GBP']:
                            summary.cash_balance += qty * 1.27  # GBP to USD
                        elif asset in ['ZEUR', 'EUR']:
                            summary.cash_balance += qty * 1.08  # EUR to USD
                        else:
                            # Get price from Kraken public API
                            price = 0.0
                            
                            # Kraken uses weird naming - try multiple formats
                            kraken_symbols = [
                                f"{asset}USD", f"{asset}USDT", f"X{asset}ZUSD",
                                f"X{asset}USD", f"{asset.replace('.B', '')}USD"
                            ]
                            
                            for ksym in kraken_symbols:
                                try:
                                    url = f"https://api.kraken.com/0/public/Ticker?pair={ksym}"
                                    resp = requests.get(url, timeout=3)
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        if not data.get('error') and data.get('result'):
                                            # Get first result
                                            result = list(data['result'].values())[0]
                                            price = float(result.get('c', [0])[0])  # 'c' is last trade price
                                            if price > 0:
                                                break
                                except Exception:
                                    pass
                            
                            # Fallback to CoinGecko if Kraken didn't have it
                            if price == 0:
                                price_fetcher = get_price_fetcher()
                                prices = price_fetcher.get_prices([asset])
                                price = prices.get(asset, 0.0)
                            
                            market_value = qty * price
                            position = AssetPosition(
                                symbol=asset,
                                exchange="kraken",
                                quantity=qty,
                                current_price=price,
                                market_value=market_value,
                                last_updated=time.time(),
                                source="kraken_api" if price > 0 else "no_price"
                            )
                            summary.positions.append(position)
                            summary.total_value += market_value
                
                summary.positions_count = len(summary.positions)
                summary.total_value += summary.cash_balance
            else:
                # Fallback to state file
                state = self._load_json_file(self.state_files['kraken_state'])
                positions = state.get('positions', {})
                price_fetcher = get_price_fetcher()
                symbols = list(positions.keys())
                prices = price_fetcher.get_prices(symbols) if symbols else {}
                
                for symbol, pos in positions.items():
                    qty = pos.get('quantity', 0)
                    if qty > 0.000001:
                        price = prices.get(symbol, 0.0)
                        market_value = qty * price
                        position = AssetPosition(
                            symbol=symbol,
                            exchange="kraken",
                            quantity=qty,
                            entry_price=pos.get('entry_price', 0),
                            current_price=price,
                            market_value=market_value,
                            last_updated=time.time(),
                            source="state_file"
                        )
                        summary.positions.append(position)
                        summary.total_value += market_value
                        summary.positions_count += 1
                summary.connected = len(summary.positions) > 0
                summary.error = "API returned empty, using state file"
                
        except Exception as e:
            summary.error = str(e)
            logger.warning(f"🐙 Kraken scan error: {e}")
        
        return summary
    
    def scan_binance(self) -> ExchangeSummary:
        """🟡 Scan Binance for all assets with REAL prices from Binance API."""
        summary = ExchangeSummary(name="binance", last_updated=time.time())
        
        if not self.binance:
            summary.error = "Not connected"
            return summary
        
        try:
            acct = self.binance.account()
            if acct:
                summary.connected = True
                
                # Process all assets
                for b in acct.get('balances', []):
                    asset = b.get('asset')
                    free = float(b.get('free', 0))
                    locked = float(b.get('locked', 0))
                    total = free + locked
                    
                    if total > 0.000001:
                        if asset in ['USDT', 'USDC', 'BUSD', 'USD', 'FDUSD', 'EUR']:
                            # Handle stablecoins/fiat
                            if asset == 'EUR':
                                summary.cash_balance += total * 1.08  # EUR to USD
                            else:
                                summary.cash_balance += total
                        else:
                            # Get price directly from Binance public API
                            price = 0.0
                            
                            # Try USDT pair first (most common)
                            for quote in ['USDT', 'USDC', 'EUR', 'BTC']:
                                try:
                                    url = f"https://api.binance.com/api/v3/ticker/price?symbol={asset}{quote}"
                                    resp = requests.get(url, timeout=3)
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        p = float(data.get('price', 0))
                                        if p > 0:
                                            if quote == 'EUR':
                                                price = p * 1.08  # EUR to USD
                                            elif quote == 'BTC':
                                                # Get BTC price
                                                btc_resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=3)
                                                if btc_resp.status_code == 200:
                                                    btc_price = float(btc_resp.json().get('price', 97000))
                                                    price = p * btc_price
                                            else:
                                                price = p
                                            break
                                except Exception:
                                    pass
                            
                            market_value = total * price
                            position = AssetPosition(
                                symbol=asset,
                                exchange="binance",
                                quantity=total,
                                current_price=price,
                                market_value=market_value,
                                last_updated=time.time(),
                                source="binance_api" if price > 0 else "no_price"
                            )
                            summary.positions.append(position)
                            summary.total_value += market_value
                
                summary.positions_count = len(summary.positions)
                summary.total_value += summary.cash_balance
                
        except Exception as e:
            summary.error = str(e)
            logger.warning(f"🟡 Binance scan error: {e}")
        
        return summary
    
    def scan_alpaca(self) -> ExchangeSummary:
        """🦙 Scan Alpaca for all assets."""
        summary = ExchangeSummary(name="alpaca", last_updated=time.time())
        
        if not self.alpaca:
            summary.error = "Not connected"
            return summary
        
        try:
            # Get account
            acct = self.alpaca.get_account()
            if acct:
                summary.connected = True
                summary.cash_balance = float(acct.get('cash', 0))
                
                # Get positions
                positions = self.alpaca.get_positions()
                for p in (positions or []):
                    qty = float(p.get('qty', 0))
                    market_value = float(p.get('market_value', 0))
                    avg_entry = float(p.get('avg_entry_price', 0))
                    current_price = float(p.get('current_price', 0))
                    unrealized_pl = float(p.get('unrealized_pl', 0))
                    unrealized_plpc = float(p.get('unrealized_plpc', 0)) * 100
                    
                    position = AssetPosition(
                        symbol=p.get('symbol'),
                        exchange="alpaca",
                        quantity=qty,
                        entry_price=avg_entry,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pl,
                        unrealized_pnl_pct=unrealized_plpc,
                        cost_basis=avg_entry * qty,
                        last_updated=time.time(),
                        source="api"
                    )
                    summary.positions.append(position)
                    summary.total_value += market_value
                    summary.total_pnl += unrealized_pl
                
                summary.positions_count = len(summary.positions)
                summary.total_value += summary.cash_balance
                
        except Exception as e:
            summary.error = str(e)
            logger.warning(f"🦙 Alpaca scan error: {e}")
        
        return summary
    
    def scan_capital(self) -> ExchangeSummary:
        """💷 Scan Capital.com for all assets."""
        summary = ExchangeSummary(name="capital", last_updated=time.time())
        
        if not self.capital:
            summary.error = "Not connected"
            return summary
        
        try:
            # Get account balance
            bal = self.capital.get_account_balance()
            if bal:
                summary.connected = True
                summary.cash_balance = float(bal.get('available', 0) or bal.get('balance', 0))
                summary.total_value = summary.cash_balance
                
            # Get positions
            try:
                positions = self.capital.get_positions()
                for p in (positions or []):
                    symbol = p.get('market', {}).get('epic') or p.get('epic')
                    qty = float(p.get('size', 0))
                    direction = p.get('direction', 'BUY')
                    if direction == 'SELL':
                        qty = -qty
                    
                    unrealized_pnl = float(p.get('profit', 0))
                    
                    position = AssetPosition(
                        symbol=symbol,
                        exchange="capital",
                        quantity=qty,
                        unrealized_pnl=unrealized_pnl,
                        last_updated=time.time(),
                        source="api"
                    )
                    summary.positions.append(position)
                    summary.total_pnl += unrealized_pnl
                
                summary.positions_count = len(summary.positions)
            except Exception as pe:
                logger.debug(f"Capital positions error: {pe}")
                
        except Exception as e:
            summary.error = str(e)
            logger.warning(f"💷 Capital.com scan error: {e}")
        
        return summary
    
    def scan_cost_basis(self) -> Dict[str, AssetPosition]:
        """📊 Scan cost basis history for tracked positions."""
        positions = {}
        
        data = self._load_json_file(self.state_files['cost_basis'])
        for symbol, pos in data.get('positions', {}).items():
            positions[f"{pos.get('exchange', 'unknown')}:{symbol}"] = AssetPosition(
                symbol=symbol,
                exchange=pos.get('exchange', 'unknown'),
                quantity=pos.get('quantity', 0),
                entry_price=pos.get('entry_price', 0),
                cost_basis=pos.get('total_cost', 0),
                realized_pnl=pos.get('realized_pnl', 0),
                last_updated=pos.get('last_trade_time', 0),
                source="cost_basis"
            )
        
        return positions
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FULL INVENTORY SCAN
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_all_assets(self, force_refresh: bool = False) -> QueenAssetInventory:
        """
        👑💰 SCAN ALL ASSETS ACROSS ALL EXCHANGES
        
        Returns complete inventory of everything Queen Sero controls.
        """
        # Check cache
        if not force_refresh and self.last_inventory:
            age = time.time() - self.last_inventory.timestamp
            if age < self.inventory_cache_ttl:
                return self.last_inventory
        
        inventory = QueenAssetInventory(timestamp=time.time())
        
        # Scan all exchanges
        kraken = self.scan_kraken()
        binance = self.scan_binance()
        alpaca = self.scan_alpaca()
        capital = self.scan_capital()
        
        inventory.exchanges = {
            'kraken': kraken,
            'binance': binance,
            'alpaca': alpaca,
            'capital': capital
        }
        
        # Aggregate totals
        for ex in [kraken, binance, alpaca, capital]:
            inventory.total_portfolio_value += ex.total_value
            inventory.total_cash += ex.cash_balance
            inventory.total_unrealized_pnl += ex.total_pnl
            inventory.total_positions += ex.positions_count
            inventory.all_positions.extend(ex.positions)
        
        inventory.total_invested = inventory.total_portfolio_value - inventory.total_cash
        
        # Add cost basis data for positions that don't have entry prices
        cost_basis_positions = self.scan_cost_basis()
        for pos in inventory.all_positions:
            key = f"{pos.exchange}:{pos.symbol}"
            if key in cost_basis_positions:
                cb = cost_basis_positions[key]
                if pos.entry_price == 0:
                    pos.entry_price = cb.entry_price
                if pos.cost_basis == 0:
                    pos.cost_basis = cb.cost_basis
                pos.realized_pnl = cb.realized_pnl
        
        self.last_inventory = inventory
        return inventory
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY & REPORTING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def display_inventory(self, inventory: QueenAssetInventory = None) -> str:
        """Generate display string of full inventory."""
        if inventory is None:
            inventory = self.scan_all_assets()
        
        # Count priced vs unpriced
        priced_count = sum(1 for p in inventory.all_positions if p.current_price > 0)
        unpriced_count = inventory.total_positions - priced_count
        priced_value = sum(p.market_value for p in inventory.all_positions if p.current_price > 0)
        
        lines = [
            "=" * 80,
            "👑💰🎮 QUEEN ASSET COMMAND CENTER - FULL INVENTORY 🎮💰👑",
            "=" * 80,
            "",
            f"📊 TOTAL PORTFOLIO VALUE: ${inventory.total_portfolio_value:,.2f}",
            f"💵 TOTAL CASH: ${inventory.total_cash:,.2f}",
            f"📈 TOTAL INVESTED: ${inventory.total_invested:,.2f}",
            f"💰 UNREALIZED P&L: ${inventory.total_unrealized_pnl:+,.2f}",
            f"🔢 TOTAL POSITIONS: {inventory.total_positions}",
            "",
            f"✅ PRICED POSITIONS: {priced_count} (${priced_value:,.2f})",
            f"❓ UNPRICED (DUST/OBSCURE): {unpriced_count}",
            "",
        ]
        
        # Per-exchange breakdown
        for name, ex in inventory.exchanges.items():
            status = "✅" if ex.connected else "❌"
            priced_ex = sum(1 for p in ex.positions if p.current_price > 0)
            priced_ex_value = sum(p.market_value for p in ex.positions if p.current_price > 0)
            
            lines.append(f"{status} {name.upper()}: ${ex.total_value:,.2f} ({ex.positions_count} positions, {priced_ex} priced)")
            if ex.cash_balance > 0:
                lines.append(f"   💵 Cash: ${ex.cash_balance:,.4f}")
            if ex.error:
                lines.append(f"   ⚠️ {ex.error}")
            if ex.positions:
                # Sort by value descending, show priced first
                sorted_positions = sorted(ex.positions, key=lambda p: -p.market_value if p.current_price > 0 else -p.quantity)
                for p in sorted_positions[:8]:  # Show top 8
                    if p.current_price > 0:
                        pnl_str = f" | P&L: ${p.unrealized_pnl:+.2f}" if p.unrealized_pnl else ""
                        lines.append(f"   💎 {p.symbol}: {p.quantity:,.6f} @ ${p.current_price:,.6f} = ${p.market_value:,.2f}{pnl_str}")
                    else:
                        lines.append(f"   🔸 {p.symbol}: {p.quantity:,.6f} (no price - dust/obscure)")
                if len(ex.positions) > 8:
                    remaining = len(ex.positions) - 8
                    remaining_value = sum(p.market_value for p in sorted_positions[8:])
                    lines.append(f"   ... and {remaining} more (${remaining_value:,.2f})")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def get_summary(self) -> Dict:
        """Get quick summary for API/display."""
        inventory = self.scan_all_assets()
        return {
            'timestamp': inventory.timestamp,
            'total_value': inventory.total_portfolio_value,
            'total_cash': inventory.total_cash,
            'total_invested': inventory.total_invested,
            'unrealized_pnl': inventory.total_unrealized_pnl,
            'positions_count': inventory.total_positions,
            'exchanges': {
                name: {
                    'connected': ex.connected,
                    'value': ex.total_value,
                    'positions': ex.positions_count,
                    'cash': ex.cash_balance,
                    'error': ex.error
                }
                for name, ex in inventory.exchanges.items()
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_command_center: Optional[QueenAssetCommandCenter] = None

def get_asset_command_center() -> QueenAssetCommandCenter:
    """Get or create the global Asset Command Center."""
    global _command_center
    if _command_center is None:
        _command_center = QueenAssetCommandCenter()
    return _command_center


# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN'S CONTINUOUS ASSET MONITOR (FREE API - NO RATE LIMITS)
# ═══════════════════════════════════════════════════════════════════════════════

class QueenAssetMonitor:
    """
    👑📊 CONTINUOUS ASSET MONITORING WITH FREE APIS
    
    Strategy:
    1. INITIAL: Get positions/quantities from TRADING APIs (authenticated)
    2. COST BASIS: Load entry prices from our trade history
    3. MONITOR: Use FREE public APIs for continuous price updates
    
    This avoids rate limits on trading APIs while giving us constant monitoring!
    """
    
    def __init__(self):
        """Initialize the monitor."""
        self.command_center = get_asset_command_center()
        
        # Cached positions (from trading APIs - updated rarely)
        self.cached_positions: Dict[str, Dict] = {}  # {exchange:symbol -> {qty, entry_price}}
        self.positions_last_updated: float = 0
        self.positions_cache_ttl: float = 300  # Update positions every 5 minutes
        
        # Cost basis data
        self.cost_basis: Dict[str, float] = {}  # {exchange:symbol -> entry_price}
        
        # Live prices (from FREE APIs - updated constantly)
        self.live_prices: Dict[str, float] = {}  # {symbol -> price}
        self.prices_last_updated: float = 0
        
        # State file for persistence
        self.state_file = Path('queen_asset_monitor_state.json')
        
        self._load_state()
        logger.info("👑📊 Queen Asset Monitor INITIALIZED")
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.cached_positions = data.get('positions', {})
                    self.cost_basis = data.get('cost_basis', {})
                    self.positions_last_updated = data.get('positions_updated', 0)
                    logger.info(f"   📂 Loaded {len(self.cached_positions)} cached positions")
        except Exception as e:
            logger.debug(f"Failed to load monitor state: {e}")
    
    def _save_state(self):
        """Persist state to disk."""
        try:
            data = {
                'positions': self.cached_positions,
                'cost_basis': self.cost_basis,
                'positions_updated': self.positions_last_updated,
                'saved_at': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save monitor state: {e}")
    
    def refresh_positions_from_apis(self, force: bool = False) -> Dict[str, Dict]:
        """
        📡 STEP 1: Get positions from TRADING APIs (authenticated)
        
        Only called occasionally to avoid rate limits.
        Returns {exchange:symbol -> {quantity, entry_price, exchange}}
        """
        now = time.time()
        if not force and (now - self.positions_last_updated) < self.positions_cache_ttl:
            return self.cached_positions
        
        logger.info("📡 Refreshing positions from trading APIs...")
        positions = {}
        
        # Get from each exchange
        inventory = self.command_center.scan_all_assets(force_refresh=True)
        
        for ex_name, ex_summary in inventory.exchanges.items():
            for pos in ex_summary.positions:
                key = f"{ex_name}:{pos.symbol}"
                positions[key] = {
                    'symbol': pos.symbol,
                    'exchange': ex_name,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price or 0,
                    'cost_basis': pos.cost_basis or 0,
                }
        
        # Also load cost basis from history
        self._load_cost_basis()
        
        # Merge cost basis into positions
        for key, pos in positions.items():
            if pos['entry_price'] == 0 and key in self.cost_basis:
                pos['entry_price'] = self.cost_basis[key]
        
        self.cached_positions = positions
        self.positions_last_updated = now
        self._save_state()
        
        logger.info(f"   ✅ Loaded {len(positions)} positions from APIs")
        return positions
    
    def _load_cost_basis(self):
        """📊 STEP 2: Load cost basis from trade history."""
        try:
            cost_basis_file = Path('cost_basis_history.json')
            if cost_basis_file.exists():
                with open(cost_basis_file) as f:
                    data = json.load(f)
                    for symbol, pos in data.get('positions', {}).items():
                        exchange = pos.get('exchange', 'unknown')
                        key = f"{exchange}:{symbol}"
                        self.cost_basis[key] = pos.get('entry_price', 0)
                logger.info(f"   📊 Loaded cost basis for {len(self.cost_basis)} positions")
        except Exception as e:
            logger.debug(f"Failed to load cost basis: {e}")
    
    def get_live_prices_free_api(self, symbols: List[str] = None) -> Dict[str, float]:
        """
        📊 STEP 3: Get live prices from FREE public APIs
        
        Uses:
        - Binance Public API (no auth, no rate limit issues)
        - CoinGecko (free tier)
        - Kraken Public API
        
        This can be called frequently without hitting rate limits!
        """
        if symbols is None:
            symbols = [p['symbol'] for p in self.cached_positions.values()]
        
        if not symbols:
            return {}
        
        prices = {}
        unique_symbols = list(set(symbols))
        
        # Method 1: Binance public API (fastest, most reliable)
        for symbol in unique_symbols:
            if symbol in prices:
                continue
            try:
                # Try USDT pair
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'price' in data:
                        prices[symbol] = float(data['price'])
                        continue
                
                # Try USDC pair
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDC"
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    if 'price' in data:
                        prices[symbol] = float(data['price'])
            except Exception:
                pass
        
        # Method 2: Kraken public API for remaining
        remaining = [s for s in unique_symbols if s not in prices]
        for symbol in remaining:
            try:
                # Kraken naming conventions
                ksym = f"{symbol}USD"
                url = f"https://api.kraken.com/0/public/Ticker?pair={ksym}"
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data.get('error') and data.get('result'):
                        result = list(data['result'].values())[0]
                        prices[symbol] = float(result.get('c', [0])[0])
            except Exception:
                pass
        
        # Method 3: CoinGecko for any still missing
        remaining = [s for s in unique_symbols if s not in prices]
        if remaining:
            price_fetcher = get_price_fetcher()
            cg_prices = price_fetcher.get_prices(remaining)
            prices.update(cg_prices)
        
        self.live_prices = prices
        self.prices_last_updated = time.time()
        return prices
    
    def get_full_portfolio_status(self, refresh_positions: bool = False) -> Dict:
        """
        👑 GET COMPLETE PORTFOLIO STATUS
        
        Combines:
        - Positions from trading APIs (cached)
        - Cost basis from trade history
        - Live prices from FREE APIs
        
        Returns full portfolio with P&L calculations!
        """
        # Step 1: Get positions (from cache or refresh)
        if refresh_positions or not self.cached_positions:
            self.refresh_positions_from_apis(force=refresh_positions)
        
        # Step 2: Get live prices (always fresh from FREE APIs)
        symbols = [p['symbol'] for p in self.cached_positions.values()]
        prices = self.get_live_prices_free_api(symbols)
        
        # Step 3: Calculate portfolio
        portfolio = {
            'timestamp': time.time(),
            'positions': [],
            'by_exchange': {},
            'totals': {
                'value': 0,
                'cost_basis': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_pct': 0,
            }
        }
        
        for key, pos in self.cached_positions.items():
            symbol = pos['symbol']
            exchange = pos['exchange']
            qty = pos['quantity']
            entry_price = pos['entry_price']
            
            # Get live price
            current_price = prices.get(symbol, 0)
            
            # Calculate values
            market_value = qty * current_price
            cost = qty * entry_price if entry_price > 0 else 0
            pnl = market_value - cost if cost > 0 else 0
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0
            
            position_data = {
                'symbol': symbol,
                'exchange': exchange,
                'quantity': qty,
                'entry_price': entry_price,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost,
                'unrealized_pnl': pnl,
                'unrealized_pnl_pct': pnl_pct,
            }
            
            portfolio['positions'].append(position_data)
            
            # Aggregate by exchange
            if exchange not in portfolio['by_exchange']:
                portfolio['by_exchange'][exchange] = {
                    'value': 0, 'cost': 0, 'pnl': 0, 'positions': 0
                }
            portfolio['by_exchange'][exchange]['value'] += market_value
            portfolio['by_exchange'][exchange]['cost'] += cost
            portfolio['by_exchange'][exchange]['pnl'] += pnl
            portfolio['by_exchange'][exchange]['positions'] += 1
            
            # Totals
            portfolio['totals']['value'] += market_value
            portfolio['totals']['cost_basis'] += cost
            portfolio['totals']['unrealized_pnl'] += pnl
        
        # Calculate total P&L percentage
        if portfolio['totals']['cost_basis'] > 0:
            portfolio['totals']['unrealized_pnl_pct'] = (
                portfolio['totals']['unrealized_pnl'] / portfolio['totals']['cost_basis'] * 100
            )
        
        return portfolio
    
    def display_portfolio(self, refresh_positions: bool = False) -> str:
        """Display the portfolio in a nice format."""
        portfolio = self.get_full_portfolio_status(refresh_positions)
        
        lines = [
            "=" * 80,
            "👑📊 QUEEN'S LIVE PORTFOLIO MONITOR (FREE API) 📊👑",
            "=" * 80,
            "",
            f"📊 TOTAL VALUE: ${portfolio['totals']['value']:,.2f}",
            f"💰 COST BASIS: ${portfolio['totals']['cost_basis']:,.2f}",
            f"📈 UNREALIZED P&L: ${portfolio['totals']['unrealized_pnl']:+,.2f} ({portfolio['totals']['unrealized_pnl_pct']:+.2f}%)",
            "",
        ]
        
        # By exchange
        for ex, data in portfolio['by_exchange'].items():
            pnl_pct = (data['pnl'] / data['cost'] * 100) if data['cost'] > 0 else 0
            lines.append(f"🏦 {ex.upper()}: ${data['value']:,.2f} | P&L: ${data['pnl']:+,.2f} ({pnl_pct:+.2f}%) | {data['positions']} positions")
        
        lines.append("")
        lines.append("📋 TOP POSITIONS:")
        
        # Sort by value, show top 10
        sorted_pos = sorted(portfolio['positions'], key=lambda p: -p['market_value'])
        for p in sorted_pos[:10]:
            if p['market_value'] > 0.01:
                pnl_str = f" | P&L: ${p['unrealized_pnl']:+.2f}" if p['cost_basis'] > 0 else ""
                lines.append(f"   💎 {p['symbol']:12} | {p['quantity']:>15,.4f} @ ${p['current_price']:>10.6f} = ${p['market_value']:>10.2f}{pnl_str}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"⏰ Prices updated: {datetime.fromtimestamp(portfolio['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("📡 Using FREE public APIs - no rate limits!")
        
        return "\n".join(lines)


# Global monitor instance
_monitor: Optional[QueenAssetMonitor] = None

def get_asset_monitor() -> QueenAssetMonitor:
    """Get or create the global Asset Monitor."""
    global _monitor
    if _monitor is None:
        _monitor = QueenAssetMonitor()
    return _monitor


# ═══════════════════════════════════════════════════════════════════════════════
# 🌊👑 QUEEN'S UNIFIED OCEAN VIEW - WHAT WE HAVE + WHAT WE CAN BUY
# ═══════════════════════════════════════════════════════════════════════════════

class QueenOceanView:
    """
    🌊👑 UNIFIED VIEW: POSITIONS + OPPORTUNITIES
    
    Combines:
    1. WHAT WE HAVE - Current positions from Asset Monitor
    2. WHAT WE CAN BUY - Opportunities from Ocean Scanner
    
    Queen sees the FULL PICTURE at all times!
    """
    
    def __init__(self):
        """Initialize the Ocean View."""
        self.monitor = get_asset_monitor()
        self.ocean_scanner = None
        
        # Opportunities from Ocean Scanner
        self.opportunities: List[Dict] = []
        self.opportunities_last_updated: float = 0
        
        # Combined view
        self.last_unified_view: Dict = {}
        
        self._connect_ocean_scanner()
        logger.info("🌊👑 Queen's Ocean View INITIALIZED")
    
    def _connect_ocean_scanner(self):
        """Connect to Ocean Scanner."""
        try:
            from aureon_ocean_scanner import OceanScanner
            
            # Get exchange clients for the scanner
            exchanges = {}
            try:
                from kraken_client import get_kraken_client
                exchanges['kraken'] = get_kraken_client()
            except Exception:
                pass
            
            try:
                from binance_client import get_binance_client
                exchanges['binance'] = get_binance_client()
            except Exception:
                pass
            
            try:
                from alpaca_client import AlpacaClient
                exchanges['alpaca'] = AlpacaClient()
            except Exception:
                pass
            
            self.ocean_scanner = OceanScanner(exchanges=exchanges)
            logger.info("   🌊 Ocean Scanner: CONNECTED")
        except Exception as e:
            logger.warning(f"   🌊 Ocean Scanner: {e}")
    
    async def scan_opportunities(self, limit: int = 20) -> List[Dict]:
        """
        🔭 SCAN THE OCEAN FOR OPPORTUNITIES
        
        Uses FREE public APIs to find the best opportunities
        without hitting rate limits!
        """
        if not self.ocean_scanner:
            return []
        
        try:
            # Discover universe if not done
            if self.ocean_scanner.total_symbols_scanned == 0:
                await self.ocean_scanner.discover_universe()
            
            # Scan for opportunities
            opps = await self.ocean_scanner.scan_ocean(limit=limit)
            
            self.opportunities = [
                {
                    'symbol': opp.symbol,
                    'exchange': opp.exchange,
                    'price': opp.price,
                    'momentum_1h': opp.momentum_1h,
                    'momentum_24h': opp.momentum_24h,
                    'volume': opp.volume,
                    'ocean_score': opp.ocean_score,
                    'reason': opp.reason,
                }
                for opp in opps
            ]
            self.opportunities_last_updated = time.time()
            
            return self.opportunities
        except Exception as e:
            logger.error(f"Ocean scan error: {e}")
            return []
    
    def get_opportunities_free_api(self, symbols: List[str] = None, limit: int = 20) -> List[Dict]:
        """
        🔭 GET QUICK OPPORTUNITIES FROM FREE APIS (no async needed)
        
        Scans Binance public API for momentum/movers.
        """
        opportunities = []
        
        try:
            # Get 24h ticker data from Binance (FREE, no auth)
            url = "https://api.binance.com/api/v3/ticker/24hr"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                tickers = resp.json()
                
                # Filter for USDT pairs and calculate scores
                for t in tickers:
                    symbol = t.get('symbol', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    try:
                        price = float(t.get('lastPrice', 0))
                        change_24h = float(t.get('priceChangePercent', 0))
                        volume = float(t.get('quoteVolume', 0))
                        
                        if price > 0 and volume > 10000:  # Min $10k volume
                            base_symbol = symbol.replace('USDT', '')
                            
                            # Calculate opportunity score
                            score = abs(change_24h) * 0.5 + min(volume / 1000000, 50) * 0.5
                            
                            opportunities.append({
                                'symbol': base_symbol,
                                'exchange': 'binance',
                                'price': price,
                                'change_24h': change_24h,
                                'volume_24h': volume,
                                'score': score,
                                'direction': 'LONG' if change_24h > 0 else 'SHORT',
                            })
                    except (ValueError, TypeError):
                        continue
                
                # Sort by absolute change (volatility = opportunity)
                opportunities.sort(key=lambda x: abs(x['change_24h']), reverse=True)
                
        except Exception as e:
            logger.debug(f"Free API opportunity scan error: {e}")
        
        self.opportunities = opportunities[:limit]
        self.opportunities_last_updated = time.time()
        return self.opportunities[:limit]
    
    def get_unified_view(self, refresh_positions: bool = False, scan_opportunities: bool = True) -> Dict:
        """
        👑🌊 GET THE UNIFIED VIEW - WHAT WE HAVE + WHAT WE CAN BUY
        
        Returns complete picture of:
        - Current positions with live prices
        - Top opportunities from the ocean
        - Suggested actions
        """
        # Get what we HAVE
        portfolio = self.monitor.get_full_portfolio_status(refresh_positions)
        
        # Get what we CAN BUY (from free APIs)
        if scan_opportunities:
            self.get_opportunities_free_api(limit=20)
        
        # Build unified view
        unified = {
            'timestamp': time.time(),
            
            # WHAT WE HAVE
            'portfolio': {
                'total_value': portfolio['totals']['value'],
                'total_cost': portfolio['totals']['cost_basis'],
                'unrealized_pnl': portfolio['totals']['unrealized_pnl'],
                'unrealized_pnl_pct': portfolio['totals']['unrealized_pnl_pct'],
                'positions_count': len(portfolio['positions']),
                'by_exchange': portfolio['by_exchange'],
                'top_positions': sorted(portfolio['positions'], key=lambda p: -p['market_value'])[:10],
            },
            
            # WHAT WE CAN BUY
            'opportunities': {
                'count': len(self.opportunities),
                'last_updated': self.opportunities_last_updated,
                'top_movers': self.opportunities[:10],
                'gainers': [o for o in self.opportunities if o.get('change_24h', 0) > 5][:5],
                'losers': [o for o in self.opportunities if o.get('change_24h', 0) < -5][:5],
            },
            
            # OVERLAP - What we have that's also moving
            'overlap': [],
            
            # SUGGESTIONS
            'suggestions': [],
        }
        
        # Find overlap between positions and opportunities
        position_symbols = {p['symbol'] for p in portfolio['positions']}
        for opp in self.opportunities:
            if opp['symbol'] in position_symbols:
                unified['overlap'].append({
                    'symbol': opp['symbol'],
                    'change_24h': opp.get('change_24h', 0),
                    'action': 'HOLD ✅' if opp.get('change_24h', 0) > 0 else 'WATCH ⚠️',
                })
        
        # Generate suggestions
        if unified['opportunities']['gainers']:
            top_gainer = unified['opportunities']['gainers'][0]
            if top_gainer['symbol'] not in position_symbols:
                unified['suggestions'].append({
                    'action': 'BUY',
                    'symbol': top_gainer['symbol'],
                    'reason': f"+{top_gainer.get('change_24h', 0):.1f}% in 24h - Strong momentum",
                    'price': top_gainer.get('price', 0),
                })
        
        self.last_unified_view = unified
        return unified
    
    def display_unified_view(self, refresh: bool = False) -> str:
        """Display the unified view in a nice format."""
        view = self.get_unified_view(refresh_positions=refresh)
        
        lines = [
            "=" * 90,
            "🌊👑 QUEEN'S UNIFIED OCEAN VIEW - WHAT WE HAVE + WHAT WE CAN BUY 👑🌊",
            "=" * 90,
            "",
            "═══════════════════════════════════════════════════════════════════════════════════════════",
            "💎 WHAT WE HAVE (CURRENT PORTFOLIO)",
            "═══════════════════════════════════════════════════════════════════════════════════════════",
            f"   📊 TOTAL VALUE: ${view['portfolio']['total_value']:,.2f}",
            f"   💰 COST BASIS: ${view['portfolio']['total_cost']:,.2f}",
            f"   📈 UNREALIZED P&L: ${view['portfolio']['unrealized_pnl']:+,.2f} ({view['portfolio']['unrealized_pnl_pct']:+.2f}%)",
            f"   🔢 POSITIONS: {view['portfolio']['positions_count']}",
            "",
        ]
        
        # Top positions
        lines.append("   📋 TOP HOLDINGS:")
        for p in view['portfolio']['top_positions'][:5]:
            if p['market_value'] > 0.01:
                pnl_str = f" | P&L: ${p['unrealized_pnl']:+.2f}" if p['cost_basis'] > 0 else ""
                lines.append(f"      💎 {p['symbol']:10} ${p['market_value']:>10.2f}{pnl_str}")
        
        lines.append("")
        lines.append("═══════════════════════════════════════════════════════════════════════════════════════════")
        lines.append("🌊 WHAT WE CAN BUY (OCEAN OPPORTUNITIES)")
        lines.append("═══════════════════════════════════════════════════════════════════════════════════════════")
        
        # Top gainers
        lines.append("   🚀 TOP GAINERS (24h):")
        for opp in view['opportunities'].get('gainers', [])[:5]:
            lines.append(f"      🟢 {opp['symbol']:10} +{opp.get('change_24h', 0):>6.2f}% @ ${opp.get('price', 0):>12.6f}")
        
        # Top losers (potential dip buys)
        lines.append("")
        lines.append("   📉 TOP DIPS (potential buys):")
        for opp in view['opportunities'].get('losers', [])[:5]:
            lines.append(f"      🔴 {opp['symbol']:10} {opp.get('change_24h', 0):>6.2f}% @ ${opp.get('price', 0):>12.6f}")
        
        # Overlap
        if view['overlap']:
            lines.append("")
            lines.append("   🔄 YOUR POSITIONS THAT ARE MOVING:")
            for o in view['overlap'][:5]:
                lines.append(f"      {o['action']} {o['symbol']:10} {o['change_24h']:+.2f}%")
        
        # Suggestions
        if view['suggestions']:
            lines.append("")
            lines.append("═══════════════════════════════════════════════════════════════════════════════════════════")
            lines.append("💡 QUEEN'S SUGGESTIONS")
            lines.append("═══════════════════════════════════════════════════════════════════════════════════════════")
            for s in view['suggestions']:
                lines.append(f"   ➡️  {s['action']} {s['symbol']}: {s['reason']}")
        
        lines.append("")
        lines.append("=" * 90)
        lines.append(f"⏰ Updated: {datetime.fromtimestamp(view['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("📡 All data from FREE public APIs - constant monitoring enabled!")
        
        return "\n".join(lines)


# Global ocean view instance
_ocean_view: Optional[QueenOceanView] = None

def get_ocean_view() -> QueenOceanView:
    """Get or create the global Ocean View."""
    global _ocean_view
    if _ocean_view is None:
        _ocean_view = QueenOceanView()
    return _ocean_view


# ═══════════════════════════════════════════════════════════════════════════════
# TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    print()
    print("👑💰🎮 QUEEN ASSET COMMAND CENTER - FULL SYSTEM TEST 🎮💰👑")
    print()
    
    # Create command center
    center = get_asset_command_center()
    
    # Scan all assets (uses trading APIs)
    print("🔍 STEP 1: Getting positions from TRADING APIs (authenticated)...")
    print()
    
    inventory = center.scan_all_assets(force_refresh=True)
    
    # Display full inventory
    print(center.display_inventory(inventory))
    
    # Now test the FREE API monitor
    print()
    print("=" * 80)
    print("📊 STEP 2: Setting up CONTINUOUS MONITORING with FREE APIs...")
    print("=" * 80)
    print()
    
    monitor = get_asset_monitor()
    
    # Refresh positions from APIs (only needed occasionally)
    monitor.refresh_positions_from_apis(force=True)
    
    # Get live portfolio using FREE APIs
    print(monitor.display_portfolio())
    
    # Now test the UNIFIED OCEAN VIEW
    print()
    print("=" * 90)
    print("🌊 STEP 3: UNIFIED OCEAN VIEW - WHAT WE HAVE + WHAT WE CAN BUY")
    print("=" * 90)
    print()
    
    ocean_view = get_ocean_view()
    print(ocean_view.display_unified_view(refresh=False))
    
    print()
    print("👑 QUEEN SERO HAS FULL VISIBILITY!")
    print()
    print("💡 USAGE:")
    print("   📊 monitor.get_full_portfolio_status()    - What we HAVE")
    print("   🌊 ocean_view.get_opportunities_free_api() - What we can BUY") 
    print("   👑 ocean_view.get_unified_view()           - BOTH combined!")
    print()
    print("   🔄 All using FREE public APIs - no rate limits!")
