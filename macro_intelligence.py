#!/usr/bin/env python3
"""
MACRO INTELLIGENCE — Pre-Execution Market Context
==================================================
Fetches and caches macro-level signals before every entry decision.
All APIs are free and require no authentication.

Signals gathered:
  1. Crypto Fear & Greed Index         (alternative.me)
  2. Market-wide data                   (CoinGecko /global)
  3. BTC + ETH + XRP 24h trends         (CoinGecko /coins/markets)
  4. Coin-specific 24h trend            (CoinGecko)
  5. Trending coins                     (CoinGecko /search/trending)
  6. BTC 6h volume pattern              (Kraken OHLC)

Output via get_entry_context(pair):
  {
    "fear_greed":        int,       # 0-100 (0=extreme fear, 100=extreme greed)
    "fear_label":        str,       # "Extreme Fear" … "Extreme Greed"
    "btc_24h":           float,     # BTC 24h % change
    "eth_24h":           float,     # ETH 24h % change
    "xrp_24h":           float,     # XRP 24h % change (payment coin correlation)
    "market_24h":        float,     # Total market cap 24h % change
    "btc_dominance":     float,     # BTC dominance %
    "coin_24h":          float,     # This coin's own 24h % change
    "coin_vol_usd":      float,     # This coin's 24h volume USD
    "is_trending":       bool,      # Coin in CoinGecko top-10 trending
    "btc_vol_pattern":   str,       # "rising" | "falling" | "flat" (6h vol trend)
    "macro_score":       float,     # -2.0 → +2.0 composite score
    "entry_ok":          bool,      # False = macro says WAIT/SKIP
    "block_reason":      str,       # Why entry is blocked (if entry_ok=False)
    "signal_age_s":      float,     # Seconds since last refresh
  }

macro_score feeds directly into find_best_target() candidate scoring.
entry_ok acts as a hard gate in research_target().

Refresh interval: 10 minutes (MACRO_REFRESH_S).
Never blocks on network — returns last cached value on failure.
"""

import json
import logging
import threading
import time
import urllib.request
from typing import Dict, Optional

logger = logging.getLogger(__name__)

MACRO_REFRESH_S = 600          # Refresh every 10 minutes
_COINGECKO_IDS = {             # Kraken base → CoinGecko ID
    "XBT":  "bitcoin",
    "BTC":  "bitcoin",
    "ETH":  "ethereum",
    "XRP":  "ripple",
    "SOL":  "solana",
    "ADA":  "cardano",
    "DOGE": "dogecoin",
    "DOT":  "polkadot",
    "LINK": "chainlink",
    "LTC":  "litecoin",
    "XLM":  "stellar",
    "AVAX": "avalanche-2",
    "ATOM": "cosmos",
    "UNI":  "uniswap",
    "ALGO": "algorand",
    "DASH": "dash",
    "XMR":  "monero",
    "ZEC":  "zcash",
    "EOS":  "eos",
    "COMP": "compound-governance-token",
    "FIL":  "filecoin",
    "NEAR": "near",
    "SUI":  "sui",
    "APT":  "aptos",
    "INJ":  "injective-protocol",
    "TIA":  "celestia",
}

# Hard-block thresholds
EXTREME_FEAR_BLOCK  = 15   # F&G ≤ 15 → block entry
MARKET_DROP_BLOCK   = -6.0 # Market cap 24h ≤ -6% → block entry
BTC_CRASH_BLOCK     = -8.0 # BTC 24h ≤ -8% → block entry


class MacroIntelligence:
    """
    Pre-execution macro context engine.

    Usage:
        macro = MacroIntelligence()
        ctx   = macro.get_entry_context("SOLUSDT")
        if not ctx["entry_ok"]:
            logger.warning(f"MACRO BLOCK: {ctx['block_reason']}")
            return None
        score += ctx["macro_score"]   # add to candidate scoring
    """

    def __init__(self):
        self._cache: dict = {}
        self._coin_cache: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._last_refresh: float = 0.0
        # Background refresh thread
        self._thread = threading.Thread(target=self._bg_refresh, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------ #
    #  PUBLIC INTERFACE                                                    #
    # ------------------------------------------------------------------ #
    def get_entry_context(self, kraken_pair: str = "") -> dict:
        """
        Return full macro context for a given pair.
        kraken_pair: e.g. "SOLUSDT", "ETHUSD", "XBTUSD" or just "SOL"
        """
        with self._lock:
            cache = dict(self._cache)

        if not cache:
            # First call before any data — trigger sync fetch
            self._refresh()
            with self._lock:
                cache = dict(self._cache)

        # Extract coin-specific data
        base = self._extract_base(kraken_pair)
        cg_id = _COINGECKO_IDS.get(base, "")
        coin_data = self._coin_cache.get(cg_id, {})

        fg        = cache.get("fear_greed", 50)
        fg_label  = cache.get("fear_label", "Neutral")
        btc_24h   = cache.get("btc_24h", 0.0)
        eth_24h   = cache.get("eth_24h", 0.0)
        xrp_24h   = cache.get("xrp_24h", 0.0)
        market_24h= cache.get("market_24h", 0.0)
        btc_dom   = cache.get("btc_dominance", 55.0)
        trending  = cache.get("trending_symbols", [])
        vol_pat   = cache.get("btc_vol_pattern", "flat")
        coin_24h  = coin_data.get("price_change_24h", btc_24h * 0.7)
        coin_vol  = coin_data.get("volume_24h", 0.0)
        is_trend  = base in trending or cg_id in trending

        # ── Composite macro_score (-2 → +2) ──────────────────────────────
        score = 0.0

        # Fear & Greed contribution  (-1 → +1)
        if fg >= 60:     score += 1.0   # Greed — momentum favours entry
        elif fg >= 45:   score += 0.5
        elif fg >= 30:   score += 0.0
        elif fg >= 20:   score -= 0.5
        else:            score -= 1.0   # Extreme Fear

        # Market trend contribution  (-0.5 → +0.5)
        if market_24h >= 2:   score += 0.5
        elif market_24h >= 0: score += 0.2
        elif market_24h >= -3:score -= 0.2
        else:                  score -= 0.5

        # BTC dominance — high dom = altcoins underperforming (-0.25 → +0.25)
        if btc_dom < 48:   score += 0.25   # altcoin season
        elif btc_dom > 58: score -= 0.25   # BTC-only market

        # Trending bonus (+0.25)
        if is_trend:
            score += 0.25

        # BTC volume pattern (+0.0 / +0.25)
        if vol_pat == "rising":
            score += 0.25

        # Coin-specific trend vs BTC
        if coin_24h > btc_24h + 1.0:   score += 0.25   # outperforming
        elif coin_24h < btc_24h - 2.0: score -= 0.25   # lagging badly

        macro_score = round(max(-2.0, min(2.0, score)), 3)

        # ── Hard-block logic ─────────────────────────────────────────────
        entry_ok    = True
        block_reason= ""

        if fg <= EXTREME_FEAR_BLOCK:
            entry_ok     = False
            block_reason = f"Extreme Fear ({fg}) — macro says WAIT"
        elif market_24h <= MARKET_DROP_BLOCK:
            entry_ok     = False
            block_reason = f"Market crash ({market_24h:+.1f}% 24h) — macro says WAIT"
        elif btc_24h <= BTC_CRASH_BLOCK:
            entry_ok     = False
            block_reason = f"BTC crash ({btc_24h:+.1f}% 24h) — macro says WAIT"

        return {
            "fear_greed":      fg,
            "fear_label":      fg_label,
            "btc_24h":         btc_24h,
            "eth_24h":         eth_24h,
            "xrp_24h":         xrp_24h,
            "market_24h":      market_24h,
            "btc_dominance":   btc_dom,
            "coin_24h":        coin_24h,
            "coin_vol_usd":    coin_vol,
            "is_trending":     is_trend,
            "btc_vol_pattern": vol_pat,
            "macro_score":     macro_score,
            "entry_ok":        entry_ok,
            "block_reason":    block_reason,
            "signal_age_s":    round(time.time() - self._last_refresh, 0),
        }

    def summary_line(self, kraken_pair: str = "") -> str:
        """One-line human-readable summary for logger output."""
        ctx = self.get_entry_context(kraken_pair)
        trend_tag = "TRENDING" if ctx["is_trending"] else ""
        block_tag = f" | BLOCKED: {ctx['block_reason']}" if not ctx["entry_ok"] else ""
        return (
            f"MACRO | F&G={ctx['fear_greed']} {ctx['fear_label']} | "
            f"Mkt={ctx['market_24h']:+.1f}% | BTC={ctx['btc_24h']:+.1f}% | "
            f"BTC.dom={ctx['btc_dominance']:.1f}% | "
            f"Coin={ctx['coin_24h']:+.1f}% | "
            f"score={ctx['macro_score']:+.2f} | vol={ctx['btc_vol_pattern']} "
            f"{trend_tag}{block_tag}"
        )

    # ------------------------------------------------------------------ #
    #  INTERNAL FETCH LOGIC                                               #
    # ------------------------------------------------------------------ #
    def _bg_refresh(self):
        """Background thread — refreshes every MACRO_REFRESH_S seconds."""
        while True:
            try:
                if time.time() - self._last_refresh >= MACRO_REFRESH_S:
                    self._refresh()
            except Exception:
                pass
            time.sleep(60)

    def _refresh(self):
        """Fetch all signals and update cache."""
        new_cache = {}
        try:
            # 1. Fear & Greed
            fg_data = self._fetch("https://api.alternative.me/fng/?limit=1")
            if fg_data:
                item = fg_data["data"][0]
                new_cache["fear_greed"]  = int(item["value"])
                new_cache["fear_label"]  = item["value_classification"]

            # 2. CoinGecko global
            global_data = self._fetch("https://api.coingecko.com/api/v3/global")
            if global_data:
                d = global_data["data"]
                new_cache["market_24h"]    = d.get("market_cap_change_percentage_24h_usd", 0.0)
                new_cache["btc_dominance"] = d.get("market_cap_percentage", {}).get("btc", 55.0)

            # 3. Core coins — BTC, ETH, XRP + all tracked coins
            all_ids = "bitcoin,ethereum,ripple," + ",".join(set(_COINGECKO_IDS.values()))
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency=usd&ids={all_ids}"
                "&order=market_cap_desc&per_page=60&page=1"
                "&sparkline=false&price_change_percentage=24h"
            )
            coins = self._fetch(url)
            if coins:
                coin_map = {c["id"]: c for c in coins}
                btc = coin_map.get("bitcoin", {})
                eth = coin_map.get("ethereum", {})
                xrp = coin_map.get("ripple", {})
                new_cache["btc_24h"] = btc.get("price_change_percentage_24h", 0.0)
                new_cache["eth_24h"] = eth.get("price_change_percentage_24h", 0.0)
                new_cache["xrp_24h"] = xrp.get("price_change_percentage_24h", 0.0)
                # Per-coin cache
                with self._lock:
                    for cid, cdata in coin_map.items():
                        self._coin_cache[cid] = {
                            "price_change_24h": cdata.get("price_change_percentage_24h", 0.0),
                            "volume_24h":       cdata.get("total_volume", 0.0),
                            "current_price":    cdata.get("current_price", 0.0),
                        }

            # 4. Trending coins
            trending = self._fetch("https://api.coingecko.com/api/v3/search/trending")
            if trending:
                syms = [c["item"]["symbol"].upper() for c in trending.get("coins", [])[:10]]
                ids  = [c["item"]["id"] for c in trending.get("coins", [])[:10]]
                new_cache["trending_symbols"] = syms + ids

            # 5. BTC 6h volume pattern from Kraken
            ohlc = self._fetch("https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60")
            if ohlc and not ohlc.get("error"):
                candles = list(ohlc["result"].values())[0][-7:]  # last 7h
                vols = [float(c[6]) for c in candles]
                if len(vols) >= 4:
                    recent = sum(vols[-3:])
                    prior  = sum(vols[-6:-3])
                    if prior > 0:
                        ratio = recent / prior
                        if ratio >= 1.25:
                            new_cache["btc_vol_pattern"] = "rising"
                        elif ratio <= 0.75:
                            new_cache["btc_vol_pattern"] = "falling"
                        else:
                            new_cache["btc_vol_pattern"] = "flat"

            if new_cache:
                with self._lock:
                    self._cache.update(new_cache)
                self._last_refresh = time.time()
                logger.info(
                    f"MACRO REFRESH | F&G={new_cache.get('fear_greed','?')} "
                    f"{new_cache.get('fear_label','?')} | "
                    f"BTC={new_cache.get('btc_24h',0):+.1f}% | "
                    f"Mkt={new_cache.get('market_24h',0):+.1f}% | "
                    f"BTC.dom={new_cache.get('btc_dominance',0):.1f}% | "
                    f"vol={new_cache.get('btc_vol_pattern','?')}"
                )

        except Exception as e:
            logger.warning(f"Macro refresh error: {e}")

    def _fetch(self, url: str, timeout: int = 8):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "AureonMacroIntel/1.0")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.debug(f"Macro fetch failed: {url[:60]}... {e}")
            return None

    @staticmethod
    def _extract_base(pair: str) -> str:
        """Extract base coin symbol from various pair formats."""
        pair = pair.upper()
        # Strip common quote suffixes
        for suffix in ("USD", "USDT", "USDC", "EUR", "BTC", "ETH"):
            if pair.endswith(suffix) and len(pair) > len(suffix):
                base = pair[:-len(suffix)]
                # Kraken internal prefix X for crypto
                if base.startswith("X") and len(base) > 1 and base[1:] in _COINGECKO_IDS:
                    return base[1:]
                return base
        return pair
