"""Compatibility shim for legacy baton-link imports.

Many modules call `link_system(__name__)` at import time; this shim keeps
those imports operational in minimal/runtime-test environments.
"""

from __future__ import annotations

from typing import Any


def link_system(_name: str, *_args: Any, **_kwargs: Any) -> bool:
    """No-op link hook used by legacy modules.

    Returns True so callers can treat the link as successful.
    """
    return True
