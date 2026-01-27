#!/usr/bin/env python3
"""Live viewer for baton relay events."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


DEFAULT_LOG = Path("state/baton_relay.jsonl")


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _match_filter(event: dict, filter_type: str | None) -> bool:
    if not filter_type:
        return True
    return event.get("type") == filter_type


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream baton relay events.")
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--follow", action="store_true", help="Follow log for new events")
    parser.add_argument("--limit", type=int, default=20, help="Show last N events before following")
    parser.add_argument("--filter", choices=["stage", "handoff", "stale", "stage_out_of_order"], help="Filter by event type")
    args = parser.parse_args()

    log_path = Path(args.log)
    lines = _read_lines(log_path)
    if args.limit and lines:
        for line in lines[-args.limit:]:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if _match_filter(event, args.filter):
                print(event)

    if not args.follow:
        return

    last_len = len(lines)
    while True:
        time.sleep(1.0)
        lines = _read_lines(log_path)
        if len(lines) <= last_len:
            continue
        for line in lines[last_len:]:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if _match_filter(event, args.filter):
                print(event)
        last_len = len(lines)


if __name__ == "__main__":
    main()
