import shutil

import pytest

from aureon.vault.hnc_swarm_key_store import ensure_dpapi_swarm_keys, load_dpapi_swarm_agent_keys


pytestmark = pytest.mark.skipif(
    shutil.which("powershell.exe") is None and shutil.which("powershell") is None,
    reason="Windows PowerShell is required for DPAPI swarm key storage",
)


def test_dpapi_swarm_key_store_round_trips_metadata_only(tmp_path):
    manifest = ensure_dpapi_swarm_keys(("seer", "lyra"), store_dir=tmp_path)
    loaded = load_dpapi_swarm_agent_keys(("seer", "lyra"), store_dir=tmp_path)

    assert manifest["secret_policy"] == "metadata_only_no_raw_keys"
    assert manifest["agent_count"] == 2
    assert set(loaded) == {"seer", "lyra"}
    assert loaded["seer"] != loaded["lyra"]
    assert "seer" not in (tmp_path / "seer.dpapi").read_text(encoding="utf-8")
    assert loaded["seer"] not in (tmp_path / "manifest.json").read_text(encoding="utf-8")
