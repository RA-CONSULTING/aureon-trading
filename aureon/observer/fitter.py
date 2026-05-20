"""``python -m aureon.observer.fitter`` — fit α/g/β/τ from trace data.

The HNC live daemon ships with hardcoded ``α=0.35, g=2.5, β=1.0, τ=10``
heuristics that match the white-paper stable regime. Production calls
for *fitted* parameters — the live kernel should run on values measured
against the real Λ(t) trace, not assumed ones.

This module reads ``state/hnc_live_trace.jsonl`` (or any path you point
it at), reconstructs the master-equation residual, fits the four
parameters using ``scipy.optimize.curve_fit`` with R² validation, and
writes ``state/hnc_fitted_params.json`` in the exact format
``aureon.core.hnc_params.load_params`` consumes. The next daemon start
picks them up via ``apply_to_lambda_engine``.

The fitter is one-shot — it computes once and exits. Re-run it whenever
you have meaningfully more trace data; the loader prefers fitted values
over heuristics, so the daemon's behaviour follows.

Two fit modes:

  ``tanh`` (default, fastest)
      Fit only ``α·tanh(g·Λ̄)`` — the observer term — directly against
      the raw Λ samples. β and τ are set from defaults. Use when you
      have less than ~20 minutes of data, or you just want the
      observer-gain numbers (this is what the spec mentioned: "tonight's
      tanh fit gave A=0.754, B=0.732 at R²=0.95").

  ``full``
      4-parameter fit. β and τ enter through the lighthouse echo term
      ``β·Λ(t-τ)``. τ is discrete (sample lag), so we grid-search a
      small window of integer τ candidates and pick the one with the
      highest R²; α / g / β are continuous and fit by curve_fit per τ.

Both modes require numpy + scipy. When either is missing the fitter
exits non-zero with a clear error (this is offline analysis, not the
hot path — graceful degrade isn't appropriate here).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger("aureon.observer.fitter")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_PATH = REPO_ROOT / "state" / "hnc_live_trace.jsonl"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "state" / "hnc_fitted_params.json"

# Minimum samples to attempt a fit. Below this the fitter refuses —
# fitting on too few points produces meaningless params that would then
# get written to disk and adopted by the daemon.
MIN_SAMPLES = 60          # 5 minutes at the daemon's 5 s cadence

# Sane bounds for curve_fit so the optimiser doesn't wander into
# numerically pathological territory. Chosen to match the HNC white
# paper's stability regime β ∈ [0.6, 1.1].
ALPHA_BOUNDS = (0.0, 2.0)
G_BOUNDS = (0.1, 10.0)
BETA_BOUNDS = (0.0, 1.2)

# τ candidates to grid-search in 'full' mode (samples). Default 5 s
# cadence → 5..50 s of memory.
TAU_CANDIDATES = (1, 2, 3, 5, 7, 10, 14, 20, 30)


@dataclass
class FitResult:
    alpha: float
    g: float
    beta: float
    tau: int
    delta_t: int
    r_squared: float
    n_samples: int
    mode: str
    fitted_at: float
    fitted_from: str

    def to_hnc_params_json(self) -> dict:
        """Shape that ``hnc_params.load_params`` consumes verbatim."""
        return {
            "alpha": float(self.alpha),
            "g": float(self.g),
            "beta": float(self.beta),
            "tau": int(self.tau),
            "delta_t": int(self.delta_t),
            "fitted_at": float(self.fitted_at),
            "fitted_from": str(self.fitted_from),
            "r_squared": float(self.r_squared),
        }


# ─── trace loading ─────────────────────────────────────────────────

def load_trace(path: Path) -> Tuple[List[float], List[float]]:
    """Return (timestamps, lambda_t_values) from a trace JSONL.

    Skips malformed lines silently; logs the count at INFO. Order is
    preserved from the file (the daemon writes monotonically).
    """
    if not path.exists():
        raise FileNotFoundError(f"trace not found: {path}")
    ts: List[float] = []
    lt: List[float] = []
    skipped = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                t = float(row["ts"])
                v = float(row["lambda_t"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                skipped += 1
                continue
            ts.append(t)
            lt.append(v)
    logger.info("loaded %d samples from %s (skipped %d malformed)",
                len(lt), path, skipped)
    return ts, lt


# ─── numpy/scipy guards ────────────────────────────────────────────

def _require_numpy_scipy():
    try:
        import numpy  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "fitter requires numpy. install it in the production env."
        ) from exc
    try:
        from scipy.optimize import curve_fit  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "fitter requires scipy. install it in the production env."
        ) from exc


# ─── tanh-only fit ─────────────────────────────────────────────────

def fit_tanh(
    lambda_values: Sequence[float],
    delta_t: int = 5,
    bounds_alpha: Tuple[float, float] = ALPHA_BOUNDS,
    bounds_g: Tuple[float, float] = G_BOUNDS,
) -> Tuple[float, float, float]:
    """Fit Λ(t) ≈ α·tanh(g·Λ̄_Δt(t)).

    Returns (alpha, g, r_squared). Designed to mirror the spec's
    "tanh fit gave A=0.754, B=0.732 at R²=0.95" finding.
    """
    _require_numpy_scipy()
    import numpy as np
    from scipy.optimize import curve_fit

    arr = np.asarray(lambda_values, dtype=float)
    n = arr.size
    if n < MIN_SAMPLES:
        raise ValueError(f"need at least {MIN_SAMPLES} samples, got {n}")

    # Predictor: rolling mean over the trailing delta_t samples.
    # Drop the first delta_t-1 samples that have no valid window.
    if delta_t < 1:
        delta_t = 1
    # Vectorised rolling mean via cumsum — the same pattern the engine uses.
    cs = np.cumsum(arr, dtype=float)
    cs[delta_t:] = cs[delta_t:] - cs[:-delta_t]
    rolled = cs[delta_t - 1:] / float(delta_t)
    targets = arr[delta_t - 1:]

    def model(x, alpha, g):
        return alpha * np.tanh(g * x)

    p0 = [0.5, 1.0]
    lower = [bounds_alpha[0], bounds_g[0]]
    upper = [bounds_alpha[1], bounds_g[1]]
    popt, _ = curve_fit(model, rolled, targets, p0=p0, bounds=(lower, upper),
                        maxfev=4000)
    alpha, g = float(popt[0]), float(popt[1])

    # Coefficient of determination.
    pred = model(rolled, alpha, g)
    ss_res = float(np.sum((targets - pred) ** 2))
    ss_tot = float(np.sum((targets - targets.mean()) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return alpha, g, r2


# ─── full 4-parameter fit ──────────────────────────────────────────

def fit_full(
    lambda_values: Sequence[float],
    delta_t: int = 5,
    tau_candidates: Iterable[int] = TAU_CANDIDATES,
) -> Tuple[float, float, float, int, float]:
    """Fit Λ(t) ≈ α·tanh(g·Λ̄_Δt(t)) + β·Λ(t-τ) over candidate τ values.

    Grid-search τ (discrete sample lag), continuous fit α/g/β at each.
    Returns (alpha, g, beta, tau_best, r_squared) for the best τ.
    """
    _require_numpy_scipy()
    import numpy as np
    from scipy.optimize import curve_fit

    arr = np.asarray(lambda_values, dtype=float)
    n = arr.size
    if n < MIN_SAMPLES:
        raise ValueError(f"need at least {MIN_SAMPLES} samples, got {n}")

    if delta_t < 1:
        delta_t = 1

    cs = np.cumsum(arr, dtype=float)
    cs[delta_t:] = cs[delta_t:] - cs[:-delta_t]
    rolled_full = cs[delta_t - 1:] / float(delta_t)

    best: Optional[Tuple[float, float, float, int, float]] = None
    for tau in tau_candidates:
        if tau < 1 or tau >= n - delta_t:
            continue
        # Align: targets[t] corresponds to rolled[t] AND lag[t] = arr[t - tau].
        # rolled_full starts at index delta_t-1 of arr; we need t >= max(delta_t-1, tau).
        start = max(delta_t - 1, tau)
        targets = arr[start:]
        rolled = rolled_full[start - (delta_t - 1):]
        lag = arr[start - tau: n - tau]
        if not (len(targets) == len(rolled) == len(lag)):
            # Defensive: alignment math failed for some edge case.
            continue
        if len(targets) < MIN_SAMPLES // 2:
            continue

        def model(_x, alpha, g, beta, _r=rolled, _l=lag):
            return alpha * np.tanh(g * _r) + beta * _l

        # curve_fit needs an x array even when unused — pass indices.
        x_dummy = np.arange(len(targets), dtype=float)
        p0 = [0.5, 1.0, 0.5]
        lower = [ALPHA_BOUNDS[0], G_BOUNDS[0], BETA_BOUNDS[0]]
        upper = [ALPHA_BOUNDS[1], G_BOUNDS[1], BETA_BOUNDS[1]]
        try:
            popt, _ = curve_fit(model, x_dummy, targets,
                                p0=p0, bounds=(lower, upper), maxfev=6000)
        except Exception as exc:  # solver instability for some τ
            logger.debug("τ=%d fit failed: %s", tau, exc)
            continue
        alpha, g, beta = float(popt[0]), float(popt[1]), float(popt[2])

        pred = model(x_dummy, alpha, g, beta)
        ss_res = float(np.sum((targets - pred) ** 2))
        ss_tot = float(np.sum((targets - targets.mean()) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        if best is None or r2 > best[4]:
            best = (alpha, g, beta, int(tau), r2)

    if best is None:
        raise RuntimeError("no τ candidate produced a valid fit")
    return best


# ─── orchestration ─────────────────────────────────────────────────

def run_fit(
    trace_path: Path = DEFAULT_TRACE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    mode: str = "tanh",
    min_samples: int = MIN_SAMPLES,
    delta_t: int = 5,
    write: bool = True,
) -> FitResult:
    """Load trace, fit, optionally write — return FitResult for inspection."""
    ts, lt = load_trace(trace_path)
    if len(lt) < min_samples:
        raise ValueError(
            f"trace has {len(lt)} samples; need at least {min_samples} to fit"
        )

    if mode == "tanh":
        alpha, g, r2 = fit_tanh(lt, delta_t=delta_t)
        # Keep beta/tau at the loader defaults — tanh-only fit doesn't
        # touch them, and load_params will fall through to env / hardcode.
        from aureon.core.hnc_params import load_params as _lp
        defaults = _lp()
        beta_out = float(defaults.beta)
        tau_out = int(defaults.tau)
    elif mode == "full":
        alpha, g, beta_out, tau_out, r2 = fit_full(lt, delta_t=delta_t)
    else:
        raise ValueError(f"unknown mode: {mode!r}; expected 'tanh' or 'full'")

    result = FitResult(
        alpha=alpha,
        g=g,
        beta=beta_out,
        tau=tau_out,
        delta_t=delta_t,
        r_squared=r2,
        n_samples=len(lt),
        mode=mode,
        fitted_at=time.time(),
        fitted_from=str(trace_path.relative_to(REPO_ROOT))
                    if trace_path.is_relative_to(REPO_ROOT) else str(trace_path),
    )

    if write:
        # Atomic write — same tmp-then-rename pattern hnc_params and
        # LambdaEngine use, so a crash mid-write never corrupts the
        # file the daemon will read on next start.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = output_path.with_suffix(output_path.suffix + ".tmp")
        tmp.write_text(json.dumps(result.to_hnc_params_json(), indent=2,
                                   sort_keys=True), encoding="utf-8")
        import os
        os.replace(tmp, output_path)
        logger.info("wrote fitted params → %s", output_path)

    return result


# ─── CLI ───────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aureon.observer.fitter",
        description="Fit HNC α/g/β/τ from a recorded trace JSONL.",
    )
    parser.add_argument("--trace-path", type=Path, default=DEFAULT_TRACE_PATH,
                        help=f"Trace JSONL to fit (default: {DEFAULT_TRACE_PATH}).")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH,
                        help=f"Where to write fitted params "
                             f"(default: {DEFAULT_OUTPUT_PATH}).")
    parser.add_argument("--mode", choices=("tanh", "full"), default="tanh",
                        help="Fit mode. tanh = α·tanh(g·Λ̄) only "
                             "(fast, matches the spec's tonight-fit). "
                             "full = 4-param incl. β/τ via grid search.")
    parser.add_argument("--min-samples", type=int, default=MIN_SAMPLES,
                        help=f"Minimum trace length to attempt a fit "
                             f"(default {MIN_SAMPLES} = 5 min @ 5s cadence).")
    parser.add_argument("--delta-t", type=int, default=5,
                        help="Observer rolling-mean window in samples (default 5).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute the fit but DON'T write the output file. "
                             "Use to inspect R² before committing the params.")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON summary on stdout.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        result = run_fit(
            trace_path=args.trace_path,
            output_path=args.output_path,
            mode=args.mode,
            min_samples=args.min_samples,
            delta_t=args.delta_t,
            write=not args.dry_run,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    summary = result.to_hnc_params_json()
    summary["mode"] = result.mode
    summary["n_samples"] = result.n_samples
    summary["dry_run"] = args.dry_run
    summary["output_path"] = str(args.output_path) if not args.dry_run else None

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print()
        print(f"HNC fit ({result.mode}) — {result.n_samples} samples")
        print("─" * 40)
        print(f"  α (alpha)    : {result.alpha:.6f}")
        print(f"  g            : {result.g:.6f}")
        print(f"  β (beta)     : {result.beta:.6f}")
        print(f"  τ (tau)      : {result.tau}")
        print(f"  Δt (delta_t) : {result.delta_t}")
        print(f"  R²           : {result.r_squared:.4f}")
        if args.dry_run:
            print()
            print("  (dry-run — file NOT written)")
        else:
            print(f"  written to   : {args.output_path}")
            print()
            print("Next daemon start will pick these up via hnc_params.load_params().")
    return 0


if __name__ == "__main__":
    sys.exit(main())
