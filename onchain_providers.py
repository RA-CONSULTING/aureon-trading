"""
On-Chain Provider Integration Layer

Supports multiple blockchain data providers (Etherscan, Covalent, Alchemy, Infura)
to detect whale transfers, exchange deposits/withdrawals, and large movements.

Architecture:
- Provider abstraction with fallback chain
- Rate limiting and caching per provider
- Unified TransferEvent dataclass
- Known exchange wallet registry
"""
import sys
import os

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

import logging
import time
import json
import requests
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from collections import deque
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

# Load env vars
try:
    from dotenv import load_dotenv
    dotenv_candidates = [Path(os.getenv("DOTENV_PATH", "")), Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"]
    for candidate in dotenv_candidates:
        try:
            if candidate.exists():
                load_dotenv(dotenv_path=str(candidate), override=False)
                break
        except Exception:
            continue
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════
# 🏦 KNOWN EXCHANGE WALLET ADDRESSES (ERC20/ETH)
# ═══════════════════════════════════════════════════════════════

KNOWN_EXCHANGE_ADDRESSES = {
    # Binance
    "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance 14",
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": "Binance 15",
    "0xDFD5293D8e347dFe59E90eFd55b2956a1343963d": "Binance 16",
    "0x56Eddb7aa87536c09CCc2793473599fD21A8b17F": "Binance 17",
    "0x9696f59E4d72E237BE84fFD425DCaD154Bf96976": "Binance 18",
    "0x4E9ce36E442e55EcD9025B9a6E0D88485d628A67": "Binance 19",
    "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": "Binance 8",
    "0xF977814e90dA44bFA03b6295A0616a897441aceC": "Binance Hot Wallet",
    
    # Kraken
    "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2": "Kraken 1",
    "0x0A869d79a7052C7f1b55a8EbAbbEa3420F0D1E13": "Kraken 2",
    "0xE853c56864A2ebe4576a807D26Fdc4A0adA51919": "Kraken 3",
    "0x267be1C1D684F78cb4F6a176C4911b741E4Ffdc0": "Kraken 4",
    
    # Coinbase
    "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": "Coinbase 1",
    "0x503828976D22510aad0201ac7EC88293211D23Da": "Coinbase 2",
    "0xddfAbCdc4D8FfC6d5beaf154f18B778f892A0740": "Coinbase 3",
    "0x3cD751E6b0078Be393132286c442345e5DC49699": "Coinbase 4",
    "0xb5d85CBf7cB3EE0D56b3bB207D5Fc4B82f43F511": "Coinbase 5",
    "0xeB2629a2734e272Bcc07BDA959863f316F4bD4Cf": "Coinbase 6",
    
    # Bitfinex
    "0x1151314c646Ce4E0eFD76d1aF4760aE66a9Fe30F": "Bitfinex 1",
    "0x876EabF441B2EE5B5b0554Fd502a8E0600950cFa": "Bitfinex 2",
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": "Bitfinex 3",
    
    # Huobi
    "0xDc76CD25977E0a5Ae17155770273aD58648900D3": "Huobi 1",
    "0xAB5C66752a9e8167967685F1450532fB96d5d24f": "Huobi 2",
    "0x6748F50f686bfbcA6Fe8ad62b22228b87F31ff2b": "Huobi 3",
    
    # Bittrex
    "0xFBb1b73C4f0BDa4f67dcA266ce6Ef42f520fBB98": "Bittrex",
    
    # Gemini
    "0x5F65f7b609678448494De4C87521CdF6cEf1e932": "Gemini",
    "0xd24400ae8BfEBb18cA49Be86258a3C749cf46853": "Gemini 2",
}

# Reverse lookup: address -> exchange name
EXCHANGE_ADDRESS_TO_NAME = {addr.lower(): name.split()[0] for addr, name in KNOWN_EXCHANGE_ADDRESSES.items()}


class TransferDirection(Enum):
    DEPOSIT = "deposit"        # Into exchange
    WITHDRAWAL = "withdrawal"  # From exchange
    INTERNAL = "internal"      # Between exchange wallets
    WHALE = "whale"            # Large transfer not exchange-related


@dataclass
class TransferEvent:
    """Unified on-chain transfer event"""
    tx_hash: str
    block_number: int
    timestamp: float
    from_address: str
    to_address: str
    amount: float  # In native units (ETH/BTC/etc)
    amount_usd: float
    token_symbol: str
    token_address: Optional[str] = None
    direction: TransferDirection = TransferDirection.WHALE
    exchange_name: Optional[str] = None
    gas_used: int = 0
    gas_price: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['direction'] = self.direction.value
        return d


# ═══════════════════════════════════════════════════════════════
# 🔌 PROVIDER INTERFACE
# ═══════════════════════════════════════════════════════════════

class OnchainProvider:
    """Base class for on-chain data providers"""
    
    def __init__(self, api_key: str, rate_limit_per_sec: float = 5.0):
        self.api_key = api_key
        self.rate_limit_per_sec = rate_limit_per_sec
        self._last_request_time = 0.0
        self._request_count = 0
        
    def _rate_limit(self):
        """Simple rate limiting"""
        now = time.time()
        min_interval = 1.0 / self.rate_limit_per_sec
        elapsed = now - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()
        self._request_count += 1
    
    def get_recent_transfers(self, address: str, limit: int = 100) -> List[TransferEvent]:
        """Get recent transfers for an address"""
        raise NotImplementedError
    
    def get_transaction(self, tx_hash: str) -> Optional[TransferEvent]:
        """Get single transaction details"""
        raise NotImplementedError
    
    def get_token_transfers(self, token_address: str, limit: int = 100) -> List[TransferEvent]:
        """Get recent transfers for a token contract"""
        raise NotImplementedError


class EtherscanProvider(OnchainProvider):
    """Etherscan API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")
        super().__init__(api_key, rate_limit_per_sec=5.0)
        self.base_url = "https://api.etherscan.io/api"
    
    def get_recent_transfers(self, address: str, limit: int = 100) -> List[TransferEvent]:
        """Fetch recent ETH + ERC20 transfers"""
        if not self.api_key:
            logger.warning("Etherscan API key not configured")
            return []
        
        self._rate_limit()
        
        try:
            # Get normal ETH transactions
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'page': 1,
                'offset': limit,
                'sort': 'desc',
                'apikey': self.api_key
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            
            events = []
            if data.get('status') == '1' and data.get('result'):
                for tx in data['result'][:limit]:
                    value_eth = float(tx.get('value', 0)) / 1e18
                    events.append(TransferEvent(
                        tx_hash=tx['hash'],
                        block_number=int(tx['blockNumber']),
                        timestamp=float(tx['timeStamp']),
                        from_address=tx['from'].lower(),
                        to_address=tx['to'].lower(),
                        amount=value_eth,
                        amount_usd=0.0,  # Filled by caller with price lookup
                        token_symbol='ETH',
                        token_address=None,
                        gas_used=int(tx.get('gasUsed', 0)),
                        gas_price=int(tx.get('gasPrice', 0))
                    ))
            
            # Get ERC20 token transfers
            self._rate_limit()
            params['action'] = 'tokentx'
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            
            if data.get('status') == '1' and data.get('result'):
                for tx in data['result'][:limit]:
                    decimals = int(tx.get('tokenDecimal', 18))
                    value = float(tx.get('value', 0)) / (10 ** decimals)
                    events.append(TransferEvent(
                        tx_hash=tx['hash'],
                        block_number=int(tx['blockNumber']),
                        timestamp=float(tx['timeStamp']),
                        from_address=tx['from'].lower(),
                        to_address=tx['to'].lower(),
                        amount=value,
                        amount_usd=0.0,
                        token_symbol=tx.get('tokenSymbol', 'UNKNOWN'),
                        token_address=tx.get('contractAddress', '').lower(),
                        gas_used=int(tx.get('gasUsed', 0)),
                        gas_price=int(tx.get('gasPrice', 0))
                    ))
            
            return events
            
        except Exception as e:
            logger.error(f"Etherscan API error: {e}")
            return []
    
    def get_transaction(self, tx_hash: str) -> Optional[TransferEvent]:
        """Get single transaction"""
        if not self.api_key:
            return None
        
        self._rate_limit()
        
        try:
            params = {
                'module': 'proxy',
                'action': 'eth_getTransactionByHash',
                'txhash': tx_hash,
                'apikey': self.api_key
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            data = resp.json()
            
            if data.get('result'):
                tx = data['result']
                value_eth = int(tx.get('value', '0x0'), 16) / 1e18
                return TransferEvent(
                    tx_hash=tx['hash'],
                    block_number=int(tx.get('blockNumber', '0x0'), 16),
                    timestamp=time.time(),  # Need to get block timestamp
                    from_address=tx.get('from', '').lower(),
                    to_address=tx.get('to', '').lower(),
                    amount=value_eth,
                    amount_usd=0.0,
                    token_symbol='ETH',
                    token_address=None,
                    gas_used=0,
                    gas_price=int(tx.get('gasPrice', '0x0'), 16)
                )
        except Exception as e:
            logger.error(f"Etherscan tx lookup error: {e}")
            return None


class CovalentProvider(OnchainProvider):
    """Covalent API provider (multi-chain)"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("COVALENT_API_KEY", "")
        super().__init__(api_key, rate_limit_per_sec=5.0)
        self.base_url = "https://api.covalenthq.com/v1"
    
    def get_recent_transfers(self, address: str, limit: int = 100, chain_id: int = 1) -> List[TransferEvent]:
        """Fetch transfers via Covalent (supports multiple chains)"""
        if not self.api_key:
            logger.warning("Covalent API key not configured")
            return []
        
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{chain_id}/address/{address}/transactions_v2/"
            headers = {'Authorization': f'Bearer {self.api_key}'}
            params = {'page-size': limit}
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            data = resp.json()
            
            events = []
            if data.get('data') and data['data'].get('items'):
                for tx in data['data']['items'][:limit]:
                    value_eth = float(tx.get('value', 0)) / 1e18
                    events.append(TransferEvent(
                        tx_hash=tx['tx_hash'],
                        block_number=tx['block_height'],
                        timestamp=datetime.fromisoformat(tx['block_signed_at'].replace('Z', '+00:00')).timestamp(),
                        from_address=tx['from_address'].lower(),
                        to_address=tx['to_address'].lower() if tx.get('to_address') else '',
                        amount=value_eth,
                        amount_usd=0.0,
                        token_symbol='ETH',
                        gas_used=tx.get('gas_spent', 0),
                        gas_price=tx.get('gas_price', 0)
                    ))
            
            return events
            
        except Exception as e:
            logger.error(f"Covalent API error: {e}")
            return []


class AlchemyProvider(OnchainProvider):
    """Alchemy API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("ALCHEMY_API_KEY", "")
        super().__init__(api_key, rate_limit_per_sec=10.0)
        # Construct URL with API key
        network = os.getenv("ALCHEMY_NETWORK", "eth-mainnet")
        self.base_url = f"https://{network}.g.alchemy.com/v2/{api_key}"
    
    def get_recent_transfers(self, address: str, limit: int = 100) -> List[TransferEvent]:
        """Fetch transfers via Alchemy"""
        if not self.api_key:
            logger.warning("Alchemy API key not configured")
            return []
        
        self._rate_limit()
        
        try:
            # Use alchemy_getAssetTransfers
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "alchemy_getAssetTransfers",
                "params": [{
                    "fromBlock": "0x0",
                    "toBlock": "latest",
                    "fromAddress": address,
                    "category": ["external", "erc20"],
                    "maxCount": hex(limit),
                    "order": "desc"
                }]
            }
            
            resp = requests.post(self.base_url, json=payload, timeout=10)
            data = resp.json()
            
            events = []
            if data.get('result') and data['result'].get('transfers'):
                for tx in data['result']['transfers']:
                    events.append(TransferEvent(
                        tx_hash=tx['hash'],
                        block_number=int(tx['blockNum'], 16),
                        timestamp=time.time(),  # Alchemy doesn't provide timestamp directly
                        from_address=tx.get('from', '').lower(),
                        to_address=tx.get('to', '').lower(),
                        amount=float(tx.get('value', 0)),
                        amount_usd=0.0,
                        token_symbol=tx.get('asset', 'ETH'),
                        token_address=tx.get('rawContract', {}).get('address', '').lower() if tx.get('rawContract') else None
                    ))
            
            return events
            
        except Exception as e:
            logger.error(f"Alchemy API error: {e}")
            return []


# ═══════════════════════════════════════════════════════════════
# 🌊 PROVIDER MANAGER WITH FALLBACK CHAIN
# ═══════════════════════════════════════════════════════════════

class OnchainProviderManager:
    """Manages multiple providers with fallback"""
    
    def __init__(self):
        self.providers: List[OnchainProvider] = []
        self._setup_providers()
        
    def _setup_providers(self):
        """Initialize all available providers"""
        # Try Etherscan first (most reliable for Ethereum)
        if os.getenv("ETHERSCAN_API_KEY"):
            self.providers.append(EtherscanProvider())
            logger.info("✅ Etherscan provider initialized")
        
        # Try Alchemy second (good rate limits)
        if os.getenv("ALCHEMY_API_KEY"):
            self.providers.append(AlchemyProvider())
            logger.info("✅ Alchemy provider initialized")
        
        # Try Covalent third (multi-chain)
        if os.getenv("COVALENT_API_KEY"):
            self.providers.append(CovalentProvider())
            logger.info("✅ Covalent provider initialized")
        
        if not self.providers:
            logger.warning("⚠️  No on-chain providers configured (set ETHERSCAN_API_KEY, ALCHEMY_API_KEY, or COVALENT_API_KEY)")
    
    def get_recent_transfers(self, address: str, limit: int = 100) -> List[TransferEvent]:
        """Try each provider in order until success"""
        for provider in self.providers:
            try:
                events = provider.get_recent_transfers(address, limit)
                if events:
                    return events
            except Exception as e:
                logger.debug(f"Provider {provider.__class__.__name__} failed: {e}")
                continue
        return []
    
    def get_transaction(self, tx_hash: str) -> Optional[TransferEvent]:
        """Try each provider in order until success"""
        for provider in self.providers:
            try:
                event = provider.get_transaction(tx_hash)
                if event:
                    return event
            except Exception as e:
                logger.debug(f"Provider {provider.__class__.__name__} failed: {e}")
                continue
        return None
    
    def classify_transfer(self, event: TransferEvent) -> TransferEvent:
        """Classify transfer direction based on exchange addresses"""
        from_addr = event.from_address.lower()
        to_addr = event.to_address.lower()
        
        from_exchange = EXCHANGE_ADDRESS_TO_NAME.get(from_addr)
        to_exchange = EXCHANGE_ADDRESS_TO_NAME.get(to_addr)
        
        if from_exchange and to_exchange:
            # Both are exchange addresses - internal movement
            event.direction = TransferDirection.INTERNAL
            event.exchange_name = from_exchange
        elif to_exchange:
            # Deposit into exchange
            event.direction = TransferDirection.DEPOSIT
            event.exchange_name = to_exchange
        elif from_exchange:
            # Withdrawal from exchange
            event.direction = TransferDirection.WITHDRAWAL
            event.exchange_name = from_exchange
        else:
            # Whale transfer (not exchange related)
            event.direction = TransferDirection.WHALE
        
        return event
    
    def get_exchange_activity(self, exchange_name: str, limit: int = 50) -> List[TransferEvent]:
        """Get all activity for a specific exchange"""
        events = []
        exchange_addrs = [addr for addr, name in KNOWN_EXCHANGE_ADDRESSES.items() if name.lower().startswith(exchange_name.lower())]
        
        for addr in exchange_addrs[:3]:  # Limit to 3 addresses to avoid rate limits
            try:
                transfers = self.get_recent_transfers(addr, limit=limit)
                for event in transfers:
                    self.classify_transfer(event)
                events.extend(transfers)
            except Exception as e:
                logger.debug(f"Failed to fetch for {addr}: {e}")
                continue
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]


# Global instance
_provider_manager: Optional[OnchainProviderManager] = None

def get_provider_manager() -> OnchainProviderManager:
    """Get singleton provider manager"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = OnchainProviderManager()
    return _provider_manager
