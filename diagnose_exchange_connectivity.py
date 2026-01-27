#!/usr/bin/env python3
"""Quick exchange connectivity checks with clear diagnostics."""
import os
import time
import hmac
import hashlib
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
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


def check_alpaca() -> None:
    _section("ALPACA")
    api_key = os.getenv("ALPACA_API_KEY", "")
    secret = os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET") or ""
    use_paper = os.getenv("ALPACA_PAPER", "false").lower() == "true"
    base_url = "https://paper-api.alpaca.markets" if use_paper else "https://api.alpaca.markets"
    print(f"Key: {_mask(api_key)}")
    print(f"Secret: {'SET' if secret else 'MISSING'}")
    print(f"ALPACA_PAPER={str(use_paper).lower()} base_url={base_url}")

    if not api_key or not secret:
        print("❌ Missing Alpaca credentials in .env")
        return

    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret}
    try:
        resp = requests.get(f"{base_url}/v2/account", headers=headers, timeout=5)
        if resp.status_code == 200:
            acct = resp.json() or {}
            print(f"✅ Auth OK. Status={acct.get('status')} Cash={acct.get('cash')}")
        else:
            print(f"❌ Auth failed ({resp.status_code}): {resp.text}")
            if resp.status_code in (401, 403):
                print("   Hint: Check paper vs live keys and IP restrictions in Alpaca API settings.")
    except Exception as exc:
        print(f"❌ Alpaca request error: {exc}")


def check_kraken() -> None:
    _section("KRAKEN")
    try:
        from kraken_client import KrakenClient
        client = KrakenClient()
    except Exception as exc:
        print(f"❌ Failed to import KrakenClient: {exc}")
        return

    print(f"Key: {_mask(client.api_key)}")
    print(f"Secret: {'SET' if client.api_secret else 'MISSING'}")
    if not client.api_key or not client.api_secret:
        print("❌ Missing Kraken credentials in .env")
        return

    try:
        balances = client.get_balance()
        asset_count = len(balances or {})
        print(f"✅ Auth OK. Assets with balance: {asset_count}")
    except Exception as exc:
        print(f"❌ Kraken auth failed: {exc}")
        print("   Hint: Check API key permissions and ensure system time is synced.")


def check_capital() -> None:
    _section("CAPITAL.COM")
    try:
        from capital_client import CapitalClient
        client = CapitalClient()
    except Exception as exc:
        print(f"❌ Failed to import CapitalClient: {exc}")
        return

    print(f"Key: {_mask(client.api_key or '')}")
    print(f"Identifier: {'SET' if client.identifier else 'MISSING'}")
    print(f"Password: {'SET' if client.password else 'MISSING'}")
    print(f"Demo mode: {client.demo_mode}")

    if not client.enabled:
        print("❌ Capital.com client disabled (missing credentials).")
        return

    accounts = client.get_accounts()
    if accounts:
        print(f"✅ Auth OK. Accounts: {len(accounts)}")
    else:
        print("❌ Capital.com accounts call failed. Check logs for session/auth errors.")


def check_binance() -> None:
    _section("BINANCE")
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_KEY") or ""
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_SECRET") or ""
    print(f"Key: {_mask(api_key)}")
    print(f"Secret: {'SET' if api_secret else 'MISSING'}")
    if not api_key or not api_secret:
        print("❌ Missing Binance credentials in .env")
        return

    base_url = "https://api.binance.com"
    try:
        ping = requests.get(f"{base_url}/api/v3/ping", timeout=5)
        print(f"Public ping: {ping.status_code}")
        ts_resp = requests.get(f"{base_url}/api/v3/time", timeout=5)
        server_time = (ts_resp.json() or {}).get("serverTime")
        print(f"Server time: {server_time}")

        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = hmac.new(api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        headers = {"X-MBX-APIKEY": api_key}
        acct = requests.get(f"{base_url}/api/v3/account?{params}&signature={signature}", headers=headers, timeout=5)
        if acct.status_code == 200:
            print("✅ Auth OK.")
        else:
            print(f"❌ Auth failed ({acct.status_code}): {acct.text}")
            if acct.status_code == 401:
                print("   Hint: Check API key permissions and IP whitelist.")
    except Exception as exc:
        print(f"❌ Binance request error: {exc}")


def main() -> None:
    check_alpaca()
    check_kraken()
    check_capital()
    check_binance()


if __name__ == "__main__":
    main()
