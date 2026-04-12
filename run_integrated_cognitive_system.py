#!/usr/bin/env python3
"""
run_integrated_cognitive_system.py -- Entry point for the Aureon ICS

Boots all cognitive subsystems, starts the live terminal dashboard,
launches the Vault UI + Phi Bridge server for phone communication,
and accepts user goals via stdin.

Usage:
    python run_integrated_cognitive_system.py
    python run_integrated_cognitive_system.py --lan
    python run_integrated_cognitive_system.py --lan --port 8080
"""

import argparse
import io
import logging
import sys

# Force UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from aureon.core.integrated_cognitive_system import IntegratedCognitiveSystem


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aureon Integrated Cognitive System — all subsystems as one organism",
    )
    parser.add_argument(
        "--lan", action="store_true",
        help="Bind on 0.0.0.0 so phones on the same WiFi can reach the "
             "Phi Bridge at http://<LAN_IP>:<port>/bridge",
    )
    parser.add_argument(
        "--port", type=int, default=5566,
        help="Port for the Vault UI + Phi Bridge server (default 5566)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    ics = IntegratedCognitiveSystem()
    try:
        ics.run(lan=args.lan, port=args.port)
    except KeyboardInterrupt:
        pass
    finally:
        ics.shutdown()


if __name__ == "__main__":
    main()
