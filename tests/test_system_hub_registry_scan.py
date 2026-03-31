from pathlib import Path

from aureon.command_centers.aureon_system_hub import SystemRegistry


def test_registry_uses_env_workspace(monkeypatch, tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()
    monkeypatch.setenv("AUREON_WORKSPACE", str(ws))

    registry = SystemRegistry()

    assert registry.workspace_path == ws.resolve()


def test_scan_workspace_resets_state_between_runs(tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()

    (ws / "aureon_alpha.py").write_text('"""alpha"""\n')
    (ws / "aureon_beta.py").write_text('"""beta"""\n')

    registry = SystemRegistry(workspace_path=str(ws))
    registry.scan_workspace()
    first_count = len(registry.systems)

    registry.scan_workspace()
    second_count = len(registry.systems)
    category_total = sum(cat.system_count for cat in registry.categories.values())

    assert first_count == 2
    assert second_count == 2
    assert category_total == 2


def test_scan_workspace_skips_cache_and_venv_dirs(tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()

    (ws / "aureon_live.py").write_text('"""root"""\n')
    pycache_dir = ws / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "aureon_hidden.py").write_text('"""hidden"""\n')

    venv_dir = ws / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "aureon_venv.py").write_text('"""venv"""\n')

    registry = SystemRegistry(workspace_path=str(ws))
    registry.scan_workspace()

    assert "aureon_live" in registry.systems
    assert "aureon_hidden" not in registry.systems
    assert "aureon_venv" not in registry.systems
