#!/usr/bin/env python3
"""
🦎 CoinGecko Price Feeder - FREE Market Data Source for Alpaca Heavy Lifting!

This creates a cache file that animal scanners can use WITHOUT hitting Alpaca API.

Usage:
    python coingecko_price_feeder.py  # Run once to populate cache
    # Or import and run in background
    
CoinGecko API is FREE with generous rate limits (10-30 calls/minute).
We fetch prices for ALL Alpaca-tradeable crypto and cache locally.
"""

import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping - causes Windows exit errors
    except Exception:
        pass

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CoinGecko FREE API
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Alpaca-tradeable coins mapped to CoinGecko IDs
ALPACA_TO_COINGECKO = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "SHIB": "shiba-inu",
    "XRP": "ripple",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "UNI": "uniswap",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "ATOM": "cosmos",
    "XLM": "stellar",
    "ALGO": "algorand",
    "FIL": "filecoin",
    "VET": "vechain",
    "ETC": "ethereum-classic",
    "AAVE": "aave",
    "MKR": "maker",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "AXS": "axie-infinity",
    "GRT": "the-graph",
    "CRV": "curve-dao-token",
    "FTM": "fantom",
    "NEAR": "near",
    "APE": "apecoin",
    "RUNE": "thorchain",
    "LDO": "lido-dao",
    "OP": "optimism",
    "ARB": "arbitrum",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "SEI": "sei-network",
    "TIA": "celestia",
    "JUP": "jupiter-exchange-solana",
    "PYTH": "pyth-network",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "PEPE": "pepe",
    "FLOKI": "floki",
    "RENDER": "render-token",
    "FET": "fetch-ai",
    "TAO": "bittensor",
    "WLD": "worldcoin-wld",
    "IMX": "immutable-x",
    "STX": "stacks",
    "ONDO": "ondo-finance",
    "JTO": "jito-governance-token",
    "BLUR": "blur",
    "GMT": "stepn",
    "APT": "aptos",
    "XTZ": "tezos",
    "HBAR": "hedera-hashgraph",
    "ICP": "internet-computer",
    "TRX": "tron",
    "CRO": "crypto-com-chain",
    "LEO": "leo-token",
}

# Cache paths
CACHE_DIR = Path("ws_cache")
BINANCE_CACHE_PATH = CACHE_DIR / "ws_prices.json"
KRAKEN_CACHE_PATH = CACHE_DIR / "kraken_prices.json"
COINGECKO_CACHE_PATH = Path("coingecko_market_cache.json")


def fetch_coingecko_prices(coin_ids: List[str]) -> Dict[str, Any]:
    """
    Fetch prices from CoinGecko FREE API.
    
    Returns dict with price, 24h change, volume for each coin.
    """
    if not coin_ids:
        return {}
    
    # CoinGecko allows up to 250 IDs per call
    ids_str = ",".join(coin_ids[:250])
    url = f"{COINGECKO_API}/simple/price"
    params = {
        "ids": ids_str,
        "vs_currencies": "usd",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"CoinGecko API error: {e}")
        return {}


def build_ticker_cache(coingecko_data: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Convert CoinGecko data to ticker cache format for animal scanners.
    """
    ticker_cache = {}
    
    # Reverse map: CoinGecko ID -> Alpaca symbol
    cg_to_alpaca = {v: k for k, v in ALPACA_TO_COINGECKO.items()}
    
    for cg_id, data in coingecko_data.items():
        if not isinstance(data, dict):
            continue
        
        base = cg_to_alpaca.get(cg_id, cg_id.upper())
        price = float(data.get('usd', 0) or 0)
        change_24h = float(data.get('usd_24h_change', 0) or 0)
        volume = float(data.get('usd_24h_vol', 0) or 0)
        
        if price <= 0:
            continue
        
        ticker_cache[f"{base}/USD"] = {
            "base": base,
            "quote": "USD",
            "price": price,
            "change24h": change_24h,
            "volume": volume,
            "source": "coingecko",
            "timestamp": time.time(),
        }
    
    return ticker_cache


def save_cache(ticker_cache: Dict[str, Dict], path: Path) -> bool:
    """Save ticker cache to JSON file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": time.time(),
            "source": "coingecko_free_api",
            "ticker_cache": ticker_cache,
            "prices": {k: v.get("price", 0) for k, v in ticker_cache.items()},
        }
        # Atomic write
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        tmp_path.rename(path)
        return True
    except Exception as e:
        logger.error(f"Failed to save cache to {path}: {e}")
        return False


def run_price_feed(interval: float = 30.0, max_iterations: int = 0):
    """
    Run continuous price feed loop.
    
    Args:
        interval: Seconds between updates (30s for free CoinGecko)
        max_iterations: 0 = forever, >0 = limited iterations
    """
    logger.info("🦎 CoinGecko Price Feeder starting...")
    logger.info(f"   📊 Tracking {len(ALPACA_TO_COINGECKO)} Alpaca-tradeable coins")
    logger.info(f"   ⏱️ Update interval: {interval}s")
    logger.info(f"   📁 Cache: {BINANCE_CACHE_PATH}")
    
    coin_ids = list(ALPACA_TO_COINGECKO.values())
    iteration = 0
    
    while True:
        iteration += 1
        try:
            # Fetch from CoinGecko
            logger.info(f"🦎 Fetching prices for {len(coin_ids)} coins...")
            cg_data = fetch_coingecko_prices(coin_ids)
            
            if cg_data:
                # Build ticker cache
                ticker_cache = build_ticker_cache(cg_data)
                logger.info(f"   ✅ Got {len(ticker_cache)} prices")
                
                # Save to both paths (for compatibility)
                save_cache(ticker_cache, BINANCE_CACHE_PATH)  # Animal scanners look here
                save_cache(ticker_cache, COINGECKO_CACHE_PATH)
                logger.info(f"   💾 Saved to {BINANCE_CACHE_PATH}")
                
                # Show sample prices
                samples = list(ticker_cache.items())[:5]
                for sym, data in samples:
                    logger.info(f"      {sym}: ${data['price']:.4f} ({data['change24h']:+.2f}%)")
            else:
                logger.warning("   ⚠️ No data from CoinGecko")
            
        except Exception as e:
            logger.error(f"Price feed error: {e}")
        
        # Check iteration limit
        if max_iterations > 0 and iteration >= max_iterations:
            logger.info(f"🦎 Completed {iteration} iterations")
            break
        
        # Sleep until next update
        time.sleep(interval)


def fetch_once() -> Dict[str, Dict]:
    """
    Fetch prices once and return ticker cache.
    Also saves to cache files.
    """
    coin_ids = list(ALPACA_TO_COINGECKO.values())
    cg_data = fetch_coingecko_prices(coin_ids)
    
    if cg_data:
        ticker_cache = build_ticker_cache(cg_data)
        save_cache(ticker_cache, BINANCE_CACHE_PATH)
        save_cache(ticker_cache, COINGECKO_CACHE_PATH)
        return ticker_cache
    
    return {}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CoinGecko Price Feeder")
    parser.add_argument("--once", action="store_true", help="Fetch once and exit")
    parser.add_argument("--interval", type=float, default=30.0, help="Update interval (seconds)")
    args = parser.parse_args()
    
    if args.once:
        cache = fetch_once()
        print(f"\n✅ Fetched {len(cache)} prices")
        print(f"   Saved to: {BINANCE_CACHE_PATH}")
    else:
        run_price_feed(interval=args.interval)
