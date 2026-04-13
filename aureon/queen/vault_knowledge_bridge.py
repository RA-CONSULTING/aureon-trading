"""
aureon/queen/vault_knowledge_bridge.py

VaultKnowledgeBridge — the live feedback pipe between the vault and the
knowledge dataset.

Problem:
    The vault ingests raw cards from ThoughtBus. The knowledge dataset
    crystallizes structured knowledge from stash pockets. But nothing
    automatically flows vault cards INTO the dataset — so the internal
    knowledge base stops growing unless a goal runs.

Solution:
    This bridge runs a background sync loop that:
        1. Polls the vault every N seconds for new cards
        2. Runs novel cards through the KnowledgeInterpreter (5W1H,
           data_type, category, meaning)
        3. Absorbs interpreted fragments into the KnowledgeDataset
        4. Every M absorptions, triggers self_organize() to rebuild
           the tag index, detect duplicates, and strengthen cross-links
        5. Publishes 'vault.bridge.synced' events to ThoughtBus

Result:
    Every piece of raw data entering the vault is automatically
    structured against the existing knowledge base. The internal
    knowledge base keeps itself organised as new data arrives.

Pure deterministic pipeline — no LLM calls.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("aureon.queen.vault_bridge")


# ─────────────────────────────────────────────────────────────────────────────
# VaultKnowledgeBridge
# ─────────────────────────────────────────────────────────────────────────────


class VaultKnowledgeBridge:
    """
    Continuously syncs the vault → knowledge dataset pipeline so every
    new card flows through the interpreter and gets self-organised
    against the existing structure.
    """

    def __init__(
        self,
        vault: Any = None,
        knowledge_dataset: Any = None,
        knowledge_interpreter: Any = None,
        stash_pockets: Any = None,
        thought_bus: Any = None,
        sync_interval_s: float = 30.0,
        self_organize_every_n_absorbs: int = 15,
        max_cards_per_cycle: int = 50,
    ):
        self.vault = vault
        self.knowledge_dataset = knowledge_dataset
        self.knowledge_interpreter = knowledge_interpreter
        self.stash_pockets = stash_pockets
        self.thought_bus = thought_bus

        self.sync_interval_s = sync_interval_s
        self.self_organize_every_n_absorbs = self_organize_every_n_absorbs
        self.max_cards_per_cycle = max_cards_per_cycle

        # Deduplication — track vault card hashes we've already absorbed
        self._seen_hashes: Set[str] = set()
        self._max_seen_cache = 5000

        # Threading
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Accounting
        self._absorb_counter = 0
        self._stats = {
            "cycles": 0,
            "cards_examined": 0,
            "cards_absorbed": 0,
            "fragments_added": 0,
            "self_organize_runs": 0,
            "errors": 0,
        }
        self._created_at = time.time()

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name="vault-knowledge-bridge",
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
                logger.debug("bridge cycle failed: %s", exc)
                with self._lock:
                    self._stats["errors"] += 1
            # Sleep in small chunks so stop() responds quickly
            for _ in range(int(self.sync_interval_s)):
                if not self._running:
                    return
                time.sleep(1.0)

    # ─────────────────────────────────────────────────────────────────────
    # One sync cycle
    # ─────────────────────────────────────────────────────────────────────
    def run_one_cycle(self) -> Dict[str, Any]:
        """
        Execute one full sync cycle:
          1. Poll recent vault cards
          2. Absorb novel ones through the interpreter
          3. Trigger self_organize() if enough have accumulated
        """
        result = {
            "examined": 0,
            "absorbed": 0,
            "fragments_added": 0,
            "self_organized": False,
        }
        with self._lock:
            self._stats["cycles"] += 1

        if self.vault is None or self.knowledge_dataset is None:
            return result

        # 1. Get recent vault cards
        try:
            recent = self.vault.recent(n=self.max_cards_per_cycle)
        except Exception:
            return result

        result["examined"] = len(recent)
        with self._lock:
            self._stats["cards_examined"] += len(recent)

        # 2. Find novel cards and absorb them
        for card in recent:
            card_hash = getattr(card, "harmonic_hash", "") or getattr(card, "content_id", "")
            if not card_hash:
                continue
            if card_hash in self._seen_hashes:
                continue
            added = self._absorb_card(card)
            if added > 0:
                result["absorbed"] += 1
                result["fragments_added"] += added
                with self._lock:
                    self._absorb_counter += added
                    self._stats["cards_absorbed"] += 1
                    self._stats["fragments_added"] += added
            self._seen_hashes.add(card_hash)

            # Cap the dedup cache
            if len(self._seen_hashes) > self._max_seen_cache:
                # Keep only the most recent half
                self._seen_hashes = set(list(self._seen_hashes)[-self._max_seen_cache // 2:])

        # 3. Trigger self-organization if enough absorbs accumulated
        if self._absorb_counter >= self.self_organize_every_n_absorbs:
            try:
                so = self.knowledge_dataset.self_organize()
                result["self_organized"] = True
                result["self_organize_result"] = so
                with self._lock:
                    self._absorb_counter = 0
                    self._stats["self_organize_runs"] += 1
            except Exception as exc:
                logger.debug("self_organize failed: %s", exc)

        # 4. Publish sync event
        if self.thought_bus is not None:
            try:
                self.thought_bus.publish(
                    "vault.bridge.synced",
                    {
                        "examined": result["examined"],
                        "absorbed": result["absorbed"],
                        "fragments_added": result["fragments_added"],
                        "self_organized": result["self_organized"],
                    },
                    source="vault_knowledge_bridge",
                )
            except Exception:
                pass

        return result

    # ─────────────────────────────────────────────────────────────────────
    # Card absorption — turns a vault card into a knowledge fragment
    # ─────────────────────────────────────────────────────────────────────
    def _absorb_card(self, card: Any) -> int:
        """
        Absorb a single vault card into the knowledge dataset via a
        synthetic one-entry stash pocket so it gets the full
        interpreter pipeline (5W1H, data_type, category, meaning).
        """
        try:
            # Extract text from the card payload
            text = self._card_to_text(card)
            if not text or len(text.strip()) < 5:
                return 0

            # Build a one-shot pocket
            if self.stash_pockets is None:
                return 0
            # Use an internal synthetic pocket — not opened via manager
            from aureon.queen.queen_stash_pockets import StashPocket
            pocket = StashPocket(
                goal_id=f"vault_bridge_{getattr(card, 'content_id', 'x')[:8]}",
                owner="vault_bridge",
            )
            tags = [
                getattr(card, "category", "other"),
                getattr(card, "source_topic", "unknown").split(".")[0],
                "vault_auto",
            ]
            pocket.dump(
                key=getattr(card, "source_topic", "vault_card"),
                value=text,
                tags=tags,
            )

            # Interpret
            interpretations = None
            if self.knowledge_interpreter is not None:
                try:
                    interpretations = self.knowledge_interpreter.interpret_pocket(pocket)
                except Exception:
                    pass

            # Absorb into dataset
            added = self.knowledge_dataset.absorb(
                pocket, interpretations=interpretations
            )
            return added
        except Exception as exc:
            logger.debug("absorb_card failed: %s", exc)
            return 0

    @staticmethod
    def _card_to_text(card: Any) -> str:
        """Extract a meaningful text blob from a vault card payload."""
        payload = getattr(card, "payload", {})
        if isinstance(payload, dict):
            # Prefer explicit text fields
            for key in ("text", "title", "summary", "message", "content"):
                val = payload.get(key)
                if val and isinstance(val, str) and len(val) > 5:
                    return val
            # Fall back to json-dumping the payload
            try:
                return json.dumps(payload, default=str)[:500]
            except Exception:
                return str(payload)[:500]
        return str(payload)[:500]

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self._stats,
                "running": self._running,
                "sync_interval_s": self.sync_interval_s,
                "seen_cache_size": len(self._seen_hashes),
                "uptime_s": round(time.time() - self._created_at, 1),
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[VaultKnowledgeBridge] = None
_singleton_lock = threading.Lock()


def get_vault_knowledge_bridge(**kwargs) -> VaultKnowledgeBridge:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = VaultKnowledgeBridge(**kwargs)
        return _singleton


def reset_vault_knowledge_bridge() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
