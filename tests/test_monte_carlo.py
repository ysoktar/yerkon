"""Monte Carlo scenario simulation: raw 3D fix results over a path.

Failed/timed-out attempts are kept (not filtered out), positions are
solved natively in 3D, and geometry-validity fields match the independent
geometry evaluator for the same anchors/position.
"""
import numpy as np
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.core.geometry_bounds import evaluate_geometry
from locbench3d.paths.trajectories import static_points_path
from locbench3d.protocol.traffic import RangingMethod
from locbench3d.simulate.monte_carlo import simulate_path_fixes

ANCHORS = np.array(
    [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
        [5.0, 5.0, 8.0],
    ]
)

_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
    source_name="unit test error model",
    source_scope="Zero-mean synthetic noise for solver regression testing only.",
)


def _zero_noise_sampler(n: int) -> np.ndarray:
    return np.zeros(n)


def test_simulate_path_fixes_recovers_true_positions_with_zero_noise():
    path = static_points_path("p1", [(4.0, 6.0, 1.5), (2.0, 2.0, 3.0)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-1",
        method=RangingMethod.SS_TWR,
        anchors=ANCHORS,
        path=path,
        error_sampler=_zero_noise_sampler,
        evidence=_EVIDENCE,
        n_repeats=1,
        seed=0,
    )
    assert len(results) == 2
    for r in results:
        assert r.success is True
        assert r.timeout is False
        assert r.error_3d_m == pytest.approx(0.0, abs=1e-4)
        assert r.error_horizontal_m == pytest.approx(0.0, abs=1e-4)
        assert r.error_vertical_m == pytest.approx(0.0, abs=1e-4)


def test_simulate_path_fixes_repeats_count_matches_request():
    path = static_points_path("p1", [(4.0, 6.0, 1.5)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-2",
        method=RangingMethod.SS_TWR,
        anchors=ANCHORS,
        path=path,
        error_sampler=lambda n: np.random.default_rng(1).normal(0, 0.1, n),
        evidence=_EVIDENCE,
        n_repeats=5,
        seed=1,
    )
    assert len(results) == 5


def test_zero_delivery_probability_produces_only_timeouts_no_fabricated_position():
    path = static_points_path("p1", [(4.0, 6.0, 1.5)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-3",
        method=RangingMethod.SS_TWR,
        anchors=ANCHORS,
        path=path,
        error_sampler=_zero_noise_sampler,
        evidence=_EVIDENCE,
        n_repeats=10,
        seed=2,
        delivery_probability=0.0,
    )
    assert len(results) == 10
    for r in results:
        assert r.timeout is True
        assert r.success is False
        assert r.estimated_x is None
        assert r.error_3d_m is None


def test_geometry_fields_match_independent_evaluator():
    path = static_points_path("p1", [(4.0, 6.0, 1.5)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-4",
        method=RangingMethod.SS_TWR,
        anchors=ANCHORS,
        path=path,
        error_sampler=_zero_noise_sampler,
        evidence=_EVIDENCE,
        n_repeats=1,
        seed=0,
    )
    r = results[0]
    expected = evaluate_geometry(np.array([4.0, 6.0, 1.5]), ANCHORS, sigma_range_m=1.0)
    assert r.geometry_valid == expected.geometry_valid
    assert r.jacobian_rank == expected.jacobian_rank


def test_tdoa_method_uses_range_difference_solver():
    path = static_points_path("p1", [(4.0, 6.0, 1.5)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-5",
        method=RangingMethod.TDOA,
        anchors=ANCHORS,
        path=path,
        error_sampler=_zero_noise_sampler,
        evidence=_EVIDENCE,
        n_repeats=1,
        seed=0,
    )
    assert results[0].success is True
    assert results[0].error_3d_m == pytest.approx(0.0, abs=1e-3)


def test_evidence_survives_on_every_result():
    path = static_points_path("p1", [(4.0, 6.0, 1.5)], dwell_s=1.0)
    results = simulate_path_fixes(
        scenario_id="scenario-6",
        method=RangingMethod.SS_TWR,
        anchors=ANCHORS,
        path=path,
        error_sampler=_zero_noise_sampler,
        evidence=_EVIDENCE,
        n_repeats=1,
        seed=0,
    )
    assert results[0].evidence.evidence_type == EvidenceType.SIMULATED_MONTE_CARLO
