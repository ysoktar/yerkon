"""Structural validation of a generated workbook.

Checks that every required sheet exists, that populated sheets' row/column
shape matches the tables that were supposed to produce them, and scans
every cell for literal Excel error tokens (a defensive check; this
project's workbook has no live formulas to begin with, since every sheet
is pre-computed by Python, so the class of "formula recalculates to an
error" bug this check would normally guard against cannot occur here -
the scan stays in place in case a future formula is added).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import openpyxl
import pandas as pd

from locbench3d.workbook.build import REQUIRED_SHEET_NAMES

_EXCEL_ERROR_TOKENS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#N/A", "#NULL!", "#NUM!")


@dataclass
class WorkbookValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_workbook(
    path: str, expected_tables: dict[str, pd.DataFrame] | None = None
) -> WorkbookValidationReport:
    report = WorkbookValidationReport()
    wb = openpyxl.load_workbook(path)

    for name in REQUIRED_SHEET_NAMES:
        if name not in wb.sheetnames:
            report.errors.append(f"required sheet missing: {name}")

    if expected_tables:
        for name, df in expected_tables.items():
            sheet_title = name[:31]
            if sheet_title not in wb.sheetnames:
                report.errors.append(f"expected table '{name}' has no matching sheet")
                continue
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            ws = wb[sheet_title]
            actual_rows = ws.max_row - 1  # minus header
            if actual_rows != len(df):
                report.errors.append(
                    f"sheet '{name}' has {actual_rows} data rows, expected {len(df)}"
                )
            header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
            expected_cols = list(df.columns)
            if header != expected_cols:
                report.errors.append(
                    f"sheet '{name}' header does not match expected columns"
                )

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.strip() in _EXCEL_ERROR_TOKENS:
                    report.errors.append(
                        f"sheet '{ws.title}' cell {cell.coordinate} contains "
                        f"a spreadsheet error token: {cell.value}"
                    )
                if cell.data_type == "f":
                    report.warnings.append(
                        f"sheet '{ws.title}' cell {cell.coordinate} contains a "
                        "live formula; this project's sheets are expected to be "
                        "fully pre-computed static values"
                    )

    return report
