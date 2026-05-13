from aureon.core.aureon_env import (
    KRAKEN_REQUIRED_ENV,
    enabled_credential_groups,
    env_presence,
    load_aureon_environment,
    missing_env,
)


def test_load_aureon_environment_from_explicit_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "ENABLE_ALPACA=true",
                "KRAKEN_API_KEY=key-from-file",
                "KRAKEN_API_SECRET=secret-from-file",
                "ALPACA_API_KEY=alpaca-key",
                "ALPACA_SECRET_KEY=alpaca-secret",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AUREON_ENV_FILE", str(env_path))
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)

    report = load_aureon_environment(tmp_path, override=False)

    assert report.loaded is True
    assert str(env_path) in report.loaded_paths
    assert {"target": "ALPACA_API_SECRET", "source": "ALPACA_SECRET_KEY"} in report.aliases_applied
    assert missing_env(KRAKEN_REQUIRED_ENV) == []
    assert missing_env(("ALPACA_API_SECRET", "APCA_API_SECRET_KEY")) == []
    assert enabled_credential_groups()["alpaca"] == ("ALPACA_API_KEY", "ALPACA_SECRET_KEY")
    assert env_presence(KRAKEN_REQUIRED_ENV)["KRAKEN_API_SECRET"]["set"] is True


def test_missing_env_reports_names_without_values(monkeypatch):
    monkeypatch.delenv("KRAKEN_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_API_SECRET", raising=False)

    assert missing_env(KRAKEN_REQUIRED_ENV) == ["KRAKEN_API_KEY", "KRAKEN_API_SECRET"]
    assert env_presence(KRAKEN_REQUIRED_ENV)["KRAKEN_API_KEY"]["length"] == 0
