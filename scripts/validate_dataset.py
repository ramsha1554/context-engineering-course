#!/usr/bin/env python3
"""Validate Hugging Face datasets (CSV).

Usage: python validate_dataset.py <filepath> [expected_columns]
Example: python validate_dataset.py data.csv text,label,split
"""

import json
import sys
from pathlib import Path

import pandas as pd


def validate_csv(filepath, expected_columns=None):
    """Validate a CSV dataset file."""
    errors = []
    warnings = []
    report = {
        "filepath": filepath,
        "format": "csv",
        "errors": errors,
        "warnings": warnings,
        "metadata": {},
    }

    if not Path(filepath).exists():
        errors.append(f"File not found: {filepath}")
        return report

    try:
        df = pd.read_csv(filepath)
        report["metadata"]["rows"] = len(df)
        report["metadata"]["columns"] = list(df.columns)
        report["metadata"]["dtypes"] = {k: str(v) for k, v in df.dtypes.items()}

        # Schema check (only if expected columns were given)
        if expected_columns:
            missing_cols = set(expected_columns) - set(df.columns)
            extra_cols = set(df.columns) - set(expected_columns)
            if missing_cols:
                errors.append(f"Missing columns: {sorted(missing_cols)}")
            if extra_cols:
                warnings.append(f"Extra columns: {sorted(extra_cols)}")

        # Missing values
        missing = df.isna().sum()
        if missing.any():
            report["metadata"]["missing_values"] = {
                k: int(v) for k, v in missing.items() if v > 0
            }
            warnings.append(f"Found {int(missing.sum())} missing values")

        # Duplicates
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            warnings.append(f"Found {dup_count} duplicate rows")

        # Empty strings
        for col in df.select_dtypes(include=["object", "string"]).columns:
            empty = int((df[col].astype(str).str.strip() == "").sum())
            if empty > 0:
                warnings.append(f"Column '{col}' has {empty} empty strings")

    except Exception as e:
        errors.append(f"Error reading file: {e}")

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_dataset.py <filepath> [expected_columns]")
        sys.exit(1)

    filepath = sys.argv[1]
    expected = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    report = validate_csv(filepath, expected)
    print(json.dumps(report, indent=2))

    if report["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
