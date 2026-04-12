#!/usr/bin/env python3
"""
run_integrated_cognitive_system.py -- Entry point for the Aureon ICS

Boots all cognitive subsystems, starts the live terminal dashboard,
and accepts user goals via stdin.

Usage:
    python run_integrated_cognitive_system.py
"""

import io
import logging
import sys

# Force UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

from aureon.core.integrated_cognitive_system import IntegratedCognitiveSystem


def main() -> None:
    ics = IntegratedCognitiveSystem()
    try:
        ics.run()
    except KeyboardInterrupt:
        pass
    finally:
        ics.shutdown()


if __name__ == "__main__":
    main()
