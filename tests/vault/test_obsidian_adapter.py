#!/usr/bin/env python3
"""
Tests for ObsidianVaultAdapter — bidirectional sync with a markdown folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.aureon_vault import AureonVault, VaultContent  # noqa: E402
from aureon.vault.obsidian_adapter import (  # noqa: E402
    ObsidianVaultAdapter,
    _parse_frontmatter,
    _render_frontmatter,
    _slugify,
)


# ─────────────────────────────────────────────────────────────────────────────
# Frontmatter helpers
# ─────────────────────────────────────────────────────────────────────────────


def test_parse_frontmatter_roundtrip_preserves_keys():
    original = {
        "title": "a note",
        "tags": ["one", "two"],
        "count": 42,
        "weight": 0.75,
        "published": True,
    }
    rendered = _render_frontmatter(original) + "body text\n"
    meta, body = _parse_frontmatter(rendered)
    assert meta["title"] == "a note"
    assert meta["tags"] == ["one", "two"]
    assert meta["count"] == 42
    assert meta["weight"] == 0.75
    assert meta["published"] is True
    assert body.strip() == "body text"


def test_parse_frontmatter_returns_empty_when_missing():
    meta, body = _parse_frontmatter("no frontmatter here\njust body\n")
    assert meta == {}
    assert "no frontmatter" in body


def test_slugify_is_filename_safe():
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("  --- ") == "note"
    assert _slugify("a/b\\c:d") == "a-b-c-d"


# ─────────────────────────────────────────────────────────────────────────────
# Sync in — Obsidian → Vault
# ─────────────────────────────────────────────────────────────────────────────


def test_sync_in_ingests_plain_markdown(tmp_path: Path):
    (tmp_path / "alpha.md").write_text("# alpha\n\nfirst note\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("# beta\n\nsecond note\n", encoding="utf-8")

    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    n = adapter.sync_in()
    assert n == 2
    assert len(vault) == 2
    titles = {c.payload.get("title") for c in vault._contents.values()}
    assert titles == {"alpha", "beta"}
    for c in vault._contents.values():
        assert c.category == adapter.NOTE_CATEGORY
        assert c.source_topic == adapter.NOTE_SOURCE_TOPIC


def test_sync_in_parses_frontmatter(tmp_path: Path):
    (tmp_path / "gamma.md").write_text(
        "---\ntitle: my note\ntags: [alpha, beta]\n---\nthe body\n",
        encoding="utf-8",
    )
    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    assert adapter.sync_in() == 1
    card = next(iter(vault._contents.values()))
    assert card.payload["title"] == "my note"
    assert card.payload["tags"] == ["alpha", "beta"]
    assert card.payload["body"].strip() == "the body"


def test_sync_in_skips_unchanged_files_on_second_pass(tmp_path: Path):
    (tmp_path / "delta.md").write_text("# delta\nbody\n", encoding="utf-8")
    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    assert adapter.sync_in() == 1
    assert adapter.sync_in() == 0
    assert len(vault) == 1


def test_sync_in_re_ingests_after_mtime_bump(tmp_path: Path):
    path = tmp_path / "epsilon.md"
    path.write_text("# eps\nv1\n", encoding="utf-8")
    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    assert adapter.sync_in() == 1
    # Rewrite with changed content AND a forward-dated mtime so any FS
    # quirks don't hide the update.
    path.write_text("# eps\nv2 changed\n", encoding="utf-8")
    future = path.stat().st_mtime + 10
    os.utime(path, (future, future))
    assert adapter.sync_in() == 1
    assert len(vault) == 2  # original + updated


def test_sync_in_recurses_into_subdirectories(tmp_path: Path):
    (tmp_path / "top.md").write_text("# top\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("# nested\n", encoding="utf-8")
    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    assert adapter.sync_in() == 2


def test_sync_in_handles_missing_root(tmp_path: Path):
    vault = AureonVault()
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path / "does_not_exist")
    assert adapter.sync_in() == 0
    assert len(vault) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Sync out — Vault → Obsidian
# ─────────────────────────────────────────────────────────────────────────────


def test_sync_out_writes_markdown_with_frontmatter(tmp_path: Path):
    vault = AureonVault()
    card = VaultContent.build(
        category="poetry",
        source_topic="vault.poem",
        payload={"title": "first poem", "body": "roses are φ-red", "tags": ["spring", "ritual"]},
        love_weight=0.9,
    )
    vault.add(card)

    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    out_path = adapter.sync_out(card)
    assert out_path is not None
    assert out_path.exists()
    assert out_path.parent.name == "aureon"
    text = out_path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "aureon_content_id" in text
    assert "aureon_harmonic_hash" in text
    assert "roses are φ-red" in text


def test_sync_out_for_non_text_payload_embeds_json_block(tmp_path: Path):
    vault = AureonVault()
    card = VaultContent.build(
        category="signal",
        source_topic="vault.signal",
        payload={"value": 0.618, "phase": "ascending"},
    )
    vault.add(card)
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    out_path = adapter.sync_out(card)
    assert out_path is not None
    text = out_path.read_text(encoding="utf-8")
    assert "```json" in text
    assert "0.618" in text


def test_sync_out_all_with_category_filter(tmp_path: Path):
    vault = AureonVault()
    vault.add(VaultContent.build("obsidian_note", "obsidian.note", {"body": "a"}))
    vault.add(VaultContent.build("obsidian_note", "obsidian.note", {"body": "b"}))
    vault.add(VaultContent.build("other", "other.topic", {"body": "c"}))
    adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmp_path)
    n = adapter.sync_out_all(category="obsidian_note")
    assert n == 2
    out_files = list((tmp_path / "aureon").glob("*.md"))
    assert len(out_files) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Round-trip — write a card out, read the folder back in, hashes match
# ─────────────────────────────────────────────────────────────────────────────


def test_exported_card_round_trips_through_second_vault(tmp_path: Path):
    vault_a = AureonVault()
    card = VaultContent.build(
        category="poetry",
        source_topic="vault.poem",
        payload={"title": "tide song", "body": "the sea remembers"},
    )
    vault_a.add(card)
    ObsidianVaultAdapter(vault=vault_a, obsidian_root=tmp_path).sync_out(card)

    vault_b = AureonVault()
    adapter_b = ObsidianVaultAdapter(vault=vault_b, obsidian_root=tmp_path)
    ingested = adapter_b.sync_in()
    assert ingested == 1
    b_card = next(iter(vault_b._contents.values()))
    assert "the sea remembers" in b_card.payload["body"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
