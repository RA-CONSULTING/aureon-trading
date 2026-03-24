#!/usr/bin/env python3
"""Quick health check for system flow and ThoughtBus/Mycelium wiring."""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import argparse
import json
from pathlib import Path


DEFAULT_SNAPSHOT = Path("state/dashboard_snapshot.json")
DEFAULT_THOUGHT_LOG = Path("logs/aureon_thoughts.jsonl")


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_last_jsonl(path: Path, limit: int):
    if not path.exists() or limit <= 0:
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def main():
    parser = argparse.ArgumentParser(description="Check system flow status and ThoughtBus/Mycelium wiring.")
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--thought-log", default=str(DEFAULT_THOUGHT_LOG))
    parser.add_argument("--tail", type=int, default=0, help="Show last N ThoughtBus events")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    thought_log_path = Path(args.thought_log)

    snapshot = _read_json(snapshot_path)
    if not snapshot:
        print(f"Snapshot not found or unreadable: {snapshot_path}")
    else:
        flight = snapshot.get("flight_check", {})
        summary = (flight.get("summary") or {})
        total = summary.get("total_systems")
        online = summary.get("online_systems")
        online_pct = summary.get("online_pct")
        critical = summary.get("critical_online")
        print("System Flow Summary")
        print(f"  total_systems: {total}")
        print(f"  online_systems: {online}")
        print(f"  online_pct: {online_pct}")
        print(f"  critical_online: {critical}")
        print("")
        print("Key Wiring (flight_check)")
        for key in ("thought_bus", "mycelium_network", "intelligence_engine", "feed_hub", "stargate", "quantum_mirror"):
            if key in flight:
                print(f"  {key}: {flight.get(key)}")
        print("")
        registry = snapshot.get("systems_registry", {})
        if registry:
            print("Systems Registry")
            for key in ("ThoughtBus", "Miner Brain", "Ultimate Intel", "Wave Scanner", "Quantum Mirror", "Timeline Oracle"):
                if key in registry:
                    print(f"  {key}: {registry.get(key)}")

    if args.tail:
        print("")
        print(f"Last {args.tail} ThoughtBus events: {thought_log_path}")
        events = _read_last_jsonl(thought_log_path, args.tail)
        for ev in events:
            topic = ev.get("topic")
            source = ev.get("source")
            ts = ev.get("ts")
            print(f"  ts={ts} source={source} topic={topic}")


if __name__ == "__main__":
    main()
