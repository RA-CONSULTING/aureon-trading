"""
Aureon Knowledge Base Module
============================
Wikipedia API integration for autonomous knowledge gathering.
Provides contextual intelligence for trading decisions.

Uses: https://wikipedia-api.readthedocs.io/
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
from pathlib import Path

try:
    import wikipediaapi
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    wikipediaapi = None

# Import ThoughtBus for publishing knowledge thoughts
try:
    from aureon_thought_bus import ThoughtBus, Thought
except ImportError:
    ThoughtBus = None
    Thought = None


@dataclass
class KnowledgeArticle:
    """Structured knowledge article from Wikipedia."""
    title: str
    summary: str
    url: str
    categories: List[str]
    sections: List[str]
    language: str
    fetch_time: str
    relevance_score: float = 0.0
    
    @property
    def summary_preview(self) -> str:
        """First 200 chars of summary."""
        return self.summary[:200] + "..." if len(self.summary) > 200 else self.summary
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeQuery:
    """A knowledge query with context."""
    query: str
    context: str  # e.g., "trading", "crypto", "economics"
    timestamp: str
    results: List[KnowledgeArticle] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'context': self.context,
            'timestamp': self.timestamp,
            'results': [r.to_dict() for r in self.results]
        }


class KnowledgeCache:
    """LRU cache for Wikipedia articles to avoid repeated API calls."""
    
    def __init__(self, max_size: int = 500, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, Tuple[KnowledgeArticle, float]] = {}
        self.access_order: deque = deque()
    
    def _make_key(self, title: str, language: str = 'en') -> str:
        """Create cache key from title and language."""
        return hashlib.md5(f"{language}:{title.lower()}".encode()).hexdigest()
    
    def get(self, title: str, language: str = 'en') -> Optional[KnowledgeArticle]:
        """Get article from cache if exists and not expired."""
        key = self._make_key(title, language)
        if key in self.cache:
            article, cached_time = self.cache[key]
            # Check TTL
            if time.time() - cached_time < self.ttl_hours * 3600:
                # Move to end of access order
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                return article
            else:
                # Expired, remove
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
        return None
    
    def set(self, title: str, article: KnowledgeArticle, language: str = 'en') -> None:
        """Add article to cache."""
        key = self._make_key(title, language)
        
        # Evict if at capacity
        while len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order.popleft()
            if oldest_key in self.cache:
                del self.cache[oldest_key]
        
        self.cache[key] = (article, time.time())
        self.access_order.append(key)
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_hours': self.ttl_hours
        }


class KnowledgeBase:
    """
    Wikipedia-powered knowledge base for autonomous data gathering.
    Integrates with Aureon's cognitive system via ThoughtBus.
    """
    
    # Trading-relevant topics for proactive knowledge gathering
    TRADING_TOPICS = [
        # Financial concepts
        "Cryptocurrency", "Bitcoin", "Ethereum", "Blockchain",
        "Stock market", "Foreign exchange market", "Commodity market",
        "Technical analysis", "Fundamental analysis", "Algorithmic trading",
        # Economic indicators
        "Inflation", "Interest rate", "Gross domestic product",
        "Federal Reserve", "European Central Bank", "Quantitative easing",
        # Risk management
        "Value at risk", "Sharpe ratio", "Kelly criterion",
        "Volatility (finance)", "Market risk", "Hedge (finance)",
        # Market structure
        "Market maker", "Liquidity (economics)", "Bid–ask spread",
        "Order book", "High-frequency trading", "Dark pool",
    ]
    
    # Entity mappings for trading terms
    ENTITY_ALIASES = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum',
        'xrp': 'Ripple (cryptocurrency)',
        'sol': 'Solana (cryptocurrency)',
        'doge': 'Dogecoin',
        'fed': 'Federal Reserve',
        'ecb': 'European Central Bank',
        'cpi': 'Consumer price index',
        'gdp': 'Gross domestic product',
        'atr': 'Average true range',
        'rsi': 'Relative strength index',
        'macd': 'MACD',
        'ema': 'Moving average',
        'sma': 'Moving average',
    }
    
    def __init__(
        self, 
        thought_bus: Optional['ThoughtBus'] = None,
        language: str = 'en',
        cache_size: int = 500,
        cache_ttl_hours: int = 24
    ):
        self.thought_bus = thought_bus
        self.language = language
        self.cache = KnowledgeCache(max_size=cache_size, ttl_hours=cache_ttl_hours)
        
        # Query history for learning
        self.query_history: deque = deque(maxlen=100)
        
        # Initialize Wikipedia API
        self.wiki = None
        if WIKIPEDIA_AVAILABLE:
            self.wiki = wikipediaapi.Wikipedia(
                user_agent='AureonTrading/1.0 (autonomous trading knowledge system)',
                language=language
            )
        
        # Metrics
        self.metrics = {
            'queries': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'last_query_time': None
        }
    
    def _publish_thought(self, topic: str, payload: Dict[str, Any], meta: Optional[Dict] = None):
        """Publish a thought to the ThoughtBus if available."""
        if self.thought_bus and Thought:
            thought = Thought(
                source="knowledge_base",
                topic=topic,
                payload=payload,
                meta=meta or {}
            )
            self.thought_bus.publish(thought)
            return thought.id
        return None
    
    def _resolve_alias(self, term: str) -> str:
        """Resolve trading aliases to Wikipedia article titles."""
        term_lower = term.lower().strip()
        return self.ENTITY_ALIASES.get(term_lower, term)
    
    def get_article(self, title: str, use_cache: bool = True) -> Optional[KnowledgeArticle]:
        """
        Fetch a Wikipedia article by title.
        
        Args:
            title: Article title or trading alias
            use_cache: Whether to check cache first
            
        Returns:
            KnowledgeArticle or None if not found
        """
        if not self.wiki:
            return None
        
        # Resolve aliases
        resolved_title = self._resolve_alias(title)
        
        # Check cache
        if use_cache:
            cached = self.cache.get(resolved_title, self.language)
            if cached:
                self.metrics['cache_hits'] += 1
                return cached
        
        # Fetch from Wikipedia
        try:
            self.metrics['api_calls'] += 1
            page = self.wiki.page(resolved_title)
            
            if not page.exists():
                return None
            
            # Extract sections (top-level only)
            sections = [s.title for s in page.sections][:10]
            
            # Extract categories
            categories = list(page.categories.keys())[:10]
            
            article = KnowledgeArticle(
                title=page.title,
                summary=page.summary,
                url=page.fullurl,
                categories=categories,
                sections=sections,
                language=self.language,
                fetch_time=datetime.utcnow().isoformat()
            )
            
            # Cache the result
            self.cache.set(resolved_title, article, self.language)
            
            return article
            
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"[KnowledgeBase] Error fetching '{resolved_title}': {e}")
            return None
    
    def search_knowledge(
        self, 
        query: str, 
        context: str = "trading",
        max_results: int = 5
    ) -> KnowledgeQuery:
        """
        Search for knowledge related to a query.
        
        Args:
            query: Search query
            context: Context for relevance scoring
            max_results: Maximum results to return
            
        Returns:
            KnowledgeQuery with results
        """
        self.metrics['queries'] += 1
        self.metrics['last_query_time'] = datetime.utcnow().isoformat()
        
        kq = KnowledgeQuery(
            query=query,
            context=context,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Try direct article fetch first
        article = self.get_article(query)
        if article:
            article.relevance_score = 1.0
            kq.results.append(article)
        
        # Also search related terms
        related_terms = self._generate_related_terms(query, context)
        for term in related_terms[:max_results - len(kq.results)]:
            if term.lower() != query.lower():
                article = self.get_article(term)
                if article:
                    # Score based on term relevance
                    article.relevance_score = 0.8 - (0.1 * related_terms.index(term))
                    kq.results.append(article)
        
        # Record query
        self.query_history.append(kq)
        
        # Publish thought
        if kq.results:
            self._publish_thought("knowledge.query_result", {
                'query': query,
                'context': context,
                'results_count': len(kq.results),
                'top_result': kq.results[0].title if kq.results else None
            })
        
        return kq
    
    def _generate_related_terms(self, query: str, context: str) -> List[str]:
        """Generate related search terms based on query and context."""
        terms = [query]
        
        # Add context-specific expansions
        if context == "trading":
            if "bitcoin" in query.lower() or "btc" in query.lower():
                terms.extend(["Bitcoin", "Cryptocurrency", "Blockchain"])
            elif "stock" in query.lower():
                terms.extend(["Stock market", "Technical analysis", "Stock exchange"])
            elif "inflation" in query.lower():
                terms.extend(["Inflation", "Consumer price index", "Federal Reserve"])
        
        return terms[:5]
    
    def get_trading_context(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading-relevant context for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "AAPL")
            
        Returns:
            Dictionary with relevant knowledge
        """
        context = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'articles': [],
            'summary': ""
        }
        
        # Map symbol to search terms
        symbol_upper = symbol.upper()
        search_terms = []
        
        if symbol_upper in ['BTC', 'XBT', 'BTCUSDT', 'BTCUSD']:
            search_terms = ['Bitcoin', 'Cryptocurrency market']
        elif symbol_upper in ['ETH', 'ETHUSDT', 'ETHUSD']:
            search_terms = ['Ethereum', 'Smart contract']
        elif symbol_upper in ['SOL', 'SOLUSDT', 'SOLUSD']:
            search_terms = ['Solana (cryptocurrency)']
        elif symbol_upper in ['XRP', 'XRPUSDT']:
            search_terms = ['Ripple (cryptocurrency)']
        else:
            # Generic stock/crypto lookup
            search_terms = [symbol]
        
        # Fetch articles
        for term in search_terms[:2]:
            article = self.get_article(term)
            if article:
                context['articles'].append({
                    'title': article.title,
                    'summary_preview': article.summary_preview,
                    'url': article.url
                })
        
        # Generate summary
        if context['articles']:
            context['summary'] = f"Knowledge context for {symbol}: {len(context['articles'])} relevant articles found."
        else:
            context['summary'] = f"No Wikipedia context found for {symbol}."
        
        return context
    
    def prefetch_trading_knowledge(self) -> Dict[str, Any]:
        """
        Prefetch common trading-related Wikipedia articles.
        Useful for warming the cache at startup.
        
        Returns:
            Summary of prefetched articles
        """
        prefetched = []
        failed = []
        
        for topic in self.TRADING_TOPICS:
            article = self.get_article(topic)
            if article:
                prefetched.append(topic)
            else:
                failed.append(topic)
            
            # Small delay to be nice to Wikipedia
            time.sleep(0.1)
        
        # Publish thought about prefetch
        self._publish_thought("knowledge.prefetch_complete", {
            'prefetched_count': len(prefetched),
            'failed_count': len(failed),
            'topics': prefetched[:10]
        })
        
        return {
            'status': 'complete',
            'prefetched': len(prefetched),
            'failed': len(failed),
            'cache_stats': self.cache.stats()
        }
    
    def explain_concept(self, concept: str) -> Optional[str]:
        """
        Get a concise explanation of a trading/financial concept.
        
        Args:
            concept: The concept to explain
            
        Returns:
            Explanation string or None
        """
        article = self.get_article(concept)
        if article:
            # Return first 500 chars of summary
            explanation = article.summary[:500]
            if len(article.summary) > 500:
                explanation += "..."
            return explanation
        return None
    
    def get_category_articles(self, category: str, max_articles: int = 10) -> List[KnowledgeArticle]:
        """
        Get articles from a Wikipedia category.
        
        Args:
            category: Category name (e.g., "Cryptocurrencies")
            max_articles: Maximum articles to fetch
            
        Returns:
            List of KnowledgeArticle objects
        """
        if not self.wiki:
            return []
        
        try:
            cat_page = self.wiki.page(f"Category:{category}")
            if not cat_page.exists():
                return []
            
            articles = []
            for title, page in list(cat_page.categorymembers.items())[:max_articles]:
                # Skip sub-categories
                if page.ns == wikipediaapi.Namespace.MAIN:
                    article = self.get_article(title)
                    if article:
                        articles.append(article)
            
            return articles
            
        except Exception as e:
            self.metrics['errors'] += 1
            print(f"[KnowledgeBase] Error fetching category '{category}': {e}")
            return []
    
    def autonomous_research(self, topic: str, depth: int = 2) -> Dict[str, Any]:
        """
        Perform autonomous research on a topic.
        Explores the topic and related concepts.
        
        Args:
            topic: Starting topic
            depth: How deep to explore (1-3)
            
        Returns:
            Research results with knowledge graph
        """
        depth = max(1, min(3, depth))  # Clamp to 1-3
        
        research = {
            'topic': topic,
            'timestamp': datetime.utcnow().isoformat(),
            'depth': depth,
            'articles': {},
            'connections': [],
            'key_concepts': []
        }
        
        # BFS exploration
        explored = set()
        to_explore = [(topic, 0)]
        
        while to_explore and len(research['articles']) < 20:
            current_topic, current_depth = to_explore.pop(0)
            
            if current_topic in explored or current_depth > depth:
                continue
            
            explored.add(current_topic)
            article = self.get_article(current_topic)
            
            if article:
                research['articles'][article.title] = {
                    'summary': article.summary_preview,
                    'url': article.url,
                    'depth': current_depth
                }
                
                # Extract related topics from sections
                if current_depth < depth:
                    for section in article.sections[:5]:
                        if section not in explored:
                            to_explore.append((section, current_depth + 1))
                            research['connections'].append({
                                'from': article.title,
                                'to': section,
                                'type': 'section'
                            })
        
        # Extract key concepts (most connected)
        concept_counts = {}
        for conn in research['connections']:
            concept_counts[conn['to']] = concept_counts.get(conn['to'], 0) + 1
        
        research['key_concepts'] = sorted(
            concept_counts.keys(), 
            key=lambda x: concept_counts[x], 
            reverse=True
        )[:5]
        
        # Publish research thought
        self._publish_thought("knowledge.research_complete", {
            'topic': topic,
            'articles_found': len(research['articles']),
            'connections': len(research['connections']),
            'key_concepts': research['key_concepts']
        })
        
        return research
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics."""
        return {
            'available': WIKIPEDIA_AVAILABLE,
            'language': self.language,
            'cache': self.cache.stats(),
            'metrics': self.metrics.copy(),
            'query_history_size': len(self.query_history)
        }


# Convenience function for integration
def create_knowledge_base(thought_bus: Optional['ThoughtBus'] = None) -> KnowledgeBase:
    """
    Create a KnowledgeBase instance with default config.
    
    Args:
        thought_bus: Optional ThoughtBus for publishing thoughts
    
    Returns:
        Configured KnowledgeBase instance
    """
    return KnowledgeBase(thought_bus=thought_bus)


# Demo and testing
def demo():
    """Demo the knowledge base functionality."""
    print("=" * 60)
    print("AUREON KNOWLEDGE BASE DEMO")
    print("=" * 60)
    
    if not WIKIPEDIA_AVAILABLE:
        print("❌ Wikipedia API not available. Install with: pip install wikipedia-api")
        return
    
    kb = KnowledgeBase()
    
    # Test 1: Direct article lookup
    print("\n[1] Direct Article Lookup: 'Bitcoin'")
    article = kb.get_article('Bitcoin')
    if article:
        print(f"    Title: {article.title}")
        print(f"    Summary: {article.summary_preview}")
        print(f"    URL: {article.url}")
        print(f"    Sections: {article.sections[:5]}")
    
    # Test 2: Alias resolution
    print("\n[2] Alias Resolution: 'btc' -> ?")
    article = kb.get_article('btc')
    if article:
        print(f"    Resolved to: {article.title}")
    
    # Test 3: Search knowledge
    print("\n[3] Knowledge Search: 'cryptocurrency trading'")
    kq = kb.search_knowledge('cryptocurrency', context='trading', max_results=3)
    print(f"    Found {len(kq.results)} results:")
    for r in kq.results:
        print(f"      • {r.title} (relevance: {r.relevance_score})")
    
    # Test 4: Trading context
    print("\n[4] Trading Context: 'ETH'")
    ctx = kb.get_trading_context('ETH')
    print(f"    Summary: {ctx['summary']}")
    for a in ctx['articles']:
        print(f"      • {a['title']}")
    
    # Test 5: Concept explanation
    print("\n[5] Concept Explanation: 'Technical analysis'")
    explanation = kb.explain_concept('Technical analysis')
    if explanation:
        print(f"    {explanation[:200]}...")
    
    # Test 6: Autonomous research
    print("\n[6] Autonomous Research: 'Algorithmic trading' (depth=1)")
    research = kb.autonomous_research('Algorithmic trading', depth=1)
    print(f"    Articles found: {len(research['articles'])}")
    print(f"    Connections: {len(research['connections'])}")
    print(f"    Key concepts: {research['key_concepts']}")
    
    # Status
    print("\n[7] Knowledge Base Status:")
    status = kb.get_status()
    print(f"    Cache size: {status['cache']['size']}")
    print(f"    API calls: {status['metrics']['api_calls']}")
    print(f"    Cache hits: {status['metrics']['cache_hits']}")
    print(f"    Errors: {status['metrics']['errors']}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    demo()
