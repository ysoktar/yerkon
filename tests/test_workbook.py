"""Excel workbook construction and structural validation.

Every required sheet must exist, every sheet with rows must have a header,
and no formula should reference a range shaped in a way openpyxl would
choke on when it re-opens the file (the common spreadsheet-corruption
failure mode this project can actually check for without Excel itself).
"""
import openpyxl
import pandas as pd
import pytest

from locbench3d.workbook.build import REQUIRED_SHEET_NAMES, build_workbook
from locbench3d.validate.workbook_validate import validate_workbook


def _sample_tables():
    return {
        "master_comparison": pd.DataFrame(
            [{"scenario_id": "s1", "method": "UWB_SS_TWR", "acc_error_3d_rmse_m": 0.3}]
        ),
        "range_comparison": pd.DataFrame(
            [{"scenario_id": "s1", "range_bin_lower_m": 0, "range_bin_upper_m": 10, "attempted_fixes": 20}]
        ),
        "hardware_profiles": pd.DataFrame([{"manufacturer": "Semtech", "exact_model": "SX1280"}]),
    }


def test_build_workbook_creates_every_required_sheet(tmp_path):
    path = tmp_path / "test.xlsx"
    build_workbook(_sample_tables(), str(path))
    wb = openpyxl.load_workbook(str(path))
    for name in REQUIRED_SHEET_NAMES:
        assert name in wb.sheetnames, f"missing required sheet: {name}"


def test_populated_sheets_contain_header_and_data_rows(tmp_path):
    path = tmp_path / "test.xlsx"
    build_workbook(_sample_tables(), str(path))
    wb = openpyxl.load_workbook(str(path))
    ws = wb["master_comparison"]
    header = [c.value for c in ws[1]]
    assert "scenario_id" in header
    assert ws.cell(row=2, column=header.index("scenario_id") + 1).value == "s1"


def test_validate_workbook_reports_no_errors_for_a_well_formed_file(tmp_path):
    path = tmp_path / "test.xlsx"
    build_workbook(_sample_tables(), str(path))
    report = validate_workbook(str(path), expected_tables=_sample_tables())
    assert report.errors == []


def test_validate_workbook_flags_missing_sheet(tmp_path):
    path = tmp_path / "test.xlsx"
    build_workbook(_sample_tables(), str(path))
    wb = openpyxl.load_workbook(str(path))
    del wb["dashboard"]
    wb.save(str(path))
    report = validate_workbook(str(path), expected_tables=_sample_tables())
    assert any("dashboard" in e for e in report.errors)


def test_validate_workbook_flags_row_count_mismatch(tmp_path):
    path = tmp_path / "test.xlsx"
    tables = _sample_tables()
    build_workbook(tables, str(path))
    bad_tables = dict(tables)
    bad_tables["master_comparison"] = pd.DataFrame(
        [{"scenario_id": "s1"}, {"scenario_id": "s2"}]
    )
    report = validate_workbook(str(path), expected_tables=bad_tables)
    assert any("master_comparison" in e for e in report.errors)


def test_empty_table_still_produces_a_sheet_with_a_notice(tmp_path):
    path = tmp_path / "test.xlsx"
    tables = _sample_tables()
    tables["gnss_comparison"] = pd.DataFrame()
    build_workbook(tables, str(path))
    wb = openpyxl.load_workbook(str(path))
    assert "gnss_comparison" in wb.sheetnames
    ws = wb["gnss_comparison"]
    assert ws.cell(row=1, column=1).value  # some notice text, not a blank sheet


def test_permission_error_on_save_gets_an_actionable_message(tmp_path, monkeypatch):
    """A common real-world failure: the output file is open in Excel and
    Windows has it locked. The raw openpyxl/zipfile traceback ('Permission
    denied' pointing into library internals) must become an actionable
    message, not just propagate as-is."""
    import openpyxl.workbook.workbook as wb_module

    def _raise_permission_error(self, filename):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(wb_module.Workbook, "save", _raise_permission_error)

    path = tmp_path / "locked.xlsx"
    with pytest.raises(PermissionError) as exc_info:
        build_workbook(_sample_tables(), str(path))
    message = str(exc_info.value)
    assert "open" in message.lower()
    assert "excel" in message.lower() or "another program" in message.lower()
    assert str(path) in message


def test_no_formula_cells_are_written_that_start_with_unsupported_prefix(tmp_path):
    """Guards against a common corruption cause: a cell value that starts
    with '=' from raw string data being misread as a formula on reopen."""
    tables = _sample_tables()
    tables["master_comparison"] = pd.DataFrame([{"scenario_id": "=SUM(A1:A2)", "method": "m"}])
    path = tmp_path / "test.xlsx"
    build_workbook(tables, str(path))
    wb = openpyxl.load_workbook(str(path))
    ws = wb["master_comparison"]
    cell = ws.cell(row=2, column=1)
    assert cell.data_type == "s"  # forced to string, not interpreted as formula
