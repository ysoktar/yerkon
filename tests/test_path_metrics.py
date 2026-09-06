"""Path-level metrics: length, speed, along/cross-track error, dropouts.

Tracking lag is never reported: no tracking/filtering model exists in this
project.
"""
import numpy as np
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.metrics.path_metrics import compute_path_metrics
from locbench3d.paths.trajectories import straight_line_path
from locbench3d.simulate.monte_carlo import FixResult

_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO, source_name="t", source_scope="t"
)


def _fix(i, t, tx, ty, tz, ex, ey, ez, success=True):
    e3d = float(np.linalg.norm([ex - tx, ey - ty, ez - tz]))
    eh = float(np.hypot(ex - tx, ey - ty))
    ev = float(abs(ez - tz))
    return FixResult(
        scenario_id="s", path_id="line-1", sample_index=i, repeat_index=0, t_s=t,
        true_x_m=tx, true_y_m=ty, true_z_m=tz,
        estimated_x=ex if success else None,
        estimated_y=ey if success else None,
        estimated_z=ez if success else None,
        success=success, timeout=not success,
        error_3d_m=e3d if success else None,
        error_horizontal_m=eh if success else None,
        error_vertical_m=ev if success else None,
        geometry_valid=True, geometry_failure_reason=None, jacobian_rank=3,
        condition_number=1.0, evidence=_EVIDENCE,
    )


def test_3d_and_horizontal_path_length_for_straight_line():
    path = straight_line_path("line-1", (0, 0, 0), (10, 0, 0), 11, 10.0)
    fixes = [
        _fix(i, path.t_s[i], path.x_m[i], path.y_m[i], path.z_m[i],
             path.x_m[i], path.y_m[i], path.z_m[i])
        for i in range(11)
    ]
    result = compute_path_metrics(path, fixes)
    assert result.path_3d_length_m == pytest.approx(10.0)
    assert result.horizontal_path_length_m == pytest.approx(10.0)
    assert result.vertical_travel_m == pytest.approx(0.0)


def test_mean_and_max_speed_from_true_trajectory():
    path = straight_line_path("line-1", (0, 0, 0), (10, 0, 0), 11, 10.0)
    fixes = [
        _fix(i, path.t_s[i], path.x_m[i], path.y_m[i], path.z_m[i],
             path.x_m[i], path.y_m[i], path.z_m[i])
        for i in range(11)
    ]
    result = compute_path_metrics(path, fixes)
    assert result.mean_speed_m_s == pytest.approx(1.0)
    assert result.max_speed_m_s == pytest.approx(1.0)


def test_dropouts_and_longest_outage_counted():
    path = straight_line_path("line-1", (0, 0, 0), (10, 0, 0), 5, 4.0)
    fixes = [
        _fix(0, 0.0, 0, 0, 0, 0, 0, 0, success=True),
        _fix(1, 1.0, 2.5, 0, 0, 0, 0, 0, success=False),
        _fix(2, 2.0, 5.0, 0, 0, 0, 0, 0, success=False),
        _fix(3, 3.0, 7.5, 0, 0, 0, 0, 0, success=True),
        _fix(4, 4.0, 10.0, 0, 0, 10, 0, 0, success=True),
    ]
    result = compute_path_metrics(path, fixes)
    assert result.dropouts == 2
    assert result.longest_outage == 2


def test_horizontal_and_3d_rmse_over_the_path():
    path = straight_line_path("line-1", (0, 0, 0), (10, 0, 0), 3, 2.0)
    fixes = [
        _fix(0, 0.0, 0, 0, 0, 0.1, 0, 0),
        _fix(1, 1.0, 5, 0, 0, 5.1, 0, 0),
        _fix(2, 2.0, 10, 0, 0, 9.9, 0, 0),
    ]
    result = compute_path_metrics(path, fixes)
    assert result.horizontal_rmse_m == pytest.approx(0.1, abs=1e-9)
    assert result.error_3d_rmse_m == pytest.approx(0.1, abs=1e-9)


def test_sample_count_and_duration():
    path = straight_line_path("line-1", (0, 0, 0), (10, 0, 0), 5, 4.0)
    fixes = [
        _fix(i, path.t_s[i], path.x_m[i], path.y_m[i], path.z_m[i],
             path.x_m[i], path.y_m[i], path.z_m[i])
        for i in range(5)
    ]
    result = compute_path_metrics(path, fixes)
    assert result.sample_count == 5
    assert result.duration_s == pytest.approx(4.0)
