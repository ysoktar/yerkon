"""Native 3D position, range, and error math. No 2D-plus-height shortcuts."""
import numpy as np
import pytest

from locbench3d.core.geometry3d import (
    error_3d,
    error_horizontal,
    error_vertical,
    true_range,
)


def test_true_range_is_full_3d_euclidean_distance():
    p = np.array([3.0, 4.0, 12.0])
    anchor = np.array([0.0, 0.0, 0.0])
    assert true_range(p, anchor) == pytest.approx(13.0)


def test_true_range_matches_pythagorean_3d_example():
    p = np.array([1.0, 2.0, 2.0])
    anchor = np.array([0.0, 0.0, 0.0])
    assert true_range(p, anchor) == pytest.approx(3.0)


def test_error_3d_uses_all_three_axes():
    truth = np.array([0.0, 0.0, 0.0])
    estimate = np.array([1.0, 2.0, 2.0])
    assert error_3d(estimate, truth) == pytest.approx(3.0)


def test_error_horizontal_ignores_z():
    truth = np.array([0.0, 0.0, 5.0])
    estimate = np.array([3.0, 4.0, -50.0])
    assert error_horizontal(estimate, truth) == pytest.approx(5.0)


def test_error_vertical_is_absolute_z_difference():
    truth = np.array([1.0, 1.0, 10.0])
    estimate = np.array([9.0, 9.0, 7.5])
    assert error_vertical(estimate, truth) == pytest.approx(2.5)


def test_error_vertical_is_never_negative():
    truth = np.array([0.0, 0.0, 2.0])
    estimate = np.array([0.0, 0.0, 9.0])
    assert error_vertical(estimate, truth) >= 0


def test_zero_height_change_still_native_3d():
    """A flat path (dz=0) must still go through the 3D formula, not a 2D one
    with height bolted on afterward."""
    truth = np.array([2.0, 2.0, 2.0])
    estimate = np.array([5.0, 6.0, 2.0])
    assert error_3d(estimate, truth) == pytest.approx(5.0)
    assert error_3d(estimate, truth) == pytest.approx(error_horizontal(estimate, truth))
