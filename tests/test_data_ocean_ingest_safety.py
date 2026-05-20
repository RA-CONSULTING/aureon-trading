import argparse

from aureon.core.aureon_global_history_db import connect
from scripts.python import ingest_global_memory
from scripts.python.ingest_economic_calendar import parse_args


def _memory_args(**overrides):
    base = {
        "db": "",
        "no_resume": False,
        "skip_account_sync": False,
        "account_sync_max_kraken": 50,
        "account_sync_binance_limit": 200,
        "account_sync_alpaca_limit": 200,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_standard_global_memory_plan_uses_budgeted_private_account_sync():
    plan = ingest_global_memory._standard_plan(_memory_args())
    sync_name, sync_cmd = plan[0]

    assert "budgeted" in sync_name
    assert "sync_global_history_db.py" in sync_cmd[0]
    assert sync_cmd[sync_cmd.index("--max-kraken") + 1] == "50"
    assert sync_cmd[sync_cmd.index("--binance-limit") + 1] == "200"
    assert sync_cmd[sync_cmd.index("--alpaca-limit") + 1] == "200"


def test_global_memory_can_skip_private_account_sync_for_data_ocean():
    plan = ingest_global_memory._standard_plan(_memory_args(skip_account_sync=True))

    assert all("sync_global_history_db.py" not in " ".join(cmd) for _, cmd in plan)


def test_calendar_seed_events_flag_accepts_optional_value():
    assert parse_args(["--seed-events"]).seed_events == "true"
    assert parse_args(["--seed-events", "false"]).seed_events == "false"


def test_global_history_db_sets_busy_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREON_SQLITE_BUSY_TIMEOUT_MS", "12345")
    conn = connect(str(tmp_path / "history.sqlite"))
    try:
        timeout_ms = int(conn.execute("PRAGMA busy_timeout;").fetchone()[0])
    finally:
        conn.close()

    assert timeout_ms == 12345
