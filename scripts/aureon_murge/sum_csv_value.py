#!/usr/bin/env python3
"""Print the sum of the numeric values in the CSV column named 'Value'."""

from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


def sum_value_column(csv_path: Path) -> Decimal:
    total = Decimal("0")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")
        if "Value" not in reader.fieldnames:
            raise ValueError("CSV file must contain a column named 'Value'.")

        for line_number, row in enumerate(reader, start=2):
            raw_value = (row.get("Value") or "").strip()
            if not raw_value:
                continue
            try:
                total += Decimal(raw_value)
            except InvalidOperation as exc:
                raise ValueError(f"Invalid numeric value on line {line_number}: {raw_value!r}") from exc

    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Sum values from the 'Value' column in a CSV file.")
    parser.add_argument("csv_file", type=Path, help="Path to the input CSV file.")
    args = parser.parse_args()

    try:
        total = sum_value_column(args.csv_file)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
