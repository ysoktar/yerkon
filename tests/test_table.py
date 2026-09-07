import csv
import os

import pytest

from yerkon.metrics import CostBreakdown, compute_reliability_metrics, cost_per_area
from yerkon.render import BASELINE_ROWS, IMAGE_COLUMNS, wrap_for_image
from yerkon.scenarios import all_scenarios, run_scenario
from yerkon.table import (
    COLUMNS,
    build_rows,
    detail_records,
    fmt_area,
    fmt_lira,
    fmt_metres,
    fmt_percent,
    write_csv,
)


@pytest.fixture(scope="module")
def results():
    return [run_scenario(s, n_repeats=3) for s in all_scenarios()]


def test_numbers_are_formatted_turkish_style():
    assert fmt_metres(1.937) == "1,94"
    assert fmt_percent(0.9772) == "≈ %97,7"
    assert fmt_lira(471523.8) == "≈ 471.524"
    assert fmt_area(1.008) == "1,01"


def test_large_distances_are_rounded_rather_than_given_false_precision():
    assert fmt_metres(232.78) == "≈ 233"


def test_a_missing_value_is_a_dash_not_a_zero():
    assert fmt_metres(None) == "-"
    assert fmt_percent(None) == "-"
    assert fmt_lira(None) == "-"


def test_four_rows_come_out_with_one_cell_per_column(results):
    rows = build_rows(results)
    assert len(rows) == 4
    assert all(len(row) == len(COLUMNS) for row in rows)


def test_every_row_carries_a_footnote_marker(results):
    markers = [row[0][-1] for row in build_rows(results)]
    assert markers == ["¹", "²", "³", "⁴"]


def test_opex_is_left_blank_rather_than_guessed(results):
    assert all(row[-1] == "-" for row in build_rows(results))


def test_csv_round_trips_with_the_header(tmp_path, results):
    rows = build_rows(results)
    path = os.path.join(tmp_path, "rows.csv")
    write_csv(rows, path)
    with open(path, encoding="utf-8-sig") as handle:
        read_back = list(csv.reader(handle))
    assert tuple(read_back[0]) == COLUMNS
    assert len(read_back) == 5
    assert read_back[1][0].startswith("YERKON")


def test_image_and_csv_use_the_same_column_count():
    assert len(IMAGE_COLUMNS) == len(COLUMNS)
    assert all(len(row) == len(COLUMNS) for row in BASELINE_ROWS)


def test_wrapping_for_the_image_changes_layout_but_not_content(results):
    rows = build_rows(results)
    wrapped = wrap_for_image(rows)
    def squash(cell):
        return "".join(cell.split())

    for plain, image in zip(rows, wrapped):
        assert [squash(c) for c in image] == [squash(c) for c in plain]


def test_details_expose_the_geometry_behind_each_row(results):
    records = detail_records(results)
    assert len(records) == 4
    for record in records:
        assert record["median_vdop"] is not None
        assert record["evidence_type"]
        assert record["error_model_scope"]
        assert record["anchor_count"] > 0


def test_availability_column_matches_the_valid_fix_rate(results):
    rows = build_rows(results)
    for row, result in zip(rows, results):
        assert row[6] == fmt_percent(result.reliability.valid_fix_rate)


def test_cost_per_area_rejects_a_zero_area():
    with pytest.raises(ValueError):
        cost_per_area(CostBreakdown(anchor_cost=100.0), 0.0)


def test_reliability_over_no_attempts_reports_nothing_rather_than_zero():
    result = compute_reliability_metrics([])
    assert result.valid_fix_rate is None
    assert result.attempted_fixes == 0
