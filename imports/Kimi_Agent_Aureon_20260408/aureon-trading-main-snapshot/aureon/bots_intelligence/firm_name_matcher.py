#!/usr/bin/env python3
"""
🔧 FIRM NAME MATCHING UTILITIES 🔧
===================================

Improved firm name → firm_id matching with fuzzy logic.
Handles variations, abbreviations, and partial matches.

Gary Leckey | January 2026 | Intelligent Firm Mapping
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import re
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

# Firm name aliases and variations
FIRM_ALIASES = {
    'citadel': ['citadel', 'citadel securities', 'citadel llc', 'ctdl'],
    'jane_street': ['jane street', 'jane st', 'janestreet', 'jane street capital'],
    'two_sigma': ['two sigma', 'twosigma', '2sigma', 'two sigma investments'],
    'jump_trading': ['jump trading', 'jump', 'jump capital'],
    'virtu_financial': ['virtu', 'virtu financial', 'virtu americas'],
    'hudson_river_trading': ['hrt', 'hudson river', 'hudson river trading'],
    'optiver': ['optiver', 'optiver trading'],
    'susquehanna': ['sus', 'susquehanna', 'sig', 'susquehanna international'],
    'de_shaw': ['de shaw', 'deshaw', 'd.e. shaw', 'de shaw & co'],
    'renaissance_technologies': ['renaissance', 'rentech', 'renaissance tech', 'medallion'],
    'drw': ['drw', 'drw trading'],
    'imc': ['imc', 'imc trading'],
    'flow_traders': ['flow traders', 'flow'],
    'tower_research': ['tower', 'tower research', 'tower research capital'],
    'wintermute': ['wintermute', 'wintermute trading'],
    'alameda': ['alameda', 'alameda research'],
    'binance': ['binance', 'binance trading'],
    'ftx': ['ftx', 'ftx trading'],
    'millennium': ['millennium', 'millennium management'],
    'point72': ['point72', 'point 72', 'point72 asset management'],
    'bridgewater': ['bridgewater', 'bridgewater associates'],
}

# Common abbreviations
ABBREVIATIONS = {
    'llc': '',
    'inc': '',
    'ltd': '',
    'capital': '',
    'trading': '',
    'securities': '',
    'management': '',
    'investments': '',
}


def normalize_firm_name(name: str) -> str:
    """
    Normalize a firm name for matching.
    
    - Lowercase
    - Remove common suffixes (LLC, Inc, etc.)
    - Remove special characters
    - Trim whitespace
    """
    if not name:
        return ''
    
    # Lowercase
    normalized = name.lower().strip()
    
    # Remove common abbreviations
    for abbr in ABBREVIATIONS:
        normalized = re.sub(r'\b' + abbr + r'\b', '', normalized, flags=re.IGNORECASE)
    
    # Remove special characters
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings (0-1)."""
    return SequenceMatcher(None, s1, s2).ratio()


def match_firm_name(firm_name: str, firm_database: dict, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
    """
    Match a firm name to a firm_id using fuzzy logic.
    
    Args:
        firm_name: The firm name to match (e.g., "Citadel Securities")
        firm_database: Dict of firm_id -> FirmIntelligence objects
        threshold: Minimum similarity score (0-1) to consider a match
        
    Returns:
        (firm_id, confidence) tuple if match found, None otherwise
    """
    if not firm_name or not firm_database:
        return None
    
    normalized_input = normalize_firm_name(firm_name)
    if not normalized_input:
        return None
    
    best_match = None
    best_score = 0.0
    
    for firm_id, firm_data in firm_database.items():
        # Check against firm_id itself
        firm_id_score = similarity_score(normalized_input, firm_id)
        if firm_id_score > best_score:
            best_score = firm_id_score
            best_match = firm_id
        
        # Check against firm name
        if hasattr(firm_data, 'name'):
            firm_name_norm = normalize_firm_name(firm_data.name)
            name_score = similarity_score(normalized_input, firm_name_norm)
            if name_score > best_score:
                best_score = name_score
                best_match = firm_id
        
        # Check against aliases
        if firm_id in FIRM_ALIASES:
            for alias in FIRM_ALIASES[firm_id]:
                alias_norm = normalize_firm_name(alias)
                alias_score = similarity_score(normalized_input, alias_norm)
                if alias_score > best_score:
                    best_score = alias_score
                    best_match = firm_id
        
        # Check for substring matches (exact match)
        if normalized_input in firm_id or firm_id in normalized_input:
            if best_score < 0.9:
                best_score = 0.9
                best_match = firm_id
    
    # Return match if above threshold
    if best_match and best_score >= threshold:
        return (best_match, best_score)
    
    return None


def match_firm_name_simple(firm_name: str) -> Optional[str]:
    """
    Quick firm name match using aliases only (no database needed).
    Returns firm_id if found.
    """
    if not firm_name:
        return None
    
    normalized = normalize_firm_name(firm_name)
    
    # Check aliases
    for firm_id, aliases in FIRM_ALIASES.items():
        for alias in aliases:
            alias_norm = normalize_firm_name(alias)
            if normalized == alias_norm or normalized in alias_norm or alias_norm in normalized:
                return firm_id
    
    return None


def get_all_aliases_for_firm(firm_id: str) -> List[str]:
    """Get all known aliases for a firm_id."""
    return FIRM_ALIASES.get(firm_id, [])


# Example usage
if __name__ == '__main__':
    print("🔧 FIRM NAME MATCHING TEST 🔧")
    print("=" * 60)
    
    # Test cases
    test_names = [
        "Citadel Securities",
        "citadel",
        "CTDL",
        "Jane Street Capital",
        "Two Sigma Investments",
        "HRT",
        "Renaissance Technologies",
        "Rentech",
        "SIG",
        "Unknown Firm LLC"
    ]
    
    for name in test_names:
        match = match_firm_name_simple(name)
        if match:
            print(f"✅ '{name}' → {match}")
            aliases = get_all_aliases_for_firm(match)
            print(f"   Aliases: {', '.join(aliases[:3])}")
        else:
            print(f"❌ '{name}' → NO MATCH")
    
    print("\n" + "=" * 60)
    print("✅ Firm matching utilities ready")
