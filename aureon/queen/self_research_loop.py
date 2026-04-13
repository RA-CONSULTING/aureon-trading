"""
aureon/queen/self_research_loop.py

SelfResearchLoop — the system actively searches its own questions.

Architecture:
    1. Periodically scan the knowledge dataset for "question" type fragments
    2. Generate search queries from each question
    3. Call WorldDataIngester to pull answers from free APIs
    4. Open a stash pocket per question, dump every result
    5. Close the pocket → interpreter → crystallizes back into the dataset
    6. Mark the original question as "answered"

The loop runs on a background thread at a configurable interval.
It is THE feedback that turns "I have a question" into "here is what
I learned, indexed and structured for future retrieval."

Pure stdlib. No LLM dependency. Uses keyword extraction to build queries.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.queen.self_research")


# ─────────────────────────────────────────────────────────────────────────────
# Helper — turn a fragment into a search query
# ─────────────────────────────────────────────────────────────────────────────


_STOPWORDS = frozenset(
    "a an the and or but if then so to of in on at by for from with into about "
    "is are was were be been being have has had do does did i you it we they "
    "this that these those my your our their what why how when where which who "
    "not no yes maybe really very".split()
)


def fragment_to_query(text: str, max_words: int = 6) -> str:
    """Extract the most meaningful keywords from a fragment as a search query."""
    if not text:
        return ""
    # Strip boilerplate
    text = re.sub(r"Aureon In-House Analysis[^\n]*\n", "", text)
    text = re.sub(r"Query:[^\n]*\n", "", text)
    text = re.sub(r"Signal:[^\n]*\n", "", text)
    text = re.sub(r"Context:.*?Excitement:[^\n]*\n", "", text, flags=re.DOTALL)
    # Extract words ≥ 4 chars, drop stopwords
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    words = [w for w in words if w not in _STOPWORDS]
    # Take first N unique words preserving order
    seen = set()
    keywords: List[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            keywords.append(w)
            if len(keywords) >= max_words:
                break
    return " ".join(keywords)


# ─────────────────────────────────────────────────────────────────────────────
# Research result
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ResearchResult:
    question_text: str
    query: str
    items_found: int
    pocket_id: str = ""
    fragments_added: int = 0
    timestamp: float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────────────────────
# SelfResearchLoop
# ─────────────────────────────────────────────────────────────────────────────


class SelfResearchLoop:
    """
    Background loop that finds unanswered questions in the knowledge
    dataset and actively researches them via the WorldDataIngester.
    """

    def __init__(
        self,
        knowledge_dataset: Any = None,
        world_data_ingester: Any = None,
        stash_pockets: Any = None,
        thought_bus: Any = None,
        interval_s: float = 60.0,
        max_questions_per_cycle: int = 3,
    ):
        self.knowledge_dataset = knowledge_dataset
        self.world_data_ingester = world_data_ingester
        self.stash_pockets = stash_pockets
        self.thought_bus = thought_bus
        self.interval_s = interval_s
        self.max_questions_per_cycle = max_questions_per_cycle

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._results: List[ResearchResult] = []
        self._max_results = 100
        self._stats = {
            "cycles": 0,
            "questions_researched": 0,
            "items_pulled": 0,
            "fragments_added": 0,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="self-research-loop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

    def _run_loop(self) -> None:
        while self._running:
            try:
                self.run_one_cycle()
            except Exception as exc:
                logger.debug("research loop cycle failed: %s", exc)
            # Sleep in small chunks so stop() responds quickly
            for _ in range(int(self.interval_s)):
                if not self._running:
                    return
                time.sleep(1.0)

    # ─────────────────────────────────────────────────────────────────────
    # Question discovery
    # ─────────────────────────────────────────────────────────────────────
    def find_unanswered_questions(self, n: int = 5) -> List[Any]:
        """Scan the dataset for question-type fragments not yet researched."""
        if self.knowledge_dataset is None:
            return []
        try:
            questions = self.knowledge_dataset.find_by_data_type("question", n=n * 3)
            # Filter out ones already tagged as researched
            return [q for q in questions if "researched" not in q.tags][:n]
        except Exception:
            return []

    # ─────────────────────────────────────────────────────────────────────
    # One cycle — research up to N questions
    # ─────────────────────────────────────────────────────────────────────
    def run_one_cycle(self) -> Dict[str, Any]:
        """
        Run one research cycle:
          1. Find unanswered question fragments
          2. For each, generate query + call ingester
          3. Open pocket, dump results, close (auto-crystallizes)
          4. Mark original question as researched
        """
        result = {
            "cycle": 0,
            "questions_processed": 0,
            "items_pulled": 0,
            "fragments_added": 0,
        }
        with self._lock:
            self._stats["cycles"] += 1
            result["cycle"] = self._stats["cycles"]

        if self.world_data_ingester is None:
            return result

        questions = self.find_unanswered_questions(n=self.max_questions_per_cycle)
        if not questions:
            # No questions yet — proactively research a default trending topic
            return self._proactive_research()

        for q_frag in questions:
            try:
                self._research_question(q_frag, result)
            except Exception as exc:
                logger.debug("research_question failed: %s", exc)

        return result

    def _research_question(self, q_frag: Any, result: Dict[str, Any]) -> None:
        """Research one question fragment."""
        question_text = getattr(q_frag, "text", "") or getattr(q_frag, "meaning", "")
        if not question_text:
            return

        query = fragment_to_query(question_text)
        if not query:
            return

        # Pull from external sources
        items = self.world_data_ingester.answer_question(query, n_per_source=2)
        if not items:
            # Mark as researched anyway so we don't loop forever
            try:
                if "researched" not in q_frag.tags:
                    q_frag.tags.append("researched")
            except Exception:
                pass
            return

        result["items_pulled"] += len(items)

        # Ingest into vault directly — these become cards
        self.world_data_ingester.ingest_to_vault(items)

        # Also dump into a stash pocket so they crystallize as fragments
        pocket = None
        if self.stash_pockets is not None:
            try:
                pocket = self.stash_pockets.open_pocket(
                    goal_id=f"research_{int(time.time())}",
                    owner="self_research_loop",
                )
                pocket.dump(
                    key="question",
                    value=question_text,
                    tags=["question", "researched_query"],
                )
                for item in items:
                    pocket.dump(
                        key=item.source,
                        value=f"{item.title}: {item.text}",
                        tags=[item.source, item.category, "external_research"],
                    )
                close_result = self.stash_pockets.close_pocket(pocket)
                result["fragments_added"] += close_result.get("fragments_crystallized", 0)
            except Exception as exc:
                logger.debug("stash pocket flow failed: %s", exc)

        # Mark question as researched
        try:
            if "researched" not in q_frag.tags:
                q_frag.tags.append("researched")
        except Exception:
            pass

        # Track
        rr = ResearchResult(
            question_text=question_text[:120],
            query=query,
            items_found=len(items),
            pocket_id=getattr(pocket, "pocket_id", "") if pocket else "",
            fragments_added=result["fragments_added"],
        )
        with self._lock:
            self._results.append(rr)
            while len(self._results) > self._max_results:
                self._results.pop(0)
            self._stats["questions_researched"] += 1
            self._stats["items_pulled"] += len(items)
            self._stats["fragments_added"] += result["fragments_added"]
        result["questions_processed"] += 1

        # Publish event
        if self.thought_bus is not None:
            try:
                self.thought_bus.publish(
                    "self_research.completed",
                    {
                        "question": question_text[:80],
                        "query": query,
                        "items_found": len(items),
                    },
                    source="self_research_loop",
                )
            except Exception:
                pass

    def _proactive_research(self) -> Dict[str, Any]:
        """When there are no unanswered questions, proactively pull
        trending topics so the dataset keeps growing."""
        result = {"cycle": self._stats["cycles"], "items_pulled": 0,
                  "fragments_added": 0, "questions_processed": 0}
        if self.world_data_ingester is None:
            return result
        try:
            # Pull a small batch of mixed trending content
            items: List[Any] = []
            items.extend(self.world_data_ingester.fetch_hacker_news(n=3))
            items.extend(self.world_data_ingester.fetch_reddit("worldnews", n=3))
            btc = self.world_data_ingester.fetch_yahoo_quote("BTC-USD")
            if btc:
                items.append(btc)
            if items:
                self.world_data_ingester.ingest_to_vault(items)
                result["items_pulled"] = len(items)
                # Crystallize into a pocket
                if self.stash_pockets is not None:
                    pocket = self.stash_pockets.open_pocket(
                        goal_id=f"proactive_{int(time.time())}",
                        owner="self_research_loop",
                    )
                    for item in items:
                        pocket.dump(
                            key=item.source,
                            value=f"{item.title}: {item.text}",
                            tags=[item.source, item.category, "proactive"],
                        )
                    close_result = self.stash_pockets.close_pocket(pocket)
                    result["fragments_added"] = close_result.get("fragments_crystallized", 0)
                    with self._lock:
                        self._stats["items_pulled"] += len(items)
                        self._stats["fragments_added"] += result["fragments_added"]
        except Exception as exc:
            logger.debug("proactive research failed: %s", exc)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self._stats,
                "running": self._running,
                "interval_s": self.interval_s,
                "recent_results": len(self._results),
            }

    def recent_results(self, n: int = 10) -> List[ResearchResult]:
        with self._lock:
            return list(self._results[-n:])


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[SelfResearchLoop] = None
_singleton_lock = threading.Lock()


def get_self_research_loop(**kwargs) -> SelfResearchLoop:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = SelfResearchLoop(**kwargs)
        return _singleton


def reset_self_research_loop() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
