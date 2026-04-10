#!/usr/bin/env python3
"""
run_vault_ui.py — Launch the Aureon Vault UI for communicating with the vault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starts a Flask server on the configured port, serves the chat UI at /,
and optionally starts the self-feedback loop daemon so the vault is
alive while you talk to it.

Usage:
    python scripts/runners/run_vault_ui.py
    python scripts/runners/run_vault_ui.py --port 5566 --start-loop
    python scripts/runners/run_vault_ui.py --host 0.0.0.0 --port 8080 --interval 0.5
"""

from __future__ import annotations

import argparse
import logging
import os
import sys


def _setup_path() -> None:
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo not in sys.path:
        sys.path.insert(0, repo)


def main() -> None:
    _setup_path()

    parser = argparse.ArgumentParser(
        description="Launch the Aureon Vault UI for communicating with the vault",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5566, help="bind port (default 5566)")
    parser.add_argument(
        "--start-loop", action="store_true",
        help="also start the self-feedback loop daemon in the background",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="base interval seconds for the love+gratitude clock (default 1.0)",
    )
    parser.add_argument(
        "--no-voice", action="store_true",
        help="disable the voice layer (chat endpoints will 400)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="verbose logging",
    )
    args = parser.parse_args()

    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import run_server

    loop = AureonSelfFeedbackLoop(
        base_interval_s=args.interval,
        enable_voice=not args.no_voice,
    )

    print("=" * 72)
    print("  AUREON VAULT UI — Queen's Voice")
    print("=" * 72)
    print(f"  Loop ID:     {loop.loop_id}")
    print(f"  Voice layer: {'ENABLED' if loop.voice_engine else 'DISABLED'}")
    print(f"  Bind:        http://{args.host}:{args.port}/")
    print(f"  Interval:    {args.interval}s")
    print(f"  Background:  {'YES' if args.start_loop else 'no (use /api/loop/start to wake it)'}")
    print("=" * 72)
    print()
    print("  Open the URL in a browser to chat with the vault.")
    print("  Send a message, press Converse, or click Run one tick.")
    print("  Press Ctrl-C to stop.")
    print()

    try:
        run_server(
            host=args.host,
            port=args.port,
            loop=loop,
            start_loop=args.start_loop,
        )
    except KeyboardInterrupt:
        print("\nShutting down vault UI...")
        try:
            loop.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
