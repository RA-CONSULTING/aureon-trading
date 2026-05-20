from __future__ import annotations

from pathlib import Path

from Kings_Accounting_Suite.tools.combined_bank_data import (
    combine_bank_data_for_period,
    parse_zempler_statement_text,
)


def test_combined_bank_data_merges_sources_and_removes_overlapping_statement_rows(tmp_path: Path) -> None:
    uploads = tmp_path / "uploads"
    business = tmp_path / "bussiness accounts"
    uploads.mkdir()
    business.mkdir()

    first_statement = uploads / "Statement_06_Apr_2024_05_Apr_2025.csv"
    first_statement.write_text(
        "\n".join(
            [
                "Date,Description,Amount,Balance",
                "2024-05-02,Client payment,100.00,100.00",
                "2024-06-03,Software,-12.50,87.50",
            ]
        ),
        encoding="utf-8",
    )

    overlapping_statement = uploads / "Statement_31_Aug_2024_10_Apr_2026.csv"
    overlapping_statement.write_text(
        "\n".join(
            [
                "Date,Description,Amount,Balance",
                "2024-05-02,Client payment,100.00,100.00",
                "2025-05-01,Outside period,20.00,120.00",
            ]
        ),
        encoding="utf-8",
    )

    second_account = business / "Transactions Report MSAGM9YS 20260414.csv"
    second_account.write_text(
        "\n".join(
            [
                "Transaction date,Transaction code,Reference,Amount,Available balance",
                "2024-07-10,FPI,Second account income,55.25,55.25",
            ]
        ),
        encoding="utf-8",
    )
    (business / "Statement__GBP_20240501-20240531.pdf").write_text("pdf evidence", encoding="utf-8")

    combined = combine_bank_data_for_period(tmp_path, "2024-05-01", "2025-04-30")
    summary = combined.to_summary()

    assert summary["csv_source_count"] == 3
    assert summary["pdf_source_count"] == 1
    assert summary["transaction_source_count"] == 4
    assert summary["evidence_file_count"] == 1
    assert summary["rows_in_period_before_dedupe"] == 4
    assert summary["unique_rows_in_period"] == 3
    assert summary["duplicate_rows_removed"] == 1
    assert "MSAGM9YS" in summary["source_accounts"]
    assert "uploads_statement" in summary["source_accounts"]
    assert summary["source_provider_summary"]["revolut"]["rows"] == 3
    assert summary["flow_provider_summary"]["revolut"]["rows"] == 3

    standard_csv = combined.to_standard_csv()
    assert "Source File" not in standard_csv
    assert "Second account income" in standard_csv

    full_csv = combined.to_full_csv()
    assert "Source File" in full_csv
    assert "Source Provider" in full_csv
    assert str(second_account) in full_csv


def test_zempler_statement_text_parser_extracts_rows_from_pdf_text(tmp_path: Path) -> None:
    statement = tmp_path / "Statement__GBP_20240601-20240630.pdf"
    text = "\n".join(
        [
            "Date",
            "Card ending in",
            "Description",
            "Amount",
            "Balance",
            "21/06/2024",
            "7528",
            "BROWN T Tina",
            "Â£405.00",
            "Â£405.44",
            "22/06/2024",
            "7528",
            "Fin: ChangeGroup UK Falls,Belfast, Ant",
            "-Â£401.00",
            "-Â£7.56",
            "Zempler Bank Ltd is registered in England and Wales",
        ]
    )

    rows = parse_zempler_statement_text(
        text,
        path=statement,
        source_account="business_gbp_monthly",
        source_directory="bussiness accounts",
    )

    assert rows == [
        {
            "Date": "2024-06-21",
            "Description": "BROWN T Tina",
            "Amount": "405.00",
            "Balance": "405.44",
            "Source File": str(statement),
            "Source Account": "business_gbp_monthly",
            "Source Directory": "bussiness accounts",
            "Source Provider": "zempler",
            "Flow Provider": "zempler",
            "Transaction Code": "7528",
            "Duplicate Source Files": "",
            "Duplicate Source Accounts": "",
            "Duplicate Source Providers": "",
        },
        {
            "Date": "2024-06-22",
            "Description": "Fin: ChangeGroup UK Falls,Belfast, Ant",
            "Amount": "-401.00",
            "Balance": "-7.56",
            "Source File": str(statement),
            "Source Account": "business_gbp_monthly",
            "Source Directory": "bussiness accounts",
            "Source Provider": "zempler",
            "Flow Provider": "zempler",
            "Transaction Code": "7528",
            "Duplicate Source Files": "",
            "Duplicate Source Accounts": "",
            "Duplicate Source Providers": "",
        },
    ]


def test_combined_bank_data_tags_sumup_flow_without_reclassifying_source_account(tmp_path: Path) -> None:
    business = tmp_path / "bussiness accounts"
    business.mkdir()
    zempler_csv = business / "Statement__GBP_20240501-20240531.csv"
    zempler_csv.write_text(
        "\n".join(
            [
                "Date,Description,Amount,Balance",
                "2024-05-10,Example Owner Sumup,-20.00,80.00",
                "2024-05-11,Ravenous Ravenous,120.00,200.00",
            ]
        ),
        encoding="utf-8",
    )

    combined = combine_bank_data_for_period(tmp_path, "2024-05-01", "2025-04-30")
    summary = combined.to_summary()

    assert summary["source_provider_summary"]["zempler"]["rows"] == 2
    assert summary["flow_provider_summary"]["sumup"]["rows"] == 2
    assert summary["flow_provider_summary"]["sumup"]["money_in"] == "120.00"
    assert summary["flow_provider_summary"]["sumup"]["money_out"] == "-20.00"


def test_combined_bank_data_can_use_explicit_company_raw_data_root(tmp_path: Path) -> None:
    raw_root = tmp_path / "company_raw" / "bank"
    raw_root.mkdir(parents=True)
    (raw_root / "client_bank.csv").write_text(
        "\n".join(
            [
                "Date,Description,Amount,Balance",
                "2024-05-03,Client receipt,250.00,250.00",
            ]
        ),
        encoding="utf-8",
    )

    combined = combine_bank_data_for_period(
        tmp_path,
        "2024-05-01",
        "2025-04-30",
        raw_roots=[raw_root],
        include_default_roots=False,
    )
    summary = combined.to_summary()

    assert summary["csv_source_count"] == 1
    assert summary["transaction_source_count"] == 1
    assert summary["unique_rows_in_period"] == 1
    assert summary["source_provider_summary"]["unknown"]["rows"] == 1
