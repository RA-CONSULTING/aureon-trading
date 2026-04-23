"""
Aureon Path Registry
====================

The README references many files by their ORIGINAL flat paths (pre-reorganisation).
This module resolves those original names to their current PEFCφS / domain locations.

Usage:
    from META.PATH_REGISTRY import resolve, list_by_domain

    path = resolve("stargate_grid.py")
    # → "3_forcing/coherence_gates/stargate_grid.py"

    research_files = list_by_domain("research")
    # → [{"filename": "stargate_grid.py", "location": "...", "purpose": "..."}, ...]
"""

import json
from pathlib import Path

_META_DIR = Path(__file__).parent
_CATALOG_PATH = _META_DIR / "CATALOG.json"
_REPO_ROOT = _META_DIR.parent


def _load_catalog() -> dict:
    with open(_CATALOG_PATH) as f:
        return json.load(f)


_catalog = _load_catalog()


def resolve(original_name: str) -> str | None:
    """
    Resolve an original flat filename to its current location.
    Returns None if the file is not in the README-critical list.
    """
    entry = _catalog["readme_critical_files"].get(original_name)
    if entry and entry["current_location"] != "NOT_FOUND":
        return entry["current_location"]
    return None


def resolve_absolute(original_name: str) -> Path | None:
    """Return an absolute Path to the file, or None if not found."""
    rel = resolve(original_name)
    if rel is None:
        return None
    return _REPO_ROOT / rel


def get_metadata(original_name: str) -> dict | None:
    """Get full metadata for a README-critical file."""
    return _catalog["readme_critical_files"].get(original_name)


def list_by_domain(domain: str) -> list[dict]:
    """List all README-critical files in a given domain."""
    return _catalog["files_by_domain"].get(domain, [])


def list_domains() -> dict:
    """Return the domain definitions."""
    return _catalog["domains"]


def print_all():
    """Print all README-critical files grouped by domain."""
    for dom_key, dom_info in _catalog["domains"].items():
        files = list_by_domain(dom_key)
        if not files:
            continue
        print(f"\n=== {dom_info['name']} ===")
        print(f"    {dom_info['description']}")
        print()
        for entry in files:
            print(f"  {entry['filename']:45s} → {entry['current_location']}")
            print(f"    purpose: {entry['purpose']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print_all()
    elif len(sys.argv) == 2:
        name = sys.argv[1]
        result = resolve(name)
        meta = get_metadata(name)
        if result:
            print(f"Filename:    {name}")
            print(f"Location:    {result}")
            print(f"Domain:      {meta['domain']} / {meta['subdomain']}")
            print(f"Purpose:     {meta['purpose']}")
        else:
            print(f"Not found: {name}")
            print("\nAvailable README-critical files:")
            for fname in sorted(_catalog["readme_critical_files"].keys()):
                print(f"  - {fname}")
