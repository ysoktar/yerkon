"""Native 3D nonlinear least-squares solvers for TWR/ToA and TDoA."""
import numpy as np
import pytest

from locbench3d.core.geometry3d import true_ranges
from locbench3d.methods.tdoa import tdoa_range_differences
from locbench3d.simulate.solver import solve_position_3d, solve_position_tdoa_3d

ANCHORS = np.array(
    [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
        [5.0, 5.0, 8.0],
    ]
)
TRUE_POSITION = np.array([4.0, 6.0, 1.5])


def test_solve_position_3d_recovers_noiseless_position():
    ranges = true_ranges(TRUE_POSITION, ANCHORS)
    estimate, success, _ = solve_position_3d(ANCHORS, ranges)
    assert success
    np.testing.assert_allclose(estimate, TRUE_POSITION, atol=1e-6)


def test_solve_position_3d_is_native_3d_not_2d_plus_height():
    """Estimating z jointly with x, y (not fixing/solving it separately)."""
    ranges = true_ranges(TRUE_POSITION, ANCHORS)
    estimate, success, _ = solve_position_3d(ANCHORS, ranges, initial_guess=np.array([0.0, 0.0, 0.0]))
    assert success
    assert estimate.shape == (3,)
    np.testing.assert_allclose(estimate, TRUE_POSITION, atol=1e-6)


def test_solve_position_tdoa_3d_recovers_noiseless_position():
    diffs = tdoa_range_differences(TRUE_POSITION, ANCHORS, ref_index=0)
    estimate, success, _ = solve_position_tdoa_3d(ANCHORS, diffs, ref_index=0)
    assert success
    np.testing.assert_allclose(estimate, TRUE_POSITION, atol=1e-4)


def test_solver_handles_noisy_ranges_with_bounded_error():
    rng = np.random.default_rng(0)
    ranges = true_ranges(TRUE_POSITION, ANCHORS) + rng.normal(0, 0.05, size=5)
    estimate, success, _ = solve_position_3d(ANCHORS, ranges)
    assert success
    error = np.linalg.norm(estimate - TRUE_POSITION)
    assert error < 1.0  # generous bound; not a precise statistical claim
