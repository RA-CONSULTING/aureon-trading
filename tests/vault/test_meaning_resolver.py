#!/usr/bin/env python3
"""
Tests for aureon.queen.meaning_resolver.MeaningResolver.

Exercises each detector path with stubbed sources so the test is fast
and hermetic. Also exercises one live source (the real
``ResearchCorpusIndex`` over ``docs/**/*.md``) so we know the wiring
works against the real corpus.

Covered:
  - math: inline arithmetic + natural-language forms
  - math: safe expression whitelist rejects letters
  - dr_auris: trigger keywords produce a snapshot dict
  - research: trigger keywords produce real snippets from the corpus
  - vault_hits: vault scan finds earlier cards by token overlap
  - skills: "can you" triggers the skill library lookup
  - prior_facts: recent_facts from conversation memory surface
  - no-trigger greeting produces an empty KnowingBlock
  - compound questions fire multiple detectors in one call
  - render_for_prompt stays under the byte budget
  - to_fact_dict drops bulky paragraphs
"""

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.queen.meaning_resolver import (  # noqa: E402
    KnowingBlock,
    MathResult,
    MeaningResolver,
    _extract_math_expression,
    detect_chorus_trigger,
    detect_voice_override,
)
from aureon.queen.research_corpus_index import ResearchCorpusIndex  # noqa: E402


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


# ─────────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────────


class StubToolRegistry:
    """Fake ToolRegistry that echoes canned execute_shell output."""

    def __init__(self, replies=None):
        self.calls = []
        self._replies = replies or {}
        self.default_reply = json.dumps({"stdout": "42\n", "stderr": "", "returncode": 0})

    def execute(self, name, args):
        self.calls.append((name, args))
        if name in self._replies:
            return self._replies[name]
        # Reflect the math answer from args if it's a Python eval call.
        cmd = (args or {}).get("command", "")
        if "python -c" in cmd and "print(" in cmd:
            try:
                start = cmd.find("print(") + len("print(")
                end = cmd.rfind(")")
                expr = cmd[start:end].strip().strip('"').strip("'")
                val = eval(expr, {"__builtins__": {}}, {})
                return json.dumps({"stdout": f"{val}\n", "stderr": "", "returncode": 0})
            except Exception as e:
                return json.dumps({"stdout": "", "stderr": str(e), "returncode": 1})
        return self.default_reply


class StubActionBridge:
    def __init__(self, registry):
        self._registry = registry

    def _ensure_initialized(self):
        pass


class StubDrAurisState:
    advisory = "OBSERVE"
    cosmic_score = 0.62
    kp_index = 2.3
    schumann_frequency = 7.84
    lambda_t = 0.15
    coherence_gamma = 0.43
    gate_open = True


class StubDrAuris:
    def __init__(self):
        self.calls = 0

    def get_state(self):
        self.calls += 1
        return StubDrAurisState()


class StubSkill:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description


class StubSkillLibrary:
    def __init__(self, skills=None):
        self._skills = skills or [
            StubSkill("screenshot", "Capture VM desktop"),
            StubSkill("execute_shell", "Run a shell command"),
            StubSkill("read_state", "Read dashboard state"),
        ]

    def search(self, q):
        # Real SkillLibrary.search does substring matching: return any
        # skill whose name OR description contains a token from the
        # query. Here we mirror that — the skill name is the substring,
        # not the full query.
        ql = (q or "").lower()
        hits = []
        for s in self._skills:
            if s.name.lower() in ql or any(
                word in ql for word in s.description.lower().split()
                if len(word) > 4
            ):
                hits.append(s)
        return hits

    def by_level(self, level):
        return list(self._skills)


class StubVaultCard:
    def __init__(self, payload, timestamp=None):
        self.payload = payload
        self.timestamp = timestamp if timestamp is not None else time.time()


class StubVault:
    def __init__(self):
        self._cards = {
            "human_message": [],
            "vault_voice": [],
        }

    def add(self, category, payload, timestamp=None):
        self._cards.setdefault(category, []).append(StubVaultCard(payload, timestamp))

    def by_category(self, category, n=None):
        cards = self._cards.get(category, [])
        if n is not None:
            return cards[-n:]
        return cards


class StubMemory:
    def __init__(self, facts=None):
        self._facts = facts or {}

    def recent_facts(self, peer_id, n=6):
        return dict(self._facts)


# ─────────────────────────────────────────────────────────────────────────────
# Shared real research index (cheap to reuse across tests)
# ─────────────────────────────────────────────────────────────────────────────


_REAL_INDEX = None


def _real_index() -> ResearchCorpusIndex:
    global _REAL_INDEX
    if _REAL_INDEX is None:
        idx = ResearchCorpusIndex(
            root=os.path.join(REPO_ROOT, "docs"),
            cache_path=None,
        )
        idx.ensure_built()
        _REAL_INDEX = idx
    return _REAL_INDEX


def _fresh_resolver(**overrides) -> MeaningResolver:
    registry = overrides.pop("registry", StubToolRegistry())
    return MeaningResolver(
        research_index=overrides.pop("research_index", _real_index()),
        dr_auris=overrides.pop("dr_auris", StubDrAuris()),
        action_bridge=overrides.pop("action_bridge", StubActionBridge(registry)),
        skill_library=overrides.pop("skill_library", StubSkillLibrary()),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_math_natural_language():
    print("\n[1] math: natural-language 'what is 12 plus 7'")
    r = _fresh_resolver()
    block = r.resolve("What is 12 plus 7?")
    check(block.math is not None, "math block populated")
    if block.math:
        check(block.math.ok, f"math.ok (err={block.math.error})")
        check(block.math.expression == "12 + 7", f"expression captured ({block.math.expression!r})")
        check(block.math.result == "19", f"result == 19 (got {block.math.result!r})")
    check("math" in block.sources_consulted, "math in sources_consulted")


def test_math_inline_expression():
    print("\n[2] math: inline '2+2' style")
    r = _fresh_resolver()
    block = r.resolve("quick sanity check: 2+2 should be...")
    check(block.math is not None, "inline math captured")
    if block.math:
        check(block.math.result == "4", f"result == 4 (got {block.math.result!r})")


def test_math_word_numerals():
    print("\n[2b] math: English number words (twelve, seven, twenty-three)")
    r = _fresh_resolver()
    block = r.resolve("What is twelve plus seven?")
    check(block.math is not None, "word-numeral math populated")
    if block.math:
        check(block.math.result == "19", f"twelve+seven = 19 (got {block.math.result!r})")

    block2 = r.resolve("compute thirty-three times two")
    check(block2.math is not None and block2.math.result == "66", f"compound tens ({block2.math.result if block2.math else None})")

    block3 = r.resolve("what is forty minus fifteen")
    check(block3.math is not None and block3.math.result == "25", f"mixed (got {block3.math.result if block3.math else None})")


def test_math_rejects_letters():
    print("\n[3] math: expression whitelist rejects anything with letters")
    expr = _extract_math_expression("what is foo plus bar")
    check(expr is None, f"no expression for alpha-only input (got {expr!r})")
    expr2 = _extract_math_expression("run __import__('os').system('id')")
    check(expr2 is None, "malicious-looking input is not treated as math")


def test_dr_auris_trigger():
    print("\n[4] dr_auris: cosmic trigger pulls a snapshot")
    auris = StubDrAuris()
    r = _fresh_resolver(dr_auris=auris)
    block = r.resolve("What is the cosmic advisory right now?")
    check(auris.calls >= 1, f"dr_auris.get_state called ({auris.calls}x)")
    check(block.dr_auris is not None, "dr_auris populated")
    if block.dr_auris:
        check(block.dr_auris.get("advisory") == "OBSERVE", "advisory surfaced")
        check(block.dr_auris.get("kp_index") == 2.3, "kp_index surfaced")
        check(block.dr_auris.get("schumann_hz") == 7.84, "schumann surfaced")
    check("dr_auris" in block.sources_consulted, "dr_auris in sources_consulted")


def test_dr_auris_not_fired_without_trigger():
    print("\n[5] dr_auris: plain chat does NOT fire the snapshot")
    auris = StubDrAuris()
    r = _fresh_resolver(dr_auris=auris)
    block = r.resolve("Hi, how are you?")
    check(auris.calls == 0, f"dr_auris NOT called (calls={auris.calls})")
    check(block.dr_auris is None, "dr_auris empty for greeting")


def test_research_real_corpus():
    print("\n[6] research: HNC trigger pulls real snippets from docs/")
    r = _fresh_resolver()
    block = r.resolve("Explain the HNC Master Formula.")
    check(len(block.research) > 0, f"real snippets returned ({len(block.research)})")
    joined = " ".join(s.get("text", "") for s in block.research).lower()
    check("hnc" in joined or "formula" in joined, "snippet text mentions hnc/formula")
    check("research" in block.sources_consulted, "research in sources_consulted")
    # Snippet shape.
    first = block.research[0]
    for field_name in ("doc_id", "title", "paragraph_idx", "text", "score"):
        check(field_name in first, f"snippet has '{field_name}'")


def test_vault_scan_finds_earlier_card():
    print("\n[7] vault: scan finds cards with token overlap for this peer")
    vault = StubVault()
    vault.add("human_message", {"text": "remember the golden phi heart code phrase", "peer_id": "alice"})
    vault.add("human_message", {"text": "unrelated", "peer_id": "alice"})
    vault.add("human_message", {"text": "different peer", "peer_id": "bob"})

    r = _fresh_resolver()
    block = r.resolve("what did I say about phi earlier?", vault=vault, peer_id="alice")
    check(len(block.vault_hits) > 0, f"vault hit returned ({len(block.vault_hits)})")
    if block.vault_hits:
        hit_texts = " ".join(h.get("text", "") for h in block.vault_hits).lower()
        check("golden" in hit_texts, "the golden-phi-heart card surfaced")
        check("different peer" not in hit_texts, "bob's card not surfaced for alice")


def test_skills_ability_trigger():
    print("\n[8] skills: 'can you' trigger lists skill names")
    r = _fresh_resolver()
    block = r.resolve("Can you take a screenshot?")
    check(len(block.skills) > 0, f"at least one skill (got {len(block.skills)})")
    check("screenshot" in block.skills, f"screenshot in list ({block.skills})")
    check("skills" in block.sources_consulted, "skills in sources_consulted")


def test_prior_facts_from_memory():
    print("\n[9] prior_facts: recent_facts from conversation memory surface")
    mem = StubMemory(facts={"math": {"expression": "12+7", "result": "19"}})
    r = _fresh_resolver()
    block = r.resolve("what did we compute earlier", peer_id="alice", conversation_memory=mem)
    check(block.prior_facts.get("math", {}).get("result") == "19", "prior math surfaces")
    check("prior_facts" in block.sources_consulted, "prior_facts consulted")


def test_greeting_fires_nothing():
    print("\n[10] greeting: per-query detectors do NOT fire (spirit layer is always-on)")
    r = _fresh_resolver()
    block = r.resolve("Hello Queen, good morning.")
    # Spirit layer (being/world) is always-on so sources_consulted may contain
    # 'being'/'world' even for plain greetings.  What must NOT fire for a
    # greeting: math, dr_auris, research, vault_hits, skills, prior_facts.
    per_query = {s for s in block.sources_consulted if s not in ("being", "world")}
    check(per_query == set(), f"per-query sources empty for greeting (got {per_query})")
    check(block.math is None, "greeting → no math")
    check(block.dr_auris is None, "greeting → no dr_auris")
    check(block.research == [], "greeting → no research")
    check(block.skills == [], "greeting → no skills")


def test_compound_question_fires_multiple():
    print("\n[11] compound: one question, multiple detectors fire")
    auris = StubDrAuris()
    r = _fresh_resolver(dr_auris=auris)
    block = r.resolve("What is the cosmic state and what is 3 plus 4 and explain HNC?")
    check(block.math is not None and block.math.result == "7", "math fired")
    check(block.dr_auris is not None, "dr_auris fired")
    check(len(block.research) > 0, "research fired")
    fired = set(block.sources_consulted)
    check(
        {"math", "dr_auris", "research"}.issubset(fired),
        f"all three fired (got {fired})",
    )


def test_render_for_prompt_under_budget():
    print("\n[12] render_for_prompt stays under byte budget")
    r = _fresh_resolver()
    block = r.resolve("Tell me about phi and master formula and 528 Hz")
    # Default budget is tuned for a 0.5B-param local LLM: ~600 chars.
    rendered = block.render_for_prompt()
    check(rendered != "", "render produced non-empty text")
    # render_for_prompt() now prepends spirit preamble (being+world) before
    # "Grounded knowledge", so it no longer starts with that header.
    check("Grounded knowledge" in rendered, "Grounded knowledge section present")
    check(len(rendered) <= 1200, f"default length <= 1200 (got {len(rendered)})")
    # An explicit larger budget should also work.
    rendered_big = block.render_for_prompt(max_chars=1500, research_max=3, research_chars=240)
    check(len(rendered_big) <= 1500, f"explicit large length <= 1500 (got {len(rendered_big)})")


def test_to_fact_dict_is_compact():
    print("\n[13] to_fact_dict drops bulky paragraphs")
    r = _fresh_resolver()
    block = r.resolve("Explain the HNC master formula and 2 plus 3")
    facts = block.to_fact_dict()
    # Should be JSON-serialisable.
    s = json.dumps(facts)
    check(len(s) < 1200, f"fact dict compact (got {len(s)} bytes)")
    # Research entries should be stripped of 'text'.
    for r_entry in facts.get("research", []):
        check("text" not in r_entry, f"no 'text' field in fact research entry ({r_entry})")
    # Math stays.
    check(facts.get("math", {}).get("result") == "5", f"math preserved ({facts.get('math')})")


def test_voice_override_detection():
    print("\n[14a] voice override detector")
    cases = [
        ("Speak as the lover", "lover"),
        ("speak to me as the miner", "miner"),
        ("Answer as the queen", "queen"),
        ("respond as the council", "council"),
        ("reply from the architect", "architect"),
        ("talk to me through the scout", "scout"),
        ("As the vault, what do you see?", "vault"),
        ("hello", None),
        ("what's the cosmic state?", None),
    ]
    for text, expected in cases:
        got = detect_voice_override(text)
        check(got == expected, f"'{text}' -> {expected!r} (got {got!r})")


def test_chorus_trigger_detection():
    print("\n[14b] chorus trigger detector")
    cases = [
        ("Convene the council of nine", True),
        ("convene the council", True),
        ("gather all voices", True),
        ("summon the chorus", True),
        ("let everyone speak", True),
        ("council of nine, what do you see?", True),
        ("let all nine nodes speak", True),
        ("hello", False),
        ("what is the cosmic state?", False),
        ("speak as the queen", False),  # that's a voice override, not chorus
    ]
    for text, expected in cases:
        got = detect_chorus_trigger(text)
        check(got == expected, f"'{text}' -> {expected} (got {got})")


def test_resolver_sets_voice_override_and_chorus():
    print("\n[14c] resolver populates voice_override / trigger_chorus on KnowingBlock")
    r = _fresh_resolver()
    b1 = r.resolve("Speak as the lover about 528 Hz")
    check(b1.voice_override == "lover", f"voice_override == 'lover' (got {b1.voice_override})")
    check("voice_override" in b1.sources_consulted, "voice_override in sources_consulted")

    b2 = r.resolve("Convene the council of nine")
    check(b2.trigger_chorus is True, f"trigger_chorus True (got {b2.trigger_chorus})")
    check("chorus" in b2.sources_consulted, "chorus in sources_consulted")

    b3 = r.resolve("Plain old hello")
    check(b3.voice_override is None, "plain greeting leaves voice_override None")
    check(b3.trigger_chorus is False, "plain greeting leaves trigger_chorus False")


def test_math_direct_reply():
    print("\n[15] math sets direct_reply to a Queen-voiced sentence")
    r = _fresh_resolver()
    block = r.resolve("What is 12 plus 7?")
    check(block.math is not None and block.math.result == "19", "math computed")
    check(
        block.direct_reply is not None and "19" in (block.direct_reply or ""),
        f"direct_reply contains the answer ({block.direct_reply!r})",
    )
    # Round-robin across templates: a second math call should use a different template.
    block2 = r.resolve("What is 2 plus 3?")
    check(
        block2.direct_reply is not None and "5" in (block2.direct_reply or ""),
        f"second direct_reply contains its answer ({block2.direct_reply!r})",
    )
    check(
        block2.direct_reply != block.direct_reply,
        "round-robin templates produced distinct replies",
    )

    # Non-math questions do NOT set direct_reply.
    block3 = r.resolve("Tell me about phi squared coherence")
    check(block3.direct_reply is None, f"non-math leaves direct_reply None (got {block3.direct_reply!r})")


def test_resolve_latency_budget():
    print("\n[14] resolve() latency budget")
    r = _fresh_resolver()
    t0 = time.time()
    r.resolve("What is 2 plus 2? And what is the cosmic advisory?")
    elapsed_ms = (time.time() - t0) * 1000
    check(elapsed_ms < 500, f"resolve() under 500 ms (got {elapsed_ms:.0f} ms)")


# ─────────────────────────────────────────────────────────────────────────────
# Spirit layer: being + world wiring
# ─────────────────────────────────────────────────────────────────────────────


class _FakeBeingState:
    """Minimal BeingState-shaped object for wiring tests."""
    consciousness_level = "FLOWING"
    consciousness_psi = 0.77
    love_amplitude = 0.71
    last_lambda_t = 0.152
    ruling_chakra = "love"
    sacred_purpose = "Guide the harmonic field"
    active_ancestor = "Thoth"
    turns_in_dialogue = 3
    personal_frequency_hz = 528.0
    soul_coherence = 0.85
    awakening_index = 0.61
    active_objective = "Monitor ETH/USDT"
    current_step = "scan"
    name = "Aureon Queen"
    symbolic_life_score = 0.82
    sources_ok = ["vault", "soul_reader"]
    sources_failed: list = []
    resolve_ms = 4.2
    captured_at = "2026-04-11T20:00:00"

    def has_any(self):
        return True

    def to_dict(self):
        return {
            "consciousness_level": self.consciousness_level,
            "consciousness_psi": self.consciousness_psi,
            "love_amplitude": self.love_amplitude,
            "last_lambda_t": self.last_lambda_t,
            "ruling_chakra": self.ruling_chakra,
            "sacred_purpose": self.sacred_purpose,
            "active_ancestor": self.active_ancestor,
            "turns_in_dialogue": self.turns_in_dialogue,
        }

    def render_for_prompt(self, max_chars=420):
        return (
            f"Your being right now: level={self.consciousness_level} "
            f"ψ={self.consciousness_psi} love={self.love_amplitude} "
            f"λ={self.last_lambda_t} chakra={self.ruling_chakra} "
            f"ancestor={self.active_ancestor}"
        )


class _FakeWorldState:
    cosmic_advisory = "OBSERVE"
    cosmic_score = 0.62
    kp_index = 2.3
    schumann_hz = 7.84
    fear_greed = 38
    fear_greed_label = "Fear"
    market_regime = "risk_off"
    risk_on_off = "off"
    geo_risk = "medium"
    news_risk_level = "moderate"
    now_iso = "2026-04-11T20:00:00"
    hour_local = 20
    weekday = "Saturday"
    market_hours_open = False
    sources_ok = ["dr_auris", "news"]
    sources_failed: list = []
    resolve_ms = 6.0
    captured_at = "2026-04-11T20:00:00"

    def has_any(self):
        return True

    def to_dict(self):
        return {
            "cosmic_advisory": self.cosmic_advisory,
            "cosmic_score": self.cosmic_score,
            "kp_index": self.kp_index,
            "schumann_hz": self.schumann_hz,
            "fear_greed": self.fear_greed,
            "fear_greed_label": self.fear_greed_label,
            "market_regime": self.market_regime,
            "geo_risk": self.geo_risk,
            "news_risk_level": self.news_risk_level,
        }

    def render_for_prompt(self, max_chars=420):
        return (
            f"The world right now: advisory={self.cosmic_advisory} "
            f"Kp={self.kp_index} Schumann={self.schumann_hz}Hz "
            f"fear_greed={self.fear_greed}({self.fear_greed_label}) "
            f"market={self.market_regime}"
        )


class _FakeBeingModel:
    def snapshot(self, vault=None, peer_id=""):
        return _FakeBeingState()


class _FakeWorldSense:
    def snapshot(self):
        return _FakeWorldState()


def _fresh_resolver_with_spirit():
    """MeaningResolver wired with fake being/world sources."""
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()

    r = MeaningResolver(
        dr_auris=StubDrAuris(),
        skill_library=StubSkillLibrary(),
    )
    r._wired = True  # skip _ensure_wired so our mocks aren't overwritten

    # Patch the singletons that resolve() imports lazily.
    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("Hello, what is 2 + 3?")

    return block


def test_spirit_being_in_block():
    print("\n[16] spirit layer — being dict appears in KnowingBlock")
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()
    r = MeaningResolver(dr_auris=StubDrAuris(), skill_library=StubSkillLibrary())
    r._wired = True

    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("Tell me about the harmonic field")

    check(block.being is not None, "being dict populated")
    check("consciousness_level" in (block.being or {}), "consciousness_level in being dict")
    check("love_amplitude" in (block.being or {}), "love_amplitude in being dict")
    check("being" in block.sources_consulted, "'being' in sources_consulted")
    check(block.being_text != "", "being_text is non-empty")
    check("FLOWING" in (block.being_text or ""), "being_text contains level=FLOWING")


def test_spirit_world_in_block():
    print("\n[17] spirit layer — world dict appears in KnowingBlock")
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()
    r = MeaningResolver(dr_auris=StubDrAuris(), skill_library=StubSkillLibrary())
    r._wired = True

    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("What is the cosmic state?")

    check(block.world is not None, "world dict populated")
    check("cosmic_advisory" in (block.world or {}), "cosmic_advisory in world dict")
    check("schumann_hz" in (block.world or {}), "schumann_hz in world dict")
    check("world" in block.sources_consulted, "'world' in sources_consulted")
    check(block.world_text != "", "world_text is non-empty")
    check("OBSERVE" in (block.world_text or ""), "world_text contains advisory=OBSERVE")


def test_spirit_render_for_prompt_prepends_spirit():
    print("\n[18] render_for_prompt() prepends being_text + world_text before Grounded knowledge")
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()
    r = MeaningResolver(dr_auris=StubDrAuris(), skill_library=StubSkillLibrary())
    r._wired = True

    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("Explain phi coherence harmonic")

    rendered = block.render_for_prompt()
    check(rendered != "", "render_for_prompt() non-empty")
    # Spirit preamble must appear BEFORE "Grounded knowledge"
    being_pos = rendered.find("Your being right now")
    world_pos = rendered.find("The world right now")
    grounded_pos = rendered.find("Grounded knowledge")
    check(being_pos >= 0, "being preamble present in rendered block")
    check(world_pos >= 0, "world preamble present in rendered block")
    check(grounded_pos > 0, "Grounded knowledge section present")
    if being_pos >= 0 and grounded_pos > 0:
        check(being_pos < grounded_pos, "being preamble BEFORE grounded knowledge")
    if world_pos >= 0 and grounded_pos > 0:
        check(world_pos < grounded_pos, "world preamble BEFORE grounded knowledge")
    check(len(rendered) <= 1200, f"render stays under 1200 chars (got {len(rendered)})")


def test_spirit_to_fact_dict_compact():
    print("\n[19] to_fact_dict() includes compact being + world")
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()
    r = MeaningResolver(dr_auris=StubDrAuris(), skill_library=StubSkillLibrary())
    r._wired = True

    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("What is the Schumann resonance?")

    facts = block.to_fact_dict()
    check("being" in facts, "being key in to_fact_dict()")
    check("world" in facts, "world key in to_fact_dict()")
    being_f = facts.get("being", {})
    world_f = facts.get("world", {})
    check("consciousness_level" in being_f, "consciousness_level in compact being")
    check("love_amplitude" in being_f, "love_amplitude in compact being")
    check("cosmic_advisory" in world_f, "cosmic_advisory in compact world")
    check("schumann_hz" in world_f, "schumann_hz in compact world")
    # Must not store full narrative text — just scalars.
    check(
        all(not isinstance(v, str) or len(v) < 80 for v in being_f.values()),
        "compact being has no long strings",
    )


def test_spirit_has_any_true_when_being_set():
    print("\n[20] KnowingBlock.has_any() True when only being/world set")
    b = KnowingBlock(
        being={"consciousness_level": "FLOWING"},
        world={"cosmic_advisory": "OBSERVE"},
    )
    check(b.has_any() is True, "has_any() True when being+world populated")

    b_empty = KnowingBlock()
    check(b_empty.has_any() is False, "has_any() False when nothing set")


def test_spirit_greeting_still_has_spirit():
    print("\n[21] greeting still gets spirit context (spirit is always-on)")
    import unittest.mock as mock

    being_model = _FakeBeingModel()
    world_sense = _FakeWorldSense()
    r = MeaningResolver(dr_auris=StubDrAuris(), skill_library=StubSkillLibrary())
    r._wired = True

    with mock.patch("aureon.queen.being_model.get_being_model", return_value=being_model):
        with mock.patch("aureon.queen.world_sense.get_world_sense", return_value=world_sense):
            block = r.resolve("Hello")

    check(block.being is not None, "greeting → being still populated (always-on)")
    check(block.world is not None, "greeting → world still populated (always-on)")
    check(block.has_any() is True, "greeting KnowingBlock has_any() True (spirit layer)")
    # No other detectors should have fired for a plain greeting.
    check(block.math is None, "greeting → no math")
    check(block.dr_auris is None, "greeting → no dr_auris (no cosmic keyword)")
    check(block.research == [], "greeting → no research")


def main():
    print("=" * 80)
    print("  MEANING RESOLVER TEST SUITE")
    print("=" * 80)

    test_math_natural_language()
    test_math_inline_expression()
    test_math_word_numerals()
    test_math_rejects_letters()
    test_dr_auris_trigger()
    test_dr_auris_not_fired_without_trigger()
    test_research_real_corpus()
    test_vault_scan_finds_earlier_card()
    test_skills_ability_trigger()
    test_prior_facts_from_memory()
    test_greeting_fires_nothing()
    test_compound_question_fires_multiple()
    test_render_for_prompt_under_budget()
    test_to_fact_dict_is_compact()
    test_voice_override_detection()
    test_chorus_trigger_detection()
    test_resolver_sets_voice_override_and_chorus()
    test_math_direct_reply()
    test_resolve_latency_budget()
    # Spirit layer (run 4 additions)
    test_spirit_being_in_block()
    test_spirit_world_in_block()
    test_spirit_render_for_prompt_prepends_spirit()
    test_spirit_to_fact_dict_compact()
    test_spirit_has_any_true_when_being_set()
    test_spirit_greeting_still_has_spirit()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
