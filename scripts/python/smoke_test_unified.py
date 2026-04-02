#!/usr/bin/env python3
"""
Unified smoke test for the live stack (no trading).

This verifies:
- repo imports work from any working directory
- optional "legacy shim" modules import (no more "module not found" warnings)
- .env keys are present
- exchange auth endpoints respond
- global history DB opens and has expected tables
"""

from __future__ import annotations

import hashlib
import hmac
import importlib
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests


# Make this script runnable from any working directory by ensuring repo imports work.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass


def _mask(value: str, keep: int = 4) -> str:
    if not value:
        return "MISSING"
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def _section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _import_check(mod: str) -> Optional[str]:
    try:
        importlib.import_module(mod)
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def check_optional_modules() -> bool:
    _section("OPTIONAL MODULE IMPORTS (SHIMS)")
    modules = [
        "aureon_bot_intelligence_profiler",
        "prime_sentinel_decree",
        "aureon_obsidian_filter",
        "aureon_whale_behavior_predictor",
        "aureon_animal_momentum_scanners",
        "aureon_mycelium",
        "aureon_probability_nexus",
        "aureon_thought_bus",
    ]
    ok = True
    for m in modules:
        err = _import_check(m)
        if err:
            ok = False
            print(f"FAIL import {m}: {err}")
        else:
            print(f"OK   import {m}")
    return ok


def check_env_keys() -> bool:
    _section("ENV KEYS PRESENT")
    keys = [
        "KRAKEN_API_KEY",
        "KRAKEN_API_SECRET",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "CAPITAL_API_KEY",
        "CAPITAL_IDENTIFIER",
        "CAPITAL_PASSWORD",
        "COINAPI_KEY",
    ]
    ok = True
    for k in keys:
        present = bool(os.getenv(k))
        ok = ok and present
        print(f"{k}: {'SET' if present else 'MISSING'}")
    return ok


def check_global_history_db() -> bool:
    _section("GLOBAL HISTORY DB")
    try:
        from aureon.core import aureon_global_history_db as ghdb  # type: ignore

        conn = ghdb.connect(None)
        try:
            tables = {
                str(r[0])
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                ).fetchall()
            }
        finally:
            conn.close()
        expected = {"meta", "account_trades", "market_bars", "market_trades", "symbols", "events", "forecasts"}
        missing = sorted(expected - tables)
        if missing:
            print("FAIL missing tables:", ", ".join(missing))
            return False
        print("OK   sqlite tables:", ", ".join(sorted(expected)))
        return True
    except Exception as exc:
        print(f"FAIL global history db: {type(exc).__name__}: {exc}")
        return False


def check_alpaca() -> bool:
    _section("ALPACA")
    api_key = os.getenv("ALPACA_API_KEY", "")
    secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET") or ""
    use_paper = os.getenv("ALPACA_PAPER", "false").lower() == "true"
    base_url = "https://paper-api.alpaca.markets" if use_paper else "https://api.alpaca.markets"
    print(f"Key: {_mask(api_key)}")
    print(f"Secret: {'SET' if secret else 'MISSING'}")
    print(f"ALPACA_PAPER={str(use_paper).lower()} base_url={base_url}")
    if not api_key or not secret:
        return False
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret}
    try:
        resp = requests.get(f"{base_url}/v2/account", headers=headers, timeout=10)
        if resp.status_code == 200:
            acct = resp.json() or {}
            print(f"OK   Auth. Status={acct.get('status')} Cash={acct.get('cash')}")
            return True
        print(f"FAIL HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as exc:
        print(f"FAIL request: {exc}")
        return False


def check_kraken() -> bool:
    _section("KRAKEN")
    try:
        from aureon.exchanges.kraken_client import get_kraken_client  # type: ignore

        client = get_kraken_client()
    except Exception as exc:
        print(f"FAIL import/init: {exc}")
        return False

    print(f"Key: {_mask(getattr(client, 'api_key', '') or '')}")
    print(f"Secret: {'SET' if getattr(client, 'api_secret', '') else 'MISSING'}")
    if not getattr(client, "api_key", "") or not getattr(client, "api_secret", ""):
        return False

    try:
        balances = client.get_balance()
        print(f"OK   Auth. Assets with balance: {len(balances or {})}")
        return True
    except Exception as exc:
        print(f"FAIL auth: {exc}")
        return False


def check_capital() -> bool:
    _section("CAPITAL.COM")
    try:
        from aureon.exchanges.capital_client import CapitalClient  # type: ignore

        client = CapitalClient()
    except Exception as exc:
        print(f"FAIL import/init: {exc}")
        return False

    print(f"Key: {_mask(getattr(client, 'api_key', '') or '')}")
    print(f"Identifier: {'SET' if getattr(client, 'identifier', '') else 'MISSING'}")
    print(f"Password: {'SET' if getattr(client, 'password', '') else 'MISSING'}")
    print(f"Demo mode: {getattr(client, 'demo_mode', None)}")
    if not getattr(client, "enabled", False):
        print("FAIL Capital client disabled (missing creds).")
        return False

    try:
        accounts = client.get_accounts()
        if accounts:
            print(f"OK   Auth. Accounts: {len(accounts)}")
            return True
        print("FAIL accounts call returned empty.")
        return False
    except Exception as exc:
        print(f"FAIL auth: {exc}")
        return False


def check_binance() -> bool:
    _section("BINANCE")
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_KEY") or ""
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_SECRET") or ""
    print(f"Key: {_mask(api_key)}")
    print(f"Secret: {'SET' if api_secret else 'MISSING'}")
    if not api_key or not api_secret:
        return False

    base_url = "https://api.binance.com"
    try:
        ping = requests.get(f"{base_url}/api/v3/ping", timeout=10)
        print(f"Public ping: {ping.status_code}")
        ts_resp = requests.get(f"{base_url}/api/v3/time", timeout=10)
        server_time = (ts_resp.json() or {}).get("serverTime")
        print(f"Server time: {server_time}")

        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = hmac.new(api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        headers = {"X-MBX-APIKEY": api_key}
        acct = requests.get(
            f"{base_url}/api/v3/account?{params}&signature={signature}",
            headers=headers,
            timeout=10,
        )
        if acct.status_code == 200:
            print("OK   Auth.")
            return True
        print(f"FAIL HTTP {acct.status_code}: {acct.text[:200]}")
        return False
    except Exception as exc:
        print(f"FAIL request: {exc}")
        return False


def check_coinapi() -> bool:
    _section("COINAPI")
    api_key = os.getenv("COINAPI_KEY", "") or os.getenv("COINAPI_API_KEY", "")
    print(f"Key: {_mask(api_key)}")
    if not api_key:
        return False
    try:
        from aureon.exchanges.coinapi_anomaly_detector import CoinAPIClient  # type: ignore

        client = CoinAPIClient(api_key)
        exchanges = client.get_exchanges() or []
        print(f"OK   Exchanges: {len(exchanges)}")
        return True
    except Exception as exc:
        print(f"FAIL request: {exc}")
        return False


def main() -> int:
    _section("UNIFIED SMOKE TEST")
    print(f"Repo: {_REPO_ROOT}")
    print(f"Python: {sys.version.split()[0]}")

    ok = True
    ok = check_optional_modules() and ok
    ok = check_env_keys() and ok
    ok = check_global_history_db() and ok

    # Connectivity checks (non-trading).
    ok = check_alpaca() and ok
    ok = check_kraken() and ok
    ok = check_capital() and ok
    ok = check_binance() and ok
    ok = check_coinapi() and ok

    _section("RESULT")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
