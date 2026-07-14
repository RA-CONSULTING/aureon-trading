import json

import pytest

from aureon.observer.real_data_contract import (
    make_live_metric,
    make_no_data_metric,
    make_real_derived_metric,
    make_test_fixture_metric,
    registered_source_ids,
    summarize_truth_status,
    validate_metric_envelope,
)
from scripts.validation import validate_real_data_contract as validator


def test_metric_envelopes_validate_against_source_registry():
    source_ids = registered_source_ids()
    live = make_live_metric(
        "space_weather.kp",
        source_id="noaa_swpc",
        source_name="NOAA SWPC",
        source_url="https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
        value=2.0,
        unit="kp",
    )
    derived = make_real_derived_metric(
        "schumann.noaa_kp_derived",
        source_id="noaa_swpc",
        source_name="NOAA SWPC",
        source_url="https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
        derived_from=["space_weather.kp"],
        derivation_method="bounded Kp-to-Schumann proxy",
        value=7.83,
        unit="hz",
    )
    blocked = make_no_data_metric(
        "firms.fire_count",
        source_id="nasa_firms",
        source_name="NASA FIRMS",
        source_url="https://firms.modaps.eosdis.nasa.gov/api/area/csv",
        blocker="missing_env:FIRMS_MAP_KEY",
    )
    fixture = make_test_fixture_metric("fixture.metric", value=1)

    for metric in (live, derived, blocked, fixture):
        assert validate_metric_envelope(metric, registry_source_ids=source_ids) == []

    counts = summarize_truth_status([live, derived, blocked, fixture])
    assert counts["operational_ready"] == 2
    assert counts["blocked"] == 1
    assert counts["test_fixture"] == 1


def test_invalid_operational_fixture_is_rejected():
    metric = make_test_fixture_metric("fixture.metric")
    metric["is_operational_metric"] = True
    with pytest.raises(ValueError, match="test_fixture metric cannot be operational"):
        validate_metric_envelope(metric)


def test_validator_flags_runtime_random_but_allows_test_fixture(tmp_path):
    root = tmp_path
    (root / "aureon").mkdir()
    (root / "aureon" / "data_feeds").mkdir()
    (root / "data").mkdir()
    (root / "tests").mkdir()
    (root / "data" / "real_data_sources.json").write_text(
        json.dumps({"sources": {"test_fixture": {"name": "Test Fixture", "category": "fixture", "endpoint": "local:test", "freshness_ttl_sec": 0, "derived_metrics_allowed": False}}}),
        encoding="utf-8",
    )
    runtime_file = root / "aureon" / "data_feeds" / "runtime_metric.py"
    runtime_file.write_text("import random\nvalue = random.random()\n", encoding="utf-8")
    test_file = root / "tests" / "test_fixture_metric.py"
    test_file.write_text("import random\nvalue = random.random()\n", encoding="utf-8")

    runtime_findings = validator.scan_text_file(runtime_file, root)
    test_findings = validator.scan_text_file(test_file, root)

    assert any(item.severity == "error" and item.code == "python_random_runtime" for item in runtime_findings)
    assert any(item.severity == "fixture" and item.code == "python_random_runtime" for item in test_findings)


def test_public_json_allows_truth_status_claim_metadata(tmp_path):
    root = tmp_path
    public_dir = root / "frontend" / "public"
    public_dir.mkdir(parents=True)
    payload_path = public_dir / "claim_metadata.json"
    payload_path.write_text(
        json.dumps(
            {
                "forecast": {
                    "truth_status": "hypothesis_only",
                    "validated": False,
                    "truth_claim_allowed": False,
                },
                "metric": make_no_data_metric(
                    "nasa.neo.close_approaches",
                    source_id="nasa_neo",
                    source_name="NASA NEO",
                    source_url="https://api.nasa.gov/neo/rest/v1/feed",
                    blocker="missing_env:NASA_API_KEY",
                ),
            }
        ),
        encoding="utf-8",
    )

    findings = validator.validate_public_metric_json(
        payload_path,
        root,
        {"nasa_neo", "test_fixture"},
    )

    assert findings == []
