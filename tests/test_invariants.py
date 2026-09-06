"""Result invariant validation over real generated tables.

These run against actual pipeline output, not just synthetic column
names, so a regression in any upstream module gets caught here too.
"""
import pandas as pd
import pytest

from locbench3d.experiment.schema import ScenarioSpec
from locbench3d.hardware.profiles import get_profile
from locbench3d.metrics.range_comparison import build_range_comparison_rows
from locbench3d.tables.master_row import build_master_row
from locbench3d.tables.pipeline import run_scenario
from locbench3d.validate.invariants import (
    InvariantViolation,
    check_master_table,
    check_no_duplicate_scenario_ids,
    check_range_comparison_table,
    check_scalability_results,
)


def _spec(scenario_id="scenario-000001", **overrides):
    base = dict(
        scenario_id=scenario_id, method="UWB_SS_TWR", anchor_count=5, tag_count=1,
        update_rate_hz=1.0, width_m=10.0, length_m=10.0, height_m=4.0,
        frame_duration_s=0.001, guard_duration_s=0.0002,
    )
    base.update(overrides)
    return ScenarioSpec(**base)


def test_valid_master_table_has_no_violations():
    result = run_scenario(_spec(), n_repeats=10, seed=0)
    hw = get_profile("Semtech SX1280")
    df = pd.DataFrame([build_master_row(result, hw)])
    violations = check_master_table(df)
    assert violations == []


def test_duplicate_scenario_ids_are_caught():
    df = pd.DataFrame([{"scenario_id": "s1"}, {"scenario_id": "s1"}])
    violations = check_no_duplicate_scenario_ids(df)
    assert len(violations) == 1
    assert isinstance(violations[0], InvariantViolation)


def test_valid_fixes_exceeding_attempted_is_caught():
    df = pd.DataFrame(
        [{"scenario_id": "s1", "rel_attempted_fixes": 5, "rel_valid_fixes": 10}]
    )
    violations = check_master_table(df)
    assert any("valid" in v.message.lower() for v in violations)


def test_p99_below_p95_is_caught():
    df = pd.DataFrame(
        [{"scenario_id": "s1", "acc_error_3d_p50_m": 1.0, "acc_error_3d_p95_m": 2.0, "acc_error_3d_p99_m": 1.5}]
    )
    violations = check_master_table(df)
    assert any("p99" in v.message.lower() for v in violations)


def test_range_comparison_table_never_has_empty_bins():
    result = run_scenario(_spec(), n_repeats=20, seed=0)
    rows = build_range_comparison_rows(
        "s1", "UWB_SS_TWR", "hw", "env", result.fixes,
        bin_edges_m=[0, 5, 10, 15, 20, 1000],
        evidence=result.error_model_evidence,
    )
    df = pd.DataFrame([r.__dict__ for r in rows])
    violations = check_range_comparison_table(df)
    assert violations == []


def test_range_comparison_flags_a_synthetic_empty_bin():
    df = pd.DataFrame([{"attempted_fixes": 0, "valid_fixes": 0}])
    violations = check_range_comparison_table(df)
    assert any("empty" in v.message.lower() for v in violations)


def test_overloaded_scalability_result_flagged_if_not_marked_infeasible():
    from locbench3d.metrics.scalability import ScalabilityResult
    from locbench3d.protocol.traffic import RangingMethod

    bad = ScalabilityResult(
        method=RangingMethod.SS_TWR, anchor_count=4, tag_count=1000,
        requested_update_rate_hz=50.0, frames_per_fix=8, frame_duration_s=0.001,
        guard_duration_s=0.0, scheduling_model="scheduled",
        frames_per_second_offered=1e6, airtime_fraction=5.0, scheduled_occupancy=5.0,
        overloaded=False,  # deliberately wrong for this test
        collision_probability=None, packet_delivery_probability=None,
        requested_fixes_per_second=1000.0, achievable_fixes_per_second=1000.0,
        achieved_per_tag_update_rate_hz=1.0, max_supported_tags=1,
    )
    violations = check_scalability_results([bad])
    assert len(violations) == 1
