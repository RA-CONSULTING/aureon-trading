"""Read-only real-source probe for Aureon providers.

No secrets are printed. The report records provider reachability, source class,
and concrete blockers such as missing required keys.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from aureon.observer.live_data_policy import simulation_fallback_allowed
from aureon.observer.real_data_contract import (
    load_source_registry,
    make_live_metric,
    make_no_data_metric,
    make_real_derived_metric,
    repo_root_from,
    summarize_truth_status,
)


def _redacted_presence(env_name: str | None) -> dict[str, Any]:
    if not env_name:
        return {"env": "", "present": True, "source": "keyless"}
    value = os.getenv(env_name, "").strip()
    return {"env": env_name, "present": bool(value), "source": "env" if value else "missing"}


def _http_probe(url: str, *, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = requests.get(
            url,
            headers=headers or {"User-Agent": "AureonRealDataProbe/1.0"},
            params=params or None,
            timeout=8,
        )
        elapsed = int((time.perf_counter() - started) * 1000)
        return {"ok": response.status_code < 400, "http_status": response.status_code, "latency_ms": elapsed}
    except Exception as exc:
        return {"ok": False, "http_status": 0, "latency_ms": 0, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}


def build_probe_report(root: Path) -> dict[str, Any]:
    registry = load_source_registry(root)
    sources = registry.get("sources", {})
    generated_at = datetime.now(timezone.utc).isoformat()
    metrics: list[dict[str, Any]] = []
    probes: dict[str, Any] = {}

    endpoint_overrides = {
        "coingecko": ("https://api.coingecko.com/api/v3/ping", None),
        "kraken_public": ("https://api.kraken.com/0/public/Time", None),
        "noaa_swpc": ("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", None),
        "open_meteo": ("https://api.open-meteo.com/v1/forecast", {"latitude": "51.5", "longitude": "-0.1", "current": "temperature_2m"}),
        "usgs_earthquake": ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_hour.geojson", None),
    }

    for source_id, source in sorted(sources.items()):
        if source_id == "test_fixture":
            continue
        env_name = source.get("auth_env")
        presence = _redacted_presence(env_name)
        endpoint = str(source.get("endpoint", ""))
        ttl = int(source.get("freshness_ttl_sec") or 300)
        source_name = str(source.get("name") or source_id)

        if env_name and not presence["present"]:
            metric = make_no_data_metric(
                f"{source_id}.readiness",
                source_id=source_id,
                source_name=source_name,
                source_url=endpoint,
                blocker=f"missing_env:{env_name}",
                freshness_ttl_sec=ttl,
            )
            probes[source_id] = {"ok": False, "credential": presence, "blocker": metric["blocker"]}
            metrics.append(metric)
            continue

        probe_url, params = endpoint_overrides.get(source_id, (endpoint, None))
        if not probe_url.startswith("http"):
            metric = make_no_data_metric(
                f"{source_id}.readiness",
                source_id=source_id,
                source_name=source_name,
                source_url=endpoint,
                blocker="no_http_probe_configured",
                freshness_ttl_sec=ttl,
            )
            probes[source_id] = {"ok": False, "credential": presence, "blocker": metric["blocker"]}
            metrics.append(metric)
            continue

        probe = _http_probe(probe_url, params=params)
        probes[source_id] = {"credential": presence, **probe}
        if probe.get("ok"):
            metrics.append(
                make_live_metric(
                    f"{source_id}.readiness",
                    source_id=source_id,
                    source_name=source_name,
                    source_url=probe_url,
                    value=probe.get("http_status"),
                    unit="http_status",
                    freshness_ttl_sec=ttl,
                )
            )
        else:
            metrics.append(
                make_no_data_metric(
                    f"{source_id}.readiness",
                    source_id=source_id,
                    source_name=source_name,
                    source_url=probe_url,
                    blocker=str(probe.get("error") or f"http_status:{probe.get('http_status')}"),
                    freshness_ttl_sec=ttl,
                )
            )

    if any(metric.get("source_id") == "noaa_swpc" and metric.get("truth_status") == "live" for metric in metrics):
        metrics.append(
            make_real_derived_metric(
                "schumann.noaa_kp_derived.readiness",
                source_id="noaa_swpc",
                source_name="NOAA Space Weather Prediction Center",
                source_url="https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                derived_from=["noaa_swpc.kp_index"],
                derivation_method="bounded Kp-to-Schumann proxy when direct station data is unavailable",
                value="available",
                freshness_ttl_sec=300,
            )
        )

    return {
        "schema_version": "aureon-real-source-probe-v1",
        "generated_at": generated_at,
        "repo_root": str(root),
        "simulation_fallback_allowed": simulation_fallback_allowed(),
        "summary": summarize_truth_status(metrics),
        "probes": probes,
        "metrics": metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = repo_root_from(Path(args.repo_root))
    report = build_probe_report(root)
    if args.output:
        path = root / args.output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if args.strict and report["summary"].get("blocked", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
