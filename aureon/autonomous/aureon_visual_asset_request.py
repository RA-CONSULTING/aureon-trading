from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_PATH = Path("state/aureon_visual_asset_request_last_run.json")
DEFAULT_AUDIT_JSON = Path("docs/audits/aureon_visual_asset_request.json")
DEFAULT_AUDIT_MD = Path("docs/audits/aureon_visual_asset_request.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_visual_asset_request.json")
DEFAULT_PUBLIC_ASSET_DIR = Path("frontend/public/aureon_visual_artifacts")


def _default_root() -> Path:
    return Path.cwd().resolve() if (Path.cwd() / "aureon").exists() else REPO_ROOT


def _rooted(root: Path, rel_path: Path) -> Path:
    candidate = Path(rel_path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str, default: str = "visual_asset") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return (slug or default)[:48]


def _infer_subject(goal: str) -> str:
    lower = goal.lower()
    patterns = [
        r"\b(?:image|picture|illustration|drawing|art|graphic|visual)\s+(?:of|for)\s+(?:a|an|the)?\s*([a-zA-Z0-9 _-]{2,80})",
        r"\b(?:draw|drwaw|generate|create|make|render)\s+(?:me\s+)?(?:a|an|the)?\s*(?:image|picture|illustration|drawing|art|graphic|visual)?\s*(?:of|for)?\s*(?:a|an|the)?\s*([a-zA-Z0-9 _-]{2,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            subject = re.split(r"\b(?:and|then|open|show|display|view|save)\b", match.group(1))[0]
            subject = subject.strip(" ._-")
            if subject:
                return subject
    return "requested visual"


def _cat_svg(title: str, prompt: str) -> str:
    safe_title = html.escape(title[:80])
    safe_prompt = html.escape(prompt[:180])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-label="{safe_title}">
  <rect width="1024" height="1024" fill="#f7efe3"/>
  <circle cx="512" cy="548" r="262" fill="#f3b36b"/>
  <path d="M304 360 L250 174 L424 290 Z" fill="#f3b36b"/>
  <path d="M720 360 L774 174 L600 290 Z" fill="#f3b36b"/>
  <path d="M315 336 L286 230 L384 298 Z" fill="#f8d0a1"/>
  <path d="M709 336 L738 230 L640 298 Z" fill="#f8d0a1"/>
  <ellipse cx="416" cy="500" rx="42" ry="58" fill="#20252b"/>
  <ellipse cx="608" cy="500" rx="42" ry="58" fill="#20252b"/>
  <circle cx="431" cy="479" r="12" fill="#fff7e8"/>
  <circle cx="623" cy="479" r="12" fill="#fff7e8"/>
  <path d="M512 544 L470 604 L554 604 Z" fill="#cf6679"/>
  <path d="M512 604 C492 646 446 660 406 646" fill="none" stroke="#3a2923" stroke-width="16" stroke-linecap="round"/>
  <path d="M512 604 C532 646 578 660 618 646" fill="none" stroke="#3a2923" stroke-width="16" stroke-linecap="round"/>
  <path d="M258 570 C348 545 410 545 482 572" fill="none" stroke="#3a2923" stroke-width="12" stroke-linecap="round"/>
  <path d="M258 638 C352 606 414 602 480 624" fill="none" stroke="#3a2923" stroke-width="12" stroke-linecap="round"/>
  <path d="M766 570 C676 545 614 545 542 572" fill="none" stroke="#3a2923" stroke-width="12" stroke-linecap="round"/>
  <path d="M766 638 C672 606 610 602 544 624" fill="none" stroke="#3a2923" stroke-width="12" stroke-linecap="round"/>
  <path d="M382 724 C458 760 566 764 642 724" fill="none" stroke="#cc7c40" stroke-width="20" stroke-linecap="round"/>
  <text x="512" y="910" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" fill="#3a2923">{safe_title}</text>
  <desc>{safe_prompt}</desc>
</svg>
"""


def _generic_svg(title: str, prompt: str) -> str:
    safe_title = html.escape(title[:80])
    safe_prompt = html.escape(prompt[:180])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-label="{safe_title}">
  <rect width="1024" height="1024" fill="#f5f7f2"/>
  <circle cx="512" cy="512" r="300" fill="#7db7a6"/>
  <path d="M232 638 C346 346 678 346 792 638" fill="none" stroke="#253238" stroke-width="38" stroke-linecap="round"/>
  <path d="M326 620 C418 514 606 514 698 620" fill="none" stroke="#f0c96d" stroke-width="32" stroke-linecap="round"/>
  <circle cx="512" cy="512" r="74" fill="#253238"/>
  <text x="512" y="900" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" fill="#253238">{safe_title}</text>
  <desc>{safe_prompt}</desc>
</svg>
"""


def _build_svg(subject: str, goal: str) -> str:
    if "cat" in subject.lower() or "cat" in goal.lower():
        return _cat_svg("Aureon visual artifact: cat", goal)
    return _generic_svg(f"Aureon visual artifact: {subject}", goal)


def _write_text(path: Path, content: str) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "ok": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _make_markdown(report: Dict[str, Any]) -> str:
    files = report.get("output_files", [])
    lines = [
        "# Aureon Visual Asset Request",
        "",
        f"- status: {report.get('status')}",
        f"- generated_at: {report.get('generated_at')}",
        f"- subject: {report.get('subject')}",
        f"- public_url: {report.get('public_url')}",
        f"- open_requested: {report.get('open_requested')}",
        "",
        "## Evidence",
        f"- who: {report.get('who')}",
        f"- what: {report.get('what')}",
        f"- where: {report.get('where')}",
        f"- how: {report.get('how')}",
        "",
        "## Output Files",
    ]
    for item in files:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def build_and_write_visual_asset_request(
    goal: str,
    *,
    root: Optional[Path] = None,
    open_requested: Optional[bool] = None,
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    prompt = str(goal or "").strip()
    subject = _infer_subject(prompt)
    digest = hashlib.sha256(prompt.encode("utf-8", errors="replace")).hexdigest()[:12]
    asset_name = f"{_slugify(subject)}_{digest}.svg"
    asset_rel = DEFAULT_PUBLIC_ASSET_DIR / asset_name
    asset_path = _rooted(root, asset_rel)
    svg = _build_svg(subject, prompt)
    asset_write = _write_text(asset_path, svg)
    public_url = f"/aureon_visual_artifacts/{asset_name}"
    open_flag = bool(open_requested) if open_requested is not None else bool(
        re.search(r"\b(?:open|show|display|view)\b", prompt.lower())
    )

    output_files = [
        asset_rel.as_posix(),
        DEFAULT_STATE_PATH.as_posix(),
        DEFAULT_AUDIT_JSON.as_posix(),
        DEFAULT_AUDIT_MD.as_posix(),
        DEFAULT_PUBLIC_JSON.as_posix(),
    ]
    generated_at = _utc_now()
    report: Dict[str, Any] = {
        "schema_version": "aureon-visual-asset-request-v1",
        "status": "visual_asset_ready" if asset_write["ok"] else "visual_asset_failed",
        "generated_at": generated_at,
        "prompt": prompt,
        "subject": subject,
        "asset_kind": "svg",
        "asset_path": str(asset_path),
        "public_url": public_url,
        "open_requested": open_flag,
        "output_files": output_files,
        "target_files": output_files,
        "who": {
            "client": "operator dashboard prompt",
            "router": "aureon.core.goal_execution_engine",
            "artifact_worker": "aureon.autonomous.aureon_visual_asset_request",
        },
        "what": {
            "deliverable": "public SVG visual artifact plus evidence packet",
            "subject": subject,
            "safe_format": "svg_static_no_external_calls",
        },
        "where": {
            "repo_root": str(root),
            "asset_path": str(asset_path),
            "public_url": public_url,
        },
        "when": {
            "generated_at": generated_at,
        },
        "how": {
            "route": "visual_asset_request",
            "safety": "no live trading, no credential access, no external mutation",
            "handover": "dashboard may show the public_url and desktop handoff may open it when armed",
        },
        "act": {
            "asset_written": bool(asset_write["ok"]),
            "evidence_written": True,
            "open_requested": open_flag,
        },
        "write_info": {
            "writer": "AureonVisualAssetRequest",
            "asset_write": asset_write,
        },
        "summary": {
            "output_file_count": len(output_files),
            "asset_written": bool(asset_write["ok"]),
            "open_requested": open_flag,
            "client_visible_artifact": bool(asset_write["ok"]),
        },
    }

    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    writes = [
        _write_text(_rooted(root, DEFAULT_STATE_PATH), payload),
        _write_text(_rooted(root, DEFAULT_AUDIT_JSON), payload),
        _write_text(_rooted(root, DEFAULT_AUDIT_MD), _make_markdown(report)),
        _write_text(_rooted(root, DEFAULT_PUBLIC_JSON), payload),
    ]
    report["write_info"]["evidence_writes"] = writes

    payload = json.dumps(report, indent=2, sort_keys=True, default=str)
    for rel in (DEFAULT_STATE_PATH, DEFAULT_AUDIT_JSON, DEFAULT_PUBLIC_JSON):
        _write_text(_rooted(root, rel), payload)
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build an Aureon visual asset request/artifact.")
    parser.add_argument("goal", nargs="*", default=["draw me an image of a cat"])
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else None
    result = build_and_write_visual_asset_request(" ".join(args.goal), root=root)
    print(json.dumps(result, indent=2, sort_keys=True, default=str) if args.json else _make_markdown(result))


if __name__ == "__main__":
    main()
