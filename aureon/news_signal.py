"""
News & Geopolitical Signal Layer
=================================
Fetches headlines from free RSS feeds (no API key required) and extracts
per-category sentiment and geopolitical risk level.

Categories produced:  crypto / forex / index / commodity / stock / macro
Output: NewsSignalResult with sentiment[-1..+1] per category + risk level

RSS Sources used (all public, no auth):
  - Reuters Business News
  - Yahoo Finance Top Stories
  - CoinDesk (crypto)
  - Investing.com Forex
  - MarketWatch

Geopolitical keywords mapped to risk regime and category impact.
Refreshes every REFRESH_INTERVAL seconds; never blocks on network failure.
"""

import time
import threading
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re

# ─────────────────────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────────────────────
REFRESH_INTERVAL = 600   # seconds between RSS fetches
FETCH_TIMEOUT    = 8     # seconds per RSS request
MAX_HEADLINES    = 40    # max headlines to analyse per cycle

# ─────────────────────────────────────────────────────────────────────────────
#  RSS feed list  (title, url, primary_category_hint)
# ─────────────────────────────────────────────────────────────────────────────
RSS_FEEDS: List[Tuple[str, str, str]] = [
    ('Reuters Business',   'https://feeds.reuters.com/reuters/businessNews',       'macro'),
    ('Yahoo Finance',      'https://finance.yahoo.com/rss/topstories',             'macro'),
    ('CoinDesk',           'https://www.coindesk.com/arc/outboundfeeds/rss/',       'crypto'),
    ('MarketWatch',        'https://feeds.marketwatch.com/marketwatch/topstories/', 'macro'),
    ('Investing Forex',    'https://www.investing.com/rss/news_25.rss',             'forex'),
]

# ─────────────────────────────────────────────────────────────────────────────
#  Keyword → (sentiment_direction, strength, [affected_categories])
#  direction: +1 = bullish/risk-on, -1 = bearish/risk-off
# ─────────────────────────────────────────────────────────────────────────────
KEYWORD_MAP: List[Tuple[str, int, float, List[str]]] = [
    # ── Geopolitical risk-off ─────────────────────────────────────────────
    ('war',           -1, 0.9, ['commodity', 'index', 'crypto']),
    ('nuclear',       -1, 1.0, ['commodity', 'index', 'crypto', 'forex']),
    ('missile',       -1, 0.8, ['commodity', 'index']),
    ('attack',        -1, 0.7, ['commodity', 'index']),
    ('sanctions',     -1, 0.8, ['forex', 'commodity', 'index']),
    ('invasion',      -1, 0.9, ['commodity', 'index', 'forex']),
    ('conflict',      -1, 0.6, ['commodity', 'index']),
    ('tariff',        -1, 0.6, ['index', 'stock', 'forex']),
    ('trade war',     -1, 0.8, ['index', 'stock', 'forex']),
    ('embargo',       -1, 0.7, ['commodity', 'forex']),
    ('default',       -1, 0.7, ['index', 'forex', 'crypto']),
    ('recession',     -1, 0.8, ['index', 'stock', 'crypto']),
    ('depression',    -1, 0.9, ['index', 'stock', 'crypto']),
    ('crash',         -1, 0.9, ['index', 'stock', 'crypto']),
    ('collapse',      -1, 0.9, ['index', 'stock', 'crypto']),
    ('crisis',        -1, 0.7, ['index', 'stock', 'forex', 'crypto']),
    ('bank run',      -1, 0.9, ['index', 'forex', 'crypto']),
    ('bankruptcy',    -1, 0.7, ['stock', 'index']),
    ('layoffs',       -1, 0.4, ['stock', 'index']),
    ('rate hike',     -1, 0.6, ['index', 'stock', 'crypto', 'forex']),
    ('interest rate rise', -1, 0.6, ['index', 'stock', 'crypto']),
    ('inflation',     -1, 0.5, ['index', 'forex', 'commodity']),
    ('stagflation',   -1, 0.8, ['index', 'stock', 'crypto']),
    ('ban crypto',    -1, 0.9, ['crypto']),
    ('crypto ban',    -1, 0.9, ['crypto']),
    ('sec charges',   -1, 0.7, ['crypto']),
    ('sec lawsuit',   -1, 0.6, ['crypto']),
    ('hack',          -1, 0.6, ['crypto']),
    ('exploit',       -1, 0.5, ['crypto']),
    ('drought',       -1, 0.4, ['commodity']),
    ('supply cut',    -1, 0.6, ['commodity']),
    ('opec cut',      -1, 0.5, ['commodity']),   # oil down is risk-off for stocks
    # ── Risk-on / bullish ────────────────────────────────────────────────
    ('rate cut',      +1, 0.8, ['index', 'stock', 'crypto', 'forex']),
    ('fed cut',       +1, 0.8, ['index', 'stock', 'crypto']),
    ('pivot',         +1, 0.7, ['index', 'stock', 'crypto']),
    ('stimulus',      +1, 0.8, ['index', 'stock', 'crypto']),
    ('bailout',       +1, 0.5, ['index', 'stock']),
    ('recovery',      +1, 0.6, ['index', 'stock', 'crypto']),
    ('gdp growth',    +1, 0.6, ['index', 'stock', 'forex']),
    ('beat expectations', +1, 0.5, ['stock', 'index']),
    ('record high',   +1, 0.6, ['index', 'stock', 'crypto']),
    ('rally',         +1, 0.5, ['index', 'stock', 'crypto']),
    ('bull',          +1, 0.5, ['index', 'stock', 'crypto']),
    ('surge',         +1, 0.4, ['index', 'stock', 'crypto']),
    ('etf approved',  +1, 0.9, ['crypto']),
    ('etf approval',  +1, 0.9, ['crypto']),
    ('bitcoin etf',   +1, 0.9, ['crypto']),
    ('institutional',  +1, 0.5, ['crypto', 'index']),
    ('adoption',      +1, 0.5, ['crypto']),
    ('upgrade',       +1, 0.4, ['stock']),
    ('earnings beat', +1, 0.6, ['stock', 'index']),
    ('deal',          +1, 0.4, ['stock']),
    ('merger',        +1, 0.4, ['stock']),
    ('acquisition',   +1, 0.4, ['stock']),
    ('ceasefire',     +1, 0.7, ['index', 'stock', 'forex']),
    ('peace',         +1, 0.5, ['index', 'stock', 'commodity']),
    ('trade deal',    +1, 0.7, ['index', 'stock', 'forex']),
    ('supply increase', +1, 0.4, ['commodity']),
]

# Pre-compile keyword patterns (case-insensitive)
_COMPILED_KEYWORDS: List[Tuple[re.Pattern, int, float, List[str]]] = [
    (re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE), direction, strength, cats)
    for kw, direction, strength, cats in KEYWORD_MAP
]

# Categories we track
ALL_CATEGORIES = ('crypto', 'forex', 'index', 'commodity', 'stock', 'macro')


@dataclass
class NewsSignalResult:
    """Per-category sentiment and overall risk level from current news cycle."""
    # Sentiment per category: -1.0 (bearish) → 0.0 (neutral) → +1.0 (bullish)
    sentiment: Dict[str, float] = field(default_factory=lambda: {c: 0.0 for c in ALL_CATEGORIES})
    # Hit counts per category (how many headlines triggered it)
    hit_counts: Dict[str, int] = field(default_factory=lambda: {c: 0 for c in ALL_CATEGORIES})
    # Overall risk level
    risk_level: str = 'NORMAL'          # NORMAL / ELEVATED / HIGH / EXTREME
    # Geopolitical risk score 0–1
    geo_risk: float = 0.0
    # Top themes found in headlines
    themes: List[str] = field(default_factory=list)
    # Raw headlines used (for logging)
    headline_count: int = 0
    # Timestamp of last fetch
    fetched_at: float = 0.0
    # Whether data is stale
    @property
    def age_minutes(self) -> float:
        return (time.time() - self.fetched_at) / 60.0

    @property
    def is_stale(self) -> bool:
        return self.age_minutes > REFRESH_INTERVAL / 60.0 + 5

    def summary(self) -> str:
        parts = [f"RISK:{self.risk_level}"]
        for cat in ('crypto', 'forex', 'index', 'commodity', 'stock'):
            s = self.sentiment.get(cat, 0.0)
            if abs(s) >= 0.1:
                arrow = '↑' if s > 0 else '↓'
                parts.append(f"{cat.upper()[:5]}={s:+.2f}{arrow}")
        if self.themes:
            parts.append(f"themes=[{', '.join(self.themes[:3])}]")
        return '  |  '.join(parts)


def _fetch_rss(url: str, timeout: int = FETCH_TIMEOUT) -> List[str]:
    """Fetch headlines from an RSS feed URL. Returns list of title strings."""
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; AureonBot/1.0)'})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        titles = []
        # Handle both RSS and Atom formats
        for item in root.iter('item'):
            t = item.findtext('title')
            d = item.findtext('description') or ''
            if t:
                titles.append(f"{t} {d}")
        for entry in root.iter('{http://www.w3.org/2005/Atom}entry'):
            t = entry.findtext('{http://www.w3.org/2005/Atom}title')
            s = entry.findtext('{http://www.w3.org/2005/Atom}summary') or ''
            if t:
                titles.append(f"{t} {s}")
        return titles[:MAX_HEADLINES // len(RSS_FEEDS) + 5]
    except Exception:
        return []


def _analyse_headlines(headlines: List[str]) -> NewsSignalResult:
    """Extract per-category sentiment and geopolitical risk from a list of headlines."""
    # Accumulate weighted sentiment per category
    cat_scores: Dict[str, List[float]] = defaultdict(list)
    themes_found: Dict[str, int] = defaultdict(int)
    geo_risk_scores: List[float] = []

    for headline in headlines:
        for pattern, direction, strength, affected_cats in _COMPILED_KEYWORDS:
            if pattern.search(headline):
                for cat in affected_cats:
                    cat_scores[cat].append(direction * strength)
                themes_found[pattern.pattern] += 1
                # Negative direction with high strength = geopolitical risk
                if direction == -1 and strength >= 0.7:
                    geo_risk_scores.append(strength)

    # Average sentiment per category, clamped to [-1, 1]
    sentiment: Dict[str, float] = {}
    hit_counts: Dict[str, int] = {}
    for cat in ALL_CATEGORIES:
        scores = cat_scores.get(cat, [])
        hit_counts[cat] = len(scores)
        if scores:
            avg = sum(scores) / len(scores)
            sentiment[cat] = max(-1.0, min(1.0, avg))
        else:
            sentiment[cat] = 0.0

    # Macro = average of all categories (overall market sentiment)
    all_scores = [s for scores in cat_scores.values() for s in scores]
    sentiment['macro'] = max(-1.0, min(1.0, sum(all_scores) / len(all_scores))) if all_scores else 0.0

    # Geopolitical risk level
    geo_risk = min(1.0, sum(geo_risk_scores) / max(len(geo_risk_scores), 1)) if geo_risk_scores else 0.0
    if geo_risk >= 0.8:
        risk_level = 'EXTREME'
    elif geo_risk >= 0.6:
        risk_level = 'HIGH'
    elif geo_risk >= 0.3:
        risk_level = 'ELEVATED'
    else:
        risk_level = 'NORMAL'

    # Top themes (sorted by hit count)
    themes = [kw for kw, _ in sorted(themes_found.items(), key=lambda x: -x[1])[:6]]
    # Clean up regex escaping for display
    themes = [t.replace(r'\b', '').replace(r'\ ', ' ').strip() for t in themes]

    return NewsSignalResult(
        sentiment=sentiment,
        hit_counts=hit_counts,
        risk_level=risk_level,
        geo_risk=geo_risk,
        themes=themes,
        headline_count=len(headlines),
        fetched_at=time.time(),
    )


class NewsSignalFetcher:
    """
    Background RSS fetcher + headline analyser.

    Usage:
        fetcher = NewsSignalFetcher()
        result  = fetcher.get()   # always instant (cached)
    """

    def __init__(self) -> None:
        self._result = NewsSignalResult()   # empty / neutral until first fetch
        self._lock   = threading.Lock()
        self._thread = threading.Thread(target=self._loop, daemon=True, name='NewsSignal')
        self._thread.start()

    def get(self) -> NewsSignalResult:
        """Return latest cached result (never blocks)."""
        with self._lock:
            return self._result

    def _fetch_all(self) -> NewsSignalResult:
        headlines: List[str] = []
        for name, url, _hint in RSS_FEEDS:
            fetched = _fetch_rss(url)
            headlines.extend(fetched)
            if len(headlines) >= MAX_HEADLINES:
                break
        return _analyse_headlines(headlines[:MAX_HEADLINES])

    def _loop(self) -> None:
        while True:
            try:
                result = self._fetch_all()
                with self._lock:
                    self._result = result
            except Exception:
                pass
            time.sleep(REFRESH_INTERVAL)


# Module-level singleton (lazy init to avoid import overhead)
_fetcher: Optional[NewsSignalFetcher] = None
_fetcher_lock = threading.Lock()


def get_news_signal() -> NewsSignalResult:
    """
    Get the latest news/geopolitical signal result.
    First call initialises the background fetcher.
    Always returns instantly (uses cached data).
    """
    global _fetcher
    if _fetcher is None:
        with _fetcher_lock:
            if _fetcher is None:
                _fetcher = NewsSignalFetcher()
    return _fetcher.get()
