"""
Pytest conftest.py for Aureon Trading.

Bootstraps the PEFCφS layer paths so tests can import modules from any layer
using the original flat-module names that existed before reorganization.
"""

import bootstrap_paths  # noqa: F401
