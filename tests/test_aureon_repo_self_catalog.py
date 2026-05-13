import json
from pathlib import Path

from aureon.autonomous.aureon_repo_self_catalog import (
    build_label,
    build_repo_self_catalog,
    render_markdown,
    write_report,
)


def test_build_label_reads_python_symbols_without_secret_values(tmp_path):
    root = tmp_path
    source = root / "aureon" / "autonomous" / "demo_system.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        '"""Demo autonomous system."""\n'
        "import os\n\n"
        "class DemoSystem:\n"
        "    pass\n\n"
        "def run_demo():\n"
        "    return True\n",
        encoding="utf-8",
    )
    secret = root / ".env"
    secret.write_text("KRAKEN_API_SECRET=not-for-manifest\n", encoding="utf-8")

    source_label = build_label(source, root)
    secret_label = build_label(secret, root)

    assert source_label.subsystem == "autonomy_and_self_management"
    assert source_label.python_symbols.module == "aureon.autonomous.demo_system"
    assert "DemoSystem" in source_label.python_symbols.classes
    assert "run_demo" in source_label.python_symbols.functions
    assert source_label.role == "Demo autonomous system."
    assert secret_label.read_status == "metadata_only_secret"
    assert secret_label.data_sensitivity == "secret_metadata_only"
    assert "not-for-manifest" not in secret_label.llm_context


def test_catalog_labels_project_files_and_records_excluded_infrastructure(tmp_path):
    root = tmp_path
    (root / "aureon" / "core").mkdir(parents=True)
    (root / "aureon" / "core" / "thought_bus.py").write_text("class ThoughtBus: pass\n", encoding="utf-8")
    (root / "Kings_Accounting_Suite" / "tools").mkdir(parents=True)
    (root / "Kings_Accounting_Suite" / "tools" / "ledger.py").write_text("def build_ledger(): pass\n", encoding="utf-8")
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / "node_modules" / "pkg" / "ignored.js").write_text("module.exports = 1\n", encoding="utf-8")

    report = build_repo_self_catalog(root, vault_note=None)

    paths = {label.path for label in report.labels}
    assert "aureon/core/thought_bus.py" in paths
    assert "Kings_Accounting_Suite/tools/ledger.py" in paths
    assert "node_modules/pkg/ignored.js" not in paths
    assert any(item.path == "node_modules" for item in report.excluded_infrastructure_roots)
    assert report.summary["cataloged_file_count"] == 2
    assert report.summary["excluded_infrastructure_root_count"] == 1
    assert report.summary["coverage_policy"].startswith("Every project file")


def test_write_report_outputs_json_csv_markdown_and_vault_note(tmp_path):
    root = tmp_path
    (root / "docs").mkdir()
    (root / "docs" / "README.md").write_text("# Knowledge\n", encoding="utf-8")
    report = build_repo_self_catalog(root, vault_note=Path(".obsidian/Aureon Self Understanding/repo_self_catalog.md"))

    markdown = render_markdown(report)
    assert "Aureon Repo Self-Catalog" in markdown
    assert "What Aureon Can Know About Itself" in markdown

    md_path, json_path, csv_path, vault_path = write_report(
        report,
        tmp_path / "self_catalog.md",
        tmp_path / "self_catalog.json",
        tmp_path / "self_catalog.csv",
        write_vault=True,
    )

    assert md_path.exists()
    assert csv_path.exists()
    assert vault_path and vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "aureon-repo-self-catalog-v1"
    assert data["vault_memory"]["status"] == "written"
    assert data["labels"][0]["path"] == "docs/README.md"
