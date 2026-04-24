from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from cryptography.fernet import Fernet


CONFIG_DIR = Path.home() / ".aureon"
ENCRYPTED_CONFIG_PATH = CONFIG_DIR / "config.json.enc"
PLAINTEXT_CONFIG_PATH = CONFIG_DIR / "config.json"
KEY_PATH = CONFIG_DIR / "config.key"


@dataclass
class TradingConfig:
    exchange: str
    api_key: str
    api_secret: str
    base_asset: str
    quote_asset: str
    trade_size: float
    mode: str = "paper"
    auto_start: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TradingConfig":
        return cls(
            exchange=payload.get("exchange", "binance"),
            api_key=payload.get("api_key", ""),
            api_secret=payload.get("api_secret", ""),
            base_asset=payload.get("base_asset", "BTC"),
            quote_asset=payload.get("quote_asset", "USDT"),
            trade_size=float(payload.get("trade_size", 0.0)),
            mode=payload.get("mode", "paper"),
            auto_start=bool(payload.get("auto_start", False)),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _get_fernet(key_path: Path = KEY_PATH) -> Fernet:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not key_path.exists():
        key_path.write_bytes(Fernet.generate_key())
    return Fernet(key_path.read_bytes())


def save_config(
    config: TradingConfig,
    *,
    encrypt: bool = True,
    config_path: Path = ENCRYPTED_CONFIG_PATH,
    plaintext_path: Path = PLAINTEXT_CONFIG_PATH,
    key_path: Path = KEY_PATH,
) -> Path:
    """Persist the trading config encrypted by default."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if encrypt:
        fernet = _get_fernet(key_path)
        token = fernet.encrypt(config.to_json().encode("utf-8"))
        config_path.write_bytes(token)
        return config_path

    plaintext_path.write_text(config.to_json())
    return plaintext_path


def load_config(
    *,
    prefer_plaintext: bool = False,
    config_path: Path = ENCRYPTED_CONFIG_PATH,
    plaintext_path: Path = PLAINTEXT_CONFIG_PATH,
    key_path: Path = KEY_PATH,
) -> TradingConfig:
    """Load an existing configuration, preferring encrypted storage."""

    if prefer_plaintext and plaintext_path.exists():
        data = json.loads(plaintext_path.read_text())
        return TradingConfig.from_dict(data)

    if config_path.exists():
        fernet = _get_fernet(key_path)
        payload = fernet.decrypt(config_path.read_bytes())
        return TradingConfig.from_dict(json.loads(payload.decode("utf-8")))

    if plaintext_path.exists():
        data = json.loads(plaintext_path.read_text())
        return TradingConfig.from_dict(data)

    raise FileNotFoundError("No configuration file found. Run the setup wizard first.")


def config_exists(
    config_path: Path = ENCRYPTED_CONFIG_PATH,
    plaintext_path: Path = PLAINTEXT_CONFIG_PATH,
) -> bool:
    return config_path.exists() or plaintext_path.exists()


def update_config(values: Dict[str, Any]) -> TradingConfig:
    """Merge updates into the persisted configuration."""

    current = TradingConfig.from_dict({})
    try:
        current = load_config()
    except FileNotFoundError:
        pass

    merged: Dict[str, Any] = {**asdict(current), **values}
    config = TradingConfig.from_dict(merged)
    save_config(config, encrypt=not values.get("force_plaintext", False))
    return config


__all__ = [
    "TradingConfig",
    "save_config",
    "load_config",
    "config_exists",
    "update_config",
    "ENCRYPTED_CONFIG_PATH",
    "PLAINTEXT_CONFIG_PATH",
    "KEY_PATH",
]
