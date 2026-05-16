"""Aureon adaptive local skill capsule.

Generated for a client prompt at query time. This capsule is intentionally
local-only: it records the request, exposes a deterministic run contract, and
can be enhanced by the coding organism once the client approves the direction.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone


PROMPT = 'Build a local barcode label generator tool for the warehouse team, with run instructions and proof.\n\nClient-approved scope answers:\n- deliverables: Adaptive local skill capsule, browser preview, runbook, Python run contract, and proof.\n- target_system: frontend/public/aureon_adaptive_skills and Aureon coding cockpit artifact preview.\n- constraints: Local-only, no live trading, payment, filing, credential, or destructive OS action.\n- goal: Build a local barcode label generator tool for the warehouse team.\n- acceptance: The skill capsule files exist, preview URL works, and no blocking snags remain.'
TASK_FAMILY = 'mixed'
DETECTED_FAMILIES = ['coding', 'ui', 'document', 'browser_qa']


def run(input_text: str = "") -> dict:
    """Return a local, testable result packet for this adaptive skill."""
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_family": TASK_FAMILY,
        "detected_families": DETECTED_FAMILIES,
        "prompt": PROMPT,
        "input_text": input_text,
        "result": "Adaptive skill capsule is ready for local enhancement and client review.",
        "authority": "local-only; no live trading, payment, filing, credential, or destructive OS action",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
