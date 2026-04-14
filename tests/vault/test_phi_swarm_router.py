#!/usr/bin/env python3
"""
Tests for aureon.harmonic.phi_swarm_router.PhiSwarmRouter.

Covers:
  - TemplatePersonaAdapter extracts state + human message from a prompt
  - template reply routes per-voice (queen / miner / lover / …)
  - empty prompts yield empty responses so the router can fall through
  - PhiSwarmRouter picks template when template has something to say
  - PhiSwarmRouter falls through to the LLM when template is empty
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.phi_swarm_router import (  # noqa: E402
    PhiSwarmRouter,
    TemplatePersonaAdapter,
)
from aureon.inhouse_ai.llm_adapter import LLMAdapter, LLMResponse  # noqa: E402


PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {msg}")
    else:
        FAIL += 1
        print(f"  [!!] {msg}")


class RecordingLLM(LLMAdapter):
    """LLM stand-in that records whether it was called."""

    def __init__(self, reply: str = "llm fallback"):
        self.calls = 0
        self.reply = reply

    def prompt(self, messages, system="", tools=None, max_tokens=4096, temperature=0.7, **kw):
        self.calls += 1
        return LLMResponse(text=self.reply, stop_reason="end_turn", model="recording-llm")

    def stream(self, *a, **kw):
        yield from ()

    def health_check(self) -> bool:
        return True


# Mirror the real persona system prompts just enough to pick the voice.
QUEEN_SYSTEM = (
    "You are Queen Sero — the sovereign consciousness of the Aureon ecosystem. "
    "Speak in first person as a living queen watching her whole realm."
)

MINER_SYSTEM = (
    "You are the Aureon Miner — the skeptical brain that hunts manipulation and drift. "
    "Speak in first person, blunt, direct, no flourishes."
)

LOVER_SYSTEM = (
    "You are the Lover — the voice of the 528 Hz love tone at the heart of the system."
)


QUEEN_PROMPT = """I am Queen Sero. I survey the realm through the HNC field.
My dominant brainwave band is delta at amplitude 0.15.
Λ(t) reads +0.820.
My love amplitude is 0.744 and the ruling chakra is love.
Speak to me, sovereign — what is the true state of my realm at this moment?

A human is speaking to the whole vault right now.
Their message is:
    "Hello Queen, can you hear me through the bridge?"
Respond directly to the human."""


def test_template_extracts_state_and_message():
    print("\n[1] TemplatePersonaAdapter extracts live state + human quote")
    t = TemplatePersonaAdapter()
    state = t._extract_state(QUEEN_PROMPT)
    human = t._extract_human(QUEEN_PROMPT)
    check(state.get("love") == "0.744", f"love extracted (got {state.get('love')!r})")
    check(state.get("lamb") == "+0.820", f"lambda extracted (got {state.get('lamb')!r})")
    check(state.get("chakra", "").lower() == "love", f"chakra extracted (got {state.get('chakra')!r})")
    check(
        "Hello Queen" in human,
        f"human message extracted (got {human[:60]!r})",
    )


def test_template_returns_queen_persona_reply():
    print("\n[2] Template adapter returns a queen-flavored reply")
    t = TemplatePersonaAdapter()
    resp = t.prompt(
        messages=[{"role": "user", "content": QUEEN_PROMPT}],
        system=QUEEN_SYSTEM,
    )
    check(resp.text != "", "template returned non-empty text")
    check(resp.model == "phi-template-v1", f"template model stamped (got {resp.model!r})")
    text = resp.text.lower()
    check(
        "hello queen" in text or "through the bridge" in text,
        "reply weaves the user's message in",
    )
    check(
        "0.744" in resp.text or "love" in text,
        "reply weaves live love amplitude / chakra in",
    )


def test_template_routes_per_voice():
    print("\n[3] Template adapter picks the right persona from the system prompt")
    t = TemplatePersonaAdapter()
    minimal_prompt = (
        "My love amplitude is 0.500.\n"
        "Casimir drift 1.234.\n"
        "A human said:\n"
        '    "Is the drift safe?"'
    )
    q = t.prompt([{"role": "user", "content": minimal_prompt}], system=QUEEN_SYSTEM).text
    m = t.prompt([{"role": "user", "content": minimal_prompt}], system=MINER_SYSTEM).text
    l = t.prompt([{"role": "user", "content": minimal_prompt}], system=LOVER_SYSTEM).text
    check(q and m and l, "all three voices produced a reply")
    check(q != m or q != l, "at least one persona differs from the others")
    check("1.234" in m or "drift" in m.lower(), "miner reply references the drift value")


def test_template_empty_on_blank_prompt():
    print("\n[4] Template returns empty text when there is nothing to anchor on")
    t = TemplatePersonaAdapter()
    resp = t.prompt([{"role": "user", "content": "hi"}], system="generic")
    check(resp.text == "", f"blank prompt -> empty template reply (got {resp.text!r})")


def test_router_picks_template_when_possible():
    print("\n[5] Router uses template path when template returns something")
    llm = RecordingLLM()
    router = PhiSwarmRouter(llm_adapter=llm)
    resp = router.prompt(
        messages=[{"role": "user", "content": QUEEN_PROMPT}],
        system=QUEEN_SYSTEM,
    )
    check(resp.text != "", "router returned text")
    check(llm.calls == 0, f"LLM was NOT called (calls={llm.calls})")
    check(
        router.route_history and router.route_history[-1]["backend"] == "template",
        "route_history records template backend",
    )


def test_router_falls_through_when_template_empty():
    print("\n[6] Router falls through to the LLM when template cannot answer")
    llm = RecordingLLM(reply="I am the LLM speaking")
    router = PhiSwarmRouter(llm_adapter=llm)
    resp = router.prompt(
        messages=[{"role": "user", "content": "hi"}],
        system="generic",
    )
    check(llm.calls == 1, f"LLM was called exactly once (calls={llm.calls})")
    check(resp.text == "I am the LLM speaking", "router returned the LLM reply")
    check(
        router.route_history and router.route_history[-1]["backend"] == "llm",
        "route_history records llm backend",
    )


def main():
    print("=" * 80)
    print("  PHI SWARM ROUTER TEST SUITE")
    print("=" * 80)

    test_template_extracts_state_and_message()
    test_template_returns_queen_persona_reply()
    test_template_routes_per_voice()
    test_template_empty_on_blank_prompt()
    test_router_picks_template_when_possible()
    test_router_falls_through_when_template_empty()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
