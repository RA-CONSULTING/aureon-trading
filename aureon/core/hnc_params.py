"""HNC fitted-parameter loader.

The Master Equation Λ(t) = Σ wᵢ sin(2πfᵢt + φᵢ) + α·tanh(g·Λ̄(t)) + β·Λ(t-τ)
takes four scalar parameters (α, g, β, τ) and an integration window (Δt).
``aureon_lambda_engine.py`` ships hardcoded defaults that match the white
paper's stable regime, but a *live* HNC field needs parameters fit to the
actual data we are ingesting — not heuristics.

This module provides a single resolver that prefers, in order:

    1. Values written into a fitted-params JSON file
       (default: ``state/hnc_fitted_params.json`` next to the lambda
       history that LambdaEngine already persists).
    2. Environment variable overrides
       (AUREON_HNC_ALPHA / _G / _BETA / _TAU / _DELTA_T).
    3. The hardcoded defaults from ``aureon_lambda_engine.py``.

Why a separate module rather than editing the engine globals: the engine
already has a working env-var override path for BETA. This module
generalises that pattern to all five tunables and adds the JSON file
layer, without disturbing the kernel math itself. Callers patch the
module globals at startup (see ``apply_to_lambda_engine``).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Resolve the same state directory LambdaEngine writes lambda_history.json to.
# aureon/core/hnc_params.py -> parents[2] is the repo root.
DEFAULT_STATE_DIR = Path(__file__).resolve().parents[2] / "state"
DEFAULT_PARAMS_PATH = DEFAULT_STATE_DIR / "hnc_fitted_params.json"


@dataclass
class HNCParams:
    """Fitted (or default) values of the five HNC tunables."""
    alpha: float = 0.35     # Observer gain
    g: float = 2.5          # tanh nonlinearity gain
    beta: float = 1.0       # Echo (lighthouse memory) gain
    tau: int = 10           # Lighthouse echo delay, samples
    delta_t: int = 5        # Observer moving-average window, samples
    fitted_at: Optional[float] = None  # unix ts when these were fit
    fitted_from: Optional[str] = None  # data window or commit hash
    r_squared: Optional[float] = None  # fit quality if available

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("HNC param env var %s=%r is not a float; using %r", name, raw, default)
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("HNC param env var %s=%r is not an int; using %r", name, raw, default)
        return default


def load_params(path: Optional[Path] = None) -> HNCParams:
    """Load HNC parameters from JSON file → env → hardcoded defaults.

    The JSON file shape matches ``HNCParams`` (alpha, g, beta, tau, delta_t,
    plus optional metadata). Missing keys fall through to env vars; missing
    env vars fall through to defaults.
    """
    file_path = path or DEFAULT_PARAMS_PATH

    file_data: dict = {}
    if file_path.exists():
        try:
            file_data = json.loads(file_path.read_text(encoding="utf-8"))
            logger.info("HNC params loaded from %s", file_path)
        except Exception as exc:
            logger.warning("HNC params file %s unreadable (%s); ignoring", file_path, exc)
            file_data = {}

    return HNCParams(
        alpha=float(file_data.get("alpha", _env_float("AUREON_HNC_ALPHA", 0.35))),
        g=float(file_data.get("g", _env_float("AUREON_HNC_G", 2.5))),
        beta=float(file_data.get("beta", _env_float("AUREON_HNC_BETA", 1.0))),
        tau=int(file_data.get("tau", _env_int("AUREON_HNC_TAU", 10))),
        delta_t=int(file_data.get("delta_t", _env_int("AUREON_HNC_DELTA_T", 5))),
        fitted_at=file_data.get("fitted_at"),
        fitted_from=file_data.get("fitted_from"),
        r_squared=file_data.get("r_squared"),
    )


def apply_to_lambda_engine(params: Optional[HNCParams] = None) -> HNCParams:
    """Patch the module-level constants in ``aureon_lambda_engine``.

    LambdaEngine reads ALPHA / G / BETA / TAU / DELTA_T from its module
    globals at every step(), so writing them at startup is enough — no
    engine refactor required. Returns the params that were applied.
    """
    if params is None:
        params = load_params()
    from aureon.core import aureon_lambda_engine as _engine
    _engine.ALPHA = params.alpha
    _engine.G = params.g
    _engine.BETA = params.beta
    _engine.TAU = params.tau
    _engine.DELTA_T = params.delta_t
    return params


def save_params(params: HNCParams, path: Optional[Path] = None) -> Path:
    """Atomic write of fitted params (uses LambdaEngine's tmp-then-rename pattern)."""
    file_path = path or DEFAULT_PARAMS_PATH
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_path.with_suffix(file_path.suffix + ".tmp")
    tmp.write_text(params.to_json(), encoding="utf-8")
    os.replace(tmp, file_path)
    return file_path
