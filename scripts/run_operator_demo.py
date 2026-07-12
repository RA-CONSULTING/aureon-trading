#!/usr/bin/env python3
"""
Aureon Operator — end-to-end demo.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run one prompt through the switchboard and print the whole cascade: which AI
lines answered, what the Aureon repo grounded it on, how the answers agreed, the
Queen's conscience verdict, and the final collapsed answer with its trace_id.

    python scripts/run_operator_demo.py "How does Aureon integrate data across systems?"

Runs fully offline with no API keys (stub/local adapters). Set OPENAI_API_KEY /
XAI_API_KEY / GEMINI_API_KEY to fan out across live models. Force offline with
AUREON_LLM_OFFLINE=1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the repo importable when run directly (mirrors conftest.py path setup).
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from aureon.operator import AureonOperator  # noqa: E402
from aureon.operator.providers import build_provider_set, describe_provider_set  # noqa: E402


def _rule(title: str) -> None:
    print(f"\n\033[35m{'─' * 3} {title} {'─' * max(0, 60 - len(title))}\033[0m")


def main(argv: list) -> int:
    prompt = " ".join(argv[1:]).strip() or "How does Aureon integrate data across systems?"

    providers = build_provider_set()
    operator = AureonOperator(providers=providers)

    print("\033[36m🎛️  AUREON OPERATOR SWITCHBOARD\033[0m")
    print(f"    offline_guard = {os.environ.get('AUREON_LLM_OFFLINE', '0')}")
    print("    lines         = " + ", ".join(
        f"{p['name']}({p['adapter']})" for p in describe_provider_set(providers)
    ))
    print(f"    prompt        = {prompt!r}")

    resp = operator.respond(prompt)

    _rule("GROUND (repo context)")
    if resp.grounding:
        print(f"lane={resp.grounding.lane or '—'}  task={resp.grounding.task_family or '—'}  "
              f"system_prompt={resp.grounding.system_prompt_chars} chars")
        for s in resp.grounding.sources:
            print(f"  • {s.get('title', '')}  ({s.get('path', '')})")
        if not resp.grounding.sources:
            print("  (no source packets matched — grounded on persona only)")

    _rule("FAN-OUT (per line)")
    for a in resp.answers:
        head = (a.text[:120] + "…") if len(a.text) > 120 else a.text
        status = "ok" if a.ok else f"ERR:{a.error[:40]}"
        print(f"  [{a.provider}/{a.model}] {a.latency_ms:.0f}ms {status}\n     {head}")

    _rule("CONSENSUS (collapse)")
    if resp.consensus:
        c = resp.consensus
        print(f"n_answers={c.n_answers}  agreement={c.agreement:.2%}  "
              f"winner={c.winner or '—'}  synthesized={c.synthesized}")
        if c.runner_ups:
            print(f"  runner-ups: {', '.join(c.runner_ups)}")

    _rule("VETO (Queen's conscience)")
    print(f"verdict={resp.conscience_verdict}  blocked={resp.blocked}")
    if resp.conscience_message:
        print(f"  🦗 {resp.conscience_message}")

    _rule("ANSWER")
    print(resp.text)

    _rule("TRACE")
    print(f"trace_id={resp.trace_id}  elapsed={resp.elapsed_ms:.0f}ms")
    print("phases: " + " → ".join(
        f"{k}:{'✓' if v else '·'}" for k, v in resp.phase_thought_ids.items()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
