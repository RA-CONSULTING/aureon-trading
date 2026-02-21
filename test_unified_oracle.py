#!/usr/bin/env python3
"""Test the unified 6-tradition ancient star-chart decoder."""
from aureon_seer import AureonTheSeer

def test():
    seer = AureonTheSeer()
    vision = seer.see()
    print("=" * 70)
    print("SEER SCORE:  %.4f" % vision.unified_score)
    print("SEER GRADE:  %s" % vision.grade)
    print("SEER ACTION: %s" % vision.action)
    print("PROPHECY:    %s..." % vision.prophecy[:120])
    print()
    r = vision.runes
    if r:
        d = r.details
        print("ORACLE OF RUNES  score=%.4f  phase=%s  conf=%.4f" % (r.score, r.phase, r.confidence))
        print("  Dominant: %s" % r.dominant_signal)
        print()
        for k in ["active_futhark_count", "active_ogham_count",
                   "active_hieroglyph_count", "active_sacred_site_count",
                   "active_aztec_count", "active_mogollon_count"]:
            print("  %s: %s" % (k, d.get(k, "N/A")))
        print("  total_active:  %s" % d.get("total_active", 0))
        print("  total_symbols: %s" % d.get("total_symbols", 0))
        print("  buy/sell/hold: %s/%s/%s" % (
            d.get("buy_symbols", 0),
            d.get("sell_symbols", 0),
            d.get("hold_symbols", 0)))
        conv = d.get("convergence_count", 0)
        max_t = d.get("max_convergence_traditions", 0)
        print("  convergence_count: %s" % conv)
        print("  max_convergence:   %s traditions" % max_t)
        cm = d.get("convergence_message", "")
        if cm:
            print("  %s" % cm)
        print()
        print("  ACTIVE SYMBOLS:")
        for sym in d.get("active_symbols", [])[:20]:
            print("    %s" % sym)
        print()
        convs = d.get("convergences", [])
        if convs:
            print("  CONVERGENCES (multi-tradition agreement):")
            for c in convs:
                print("    %s: %s (%d traditions, str=%.4f)" % (
                    c["aspect_key"], ", ".join(c["symbols"]),
                    c["tradition_count"], c["avg_strength"]))
    print("=" * 70)

test()
