#!/usr/bin/env python3
"""
Ingest Existing Feeds into Global History DB
=============================================
Wires the existing Aureon feed modules (CoinGecko, Global Financial Feed,
News Sentiment, Glassnode On-Chain, Coinbase Historical, Macro Intelligence)
into the unified SQLite global history database.

Each feed is independently try/except-wrapped so one failure never blocks
the rest.

Usage:
    python ingest_existing_feeds.py
    python ingest_existing_feeds.py --feeds coingecko,coinbase
    python ingest_existing_feeds.py --feeds all --coinbase-pairs BTC-USD,ETH-USD
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root sys.path setup (same pattern as sync_global_history_db.py)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (
    _REPO_ROOT,
    _REPO_ROOT / "aureon" / "core",
    _REPO_ROOT / "aureon" / "exchanges",
    _REPO_ROOT / "aureon" / "data_feeds",
    _REPO_ROOT / "aureon" / "intelligence",
    _REPO_ROOT / "aureon" / "monitors",
):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

try:
    from aureon_baton_link import link_system as _baton_link
    _baton_link(__name__)
except Exception:
    pass

import argparse
import json
import os
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# DB module (always required)
# ---------------------------------------------------------------------------
import aureon_global_history_db as db

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_COINGECKO_COINS = [
    "bitcoin", "ethereum", "ripple", "solana", "cardano", "dogecoin",
    "polkadot", "avalanche-2", "chainlink", "matic-network", "litecoin",
    "uniswap", "cosmos", "near", "stellar",
]

DEFAULT_COINBASE_PAIRS = [
    "BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "ADA-USD", "DOGE-USD",
]

DEFAULT_NEWS_KEYWORDS = [
    "market", "stocks", "crypto", "forex", "economy", "inflation",
    "fed", "geopolitical",
]

ALL_FEEDS = ["coingecko", "macro", "news", "glassnode", "coinbase", "macro_intel"]

# Macro snapshot fields we want to persist as individual sentiment rows.
MACRO_SNAPSHOT_FIELDS = [
    "crypto_fear_greed", "crypto_fg_classification",
    "vix", "vix_change",
    "dxy", "dxy_change",
    "us_10y_yield", "us_2y_yield", "yield_curve_inversion",
    "spx", "spx_change",
    "gold", "gold_change",
    "oil", "oil_change",
    "total_crypto_mcap", "btc_dominance",
    "eur_usd", "gbp_usd", "usd_jpy",
    "risk_on_off", "market_regime",
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _ts_id(source: str, ts_ms: int, suffix: str = "") -> str:
    """Generate a deterministic unique ID for deduplication."""
    base = f"{source}:{ts_ms}"
    return f"{base}:{suffix}" if suffix else base


# ===================================================================
# 1. CoinGecko
# ===================================================================
def ingest_coingecko(conn, coins: list[str]) -> dict:
    """Fetch current CoinGecko prices and store as point-in-time market bars."""
    try:
        from coingecko_price_feeder import fetch_coingecko_prices
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    print("\n[coingecko] Fetching prices ...")
    prices = fetch_coingecko_prices(coins)
    if not prices:
        return {"status": "ok", "inserted": 0, "note": "no data returned"}

    now = _now_ms()
    inserted = 0
    for coin_id, data in prices.items():
        usd_price = data.get("usd")
        if usd_price is None:
            continue
        bar = {
            "provider": "coingecko",
            "venue": "coingecko",
            "symbol_id": f"coingecko:{coin_id}",
            "symbol": coin_id,
            "period_id": "snapshot",
            "time_start_ms": now,
            "time_end_ms": now,
            "open": usd_price,
            "high": usd_price,
            "low": usd_price,
            "close": usd_price,
            "volume": data.get("usd_24h_vol"),
            "trades_count": None,
            "ingested_at_ms": now,
            "raw_json": json.dumps(data),
        }
        if db.insert_market_bar(conn, bar):
            inserted += 1
    conn.commit()
    db.set_watermark_ms(conn, "coingecko", now)
    conn.commit()
    print(f"[coingecko] Inserted {inserted} market bars for {len(prices)} coins.")
    return {"status": "ok", "inserted": inserted, "coins": len(prices)}


# ===================================================================
# 2. Global Financial Feed (macro snapshot)
# ===================================================================
def ingest_macro(conn) -> dict:
    """Take a GlobalFinancialFeed snapshot and store each indicator."""
    try:
        from global_financial_feed import GlobalFinancialFeed
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    print("\n[macro] Fetching global financial snapshot ...")
    feed = GlobalFinancialFeed()
    snap = feed.get_snapshot()
    snap_dict = snap.to_dict() if hasattr(snap, "to_dict") else {}

    now = _now_ms()
    inserted = 0
    for field_name in MACRO_SNAPSHOT_FIELDS:
        raw_value = getattr(snap, field_name, None)
        if raw_value is None:
            raw_value = snap_dict.get(field_name)
        if raw_value is None:
            continue

        # Coerce booleans / strings to a numeric value where possible
        numeric_value = None
        label = None
        if isinstance(raw_value, bool):
            numeric_value = 1.0 if raw_value else 0.0
            label = str(raw_value)
        elif isinstance(raw_value, (int, float)):
            numeric_value = float(raw_value)
        elif isinstance(raw_value, str):
            label = raw_value

        row = {
            "source": "global_financial_feed",
            "sentiment_id": _ts_id("gff", now, field_name),
            "sentiment_type": field_name,
            "symbol": None,
            "value": numeric_value,
            "label": label,
            "ts_ms": now,
            "ingested_at_ms": now,
            "raw_json": json.dumps({"field": field_name, "raw": raw_value}),
        }
        if db.insert_sentiment(conn, row):
            inserted += 1
    conn.commit()
    db.set_watermark_ms(conn, "global_financial_feed", now)
    conn.commit()
    print(f"[macro] Inserted {inserted} sentiment rows from macro snapshot.")
    return {"status": "ok", "inserted": inserted}


# ===================================================================
# 3. News Sentiment
# ===================================================================
def ingest_news(conn, keywords: list[str]) -> dict:
    """Fetch recent news articles, store each + aggregate as sentiment rows."""
    try:
        from aureon_news_feed import NewsFeed, NewsFeedConfig
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    api_key = os.environ.get("WORLD_NEWS_API_KEY", "")
    if not api_key:
        return {"status": "skipped", "reason": "WORLD_NEWS_API_KEY not set"}

    print("\n[news] Fetching recent articles ...")
    import asyncio

    config = NewsFeedConfig(api_key=api_key)
    feed = NewsFeed(config)
    now = _now_ms()
    inserted_articles = 0
    inserted_agg = 0

    async def _fetch_all():
        all_articles = []
        for kw in keywords:
            try:
                arts = await feed.search_news(text=kw, number=10)
                all_articles.extend(arts)
            except Exception as exc:
                print(f"  [news] search_news('{kw}') failed: {exc}")
        return all_articles

    articles = asyncio.run(_fetch_all())

    # Deduplicate by article ID
    seen_ids: set = set()
    unique_articles = []
    for art in articles:
        if art.id not in seen_ids:
            seen_ids.add(art.id)
            unique_articles.append(art)

    # Store each article as a sentiment row
    for art in unique_articles:
        pub_ms = now
        try:
            dt = datetime.strptime(art.publish_date, "%Y-%m-%d %H:%M:%S")
            pub_ms = int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
        except Exception:
            pass

        row = {
            "source": "news_feed",
            "sentiment_id": _ts_id("news_article", pub_ms, str(art.id)),
            "sentiment_type": "news_article",
            "symbol": art.category,
            "value": art.sentiment,
            "label": art.sentiment_label,
            "ts_ms": pub_ms,
            "ingested_at_ms": now,
            "raw_json": json.dumps({
                "id": art.id,
                "title": art.title,
                "url": art.url,
                "summary": art.summary[:500] if art.summary else None,
                "category": art.category,
                "sentiment": art.sentiment,
            }),
        }
        if db.insert_sentiment(conn, row):
            inserted_articles += 1

    # Store aggregate sentiment
    if unique_articles:
        agg = feed.analyze_sentiment_aggregate(unique_articles)
        signals = feed.extract_market_signals(unique_articles)
        agg_row = {
            "source": "news_feed",
            "sentiment_id": _ts_id("news_agg", now),
            "sentiment_type": "news_aggregate",
            "symbol": None,
            "value": agg.get("average_sentiment"),
            "label": f"bullish_ratio={agg.get('bullish_ratio')},bearish_ratio={agg.get('bearish_ratio')}",
            "ts_ms": now,
            "ingested_at_ms": now,
            "raw_json": json.dumps({"aggregate": agg, "signals": signals}),
        }
        if db.insert_sentiment(conn, agg_row):
            inserted_agg += 1

    conn.commit()
    db.set_watermark_ms(conn, "news_feed", now)
    conn.commit()
    print(f"[news] Inserted {inserted_articles} article rows + {inserted_agg} aggregate rows "
          f"({len(unique_articles)} unique articles).")
    return {"status": "ok", "articles": inserted_articles, "aggregates": inserted_agg}


# ===================================================================
# 4. Glassnode On-Chain
# ===================================================================
def ingest_glassnode(conn, hours_back: int) -> dict:
    """Fetch whale movements and exchange flows, store as onchain_metric rows."""
    try:
        from glassnode_client import GlassnodeClient
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    api_key = os.environ.get("GLASSNODE_API_KEY", "")
    if not api_key:
        return {"status": "skipped", "reason": "GLASSNODE_API_KEY not set"}

    print(f"\n[glassnode] Fetching on-chain data (last {hours_back}h) ...")
    client = GlassnodeClient()
    now = _now_ms()
    inserted = 0

    # -- Whale movements --
    try:
        whales = client.detect_whale_movements(min_usd_value=100_000, hours_back=hours_back)
        for wm in whales:
            ts = int(wm.timestamp * 1000) if wm.timestamp < 1e12 else int(wm.timestamp)
            row = {
                "provider": "glassnode",
                "metric_id": _ts_id("whale", ts, wm.asset),
                "metric_name": "whale_movement",
                "asset": wm.asset,
                "value": wm.usd_value,
                "ts_ms": ts,
                "ingested_at_ms": now,
                "raw_json": json.dumps({
                    "amount": wm.amount,
                    "usd_value": wm.usd_value,
                    "asset": wm.asset,
                }),
            }
            if db.insert_onchain_metric(conn, row):
                inserted += 1
    except Exception as exc:
        print(f"  [glassnode] detect_whale_movements failed: {exc}")

    # -- Exchange flows --
    try:
        flows = client.get_exchange_flows(hours_back=hours_back)
        for ef in flows:
            ts = int(ef.timestamp * 1000) if ef.timestamp < 1e12 else int(ef.timestamp)
            row = {
                "provider": "glassnode",
                "metric_id": _ts_id("exflow", ts, ef.asset),
                "metric_name": "exchange_flow",
                "asset": ef.asset,
                "value": ef.net_flow_usd,
                "ts_ms": ts,
                "ingested_at_ms": now,
                "raw_json": json.dumps({
                    "inflow_usd": ef.inflow_usd,
                    "outflow_usd": ef.outflow_usd,
                    "net_flow_usd": ef.net_flow_usd,
                    "asset": ef.asset,
                    "exchange": getattr(ef, "exchange", None),
                }),
            }
            if db.insert_onchain_metric(conn, row):
                inserted += 1
    except Exception as exc:
        print(f"  [glassnode] get_exchange_flows failed: {exc}")

    # -- Intelligence summary (store as single snapshot metric) --
    try:
        summary = client.get_whale_intelligence_summary()
        row = {
            "provider": "glassnode",
            "metric_id": _ts_id("intel_summary", now),
            "metric_name": "whale_intelligence_summary",
            "asset": "ALL",
            "value": summary.get("large_tx_volume_24h"),
            "ts_ms": now,
            "ingested_at_ms": now,
            "raw_json": json.dumps(summary),
        }
        if db.insert_onchain_metric(conn, row):
            inserted += 1
    except Exception as exc:
        print(f"  [glassnode] get_whale_intelligence_summary failed: {exc}")

    conn.commit()
    db.set_watermark_ms(conn, "glassnode", now)
    conn.commit()
    print(f"[glassnode] Inserted {inserted} onchain_metric rows.")
    return {"status": "ok", "inserted": inserted}


# ===================================================================
# 5. Coinbase Historical
# ===================================================================
def ingest_coinbase(conn, pairs: list[str]) -> dict:
    """Bulk-load 1 year of OHLCV candles from Coinbase public API."""
    try:
        from coinbase_historical_feed import CoinbaseHistoricalFeed
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    print(f"\n[coinbase] Fetching historical candles for {pairs} ...")
    feed = CoinbaseHistoricalFeed()
    now = _now_ms()
    inserted = 0
    total_candles = 0

    try:
        all_data = feed.fetch_year_of_data(pairs)
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}

    for pair, candles in all_data.items():
        pair_inserted = 0
        for c in candles:
            ts_ms = int(c.timestamp.timestamp() * 1000) if hasattr(c.timestamp, "timestamp") else int(c.timestamp)
            bar = {
                "provider": "coinbase",
                "venue": "coinbase",
                "symbol_id": f"coinbase:{pair}",
                "symbol": pair,
                "period_id": "1h",
                "time_start_ms": ts_ms,
                "time_end_ms": ts_ms + 3_600_000,  # 1 hour
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "trades_count": None,
                "ingested_at_ms": now,
                "raw_json": None,
            }
            if db.insert_market_bar(conn, bar):
                pair_inserted += 1
        inserted += pair_inserted
        total_candles += len(candles)
        print(f"  [coinbase] {pair}: {pair_inserted} new / {len(candles)} total candles")
        conn.commit()

    db.set_watermark_ms(conn, "coinbase_historical", now)
    conn.commit()
    print(f"[coinbase] Inserted {inserted} market bars ({total_candles} candles processed).")
    return {"status": "ok", "inserted": inserted, "total_candles": total_candles}


# ===================================================================
# 6. Macro Intelligence
# ===================================================================
def ingest_macro_intel(conn) -> dict:
    """Store MacroIntelligence entry context as sentiment rows."""
    try:
        from macro_intelligence import MacroIntelligence
    except ImportError as exc:
        return {"status": "skipped", "reason": f"import failed: {exc}"}

    print("\n[macro_intel] Fetching macro intelligence context ...")
    mi = MacroIntelligence()
    now = _now_ms()
    inserted = 0

    # Query context for a few representative pairs to capture all sub-components
    probe_pairs = ["XBTUSD", "ETHUSD", "SOLUSD"]
    for pair in probe_pairs:
        try:
            ctx = mi.get_entry_context(pair)
        except Exception as exc:
            print(f"  [macro_intel] get_entry_context('{pair}') failed: {exc}")
            continue

        fields_to_store = [
            "fear_greed", "fear_label", "btc_24h", "eth_24h", "market_24h",
            "btc_dominance", "macro_score", "btc_vol_pattern", "is_trending",
        ]
        for field_name in fields_to_store:
            raw = ctx.get(field_name)
            if raw is None:
                continue
            numeric_value = None
            label = None
            if isinstance(raw, bool):
                numeric_value = 1.0 if raw else 0.0
                label = str(raw)
            elif isinstance(raw, (int, float)):
                numeric_value = float(raw)
            elif isinstance(raw, str):
                label = raw

            row = {
                "source": "macro_intelligence",
                "sentiment_id": _ts_id("macro_intel", now, f"{pair}:{field_name}"),
                "sentiment_type": field_name,
                "symbol": pair,
                "value": numeric_value,
                "label": label,
                "ts_ms": now,
                "ingested_at_ms": now,
                "raw_json": json.dumps({"pair": pair, "field": field_name, "raw": raw}),
            }
            if db.insert_sentiment(conn, row):
                inserted += 1

    conn.commit()
    db.set_watermark_ms(conn, "macro_intelligence", now)
    conn.commit()
    print(f"[macro_intel] Inserted {inserted} sentiment rows from macro intelligence.")
    return {"status": "ok", "inserted": inserted}


# ===================================================================
# CLI + orchestration
# ===================================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest existing Aureon feed modules into the global history SQLite DB.",
    )
    p.add_argument("--db", default=None, help="SQLite path override")
    p.add_argument(
        "--feeds", default="all",
        help="CSV of feeds to run: coingecko,macro,news,glassnode,coinbase,macro_intel,all  (default: all)",
    )
    p.add_argument(
        "--coinbase-pairs", default=",".join(DEFAULT_COINBASE_PAIRS),
        help="CSV of Coinbase pairs (default: %(default)s)",
    )
    p.add_argument(
        "--coingecko-coins", default=",".join(DEFAULT_COINGECKO_COINS),
        help="CSV of CoinGecko coin IDs",
    )
    p.add_argument(
        "--news-keywords", default=",".join(DEFAULT_NEWS_KEYWORDS),
        help="CSV of news search keywords (default: %(default)s)",
    )
    p.add_argument(
        "--hours-back", type=int, default=24,
        help="Hours of history for live feeds like Glassnode (default: 24)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    feeds_requested = [f.strip().lower() for f in args.feeds.split(",")]
    if "all" in feeds_requested:
        feeds_requested = list(ALL_FEEDS)

    coins = [c.strip() for c in args.coingecko_coins.split(",") if c.strip()]
    pairs = [p.strip() for p in args.coinbase_pairs.split(",") if p.strip()]
    keywords = [k.strip() for k in args.news_keywords.split(",") if k.strip()]

    print("=" * 70)
    print("  Aureon Feed Ingestion -> Global History DB")
    print("=" * 70)
    print(f"  Feeds     : {', '.join(feeds_requested)}")
    print(f"  DB        : {args.db or '(default)'}")
    print(f"  Hours back: {args.hours_back}")
    print("=" * 70)

    conn = db.connect(args.db)
    results: dict[str, dict] = {}
    t0 = time.time()

    # Dispatch table
    dispatch = {
        "coingecko":  lambda: ingest_coingecko(conn, coins),
        "macro":      lambda: ingest_macro(conn),
        "news":       lambda: ingest_news(conn, keywords),
        "glassnode":  lambda: ingest_glassnode(conn, args.hours_back),
        "coinbase":   lambda: ingest_coinbase(conn, pairs),
        "macro_intel": lambda: ingest_macro_intel(conn),
    }

    for feed_name in feeds_requested:
        if feed_name not in dispatch:
            print(f"\n[{feed_name}] Unknown feed, skipping.")
            results[feed_name] = {"status": "skipped", "reason": "unknown feed name"}
            continue
        try:
            results[feed_name] = dispatch[feed_name]()
        except Exception as exc:
            print(f"\n[{feed_name}] FAILED: {exc}")
            results[feed_name] = {"status": "error", "reason": str(exc)}

    conn.close()
    elapsed = time.time() - t0

    # Summary
    print("\n" + "=" * 70)
    print("  INGESTION SUMMARY")
    print("=" * 70)
    for name, res in results.items():
        status = res.get("status", "?")
        detail = ""
        if status == "ok":
            parts = []
            for k, v in res.items():
                if k != "status":
                    parts.append(f"{k}={v}")
            detail = ", ".join(parts)
        elif status in ("skipped", "error"):
            detail = res.get("reason", "")
        print(f"  {name:15s}  {status:8s}  {detail}")
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
