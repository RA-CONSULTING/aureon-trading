"""``python -m aureon.status`` — headless HNC field state.

Two modes:

  1. **One-shot read** (default): print whatever was last persisted by a
     running daemon. Reads ``state/lambda_history.json`` (the LambdaEngine
     auto-persist file) and the most recent line of
     ``state/hnc_live_trace.jsonl`` (the daemon trace), formats them, and
     exits. Cheap; doesn't start a daemon.

  2. **Probe** (``--probe N``): start an in-process HNC daemon, run for N
     seconds, print the resulting state, exit. Useful when the
     long-running daemon isn't up yet and you just want to see the field
     compute against current real data.

Output format is a small dict (``--json`` for machine-readable, default
for human-readable). Designed to be supervisord/cron-safe: no colors, no
prompts, exits non-zero on hard error.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

from aureon.core.hnc_params import DEFAULT_PARAMS_PATH, load_params

REPO_ROOT = Path(__file__).resolve().parents[1]
LAMBDA_HISTORY_PATH = REPO_ROOT / "state" / "lambda_history.json"
TRACE_PATH = REPO_ROOT / "state" / "hnc_live_trace.jsonl"


def _read_last_jsonl(path: Path) -> Optional[dict]:
    """Read the last line of a JSONL file. Returns None if empty/missing."""
    if not path.exists():
        return None
    try:
        # tail-style read — small files: just read all.
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            if size == 0:
                return None
            chunk = min(size, 8192)
            fh.seek(-chunk, 2)
            tail = fh.read().decode("utf-8", errors="replace")
        last_line = next((ln for ln in reversed(tail.splitlines()) if ln.strip()), "")
        return json.loads(last_line) if last_line else None
    except Exception:
        return None


def _read_lambda_history() -> Optional[dict]:
    if not LAMBDA_HISTORY_PATH.exists():
        return None
    try:
        return json.loads(LAMBDA_HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_human(state: dict, params: dict, params_path: Path) -> str:
    lines = ["HNC Live Field — status"]
    if not state:
        lines.append("  (no live trace yet — start the daemon, or run with --probe)")
    else:
        ts = state.get("ts")
        age = (time.time() - ts) if ts else None
        lines.append(f"  step:                {state.get('step')}")
        lines.append(f"  Λ_full:              {state.get('lambda_t'):.6f}")
        lines.append(f"  ψ (consciousness):   {state.get('consciousness_psi'):.4f}")
        lines.append(f"  level:               {state.get('consciousness_level')}")
        lines.append(f"  coherence Γ:         {state.get('coherence_gamma'):.4f}")
        lines.append(f"  symbolic life score: {state.get('symbolic_life_score'):.4f}")
        if age is not None:
            lines.append(f"  last update:         {age:.1f}s ago")
        sources = state.get("sources") or {}
        if sources:
            lines.append("  sources online:")
            for name, payload in sources.items():
                lines.append(
                    f"    - {name}: value={payload.get('value'):.3f} "
                    f"conf={payload.get('confidence'):.2f} "
                    f"state={payload.get('state')!r}"
                )
    lines.append("")
    lines.append("HNC parameters:")
    lines.append(f"  α={params.get('alpha')} g={params.get('g')} "
                 f"β={params.get('beta')} τ={params.get('tau')} "
                 f"Δt={params.get('delta_t')}")
    if params.get("fitted_at"):
        lines.append(f"  fitted_at={params.get('fitted_at')} "
                     f"R²={params.get('r_squared')} from {params.get('fitted_from')}")
        lines.append(f"  source: {params_path}")
    else:
        lines.append("  (defaults — no fitted-params file present)")
    return "\n".join(lines)


def _format_json(state: dict, params: dict) -> str:
    return json.dumps({"state": state, "params": params}, indent=2, sort_keys=True)


async def _probe(seconds: float) -> dict:
    """Run a short in-process daemon, return last state dict."""
    from aureon.core.hnc_live_daemon import HNCLiveDaemon
    daemon = HNCLiveDaemon()
    await daemon.run(duration_s=seconds)
    return daemon.current_state or {}


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="aureon.status",
                                     description="Headless HNC field state.")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of human text.")
    parser.add_argument("--probe", type=float, metavar="SECONDS", default=None,
                        help="Start an in-process daemon for N seconds and "
                             "print the resulting state. Default: read the "
                             "last-persisted state without running anything.")
    args = parser.parse_args(argv)

    params_path = DEFAULT_PARAMS_PATH
    params_obj = load_params()
    params_dict = {
        "alpha": params_obj.alpha,
        "g": params_obj.g,
        "beta": params_obj.beta,
        "tau": params_obj.tau,
        "delta_t": params_obj.delta_t,
        "fitted_at": params_obj.fitted_at,
        "fitted_from": params_obj.fitted_from,
        "r_squared": params_obj.r_squared,
    }

    if args.probe:
        try:
            state = asyncio.run(_probe(args.probe))
        except KeyboardInterrupt:
            return 130
        # Fold sources from the in-process daemon into the trace shape.
    else:
        state = _read_last_jsonl(TRACE_PATH) or {}

    if args.json:
        print(_format_json(state, params_dict))
    else:
        print(_format_human(state, params_dict, params_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
