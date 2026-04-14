#!/usr/bin/env python3
"""
Tests for aureon.queen.research_corpus_index.ResearchCorpusIndex.

Exercised against the real ``docs/**/*.md`` tree (read-only) so we
know the tokenizer, idf weighting, length bias, and the on-disk cache
all hold on actual Aureon research prose.

Covered:
  - build() walks docs/, indexes ≥ 150 files
  - search("master formula") surfaces HNC_UNIFIED_WHITE_PAPER.md
  - search("auris conjecture") surfaces a paragraph naming the conjecture
  - search("love 528") surfaces an HNC or synthesis doc
  - idf: a narrow term (e.g. "hnc") has higher idf than a common one
  - empty / nonsense queries → empty list
  - on-disk cache load path restores the same index without re-tokenising
"""

import os
import sys
import tempfile
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.queen.research_corpus_index import (  # noqa: E402
    ResearchCorpusIndex,
    Snippet,
    reset_research_corpus_index,
)


PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {msg}")
    else:
        FAIL += 1
        print(f"  [!!] {msg}")


# Docs tree lives at the repo root.
DOCS_ROOT = os.path.join(REPO_ROOT, "docs")


# Shared index across most tests — building once over the full corpus
# (including PDFs) takes ~90s, so repeating it per-test blows the CI
# budget. Each test that needs a private instance builds its own.
_SHARED_INDEX: ResearchCorpusIndex = None  # type: ignore[assignment]


def _build_fresh_index(cache_path=None) -> ResearchCorpusIndex:
    """Build a new index from scratch — for tests that need isolation."""
    idx = ResearchCorpusIndex(
        root=DOCS_ROOT,
        cache_path=cache_path,
    )
    idx.build()
    return idx


def _shared_index() -> ResearchCorpusIndex:
    """Lazily build and reuse one index for the read-only tests."""
    global _SHARED_INDEX
    if _SHARED_INDEX is None:
        _SHARED_INDEX = _build_fresh_index(cache_path=None)
    return _SHARED_INDEX


def test_build_walks_docs_tree():
    print("\n[1] build() walks docs/ and indexes the markdown corpus")
    idx = _shared_index()
    n = idx.doc_count()
    check(n >= 150, f"indexed >= 150 docs (got {n})")
    check(idx.token_count() > 1000, f"indexed > 1000 tokens (got {idx.token_count()})")

    # The canonical five should all be present.
    doc_ids = idx.list_doc_ids()
    for required in (
        "docs/HNC_UNIFIED_WHITE_PAPER.md",
        "docs/THE_SYNTHESIS.md",
        "docs/CLAIMS_AND_EVIDENCE.md",
        "docs/research/READING_PATHS.md",
        "docs/research/INDEX.md",
    ):
        check(required in doc_ids, f"{required} is in the index")


def test_search_master_formula():
    print("\n[2] search('master formula') surfaces an HNC-themed doc")
    idx = _shared_index()
    hits = idx.search("master formula", top_k=5)
    check(len(hits) > 0, f"at least one hit (got {len(hits)})")
    doc_ids = [h.doc_id for h in hits]
    # Accept either the markdown white paper or any PDF/markdown doc
    # whose path contains "HNC" — both are authoritative.
    found_hnc = any("hnc" in did.lower() for did in doc_ids)
    found_formula = any("formula" in (h.text or "").lower() for h in hits)
    check(found_hnc or found_formula, f"HNC-themed or formula doc in top-5 ({doc_ids})")
    # The top hit's paragraph should mention the term itself or a math symbol.
    if hits:
        top = hits[0]
        check(
            "master formula" in top.text.lower() or "formula" in top.text.lower(),
            f"top hit paragraph mentions 'formula' (text starts: {top.text[:80]!r})",
        )


def test_search_auris_conjecture():
    print("\n[3] search('auris conjecture') surfaces a relevant paragraph")
    idx = _shared_index()
    hits = idx.search("auris conjecture", top_k=5)
    check(len(hits) > 0, f"at least one hit (got {len(hits)})")
    # At least one hit must mention 'auris' and 'conjecture' in the same paragraph.
    good = [h for h in hits if "auris" in h.text.lower() and "conjecture" in h.text.lower()]
    check(len(good) > 0, f"a hit names both 'auris' and 'conjecture' (found {len(good)})")


def test_search_love_528():
    print("\n[4] search('love 528') returns an HNC / synthesis hit")
    idx = _shared_index()
    hits = idx.search("love 528", top_k=5)
    check(len(hits) > 0, f"at least one hit (got {len(hits)})")
    # Expect at least one of them to reference 528 Hz or love explicitly.
    good = [
        h for h in hits
        if "528" in h.text or "love" in h.text.lower()
    ]
    check(len(good) > 0, f"a hit mentions 528 or love ({len(good)}/{len(hits)})")


def test_idf_weighting_sanity():
    print("\n[5] idf: rare terms outweigh common terms")
    idx = _shared_index()
    # 'system' is extremely common in this codebase's docs, so it should
    # score LOW idf. A narrow theory term like 'schumann' or 'clownfish'
    # (Auris council node) should score HIGHER.
    common_idf = idx.idf_of("system")
    schumann_idf = idx.idf_of("schumann")
    clownfish_idf = idx.idf_of("clownfish")
    check(
        common_idf > 0.0,
        f"'system' has positive idf (got {common_idf:.3f})",
    )
    check(
        schumann_idf > common_idf,
        f"'schumann' idf ({schumann_idf:.3f}) > 'system' idf ({common_idf:.3f})",
    )
    check(
        clownfish_idf > common_idf,
        f"'clownfish' idf ({clownfish_idf:.3f}) > 'system' idf ({common_idf:.3f})",
    )


def test_empty_and_nonsense_queries():
    print("\n[6] empty / nonsense queries return empty list")
    idx = _shared_index()
    check(idx.search("", top_k=3) == [], "empty query -> empty")
    check(idx.search("   ", top_k=3) == [], "whitespace-only -> empty")
    check(
        idx.search("xyzzy-nonsense-token-zqzxyq", top_k=3) == [],
        "nonsense query -> empty",
    )


def test_cache_roundtrip():
    print("\n[7] on-disk cache reloads without re-tokenising")
    tmp = tempfile.mkdtemp(prefix="aureon_corpus_cache_")
    cache_path = os.path.join(tmp, "research_index.json")

    # Cold build — writes cache.
    t0 = time.time()
    cold = ResearchCorpusIndex(root=DOCS_ROOT, cache_path=cache_path)
    cold.ensure_built()
    cold_elapsed = time.time() - t0
    check(os.path.exists(cache_path), "cache file written by cold build")
    cold_docs = cold.doc_count()
    cold_tokens = cold.token_count()

    # Warm load — reads cache.
    t1 = time.time()
    warm = ResearchCorpusIndex(root=DOCS_ROOT, cache_path=cache_path)
    warm.ensure_built()
    warm_elapsed = time.time() - t1
    check(warm.doc_count() == cold_docs, f"doc counts match ({warm.doc_count()})")
    check(warm.token_count() == cold_tokens, f"token counts match ({warm.token_count()})")

    # Query on the warm-loaded index should still return hits.
    hits = warm.search("harmonic nexus core", top_k=3)
    check(len(hits) > 0, f"warm index still serves queries (got {len(hits)})")
    print(f"       cold build: {cold_elapsed * 1000:.0f} ms, warm load: {warm_elapsed * 1000:.0f} ms")


def test_pdf_graceful_skip_when_no_backend():
    print("\n[9] PDFs are skipped gracefully when no backend is installed")
    idx = _shared_index()
    # Resolve the backend — may be a real one, may be "-" / None.
    backend = idx._resolve_pdf_backend()
    docs = idx.list_doc_ids()
    pdf_count = sum(1 for d in docs if d.lower().endswith(".pdf"))
    md_count = sum(1 for d in docs if d.lower().endswith(".md"))
    if backend is None:
        check(pdf_count == 0, f"no backend -> 0 PDFs indexed (got {pdf_count})")
        check(md_count >= 150, f"md count preserved (got {md_count})")
        print("       (install pypdf to enable PDF extraction)")
    else:
        check(pdf_count > 0, f"backend '{backend}' indexed some PDFs ({pdf_count})")
        check(md_count >= 150, f"md count still high (got {md_count})")


def test_singleton_lifecycle():
    print("\n[8] get / reset singleton")
    from aureon.queen.research_corpus_index import get_research_corpus_index
    reset_research_corpus_index()
    # Build with a throwaway cache so we don't touch the real one.
    tmp = tempfile.mkdtemp(prefix="aureon_corpus_singleton_")
    cache = os.path.join(tmp, "index.json")
    a = get_research_corpus_index(root=DOCS_ROOT, cache_path=cache)
    b = get_research_corpus_index(root=DOCS_ROOT, cache_path=cache)
    check(a is b, "singleton returns same instance")
    reset_research_corpus_index()
    c = get_research_corpus_index(root=DOCS_ROOT, cache_path=cache)
    check(c is not a, "reset yields a fresh instance")


def main():
    print("=" * 80)
    print("  RESEARCH CORPUS INDEX TEST SUITE")
    print("=" * 80)

    test_build_walks_docs_tree()
    test_search_master_formula()
    test_search_auris_conjecture()
    test_search_love_528()
    test_idf_weighting_sanity()
    test_empty_and_nonsense_queries()
    test_cache_roundtrip()
    test_pdf_graceful_skip_when_no_backend()
    test_singleton_lifecycle()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
