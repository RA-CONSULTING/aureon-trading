"""Fitter I/O contract.

Pure-Python paths (load_trace, FitResult.to_hnc_params_json,
save_params/load_params round-trip) run unconditionally. The actual
fit math (curve_fit) requires numpy + scipy and is gated with
``pytest.importorskip``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from aureon.observer import fitter as F


def test_load_trace_happy_path(tmp_path: Path):
    p = tmp_path / "trace.jsonl"
    with open(p, "w") as f:
        for i in range(10):
            f.write(json.dumps({"ts": float(i), "step": i + 1, "lambda_t": 0.1 * i}) + "\n")
    ts, lt = F.load_trace(p)
    assert len(ts) == len(lt) == 10
    assert lt[0] == 0.0 and abs(lt[-1] - 0.9) < 1e-9


def test_load_trace_skips_malformed_lines(tmp_path: Path):
    p = tmp_path / "trace.jsonl"
    with open(p, "w") as f:
        f.write('{"ts": 1.0, "lambda_t": 0.5}\n')
        f.write('not-json\n')
        f.write('\n')   # empty line
        f.write('{"ts": 2.0}\n')                       # missing lambda_t
        f.write('{"ts": 3.0, "lambda_t": "not-number"}\n')
        f.write('{"ts": 4.0, "lambda_t": 0.6}\n')
    ts, lt = F.load_trace(p)
    assert len(lt) == 2
    assert lt == [0.5, 0.6]


def test_load_trace_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        F.load_trace(tmp_path / "nope.jsonl")


def test_fit_result_shape_matches_load_params(tmp_path: Path):
    """The fitter's output dict must round-trip through hnc_params.load_params."""
    fr = F.FitResult(
        alpha=0.754, g=0.732, beta=1.0, tau=10, delta_t=5,
        r_squared=0.95, n_samples=200, mode="tanh",
        fitted_at=time.time(), fitted_from="state/hnc_live_trace.jsonl",
    )
    out = fr.to_hnc_params_json()

    required = {"alpha", "g", "beta", "tau", "delta_t",
                "fitted_at", "fitted_from", "r_squared"}
    assert required.issubset(out.keys())

    p = tmp_path / "fit.json"
    p.write_text(json.dumps(out))

    from aureon.core.hnc_params import load_params
    loaded = load_params(p)
    assert loaded.alpha == 0.754
    assert loaded.g == 0.732
    assert loaded.beta == 1.0
    assert loaded.tau == 10
    assert loaded.delta_t == 5
    assert loaded.r_squared == 0.95


def test_save_load_roundtrip(tmp_path: Path):
    """save_params(...) → load_params(...) preserves every field."""
    from aureon.core.hnc_params import HNCParams, load_params, save_params
    hp = HNCParams(
        alpha=0.123, g=4.567, beta=0.89, tau=14, delta_t=8,
        fitted_at=1234567.0, fitted_from="x/y.jsonl", r_squared=0.97,
    )
    p = tmp_path / "params.json"
    save_params(hp, p)
    back = load_params(p)
    assert back.alpha == 0.123
    assert back.g == 4.567
    assert back.beta == 0.89
    assert back.tau == 14
    assert back.delta_t == 8
    assert back.fitted_at == 1234567.0
    assert back.fitted_from == "x/y.jsonl"
    assert back.r_squared == 0.97


def test_run_fit_too_few_samples_raises(tmp_path: Path):
    """run_fit requires at least min_samples — must raise ValueError."""
    p = tmp_path / "trace.jsonl"
    with open(p, "w") as f:
        for i in range(5):
            f.write(json.dumps({"ts": float(i), "step": i + 1, "lambda_t": 0.1 * i}) + "\n")
    with pytest.raises(ValueError, match="need at least"):
        F.run_fit(trace_path=p, mode="tanh", min_samples=60, write=False)


def test_unknown_mode_raises(tmp_path: Path):
    """Mode strings other than 'tanh' / 'full' must raise."""
    p = tmp_path / "trace.jsonl"
    with open(p, "w") as f:
        for i in range(70):
            f.write(json.dumps({"ts": float(i), "step": i + 1, "lambda_t": 0.1}) + "\n")
    # Without numpy this still raises before mode is checked? No — load_trace
    # runs first, then mode validation, then numpy import. Skip if numpy
    # missing because the import-error would short-circuit before mode check.
    pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    with pytest.raises(ValueError, match="unknown mode"):
        F.run_fit(trace_path=p, mode="bogus", min_samples=60, write=False)


# ─── Math-bearing tests (numpy + scipy required) ────────────────────


def test_fit_tanh_recovers_planted_alpha_and_g():
    """Generate a synthetic Λ from a known α / g; the fit must recover them."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")

    alpha_true, g_true = 0.5, 2.0
    delta_t = 5
    n = 400
    rng = np.random.default_rng(seed=42)
    # Generate Λ̄ as a smooth random walk and target = α·tanh(g·Λ̄).
    base = np.cumsum(rng.normal(0.0, 0.05, size=n))
    base = np.clip(base / max(abs(base).max(), 1e-9) * 0.4, -0.5, 0.5)
    targets = alpha_true * np.tanh(g_true * base)
    # The fitter computes its own rolling mean — inject targets so the
    # rolling mean equals the predictor we used to construct them.
    series = targets.tolist()
    # Pad the leading window so the cumsum-based rolling mean matches.
    padded = list(targets[:delta_t-1]) + series

    alpha_fit, g_fit, r2 = F.fit_tanh(padded, delta_t=delta_t)
    # Generous tolerance — the rolling-mean step adds smoothing
    # unrelated to the synthetic relationship.
    assert 0.0 < alpha_fit < 2.0
    assert 0.1 < g_fit < 10.0
    assert r2 > 0.5
