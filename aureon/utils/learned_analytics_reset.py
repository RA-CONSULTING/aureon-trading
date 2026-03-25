"""Helpers to reset AdaptiveLearningEngine learned analytics safely.

This module is intentionally stdlib-only so it can be imported from
runtime code (startup path) without heavy dependencies.

Behavior:
- Optional, opt-in auto reset via environment variables.
- Archive existing history before wiping.
- Idempotent by `regime_tag` so startup reset doesn't repeat forever.
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_truthy(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return _is_truthy(val)


def _read_json_file(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _archive_path_for(history_path: str, ts: str) -> str:
    base = os.path.basename(history_path)
    directory = os.path.dirname(history_path) or '.'
    stem = base.rsplit(".", 1)[0] if "." in base else base

    # Preserve old behavior for the default filename.
    if base == "adaptive_learning_history.json":
        return os.path.join(directory, f"learning_archive_{ts}.json")

    return os.path.join(directory, f"{stem}_learning_archive_{ts}.json")


@dataclass(frozen=True)
class ResetResult:
    did_reset: bool
    history_path: str
    backup_path: Optional[str] = None
    reason: Optional[str] = None
    regime_tag: Optional[str] = None
    error: Optional[str] = None


def reset_learned_analytics(
    *,
    history_path: str = "adaptive_learning_history.json",
    reason: str = "manual reset",
    regime_tag: str = "penny_profit_v1",
    archive: bool = True,
) -> ResetResult:
    ts = _timestamp()

    try:
        original: Optional[Dict[str, Any]]
        if os.path.exists(history_path):
            try:
                original = _read_json_file(history_path)
            except Exception as e:  # noqa: BLE001
                # If the file is corrupted, archive it as-is to avoid losing info.
                directory = os.path.dirname(history_path) or '.'
                corrupted_backup = os.path.join(directory, f"learning_archive_corrupted_{ts}.json")
                try:
                    os.replace(history_path, corrupted_backup)
                    logger.warning(
                        "Learned analytics file was not parseable; moved aside to %s (%s)",
                        corrupted_backup,
                        e,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning("Learned analytics file was not parseable (%s)", e)
                original = None
        else:
            original = None

        backup_path = None
        if archive and original is not None:
            backup_path = _archive_path_for(history_path, ts)
            _write_json_file(backup_path, original)

        reset_payload: Dict[str, Any] = {
            "trades": [],
            "thresholds": {},
            "updated_at": datetime.now().isoformat(),
            "reset_at": ts,
            "reset_reason": reason,
            "regime_tag": regime_tag,
        }
        _write_json_file(history_path, reset_payload)

        return ResetResult(
            did_reset=True,
            history_path=history_path,
            backup_path=backup_path,
            reason=reason,
            regime_tag=regime_tag,
        )
    except Exception as e:  # noqa: BLE001
        return ResetResult(
            did_reset=False,
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
            error=str(e),
        )


def reset_learned_analytics_if_needed(
    *,
    history_path: str = "adaptive_learning_history.json",
    reason: str = "startup auto reset",
    regime_tag: str = "penny_profit_v1",
    force: bool = False,
    archive: bool = True,
) -> ResetResult:
    if force:
        return reset_learned_analytics(
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
            archive=archive,
        )

    try:
        data = _read_json_file(history_path)
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not read learned analytics history (%s); forcing reset", e)
        return reset_learned_analytics(
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
            archive=archive,
        )

    # Missing file or empty schema: ensure it exists, but don't archive repeatedly.
    if not data:
        return reset_learned_analytics(
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
            archive=False,
        )

    existing_regime = str(data.get("regime_tag") or "")
    trades = data.get("trades")
    trade_count = len(trades) if isinstance(trades, list) else 0

    # If already in this regime and already empty, do nothing.
    if existing_regime == regime_tag and trade_count == 0:
        return ResetResult(
            did_reset=False,
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
        )

    # If same regime but has trades, do not wipe unless explicitly forced.
    if existing_regime == regime_tag and trade_count > 0:
        return ResetResult(
            did_reset=False,
            history_path=history_path,
            reason=reason,
            regime_tag=regime_tag,
        )

    # Different regime tag → reset (and archive) exactly once.
    return reset_learned_analytics(
        history_path=history_path,
        reason=reason,
        regime_tag=regime_tag,
        archive=archive,
    )


def auto_reset_enabled() -> bool:
    return env_truthy("AUREON_AUTO_RESET_LEARNED_ANALYTICS")


def auto_reset_config() -> Dict[str, Any]:
    return {
        "enabled": auto_reset_enabled(),
        "reason": os.getenv("AUREON_AUTO_RESET_LEARNED_ANALYTICS_REASON", "startup auto reset"),
        "regime_tag": os.getenv("AUREON_LEARNED_ANALYTICS_REGIME_TAG", "penny_profit_v1"),
        "force": env_truthy("AUREON_AUTO_RESET_LEARNED_ANALYTICS_FORCE"),
        "archive": not env_truthy("AUREON_AUTO_RESET_LEARNED_ANALYTICS_NO_ARCHIVE"),
    }
