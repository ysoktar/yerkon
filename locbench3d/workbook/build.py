"""Excel workbook construction.

The workbook is fully pre-computed by Python: every sheet is written as
static values, not live formulas. This sidesteps an entire class of
spreadsheet-corruption and formula-error risk (a stale reference, a
locale-dependent function, a circular reference) and means the workbook
needs no formula engine to open correctly, only a standard XLSX reader.

Every required sheet from the requirements document is created regardless
of what data is supplied to ``build_workbook``: a required sheet with no
table supplied gets a placeholder notice instead of being silently
skipped, so `wb.sheetnames` always matches the full required list.
"""
from __future__ import annotations

from typing import Optional, Union

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

REQUIRED_SHEET_NAMES: tuple[str, ...] = (
    "start_here",
    "experiment_requirements",
    "experiment_design",
    "experiment_count_preview",
    "hardware_profiles",
    "sx1280_software_refs",
    "method_catalog",
    "applicability_matrix",
    "anchor_layouts_3d",
    "path_definitions_3d",
    "master_comparison",
    "sx1280_raw_measurements",
    "sx1280_published_data",
    "standardized_external",
    "range_comparison",
    "path_comparison",
    "geometry_comparison",
    "volume_comparison",
    "channel_comparison",
    "environment_comparison",
    "scalability_comparison",
    "gnss_comparison",
    "accuracy",
    "latency",
    "energy",
    "cost",
    "pareto_analysis",
    "official_references",
    "field_catalog",
    "definitions",
    "equations",
    "sources",
    "dashboard",
)

SheetContent = Union[pd.DataFrame, list, None]


def _to_native(value):
    if value is None:
        return None
    if isinstance(value, float) and value != value:  # NaN
        return None
    if isinstance(value, (list, tuple, set, frozenset)):
        return "|".join(str(v) for v in value)
    if isinstance(value, dict):
        return "|".join(f"{k}:{v}" for k, v in value.items())
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _write_dataframe(ws, df: pd.DataFrame) -> None:
    for col_idx, col_name in enumerate(df.columns, start=1):
        ws.cell(row=1, column=col_idx, value=str(col_name))
    for row_idx, row in enumerate(df.itertuples(index=False), start=2):
        for col_idx, raw_value in enumerate(row, start=1):
            value = _to_native(raw_value)
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value
            if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
                # Force text so a value that merely starts with a formula-like
                # character is never reinterpreted as a live formula on open.
                cell.data_type = "s"
    if len(df) > 0:
        ws.freeze_panes = "A2"
        last_col_letter = get_column_letter(max(len(df.columns), 1))
        ws.auto_filter.ref = f"A1:{last_col_letter}{len(df) + 1}"


def _write_placeholder(ws, message: str) -> None:
    ws.cell(row=1, column=1, value=message)


def _write_text_sheet(ws, lines: list) -> None:
    for i, line in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=str(line))


def build_workbook(
    tables: dict[str, SheetContent],
    output_path: str,
    sheet_notes: Optional[dict[str, str]] = None,
) -> None:
    wb = Workbook()
    wb.remove(wb.active)

    all_names = list(REQUIRED_SHEET_NAMES)
    for name in tables:
        if name not in all_names:
            all_names.append(name)

    for name in all_names:
        title = name[:31]
        ws = wb.create_sheet(title=title)
        content = tables.get(name)
        if isinstance(content, pd.DataFrame):
            if content.empty:
                note = (
                    f"No rows generated for '{name}' in this run. "
                    "This is not a missing feature: either no scenario in "
                    "this run produced data for this table, or (see "
                    "docs/LIMITATIONS.md) the underlying data source was "
                    "not available in this environment."
                )
                _write_placeholder(ws, note)
            else:
                _write_dataframe(ws, content)
        elif isinstance(content, list):
            _write_text_sheet(ws, content)
        else:
            note = (sheet_notes or {}).get(name) or (
                f"Sheet '{name}' has no content in this build. See "
                "docs/ARCHITECTURE.md for what this sheet is meant to hold."
            )
            _write_placeholder(ws, note)

    wb.save(output_path)
