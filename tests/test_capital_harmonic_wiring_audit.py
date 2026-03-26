from aureon.exchanges.capital_cfd_trader import CapitalCFDTrader


def test_harmonic_wiring_audit_has_required_sections():
    trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
    audit = CapitalCFDTrader._build_harmonic_wiring_audit(trader)
    assert isinstance(audit, dict)
    assert "checks" in audit
    names = {item.get("name") for item in audit["checks"]}
    assert "harmonic_fusion" in names
    assert "probability_validation_report" in names
    assert audit.get("total", 0) >= len(names)
    assert audit.get("passed") == audit.get("total")
    assert audit.get("ok") is True
