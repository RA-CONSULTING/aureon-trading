from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def run_command(command: Sequence[str], timeout: int) -> int:
    result = subprocess.run(command, timeout=timeout)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Post-build smoke test for aureon.exe")
    parser.add_argument("--binary", required=True, help="Path to aureon.exe")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for process exit")
    args = parser.parse_args()

    exe_path = Path(args.binary)
    if not exe_path.exists():
        sys.exit(f"Binary not found at {exe_path}")

    return_code = run_command([str(exe_path), "--start", "--no-dashboard"], timeout=args.timeout)
    if return_code != 0:
        sys.exit(f"Smoke test failed with exit code {return_code}")

    print("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
