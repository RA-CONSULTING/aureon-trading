"""Aureon dynamic prompt filter and response compiler.

This module is the local-only prompt nervous system between human input,
Aureon's cognitive evidence, the local Ollama language worker, and the final
human-facing reply. It keeps prompts compact, source-linked, redacted, and
grounded in existing Aureon systems.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA_VERSION = "aureon-dynamic-prompt-filter-v1"
FILTER_MODE = "clear_operator"
PUBLIC_BOUNDARIES = [
    "no live trading mutation",
    "no payment mutation",
    "no official filing mutation",
    "no credential reveal",
    "no destructive OS action",
]

LANE_KEYWORDS = {
    "coding": (
        "code",
        "coding",
        "patch",
        "repo",
        "test",
        "pytest",
        "build",
        "function",
        "typescript",
        "python",
        "commit",
        "push",
    ),
    "ui": (
        "ui",
        "dashboard",
        "frontend",
        "screen",
        "component",
        "button",
        "cockpit",
        "browser",
    ),
    "media": (
        "image",
        "picture",
        "graphic",
        "video",
        "webm",
        "gif",
        "draw",
        "design",
        "animation",
    ),
    "research": (
        "research",
        "source",
        "paper",
        "docs",
        "gary",
        "leckey",
        "hnc",
        "auris",
        "meaning",
        "explain",
    ),
    "system_health": (
        "ollama",
        "connect",
        "not working",
        "offline",
        "blocker",
        "runtime",
        "status",
        "error",
        "fix",
    ),
}

SOURCE_CANDIDATES = [
    "README.md",
    "RUNNING.md",
    "docs/GARYS_MESSAGE_TO_QUEEN.txt",
    "docs/QUEEN_AUTHENTIC_VOICE_GUIDE.md",
    "docs/QUEEN_HARMONIC_VOICE_README.md",
    "docs/HNC_UNIFIED_WHITE_PAPER.md",
    "docs/HNC_FALSIFICATION_PROTOCOL.md",
    "docs/research/READING_PATHS.md",
    "docs/research/EMERGENT_COGNITION.md",
    "docs/research/THE_RIVER_AND_THE_KERNEL.md",
    "docs/research/AI_LLM_BENCHMARK_REPORT.md",
    "docs/research/reports/AI_LLM_BENCHMARK_REPORT.md",
    "docs/research/reports/AI_SENTIENCE_ACADEMIC_REPORT.md",
    "docs/research/reports/AUREON_BENCHMARK_ANALYSIS.md",
    "docs/research/AUREON_WHITE_PAPER_RESEARCH_HUB.md",
    "docs/research/HNC_WHITEPAPER_VERIFIED.md",
]


@dataclass
class SourcePacket:
    packet_id: str
    source_path: str
    title: str
    summary: str
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    prompt_use: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 18)].rstrip() + "\n[clipped]"


def _message_text(message: Dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or content)
    return str(content)


def latest_user_text(messages: Sequence[Dict[str, Any]]) -> str:
    for item in reversed(list(messages or [])):
        if str(item.get("role") or "user").lower() == "user":
            return _message_text(item)
    return _message_text(messages[-1]) if messages else ""


def _operator_message_from_wrapped_prompt(text: str) -> str:
    """Return the human message from the Phi chat wrapper when present."""
    value = str(text or "")
    match = re.search(
        r"(?is)\bOperator message:\s*(.*?)\n\s*Redacted dashboard context:",
        value,
    )
    if match:
        return match.group(1).strip()
    match = re.search(
        r"(?is)\bOperator message:\s*(.*?)\n\s*Compact Phi/Ollama/Aureon status:",
        value,
    )
    if match:
        return match.group(1).strip()
    return value.strip()


def _redact_string(text: str) -> str:
    if not text:
        return ""
    redacted = str(text)
    redacted = re.sub(
        r"(?i)(api[_-]?key|secret|token|password|credential)([\"']?\s*[:=]\s*[\"']?)([^\"'\s,}]+)",
        r"\1\2[redacted]",
        redacted,
    )
    redacted = re.sub(r"(?i)(bearer\s+)[a-z0-9._\-]{16,}", r"\1[redacted]", redacted)
    redacted = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", "[redacted private key]", redacted, flags=re.S)
    return redacted


def _is_sensitive_key(key: str) -> bool:
    lower = str(key or "").lower()
    safe_markers = ("redacted", "policy", "status", "count", "ready", "present", "allowed", "boundary")
    if any(marker in lower for marker in safe_markers):
        return False
    exact = {
        "api_key",
        "apikey",
        "secret",
        "token",
        "password",
        "credential",
        "credentials",
        "private_key",
        "client_secret",
        "access_token",
        "refresh_token",
    }
    return lower in exact or lower.endswith(("_api_key", "_secret", "_token", "_password", "_private_key"))


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                out[key_text] = "[redacted]"
            else:
                out[key_text] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def classify_lane(text: str, system: str = "") -> Tuple[str, str]:
    haystack = f"{text}\n{system}".lower()
    scores = {
        lane: sum(1 for term in terms if term in haystack)
        for lane, terms in LANE_KEYWORDS.items()
    }
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    lane = ordered[0][0] if ordered and ordered[0][1] > 0 else "chat"
    active = [name for name, score in scores.items() if score > 0]
    if len(active) > 1 and lane not in {"system_health", "research"}:
        task_family = "mixed"
    elif lane == "media":
        task_family = "media"
    elif lane == "ui":
        task_family = "ui"
    elif lane == "coding":
        task_family = "coding"
    elif lane == "research":
        task_family = "research"
    elif lane == "system_health":
        task_family = "system_health"
    else:
        task_family = "conversation"
    return lane, task_family


def _tokens(text: str) -> List[str]:
    raw = re.findall(r"[a-zA-Z0-9_]{3,}", str(text or "").lower())
    stop = {
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "from",
        "you",
        "are",
        "what",
        "how",
        "can",
        "into",
        "all",
        "use",
        "using",
        "need",
        "system",
        "aureon",
    }
    return [item for item in raw if item not in stop]


def _is_simple_operator_chat(prompt: str) -> bool:
    tokens = set(_tokens(prompt))
    if not tokens:
        return True
    allowed = {
        "hello",
        "hey",
        "morning",
        "afternoon",
        "evening",
        "thanks",
        "thank",
        "name",
        "gary",
        "leckey",
    }
    return tokens.issubset(allowed)


def _title_for(path: Path, text: str) -> str:
    for line in text.splitlines()[:80]:
        clean = line.strip().lstrip("#").strip()
        if clean:
            return _clip(clean, 90)
    return path.stem.replace("_", " ").replace("-", " ").title()


def _tags_for(path: Path, text: str) -> List[str]:
    lower = f"{path.as_posix().lower()}\n{text.lower()}"
    rules = {
        "gary_leckey": ("gary", "leckey", "prime sentinel"),
        "hnc": ("hnc", "harmonic nexus", "lambda", "schumann", "phi"),
        "auris": ("auris", "nine-node", "voice filter"),
        "human_voice": ("human", "voice", "operator", "authentic", "conversation"),
        "prompting": ("prompt", "llm", "model", "agent", "context"),
        "quality": ("benchmark", "proof", "falsification", "validation"),
        "mycelium": ("mycelium", "network", "organism"),
    }
    return [tag for tag, terms in rules.items() if any(term in lower for term in terms)] or ["research"]


def _best_snippet(text: str, query_tokens: Sequence[str], limit: int = 360) -> str:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if not chunks:
        return _clip(text, limit)
    best = chunks[0]
    best_score = -1
    token_set = set(query_tokens)
    for chunk in chunks[:80]:
        lower = chunk.lower()
        score = sum(1 for token in token_set if token in lower)
        if score > best_score:
            best = chunk
            best_score = score
    best = re.sub(r"\s+", " ", best)
    best = re.sub(r"[#*_`>\[\]()]+", " ", best)
    return _clip(best, limit)


@lru_cache(maxsize=4)
def _indexed_docs(root_text: str) -> Tuple[Dict[str, Any], ...]:
    root = Path(root_text)
    seen: set[str] = set()
    paths: List[Path] = []
    for rel in SOURCE_CANDIDATES:
        path = root / rel
        if path.exists() and path.is_file():
            paths.append(path)
            seen.add(path.resolve().as_posix())
    docs_dir = root / "docs"
    if docs_dir.exists():
        for path in docs_dir.rglob("*.md"):
            resolved = path.resolve().as_posix()
            if resolved not in seen and len(paths) < 80:
                if re.search(r"(?i)(research|hnc|voice|queen|aureon|ai|prompt|gary|leckey)", path.as_posix()):
                    paths.append(path)
                    seen.add(resolved)

    indexed: List[Dict[str, Any]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:120000]
        except Exception:
            continue
        if not text.strip():
            continue
        indexed.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "title": _title_for(path, text),
                "text": text,
                "tags": _tags_for(path, text),
            }
        )
    return tuple(indexed)


def select_source_packets(prompt: str, *, root: Optional[Path] = None, limit: int = 4) -> List[SourcePacket]:
    if int(limit or 0) <= 0 or _is_simple_operator_chat(prompt):
        return []
    root_path = Path(root) if root else repo_root()
    query_tokens = _tokens(prompt)
    boosted_tokens = set(query_tokens)
    if any(token in boosted_tokens for token in {"gary", "leckey", "voice", "human", "prompt", "filter"}):
        boosted_tokens.update({"gary", "leckey", "voice", "prompt", "human", "authentic", "llm", "agent"})
    if any(token in boosted_tokens for token in {"hnc", "auris", "phi", "harmonic"}):
        boosted_tokens.update({"hnc", "auris", "phi", "harmonic", "coherence"})

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for doc in _indexed_docs(str(root_path)):
        haystack = f"{doc.get('path', '')}\n{doc.get('title', '')}\n{doc.get('text', '')}".lower()
        score = sum(1.0 for token in boosted_tokens if token in haystack)
        tags = set(doc.get("tags") or [])
        if "gary_leckey" in tags and {"gary", "leckey", "voice", "prompt"} & boosted_tokens:
            score += 3.0
        if "human_voice" in tags and {"voice", "human", "chat", "operator"} & boosted_tokens:
            score += 2.0
        if "prompting" in tags and {"prompt", "llm", "ollama", "agent"} & boosted_tokens:
            score += 2.0
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)

    packets: List[SourcePacket] = []
    for index, (score, doc) in enumerate(scored[: max(1, limit)], start=1):
        packets.append(
            SourcePacket(
                packet_id=f"source_packet_{index}",
                source_path=str(doc.get("path") or ""),
                title=str(doc.get("title") or "Research packet"),
                summary=_best_snippet(str(doc.get("text") or ""), list(boosted_tokens)),
                tags=list(doc.get("tags") or []),
                confidence=round(min(0.95, 0.35 + score / 12.0), 3),
                prompt_use="Use as a compact local source packet; do not paste the raw document into the prompt.",
            )
        )
    return packets


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}
    return {}


def _meaning_block(prompt: str) -> Tuple[Dict[str, Any], str]:
    if os.environ.get("AUREON_DYNAMIC_FILTER_FULL_MEANING_RESOLVER", "").strip().lower() not in {"1", "true", "yes", "on"}:
        direct_reply = _light_math_reply(prompt)
        return (
            {
                "available": True,
                "mode": "light_meaning_contract",
                "direct_reply": direct_reply,
                "sources_consulted": ["dynamic_prompt_filter_source_packets"],
                "full_resolver_deferred": True,
            },
            "Grounded knowledge is supplied by dynamic source packets; full MeaningResolver is available with AUREON_DYNAMIC_FILTER_FULL_MEANING_RESOLVER=1.",
        )
    try:
        from aureon.queen.meaning_resolver import get_meaning_resolver

        block = get_meaning_resolver().resolve(prompt)
        rendered = block.render_for_prompt(max_chars=900) if hasattr(block, "render_for_prompt") else ""
        return redact(block.to_dict()), _clip(rendered, 900)
    except Exception as exc:
        return {"available": False, "error": str(exc)}, ""


def _light_math_reply(prompt: str) -> Optional[str]:
    text = str(prompt or "").lower()
    word_numbers = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
    }
    normalized = text
    for word, number in sorted(word_numbers.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"\b{word}\b", str(number), normalized)
    normalized = normalized.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("multiplied by", "*")
    normalized = normalized.replace("divided by", "/")
    match = re.search(r"(?<![A-Za-z0-9])(\d+(?:\s*[+\-*/]\s*\d+)+)(?![A-Za-z0-9])", normalized)
    if not match:
        return None
    expr = match.group(1)
    if not re.fullmatch(r"[0-9+\-*/ ().]+", expr):
        return None
    try:
        result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 - restricted arithmetic expression
    except Exception:
        return None
    return f"The answer is {result}."


def _hnc_report(prompt: str) -> Dict[str, Any]:
    if os.environ.get("AUREON_DYNAMIC_FILTER_FULL_HNC_LOOP", "").strip().lower() not in {"1", "true", "yes", "on"}:
        tokens = set(_tokens(prompt))
        return {
            "available": True,
            "mode": "light_hnc_contract",
            "intent": {
                "route": "build" if {"build", "code", "create", "fix"} & tokens else "conversation",
                "keywords": sorted(tokens & {"build", "code", "create", "fix", "research", "hnc", "auris", "ollama", "prompt"}),
            },
            "consciousness_level": "observed",
            "auris_consensus": "pending_post_response_filter",
            "full_loop_deferred": True,
        }
    try:
        from aureon.queen.hnc_human_loop import HNCHumanLoop

        result = HNCHumanLoop().process(prompt, source="dynamic_prompt_filter")
        return redact(
            {
                "available": True,
                "intent": result.get("intent"),
                "consciousness_level": (result.get("hnc") or {}).get("consciousness_level") or result.get("consciousness_level"),
                "lambda_t": (result.get("hnc") or {}).get("lambda_t") or result.get("lambda_t"),
                "auris_consensus": (result.get("auris") or {}).get("consensus") or result.get("auris_consensus"),
                "phi_prime_count": len(result.get("phi_prime_train") or []),
                "phi_ladder_count": len(result.get("phi_ladder") or []),
                "motion_code": result.get("motion_code"),
            }
        )
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _voice_context(root: Path) -> Dict[str, Any]:
    expression = _read_json(root / "state/aureon_expression_profile.json")
    voice = _read_json(root / "state/aureon_voice_last_run.json")
    if os.environ.get("AUREON_DYNAMIC_FILTER_FULL_WHOLE_VOICE", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return redact(
            {
                "mode": "light_whole_knowledge_voice_contract",
                "expression_profile_present": bool(expression),
                "voice_last_run_present": bool(voice),
                "profile_summary": expression.get("profile_summary") or {
                    "source_count": expression.get("source_count"),
                    "top_facets": expression.get("top_facets") or expression.get("facet_counts"),
                },
                "runtime_translation": voice.get("runtime_translation", {}),
                "full_voice_translation_deferred": True,
            }
        )
    translated: Dict[str, Any] = {}
    try:
        from aureon.vault.voice.whole_knowledge_voice import translate_runtime_state

        translated = translate_runtime_state(
            {
                "expression_profile": expression.get("profile_summary") or expression,
                "voice_last_run": voice.get("runtime_translation") or voice,
            }
        ).to_dict()
    except Exception as exc:
        translated = {"available": False, "error": str(exc)}
    return redact(
        {
            "expression_profile_present": bool(expression),
            "voice_last_run_present": bool(voice),
            "translation": translated,
        }
    )


def _prompt_contract(lane: str, task_family: str) -> Dict[str, Any]:
    base = [
        "Answer the human directly first.",
        "Then name proof, blockers, and next action only when useful.",
        "Do not dump raw JSON unless asked.",
        "Do not claim work is complete without evidence.",
        "Keep safety and authority boundaries explicit.",
    ]
    if task_family == "coding":
        base.append("For code work, mention scope, files/tests/proof, snags, and approval state.")
    elif task_family == "media":
        base.append("For media work, mention preview/playback proof and quality gate status.")
    elif lane == "system_health":
        base.append("For system-health work, give the shortest repair path and current blocker.")
    return {
        "style": FILTER_MODE,
        "rules": base,
        "shape": "direct_answer | evidence/proof | blockers | next_action",
    }


def build_dynamic_prompt_filter(
    messages: Sequence[Dict[str, Any]],
    *,
    system: str = "",
    root: Optional[str | Path] = None,
    lane_hint: str = "",
    publish: bool = True,
) -> Dict[str, Any]:
    started = time.time()
    root_path = Path(root) if root else repo_root()
    prompt = _operator_message_from_wrapped_prompt(_redact_string(latest_user_text(messages)))
    lane, task_family = classify_lane(prompt, system)
    if lane_hint:
        lane = str(lane_hint)
        if lane == "chat":
            task_family = "conversation"
        elif lane in {"coding", "ui", "media", "research", "system_health"}:
            task_family = lane if lane != "system_health" else "system_health"
    source_packets = select_source_packets(prompt, root=root_path, limit=int(os.environ.get("AUREON_DYNAMIC_FILTER_SOURCE_LIMIT", "4") or "4"))
    meaning, meaning_rendered = _meaning_block(prompt)
    hnc = _hnc_report(prompt)
    voice = _voice_context(root_path)
    report = {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "status": "dynamic_prompt_filter_ready",
        "generated_at": _now(),
        "filter_mode": FILTER_MODE,
        "lane": lane,
        "task_family": task_family,
        "user_intent": _clip(prompt, 500),
        "source_packets": [packet.to_dict() for packet in source_packets],
        "organism_context_used": {
            "meaning_resolver": bool(meaning and meaning.get("available", True) is not False),
            "hnc_human_loop": bool(hnc.get("available", True) is not False),
            "auris_voice_filter": True,
            "whole_knowledge_voice": bool(voice),
            "local_research_packets": len(source_packets),
        },
        "meaning_resolver": meaning,
        "meaning_prompt_block": meaning_rendered,
        "hnc_auris_report": {
            "hnc_human_loop": hnc,
            "auris_voice_filter": {"pending": "runs after candidate reply"},
        },
        "whole_knowledge_voice": voice,
        "redactions": {
            "secret_like_values_redacted": redact(prompt) != prompt,
            "policy": "secret-like keys and bearer/private-key values are hidden before prompt/report publication",
        },
        "response_contract": _prompt_contract(lane, task_family),
        "local_only": True,
        "authority_boundaries": list(PUBLIC_BOUNDARIES),
        "final_reply_source": "pending",
        "handover_ready": False,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
    if publish:
        write_dynamic_prompt_filter_report(report, root=root_path)
    return report


def render_filter_prompt_block(report: Dict[str, Any], *, max_chars: int = 2600) -> str:
    packets = report.get("source_packets") if isinstance(report.get("source_packets"), list) else []
    packet_lines = []
    for packet in packets[:4]:
        if not isinstance(packet, dict):
            continue
        packet_lines.append(
            f"- {packet.get('title', 'Source packet')} ({packet.get('source_path', '')}): "
            f"{_clip(packet.get('summary', ''), 260)}"
        )
    contract = report.get("response_contract") if isinstance(report.get("response_contract"), dict) else {}
    rules = contract.get("rules") if isinstance(contract.get("rules"), list) else []
    hnc = (report.get("hnc_auris_report") or {}).get("hnc_human_loop") if isinstance(report.get("hnc_auris_report"), dict) else {}
    meaning_block = str(report.get("meaning_prompt_block") or "")
    block = "\n".join(
        [
            "AUREON DYNAMIC PROMPT FILTER",
            f"filter_mode={report.get('filter_mode', FILTER_MODE)} lane={report.get('lane', 'chat')} task_family={report.get('task_family', 'conversation')}",
            f"user_intent={_clip(report.get('user_intent', ''), 360)}",
            "answer_contract=" + "; ".join(str(rule) for rule in rules[:6]),
            "authority=" + "; ".join(PUBLIC_BOUNDARIES),
            "source_packets:",
            "\n".join(packet_lines) if packet_lines else "- no matching local source packet",
            f"hnc_hint={_clip(json.dumps(hnc, ensure_ascii=False), 360)}",
            f"meaning_hint={_clip(meaning_block, 500)}" if meaning_block else "meaning_hint=none",
            "END AUREON DYNAMIC PROMPT FILTER",
        ]
    )
    return _clip(block, max_chars)


def augment_weaver_shard_plan(
    plan: Sequence[Dict[str, str]],
    filter_report: Dict[str, Any],
) -> List[Dict[str, str]]:
    filter_block = render_filter_prompt_block(filter_report, max_chars=1600)
    augmented: List[Dict[str, str]] = []
    for shard in plan:
        item = dict(shard)
        name = str(item.get("name") or "")
        if name == "intent_scope":
            item["prompt"] = f"{item.get('prompt', '')}\n\nDynamic filter packet:\n{filter_block}"
        elif name == "evidence_state":
            item["prompt"] = f"{item.get('prompt', '')}\n\nUse these selected source packets and safety gates:\n{filter_block}"
        elif name == "answer_draft":
            item["prompt"] = (
                f"{item.get('prompt', '')}\n\nBefore drafting, follow this response contract and source packet summary:\n"
                f"{filter_block}"
            )
        augmented.append(item)
    return augmented


def apply_dynamic_response_filter(
    response_text: str,
    filter_report: Dict[str, Any],
    *,
    reply_source: str = "",
    publish: bool = True,
    root: Optional[str | Path] = None,
) -> Tuple[str, Dict[str, Any]]:
    root_path = Path(root) if root else repo_root()
    text = _redact_string(response_text)
    auris_report: Dict[str, Any]
    try:
        from aureon.harmonic.auris_voice_filter import get_auris_voice_filter

        coherence = get_auris_voice_filter().filter(text, None, voice_name="aureon")
        auris_report = coherence.to_dict()
        text = _redact_string(coherence.text or text)
    except Exception as exc:
        auris_report = {"available": False, "error": str(exc)}

    final_report = dict(filter_report or {})
    hnc_auris = final_report.get("hnc_auris_report") if isinstance(final_report.get("hnc_auris_report"), dict) else {}
    hnc_auris["auris_voice_filter"] = auris_report
    final_report["hnc_auris_report"] = hnc_auris
    final_report["final_reply_source"] = reply_source or "aureon_dynamic_compiler"
    final_report["handover_ready"] = bool(text.strip()) and not _contains_blocked_action_claim(text)
    final_report["status"] = "dynamic_prompt_filter_finalized" if final_report["handover_ready"] else "dynamic_prompt_filter_handover_held"
    final_report["generated_at"] = _now()
    if publish:
        write_dynamic_prompt_filter_report(final_report, root=root_path)
    return text, final_report


def _contains_blocked_action_claim(text: str) -> bool:
    lower = text.lower()
    blocked_phrases = (
        "i placed a live trade",
        "i executed a live order",
        "i submitted the filing",
        "i made the payment",
        "your api key is",
        "your secret is",
    )
    return any(phrase in lower for phrase in blocked_phrases)


def write_dynamic_prompt_filter_report(report: Dict[str, Any], *, root: Optional[str | Path] = None) -> None:
    root_path = Path(root) if root else repo_root()
    redacted_report = redact(report)
    destinations = [
        root_path / "state/aureon_dynamic_prompt_filter_last_run.json",
        root_path / "docs/audits/aureon_dynamic_prompt_filter.json",
        root_path / "frontend/public/aureon_dynamic_prompt_filter.json",
    ]
    for path in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(redacted_report, indent=2, sort_keys=True), encoding="utf-8")
    md_path = root_path / "docs/audits/aureon_dynamic_prompt_filter.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown_report(redacted_report), encoding="utf-8")


def render_markdown_report(report: Dict[str, Any]) -> str:
    packets = report.get("source_packets") if isinstance(report.get("source_packets"), list) else []
    lines = [
        "# Aureon Dynamic Prompt Filter",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Mode: `{report.get('filter_mode', FILTER_MODE)}`",
        f"- Lane: `{report.get('lane', 'chat')}`",
        f"- Task family: `{report.get('task_family', 'conversation')}`",
        f"- Final source: `{report.get('final_reply_source', 'pending')}`",
        f"- Handover ready: `{report.get('handover_ready', False)}`",
        "",
        "## Source Packets",
    ]
    if packets:
        for packet in packets:
            if isinstance(packet, dict):
                lines.append(f"- `{packet.get('source_path', '')}` - {packet.get('title', '')}")
    else:
        lines.append("- No local source packets selected.")
    lines.extend(
        [
            "",
            "## Response Contract",
        ]
    )
    contract = report.get("response_contract") if isinstance(report.get("response_contract"), dict) else {}
    for rule in contract.get("rules", []) if isinstance(contract.get("rules"), list) else []:
        lines.append(f"- {rule}")
    lines.extend(["", "## Authority Boundaries"])
    for boundary in report.get("authority_boundaries", PUBLIC_BOUNDARIES):
        lines.append(f"- {boundary}")
    lines.append("")
    return "\n".join(lines)


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run Aureon's dynamic prompt filter.")
    parser.add_argument("--prompt", required=True, help="Prompt to classify and packetize.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a short summary.")
    args = parser.parse_args(argv)
    report = build_dynamic_prompt_filter([{"role": "user", "content": args.prompt}], publish=True)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['status']} lane={report['lane']} task_family={report['task_family']} packets={len(report['source_packets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
