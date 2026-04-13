"""
aureon/queen/knowledge_interpreter.py

KnowledgeInterpreter — turns raw stash-pocket dumps into STRUCTURED
knowledge by running a 4-perspective swarm over each entry.

The point: capturing data is not the same as understanding it.
The system must consider WHAT each fragment IS — what kind of data,
what it means, what category it belongs to, what it relates to.

Architecture:
    raw dump → 4 interpretive passes → enriched fragment
        ├── ClassifierPass    → data_type (fact / observation /
        │                        decision / result / error / question)
        ├── SemanticPass      → 1-sentence meaning summary
        ├── CategoristPass    → category (market / system / memory /
        │                        code / user_input / temporal / self)
        └── LinkerPass        → related fragment IDs (graph edges)

Each pass uses ONE of:
    a) The swarm LLM adapter (if available)
    b) Deterministic rule engine (always works, no LLM dependency)

The deterministic path is the default — we don't lean on LLMs.
The LLM path is purely additive enrichment when one is wired.

This is "self-English from random inputs to structured logic."
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.queen.knowledge_interpreter")


# ─────────────────────────────────────────────────────────────────────────────
# Data type taxonomy
# ─────────────────────────────────────────────────────────────────────────────


DATA_TYPES = [
    "fact",          # static information ("Bitcoin uses SHA-256")
    "observation",   # measurement / sensing ("BTC price is $70,000")
    "decision",      # cognitive output ("HOLD until coherence > 0.55")
    "result",        # outcome of an action ("file written to /tmp/x.py")
    "error",         # failure / exception ("connection refused")
    "question",      # an open question ("what is the gamma threshold?")
    "reflection",    # self-reference ("I just analysed bitcoin")
    "tool_output",   # raw tool dispatch result
]


CATEGORIES = [
    "market",        # trading / prices / coins
    "system",        # files / processes / network / OS
    "memory",        # vault / elephant / events
    "code",          # python / shell / scripts
    "user_input",    # human-typed text
    "temporal",      # time-related, hot topics, bursts
    "self",          # consciousness, identity, being model
    "swarm",         # agent dispatch, coordination
    "knowledge",     # research, learning, fragments
    "other",         # default
]


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic classification — no LLM needed
# ─────────────────────────────────────────────────────────────────────────────


# Words that signal a particular data type
TYPE_KEYWORDS = {
    "fact":        ["is", "are", "uses", "contains", "has"],
    "observation": ["price", "level", "rate", "count", "amount", "value"],
    "decision":    ["execute", "hold", "decide", "choose", "vote", "decree"],
    "result":      ["completed", "success", "created", "wrote", "executed"],
    "error":       ["error", "failed", "exception", "denied", "missing", "unavailable"],
    "question":    ["what", "why", "how", "when", "where"],
    "reflection":  ["i ", "myself", "my own", "remember", "thinking"],
    "tool_output": ["result", "output", "stdout", "tool_used"],
}


CATEGORY_KEYWORDS = {
    "market":      ["bitcoin", "btc", "ethereum", "eth", "crypto", "price",
                    "trade", "exchange", "binance", "kraken", "market", "coin"],
    "system":      ["system", "process", "network", "cpu", "platform",
                    "hostname", "file", "directory", "path", "/tmp", "/home"],
    "memory":      ["vault", "elephant", "memory", "remember", "card",
                    "fragment", "history", "event"],
    "code":        ["python", "shell", "script", "code", "function", "class",
                    "import", "def ", ".py", ".sh"],
    "user_input":  ["user", "human", "input", "asked", "request"],
    "temporal":    ["second", "minute", "hour", "tick", "uptime", "burst",
                    "rate", "frequency", "timestamp", "phase"],
    "self":        ["queen", "sero", "consciousness", "lambda", "psi",
                    "gamma", "auris", "tablet", "soul", "being"],
    "swarm":       ["agent", "swarm", "team", "coordinator", "dispatch",
                    "synthesis", "analyst", "scout", "architect"],
    "knowledge":   ["knowledge", "learn", "research", "study", "teach",
                    "wisdom", "fragment", "dataset"],
}


def classify_data_type(text: str) -> str:
    """Score the text against each data type keyword set, return best match."""
    if not text:
        return "other"
    lower = text.lower()
    scores: Dict[str, int] = {dt: 0 for dt in DATA_TYPES}
    for dt, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[dt] += 1
    # Preference order if tied
    best = max(scores.items(), key=lambda x: (x[1], -DATA_TYPES.index(x[0])))
    if best[1] == 0:
        return "fact"  # default
    return best[0]


def classify_category(text: str, tags: List[str]) -> str:
    """Score the text+tags against each category keyword set."""
    if not text and not tags:
        return "other"
    lower = (text + " " + " ".join(tags)).lower()
    scores: Dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[cat] += 1
    best = max(scores.items(), key=lambda x: x[1])
    if best[1] == 0:
        return "other"
    return best[0]


def extract_meaning(text: str, max_words: int = 20) -> str:
    """
    Produce a 1-sentence summary of what the text is about.
    Deterministic: takes the first meaningful sentence and trims it.
    """
    if not text:
        return ""
    # Strip "Aureon In-House Analysis" boilerplate that the brain adapter prepends
    text = re.sub(r"Aureon In-House Analysis[^\n]*\n", "", text)
    text = re.sub(r"Query:[^\n]*\n", "", text)
    text = re.sub(r"Signal:[^\n]*\n", "", text)
    text = text.strip()
    if not text:
        return ""

    # First sentence
    sentences = re.split(r"[.!?]\s+", text)
    first = sentences[0].strip() if sentences else text
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words]) + "..."
    return first


def find_related_keywords(text: str, all_fragments: List[Any], n: int = 3) -> List[int]:
    """
    Find indices of fragments that share keyword overlap with this text.
    Returns up to n indices.
    """
    if not text or not all_fragments:
        return []
    target_words = set(re.findall(r"[a-zA-Z]{4,}", text.lower()))
    if not target_words:
        return []

    scored: List[Tuple[int, int]] = []
    for i, frag in enumerate(all_fragments):
        frag_text = getattr(frag, "text", "") or ""
        if not frag_text:
            continue
        frag_words = set(re.findall(r"[a-zA-Z]{4,}", frag_text.lower()))
        overlap = len(target_words & frag_words)
        if overlap > 0:
            scored.append((overlap, i))
    scored.sort(key=lambda x: -x[0])
    return [idx for _, idx in scored[:n]]


# ─────────────────────────────────────────────────────────────────────────────
# Interpretation result
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Interpretation:
    """Structured understanding of one raw stash entry."""

    data_type: str = "fact"
    category: str = "other"
    meaning: str = ""
    related_indices: List[int] = field(default_factory=list)
    interpretation_source: str = "deterministic"  # or "swarm"
    confidence: float = 0.5


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeInterpreter
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeInterpreter:
    """
    The swarm-driven understanding layer between raw dumps and crystallized
    knowledge. Runs 4 interpretive passes over each entry and produces
    structured Interpretation objects.

    The deterministic path always works (no LLM dependency).
    If a swarm with an LLM adapter is wired, an additional pass enriches
    the meaning summary, but it never blocks the structured pipeline.
    """

    def __init__(
        self,
        swarm: Any = None,
        knowledge_dataset: Any = None,
        nexus_system: Any = None,
        use_llm: bool = False,
    ):
        self.swarm = swarm
        self.knowledge_dataset = knowledge_dataset
        self.nexus_system = nexus_system
        self.use_llm = use_llm
        self._lock = threading.RLock()
        self._stats = {
            "interpretations": 0,
            "swarm_passes": 0,
            "deterministic_passes": 0,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Per-entry interpretation
    # ─────────────────────────────────────────────────────────────────────
    def interpret_entry(
        self,
        text: str,
        tags: List[str],
        existing_fragments: Optional[List[Any]] = None,
    ) -> Interpretation:
        """
        Run all 4 interpretive passes over one raw dump entry.
        Returns a structured Interpretation.
        """
        # Pass 1: Classification — what KIND of data is this?
        data_type = classify_data_type(text)

        # Pass 2: Categorisation — what DOMAIN does it belong to?
        category = classify_category(text, tags)

        # Pass 3: Semantic — what does it MEAN?
        meaning = extract_meaning(text)

        # Pass 4: Linking — what does it RELATE to?
        related: List[int] = []
        if existing_fragments:
            related = find_related_keywords(text, existing_fragments, n=3)

        interpretation = Interpretation(
            data_type=data_type,
            category=category,
            meaning=meaning,
            related_indices=related,
            interpretation_source="deterministic",
            confidence=0.7,
        )

        # Optional LLM enrichment pass — purely additive, never blocking
        if self.use_llm and self.swarm is not None:
            try:
                enriched = self._llm_enrich(text, tags, interpretation)
                if enriched.meaning:
                    interpretation.meaning = enriched.meaning
                interpretation.interpretation_source = "swarm"
                interpretation.confidence = 0.85
                with self._lock:
                    self._stats["swarm_passes"] += 1
            except Exception:
                with self._lock:
                    self._stats["deterministic_passes"] += 1
        else:
            with self._lock:
                self._stats["deterministic_passes"] += 1

        with self._lock:
            self._stats["interpretations"] += 1

        return interpretation

    def _llm_enrich(
        self,
        text: str,
        tags: List[str],
        base: Interpretation,
    ) -> Interpretation:
        """Use the swarm LLM adapter for a richer semantic pass."""
        adapter = getattr(self.swarm, "adapter", None)
        if adapter is None:
            return base
        try:
            resp = adapter.prompt(
                messages=[{"role": "user", "content": (
                    f"Summarise this knowledge fragment in ONE sentence (max 15 words):\n\n"
                    f"{text[:300]}\n\nTags: {tags}"
                )}],
                system="You are a concise knowledge classifier.",
                max_tokens=80,
                temperature=0.2,
            )
            new_meaning = (resp.text or "").strip().split("\n")[0][:200]
            if new_meaning:
                base.meaning = new_meaning
        except Exception:
            pass
        return base

    # ─────────────────────────────────────────────────────────────────────
    # Per-pocket interpretation
    # ─────────────────────────────────────────────────────────────────────
    def interpret_pocket(self, pocket: Any) -> Dict[str, Interpretation]:
        """
        Interpret every entry in a pocket.
        Returns dict: entry_index → Interpretation.
        """
        existing_fragments: List[Any] = []
        if self.knowledge_dataset is not None:
            try:
                existing_fragments = list(getattr(self.knowledge_dataset, "_fragments", []))
            except Exception:
                pass

        results: Dict[int, Interpretation] = {}
        try:
            entries = list(getattr(pocket, "entries", []))
            for i, entry in enumerate(entries):
                text = getattr(entry, "value", "") or ""
                tags = list(getattr(entry, "tags", []) or [])
                interpretation = self.interpret_entry(
                    text=text,
                    tags=tags,
                    existing_fragments=existing_fragments,
                )
                results[i] = interpretation
        except Exception as exc:
            logger.debug("interpret_pocket failed: %s", exc)
        return results

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._stats)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[KnowledgeInterpreter] = None
_singleton_lock = threading.Lock()


def get_knowledge_interpreter(**kwargs) -> KnowledgeInterpreter:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = KnowledgeInterpreter(**kwargs)
        return _singleton


def reset_knowledge_interpreter() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
