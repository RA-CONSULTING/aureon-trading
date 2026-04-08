"""Import this module early in entry-point scripts to ensure all aureon/
subdirectories are on sys.path.  This keeps bare module-name imports working
after the repository reorganisation.

Usage (at the top of a runner script)::

    import aureon._path_setup  # noqa: F401
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUREON = os.path.join(_ROOT, "aureon")

for _dirpath, _dirnames, _ in os.walk(_AUREON):
    _dirnames[:] = [d for d in _dirnames if not d.startswith(("__pycache__", "."))]
    if _dirpath not in sys.path:
        sys.path.insert(0, _dirpath)

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
