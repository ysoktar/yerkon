"""Reliability metrics: dropout, solver-failure, outliers, availability.

Failed and timed-out attempts must count in the denominators, and a
threshold-based availability metric must not be computed with a threshold
the caller never provided.
"""
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.metrics.reliability import compute_reliability_metrics
from locbench3d.simulate.monte_carlo import FixResult

_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO, source_name="t", source_scope="t"
)


def _fix(i, success, timeout, error_3d=None):
    return FixResult(
        scenario_id="s", path_id="p", sample_index=i, repeat_index=0, t_s=float(i),
        true_x_m=0.0, true_y_m=0.0, true_z_m=0.0,
        estimated_x=0.0 if success else None,
        estimated_y=0.0 if success else None,
        estimated_z=0.0 if success else None,
        success=success, timeout=timeout,
        error_3d_m=error_3d, error_horizontal_m=error_3d, error_vertical_m=0.0,
        geometry_valid=True, geometry_failure_reason=None, jacobian_rank=3,
        condition_number=1.0, evidence=_EVIDENCE,
    )


def test_attempted_valid_invalid_counts():
    fixes = [
        _fix(0, True, False, 0.1),
        _fix(1, True, False, 0.2),
        _fix(2, False, True),  # dropout
        _fix(3, False, False),  # solver failure
    ]
    r = compute_reliability_metrics(fixes)
    assert r.attempted_fixes == 4
    assert r.valid_fixes == 2
    assert r.invalid_fixes == 2
    assert r.valid_fix_rate == pytest.approx(0.5)
    assert r.dropout_rate == pytest.approx(0.25)
    assert r.solver_failure_rate == pytest.approx(0.25)


def test_availability_under_threshold_counts_failures_as_unavailable():
    fixes = [
        _fix(0, True, False, 0.05),
        _fix(1, True, False, 5.0),
        _fix(2, False, True),
    ]
    r = compute_reliability_metrics(fixes, accuracy_thresholds_m=[0.1, 1.0])
    assert r.availability_by_threshold[0.1] == pytest.approx(1 / 3)
    assert r.availability_by_threshold[1.0] == pytest.approx(1 / 3)


def test_no_threshold_supplied_means_no_availability_field_invented():
    fixes = [_fix(0, True, False, 0.1)]
    r = compute_reliability_metrics(fixes)
    assert r.availability_by_threshold == {}


def test_empty_input_returns_none_rates_not_zero():
    r = compute_reliability_metrics([])
    assert r.attempted_fixes == 0
    assert r.valid_fix_rate is None
    assert r.dropout_rate is None


def test_longest_outage_counts_consecutive_invalid_attempts():
    fixes = [
        _fix(0, True, False, 0.1),
        _fix(1, False, True),
        _fix(2, False, True),
        _fix(3, False, False),
        _fix(4, True, False, 0.1),
    ]
    r = compute_reliability_metrics(fixes)
    assert r.longest_outage_fixes == 3


def test_reacquisition_time_is_none_when_not_modeled():
    r = compute_reliability_metrics([_fix(0, True, False, 0.1)])
    assert r.reacquisition_time_s is None
