"""
ObsidianVaultAdapter — bidirectional sync between Aureon and an Obsidian vault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

An Obsidian vault is, structurally, a folder of Markdown files with optional
YAML frontmatter. This adapter treats that folder as a persistent backing
store for the AureonVault:

  Obsidian note  ──────  read as ──────▶  VaultContent (category="obsidian_note")
                                         source_topic="obsidian.note"
                                         payload={title, body, tags, path, mtime}

  VaultContent   ──────  written as ─────▶  <content_id>-<slug>.md with YAML
                                           frontmatter carrying category,
                                           source_topic, harmonic_hash, etc.

Sync is one-shot by default (`sync_in` / `sync_out`) and can be promoted to
a polling watcher (`watch`) if you want live edits to flow in. There is no
filesystem-event dependency — pure stdlib, works on any platform, and the
in-memory `_seen_paths` cache dedups re-scans.

Conflict model: last-write-wins per file path. The vault's harmonic_hash is
what resolves duplicates — two adapters pointing at the same Obsidian folder
converge because they produce the same hash for the same note content.

Gary Leckey · Aureon Institute — April 2026
"""

from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.vault.obsidian_adapter")


FRONTMATTER_DELIM = "---"
SAFE_SLUG_RE = re.compile(r"[^a-z0-9]+")


# ─────────────────────────────────────────────────────────────────────────────
# Frontmatter parsing (tiny, zero-dep)
# ─────────────────────────────────────────────────────────────────────────────


def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """Split `---\\nkey: val\\n---\\nbody` into (dict, body). No YAML lib.

    We support scalar strings, ints, floats, booleans, and inline lists
    `[a, b, c]`. Anything else becomes a raw string.
    """
    if not text.startswith(FRONTMATTER_DELIM + "\n"):
        return {}, text
    try:
        end = text.index("\n" + FRONTMATTER_DELIM + "\n", len(FRONTMATTER_DELIM) + 1)
    except ValueError:
        return {}, text
    header = text[len(FRONTMATTER_DELIM) + 1:end]
    body = text[end + len(FRONTMATTER_DELIM) + 2:]
    meta: Dict[str, Any] = {}
    for line in header.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        meta[key.strip()] = _coerce_scalar(raw.strip())
    return meta, body


def _coerce_scalar(raw: str) -> Any:
    if raw == "":
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(p.strip()) for p in inner.split(",")]
    lower = raw.lower()
    if lower in ("true", "false"):
        return lower == "true"
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def _render_frontmatter(meta: Dict[str, Any]) -> str:
    lines = [FRONTMATTER_DELIM]
    for key, value in meta.items():
        if isinstance(value, list):
            inner = ", ".join(_render_scalar(v) for v in value)
            lines.append(f"{key}: [{inner}]")
        else:
            lines.append(f"{key}: {_render_scalar(value)}")
    lines.append(FRONTMATTER_DELIM)
    return "\n".join(lines) + "\n"


def _render_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote if it contains characters that would break our tiny parser
    if any(c in s for c in (":", "#", "[", "]", "\n")):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _slugify(text: str, max_len: int = 40) -> str:
    s = SAFE_SLUG_RE.sub("-", (text or "").lower()).strip("-")
    return (s[:max_len] or "note").strip("-") or "note"


# ─────────────────────────────────────────────────────────────────────────────
# ObsidianVaultAdapter
# ─────────────────────────────────────────────────────────────────────────────


class ObsidianVaultAdapter:
    """Bidirectional sync between an Obsidian folder and an AureonVault."""

    NOTE_CATEGORY: str = "obsidian_note"
    NOTE_SOURCE_TOPIC: str = "obsidian.note"

    def __init__(
        self,
        vault: Any,
        obsidian_root: Any,
        *,
        encoding: str = "utf-8",
        export_subdir: str = "aureon",
        poll_interval_s: float = 1.618,
    ):
        self.vault = vault
        self.obsidian_root = Path(obsidian_root)
        self.encoding = str(encoding)
        self.export_subdir = str(export_subdir)
        self.poll_interval_s = float(poll_interval_s)

        self._lock = threading.RLock()
        # path -> (mtime, harmonic_hash)  —  so we skip unchanged files
        self._seen: Dict[str, Tuple[float, str]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = {"in": 0, "out": 0, "skipped": 0, "errors": 0}

    # ─────────────────────────────────────────────────────────────────────
    # Sync in — Obsidian → AureonVault
    # ─────────────────────────────────────────────────────────────────────

    def sync_in(self) -> int:
        """Scan the Obsidian folder, ingest new/changed .md files. Returns ingested count."""
        root = self.obsidian_root
        if not root.exists() or not root.is_dir():
            logger.debug("ObsidianVaultAdapter: root missing: %s", root)
            return 0
        ingested = 0
        for path in sorted(root.rglob("*.md")):
            try:
                if self._ingest_file(path):
                    ingested += 1
            except Exception as e:
                logger.debug("ObsidianVaultAdapter: ingest %s failed: %s", path, e)
                self._stats["errors"] += 1
        self._stats["in"] += ingested
        return ingested

    def _ingest_file(self, path: Path) -> bool:
        key = str(path.resolve())
        try:
            stat = path.stat()
        except OSError:
            return False
        mtime = float(stat.st_mtime)
        with self._lock:
            prev = self._seen.get(key)
        if prev is not None and prev[0] >= mtime:
            self._stats["skipped"] += 1
            return False

        text = path.read_text(encoding=self.encoding, errors="replace")
        meta, body = _parse_frontmatter(text)
        title = str(meta.get("title") or path.stem)
        tags = meta.get("tags")
        if not isinstance(tags, list):
            tags = [tags] if tags else []
        payload = {
            "title": title,
            "body": body.strip(),
            "tags": [str(t) for t in tags],
            "path": str(path),
            "mtime": mtime,
            "frontmatter": meta,
        }
        content = self._build_content(payload)
        if content is None:
            return False
        # Skip if we already hold this exact hash (file rewritten without changes).
        if self._vault_has_hash(content.harmonic_hash):
            with self._lock:
                self._seen[key] = (mtime, content.harmonic_hash)
            self._stats["skipped"] += 1
            return False
        added = self._vault_add(content)
        if added:
            with self._lock:
                self._seen[key] = (mtime, content.harmonic_hash)
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────
    # Sync out — AureonVault → Obsidian
    # ─────────────────────────────────────────────────────────────────────

    def sync_out(self, card: Any) -> Optional[Path]:
        """Write a single VaultContent card out as a Markdown file."""
        to_dict = getattr(card, "to_dict", None)
        card_dict = to_dict() if callable(to_dict) else dict(card) if isinstance(card, dict) else {}
        if not card_dict:
            return None

        payload = card_dict.get("payload") or {}
        title = str(payload.get("title") or card_dict.get("source_topic") or "card")
        body = payload.get("body")
        if not isinstance(body, str):
            # Non-note cards: embed payload as a fenced JSON block so the
            # note is still human-readable in Obsidian.
            import json as _json
            body = "```json\n" + _json.dumps(payload, indent=2, default=str) + "\n```"

        meta = {
            "aureon_content_id": card_dict.get("content_id", ""),
            "aureon_category": card_dict.get("category", ""),
            "aureon_source_topic": card_dict.get("source_topic", ""),
            "aureon_harmonic_hash": card_dict.get("harmonic_hash", ""),
            "aureon_timestamp": card_dict.get("timestamp", time.time()),
            "title": title,
        }
        tags = payload.get("tags")
        if isinstance(tags, list) and tags:
            meta["tags"] = [str(t) for t in tags]

        slug = _slugify(title)
        cid = str(card_dict.get("content_id") or "") or str(int(time.time() * 1000))
        out_dir = self.obsidian_root / self.export_subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{cid}-{slug}.md"
        out_path.write_text(_render_frontmatter(meta) + body + "\n", encoding=self.encoding)
        with self._lock:
            self._seen[str(out_path.resolve())] = (out_path.stat().st_mtime, meta["aureon_harmonic_hash"])
        self._stats["out"] += 1
        return out_path

    def sync_out_all(self, category: Optional[str] = None, limit: Optional[int] = None) -> int:
        """Write every card (optionally filtered by category) out to Obsidian."""
        cards = self._iter_vault_cards()
        n = 0
        for card in cards:
            cat = getattr(card, "category", "") or (card.get("category", "") if isinstance(card, dict) else "")
            if category and cat != category:
                continue
            if self.sync_out(card) is not None:
                n += 1
                if limit and n >= limit:
                    break
        return n

    # ─────────────────────────────────────────────────────────────────────
    # Watch loop
    # ─────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop, name="ObsidianVaultAdapterWatch", daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _watch_loop(self) -> None:
        while self._running:
            try:
                self.sync_in()
            except Exception as e:
                logger.debug("ObsidianVaultAdapter: watch sync failed: %s", e)
            time.sleep(self.poll_interval_s)

    # ─────────────────────────────────────────────────────────────────────
    # Vault helpers
    # ─────────────────────────────────────────────────────────────────────

    def _build_content(self, payload: Dict[str, Any]) -> Optional[Any]:
        try:
            from aureon.vault.aureon_vault import VaultContent
        except Exception:
            return None
        love = float(getattr(self.vault, "love_amplitude", 0.0) or 0.0)
        return VaultContent.build(
            category=self.NOTE_CATEGORY,
            source_topic=self.NOTE_SOURCE_TOPIC,
            payload=payload,
            love_weight=love,
        )

    def _vault_has_hash(self, h: str) -> bool:
        if not h:
            return False
        contents = getattr(self.vault, "_contents", None)
        if contents:
            for c in contents.values():
                if getattr(c, "harmonic_hash", "") == h:
                    return True
        return False

    def _vault_add(self, content: Any) -> bool:
        adder = getattr(self.vault, "add", None)
        if not callable(adder):
            return False
        try:
            adder(content)
            return True
        except Exception as e:
            logger.debug("ObsidianVaultAdapter: vault.add failed: %s", e)
            return False

    def _iter_vault_cards(self) -> List[Any]:
        contents = getattr(self.vault, "_contents", None)
        if contents:
            return list(contents.values())
        getter = getattr(self.vault, "all_cards", None)
        return list(getter()) if callable(getter) else []

    # ─────────────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            seen = len(self._seen)
        return {
            "root": str(self.obsidian_root),
            "seen": seen,
            "running": self._running,
            "poll_interval_s": self.poll_interval_s,
            **self._stats,
        }


__all__ = [
    "ObsidianVaultAdapter",
]
