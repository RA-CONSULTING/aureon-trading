"""
aureon/integrations/world_data/world_data_ingester.py

WorldDataIngester — pulls live external data into the Aureon vault from
FREE APIs that require NO keys:

  - Wikipedia REST API   (wiki articles for any topic)
  - Yahoo Finance        (live prices, market data)
  - CoinGecko            (free crypto market data)
  - Hacker News          (tech / world headlines)
  - Reddit JSON          (worldnews / geopolitics / locality subreddits)
  - GDELT                (geopolitical event database)

Architecture:
  fetch_*() methods → list of WorldDataItem
  ingest_* methods → publish to ThoughtBus + write to vault as cards
  search(query) → universal cross-source search

Each item becomes a vault card with a category (so the interpreter
classifies it correctly) and ends up in the knowledge dataset via the
normal stash pocket / interpretation flow.

Pure stdlib: urllib + json. No aiohttp, no requests. No API keys.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.integrations.world_data")


# ─────────────────────────────────────────────────────────────────────────────
# Data structure
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class WorldDataItem:
    """One item pulled from any external API."""
    source: str            # "wikipedia" / "yahoo_finance" / "coingecko" / ...
    topic: str             # query / symbol / subreddit / term
    title: str
    text: str
    url: str = ""
    timestamp: float = field(default_factory=time.time)
    raw: Dict[str, Any] = field(default_factory=dict)
    category: str = "knowledge"   # for the interpreter

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# WorldDataIngester
# ─────────────────────────────────────────────────────────────────────────────


class WorldDataIngester:
    """
    Pulls external knowledge from free no-key APIs.
    Thread-safe singleton.
    """

    USER_AGENT = "Aureon-ICS/1.0 (research; +https://github.com/RA-CONSULTING/aureon-trading)"

    def __init__(
        self,
        vault: Any = None,
        thought_bus: Any = None,
        timeout: float = 8.0,
    ):
        self.vault = vault
        self.thought_bus = thought_bus
        self.timeout = timeout
        self._lock = threading.RLock()
        self._stats = {
            "wikipedia_calls": 0,
            "yahoo_calls": 0,
            "coingecko_calls": 0,
            "hackernews_calls": 0,
            "reddit_calls": 0,
            "gdelt_calls": 0,
            "items_ingested": 0,
            "errors": 0,
        }

    # ─────────────────────────────────────────────────────────────────────
    # HTTP helper
    # ─────────────────────────────────────────────────────────────────────
    def _http_get(self, url: str) -> Optional[Any]:
        """Plain stdlib HTTP GET → parsed JSON. Returns None on any error."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
                return json.loads(data.decode("utf-8"))
        except Exception as exc:
            logger.debug("HTTP GET failed (%s): %s", url, exc)
            with self._lock:
                self._stats["errors"] += 1
            return None

    # ─────────────────────────────────────────────────────────────────────
    # Wikipedia REST API (no key)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_wikipedia(self, topic: str) -> Optional[WorldDataItem]:
        """Fetch the summary card for a Wikipedia topic."""
        with self._lock:
            self._stats["wikipedia_calls"] += 1
        # URL-encode the topic
        safe = urllib.parse.quote(topic.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe}"
        data = self._http_get(url)
        if not data or "extract" not in data:
            return None
        return WorldDataItem(
            source="wikipedia",
            topic=topic,
            title=data.get("title", topic),
            text=data.get("extract", "")[:1500],
            url=data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            raw={"description": data.get("description", "")},
            category="knowledge",
        )

    def search_wikipedia(self, query: str, n: int = 3) -> List[WorldDataItem]:
        """Search Wikipedia for a query, return top n summaries."""
        with self._lock:
            self._stats["wikipedia_calls"] += 1
        safe = urllib.parse.quote(query)
        url = (
            f"https://en.wikipedia.org/w/api.php?action=opensearch"
            f"&search={safe}&limit={n}&namespace=0&format=json"
        )
        data = self._http_get(url)
        if not data or len(data) < 4:
            return []
        titles = data[1]
        items: List[WorldDataItem] = []
        for title in titles[:n]:
            item = self.fetch_wikipedia(title)
            if item:
                items.append(item)
        return items

    # ─────────────────────────────────────────────────────────────────────
    # Yahoo Finance (no key — public chart endpoint)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_yahoo_quote(self, symbol: str) -> Optional[WorldDataItem]:
        """
        Fetch the latest price for a symbol from Yahoo Finance public endpoint.
        Examples: "BTC-USD", "ETH-USD", "AAPL", "^GSPC"
        """
        with self._lock:
            self._stats["yahoo_calls"] += 1
        safe = urllib.parse.quote(symbol)
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{safe}"
            f"?interval=1d&range=5d"
        )
        data = self._http_get(url)
        if not data:
            return None
        try:
            chart = data.get("chart", {}).get("result", [])
            if not chart:
                return None
            result = chart[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice")
            currency = meta.get("currency", "USD")
            prev_close = meta.get("previousClose", price)
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            text = (
                f"{symbol} {currency} {price:.2f} "
                f"({'+' if change_pct >= 0 else ''}{change_pct:.2f}%) "
                f"prev_close={prev_close:.2f}"
            )
            return WorldDataItem(
                source="yahoo_finance",
                topic=symbol,
                title=f"{symbol} {currency}",
                text=text,
                url=f"https://finance.yahoo.com/quote/{safe}",
                raw={"price": price, "prev_close": prev_close, "change_pct": change_pct},
                category="market",
            )
        except Exception as exc:
            logger.debug("Yahoo parse failed: %s", exc)
            return None

    # ─────────────────────────────────────────────────────────────────────
    # CoinGecko (free, no key)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_coingecko(self, coin_id: str = "bitcoin") -> Optional[WorldDataItem]:
        """Fetch market data for a coin from CoinGecko."""
        with self._lock:
            self._stats["coingecko_calls"] += 1
        url = (
            f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            f"?localization=false&tickers=false&market_data=true"
            f"&community_data=false&developer_data=false"
        )
        data = self._http_get(url)
        if not data:
            return None
        try:
            market = data.get("market_data", {})
            price = market.get("current_price", {}).get("usd", 0)
            change_24h = market.get("price_change_percentage_24h", 0)
            mcap = market.get("market_cap", {}).get("usd", 0)
            vol = market.get("total_volume", {}).get("usd", 0)
            text = (
                f"{coin_id} ${price:,.2f} "
                f"({'+' if change_24h >= 0 else ''}{change_24h:.2f}% 24h) "
                f"mcap=${mcap/1e9:.1f}B vol=${vol/1e9:.1f}B"
            )
            return WorldDataItem(
                source="coingecko",
                topic=coin_id,
                title=data.get("name", coin_id),
                text=text,
                url=f"https://www.coingecko.com/en/coins/{coin_id}",
                raw={"price": price, "change_24h": change_24h, "mcap": mcap, "volume": vol},
                category="market",
            )
        except Exception as exc:
            logger.debug("CoinGecko parse failed: %s", exc)
            return None

    # ─────────────────────────────────────────────────────────────────────
    # Hacker News (no key)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_hacker_news(self, n: int = 5) -> List[WorldDataItem]:
        """Fetch top stories from Hacker News."""
        with self._lock:
            self._stats["hackernews_calls"] += 1
        ids = self._http_get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if not ids:
            return []
        items: List[WorldDataItem] = []
        for sid in ids[:n]:
            story = self._http_get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            )
            if not story or "title" not in story:
                continue
            items.append(WorldDataItem(
                source="hacker_news",
                topic="top",
                title=story.get("title", ""),
                text=story.get("title", "") + " — " + str(story.get("score", 0)) + " points",
                url=story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                raw={"score": story.get("score", 0), "by": story.get("by", "")},
                category="knowledge",
            ))
        return items

    # ─────────────────────────────────────────────────────────────────────
    # Reddit JSON (no key)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_reddit(
        self,
        subreddit: str = "worldnews",
        n: int = 5,
        sort: str = "top",
    ) -> List[WorldDataItem]:
        """Fetch top posts from a subreddit (worldnews / geopolitics / etc)."""
        with self._lock:
            self._stats["reddit_calls"] += 1
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={n}&t=day"
        data = self._http_get(url)
        if not data:
            return []
        items: List[WorldDataItem] = []
        try:
            children = data.get("data", {}).get("children", [])
            for c in children[:n]:
                post = c.get("data", {})
                title = post.get("title", "")
                if not title:
                    continue
                # Categorise based on subreddit
                cat = "knowledge"
                sub_lower = subreddit.lower()
                if "news" in sub_lower or "politics" in sub_lower or "geopolitic" in sub_lower:
                    cat = "user_input"  # external world events
                elif "crypto" in sub_lower or "bitcoin" in sub_lower:
                    cat = "market"
                items.append(WorldDataItem(
                    source=f"reddit_r/{subreddit}",
                    topic=subreddit,
                    title=title,
                    text=f"{title} — {post.get('selftext', '')[:300]}",
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    raw={"score": post.get("score", 0), "ups": post.get("ups", 0),
                         "num_comments": post.get("num_comments", 0)},
                    category=cat,
                ))
        except Exception as exc:
            logger.debug("Reddit parse failed: %s", exc)
        return items

    # ─────────────────────────────────────────────────────────────────────
    # GDELT (no key — geopolitical event database)
    # ─────────────────────────────────────────────────────────────────────
    def fetch_gdelt(self, query: str, n: int = 5) -> List[WorldDataItem]:
        """Search GDELT for geopolitical events related to a query."""
        with self._lock:
            self._stats["gdelt_calls"] += 1
        safe = urllib.parse.quote(query)
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc"
            f"?query={safe}&mode=ArtList&maxrecords={n}&format=json"
        )
        data = self._http_get(url)
        if not data:
            return []
        items: List[WorldDataItem] = []
        try:
            articles = data.get("articles", [])
            for art in articles[:n]:
                title = art.get("title", "")
                if not title:
                    continue
                items.append(WorldDataItem(
                    source="gdelt",
                    topic=query,
                    title=title,
                    text=f"{title} — {art.get('domain', '')} ({art.get('language', '')})",
                    url=art.get("url", ""),
                    raw={"domain": art.get("domain", ""), "seendate": art.get("seendate", "")},
                    category="user_input",  # geopolitical world event
                ))
        except Exception as exc:
            logger.debug("GDELT parse failed: %s", exc)
        return items

    # ─────────────────────────────────────────────────────────────────────
    # Universal search — answers a question from multiple sources
    # ─────────────────────────────────────────────────────────────────────
    def answer_question(self, question: str, n_per_source: int = 2) -> List[WorldDataItem]:
        """
        Try to answer a question by searching multiple sources.
        Returns aggregated WorldDataItems.
        """
        results: List[WorldDataItem] = []

        # 1. Wikipedia (most reliable for facts)
        try:
            results.extend(self.search_wikipedia(question, n=n_per_source))
        except Exception:
            pass

        # 2. Reddit r/worldnews if question mentions news/world/politics
        lower = question.lower()
        if any(w in lower for w in ["news", "world", "politic", "election", "war", "crisis"]):
            try:
                results.extend(self.fetch_reddit("worldnews", n=n_per_source))
            except Exception:
                pass

        # 3. GDELT for geopolitical questions
        if any(w in lower for w in ["politic", "geopolit", "country", "war", "diplom", "treaty"]):
            try:
                results.extend(self.fetch_gdelt(question, n=n_per_source))
            except Exception:
                pass

        # 4. Yahoo Finance / CoinGecko for market questions
        if any(w in lower for w in ["price", "market", "stock", "trade", "btc", "eth", "bitcoin", "ethereum"]):
            symbols = []
            if "btc" in lower or "bitcoin" in lower:
                symbols.append("BTC-USD")
            if "eth" in lower or "ethereum" in lower:
                symbols.append("ETH-USD")
            for sym in symbols[:n_per_source]:
                item = self.fetch_yahoo_quote(sym)
                if item:
                    results.append(item)

        return results

    # ─────────────────────────────────────────────────────────────────────
    # Vault ingestion + ThoughtBus publishing
    # ─────────────────────────────────────────────────────────────────────
    def ingest_to_vault(self, items: List[WorldDataItem]) -> int:
        """Write items as cards into the vault and publish to ThoughtBus."""
        if not items:
            return 0
        ingested = 0
        for item in items:
            try:
                if self.vault is not None:
                    self.vault.ingest(
                        topic=f"world_data.{item.source}",
                        payload={
                            "title": item.title,
                            "text": item.text,
                            "url": item.url,
                            "topic": item.topic,
                            "category": item.category,
                            "raw": item.raw,
                        },
                        category=item.category,
                    )
                if self.thought_bus is not None:
                    try:
                        self.thought_bus.publish(
                            f"world_data.{item.source}",
                            {
                                "title": item.title,
                                "text": item.text[:200],
                                "url": item.url,
                                "topic": item.topic,
                            },
                            source="world_data_ingester",
                        )
                    except Exception:
                        pass
                ingested += 1
            except Exception as exc:
                logger.debug("ingest failed: %s", exc)
        with self._lock:
            self._stats["items_ingested"] += ingested
        return ingested

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._stats)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[WorldDataIngester] = None
_singleton_lock = threading.Lock()


def get_world_data_ingester(**kwargs) -> WorldDataIngester:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = WorldDataIngester(**kwargs)
        return _singleton


def reset_world_data_ingester() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
