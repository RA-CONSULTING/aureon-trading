#!/usr/bin/env python3
"""Bridge into Gary's WorldDataIngester for the flAmeBorn app."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_ingester(gary_root: Path):
    if not gary_root.exists():
        raise FileNotFoundError(f"Gary repo root not found: {gary_root}")
    sys.path.insert(0, str(gary_root))
    from aureon.integrations.world_data.world_data_ingester import get_world_data_ingester

    return get_world_data_ingester()


def main() -> int:
    parser = argparse.ArgumentParser(description="Query Gary's WorldDataIngester and emit JSON.")
    parser.add_argument("--gary-root", required=True, help="Path to Gary's aureon-trading repo")
    parser.add_argument("--query", required=True, help="Research query")
    parser.add_argument("--limit", type=int, default=3, help="Items per source hint")
    args = parser.parse_args()

    gary_root = Path(args.gary_root).expanduser().resolve()
    ingester = load_ingester(gary_root)
    items = ingester.answer_question(args.query, n_per_source=max(1, min(6, args.limit)))
    payload = {
        "query": args.query,
        "limit": max(1, min(6, args.limit)),
        "items": [item.to_dict() for item in items],
        "status": ingester.get_status(),
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
