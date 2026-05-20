"""AdaptivePrimeProfitGate observer_coherence parameter.

Backward-compat plus the four valid input modes:
  - None + env unset    → today's behaviour (no scaling, multiplier 1.0)
  - explicit float       → clamped to [0,1], buffer scaled
  - explicit False       → disables even if env opt-in is set
  - None + env set       → auto-consult observer singleton
"""

from __future__ import annotations

import os

import pytest

from aureon.utils.adaptive_prime_profit_gate import AdaptivePrimeProfitGate


@pytest.fixture
def gate():
    return AdaptivePrimeProfitGate()


@pytest.fixture(autouse=True)
def _clear_env():
    """Make sure no test sees the env opt-in unless it sets it itself."""
    saved = os.environ.pop("AUREON_KELLY_OBSERVE_COHERENCE", None)
    yield
    if saved is not None:
        os.environ["AUREON_KELLY_OBSERVE_COHERENCE"] = saved
    else:
        os.environ.pop("AUREON_KELLY_OBSERVE_COHERENCE", None)


def test_baseline_no_observer_param(gate):
    """No coherence supplied + env unset → no scaling, behaviour unchanged."""
    r = gate.calculate_gates("binance", 100.0)
    assert r.observer_coherence is None
    assert r.observer_buffer_multiplier == 1.0


def test_high_coherence_leaves_buffer_unchanged(gate):
    baseline = gate.calculate_gates("binance", 100.0)
    high = gate.calculate_gates("binance", 100.0, observer_coherence=1.0)
    assert high.observer_buffer_multiplier == 1.0
    assert abs(high.r_prime_buffer - baseline.r_prime_buffer) < 1e-12


def test_low_coherence_widens_buffer(gate):
    baseline = gate.calculate_gates("binance", 100.0)
    low = gate.calculate_gates("binance", 100.0, observer_coherence=0.0)
    assert abs(low.observer_buffer_multiplier - 1.5) < 1e-9
    assert low.r_prime_buffer > baseline.r_prime_buffer


def test_buffer_ordering_low_mid_high(gate):
    high = gate.calculate_gates("binance", 100.0, observer_coherence=1.0)
    mid = gate.calculate_gates("binance", 100.0, observer_coherence=0.5)
    low = gate.calculate_gates("binance", 100.0, observer_coherence=0.0)
    assert low.r_prime_buffer > mid.r_prime_buffer > high.r_prime_buffer


def test_breakeven_and_prime_unchanged_by_coherence(gate):
    """Only the safety gate scales — r_breakeven and r_prime are anchored."""
    baseline = gate.calculate_gates("binance", 100.0)
    low = gate.calculate_gates("binance", 100.0, observer_coherence=0.0)
    assert low.r_breakeven == baseline.r_breakeven
    assert low.r_prime == baseline.r_prime


def test_explicit_false_disables_even_with_env_set(gate):
    """observer_coherence=False overrides env opt-in."""
    os.environ["AUREON_KELLY_OBSERVE_COHERENCE"] = "1"
    r = gate.calculate_gates("binance", 100.0, observer_coherence=False)
    assert r.observer_coherence is None
    assert r.observer_buffer_multiplier == 1.0


def test_env_optin_consults_singleton(gate):
    """Env on + observer constructed → auto-consults."""
    from aureon.observer import HarmonicObserver
    obs = HarmonicObserver(publish_to_bus=False)  # auto-claims singleton
    os.environ["AUREON_KELLY_OBSERVE_COHERENCE"] = "1"
    r = gate.calculate_gates("binance", 100.0)
    # Fresh observer has no rocks → coherence_score == 0 → multiplier 1.5
    assert r.observer_coherence == 0.0
    assert abs(r.observer_buffer_multiplier - 1.5) < 1e-9


def test_env_optin_no_observer_falls_back(gate):
    """Env on but no singleton → multiplier stays 1.0."""
    os.environ["AUREON_KELLY_OBSERVE_COHERENCE"] = "1"
    r = gate.calculate_gates("binance", 100.0)
    assert r.observer_coherence is None
    assert r.observer_buffer_multiplier == 1.0


def test_cache_isolation_between_multipliers(gate):
    """Different coherence values must not share cached entries."""
    a = gate.calculate_gates("binance", 200.0, observer_coherence=0.2)
    b = gate.calculate_gates("binance", 200.0, observer_coherence=0.9)
    assert a.r_prime_buffer != b.r_prime_buffer


def test_to_dict_carries_observer_fields(gate):
    r = gate.calculate_gates("binance", 100.0, observer_coherence=0.3)
    d = r.to_dict()
    assert d["observer_coherence"] == 0.3
    assert d["observer_buffer_multiplier"] > 1.0


def test_clamps_out_of_range_coherence(gate):
    """Values outside [0,1] should be clamped."""
    r_neg = gate.calculate_gates("binance", 100.0, observer_coherence=-0.5)
    r_big = gate.calculate_gates("binance", 100.0, observer_coherence=2.0)
    # -0.5 clamps to 0.0 → multiplier 1.5
    assert abs(r_neg.observer_buffer_multiplier - 1.5) < 1e-9
    # 2.0 clamps to 1.0 → multiplier 1.0
    assert r_big.observer_buffer_multiplier == 1.0
