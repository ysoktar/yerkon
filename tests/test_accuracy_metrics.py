"""Axis, horizontal, vertical, and full-3D accuracy metrics.

P95/P99 are first-class outputs, and a scenario with zero successful
fixes must report None, not 0, for every accuracy field.
"""
import numpy as np
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.simulate.monte_carlo import FixResult
from locbench3d.metrics.accuracy import compute_accuracy_metrics

_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
    source_name="test",
    source_scope="test scope",
)


def _fix(i, ex, ey, ez, success=True, timeout=False):
    e3d = float(np.sqrt(ex**2 + ey**2 + ez**2))
    eh = float(np.hypot(ex, ey))
    ev = float(abs(ez))
    return FixResult(
        scenario_id="s",
        path_id="p",
        sample_index=i,
        repeat_index=0,
        t_s=float(i),
        true_x_m=0.0,
        true_y_m=0.0,
        true_z_m=0.0,
        estimated_x=ex if success else None,
        estimated_y=ey if success else None,
        estimated_z=ez if success else None,
        success=success,
        timeout=timeout,
        error_3d_m=e3d if success else None,
        error_horizontal_m=eh if success else None,
        error_vertical_m=ev if success else None,
        geometry_valid=True,
        geometry_failure_reason=None,
        jacobian_rank=3,
        condition_number=1.0,
        evidence=_EVIDENCE,
    )


def test_axis_bias_and_rmse_match_hand_computation():
    fixes = [_fix(0, 1.0, 0.0, 0.0), _fix(1, -1.0, 0.0, 0.0), _fix(2, 2.0, 0.0, 0.0)]
    result = compute_accuracy_metrics(fixes)
    assert result.x_bias_m == pytest.approx(np.mean([1.0, -1.0, 2.0]))
    assert result.x_rmse_m == pytest.approx(np.sqrt(np.mean([1.0, 1.0, 4.0])))


def test_percentiles_are_ordered_p50_le_p95_le_p99():
    rng = np.random.default_rng(0)
    fixes = [_fix(i, *rng.normal(0, 1, 3)) for i in range(500)]
    result = compute_accuracy_metrics(fixes)
    assert result.error_3d_p50_m <= result.error_3d_p95_m <= result.error_3d_p99_m
    assert result.horizontal_p50_m <= result.horizontal_p95_m <= result.horizontal_p99_m


def test_no_successful_fixes_returns_none_not_zero():
    fixes = [_fix(0, 0, 0, 0, success=False, timeout=True)]
    result = compute_accuracy_metrics(fixes)
    assert result.error_3d_rmse_m is None
    assert result.error_3d_p95_m is None
    assert result.x_bias_m is None


def test_error_ellipsoid_volume_is_positive_for_nondegenerate_errors():
    rng = np.random.default_rng(1)
    fixes = [_fix(i, *rng.normal(0, 1, 3)) for i in range(200)]
    result = compute_accuracy_metrics(fixes)
    assert result.error_ellipsoid_volume_m3 is not None
    assert result.error_ellipsoid_volume_m3 > 0


def test_max_error_matches_sample_maximum():
    fixes = [_fix(0, 3.0, 4.0, 0.0), _fix(1, 0.1, 0.1, 0.1)]
    result = compute_accuracy_metrics(fixes)
    assert result.error_3d_max_m == pytest.approx(5.0)
