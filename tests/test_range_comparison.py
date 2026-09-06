"""Range comparison table: one row per scenario and non-empty distance bin.

Empty bins must never be emitted.
"""
import numpy as np
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.metrics.range_comparison import build_range_comparison_rows
from locbench3d.simulate.monte_carlo import FixResult

_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO, source_name="t", source_scope="t"
)


def _fix(true_range, error, success=True):
    return FixResult(
        scenario_id="scenario-1", path_id="p", sample_index=0, repeat_index=0, t_s=0.0,
        true_x_m=true_range, true_y_m=0.0, true_z_m=0.0,
        estimated_x=true_range + error if success else None,
        estimated_y=0.0 if success else None,
        estimated_z=0.0 if success else None,
        success=success, timeout=not success,
        error_3d_m=abs(error) if success else None,
        error_horizontal_m=abs(error) if success else None,
        error_vertical_m=0.0 if success else None,
        geometry_valid=True, geometry_failure_reason=None, jacobian_rank=3,
        condition_number=1.0, evidence=_EVIDENCE,
    )


def test_bins_only_emitted_for_ranges_with_data():
    fixes = [_fix(5.0, 0.1), _fix(5.0, -0.1), _fix(95.0, 0.3)]
    rows = build_range_comparison_rows(
        scenario_id="scenario-1",
        method="UWB_SS_TWR",
        hardware_profile="generic",
        environment="test-env",
        fixes=fixes,
        bin_edges_m=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        evidence=_EVIDENCE,
    )
    bins_with_data = {(r.range_bin_lower_m, r.range_bin_upper_m) for r in rows}
    assert bins_with_data == {(0, 10), (90, 100)}
    assert len(rows) == 2


def test_row_contains_bias_and_rmse_for_its_bin():
    fixes = [_fix(5.0, 0.2), _fix(5.0, -0.2)]
    rows = build_range_comparison_rows(
        scenario_id="s", method="m", hardware_profile="h", environment="e",
        fixes=fixes, bin_edges_m=[0, 10], evidence=_EVIDENCE,
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.attempted_fixes == 2
    assert row.valid_fixes == 2
    assert row.measurement_bias_m == pytest.approx(0.0, abs=1e-9)
    assert row.measurement_rmse_m == pytest.approx(0.2, abs=1e-9)


def test_failed_attempts_count_toward_attempted_but_not_bias_rmse():
    fixes = [_fix(5.0, 0.1), _fix(5.0, 0.0, success=False)]
    rows = build_range_comparison_rows(
        scenario_id="s", method="m", hardware_profile="h", environment="e",
        fixes=fixes, bin_edges_m=[0, 10], evidence=_EVIDENCE,
    )
    row = rows[0]
    assert row.attempted_fixes == 2
    assert row.valid_fixes == 1
    assert row.dropout_rate == pytest.approx(0.5)
