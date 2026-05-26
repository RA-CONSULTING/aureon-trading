"""Online research cinema pipeline.

This turns real online research into a compact evidence packet:
source discovery, fetch proof, extractive synthesis, visual frames, animated
motion replay, and a cited paper draft. Public artifacts store bounded
snippets and hashes rather than full page bodies.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import textwrap
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional in some runtimes
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore

from aureon.search.swarm_search_fabric import publish_search_event

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_MANIFEST = Path("frontend/public/aureon_online_research_cinema.json")
STATE_MANIFEST = Path("state/aureon_online_research_cinema_latest.json")
DOCS_INDEX = Path("docs/audits/aureon_online_research_cinema_latest.json")

USER_AGENT = "Mozilla/5.0 (Aureon Research Cinema; local evidence agent)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rooted(root: Optional[Path], rel: Path) -> Path:
    base = Path(root or REPO_ROOT).resolve()
    return rel if rel.is_absolute() else base / rel


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "research").lower()).strip("-")
    return slug[:80] or "research"


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()


def _safe_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp_path, path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def _extract_visible_text(markup: str) -> Dict[str, str]:
    if BeautifulSoup is None:
        return {"title": "", "text": _clean_text(re.sub(r"<[^>]+>", " ", markup))}
    soup = BeautifulSoup(markup or "", "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    title = _clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    text = _clean_text(soup.get_text(" ", strip=True))
    return {"title": title, "text": text}


def _unwrap_duckduckgo_url(url: str) -> str:
    if "duckduckgo.com/l/" not in url:
        return url
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("uddg"):
        return str(query["uddg"][0])
    return url


def discover_sources(query: str, *, max_sources: int = 5) -> List[Dict[str, str]]:
    """Discover online sources through DuckDuckGo HTML, falling back to docs."""

    fallback = [
        {
            "title": "NumPy FFT documentation",
            "url": "https://numpy.org/doc/stable/reference/routines.fft.html",
            "snippet": "Reference for discrete Fourier transforms used in harmonic/spectral analysis.",
        },
        {
            "title": "SciPy signal processing",
            "url": "https://docs.scipy.org/doc/scipy/reference/signal.html",
            "snippet": "Signal-processing routines for filters, spectral analysis, and waveform work.",
        },
        {
            "title": "NIST/SEMATECH e-Handbook of Statistical Methods",
            "url": "https://www.itl.nist.gov/div898/handbook/",
            "snippet": "Statistical methods reference for measurement, uncertainty, and validation.",
        },
        {
            "title": "Wikipedia: Golden ratio",
            "url": "https://en.wikipedia.org/wiki/Golden_ratio",
            "snippet": "General reference on phi/golden ratio context.",
        },
        {
            "title": "Wikipedia: Signal-to-noise ratio",
            "url": "https://en.wikipedia.org/wiki/Signal-to-noise_ratio",
            "snippet": "General reference on separating signal from noise.",
        },
    ]
    if requests is None or BeautifulSoup is None:
        return fallback[:max_sources]

    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        rows: List[Dict[str, str]] = []
        for item in soup.select(".result__body"):
            title_el = item.select_one(".result__a")
            snippet_el = item.select_one(".result__snippet")
            href = title_el.get("href") if title_el else ""
            url = _unwrap_duckduckgo_url(str(href or ""))
            if not url.startswith("http"):
                continue
            rows.append(
                {
                    "title": _clean_text(title_el.get_text(" ", strip=True) if title_el else url),
                    "url": url,
                    "snippet": _clean_text(snippet_el.get_text(" ", strip=True) if snippet_el else ""),
                }
            )
            if len(rows) >= max_sources:
                break
        return rows or fallback[:max_sources]
    except Exception:
        return fallback[:max_sources]


def fetch_source(url: str, topic: str) -> Dict[str, Any]:
    if requests is None:
        return {"url": url, "success": False, "error": "requests unavailable"}
    started = time.perf_counter()
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if not resp.encoding or resp.encoding.lower() in {"iso-8859-1", "latin-1"}:
            resp.encoding = resp.apparent_encoding or "utf-8"
        content_type = str(resp.headers.get("content-type") or "")
        extracted = _extract_visible_text(resp.text)
        text = extracted["text"]
        summary = summarize_text(text, topic)
        return {
            "url": url,
            "success": True,
            "status_code": resp.status_code,
            "content_type": content_type,
            "title": extracted["title"] or url,
            "text_hash": _hash(text),
            "text_chars": len(text),
            "summary": summary,
            "excerpt": text[:900],
            "round_trip_ms": round((time.perf_counter() - started) * 1000, 2),
            "fetched_at": _utc_now(),
        }
    except Exception as exc:
        return {
            "url": url,
            "success": False,
            "error": str(exc),
            "round_trip_ms": round((time.perf_counter() - started) * 1000, 2),
            "fetched_at": _utc_now(),
        }


def summarize_text(text: str, topic: str, *, max_sentences: int = 3) -> str:
    text = _clean_text(text)
    if not text:
        return ""
    topic_terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", topic or "") if len(term) > 2]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    ranked: List[tuple[int, int, str]] = []
    for index, sentence in enumerate(sentences[:220]):
        lower = sentence.lower()
        score = sum(1 for term in topic_terms if term in lower)
        if score or index < 12:
            ranked.append((score, -index, sentence))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    picked = [_clean_text(row[2]) for row in ranked[:max_sentences] if row[2]]
    return " ".join(picked)[:1400]


def _wrap(draw: Any, text: str, width: int, font: Any) -> List[str]:
    lines: List[str] = []
    for paragraph in (text or "").splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def render_frame(path: Path, *, title: str, subtitle: str, body: str, footer: str) -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("Pillow is required for research cinema frames")
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1280, 720), color=(8, 14, 22))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("arial.ttf", 38) if Path("C:/Windows/Fonts/arial.ttf").exists() else ImageFont.load_default()
    body_font = ImageFont.truetype("arial.ttf", 24) if Path("C:/Windows/Fonts/arial.ttf").exists() else ImageFont.load_default()
    small_font = ImageFont.truetype("arial.ttf", 18) if Path("C:/Windows/Fonts/arial.ttf").exists() else ImageFont.load_default()

    draw.rectangle((0, 0, 1280, 92), fill=(12, 37, 54))
    draw.text((44, 28), title[:90], fill=(182, 245, 255), font=title_font)
    draw.text((46, 110), subtitle[:140], fill=(124, 224, 202), font=small_font)
    y = 162
    for line in _wrap(draw, body[:1800], 1160, body_font)[:15]:
        draw.text((56, y), line, fill=(227, 235, 239), font=body_font)
        y += 34
    draw.rectangle((0, 666, 1280, 720), fill=(10, 30, 43))
    draw.text((48, 684), footer[:170], fill=(158, 196, 210), font=small_font)
    image.save(path)


def compile_gif(frame_paths: Sequence[Path], gif_path: Path) -> bool:
    if Image is None or not frame_paths:
        return False
    frames = [Image.open(frame).convert("RGB") for frame in frame_paths if frame.exists()]
    if not frames:
        return False
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=1400, loop=0)
    return gif_path.exists()


def write_motion_html(path: Path, frame_paths: Sequence[Path], root: Path, title: str) -> None:
    slides = []
    for frame in frame_paths:
        rel = _rel(path.parent, frame)
        slides.append(f'<img src="{html.escape(rel)}" alt="research frame" />')
    body = "\n".join(slides)
    _write_text(
        path,
        f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>{html.escape(title)}</title>
<style>
body {{ margin:0; background:#081018; color:#e5f7ff; font-family:Arial,sans-serif; }}
.stage {{ min-height:100vh; display:grid; place-items:center; }}
img {{ width:min(100vw,1280px); height:auto; display:none; box-shadow:0 24px 80px rgba(0,0,0,.45); }}
img.active {{ display:block; }}
.bar {{ position:fixed; left:0; right:0; bottom:0; padding:10px 18px; background:rgba(0,0,0,.7); }}
</style>
</head>
<body>
<main class=\"stage\">{body}</main>
<div class=\"bar\">Aureon online research cinema - local replay, evidence only</div>
<script>
const frames = [...document.querySelectorAll('img')];
let i = 0;
function tick() {{
  frames.forEach((frame, idx) => frame.classList.toggle('active', idx === i));
  i = (i + 1) % Math.max(1, frames.length);
}}
tick();
setInterval(tick, 1400);
</script>
</body>
</html>
""",
    )


def make_paper(topic: str, sources: Sequence[Mapping[str, Any]]) -> str:
    usable = [source for source in sources if source.get("success")]
    lines = [
        f"# {topic}: Online Research Packet",
        "",
        f"Generated: {_utc_now()}",
        "",
        "## Abstract",
        "",
        (
            f"This paper assembles a source-linked working model for `{topic}`. "
            "Aureon treats the material as an evidence packet: online sources are fetched, "
            "summarized, hashed, rendered into a motion replay, and converted into a "
            "test/action handoff. The packet is designed to support reasoning and future "
            "validation, not to pretend that retrieved text alone proves a trading or "
            "scientific claim."
        ),
        "",
        "## Method",
        "",
        "- Discover or accept online source URLs.",
        "- Fetch each source with timestamp, HTTP status, round-trip time, and content hash.",
        "- Store bounded snippets and extractive summaries instead of full public page bodies.",
        "- Render source frames and compile a replay so the research path can be inspected.",
        "- Produce a test/action handoff with explicit unknowns and validation tasks.",
        "",
        "## Source Evidence",
        "",
    ]
    for idx, source in enumerate(usable, 1):
        lines.extend(
            [
                f"### Source {idx}: {source.get('title') or source.get('url')}",
                "",
                f"- URL: {source.get('url')}",
                f"- HTTP status: `{source.get('status_code')}`",
                f"- Text hash: `{str(source.get('text_hash') or '')[:16]}`",
                f"- Round trip: `{source.get('round_trip_ms')} ms`",
                "",
                str(source.get("summary") or "No extractive summary available."),
                "",
            ]
        )
    lines.extend(
        [
            "## Harmonic Nexus Score Working Formula",
            "",
            (
                "For implementation purposes, the Harmonic Nexus Score can be treated as a "
                "bounded evidence-coherence score rather than a mystical constant. A practical "
                "version is:"
            ),
            "",
            "`HNS = 100 * clamp(0, 1, 0.30*S + 0.25*C + 0.20*R + 0.15*F + 0.10*X)`",
            "",
            "- `S`: source strength and freshness.",
            "- `C`: harmonic/coherence agreement across Seer, Lyra, HNC, and market context.",
            "- `R`: repeatability under tests, replay, or historical validation.",
            "- `F`: signal-to-noise and friction-adjusted feasibility.",
            "- `X`: contradiction handling, vetoes, and counter-intelligence pressure.",
            "",
            "## Data Ingest To Test To Action",
            "",
            "1. Data ingest: fetch source, hash it, cite it, and summarize only bounded excerpts.",
            "2. Test: convert claims into measurable checks, replay frames, and benchmark rows.",
            "3. Action: publish a non-mutating action packet until the relevant executor/runtime path is already authorized.",
            "",
            "## Limitations",
            "",
            "- Online snippets are context, not full reproduction of source material.",
            "- The score formula is an Aureon operational model and must be calibrated against outcomes.",
            "- Any trading action still depends on existing live executor, lifecycle, and risk controls.",
            "",
            "## Test/Action Handoff",
            "",
            "- Add unit tests for source freshness, hash integrity, frame generation, and paper output.",
            "- Feed the score components into Seer/Lyra/HNC as explainable features.",
            "- Compare HNS changes against real outcome evidence before promoting confidence.",
            "",
        ]
    )
    return "\n".join(lines)


def _module_slug(slug: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", slug.replace("-", "_")).strip("_") or "research_model"


def make_score_model_code(topic: str, slug: str, source_count: int) -> str:
    """Generate a small deterministic score module from the research packet."""

    class_name = "".join(part.capitalize() for part in _module_slug(slug).split("_")) + "Inputs"
    return f'''"""Generated Harmonic Nexus score model for {topic}.

This file was generated from the online research cinema packet. It is a
deterministic helper, not trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


SOURCE_COUNT = {int(source_count)}
TOPIC = {topic!r}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class {class_name}:
    source_strength: float
    coherence_agreement: float
    repeatability: float
    friction_feasibility: float
    contradiction_handling: float

    def normalized(self) -> "{class_name}":
        return {class_name}(
            source_strength=_clamp01(self.source_strength),
            coherence_agreement=_clamp01(self.coherence_agreement),
            repeatability=_clamp01(self.repeatability),
            friction_feasibility=_clamp01(self.friction_feasibility),
            contradiction_handling=_clamp01(self.contradiction_handling),
        )


def harmonic_nexus_score(inputs: {class_name}) -> float:
    """Return 0-100 bounded evidence/coherence score."""
    n = inputs.normalized()
    raw = (
        0.30 * n.source_strength
        + 0.25 * n.coherence_agreement
        + 0.20 * n.repeatability
        + 0.15 * n.friction_feasibility
        + 0.10 * n.contradiction_handling
    )
    return round(100.0 * _clamp01(raw), 6)


def score_breakdown(inputs: {class_name}) -> Dict[str, float]:
    n = inputs.normalized()
    return {{
        "source_strength": round(30.0 * n.source_strength, 6),
        "coherence_agreement": round(25.0 * n.coherence_agreement, 6),
        "repeatability": round(20.0 * n.repeatability, 6),
        "friction_feasibility": round(15.0 * n.friction_feasibility, 6),
        "contradiction_handling": round(10.0 * n.contradiction_handling, 6),
        "score": harmonic_nexus_score(n),
    }}


def build_default_inputs() -> {class_name}:
    """Build conservative defaults from packet source count."""
    source_strength = min(1.0, SOURCE_COUNT / 5.0)
    return {class_name}(
        source_strength=source_strength,
        coherence_agreement=0.5,
        repeatability=0.0,
        friction_feasibility=0.5,
        contradiction_handling=0.5,
    )


__all__ = [
    "{class_name}",
    "harmonic_nexus_score",
    "score_breakdown",
    "build_default_inputs",
]
'''


def make_score_model_test_code(module_path: str, class_name: str) -> str:
    return f'''from {module_path} import {class_name}, harmonic_nexus_score, score_breakdown, build_default_inputs


def test_harmonic_nexus_score_bounds_inputs():
    score = harmonic_nexus_score({class_name}(2.0, -1.0, 0.5, 0.5, 0.5))
    assert 0.0 <= score <= 100.0


def test_harmonic_nexus_score_full_strength_is_100():
    score = harmonic_nexus_score({class_name}(1.0, 1.0, 1.0, 1.0, 1.0))
    assert score == 100.0


def test_harmonic_nexus_breakdown_matches_score():
    inputs = {class_name}(1.0, 0.5, 0.25, 0.5, 1.0)
    breakdown = score_breakdown(inputs)
    assert breakdown["score"] == harmonic_nexus_score(inputs)
    assert set(breakdown) == {{
        "source_strength",
        "coherence_agreement",
        "repeatability",
        "friction_feasibility",
        "contradiction_handling",
        "score",
    }}


def test_default_inputs_are_conservative():
    score = harmonic_nexus_score(build_default_inputs())
    assert 0.0 <= score < 100.0
'''


def make_coding_handoff(topic: str, module_rel: str, test_rel: str, source_count: int) -> str:
    return f"""# {topic}: Coding Handoff

Generated: {_utc_now()}

## Created Files

- `{module_rel}`
- `{test_rel}`

## Purpose

This coding handoff converts the online research packet into a deterministic
Harmonic Nexus Score helper that can be imported, tested, and later connected
to Seer/Lyra/HNC feature rows.

## Inputs

- source_strength
- coherence_agreement
- repeatability
- friction_feasibility
- contradiction_handling

## Evidence

- online source count: `{source_count}`
- authority: `research_code_artifact_only`
- trading mutation: `none`

## Next Test Action

Run the generated pytest file, then wire the score only as an explainable
feature until outcome calibration proves its value.
"""


def _write_via_architect(root: Path, rel: str, content: str) -> Dict[str, Any]:
    """Write a file through QueenCodeArchitect when available, else fallback."""

    try:
        from aureon.queen.queen_code_architect import QueenCodeArchitect

        architect = QueenCodeArchitect(repo_path=str(root))
        ok = bool(architect.write_file(rel, content, backup=True))
        path = _rooted(root, Path(rel))
        return {
            "path": rel,
            "ok": ok and path.exists(),
            "bytes": len(content.encode("utf-8")),
            "authoring_path": "QueenCodeArchitect.write_file",
        }
    except Exception as exc:
        path = _rooted(root, Path(rel))
        _write_text(path, content)
        return {
            "path": rel,
            "ok": path.exists(),
            "bytes": len(content.encode("utf-8")),
            "authoring_path": "direct_safe_research_writer",
            "architect_error": str(exc)[:240],
        }


def write_generated_code_artifacts(
    *,
    root: Path,
    topic: str,
    slug: str,
    source_count: int,
    trace_id: Optional[str],
    query_id: Optional[str],
    query: str,
) -> Dict[str, Any]:
    """Generate model/test/handoff files from a research packet."""

    module_name = f"{_module_slug(slug)}_model"
    class_name = "".join(part.capitalize() for part in _module_slug(slug).split("_")) + "Inputs"
    package_init = "aureon/generated/__init__.py"
    subpackage_init = "aureon/generated/research_cinema/__init__.py"
    tests_init = "tests/generated/__init__.py"
    module_rel = f"aureon/generated/research_cinema/{module_name}.py"
    test_rel = f"tests/generated/test_{module_name}.py"
    handoff_rel = f"docs/research/{slug}_coding_handoff.md"
    manifest_rel = f"state/online_research_cinema/{slug}/generated_code_manifest.json"

    writes = [
        _write_via_architect(root, package_init, '"""Generated Aureon artifacts."""\n'),
        _write_via_architect(root, subpackage_init, '"""Research cinema generated helpers."""\n'),
        _write_via_architect(root, tests_init, '"""Generated test artifacts."""\n'),
        _write_via_architect(root, module_rel, make_score_model_code(topic, slug, source_count)),
        _write_via_architect(
            root,
            test_rel,
            make_score_model_test_code(f"aureon.generated.research_cinema.{module_name}", class_name),
        ),
        _write_via_architect(root, handoff_rel, make_coding_handoff(topic, module_rel, test_rel, source_count)),
    ]
    for row in writes:
        publish_search_event(
            phase="coding_file_written",
            source_system="online_research_cinema",
            query=query,
            trace_id=trace_id,
            query_id=query_id,
            source=row.get("authoring_path"),
            result_count=1 if row.get("ok") else 0,
            status="success" if row.get("ok") else "error",
            metadata={"path": row.get("path"), "bytes": row.get("bytes")},
            root=root,
        )

    manifest = {
        "generated_at": _utc_now(),
        "topic": topic,
        "status": "coding_artifacts_ready" if all(row.get("ok") for row in writes) else "coding_artifacts_attention",
        "module_import": f"aureon.generated.research_cinema.{module_name}",
        "model_class": class_name,
        "generated_files": writes,
        "test_command": f"python -m pytest {test_rel} -q",
        "authority": "research_code_artifact_only",
        "no_external_mutation": True,
        "no_trading_gate_bypass": True,
    }
    _safe_write_json(_rooted(root, Path(manifest_rel)), manifest)
    publish_search_event(
        phase="coding_handoff_ready",
        source_system="online_research_cinema",
        query=query,
        trace_id=trace_id,
        query_id=query_id,
        source="research_code_generator",
        result_count=sum(1 for row in writes if row.get("ok")),
        status=manifest["status"],
        metadata={"manifest": manifest_rel, "test_command": manifest["test_command"]},
        root=root,
    )
    return manifest


def build_online_research_cinema(
    *,
    topic: str,
    query: Optional[str] = None,
    urls: Optional[Sequence[str]] = None,
    max_sources: int = 5,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build the online evidence packet, paper, and motion replay."""

    root_path = Path(root or REPO_ROOT).resolve()
    topic_query = query or topic
    trace_event = publish_search_event(
        phase="online_research_goal_received",
        source_system="online_research_cinema",
        query=topic_query,
        source="operator_topic",
        status="received",
        metadata={"topic": topic},
        root=root_path,
    )
    trace_id = trace_event.get("trace_id")
    query_id = trace_event.get("query_id")

    discovered = [{"title": url, "url": url, "snippet": "operator supplied URL"} for url in (urls or [])]
    if not discovered:
        discovered = discover_sources(topic_query, max_sources=max_sources)
    discovered = discovered[: max(1, int(max_sources or 5))]

    for source in discovered:
        publish_search_event(
            phase="online_source_discovered",
            source_system="online_research_cinema",
            query=topic_query,
            url=source.get("url"),
            trace_id=trace_id,
            query_id=query_id,
            source="online_discovery",
            status="success",
            metadata={"title": source.get("title"), "snippet": source.get("snippet")},
            root=root_path,
        )

    fetched: List[Dict[str, Any]] = []
    for source in discovered:
        row = fetch_source(str(source.get("url") or ""), topic)
        row["discovery_title"] = source.get("title")
        row["discovery_snippet"] = source.get("snippet")
        fetched.append(row)
        publish_search_event(
            phase="online_source_fetched",
            source_system="online_research_cinema",
            query=topic_query,
            url=row.get("url"),
            trace_id=trace_id,
            query_id=query_id,
            source="requests",
            result_count=1 if row.get("success") else 0,
            status="success" if row.get("success") else "error",
            error=row.get("error"),
            metadata={
                "http_status": row.get("status_code"),
                "round_trip_ms": row.get("round_trip_ms"),
                "text_hash": row.get("text_hash"),
            },
            root=root_path,
        )
        if row.get("success"):
            publish_search_event(
                phase="online_source_summarized",
                source_system="online_research_cinema",
                query=topic_query,
                url=row.get("url"),
                trace_id=trace_id,
                query_id=query_id,
                source="extractive_summary",
                result_count=1,
                status="success",
                metadata={"summary_chars": len(str(row.get("summary") or ""))},
                root=root_path,
            )

    slug = _slug(topic)
    out_dir = _rooted(root_path, Path("state/online_research_cinema") / slug)
    public_dir = _rooted(root_path, Path("frontend/public/online_research_cinema") / slug)
    frame_paths: List[Path] = []
    usable = [row for row in fetched if row.get("success")]

    if Image is not None:
        title_frame = out_dir / "frames" / "000_title.png"
        render_frame(
            title_frame,
            title=topic,
            subtitle="Online data ingest -> research cinema -> paper -> test/action handoff",
            body=f"Sources discovered: {len(discovered)}\nSources fetched: {len(usable)}\nTrace: {trace_id}",
            footer="Aureon Research Cinema | evidence packet",
        )
        frame_paths.append(title_frame)
        for index, row in enumerate(usable, 1):
            frame = out_dir / "frames" / f"{index:03d}_source.png"
            render_frame(
                frame,
                title=f"Source {index}: {row.get('title') or row.get('discovery_title') or 'online source'}",
                subtitle=str(row.get("url") or ""),
                body=str(row.get("summary") or row.get("excerpt") or ""),
                footer=f"status={row.get('status_code')} hash={str(row.get('text_hash') or '')[:16]} rt={row.get('round_trip_ms')}ms",
            )
            frame_paths.append(frame)
            publish_search_event(
                phase="research_frame_rendered",
                source_system="online_research_cinema",
                query=topic_query,
                url=row.get("url"),
                trace_id=trace_id,
                query_id=query_id,
                source="pillow_frame",
                result_count=1,
                status="success",
                metadata={"frame": _rel(root_path, frame)},
                root=root_path,
            )

    gif_path = out_dir / "motion.gif"
    gif_ok = compile_gif(frame_paths, gif_path) if frame_paths else False
    html_path = out_dir / "motion.html"
    if frame_paths:
        write_motion_html(html_path, frame_paths, root_path, topic)
        public_dir.mkdir(parents=True, exist_ok=True)
        for frame in frame_paths:
            target = public_dir / frame.name
            target.write_bytes(frame.read_bytes())
        public_html = public_dir / "motion.html"
        write_motion_html(public_html, [public_dir / frame.name for frame in frame_paths], root_path, topic)

    publish_search_event(
        phase="research_motion_compiled",
        source_system="online_research_cinema",
        query=topic_query,
        trace_id=trace_id,
        query_id=query_id,
        source="pillow_gif_html_replay",
        result_count=len(frame_paths),
        status="success" if frame_paths else "attention",
        metadata={"gif_path": _rel(root_path, gif_path), "gif_created": gif_ok, "html_path": _rel(root_path, html_path)},
        root=root_path,
    )

    paper_text = make_paper(topic, fetched)
    paper_path = _rooted(root_path, Path("docs/research") / f"{slug}_online_research_packet.md")
    _write_text(paper_path, paper_text)
    publish_search_event(
        phase="research_paper_drafted",
        source_system="online_research_cinema",
        query=topic_query,
        trace_id=trace_id,
        query_id=query_id,
        source="paper_generator",
        result_count=1,
        status="success",
        metadata={"paper_path": _rel(root_path, paper_path), "paper_chars": len(paper_text)},
        root=root_path,
    )

    publish_search_event(
        phase="coding_brief_created",
        source_system="online_research_cinema",
        query=topic_query,
        trace_id=trace_id,
        query_id=query_id,
        source="research_to_code_handoff",
        result_count=1,
        status="success",
        metadata={"topic": topic, "source_count": len(usable)},
        root=root_path,
    )
    coding_manifest = write_generated_code_artifacts(
        root=root_path,
        topic=topic,
        slug=slug,
        source_count=len(usable),
        trace_id=trace_id,
        query_id=query_id,
        query=topic_query,
    )

    source_rows = [
        {
            "title": row.get("title") or row.get("discovery_title"),
            "url": row.get("url"),
            "success": row.get("success"),
            "status_code": row.get("status_code"),
            "round_trip_ms": row.get("round_trip_ms"),
            "text_hash": row.get("text_hash"),
            "text_chars": row.get("text_chars"),
            "summary": row.get("summary"),
            "excerpt": str(row.get("excerpt") or "")[:360],
            "error": row.get("error"),
        }
        for row in fetched
    ]
    motion_picture = {
        "gif_path": _rel(root_path, gif_path),
        "html_path": _rel(root_path, html_path),
        "public_html": f"/online_research_cinema/{slug}/motion.html",
        "frame_paths": [_rel(root_path, frame) for frame in frame_paths],
    }
    try:
        from aureon.search.research_metacognition import build_research_metacognition

        metacognition = build_research_metacognition(
            topic=topic,
            query=topic_query,
            source_rows=source_rows,
            paper_path=_rel(root_path, paper_path),
            paper_text=paper_text,
            motion_picture=motion_picture,
            coding_manifest=coding_manifest,
            trace_id=trace_id,
            query_id=query_id,
            root=root_path,
        )
    except Exception as exc:
        publish_search_event(
            phase="metacognition_failed",
            source_system="online_research_cinema",
            query=topic_query,
            trace_id=trace_id,
            query_id=query_id,
            source="research_metacognition",
            result_count=0,
            status="error",
            error=str(exc),
            metadata={"topic": topic},
            root=root_path,
        )
        metacognition = {
            "status": "research_metacognition_attention",
            "error": str(exc)[:500],
            "summary": {},
        }
    meta_summary = metacognition.get("summary", {}) if isinstance(metacognition, dict) else {}
    manifest: Dict[str, Any] = {
        "schema_version": "aureon-online-research-cinema-v1",
        "status": "online_research_cinema_ready" if usable and paper_path.exists() else "online_research_cinema_attention",
        "generated_at": _utc_now(),
        "mode": "real_online_sources_bounded_public_evidence",
        "topic": topic,
        "query": topic_query,
        "summary": {
            "discovered_source_count": len(discovered),
            "fetched_source_count": len(usable),
            "frame_count": len(frame_paths),
            "motion_gif_created": gif_ok,
            "motion_html_created": html_path.exists(),
            "paper_created": paper_path.exists(),
            "coding_artifacts_created": coding_manifest.get("status") == "coding_artifacts_ready",
            "generated_file_count": len(coding_manifest.get("generated_files") or []),
            "metacognition_active": metacognition.get("status") == "research_metacognition_active",
            "metacognitive_concept_count": meta_summary.get("concept_count"),
            "metacognitive_route_count": meta_summary.get("organism_route_count"),
            "understanding_published": bool(metacognition.get("understanding_hash")),
            "test_action_handoff_ready": bool(usable and paper_path.exists()),
            "no_credentials_read": True,
            "no_external_mutation": True,
            "public_full_page_bodies_stored": False,
        },
        "source_rows": source_rows,
        "motion_picture": motion_picture,
        "paper": {
            "path": _rel(root_path, paper_path),
            "title": f"{topic}: Online Research Packet",
            "chars": len(paper_text),
        },
        "coding_handoff": coding_manifest,
        "metacognition": metacognition,
        "test_action_handoff": {
            "ingest": "online source rows are fetched, timestamped, hashed, and summarized",
            "test": "source freshness, hash integrity, frame generation, and paper generation can be asserted",
            "action": "publish action packets only through existing authorized runtime paths",
        },
        "manual_boundaries": [
            "online source bodies are summarized and hashed; public artifacts do not store full page bodies",
            "screenshots/frames are research replay evidence, not trading authority",
            "credentials and API keys are not read",
            "external websites are fetched through ordinary GET requests only; no form submission or account mutation",
        ],
        "source_paths": {
            "state_manifest": STATE_MANIFEST.as_posix(),
            "public_manifest": PUBLIC_MANIFEST.as_posix(),
            "docs_manifest": DOCS_INDEX.as_posix(),
            "paper": _rel(root_path, paper_path),
        },
    }
    _safe_write_json(_rooted(root_path, STATE_MANIFEST), manifest)
    _safe_write_json(_rooted(root_path, PUBLIC_MANIFEST), manifest)
    _safe_write_json(_rooted(root_path, DOCS_INDEX), manifest)
    _safe_write_json(out_dir / "manifest.json", manifest)
    return manifest


__all__ = [
    "build_online_research_cinema",
    "discover_sources",
    "fetch_source",
    "make_paper",
    "write_generated_code_artifacts",
]
