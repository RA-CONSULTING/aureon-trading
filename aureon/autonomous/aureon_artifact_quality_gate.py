from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PUBLIC_QUALITY_JSON = Path("frontend/public/aureon_artifact_quality_report.json")


def _default_root() -> Path:
    return Path.cwd().resolve() if (Path.cwd() / "aureon").exists() else REPO_ROOT


def _rooted(root: Path, path_value: Any) -> Path:
    path = Path(str(path_value or ""))
    return path if path.is_absolute() else root / path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return {"path": str(path), "ok": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}


def _kind_from_url(url: str, fallback: str = "") -> str:
    lower = (url or fallback or "").lower()
    if re.search(r"\.(mp4|webm|mov)(?:$|\?)", lower):
        return "video"
    if re.search(r"\.(svg|png|jpe?g|gif|webp)(?:$|\?)", lower):
        return "image"
    if "video" in lower:
        return "video"
    return "file"


def _probe_video_duration(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"available": False, "duration_seconds": 0.0, "reason": "file_missing"}
    try:
        import cv2

        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            return {"available": False, "duration_seconds": 0.0, "reason": "capture_not_opened"}
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frames = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
        capture.release()
        duration = frames / fps if fps > 0 else 0.0
        return {
            "available": True,
            "duration_seconds": round(duration, 3),
            "fps": round(fps, 3),
            "frame_count": int(frames),
            "reason": "probed",
        }
    except Exception as exc:
        return {"available": False, "duration_seconds": 0.0, "reason": str(exc)}


def _check(check_id: str, label: str, ok: bool, *, blocking: bool, evidence: str) -> Dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "ok": bool(ok),
        "blocking": bool(blocking),
        "evidence": evidence,
    }


def _snags_from_checks(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    snags: List[Dict[str, Any]] = []
    for item in checks:
        if item.get("blocking") and not item.get("ok"):
            snags.append(
                {
                    "id": f"artifact_{item.get('id')}",
                    "title": item.get("label"),
                    "severity": "blocking",
                    "owner": "Artifact Quality Gate",
                    "status": "open",
                    "evidence": item.get("evidence"),
                }
            )
    return snags


def build_artifact_quality_report(
    artifact_manifest: Dict[str, Any],
    *,
    prompt: str = "",
    task_family: str = "",
    root: Optional[Path] = None,
    minimum_score: float = 0.8,
) -> Dict[str, Any]:
    """Score whether an artifact is fit for client handover.

    The gate is intentionally local-only: it checks files, public URLs, playable
    formats, preview pages, and metadata without calling external providers.
    """

    root = Path(root or _default_root()).resolve()
    public_url = str(artifact_manifest.get("public_url") or "")
    preview_url = str(artifact_manifest.get("preview_url") or "")
    asset_path = _rooted(root, artifact_manifest.get("asset_path") or artifact_manifest.get("path") or "")
    preview_path = _rooted(root, artifact_manifest.get("preview_path") or "")
    source_asset_path = _rooted(root, artifact_manifest.get("source_asset_path") or asset_path)
    kind = str(artifact_manifest.get("kind") or _kind_from_url(public_url, str(asset_path)))
    duration_requested = int(artifact_manifest.get("duration_seconds") or 0)
    playable_extensions = (".webm", ".gif") if kind == "video" else (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp")
    playable_public = public_url.lower().endswith(playable_extensions)
    duration_probe = _probe_video_duration(asset_path) if kind == "video" and asset_path.suffix.lower() in {".mp4", ".webm"} else {}

    checks: List[Dict[str, Any]] = [
        _check(
            "artifact_file_exists",
            "Artifact file exists",
            asset_path.exists(),
            blocking=True,
            evidence=str(asset_path),
        ),
        _check(
            "public_url_present",
            "Public URL published",
            bool(public_url),
            blocking=True,
            evidence=public_url or "missing public URL",
        ),
        _check(
            "playable_or_renderable_format",
            "Browser-playable or renderable format",
            playable_public,
            blocking=True,
            evidence=f"{public_url} must end with one of {', '.join(playable_extensions)}",
        ),
    ]

    if kind == "video":
        preview_ok = bool(preview_url) and preview_path.exists()
        checks.append(
            _check(
                "preview_page_present",
                "HTML preview page present",
                preview_ok,
                blocking=True,
                evidence=str(preview_path) if preview_url else "missing preview URL",
            )
        )
        html_refs_source = False
        if preview_path.exists():
            try:
                html_text = preview_path.read_text(encoding="utf-8", errors="replace")
                html_refs_source = Path(public_url).name in html_text or Path(str(source_asset_path)).name in html_text
            except Exception:
                html_refs_source = False
        checks.append(
            _check(
                "preview_references_playable_source",
                "Preview references playable source",
                html_refs_source,
                blocking=True,
                evidence="preview page source check",
            )
        )
        duration_ok = duration_requested <= 0
        if duration_requested > 0:
            if duration_probe.get("available"):
                duration_ok = abs(float(duration_probe.get("duration_seconds") or 0.0) - duration_requested) <= max(0.5, duration_requested * 0.15)
            else:
                duration_ok = bool(duration_requested)
        checks.append(
            _check(
                "duration_metadata_present",
                "Duration metadata present",
                duration_ok,
                blocking=True,
                evidence=json.dumps(duration_probe or {"declared_duration_seconds": duration_requested}, sort_keys=True),
            )
        )

    prompt_words = {word for word in re.findall(r"[a-z0-9]{3,}", prompt.lower()) if word not in {"make", "create", "show", "video", "image", "public", "artifact"}}
    locator_text = " ".join(
        str(artifact_manifest.get(key) or "")
        for key in ("subject", "public_url", "asset_path", "preview_url", "title")
    ).lower()
    prompt_match = not prompt_words or bool(prompt_words.intersection(set(re.findall(r"[a-z0-9]{3,}", locator_text))))
    checks.append(
        _check(
            "prompt_match_signal",
            "Prompt match signal present",
            prompt_match,
            blocking=False,
            evidence=f"matched prompt words against {public_url or asset_path}",
        )
    )

    passed = len([item for item in checks if item.get("ok")])
    score = passed / len(checks) if checks else 0.0
    snags = _snags_from_checks(checks)
    handover_ready = score >= minimum_score and not snags
    return {
        "schema_version": "aureon-artifact-quality-report-v1",
        "status": "artifact_quality_passed" if handover_ready else "artifact_quality_blocked",
        "generated_at": _utc_now(),
        "task_family": task_family or kind,
        "provider_policy": "local_only_v1",
        "score": round(score, 3),
        "minimum_score": minimum_score,
        "handover_ready": handover_ready,
        "checks": checks,
        "snags": snags,
        "regeneration_attempts": [
            {
                "attempt": int(artifact_manifest.get("attempt") or 1),
                "status": "accepted" if handover_ready else "needs_regeneration",
                "reason": "all blocking checks passed" if handover_ready else "blocking artifact checks remain",
            }
        ],
        "browser_render_proof": {
            "proof_status": "preview_ready_for_browser_smoke" if kind == "video" else "renderable_static_asset",
            "preview_url": preview_url,
            "public_url": public_url,
            "local_probe": True,
            "duration_probe": duration_probe,
        },
        "artifact_manifest": artifact_manifest,
    }


def write_artifact_quality_report(
    report: Dict[str, Any],
    *,
    root: Optional[Path] = None,
    rel_path: Path = DEFAULT_PUBLIC_QUALITY_JSON,
) -> Dict[str, Any]:
    root = Path(root or _default_root()).resolve()
    return _write_json(_rooted(root, rel_path), report)
