"""
Cognition ingress — CLI entry point for the goal router.

A prompt drops in; the pipeline bends it through seven phases. Usage::

    python -m aureon.cognition.ingress --prompt "echo hello world"

The default ThoughtBus singleton persists to ``thoughts.jsonl`` at the
CWD, so the CognitiveDashboard can tail it live.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from aureon.cognition.pipeline import CognitionPipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aureon.cognition.ingress",
        description="Submit a prompt to the seven-phase cognition pipeline.",
    )
    parser.add_argument("--prompt", required=True, help="The user prompt to route.")
    parser.add_argument("--peer-id", default=None, help="Optional peer identifier.")
    parser.add_argument("--session-id", default=None, help="Optional session identifier.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the final envelope as JSON on stdout.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    pipeline = CognitionPipeline()
    env = pipeline.run(args.prompt, peer_id=args.peer_id, session_id=args.session_id)
    if args.json:
        print(json.dumps(env.to_dict(), indent=2, default=str))
    else:
        collapsed = env.collapsed
        winner_text = collapsed.text if collapsed else ""
        print(f"trace_id        = {env.trace_id}")
        print(f"primary_verb    = {env.intent.primary_verb if env.intent else 'unknown'}")
        print(f"n_branches      = {env.complexity.n_branches if env.complexity else 0}")
        print(f"winning_branch  = {collapsed.winning_branch_id if collapsed else ''}")
        print(f"collapsed_text  = {winner_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
