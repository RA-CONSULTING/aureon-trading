"""Truth envelope for Aureon metrics and data-source readings.

Every operational value should be one of:

* live: collected directly from a real provider.
* real_derived: calculated from real provider inputs, with derivation named.
* cached_real: last-good real provider value, with freshness metadata.
* no_data: source unavailable or key missing; do not substitute a fake value.
* test_fixture: deterministic test/demo input, never operational truth.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

TRUTH_STATUSES = {"live", "real_derived", "cached_real", "no_data", "test_fixture"}
OPERATIONAL_STATUSES = {"live", "real_derived", "cached_real", "no_data"}
DEFAULT_TTL_SEC = 300


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aureon").is_dir() and (candidate / "data").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def load_source_registry(root: Path | None = None) -> dict[str, Any]:
    path = repo_root_from(root) / "data" / "real_data_sources.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"sources": {}}
    if not isinstance(payload, dict):
        raise ValueError(f"real data source registry must be a JSON object: {path}")
    payload.setdefault("sources", {})
    return payload


def registered_source_ids(root: Path | None = None) -> set[str]:
    sources = load_source_registry(root).get("sources", {})
    if not isinstance(sources, Mapping):
        raise ValueError("real data source registry 'sources' must be an object")
    return {str(source_id) for source_id in sources}


@dataclass(frozen=True)
class RealDataMetric:
    name: str
    truth_status: str
    source_id: str
    source_name: str
    source_url: str
    collected_at: float = field(default_factory=time.time)
    freshness_ttl_sec: int = DEFAULT_TTL_SEC
    derived_from: list[str] = field(default_factory=list)
    derivation_method: str = ""
    is_operational_metric: bool = True
    blocker: str = ""
    value: Any = None
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        validate_metric_envelope(payload)
        return payload


def make_live_metric(
    name: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    value: Any = None,
    unit: str = "",
    freshness_ttl_sec: int = DEFAULT_TTL_SEC,
    collected_at: float | None = None,
) -> dict[str, Any]:
    return RealDataMetric(
        name=name,
        truth_status="live",
        source_id=source_id,
        source_name=source_name,
        source_url=source_url,
        value=value,
        unit=unit,
        freshness_ttl_sec=freshness_ttl_sec,
        collected_at=time.time() if collected_at is None else float(collected_at),
    ).to_dict()


def make_real_derived_metric(
    name: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    derived_from: Iterable[str],
    derivation_method: str,
    value: Any = None,
    unit: str = "",
    freshness_ttl_sec: int = DEFAULT_TTL_SEC,
    collected_at: float | None = None,
) -> dict[str, Any]:
    return RealDataMetric(
        name=name,
        truth_status="real_derived",
        source_id=source_id,
        source_name=source_name,
        source_url=source_url,
        value=value,
        unit=unit,
        derived_from=list(derived_from),
        derivation_method=derivation_method,
        freshness_ttl_sec=freshness_ttl_sec,
        collected_at=time.time() if collected_at is None else float(collected_at),
    ).to_dict()


def make_cached_real_metric(
    name: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    value: Any = None,
    unit: str = "",
    freshness_ttl_sec: int = DEFAULT_TTL_SEC,
    collected_at: float | None = None,
) -> dict[str, Any]:
    return RealDataMetric(
        name=name,
        truth_status="cached_real",
        source_id=source_id,
        source_name=source_name,
        source_url=source_url,
        value=value,
        unit=unit,
        freshness_ttl_sec=freshness_ttl_sec,
        collected_at=time.time() if collected_at is None else float(collected_at),
    ).to_dict()


def make_no_data_metric(
    name: str,
    *,
    source_id: str,
    source_name: str,
    source_url: str,
    blocker: str,
    freshness_ttl_sec: int = DEFAULT_TTL_SEC,
    collected_at: float | None = None,
) -> dict[str, Any]:
    return RealDataMetric(
        name=name,
        truth_status="no_data",
        source_id=source_id,
        source_name=source_name,
        source_url=source_url,
        blocker=blocker,
        freshness_ttl_sec=freshness_ttl_sec,
        collected_at=time.time() if collected_at is None else float(collected_at),
    ).to_dict()


def make_test_fixture_metric(name: str, *, blocker: str = "test_fixture", value: Any = None) -> dict[str, Any]:
    return RealDataMetric(
        name=name,
        truth_status="test_fixture",
        source_id="test_fixture",
        source_name="Test Fixture",
        source_url="local:test-fixture",
        blocker=blocker,
        value=value,
        is_operational_metric=False,
    ).to_dict()


def validate_metric_envelope(metric: Mapping[str, Any], *, registry_source_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    required = (
        "name",
        "truth_status",
        "source_id",
        "source_name",
        "source_url",
        "collected_at",
        "freshness_ttl_sec",
        "derived_from",
        "derivation_method",
        "is_operational_metric",
        "blocker",
    )
    for key in required:
        if key not in metric:
            errors.append(f"missing field: {key}")

    status = str(metric.get("truth_status", ""))
    if status not in TRUTH_STATUSES:
        errors.append(f"invalid truth_status: {status}")

    source_id = str(metric.get("source_id", ""))
    if registry_source_ids is not None and source_id not in registry_source_ids and source_id != "test_fixture":
        errors.append(f"unregistered source_id: {source_id}")

    if status == "real_derived":
        if not metric.get("derived_from"):
            errors.append("real_derived metric must list derived_from")
        if not str(metric.get("derivation_method", "")).strip():
            errors.append("real_derived metric must name derivation_method")

    if status == "no_data" and not str(metric.get("blocker", "")).strip():
        errors.append("no_data metric must include blocker")

    if status == "test_fixture" and bool(metric.get("is_operational_metric", True)):
        errors.append("test_fixture metric cannot be operational")

    try:
        ttl = int(metric.get("freshness_ttl_sec", 0))
        if ttl < 0:
            errors.append("freshness_ttl_sec cannot be negative")
    except Exception:
        errors.append("freshness_ttl_sec must be an integer")

    if errors:
        raise ValueError("; ".join(errors))
    return []


def summarize_truth_status(metrics: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(TRUTH_STATUSES)}
    for metric in metrics:
        status = str(metric.get("truth_status", ""))
        if status in counts:
            counts[status] += 1
    counts["operational_ready"] = counts["live"] + counts["real_derived"] + counts["cached_real"]
    counts["blocked"] = counts["no_data"]
    return counts


__all__ = [
    "DEFAULT_TTL_SEC",
    "OPERATIONAL_STATUSES",
    "RealDataMetric",
    "TRUTH_STATUSES",
    "load_source_registry",
    "make_cached_real_metric",
    "make_live_metric",
    "make_no_data_metric",
    "make_real_derived_metric",
    "make_test_fixture_metric",
    "registered_source_ids",
    "repo_root_from",
    "summarize_truth_status",
    "validate_metric_envelope",
]
