#!/usr/bin/env python3
"""
Ingest ALL Queen systems into Aureon's unified global history SQLite database.

The Queen is a massive AI consciousness / trading system with 99+ modules.
This script is the bridge that wires every accumulated piece of knowledge,
memory, insight, thought, tactic, and trading signal into the single-file
global history DB so the rest of the Aureon ecosystem can query it.

Sources ingested (10 total):
  1. Consciousness state file  (memories + wisdom)
  2. Trading knowledge          (concepts)
  3. Warfare tactics            (loss-learning tactics)
  4. Battle results             (simulation outcomes)
  5. Consciousness decisions    (realm votes, consensus)
  6. Thought-bus JSONL files    (queen_thoughts, portfolio_thoughts, queen_trades)
  7. Live queen modules         (deep intel, market awareness, neuron, consciousness,
                                 open-source data, loss learning, eternal machine)
  8. Neuron weights             (neural network weight matrices)
  9. Capital knowledge          (capital markets learned knowledge)
 10. All remaining queen state  (glob queen_*.json catch-all)

Usage:
  python scripts/python/ingest_queen_knowledge.py
  python scripts/python/ingest_queen_knowledge.py --sources state,knowledge,live
  python scripts/python/ingest_queen_knowledge.py --db path/to/custom.sqlite
"""

from __future__ import annotations

import argparse
import glob as globmod
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Repo-root / sys.path setup (same pattern as other scripts/python/ scripts)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Also add aureon/queen so that queen modules can be imported directly.
_QUEEN_DIR = _REPO_ROOT / "aureon" / "queen"
if str(_QUEEN_DIR) not in sys.path:
    sys.path.insert(0, str(_QUEEN_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass

from aureon.core.aureon_global_history_db import (
    connect,
    insert_forecast,
    insert_queen_insight,
    insert_queen_knowledge,
    insert_queen_memory,
    insert_queen_thought,
    insert_sentiment,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BATCH_SIZE = 500

ALL_SOURCES = [
    "state", "knowledge", "tactics", "battles", "decisions",
    "thoughts", "live", "weights", "capital", "all_state",
]


def _json_safe(obj: Any) -> str:
    """Serialize obj to compact JSON, handling non-serializable types."""
    try:
        return json.dumps(obj, ensure_ascii=True, separators=(",", ":"), default=str)
    except Exception:
        try:
            return json.dumps({"_unserializable": True, "repr": repr(obj)},
                              ensure_ascii=True, separators=(",", ":"))
        except Exception:
            return "{}"


def _to_ms(ts: Any) -> Optional[int]:
    """Convert a timestamp to epoch milliseconds.

    Handles:
      - epoch seconds (float/int < 10^12)
      - epoch ms (int >= 10^12)
      - ISO datetime strings
      - None / missing
    """
    if ts is None:
        return None
    if isinstance(ts, str):
        ts = ts.strip()
        if not ts:
            return None
        # Try parsing ISO format
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                     "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                     "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                     "%Y-%m-%d"):
            try:
                dt = datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        # Maybe it is a numeric string
        try:
            ts = float(ts)
        except ValueError:
            return None
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return None
    if ts > 1e15:
        # Microseconds? Convert to ms.
        return int(ts / 1000)
    if ts > 1e12:
        # Already milliseconds.
        return int(ts)
    # Seconds.
    return int(ts * 1000)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _det_id(*parts: Any) -> str:
    """Build a deterministic dedup ID from parts."""
    raw = ":".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:24]


def _load_json(path: Path) -> Optional[Any]:
    """Load a JSON file, returning None on missing/corrupt."""
    if not path.is_file():
        print(f"  [skip] File not found: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"  [warn] Could not parse {path}: {exc}")
        return None


class _Counter:
    """Simple inserted/skipped counter for a source."""
    def __init__(self, name: str):
        self.name = name
        self.inserted = 0
        self.skipped = 0
        self.errors = 0

    def record(self, ok: bool) -> None:
        if ok:
            self.inserted += 1
        else:
            self.skipped += 1

    def summary(self) -> str:
        parts = [f"inserted={self.inserted}", f"skipped={self.skipped}"]
        if self.errors:
            parts.append(f"errors={self.errors}")
        return f"  [{self.name}] {', '.join(parts)}"


def _batch_commit(conn, counter: _Counter) -> None:
    """Commit every BATCH_SIZE inserts."""
    total = counter.inserted + counter.skipped
    if total > 0 and total % BATCH_SIZE == 0:
        conn.commit()


# ---------------------------------------------------------------------------
# SOURCE 1: Consciousness State File
# ---------------------------------------------------------------------------

def ingest_consciousness_state(conn, repo: Path) -> _Counter:
    c = _Counter("consciousness_state")
    path = repo / "state" / "queen" / "queen_consciousness_state.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    # Memories
    memories = data.get("memories") or {}
    for mem_id, mem in memories.items():
        ok = insert_queen_memory(conn, {
            "memory_id": f"consciousness:{mem_id}",
            "memory_type": "memory",
            "category": mem.get("category"),
            "title": mem.get("title"),
            "description": mem.get("description"),
            "symbol": mem.get("context", {}).get("symbol") if isinstance(mem.get("context"), dict) else None,
            "outcome": mem.get("outcome"),
            "outcome_value": mem.get("outcome_value"),
            "importance": mem.get("importance"),
            "confidence": None,
            "lesson": mem.get("lesson_learned"),
            "ts_ms": _to_ms(mem.get("created")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(mem),
        })
        c.record(ok)
        _batch_commit(conn, c)

    # Wisdom
    wisdom = data.get("wisdom") or {}
    for wis_id, wis in wisdom.items():
        ok = insert_queen_memory(conn, {
            "memory_id": f"wisdom:{wis_id}",
            "memory_type": "wisdom",
            "category": wis.get("applies_to"),
            "title": wis.get("truth", "")[:120] if wis.get("truth") else None,
            "description": wis.get("truth"),
            "symbol": None,
            "outcome": None,
            "outcome_value": None,
            "importance": wis.get("times_validated"),
            "confidence": wis.get("certainty"),
            "lesson": wis.get("truth"),
            "ts_ms": _to_ms(wis.get("created")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(wis),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 2: Trading Knowledge
# ---------------------------------------------------------------------------

def ingest_trading_knowledge(conn, repo: Path) -> _Counter:
    c = _Counter("trading_knowledge")
    path = repo / "state" / "queen" / "queen_trading_knowledge.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    concepts = data.get("concepts") or data  # fallback: top-level is the map
    if not isinstance(concepts, dict):
        print("  [warn] Unexpected trading_knowledge structure")
        return c

    for slug, item in concepts.items():
        if not isinstance(item, dict):
            continue
        ok = insert_queen_knowledge(conn, {
            "knowledge_id": f"concept:{slug}",
            "knowledge_type": "concept",
            "topic": item.get("topic") or slug,
            "summary": item.get("summary"),
            "source": item.get("source"),
            "confidence": item.get("confidence"),
            "success_rate": item.get("success_rate"),
            "times_applied": item.get("times_applied"),
            "ts_ms": _to_ms(item.get("learned_at")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(item),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 3: Warfare Tactics
# ---------------------------------------------------------------------------

def ingest_warfare_tactics(conn, repo: Path) -> _Counter:
    c = _Counter("warfare_tactics")
    path = repo / "state" / "queen" / "queen_warfare_tactics.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    # The file may be a dict of tactics or a list; handle both.
    items: Dict[str, Any] = {}
    if isinstance(data, dict):
        # If wrapped in a key like "tactics", unwrap; otherwise treat top-level as map.
        for key in ("tactics", "strategies", "lessons"):
            if key in data and isinstance(data[key], (dict, list)):
                data = data[key]
                break
        if isinstance(data, dict):
            items = data
        elif isinstance(data, list):
            items = {str(i): v for i, v in enumerate(data) if isinstance(v, dict)}
    elif isinstance(data, list):
        items = {str(i): v for i, v in enumerate(data) if isinstance(v, dict)}

    for tactic_id, tactic in items.items():
        if not isinstance(tactic, dict):
            continue
        ok = insert_queen_knowledge(conn, {
            "knowledge_id": f"tactic:{tactic_id}",
            "knowledge_type": "tactic",
            "topic": tactic.get("name") or tactic.get("topic") or tactic.get("tactic") or tactic_id,
            "summary": tactic.get("summary") or tactic.get("description") or _json_safe(tactic)[:500],
            "source": tactic.get("source", "warfare_tactics"),
            "confidence": tactic.get("confidence"),
            "success_rate": tactic.get("success_rate") or tactic.get("win_rate"),
            "times_applied": tactic.get("times_applied") or tactic.get("times_used"),
            "ts_ms": _to_ms(tactic.get("created") or tactic.get("learned_at") or tactic.get("timestamp")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(tactic),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 4: Battle Results
# ---------------------------------------------------------------------------

def ingest_battle_results(conn, repo: Path) -> _Counter:
    c = _Counter("battle_results")
    path = repo / "state" / "queen" / "queen_battle_results.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    # May be a list or dict of battle results.
    battles: list = []
    if isinstance(data, list):
        battles = data
    elif isinstance(data, dict):
        for key in ("results", "battles", "simulations"):
            if key in data and isinstance(data[key], list):
                battles = data[key]
                break
        if not battles:
            # Treat each top-level key as a battle.
            battles = [{"_key": k, **v} for k, v in data.items() if isinstance(v, dict)]

    for i, battle in enumerate(battles):
        if not isinstance(battle, dict):
            continue
        bid = battle.get("id") or battle.get("battle_id") or battle.get("_key") or str(i)
        ok = insert_queen_insight(conn, {
            "insight_id": f"battle:{bid}",
            "source": "battle_simulator",
            "insight_type": "battle_result",
            "symbol": battle.get("symbol"),
            "title": battle.get("title") or battle.get("name") or f"Battle #{bid}",
            "conclusion": battle.get("result") or battle.get("outcome") or battle.get("summary"),
            "confidence": battle.get("confidence"),
            "severity": battle.get("severity") or battle.get("impact"),
            "ts_ms": _to_ms(battle.get("timestamp") or battle.get("created") or battle.get("ts")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(battle),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 5: Consciousness Decisions
# ---------------------------------------------------------------------------

def ingest_consciousness_decisions(conn, repo: Path) -> _Counter:
    c = _Counter("consciousness_decisions")
    path = repo / "state" / "queen" / "queen_consciousness_decisions.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    decisions: list = []
    if isinstance(data, list):
        decisions = data
    elif isinstance(data, dict):
        for key in ("decisions", "history"):
            if key in data and isinstance(data[key], list):
                decisions = data[key]
                break
        if not decisions:
            decisions = [{"_key": k, **v} for k, v in data.items() if isinstance(v, dict)]

    for i, dec in enumerate(decisions):
        if not isinstance(dec, dict):
            continue
        did = dec.get("id") or dec.get("decision_id") or dec.get("_key") or str(i)
        ok = insert_queen_insight(conn, {
            "insight_id": f"decision:{did}",
            "source": "consciousness",
            "insight_type": "decision",
            "symbol": dec.get("symbol"),
            "title": dec.get("title") or dec.get("action") or f"Decision #{did}",
            "conclusion": dec.get("consensus") or dec.get("result") or dec.get("summary"),
            "confidence": dec.get("confidence"),
            "severity": dec.get("severity"),
            "ts_ms": _to_ms(dec.get("timestamp") or dec.get("created") or dec.get("ts")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(dec),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 6: Thought Bus JSONL Files
# ---------------------------------------------------------------------------

def _ingest_jsonl(conn, filepath: Path, source_name: str, limit: int,
                  also_insight: bool = False) -> _Counter:
    """Read a JSONL file line-by-line, storing as queen_thoughts (and optionally insights)."""
    c = _Counter(f"thoughts:{filepath.name}")
    if not filepath.is_file():
        print(f"  [skip] File not found: {filepath}")
        return c
    now = _now_ms()
    count = 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            if count >= limit:
                print(f"  [info] Reached thoughts-limit ({limit}) for {filepath.name}")
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                c.errors += 1
                continue
            if not isinstance(obj, dict):
                c.errors += 1
                continue

            tid = obj.get("id") or _det_id(source_name, lineno, obj.get("ts", ""))
            payload = obj.get("payload") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {"text": payload}

            symbol = (payload.get("symbol") or obj.get("symbol")
                      or obj.get("meta", {}).get("symbol") if isinstance(obj.get("meta"), dict) else None)
            topic = obj.get("topic") or payload.get("topic")
            thought_text = (payload.get("text") or payload.get("message")
                           or payload.get("thought") or _json_safe(payload)[:1000])
            confidence = payload.get("confidence") or obj.get("confidence")

            ok = insert_queen_thought(conn, {
                "thought_id": f"{source_name}:{tid}",
                "source": obj.get("source") or source_name,
                "topic": topic,
                "symbol": symbol,
                "thought_text": thought_text,
                "confidence": confidence,
                "ts_ms": _to_ms(obj.get("ts")),
                "ingested_at_ms": now,
                "raw_json": _json_safe(obj),
            })
            c.record(ok)
            count += 1

            # For trade JSONL, also store as insight
            if also_insight:
                insert_queen_insight(conn, {
                    "insight_id": f"trade_signal:{tid}",
                    "source": source_name,
                    "insight_type": "trade_signal",
                    "symbol": symbol,
                    "title": topic or "trade_signal",
                    "conclusion": thought_text,
                    "confidence": confidence,
                    "severity": None,
                    "ts_ms": _to_ms(obj.get("ts")),
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(obj),
                })

            _batch_commit(conn, c)

    conn.commit()
    return c


def ingest_thoughts(conn, repo: Path, limit: int) -> List[_Counter]:
    counters = []
    thought_files = [
        (repo / "data" / "queen_thoughts.jsonl", "queen_thoughts", False),
        (repo / "data" / "portfolio_thoughts.jsonl", "portfolio_thoughts", False),
        (repo / "data" / "queen_trades.jsonl", "queen_trades", True),
    ]
    for path, src, also_insight in thought_files:
        counters.append(_ingest_jsonl(conn, path, src, limit, also_insight=also_insight))
    return counters


# ---------------------------------------------------------------------------
# SOURCE 7: Live Queen Modules
# ---------------------------------------------------------------------------

def ingest_live_modules(conn, repo: Path) -> List[_Counter]:
    """Try to import and query each live queen module. Each is try/except guarded."""
    counters = []
    now = _now_ms()

    # 7a: QueenDeepIntelligence
    c = _Counter("live:deep_intelligence")
    try:
        from aureon.queen.queen_deep_intelligence import QueenDeepIntelligence
        engine = QueenDeepIntelligence()
        insights = engine.generate_insights()
        if insights:
            for ins in insights:
                raw = ins if isinstance(ins, dict) else (ins.__dict__ if hasattr(ins, "__dict__") else {"value": str(ins)})
                iid = raw.get("id") or _det_id("deep_intel", raw.get("title", ""), raw.get("insight_type", ""))
                ok = insert_queen_insight(conn, {
                    "insight_id": f"deep_intel:{iid}",
                    "source": "deep_intelligence",
                    "insight_type": raw.get("insight_type", "deep_insight"),
                    "symbol": raw.get("symbol"),
                    "title": raw.get("title"),
                    "conclusion": raw.get("conclusion") or raw.get("reasoning"),
                    "confidence": raw.get("confidence"),
                    "severity": raw.get("severity"),
                    "ts_ms": now,
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(raw),
                })
                c.record(ok)
            conn.commit()
        print(f"  [ok] QueenDeepIntelligence: {c.inserted} insights")
    except Exception as exc:
        print(f"  [skip] QueenDeepIntelligence: {exc}")
        c.errors += 1
    counters.append(c)

    # 7b: QueenMarketAwareness
    c = _Counter("live:market_awareness")
    try:
        from aureon.queen.queen_market_awareness import QueenMarketAwareness
        awareness = QueenMarketAwareness()
        # Try common method names to get a snapshot
        snapshot = None
        for method in ("get_market_condition", "get_snapshot", "get_state", "assess"):
            fn = getattr(awareness, method, None)
            if callable(fn):
                snapshot = fn()
                break
        if snapshot is None and hasattr(awareness, "__dict__"):
            snapshot = awareness.__dict__
        if snapshot:
            raw = snapshot if isinstance(snapshot, dict) else (snapshot.__dict__ if hasattr(snapshot, "__dict__") else {"value": str(snapshot)})
            ok = insert_queen_insight(conn, {
                "insight_id": f"market_condition:{_det_id('market_awareness', now)}",
                "source": "market_awareness",
                "insight_type": "market_condition",
                "symbol": raw.get("symbol", "BTC"),
                "title": f"Market: {raw.get('market_state', 'unknown')}",
                "conclusion": _json_safe({k: raw.get(k) for k in
                    ("btc_price", "market_state", "market_severity", "should_hold", "recovery_outlook")
                    if k in raw}),
                "confidence": raw.get("confidence"),
                "severity": raw.get("market_severity"),
                "ts_ms": now,
                "ingested_at_ms": now,
                "raw_json": _json_safe(raw),
            })
            c.record(ok)
            conn.commit()
        print(f"  [ok] QueenMarketAwareness: {c.inserted} insights")
    except Exception as exc:
        print(f"  [skip] QueenMarketAwareness: {exc}")
        c.errors += 1
    counters.append(c)

    # 7c: QueenNeuron / QueenNeuronV2
    c = _Counter("live:neuron")
    for mod_name in ("aureon.queen.queen_neuron_v2", "aureon.queen.queen_neuron"):
        try:
            mod = __import__(mod_name, fromlist=["_"])
            # Look for a class with "Neuron" in the name
            cls = None
            for attr_name in dir(mod):
                obj = getattr(mod, attr_name, None)
                if isinstance(obj, type) and "neuron" in attr_name.lower():
                    cls = obj
                    break
            if cls:
                instance = cls()
                state = None
                for method in ("get_weights", "get_state", "export_state", "state_dict"):
                    fn = getattr(instance, method, None)
                    if callable(fn):
                        state = fn()
                        break
                if state is None and hasattr(instance, "__dict__"):
                    state = instance.__dict__
                if state:
                    raw = state if isinstance(state, dict) else {"state": str(state)[:2000]}
                    ok = insert_queen_knowledge(conn, {
                        "knowledge_id": f"neural_weights:{mod_name}:{_det_id(mod_name, now)}",
                        "knowledge_type": "neural_weights",
                        "topic": mod_name.split(".")[-1],
                        "summary": f"Live neural weights from {mod_name}",
                        "source": mod_name,
                        "confidence": None,
                        "success_rate": None,
                        "times_applied": None,
                        "ts_ms": now,
                        "ingested_at_ms": now,
                        "raw_json": _json_safe(raw),
                    })
                    c.record(ok)
                    conn.commit()
                    print(f"  [ok] {mod_name}: stored weights")
                    break  # Only need one neuron version
        except Exception as exc:
            print(f"  [skip] {mod_name}: {exc}")
            c.errors += 1
    counters.append(c)

    # 7d: QueenConsciousness
    c = _Counter("live:consciousness")
    try:
        from aureon.queen.queen_consciousness_model import QueenConsciousness
        consciousness = QueenConsciousness()
        summary = None
        for method in ("get_state_summary", "get_state", "state_summary", "summarize"):
            fn = getattr(consciousness, method, None)
            if callable(fn):
                summary = fn()
                break
        if summary is None and hasattr(consciousness, "__dict__"):
            summary = consciousness.__dict__
        if summary:
            raw = summary if isinstance(summary, dict) else (summary.__dict__ if hasattr(summary, "__dict__") else {"value": str(summary)})
            ok = insert_queen_insight(conn, {
                "insight_id": f"consciousness_state:{_det_id('consciousness', now)}",
                "source": "consciousness_model",
                "insight_type": "consciousness_state",
                "symbol": None,
                "title": f"Consciousness: mood={raw.get('mood', '?')}, regime={raw.get('reality_regime', '?')}",
                "conclusion": _json_safe({k: raw.get(k) for k in
                    ("identity", "mood", "reality_regime", "dream_progress", "happiness_quotient")
                    if k in raw}),
                "confidence": raw.get("happiness_quotient"),
                "severity": None,
                "ts_ms": now,
                "ingested_at_ms": now,
                "raw_json": _json_safe(raw),
            })
            c.record(ok)
            conn.commit()
        print(f"  [ok] QueenConsciousness: {c.inserted} insights")
    except Exception as exc:
        print(f"  [skip] QueenConsciousness: {exc}")
        c.errors += 1
    counters.append(c)

    # 7e: OpenSourceDataEngine
    c = _Counter("live:open_source_data")
    try:
        from aureon.queen.queen_open_source_data_engine import OpenSourceDataEngine
        engine = OpenSourceDataEngine()
        data = None
        for method in ("get_sentiment", "get_market_data", "get_whale_alerts", "fetch_all", "get_data"):
            fn = getattr(engine, method, None)
            if callable(fn):
                data = fn()
                break
        if data:
            items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                sid = item.get("id") or _det_id("osde", i, now)
                ok = insert_sentiment(conn, {
                    "source": "open_source_data_engine",
                    "sentiment_id": f"osde:{sid}",
                    "sentiment_type": item.get("type") or item.get("sentiment_type") or "market",
                    "symbol": item.get("symbol") or item.get("asset"),
                    "value": item.get("value") or item.get("score"),
                    "label": item.get("label") or item.get("sentiment"),
                    "ts_ms": _to_ms(item.get("timestamp") or item.get("ts")) or now,
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(item),
                })
                c.record(ok)
            conn.commit()
        print(f"  [ok] OpenSourceDataEngine: {c.inserted} sentiment rows")
    except Exception as exc:
        print(f"  [skip] OpenSourceDataEngine: {exc}")
        c.errors += 1
    counters.append(c)

    # 7f: QueenLossLearning
    c = _Counter("live:loss_learning")
    try:
        from aureon.queen.queen_loss_learning import QueenLossLearning
        learner = QueenLossLearning()
        lessons = None
        for method in ("get_lessons", "get_loss_patterns", "get_knowledge", "export"):
            fn = getattr(learner, method, None)
            if callable(fn):
                lessons = fn()
                break
        if lessons:
            items = lessons if isinstance(lessons, list) else ([lessons] if isinstance(lessons, dict) else [])
            for i, lesson in enumerate(items):
                if not isinstance(lesson, dict):
                    continue
                lid = lesson.get("id") or _det_id("loss_lesson", i, lesson.get("topic", ""))
                ok = insert_queen_knowledge(conn, {
                    "knowledge_id": f"loss_lesson:{lid}",
                    "knowledge_type": "loss_lesson",
                    "topic": lesson.get("topic") or lesson.get("pattern") or f"loss_lesson_{i}",
                    "summary": lesson.get("summary") or lesson.get("lesson") or lesson.get("description"),
                    "source": "loss_learning",
                    "confidence": lesson.get("confidence"),
                    "success_rate": lesson.get("success_rate"),
                    "times_applied": lesson.get("times_applied"),
                    "ts_ms": _to_ms(lesson.get("timestamp") or lesson.get("created")),
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(lesson),
                })
                c.record(ok)
            conn.commit()
        print(f"  [ok] QueenLossLearning: {c.inserted} knowledge rows")
    except Exception as exc:
        print(f"  [skip] QueenLossLearning: {exc}")
        c.errors += 1
    counters.append(c)

    # 7g: QueenEternalMachine
    c = _Counter("live:eternal_machine")
    try:
        from aureon.queen.queen_eternal_machine import QueenEternalMachine
        machine = QueenEternalMachine()
        status = None
        for method in ("get_breadcrumb_status", "get_positions", "get_status", "breadcrumb_status"):
            fn = getattr(machine, method, None)
            if callable(fn):
                status = fn()
                break
        if status:
            raw = status if isinstance(status, dict) else (status.__dict__ if hasattr(status, "__dict__") else {"value": str(status)})
            positions = raw.get("positions") or raw.get("breadcrumbs") or []
            if isinstance(positions, dict):
                positions = list(positions.values())
            if not positions and isinstance(raw, dict):
                # The whole thing might be the position data
                positions = [raw]
            for i, pos in enumerate(positions):
                if not isinstance(pos, dict):
                    continue
                pid = pos.get("id") or _det_id("position", pos.get("symbol", ""), i)
                ok = insert_queen_insight(conn, {
                    "insight_id": f"position_snapshot:{pid}:{_det_id(now, i)}",
                    "source": "eternal_machine",
                    "insight_type": "position_snapshot",
                    "symbol": pos.get("symbol"),
                    "title": f"Position: {pos.get('symbol', '?')} qty={pos.get('qty', '?')}",
                    "conclusion": _json_safe({k: pos.get(k) for k in
                        ("symbol", "qty", "cost", "value", "pnl") if k in pos}),
                    "confidence": None,
                    "severity": None,
                    "ts_ms": now,
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(pos),
                })
                c.record(ok)
            conn.commit()
        print(f"  [ok] QueenEternalMachine: {c.inserted} position snapshots")
    except Exception as exc:
        print(f"  [skip] QueenEternalMachine: {exc}")
        c.errors += 1
    counters.append(c)

    return counters


# ---------------------------------------------------------------------------
# SOURCE 8: Neuron Weights
# ---------------------------------------------------------------------------

def ingest_neuron_weights(conn, repo: Path) -> _Counter:
    c = _Counter("neuron_weights")
    path = repo / "state" / "queen" / "queen_neuron_v2_weights.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    # Weights file may have multiple layers/sections or be a flat blob.
    if isinstance(data, dict):
        for layer_name, weights in data.items():
            ok = insert_queen_knowledge(conn, {
                "knowledge_id": f"neural_weights:v2:{layer_name}",
                "knowledge_type": "neural_weights",
                "topic": f"neuron_v2:{layer_name}",
                "summary": f"Neural weight matrix for layer '{layer_name}', shape/size: {_describe_shape(weights)}",
                "source": "queen_neuron_v2_weights.json",
                "confidence": None,
                "success_rate": None,
                "times_applied": None,
                "ts_ms": now,
                "ingested_at_ms": now,
                "raw_json": _json_safe(weights),
            })
            c.record(ok)
            _batch_commit(conn, c)
    else:
        ok = insert_queen_knowledge(conn, {
            "knowledge_id": "neural_weights:v2:full",
            "knowledge_type": "neural_weights",
            "topic": "neuron_v2:full_weights",
            "summary": f"Full neural weight dump, type={type(data).__name__}",
            "source": "queen_neuron_v2_weights.json",
            "confidence": None,
            "success_rate": None,
            "times_applied": None,
            "ts_ms": now,
            "ingested_at_ms": now,
            "raw_json": _json_safe(data),
        })
        c.record(ok)

    conn.commit()
    return c


def _describe_shape(obj: Any) -> str:
    """Describe shape of a weight matrix for the summary field."""
    if isinstance(obj, list):
        if obj and isinstance(obj[0], list):
            return f"{len(obj)}x{len(obj[0])}"
        return f"[{len(obj)}]"
    if isinstance(obj, dict):
        return f"dict({len(obj)} keys)"
    return type(obj).__name__


# ---------------------------------------------------------------------------
# SOURCE 9: Capital Knowledge
# ---------------------------------------------------------------------------

def ingest_capital_knowledge(conn, repo: Path) -> _Counter:
    c = _Counter("capital_knowledge")
    path = repo / "state" / "queen" / "queen_capital_knowledge.json"
    data = _load_json(path)
    if data is None:
        return c
    now = _now_ms()

    items: Dict[str, Any] = {}
    if isinstance(data, dict):
        # May have a wrapping key
        for key in ("knowledge", "concepts", "capital"):
            if key in data and isinstance(data[key], dict):
                items = data[key]
                break
        if not items:
            items = data
    elif isinstance(data, list):
        items = {str(i): v for i, v in enumerate(data) if isinstance(v, dict)}

    for kid, item in items.items():
        if not isinstance(item, dict):
            continue
        ok = insert_queen_knowledge(conn, {
            "knowledge_id": f"capital_knowledge:{kid}",
            "knowledge_type": "capital_knowledge",
            "topic": item.get("topic") or item.get("name") or kid,
            "summary": item.get("summary") or item.get("description") or _json_safe(item)[:500],
            "source": item.get("source", "capital_knowledge"),
            "confidence": item.get("confidence"),
            "success_rate": item.get("success_rate"),
            "times_applied": item.get("times_applied"),
            "ts_ms": _to_ms(item.get("learned_at") or item.get("timestamp") or item.get("created")),
            "ingested_at_ms": now,
            "raw_json": _json_safe(item),
        })
        c.record(ok)
        _batch_commit(conn, c)

    conn.commit()
    return c


# ---------------------------------------------------------------------------
# SOURCE 10: All Other Queen State Files (catch-all)
# ---------------------------------------------------------------------------

# Files already handled by specific sources — skip in the catch-all.
_HANDLED_FILES = {
    "queen_consciousness_state.json",
    "queen_trading_knowledge.json",
    "queen_warfare_tactics.json",
    "queen_battle_results.json",
    "queen_consciousness_decisions.json",
    "queen_neuron_v2_weights.json",
    "queen_capital_knowledge.json",
}


def ingest_all_state(conn, repo: Path) -> List[_Counter]:
    """Glob state/queen/queen_*.json and ingest any not covered by specific sources."""
    counters = []
    state_dir = repo / "state" / "queen"
    if not state_dir.is_dir():
        print(f"  [skip] Directory not found: {state_dir}")
        return counters

    pattern = str(state_dir / "queen_*.json")
    for filepath in sorted(globmod.glob(pattern)):
        fpath = Path(filepath)
        fname = fpath.name
        if fname in _HANDLED_FILES:
            continue

        c = _Counter(f"state:{fname}")
        data = _load_json(fpath)
        if data is None:
            counters.append(c)
            continue
        now = _now_ms()

        # Store the entire file as a state snapshot knowledge entry.
        # If it is a dict with many keys, store each top-level key separately.
        if isinstance(data, dict) and len(data) > 1:
            for key, val in data.items():
                ok = insert_queen_knowledge(conn, {
                    "knowledge_id": f"state_snapshot:{fname}:{key}",
                    "knowledge_type": "state_snapshot",
                    "topic": f"{fname}:{key}",
                    "summary": _json_safe(val)[:500] if not isinstance(val, str) else val[:500],
                    "source": fname,
                    "confidence": None,
                    "success_rate": None,
                    "times_applied": None,
                    "ts_ms": now,
                    "ingested_at_ms": now,
                    "raw_json": _json_safe(val),
                })
                c.record(ok)
                _batch_commit(conn, c)
        else:
            ok = insert_queen_knowledge(conn, {
                "knowledge_id": f"state_snapshot:{fname}",
                "knowledge_type": "state_snapshot",
                "topic": fname,
                "summary": _json_safe(data)[:500],
                "source": fname,
                "confidence": None,
                "success_rate": None,
                "times_applied": None,
                "ts_ms": now,
                "ingested_at_ms": now,
                "raw_json": _json_safe(data),
            })
            c.record(ok)

        conn.commit()
        counters.append(c)

    return counters


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest ALL Queen knowledge into Aureon's global history SQLite database.",
    )
    parser.add_argument("--db", default=None, help="SQLite database path override")
    parser.add_argument(
        "--sources",
        default="all",
        help="Comma-separated sources to ingest: "
             "state,knowledge,tactics,battles,decisions,thoughts,live,weights,capital,all_state,all "
             "(default: all)",
    )
    parser.add_argument(
        "--thoughts-limit",
        type=int,
        default=50000,
        help="Max thought lines to ingest per JSONL file (default: 50000)",
    )
    args = parser.parse_args()

    requested = {s.strip().lower() for s in args.sources.split(",")}
    run_all = "all" in requested

    print("=" * 72)
    print("  Aureon Queen Knowledge Ingestion")
    print("=" * 72)
    print(f"  Repo root : {_REPO_ROOT}")
    print(f"  Sources   : {'all' if run_all else ', '.join(sorted(requested))}")
    print(f"  Thoughts limit: {args.thoughts_limit}")
    print()

    conn = connect(args.db)
    print(f"  Database  : {conn.execute('PRAGMA database_list').fetchone()[2]}")
    print()

    all_counters: List[_Counter] = []

    # 1. Consciousness state
    if run_all or "state" in requested:
        print("[1/10] Consciousness state ...")
        all_counters.append(ingest_consciousness_state(conn, _REPO_ROOT))

    # 2. Trading knowledge
    if run_all or "knowledge" in requested:
        print("[2/10] Trading knowledge ...")
        all_counters.append(ingest_trading_knowledge(conn, _REPO_ROOT))

    # 3. Warfare tactics
    if run_all or "tactics" in requested:
        print("[3/10] Warfare tactics ...")
        all_counters.append(ingest_warfare_tactics(conn, _REPO_ROOT))

    # 4. Battle results
    if run_all or "battles" in requested:
        print("[4/10] Battle results ...")
        all_counters.append(ingest_battle_results(conn, _REPO_ROOT))

    # 5. Consciousness decisions
    if run_all or "decisions" in requested:
        print("[5/10] Consciousness decisions ...")
        all_counters.append(ingest_consciousness_decisions(conn, _REPO_ROOT))

    # 6. Thought bus JSONL
    if run_all or "thoughts" in requested:
        print("[6/10] Thought bus JSONL files ...")
        all_counters.extend(ingest_thoughts(conn, _REPO_ROOT, args.thoughts_limit))

    # 7. Live queen modules
    if run_all or "live" in requested:
        print("[7/10] Live queen modules ...")
        all_counters.extend(ingest_live_modules(conn, _REPO_ROOT))

    # 8. Neuron weights
    if run_all or "weights" in requested:
        print("[8/10] Neuron weights ...")
        all_counters.append(ingest_neuron_weights(conn, _REPO_ROOT))

    # 9. Capital knowledge
    if run_all or "capital" in requested:
        print("[9/10] Capital knowledge ...")
        all_counters.append(ingest_capital_knowledge(conn, _REPO_ROOT))

    # 10. All remaining state files
    if run_all or "all_state" in requested:
        print("[10/10] All remaining queen state files ...")
        all_counters.extend(ingest_all_state(conn, _REPO_ROOT))

    # Final commit
    conn.commit()
    conn.close()

    # Summary
    print()
    print("-" * 72)
    print("  INGESTION SUMMARY")
    print("-" * 72)
    total_inserted = 0
    total_skipped = 0
    total_errors = 0
    for counter in all_counters:
        print(counter.summary())
        total_inserted += counter.inserted
        total_skipped += counter.skipped
        total_errors += counter.errors
    print("-" * 72)
    print(f"  TOTAL: inserted={total_inserted}, skipped={total_skipped}, errors={total_errors}")
    print("=" * 72)
    print("  Queen knowledge ingestion complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
