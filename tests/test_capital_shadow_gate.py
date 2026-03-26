import time

from aureon.exchanges.capital_cfd_trader import CapitalCFDTrader, CFDShadowTrade


def _mk_trader() -> CapitalCFDTrader:
    trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
    trader.SHADOW_MIN_VALIDATE = 10.0
    trader._latest_target_snapshot = {
        "symbol": "EURUSD",
        "direction": "BUY",
        "timeline_confidence": 0.62,
        "fusion_global_coherence": 0.58,
    }
    trader._latest_candidate_snapshot = [
        {"symbol": "EURUSD", "direction": "BUY", "brain_coherence": 0.42}
    ]
    trader._probability_snapshot = {
        "ok": True,
        "direction_accuracy": 0.72,
        "profit_factor": 1.23,
        "updated": "2026-03-01T00:00:00",
        "reason": "ok",
    }
    trader._probability_snapshot_at = time.time()
    trader._canonical_symbol = CapitalCFDTrader._canonical_symbol.__get__(trader, CapitalCFDTrader)
    trader._probability_validation_snapshot = CapitalCFDTrader._probability_validation_snapshot.__get__(trader, CapitalCFDTrader)
    return trader


def test_shadow_promotion_gate_passes_when_layers_align():
    trader = _mk_trader()
    shadow = CFDShadowTrade(
        symbol="EURUSD",
        direction="BUY",
        asset_class="forex",
        size=0.01,
        entry_price=1.1,
        target_move_pct=0.1,
        score=3.0,
    )
    gate = CapitalCFDTrader._build_shadow_promotion_gate(trader, shadow, {"change_pct": 0.18})
    assert gate["ok"] is True
    assert all(gate["checks"].values())


def test_shadow_promotion_gate_fails_on_live_direction_flip():
    trader = _mk_trader()
    shadow = CFDShadowTrade(
        symbol="EURUSD",
        direction="BUY",
        asset_class="forex",
        size=0.01,
        entry_price=1.1,
        target_move_pct=0.1,
        score=3.0,
    )
    gate = CapitalCFDTrader._build_shadow_promotion_gate(trader, shadow, {"change_pct": -0.05})
    assert gate["ok"] is False
    assert gate["checks"]["direction_live"] is False
