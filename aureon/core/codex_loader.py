"""Codex Loader - centralizes access to JSON codex files extracted from legacy archives.

This module searches multiple extracted zip directories for canonical JSON codex
files (Auris Codex, Emotional Frequency Codex, Tarot deck, etc.) and exposes a
simple API with caching.  If a codex is missing, safe defaults are returned.
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# Search locations ordered by priority (local data folder first, then extracted zips)
CODEX_SEARCH_PATHS: List[Path] = [
    Path("data/codex"),
    Path("extracted_deploy"),
    Path("extracted_earth"),
    Path("extracted_rainbow/RAINBOW-main/extracted_earth_3"),
    Path("extracted_rainbow"),
    Path("extracted_aqts/AUREON-QUANTUM-TRADING-SYSTEM-AQTS--main"),
    Path("extracted_earth_3"),
    Path("."),
]

CODEX_FILES = {
    "auris_codex": ["auris_codex_expanded.json", "auris_codex.json"],
    "emotional_frequency": [
        "emotional_frequency_codex_complete.json",
        "emotional_frequency_codex.json",
    ],
    "symbolic_layer": ["symbolic_compiler_layer.json"],
    "tarot_deck": ["tarot_deck.json", "tarot-major-arcana.json"],
    "auris_symbols": ["auris_symbols.json"],
    "emotional_spectrum": [
        "emotional_spectrum_tree.json",
        "emotional_spectrum_tree_complete.json",
    ],
    "chakra_rules": ["ruleset-chakras.json", "ruleset.json"],
}

DEFAULT_EMOTIONAL_FREQUENCIES = {
    "Anger": 110,
    "Rage": 147,
    "Sadness": 174,
    "Hope": 432,
    "Fear": 452,
    "LOVE": 528,
    "Gratitude": 639,
    "Joy": 741,
    "Compassion": 873,
    "Awe": 963,
}


def _locate_file(possible_names: List[str]) -> Optional[Path]:
    for base in CODEX_SEARCH_PATHS:
        for name in possible_names:
            candidate = base / name
            if candidate.exists():
                return candidate
    return None


def _load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load_codex(key: str) -> Optional[Any]:
    names = CODEX_FILES.get(key)
    if not names:
        return None
    path = _locate_file(names)
    if not path:
        return None
    try:
        return _load_json_file(path)
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_emotional_frequency_map() -> Dict[str, float]:
    data = load_codex("emotional_frequency")
    if isinstance(data, dict):
        entries = data.get("emotional_frequency_codex") or data.get("frequencies")
        if isinstance(entries, list):
            return {
                entry.get("emotion"): float(entry.get("frequency_hz", 0))
                for entry in entries
                if entry.get("emotion")
            }
    return DEFAULT_EMOTIONAL_FREQUENCIES.copy()


@lru_cache(maxsize=1)
def get_auris_codex() -> Dict[str, Any]:
    data = load_codex("auris_codex")
    if isinstance(data, dict):
        return data
    return {}


@lru_cache(maxsize=1)
def get_symbolic_layer() -> Dict[str, Any]:
    data = load_codex("symbolic_layer")
    if isinstance(data, dict):
        return data
    return {}


@lru_cache(maxsize=1)
def get_tarot_deck() -> List[Dict[str, Any]]:
    data = load_codex("tarot_deck")
    if isinstance(data, dict):
        cards = data.get("cards") or data.get("tarot")
        if isinstance(cards, list):
            return cards
    return []


@lru_cache(maxsize=1)
def get_auris_symbols() -> List[Dict[str, Any]]:
    data = load_codex("auris_symbols")
    if isinstance(data, dict):
        symbols = data.get("sacred_symbols") or data.get("symbols")
        if isinstance(symbols, list):
            return symbols
    return []


@lru_cache(maxsize=1)
def get_emotional_spectrum() -> Dict[str, Any]:
    data = load_codex("emotional_spectrum")
    if isinstance(data, dict):
        return data
    return {}


@lru_cache(maxsize=1)
def get_chakra_rules() -> Dict[str, Any]:
    data = load_codex("chakra_rules")
    if isinstance(data, dict):
        return data
    return {}


@dataclass
class CodexRegistry:
    emotional_frequencies: Dict[str, float]
    auris_codex: Dict[str, Any]
    symbolic_layer: Dict[str, Any]
    tarot_deck: List[Dict[str, Any]]
    auris_symbols: List[Dict[str, Any]]
    emotional_spectrum: Dict[str, Any]
    chakra_rules: Dict[str, Any]

    @classmethod
    def load(cls) -> "CodexRegistry":
        return cls(
            emotional_frequencies=get_emotional_frequency_map(),
            auris_codex=get_auris_codex(),
            symbolic_layer=get_symbolic_layer(),
            tarot_deck=get_tarot_deck(),
            auris_symbols=get_auris_symbols(),
            emotional_spectrum=get_emotional_spectrum(),
            chakra_rules=get_chakra_rules(),
        )
