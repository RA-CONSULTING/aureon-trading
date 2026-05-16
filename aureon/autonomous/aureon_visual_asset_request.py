from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aureon.autonomous.aureon_artifact_quality_gate import (
    DEFAULT_PUBLIC_QUALITY_JSON,
    build_artifact_quality_report,
    write_artifact_quality_report,
)


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
        r"\b(?:image|picture|illustration|drawing|art|graphic|visual|video|clip|animation)\s+(?:of|for)\s+(?:a|an|the)?\s*([a-zA-Z0-9 _-]{2,80})",
        r"\b(?:draw|drwaw|generate|create|make|render)\s+(?:me\s+)?(?:a|an|the)?\s*(?:image|picture|illustration|drawing|art|graphic|visual|video|clip|animation)?\s*(?:of|for)?\s*(?:a|an|the)?\s*([a-zA-Z0-9 _-]{2,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            subject = re.split(r"\b(?:and|then|open|show|display|view|save|to|with)\b", match.group(1))[0]
            subject = subject.strip(" ._-")
            if subject:
                return subject
    return "requested visual"


def _infer_asset_kind(goal: str) -> str:
    lower = goal.lower()
    if re.search(r"\b(?:video|clip|animation|mp4)\b", lower):
        return "mp4"
    return "svg"


def _infer_duration_seconds(goal: str) -> int:
    lower = goal.lower()
    match = re.search(r"\b(\d{1,2})\s*(?:second|seconds|sec|secs|s)\b", lower)
    if not match:
        return 10 if _infer_asset_kind(goal) == "mp4" else 0
    return max(1, min(30, int(match.group(1))))


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


def _dog_svg(title: str, prompt: str) -> str:
    safe_title = html.escape(title[:80])
    safe_prompt = html.escape(prompt[:180])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024" role="img" aria-label="{safe_title}">
  <rect width="1024" height="1024" fill="#eef7f3"/>
  <circle cx="782" cy="158" r="92" fill="#f7c85f"/>
  <rect x="0" y="700" width="1024" height="324" fill="#8bcf95"/>
  <ellipse cx="520" cy="566" rx="260" ry="178" fill="#a87345"/>
  <circle cx="340" cy="476" r="138" fill="#b98252"/>
  <path d="M247 370 C190 258 304 238 336 368 Z" fill="#6b432b"/>
  <path d="M412 374 C484 272 568 346 452 440 Z" fill="#6b432b"/>
  <ellipse cx="302" cy="470" rx="28" ry="42" fill="#20252b"/>
  <circle cx="311" cy="455" r="8" fill="#fff7e8"/>
  <ellipse cx="220" cy="536" rx="64" ry="44" fill="#d8a477"/>
  <circle cx="190" cy="528" r="18" fill="#20252b"/>
  <path d="M226 584 C268 624 328 626 370 586" fill="none" stroke="#3a2923" stroke-width="15" stroke-linecap="round"/>
  <path d="M734 524 C850 440 876 534 782 602" fill="none" stroke="#6b432b" stroke-width="36" stroke-linecap="round"/>
  <rect x="384" y="684" width="46" height="176" rx="23" fill="#6b432b"/>
  <rect x="584" y="684" width="46" height="176" rx="23" fill="#6b432b"/>
  <ellipse cx="408" cy="864" rx="56" ry="24" fill="#3a2923"/>
  <ellipse cx="610" cy="864" rx="56" ry="24" fill="#3a2923"/>
  <path d="M228 754 C366 724 562 724 706 754" fill="none" stroke="#5aa467" stroke-width="14" stroke-linecap="round"/>
  <text x="512" y="940" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" fill="#253238">{safe_title}</text>
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
    if "dog" in subject.lower() or "dog" in goal.lower():
        return _dog_svg("Aureon visual artifact: dog", goal)
    return _generic_svg(f"Aureon visual artifact: {subject}", goal)


def _write_dog_video(path: Path, title: str, prompt: str, duration_s: int) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cv2
        import numpy as np
    except Exception as exc:  # pragma: no cover - exercised only when optional codec stack is missing
        fallback = _build_svg(title, prompt)
        fallback_path = path.with_suffix(".svg")
        return {**_write_text(fallback_path, fallback), "fallback_path": str(fallback_path), "error": str(exc)}

    webm_path = path.with_suffix(".webm")
    gif_path = path.with_name(f"{path.stem}_preview.gif")
    html_path = path.with_name(f"{path.stem}_preview.html")
    width, height, fps = 960, 540, 24
    frame_count = max(1, int(duration_s * fps))
    mp4_writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    webm_writer = cv2.VideoWriter(str(webm_path), cv2.VideoWriter_fourcc(*"VP80"), fps, (width, height))
    if not mp4_writer.isOpened():
        raise RuntimeError(f"Could not open MP4 writer for {path}")

    gif_frames = []
    try:
        from PIL import Image

        pil_image = Image
    except Exception:
        pil_image = None

    safe_title = title[:70]
    for index in range(frame_count):
        t = index / max(1, frame_count - 1)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (238, 246, 241)
        cv2.rectangle(frame, (0, 360), (width, height), (100, 178, 110), -1)
        cv2.circle(frame, (780, 92), 46, (89, 197, 247), -1)
        x = int(130 + 540 * t)
        y = 320 + int(12 * np.sin(t * np.pi * 4))
        cv2.ellipse(frame, (x + 170, y), (150, 74), 0, 0, 360, (70, 118, 168), -1)
        cv2.circle(frame, (x + 52, y - 44), 70, (82, 130, 180), -1)
        cv2.ellipse(frame, (x + 8, y - 86), (34, 64), -25, 0, 360, (43, 67, 107), -1)
        cv2.ellipse(frame, (x + 96, y - 90), (34, 64), 28, 0, 360, (43, 67, 107), -1)
        cv2.circle(frame, (x + 30, y - 50), 10, (35, 37, 40), -1)
        cv2.circle(frame, (x + 34, y - 54), 3, (255, 255, 255), -1)
        cv2.ellipse(frame, (x - 8, y - 18), (36, 24), 0, 0, 360, (112, 164, 214), -1)
        cv2.circle(frame, (x - 28, y - 20), 8, (35, 37, 40), -1)
        cv2.line(frame, (x + 286, y - 28), (x + 372, y - 84), (43, 67, 107), 22, cv2.LINE_AA)
        for leg_x, phase in ((x + 110, 0.0), (x + 225, 0.5)):
            swing = int(20 * np.sin((t + phase) * np.pi * 4))
            cv2.line(frame, (leg_x, y + 54), (leg_x + swing, y + 132), (43, 67, 107), 19, cv2.LINE_AA)
            cv2.ellipse(frame, (leg_x + swing + 12, y + 140), (34, 13), 0, 0, 360, (35, 37, 40), -1)
        cv2.putText(frame, safe_title, (36, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.86, (38, 50, 56), 2, cv2.LINE_AA)
        cv2.putText(frame, f"{duration_s}s Aureon public artifact", (36, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (60, 76, 83), 2, cv2.LINE_AA)
        mp4_writer.write(frame)
        if webm_writer.isOpened():
            webm_writer.write(frame)
        if pil_image is not None and index % 2 == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gif_frames.append(pil_image.fromarray(rgb).resize((720, 405), pil_image.Resampling.LANCZOS))
    mp4_writer.release()
    if webm_writer.isOpened():
        webm_writer.release()

    gif_ok = False
    if gif_frames:
        gif_frames[0].save(
            gif_path,
            save_all=True,
            append_images=gif_frames[1:],
            duration=max(1, int(1000 / 12)),
            loop=0,
            optimize=True,
        )
        gif_ok = gif_path.exists()

    html_doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title[:80])}</title>
    <style>
      body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #101820; color: #f5f7f2; font-family: Arial, sans-serif; }}
      main {{ width: min(960px, calc(100vw - 32px)); }}
      video, img {{ display: block; width: 100%; max-height: 72vh; background: #000; border: 1px solid #33424d; }}
      p {{ margin: 12px 0 0; color: #c7d2da; font-size: 14px; }}
      a {{ color: #8bd3ff; }}
    </style>
  </head>
  <body>
    <main>
      <video controls autoplay muted loop playsinline poster="/aureon_visual_artifacts/{gif_path.name}">
        <source src="/aureon_visual_artifacts/{webm_path.name}" type="video/webm" />
        <source src="/aureon_visual_artifacts/{path.name}" type="video/mp4" />
      </video>
      <p>If the video element does not play, use the animated <a href="/aureon_visual_artifacts/{gif_path.name}">GIF preview</a>.</p>
    </main>
  </body>
</html>
"""
    html_write = _write_text(html_path, html_doc)
    return {
        "path": str(path),
        "ok": path.exists() and (webm_path.exists() or gif_ok),
        "bytes": path.stat().st_size if path.exists() else 0,
        "playable_path": str(webm_path) if webm_path.exists() else str(gif_path),
        "playable_ok": webm_path.exists(),
        "preview_path": str(html_path),
        "gif_path": str(gif_path),
        "html_write": html_write,
        "variant_paths": [str(item) for item in (path, webm_path, gif_path, html_path) if item.exists()],
    }


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
    asset_kind = _infer_asset_kind(prompt)
    duration_s = _infer_duration_seconds(prompt)
    digest = hashlib.sha256(prompt.encode("utf-8", errors="replace")).hexdigest()[:12]
    asset_name = f"{_slugify(subject)}_{digest}.{asset_kind}"
    asset_rel = DEFAULT_PUBLIC_ASSET_DIR / asset_name
    asset_path = _rooted(root, asset_rel)
    public_asset_rel = asset_rel
    preview_rel: Optional[Path] = None
    source_asset_path = asset_path
    if asset_kind == "mp4":
        asset_write = _write_dog_video(asset_path, f"Aureon video artifact: {subject}", prompt, duration_s or 10)
        webm_rel = asset_rel.with_suffix(".webm")
        gif_rel = asset_rel.with_name(f"{asset_rel.stem}_preview.gif")
        html_rel = asset_rel.with_name(f"{asset_rel.stem}_preview.html")
        if _rooted(root, webm_rel).exists():
            public_asset_rel = webm_rel
        elif _rooted(root, gif_rel).exists():
            public_asset_rel = gif_rel
        if _rooted(root, html_rel).exists():
            preview_rel = html_rel
    else:
        svg = _build_svg(subject, prompt)
        asset_write = _write_text(asset_path, svg)
    public_url = f"/{public_asset_rel.as_posix().split('frontend/public/', 1)[-1]}"
    preview_url = f"/{preview_rel.as_posix().split('frontend/public/', 1)[-1]}" if preview_rel else ""
    open_flag = bool(open_requested) if open_requested is not None else bool(
        re.search(r"\b(?:open|show|display|view)\b", prompt.lower())
    )

    video_variant_rels = []
    if asset_kind == "mp4":
        for rel in (
            asset_rel,
            asset_rel.with_suffix(".webm"),
            asset_rel.with_name(f"{asset_rel.stem}_preview.gif"),
            asset_rel.with_name(f"{asset_rel.stem}_preview.html"),
        ):
            if _rooted(root, rel).exists():
                video_variant_rels.append(rel.as_posix())

    output_files = [
        *(video_variant_rels or [asset_rel.as_posix()]),
        DEFAULT_PUBLIC_QUALITY_JSON.as_posix(),
        DEFAULT_STATE_PATH.as_posix(),
        DEFAULT_AUDIT_JSON.as_posix(),
        DEFAULT_AUDIT_MD.as_posix(),
        DEFAULT_PUBLIC_JSON.as_posix(),
    ]
    generated_at = _utc_now()
    artifact_manifest = {
        "kind": "video" if asset_kind == "mp4" else "image",
        "asset_kind": asset_kind,
        "subject": subject,
        "asset_path": str(_rooted(root, public_asset_rel)),
        "source_asset_path": str(source_asset_path),
        "preview_path": str(_rooted(root, preview_rel)) if preview_rel else "",
        "public_url": public_url,
        "preview_url": preview_url,
        "duration_seconds": duration_s,
        "variant_paths": [
            str(_rooted(root, Path(item)))
            for item in (video_variant_rels or [asset_rel.as_posix()])
        ],
        "attempt": 1,
    }
    artifact_quality_report = build_artifact_quality_report(
        artifact_manifest,
        prompt=prompt,
        task_family="video" if asset_kind == "mp4" else "image_graphic_design",
        root=root,
    )
    quality_write = write_artifact_quality_report(artifact_quality_report, root=root)
    ready = bool(asset_write["ok"]) and bool(artifact_quality_report.get("handover_ready"))
    report: Dict[str, Any] = {
        "schema_version": "aureon-visual-asset-request-v1",
        "status": "visual_asset_ready" if ready else "visual_asset_failed_quality_gate",
        "generated_at": generated_at,
        "prompt": prompt,
        "subject": subject,
        "asset_kind": asset_kind,
        "duration_seconds": duration_s,
        "asset_path": str(_rooted(root, public_asset_rel)),
        "source_asset_path": str(source_asset_path),
        "preview_path": str(_rooted(root, preview_rel)) if preview_rel else "",
        "public_url": public_url,
        "preview_url": preview_url,
        "open_requested": open_flag,
        "artifact_manifest": artifact_manifest,
        "artifact_quality_report": artifact_quality_report,
        "regeneration_attempts": artifact_quality_report.get("regeneration_attempts", []),
        "handover_ready": bool(artifact_quality_report.get("handover_ready")),
        "approval_state": {
            "state": "pending_user_review_after_apply" if artifact_quality_report.get("handover_ready") else "blocked_by_quality_gate",
            "policy": "after_apply",
            "client_visible_product": bool(artifact_quality_report.get("handover_ready")),
        },
        "output_files": output_files,
        "target_files": output_files,
        "who": {
            "client": "operator dashboard prompt",
            "router": "aureon.core.goal_execution_engine",
            "artifact_worker": "aureon.autonomous.aureon_visual_asset_request",
        },
        "what": {
            "deliverable": "public visual/video artifact plus evidence packet",
            "subject": subject,
            "safe_format": "static_svg_or_browser_playable_webm_with_gif_preview_no_external_calls",
        },
        "where": {
            "repo_root": str(root),
            "asset_path": str(_rooted(root, public_asset_rel)),
            "source_asset_path": str(source_asset_path),
            "preview_path": str(_rooted(root, preview_rel)) if preview_rel else "",
            "public_url": public_url,
            "preview_url": preview_url,
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
            "quality_gate_passed": bool(artifact_quality_report.get("handover_ready")),
            "evidence_written": True,
            "open_requested": open_flag,
        },
        "write_info": {
            "writer": "AureonVisualAssetRequest",
            "asset_write": asset_write,
            "quality_write": quality_write,
        },
        "summary": {
            "output_file_count": len(output_files),
            "asset_written": bool(asset_write["ok"]),
            "artifact_quality_passed": bool(artifact_quality_report.get("handover_ready")),
            "artifact_quality_score": artifact_quality_report.get("score", 0),
            "browser_playable": bool(public_url.endswith((".webm", ".gif", ".svg"))),
            "open_requested": open_flag,
            "client_visible_artifact": bool(asset_write["ok"]) and bool(artifact_quality_report.get("handover_ready")),
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
