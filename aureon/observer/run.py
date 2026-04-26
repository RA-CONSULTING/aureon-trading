"""``python -m aureon.observer.run`` — standalone HNC field observer.

Two run modes:

  1. **Tail mode (default)**: tail an existing JSONL trace produced by
     ``aureon/core/hnc_live_daemon.py`` and feed it through a
     HarmonicObserver. Useful when the live daemon is already running
     elsewhere and you want a separate observer process — for instance,
     to record ThoughtBus events into a dedicated log without touching
     the daemon's process.

  2. **Daemon-attached mode** (``--with-daemon``): start an HNCLiveDaemon
     in this process with attach_observer=True. Equivalent to running
     ``python -m aureon.core.hnc_live_daemon`` but with a final
     human-readable rocks summary on shutdown.

Either way, on exit the runner prints (a) the active rock catalogue,
(b) the metrics snapshot, (c) the JSON-serialisable state of the
observer at shutdown. ``--json`` makes the entire output machine-readable.

Tail-mode JSONL contract — matches HNCLiveDaemon._append_trace:
  {"ts": float, "step": int, "lambda_t": float,
   "consciousness_psi": float, "consciousness_level": str,
   "coherence_gamma": float, ...}
The runner constructs a duck-typed object from each line and calls
``observer.ingest_state(state)`` so psi / level flow through the same
path the live daemon uses.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aureon.observer.run")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_PATH = REPO_ROOT / "state" / "hnc_live_trace.jsonl"


@dataclass
class _DuckLambdaState:
    """Subset of LambdaState fields the observer's ingest_state reads."""
    lambda_t: float
    timestamp: float
    consciousness_psi: Optional[float] = None
    consciousness_level: Optional[str] = None
    coherence_gamma: Optional[float] = None


def _row_to_state(row: dict) -> Optional[_DuckLambdaState]:
    """Translate a trace JSONL row to a state object the observer accepts."""
    lt = row.get("lambda_t")
    ts = row.get("ts")
    if lt is None or ts is None:
        return None
    try:
        return _DuckLambdaState(
            lambda_t=float(lt),
            timestamp=float(ts),
            consciousness_psi=row.get("consciousness_psi"),
            consciousness_level=row.get("consciousness_level"),
            coherence_gamma=row.get("coherence_gamma"),
        )
    except (TypeError, ValueError):
        return None


def _print_final(observer, as_json: bool) -> None:
    snap = observer.metrics_snapshot()
    if as_json:
        print(json.dumps({
            "snapshot": snap,
            "rocks_active": [r.to_dict() for r in observer.current_rocks()],
        }, indent=2, sort_keys=True, default=str))
        return

    print()
    print("HNC Observer — final state")
    print("─" * 40)
    print(f"  uptime              : {snap.get('uptime_s', 0.0):.1f}s")
    print(f"  samples (fast/slow) : {snap.get('n_samples_fast')} / {snap.get('n_samples_slow')}")
    print(f"  ingested            : {snap.get('n_ingested')}")
    print(f"  ThoughtBus events   : {snap.get('n_events_emitted')}")
    print(f"  regime              : {snap.get('regime')}")
    print(f"  coherence_score     : {snap.get('coherence_score'):.3f}")
    latest = snap.get("latest_field") or {}
    if latest.get("lambda_t") is not None:
        print(f"  last lambda_t       : {latest.get('lambda_t'):.4f}")
    if latest.get("consciousness_psi") is not None:
        print(f"  last psi            : {latest.get('consciousness_psi'):.4f} "
              f"({latest.get('consciousness_level')})")
    rocks = observer.current_rocks()
    if rocks:
        print(f"  active rocks        : {len(rocks)}")
        for r in rocks[:10]:
            print(f"    - {r.kind:>10} {r.scale:>4} "
                  f"hz={r.dominant_hz:7.3f} amp={r.amplitude:7.3f} "
                  f"z={r.z_score:5.2f} persist={r.persistence_s:6.1f}s")
    else:
        print("  active rocks        : (none yet — feed more samples)")
    print()


# ─── tail mode ─────────────────────────────────────────────────────

async def _tail_jsonl(
    path: Path,
    observer,
    duration_s: Optional[float],
    poll_interval_s: float,
    from_start: bool,
) -> None:
    """Tail ``path`` and feed each new JSONL row to ``observer.ingest_state``.

    If ``from_start`` is True, also process every line already in the
    file before tailing — useful for replaying a recorded trace.
    """
    deadline = (time.time() + duration_s) if duration_s else None
    stop = asyncio.Event()

    def _handle_sig():
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_sig)
        except (NotImplementedError, RuntimeError):
            pass

    # Wait for the file to appear.
    while not path.exists():
        if stop.is_set():
            return
        if deadline and time.time() >= deadline:
            return
        logger.info("waiting for trace at %s...", path)
        try:
            await asyncio.wait_for(stop.wait(), timeout=2.0)
            return
        except asyncio.TimeoutError:
            pass

    # Open and seek.
    n_processed = 0
    with open(path, "r", encoding="utf-8") as fh:
        if not from_start:
            fh.seek(0, 2)  # end of file
        buf = ""
        while not stop.is_set():
            if deadline and time.time() >= deadline:
                break
            chunk = fh.read()
            if chunk:
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    state = _row_to_state(row)
                    if state is not None:
                        observer.ingest_state(state)
                        n_processed += 1
            else:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=poll_interval_s)
                except asyncio.TimeoutError:
                    pass

    logger.info("tail mode processed %d rows from %s", n_processed, path)


# ─── daemon-attached mode ──────────────────────────────────────────

async def _run_with_daemon(duration_s: Optional[float], observer) -> None:
    from aureon.core.hnc_live_daemon import HNCLiveDaemon
    daemon = HNCLiveDaemon(attach_observer=False, observer=observer)
    # We pre-built the observer ourselves (so the runner can print on
    # exit); pass it in so the daemon doesn't construct a second one.
    daemon._observer = observer
    await daemon.run(duration_s=duration_s)


# ─── CLI ───────────────────────────────────────────────────────────

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aureon.observer.run",
        description="Standalone HNC field observer — tail an existing trace "
                    "or run with an in-process live daemon.",
    )
    parser.add_argument("--with-daemon", action="store_true",
                        help="Start an HNCLiveDaemon in-process and attach "
                             "the observer to it. Default tails the trace JSONL.")
    parser.add_argument("--trace-path", type=Path, default=DEFAULT_TRACE_PATH,
                        help=f"Trace JSONL to tail (default: {DEFAULT_TRACE_PATH}).")
    parser.add_argument("--duration", type=float, default=None,
                        help="Stop after N seconds. Default: run until SIGINT.")
    parser.add_argument("--poll-interval", type=float, default=1.0,
                        help="Tail poll interval in seconds (default 1.0).")
    parser.add_argument("--from-start", action="store_true",
                        help="Tail mode: replay the trace from beginning "
                             "before tailing. Default starts at end-of-file.")
    parser.add_argument("--fast-window-min", type=float, default=360.0,
                        help="Fast observation window in minutes (default 360 = 6h).")
    parser.add_argument("--slow-window-min", type=float, default=20160.0,
                        help="Slow observation window in minutes (default 20160 = 14d).")
    parser.add_argument("--no-publish", action="store_true",
                        help="Disable ThoughtBus publishing.")
    parser.add_argument("--json", action="store_true",
                        help="Emit final state as JSON instead of human text.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=os.environ.get("AUREON_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from aureon.observer import HarmonicObserver
    observer = HarmonicObserver(
        fast_window_minutes=args.fast_window_min,
        slow_window_minutes=args.slow_window_min,
        publish_to_bus=not args.no_publish,
    )

    try:
        if args.with_daemon:
            asyncio.run(_run_with_daemon(args.duration, observer))
        else:
            asyncio.run(_tail_jsonl(
                path=args.trace_path,
                observer=observer,
                duration_s=args.duration,
                poll_interval_s=args.poll_interval,
                from_start=args.from_start,
            ))
    except KeyboardInterrupt:
        return 130
    finally:
        _print_final(observer, as_json=args.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
