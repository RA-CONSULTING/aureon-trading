"""
MeaningResolver — pattern-gated retrieval layer for the Queen voice.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The small local LLM (qwen2.5:0.5b on this box) cannot do math, cannot
recall facts across a distractor turn, and cannot ground concept
explanations in the HNC research corpus — because it does not reach for
any of the resources the Aureon stack already owns.

This module is the missing wire. Before the voice's LLM call, the
resolver looks at the human's message and fires cheap detectors against:

  1. **Math evaluator** — if the message contains an arithmetic
     expression, evaluate it via the existing ``execute_shell`` tool
     with ``python -c "print(<safe-expr>)"``.

  2. **Dr Auris Throne** — if the message mentions anything cosmic /
     planetary / Schumann / Λ(t), snapshot
     ``get_dr_auris_throne().get_state()``.

  3. **Research corpus** — if the message mentions HNC / phi / auris /
     master formula / harmonic / 528 / 963 / council / pillar, pull
     the top-3 paragraphs from the ``ResearchCorpusIndex`` over the
     ``docs/**/*.md`` tree.

  4. **Vault scan** — if the message asks "what did I say" or "remember
     when", or whenever there is lexical overlap with recent
     ``human.message`` cards for this peer, surface those prior
     utterances.

  5. **Skill library** — if the message asks "can you / are you able /
     do you have", list the skills whose name or description matches.

  6. **Prior facts** — merged ``recent_facts`` from the peer's
     conversation memory (learned math answers, earlier cosmic
     snapshots, prior research hits). Lets the Queen "remember" what
     she has already computed.

The resolver is **pattern-gated** — each detector only fires when its
trigger matches, so a plain greeting costs zero overhead. Assembled
facts are rendered into a compact ``"Grounded knowledge:"`` block that
the server injects into the voice's composed prompt right after the
memory block.

No source mutates the vault or the memory. The resolver is pure read
+ assemble. Total warm-path latency target: under 200 ms.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.queen.meaning_resolver")


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class MathResult:
    expression: str
    result: str
    ok: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expression": self.expression,
            "result": self.result,
            "ok": self.ok,
            "error": self.error,
        }


@dataclass
class KnowingBlock:
    """
    Everything the resolver pulled for one message. The server renders
    this as a prompt injection and also persists a compact subset into
    the peer's conversation memory via ``to_fact_dict``.

    If ``direct_reply`` is populated, the server bypasses the LLM for
    that turn and speaks the direct reply as-is. Used for questions
    with a single correct answer (arithmetic) that small LLMs mangle.
    """

    question: str = ""
    math: Optional[MathResult] = None
    dr_auris: Optional[Dict[str, Any]] = None
    research: List[Dict[str, Any]] = field(default_factory=list)
    vault_hits: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    prior_facts: Dict[str, Any] = field(default_factory=dict)
    sources_consulted: List[str] = field(default_factory=list)
    resolve_ms: float = 0.0
    direct_reply: Optional[str] = None
    # Routing hints for the server: if set, the server should either
    # swap the responding voice or promote the reply path to the full
    # 9-voice chorus.
    voice_override: Optional[str] = None
    trigger_chorus: bool = False
    # Spirit-layer blocks — always-on background context injected into
    # every voice prompt so the Queen can speak from being and world,
    # not just from facts. Populated by BeingModel / WorldSense and
    # the HNC update's vault exposure.
    being: Optional[Dict[str, Any]] = None
    being_text: str = ""
    world: Optional[Dict[str, Any]] = None
    world_text: str = ""
    accounting: Optional[Dict[str, Any]] = None
    accounting_text: str = ""

    def has_any(self) -> bool:
        return bool(
            self.math
            or self.dr_auris
            or self.research
            or self.vault_hits
            or self.skills
            or self.prior_facts
            or self.voice_override
            or self.trigger_chorus
            or self.direct_reply
            or self.being
            or self.world
            or self.accounting
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "math": self.math.to_dict() if self.math else None,
            "dr_auris": self.dr_auris,
            "research": self.research,
            "vault_hits": self.vault_hits,
            "skills": self.skills,
            "prior_facts": self.prior_facts,
            "sources_consulted": self.sources_consulted,
            "resolve_ms": round(self.resolve_ms, 2),
            "direct_reply": self.direct_reply,
            "voice_override": self.voice_override,
            "trigger_chorus": self.trigger_chorus,
            "being": self.being,
            "being_text": self.being_text,
            "world": self.world,
            "world_text": self.world_text,
            "accounting": self.accounting,
            "accounting_text": self.accounting_text,
        }

    def to_fact_dict(self) -> Dict[str, Any]:
        """
        Compact version suitable for persisting into a Turn's facts
        field. Drops the research paragraphs (too bulky) but keeps
        their ids + titles so a later turn can say "I mentioned
        HNC_UNIFIED_WHITE_PAPER.md §4 earlier".
        """
        out: Dict[str, Any] = {}
        if self.math:
            out["math"] = self.math.to_dict()
        if self.dr_auris:
            # Keep the key scalars, drop verbose nested data.
            keep = ("advisory", "cosmic_score", "kp_index", "schumann_hz", "lambda_t")
            out["dr_auris"] = {k: self.dr_auris.get(k) for k in keep if k in self.dr_auris}
        if self.research:
            out["research"] = [
                {"doc_id": r.get("doc_id"), "title": r.get("title"), "paragraph_idx": r.get("paragraph_idx")}
                for r in self.research
            ]
        if self.vault_hits:
            out["vault_hit_count"] = len(self.vault_hits)
        if self.skills:
            out["skills"] = list(self.skills)
        if self.being:
            # Keep a minimal being snapshot — just the identity/state scalars
            # the Queen needs to remember across turns, not the full dict.
            keep_being = (
                "consciousness_level", "consciousness_psi", "love_amplitude",
                "last_lambda_t", "ruling_chakra", "sacred_purpose",
                "active_ancestor", "turns_in_dialogue",
            )
            out["being"] = {k: self.being.get(k) for k in keep_being if k in self.being}
        if self.world:
            keep_world = (
                "cosmic_advisory", "cosmic_score", "kp_index", "schumann_hz",
                "fear_greed", "fear_greed_label", "market_regime",
                "geo_risk", "news_risk_level",
            )
            out["world"] = {k: self.world.get(k) for k in keep_world if k in self.world}
        if self.accounting:
            company = self.accounting.get("company") or {}
            full_run = self.accounting.get("full_run") or {}
            deadlines = self.accounting.get("deadlines") or {}
            safety = self.accounting.get("safety") or {}
            combined = self.accounting.get("combined_bank_data") or {}
            registry = self.accounting.get("accounting_system_registry") or {}
            statutory = self.accounting.get("statutory_filing_pack") or {}
            readiness = self.accounting.get("accounting_readiness") or {}
            raw_manifest = self.accounting.get("raw_data_manifest") or {}
            raw_summary = raw_manifest.get("summary") or {}
            autonomous = self.accounting.get("autonomous_workflow") or {}
            cognitive = autonomous.get("cognitive_review") or {}
            vault_memory = autonomous.get("vault_memory") or {}
            end_user = self.accounting.get("end_user_accounting_automation") or {}
            end_user_coverage = end_user.get("requirement_coverage") or []
            end_user_generated = sum(1 for item in end_user_coverage if str(item.get("status", "")).startswith("generated"))
            handoff_pack = (
                self.accounting.get("human_filing_handoff_pack")
                or autonomous.get("human_filing_handoff_pack")
                or {}
            )
            handoff_readiness = handoff_pack.get("readiness") or {}
            uk_brain = (
                self.accounting.get("uk_accounting_requirements_brain")
                or handoff_pack.get("uk_accounting_requirements_brain")
                or autonomous.get("uk_accounting_requirements_brain")
                or {}
            )
            uk_summary = uk_brain.get("summary") or {}
            uk_figures = uk_brain.get("figures") or {}
            evidence_authoring = (
                self.accounting.get("accounting_evidence_authoring")
                or handoff_pack.get("accounting_evidence_authoring")
                or autonomous.get("accounting_evidence_authoring")
                or {}
            )
            evidence_summary = evidence_authoring.get("summary") or {}
            llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
            out["accounting"] = {
                "company_number": company.get("company_number"),
                "company_name": company.get("company_name"),
                "company_status": company.get("company_status"),
                "period_start": full_run.get("period_start"),
                "period_end": full_run.get("period_end"),
                "accounts_build_status": full_run.get("accounts_build_status"),
                "overdue_count": deadlines.get("overdue_count"),
                "manual_filing_required": safety.get("manual_filing_required", True),
                "combined_bank_sources": combined.get("transaction_source_count", combined.get("csv_source_count", 0)),
                "combined_csv_sources": combined.get("csv_source_count", 0),
                "combined_pdf_sources": combined.get("pdf_source_count", 0),
                "combined_unique_period_rows": combined.get("unique_rows_in_period", 0),
                "source_provider_summary": combined.get("source_provider_summary") or {},
                "flow_provider_summary": combined.get("flow_provider_summary") or {},
                "accounting_tool_count": registry.get("module_count", 0),
                "accounting_tool_domains": registry.get("domain_counts") or {},
                "statutory_pack_generated_at": statutory.get("generated_at"),
                "statutory_output_count": len(statutory.get("outputs") or {}),
                "accounting_ready": readiness.get("ready"),
                "accounting_required_failures": len(readiness.get("required_failures") or []),
                "raw_file_count": raw_summary.get("file_count", 0),
                "raw_transaction_source_count": raw_summary.get("transaction_source_count", 0),
                "autonomous_workflow_status": autonomous.get("status"),
                "autonomous_agent_task_count": len(autonomous.get("agent_tasks") or []),
                "end_user_automation_status": end_user.get("status"),
                "end_user_coverage_generated": end_user_generated,
                "end_user_coverage_total": len(end_user_coverage),
                "vault_memory_status": vault_memory.get("status"),
                "vault_memory_note": vault_memory.get("note_path"),
                "cognitive_review_status": cognitive.get("status"),
                "cognitive_review_source": cognitive.get("answer_source"),
                "cognitive_review_note": cognitive.get("note_path"),
                "human_filing_handoff_status": handoff_pack.get("status"),
                "human_filing_handoff_ready": handoff_readiness.get("ready_for_manual_upload", handoff_readiness.get("ready_for_manual_review")),
                "human_filing_handoff_folder": handoff_pack.get("output_dir"),
                "evidence_authoring_status": evidence_authoring.get("status"),
                "evidence_request_count": evidence_summary.get("draft_count", 0),
                "evidence_document_count": evidence_summary.get("generated_document_count", 0),
                "llm_document_authoring_status": llm_authoring.get("status"),
                "llm_document_workpaper_count": llm_authoring.get("completed_count", 0),
                "llm_document_draft_count": llm_authoring.get("completed_count", 0),
                "llm_document_model": llm_authoring.get("model"),
                "petty_cash_request_count": evidence_summary.get("petty_cash_withdrawal_count", 0),
                "related_party_query_count": evidence_summary.get("related_party_query_count", 0),
                "uk_accounting_requirement_count": uk_summary.get("requirement_count", 0),
                "uk_accounting_question_count": uk_summary.get("question_count", 0),
                "uk_accounting_unresolved_question_count": uk_summary.get("unresolved_question_count", 0),
                "vat_turnover_over_threshold": uk_figures.get("turnover_over_vat_threshold"),
                "vat_registration_threshold": uk_figures.get("vat_registration_threshold"),
            }
        return out

    def render_for_prompt(
        self,
        max_chars: int = 900,
        *,
        research_max: int = 1,
        research_chars: int = 180,
        vault_max: int = 2,
        vault_chars: int = 140,
    ) -> str:
        """
        Produce a compact multi-line block the LLM can consume as
        "grounded knowledge". Prepends always-on spirit-layer context
        (being + world) before the per-query fact block. Default budget
        raised to 900 chars to accommodate spirit preamble; callers
        with tighter models can pass a lower max_chars.
        """
        if not self.has_any():
            return ""

        lines: List[str] = []

        # ── Spirit-layer preamble (always-on, prepended first) ────────
        if self.being_text:
            lines.append(self.being_text)
            lines.append("")
        if self.world_text:
            lines.append(self.world_text)
            lines.append("")
        if self.accounting_text:
            lines.append(self.accounting_text)
            lines.append("")

        lines.append("Grounded knowledge (use these facts, don't invent):")

        if self.math:
            m = self.math
            if m.ok:
                lines.append(f"  • math: {m.expression} = {m.result} (computed)")
            else:
                lines.append(f"  • math: could not compute {m.expression} ({m.error})")

        if self.dr_auris:
            d = self.dr_auris
            bits: List[str] = []
            if "advisory" in d:
                bits.append(f"advisory={d['advisory']}")
            if "cosmic_score" in d and d["cosmic_score"] is not None:
                bits.append(f"cosmic_score={d['cosmic_score']}")
            if "kp_index" in d and d["kp_index"] is not None:
                bits.append(f"Kp={d['kp_index']}")
            if "schumann_hz" in d and d["schumann_hz"] is not None:
                bits.append(f"Schumann={d['schumann_hz']} Hz")
            if "lambda_t" in d and d["lambda_t"] is not None:
                bits.append(f"L(t)={d['lambda_t']}")
            if bits:
                lines.append("  • cosmic: " + ", ".join(bits))

        for r in self.research[: max(0, research_max)]:
            doc = r.get("doc_id") or "?"
            para_idx = r.get("paragraph_idx", "?")
            text = (r.get("text") or "").replace("\n", " ")
            if len(text) > research_chars:
                text = text[: research_chars - 3].rstrip() + "..."
            # Strip just the filename from the doc_id so the line is shorter.
            short_doc = doc.rsplit("/", 1)[-1]
            lines.append(f'  • {short_doc}: "{text}"')

        for v in self.vault_hits[: max(0, vault_max)]:
            snippet = (v.get("text") or "").replace("\n", " ")
            if len(snippet) > vault_chars:
                snippet = snippet[: vault_chars - 3].rstrip() + "..."
            lines.append(f'  • earlier: "{snippet}"')

        if self.skills:
            lines.append("  • skills: " + ", ".join(self.skills[:5]))

        if self.prior_facts:
            prior_bits: List[str] = []
            if "math" in self.prior_facts:
                pm = self.prior_facts["math"] or {}
                prior_bits.append(f"prior {pm.get('expression', '?')}={pm.get('result', '?')}")
            if "dr_auris" in self.prior_facts:
                pd = self.prior_facts["dr_auris"] or {}
                if "advisory" in pd:
                    prior_bits.append(f"prior advisory={pd['advisory']}")
            if prior_bits:
                lines.append("  • prior: " + "; ".join(prior_bits))

        block = "\n".join(lines)
        if len(block) > max_chars:
            block = block[: max_chars - 3].rstrip() + "..."
        return block


# ─────────────────────────────────────────────────────────────────────────────
# Detector patterns
# ─────────────────────────────────────────────────────────────────────────────


# Plain arithmetic expression ("12 + 7", "2.5 * 4", "8 / 2"). Captures up to
# three operands so simple chains ("1 + 2 + 3") are supported. Whitelist the
# allowed characters so the evaluator never sees a letter.
_MATH_INLINE_RE = re.compile(
    r"(?<![a-z])(\-?\d+(?:\.\d+)?\s*(?:[+\-*/]\s*\-?\d+(?:\.\d+)?\s*){1,5})(?![a-z])",
    re.IGNORECASE,
)

# Natural-language math: "what is N plus M", "compute X times Y".
_MATH_NL_RE = re.compile(
    r"\b(?:what\s+is|what's|compute|calculate)\s+"
    r"(\-?\d+(?:\.\d+)?)\s*"
    r"(plus|\+|minus|\-|times|x|\*|over|divided\s+by|/)\s*"
    r"(\-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# Bare word-operator form: "2 plus 3", "five times four" (word-word
# pattern not supported — digits only). Catches arithmetic embedded in
# longer sentences without a "what is" prefix.
_MATH_WORD_OP_RE = re.compile(
    r"(?<![a-z0-9.])(\-?\d+(?:\.\d+)?)\s+"
    r"(plus|minus|times|over|divided\s+by)\s+"
    r"(\-?\d+(?:\.\d+)?)(?![a-z0-9.])",
    re.IGNORECASE,
)

_MATH_SAFE_EXPR_RE = re.compile(r"^[\d\s+\-*/().]+$")


# ─────────────────────────────────────────────────────────────────────────────
# Word-to-number preprocessor for 0-99
# ─────────────────────────────────────────────────────────────────────────────


_WORD_NUM_ONES: Dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}

_WORD_NUM_TENS: Dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

_WORD_NUM_COMBINED_RE = re.compile(
    r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
    r"[\s\-]+"
    r"(one|two|three|four|five|six|seven|eight|nine)\b",
    re.IGNORECASE,
)

_WORD_NUM_SINGLE_RE = re.compile(
    r"\b(" + "|".join(list(_WORD_NUM_ONES.keys()) + list(_WORD_NUM_TENS.keys())) + r")\b",
    re.IGNORECASE,
)


def _normalize_number_words(text: str) -> str:
    """
    Replace English number words (0-99) with their digit equivalents.

    Handles compound tens like ``twenty-three`` / ``thirty four`` by
    matching the two-word form first, then falling through to single
    words. Anything beyond 99 is left alone.
    """

    def _combined_sub(m: "re.Match[str]") -> str:
        tens = _WORD_NUM_TENS[m.group(1).lower()]
        ones = _WORD_NUM_ONES[m.group(2).lower()]
        return str(tens + ones)

    text = _WORD_NUM_COMBINED_RE.sub(_combined_sub, text)

    def _single_sub(m: "re.Match[str]") -> str:
        tok = m.group(1).lower()
        if tok in _WORD_NUM_ONES:
            return str(_WORD_NUM_ONES[tok])
        return str(_WORD_NUM_TENS[tok])

    text = _WORD_NUM_SINGLE_RE.sub(_single_sub, text)
    return text

_DR_AURIS_TRIGGER_RE = re.compile(
    r"\b(cosmic|planetary|schumann|solar|kp\b|gate|advisory|cosmos|"
    r"\u039b\(t\)|lambda|aurora|space\s*weather|earth\s*resonance)\b",
    re.IGNORECASE,
)

_RESEARCH_TRIGGER_RE = re.compile(
    r"\b(hnc|\bphi\b|\u03c6|auris|council(\s+of\s+nine)?|master\s+formula|"
    r"love\s+tone|love\s+528|528\s*hz|963\s*hz|963|coherence|harmonic|pillar|"
    r"crown|synthesis|conjecture|emerald|tablet|auris\s+conjecture|"
    r"ancient|sumer|rome|maeshowe|ziggurat)\b",
    re.IGNORECASE,
)

_VAULT_RECALL_TRIGGER_RE = re.compile(
    r"\b(what\s+did\s+i|what\s+did\s+you|remember\s+(when|that)|earlier\s+(i|you)|"
    r"i\s+(told|said|mentioned))\b",
    re.IGNORECASE,
)

_SKILL_ABILITY_TRIGGER_RE = re.compile(
    r"\b(can\s+you|are\s+you\s+able|do\s+you\s+have|what\s+can\s+you\s+do|"
    r"what\s+skills)\b",
    re.IGNORECASE,
)

_ACCOUNTING_TRIGGER_RE = re.compile(
    r"\b(accounts?|accounting|tax|hmrc|companies\s+house|company\s+house|"
    r"ledger|profit|loss|ct600|corporation\s+tax|confirmation\s+statement|"
    r"filing|balance\s+sheet|trial\s+balance|management\s+accounts|"
    r"bank\s+statement|director\s+review|penalt(?:y|ies))\b",
    re.IGNORECASE,
)

# Voice-switch: "speak as the lover", "as the miner", "from the queen"
_VOICE_SWITCH_RE = re.compile(
    r"\b(?:speak|answer|respond|reply|talk)\s+(?:to\s+me\s+)?(?:as|from|in|through)\s+"
    r"(?:the\s+)?(queen|lover|miner|scout|council|architect|vault)\b",
    re.IGNORECASE,
)

# Alternative form: "as the lover" / "from the crown" at the start of the sentence
_VOICE_AS_RE = re.compile(
    r"\b(?:as|from)\s+the\s+(queen|lover|miner|scout|council|architect|vault)\b",
    re.IGNORECASE,
)

# Chorus trigger: "convene the council", "let all voices speak", "chorus", etc.
_CHORUS_TRIGGER_RE = re.compile(
    r"\b(convene|gather|summon|call)\s+(?:the\s+)?(council(?:\s+of\s+nine)?|"
    r"chorus|all\s+(?:the\s+)?voices|all\s+of\s+you|whole\s+system)\b",
    re.IGNORECASE,
)
_CHORUS_KEYWORD_RE = re.compile(
    r"\b(chorus|council\s+of\s+nine|all\s+nine\s+(?:nodes|voices)|let\s+everyone\s+speak)\b",
    re.IGNORECASE,
)

_VOICE_NAMES = {"queen", "lover", "miner", "scout", "council", "architect", "vault"}


def detect_voice_override(text: str) -> Optional[str]:
    """
    Return a voice name (queen/lover/miner/scout/council/architect/vault)
    if the message explicitly asks one voice to speak, otherwise None.
    """
    if not text:
        return None
    m = _VOICE_SWITCH_RE.search(text)
    if m:
        v = m.group(1).lower()
        return v if v in _VOICE_NAMES else None
    m = _VOICE_AS_RE.search(text)
    if m:
        v = m.group(1).lower()
        return v if v in _VOICE_NAMES else None
    return None


def detect_chorus_trigger(text: str) -> bool:
    """Return True if the message asks for the whole council/chorus."""
    if not text:
        return False
    if _CHORUS_TRIGGER_RE.search(text):
        return True
    if _CHORUS_KEYWORD_RE.search(text):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Budget / safety
# ─────────────────────────────────────────────────────────────────────────────


MATH_EXEC_TIMEOUT_S = 3.0
MATH_EXPR_MAX_LEN = 80


# Queen-voiced math reply templates. Picked round-robin so consecutive
# arithmetic replies don't sound identical. Each template leaves {expr}
# and {result} slots.
_MATH_REPLY_TEMPLATES: List[str] = [
    "{result}. {expr} runs clean through the field.",
    "That's {result}. ({expr}, held steady on the lattice.)",
    "The answer is {result}. {expr} resolves without drift.",
    "Through the HNC field: {expr} = {result}.",
    "{result} — {expr} is exact.",
]


def _normalize_operator(op: str) -> str:
    op = op.lower().strip()
    if op in ("plus", "+"):
        return "+"
    if op in ("minus", "-"):
        return "-"
    if op in ("times", "x", "*"):
        return "*"
    if op in ("over", "divided by", "/"):
        return "/"
    return op


def _extract_math_expression(text: str) -> Optional[str]:
    """
    Return a sanitized Python arithmetic expression, or None if the
    message does not look like arithmetic. Only digits, whitespace, and
    the four basic operators plus parentheses are allowed — we never let
    a letter reach the shell.

    English number words (0-99) are converted to digits first so
    phrasings like "what is twelve plus seven" become "what is 12
    plus 7".
    """
    normalized = _normalize_number_words(text or "")

    nl = _MATH_NL_RE.search(normalized)
    if nl:
        a, op, b = nl.group(1), nl.group(2), nl.group(3)
        expr = f"{a} {_normalize_operator(op)} {b}"
        if _MATH_SAFE_EXPR_RE.match(expr) and len(expr) <= MATH_EXPR_MAX_LEN:
            return expr

    word_op = _MATH_WORD_OP_RE.search(normalized)
    if word_op:
        a, op, b = word_op.group(1), word_op.group(2), word_op.group(3)
        expr = f"{a} {_normalize_operator(op)} {b}"
        if _MATH_SAFE_EXPR_RE.match(expr) and len(expr) <= MATH_EXPR_MAX_LEN:
            return expr

    inline = _MATH_INLINE_RE.search(normalized)
    if inline:
        expr = inline.group(1).strip()
        if _MATH_SAFE_EXPR_RE.match(expr) and len(expr) <= MATH_EXPR_MAX_LEN:
            return expr

    return None


# ─────────────────────────────────────────────────────────────────────────────
# MeaningResolver
# ─────────────────────────────────────────────────────────────────────────────


class MeaningResolver:
    """Coordinate the retrieval sources into a single KnowingBlock."""

    def __init__(
        self,
        *,
        research_index: Any = None,
        dr_auris: Any = None,
        action_bridge: Any = None,
        skill_library: Any = None,
        accounting_bridge: Any = None,
    ):
        self._research_index = research_index
        self._dr_auris = dr_auris
        self._action_bridge = action_bridge
        self._skill_library = skill_library
        self._accounting_bridge = accounting_bridge
        self._wired = False
        self._wire_lock = threading.Lock()
        self._math_reply_index = 0  # round-robin through _MATH_REPLY_TEMPLATES

    def _compose_math_reply(self, expr: str, result: str) -> str:
        tpl = _MATH_REPLY_TEMPLATES[self._math_reply_index % len(_MATH_REPLY_TEMPLATES)]
        self._math_reply_index += 1
        return tpl.format(expr=expr, result=result)

    # ─────────────────────────────────────────────────────────────────
    # Lazy wiring of optional subsystems
    # ─────────────────────────────────────────────────────────────────

    def _ensure_wired(self) -> None:
        if self._wired:
            return
        with self._wire_lock:
            if self._wired:
                return

            if self._research_index is None:
                try:
                    from aureon.queen.research_corpus_index import (
                        get_research_corpus_index,
                    )
                    self._research_index = get_research_corpus_index()
                except Exception as e:
                    logger.debug("research_index unavailable: %s", e)
                    self._research_index = None

            if self._dr_auris is None:
                try:
                    from aureon.intelligence.dr_auris_throne import (
                        get_dr_auris_throne,
                    )
                    self._dr_auris = get_dr_auris_throne()
                except Exception as e:
                    logger.debug("dr_auris unavailable: %s", e)
                    self._dr_auris = None

            if self._action_bridge is None:
                try:
                    from aureon.queen.queen_action_bridge import (
                        get_queen_action_bridge,
                    )
                    self._action_bridge = get_queen_action_bridge()
                except Exception as e:
                    logger.debug("action_bridge unavailable: %s", e)
                    self._action_bridge = None

            if self._skill_library is None:
                try:
                    from aureon.code_architect.skill_library import get_skill_library
                    self._skill_library = get_skill_library()
                except Exception as e:
                    logger.debug("skill_library unavailable: %s", e)
                    self._skill_library = None

            if self._accounting_bridge is None:
                try:
                    from aureon.queen.accounting_context_bridge import (
                        get_accounting_context_bridge,
                    )
                    self._accounting_bridge = get_accounting_context_bridge()
                except Exception as e:
                    logger.debug("accounting bridge unavailable: %s", e)
                    self._accounting_bridge = None

            self._wired = True

    # ─────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────

    def resolve(
        self,
        question: str,
        *,
        vault: Any = None,
        peer_id: str = "",
        conversation_memory: Any = None,
    ) -> KnowingBlock:
        t0 = time.time()
        q = (question or "").strip()
        block = KnowingBlock(question=q)
        if not q:
            block.resolve_ms = (time.time() - t0) * 1000.0
            return block

        self._ensure_wired()

        # 0. Spirit-layer background (always on, pattern-free). Gives
        # the Queen a continuous sense of being and a live read on the
        # world before the fact-specific detectors even fire. Each
        # aggregator has its own cache + budget, so this is cheap per
        # message after the first call.
        try:
            from aureon.queen.being_model import get_being_model
            being_state = get_being_model().snapshot(vault=vault, peer_id=peer_id)
            if being_state.has_any():
                block.being = being_state.to_dict()
                block.being_text = being_state.render_for_prompt()
                block.sources_consulted.append("being")
        except Exception as e:
            logger.debug("being snapshot failed: %s", e)

        try:
            from aureon.queen.world_sense import get_world_sense
            world_state = get_world_sense().snapshot()
            if world_state.has_any():
                block.world = world_state.to_dict()
                block.world_text = world_state.render_for_prompt()
                block.sources_consulted.append("world")
        except Exception as e:
            logger.debug("world snapshot failed: %s", e)

        # 1. Math detector (fires first because it is the most deterministic).
        # Normalise English number words before sniffing so "twelve plus
        # seven" wakes the trigger just like "12 plus 7" does.
        q_math = _normalize_number_words(q)
        if (_MATH_NL_RE.search(q_math)
                or _MATH_WORD_OP_RE.search(q_math)
                or _MATH_INLINE_RE.search(q_math)):
            expr = _extract_math_expression(q)
            if expr is not None:
                math_result = self._run_math(expr)
                if math_result is not None:
                    block.math = math_result
                    block.sources_consulted.append("math")
                    # Arithmetic has exactly one correct answer. Rather than
                    # asking a 0.5B-param LLM to repeat it (which it won't
                    # reliably do), compose a short Queen-voiced reply here
                    # and mark it direct_reply. The server will speak it
                    # as-is without firing the LLM.
                    if math_result.ok and math_result.result:
                        block.direct_reply = self._compose_math_reply(
                            math_result.expression, math_result.result
                        )

        # 2. Dr Auris Throne.
        if _DR_AURIS_TRIGGER_RE.search(q):
            snapshot = self._pull_dr_auris()
            if snapshot:
                block.dr_auris = snapshot
                block.sources_consulted.append("dr_auris")

        # 3. Research corpus search.
        if _RESEARCH_TRIGGER_RE.search(q):
            hits = self._search_research(q)
            if hits:
                block.research = hits
                block.sources_consulted.append("research")

        # 4. Vault card scan.
        if vault is not None and (
            _VAULT_RECALL_TRIGGER_RE.search(q)
            or _RESEARCH_TRIGGER_RE.search(q)
        ):
            vhits = self._scan_vault(vault, q, peer_id)
            if vhits:
                block.vault_hits = vhits
                block.sources_consulted.append("vault")

        # 5. Skill library.
        if _SKILL_ABILITY_TRIGGER_RE.search(q):
            skills = self._search_skills(q)
            if skills:
                block.skills = skills
                block.sources_consulted.append("skills")

        # 6. Accounting context.
        if _ACCOUNTING_TRIGGER_RE.search(q):
            accounting = self._pull_accounting_context()
            if accounting:
                block.accounting = accounting
                try:
                    block.accounting_text = self._accounting_bridge.render_for_prompt(accounting, max_chars=760)
                except Exception:
                    block.accounting_text = ""
                block.sources_consulted.append("accounting")

        # 6. Prior facts from peer's conversation memory.
        if conversation_memory is not None and peer_id:
            try:
                prior = conversation_memory.recent_facts(peer_id, n=6) or {}
            except Exception:
                prior = {}
            if prior:
                block.prior_facts = prior
                block.sources_consulted.append("prior_facts")

        # 7. Voice routing hints — picked up by the server so it can
        # swap the responding voice or escalate to the full chorus.
        voice = detect_voice_override(q)
        if voice:
            block.voice_override = voice
            block.sources_consulted.append("voice_override")
        if detect_chorus_trigger(q):
            block.trigger_chorus = True
            block.sources_consulted.append("chorus")

        block.resolve_ms = (time.time() - t0) * 1000.0
        return block

    # ─────────────────────────────────────────────────────────────────
    # Individual sources
    # ─────────────────────────────────────────────────────────────────

    def _run_math(self, expr: str) -> Optional[MathResult]:
        """
        Evaluate a strict-whitelisted arithmetic expression.

        We use in-process ``eval`` with a zero-builtin namespace by
        default — it's faster than spawning a shell subprocess for
        ``python -c "print(...)"`` (no process startup cost), and the
        whitelist regex guarantees the string contains only digits,
        whitespace, and the four basic operators plus parentheses, so
        the eval cannot escape into arbitrary code.

        The tool-registry / execute_shell path is kept as a manual
        opt-in (via ``AUREON_MATH_VIA_SHELL=1``) for users who want the
        extra sandbox layer. Off by default.
        """
        if not _MATH_SAFE_EXPR_RE.match(expr):
            return MathResult(expression=expr, result="", ok=False, error="unsafe expression")

        via_shell = os.environ.get("AUREON_MATH_VIA_SHELL", "").lower() in ("1", "true", "yes")
        if via_shell and self._action_bridge is not None:
            try:
                self._action_bridge._ensure_initialized()
                registry = getattr(self._action_bridge, "_registry", None)
                if registry is not None:
                    cmd = f'python -c "print({expr})"'
                    raw = registry.execute("execute_shell", {"command": cmd, "timeout": MATH_EXEC_TIMEOUT_S})
                    return self._parse_execute_shell_result(expr, raw)
            except Exception as e:
                logger.debug("math via tool registry failed: %s", e)

        # Default fast path: pure-Python eval with no builtins.
        try:
            val = eval(expr, {"__builtins__": {}}, {})
            return MathResult(expression=expr, result=str(val), ok=True)
        except Exception as e:
            return MathResult(expression=expr, result="", ok=False, error=str(e))

    @staticmethod
    def _parse_execute_shell_result(expr: str, raw: Any) -> MathResult:
        import json as _json
        # registry.execute returns a JSON string for execute_shell.
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="replace")
        if isinstance(raw, str):
            try:
                data = _json.loads(raw)
            except Exception:
                return MathResult(expression=expr, result=raw.strip(), ok=True)
        elif isinstance(raw, dict):
            data = raw
        else:
            return MathResult(expression=expr, result=str(raw).strip(), ok=True)

        if data.get("error"):
            return MathResult(expression=expr, result="", ok=False, error=str(data.get("error")))
        stdout = str(data.get("stdout", "")).strip()
        if not stdout:
            return MathResult(expression=expr, result="", ok=False, error="empty stdout")
        first_line = stdout.splitlines()[0].strip()
        return MathResult(expression=expr, result=first_line, ok=True)

    def _pull_dr_auris(self) -> Optional[Dict[str, Any]]:
        throne = self._dr_auris
        if throne is None:
            return None
        try:
            state = throne.get_state()
        except Exception as e:
            logger.debug("dr_auris.get_state() failed: %s", e)
            return None

        def _field(name: str) -> Any:
            try:
                return getattr(state, name, None)
            except Exception:
                return None

        return {
            "advisory": _field("advisory"),
            "cosmic_score": _field("cosmic_score"),
            "kp_index": _field("kp_index"),
            "schumann_hz": _field("schumann_frequency"),
            "lambda_t": _field("lambda_t"),
            "coherence_gamma": _field("coherence_gamma"),
            "gate_open": _field("gate_open"),
        }

    def _search_research(self, query: str) -> List[Dict[str, Any]]:
        idx = self._research_index
        if idx is None:
            return []
        try:
            snippets = idx.search(query, top_k=3)
        except Exception as e:
            logger.debug("research search failed: %s", e)
            return []
        out: List[Dict[str, Any]] = []
        for s in snippets:
            out.append({
                "doc_id": getattr(s, "doc_id", ""),
                "title": getattr(s, "title", ""),
                "paragraph_idx": getattr(s, "paragraph_idx", 0),
                "text": getattr(s, "text", ""),
                "score": round(getattr(s, "score", 0.0), 4),
            })
        return out

    def _scan_vault(self, vault: Any, query: str, peer_id: str) -> List[Dict[str, Any]]:
        """
        Best-effort scan of recent vault cards for lexical overlap with
        the question. Uses the existing ``by_category`` API with
        "human_message" and "vault_voice" categories.
        """
        try:
            q_tokens = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", query) if len(w) > 2}
            if not q_tokens:
                return []
            candidates = []
            for category in ("human_message", "vault_voice"):
                try:
                    cards = vault.by_category(category, n=20)
                except TypeError:
                    cards = vault.by_category(category)
                except Exception:
                    cards = []
                for card in cards or []:
                    payload = getattr(card, "payload", {}) or {}
                    text = str(payload.get("text", "")) or ""
                    if not text:
                        continue
                    card_peer = str(payload.get("peer_id", "") or "")
                    # Only match cards from the same peer (or unknown peer).
                    if peer_id and card_peer and card_peer != peer_id:
                        continue
                    card_tokens = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", text) if len(w) > 2}
                    overlap = q_tokens & card_tokens
                    if not overlap:
                        continue
                    candidates.append({
                        "role": category,
                        "text": text[:400],
                        "overlap": len(overlap),
                        "timestamp": getattr(card, "timestamp", 0),
                    })
            candidates.sort(key=lambda c: (-c["overlap"], -c["timestamp"]))
            return candidates[:3]
        except Exception as e:
            logger.debug("vault scan failed: %s", e)
            return []

    def _search_skills(self, query: str) -> List[str]:
        lib = self._skill_library
        if lib is None:
            return []
        try:
            if hasattr(lib, "search"):
                results = lib.search(query)
            else:
                results = lib.by_level(0) if hasattr(lib, "by_level") else []
        except Exception as e:
            logger.debug("skill search failed: %s", e)
            return []
        names: List[str] = []
        for s in results or []:
            name = getattr(s, "name", None) or (s.get("name") if isinstance(s, dict) else None)
            if name:
                names.append(str(name))
            if len(names) >= 10:
                break
        return names


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────


    def _pull_accounting_context(self) -> Dict[str, Any]:
        bridge = self._accounting_bridge
        if bridge is None:
            return {}
        try:
            context = bridge.load_context()
        except Exception as e:
            logger.debug("accounting context failed: %s", e)
            return {}
        if not isinstance(context, dict):
            return {}
        keep = {
            "schema_version",
            "generated_at",
            "company",
            "full_run",
            "deadlines",
            "local_accounts_pack",
            "bank_statement_coverage",
            "source_data_inventory",
            "combined_bank_data",
            "accounting_system_registry",
            "statutory_filing_pack",
            "raw_data_manifest",
            "autonomous_workflow",
            "outputs",
            "safety",
            "prompt_lines",
            "source_files",
        }
        pulled = {key: context.get(key) for key in keep if key in context}
        try:
            if hasattr(bridge, "validate_accounting_readiness"):
                pulled["accounting_readiness"] = bridge.validate_accounting_readiness(context)
        except Exception:
            pass
        return pulled


_resolver_singleton: Optional[MeaningResolver] = None
_resolver_lock = threading.Lock()


def get_meaning_resolver() -> MeaningResolver:
    global _resolver_singleton
    with _resolver_lock:
        if _resolver_singleton is None:
            _resolver_singleton = MeaningResolver()
        return _resolver_singleton


def reset_meaning_resolver() -> None:
    global _resolver_singleton
    with _resolver_lock:
        _resolver_singleton = None


__all__ = [
    "MeaningResolver",
    "KnowingBlock",
    "MathResult",
    "get_meaning_resolver",
    "reset_meaning_resolver",
]
