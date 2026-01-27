from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import getpass
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Tuple

import requests

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from cli.config_manager import TradingConfig, save_config  # type: ignore
else:
    from .config_manager import TradingConfig, save_config

SUPPORTED_EXCHANGES: Dict[str, str] = {
    "binance": "https://api.binance.com/api/v3/ping",
    "kraken": "https://api.kraken.com/0/public/Time",
    "coinbase": "https://api.exchange.coinbase.com/time",
}


def prompt_input(prompt: str, secret: bool = False) -> str:
    return getpass.getpass(prompt) if secret else input(prompt)


def validate_connectivity(exchange: str, api_key: str, api_secret: str) -> Tuple[bool, str]:
    """Perform a light connectivity check to validate keys and network reachability."""

    if exchange not in SUPPORTED_EXCHANGES:
        return False, f"Unsupported exchange: {exchange}"

    try:
        response = requests.get(SUPPORTED_EXCHANGES[exchange], timeout=5)
        if response.status_code != 200:
            return False, f"Connectivity check failed with status {response.status_code}"
    except requests.RequestException as exc:
        return False, f"Connectivity error: {exc}"

    if not api_key or not api_secret:
        return False, "API key and secret must both be provided."

    return True, "Connectivity check passed."


def _prompt_trade_size() -> float:
    while True:
        trade_size_raw = input("Position size per trade (default=50): ").strip() or "50"
        try:
            trade_size = float(trade_size_raw)
            if trade_size <= 0:
                raise ValueError("Trade size must be positive.")
            return trade_size
        except ValueError as exc:
            print(f"Invalid size provided: {exc}. Please enter a positive number.")


def run_setup_wizard(force_plaintext: bool = False) -> TradingConfig:
    print("\n=== Aureon Setup Wizard ===")
    print("This guided setup will collect exchange credentials and trading defaults.\n")

    print("Choose an exchange:")
    for idx, name in enumerate(SUPPORTED_EXCHANGES.keys(), start=1):
        print(f"  {idx}. {name}")
    exchange_choice = input("Select an exchange number (default=1): ").strip() or "1"
    try:
        exchange = list(SUPPORTED_EXCHANGES.keys())[int(exchange_choice) - 1]
    except (IndexError, ValueError):
        exchange = "binance"

    api_key = prompt_input("Enter API key: ")
    api_secret = prompt_input("Enter API secret (input hidden): ", secret=True)

    base_asset = (input("Base asset (default=BTC): ").strip() or "BTC").upper()
    quote_asset = (input("Quote asset (default=USDT): ").strip() or "USDT").upper()

    retry_count = 0
    max_retries = 3
    while base_asset == quote_asset:
        print("Base and quote assets must differ.")
        print("Enter 'q' to abort setup.")
        base_asset = (input("Base asset (default=BTC): ").strip() or "BTC").upper()
        if base_asset.lower() == "q":
            print("Setup aborted by user.")
            sys.exit(1)
        quote_asset = (input("Quote asset (default=USDT): ").strip() or "USDT").upper()
        if quote_asset.lower() == "q":
            print("Setup aborted by user.")
            sys.exit(1)
        retry_count += 1
        if retry_count >= max_retries and base_asset == quote_asset:
            print("Too many failed attempts. Setup aborted.")
            sys.exit(1)

    trade_size = _prompt_trade_size()

    mode = input("Mode [live/paper] (default=paper): ").strip().lower() or "paper"
    auto_start_response = input("Enable auto-start on login? [y/N]: ").strip().lower()
    auto_start = auto_start_response == "y"

    ok, message = validate_connectivity(exchange, api_key, api_secret)
    print(message)
    if not ok:
        print("Connectivity failed. Please rerun the wizard once the issue is resolved.")
        sys.exit(1)

    config = TradingConfig(
        exchange=exchange,
        api_key=api_key,
        api_secret=api_secret,
        base_asset=base_asset,
        quote_asset=quote_asset,
        trade_size=trade_size,
        mode=mode if mode in {"live", "paper"} else "paper",
        auto_start=auto_start,
    )

    print("\nSummary:")
    summary = asdict(config)
    summary.pop("api_secret")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    confirm = input("Save these settings? [Y/n]: ").strip().lower() or "y"
    if confirm == "n":
        print("Setup aborted by user.")
        sys.exit(1)

    if force_plaintext:
        save_config(config, encrypt=False)
        print("Config saved in plaintext for development use only.")
        return config

    encrypt_response = input("Encrypt configuration at rest? [Y/n]: ").strip().lower() or "y"
    encrypt = encrypt_response != "n"
    save_config(config, encrypt=encrypt)

    storage_mode = "encrypted" if encrypt else "plaintext"
    print(f"Configuration saved ({storage_mode}).")
    return config


if __name__ == "__main__":
    run_setup_wizard()
