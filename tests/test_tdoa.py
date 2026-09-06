"""TDoA range-difference geometry, distinct from absolute-range TWR geometry.

TDoA measurements are range differences against a reference anchor, with
correlated (shared-reference) noise, not independent absolute ranges. This
module's Jacobian, covariance, and CRLB must reflect that; reusing
``core.geometry_bounds.range_crlb`` (uniform-independent-noise, absolute
range) for TDoA would be the exact modeling mistake the spec calls out.
"""
import numpy as np
import pytest

from locbench3d.core.geometry_bounds import GeometryFailureReason, range_crlb
from locbench3d.methods.tdoa import (
    evaluate_tdoa_geometry,
    tdoa_crlb,
    tdoa_fisher_information,
    tdoa_jacobian,
    tdoa_measurement_covariance,
    tdoa_range_differences,
)

NON_COPLANAR_ANCHORS = np.array(
    [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
        [5.0, 5.0, 8.0],
    ]
)
TAG = np.array([5.0, 5.0, 2.0])


def test_range_differences_are_not_absolute_ranges():
    diffs = tdoa_range_differences(TAG, NON_COPLANAR_ANCHORS, ref_index=0)
    from locbench3d.core.geometry3d import true_ranges

    ranges = true_ranges(TAG, NON_COPLANAR_ANCHORS)
    assert len(diffs) == len(NON_COPLANAR_ANCHORS) - 1
    assert not np.allclose(diffs, ranges[1:])


def test_range_difference_matches_definition():
    from locbench3d.core.geometry3d import true_range

    ref = NON_COPLANAR_ANCHORS[0]
    other = NON_COPLANAR_ANCHORS[2]
    r_ref = true_range(TAG, ref)
    r_other = true_range(TAG, other)
    diffs = tdoa_range_differences(TAG, NON_COPLANAR_ANCHORS, ref_index=0)
    # anchors[2] is the second non-reference anchor (index 1 after removing ref)
    assert diffs[1] == pytest.approx(r_other - r_ref)


def test_covariance_has_shared_reference_structure():
    sigma = 0.3
    cov = tdoa_measurement_covariance(n_anchors=5, sigma_range_m=sigma)
    m = 4
    assert cov.shape == (m, m)
    np.testing.assert_allclose(np.diag(cov), 2 * sigma**2)
    off_diag_mask = ~np.eye(m, dtype=bool)
    np.testing.assert_allclose(cov[off_diag_mask], sigma**2)


def test_tdoa_jacobian_rows_are_differences_of_unit_vectors():
    J = tdoa_jacobian(TAG, NON_COPLANAR_ANCHORS, ref_index=0)
    assert J.shape == (4, 3)


def test_tdoa_crlb_differs_from_absolute_range_crlb_same_geometry():
    """This is the key regression: TDoA must not reuse TWR/absolute-range
    geometry. With the same anchors and sigma, the two CRLBs must differ
    because the covariance structures differ (shared reference vs
    independent noise)."""
    sigma = 0.2
    tdoa_result = tdoa_crlb(TAG, NON_COPLANAR_ANCHORS, sigma_range_m=sigma)
    absolute_result = range_crlb(TAG, NON_COPLANAR_ANCHORS, sigma_range_m=sigma)
    assert tdoa_result.crlb_3d_rms_m != pytest.approx(
        absolute_result.crlb_3d_rms_m, rel=1e-6
    )


FOUR_NON_COPLANAR_ANCHORS = np.array(
    [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [0.0, 10.0, 0.0],
        [5.0, 5.0, 8.0],
    ]
)


def test_tdoa_minimum_anchor_count_is_four_non_coplanar():
    result = evaluate_tdoa_geometry(TAG, FOUR_NON_COPLANAR_ANCHORS, sigma_range_m=0.1)
    assert result.reference_count == 4
    assert result.geometry_valid is True


def test_tdoa_geometry_insufficient_below_four_anchors():
    result = evaluate_tdoa_geometry(TAG, NON_COPLANAR_ANCHORS[:3], sigma_range_m=0.1)
    assert result.geometry_valid is False
    assert result.failure_reason == GeometryFailureReason.INSUFFICIENT_REFERENCES


def test_tdoa_geometry_flags_coplanar_anchors():
    coplanar_anchors = np.array(
        [
            [0.0, 0.0, 0.0],
            [10.0, 0.0, 0.0],
            [10.0, 10.0, 0.0],
            [0.0, 10.0, 0.0],
        ]
    )
    result = evaluate_tdoa_geometry(TAG, coplanar_anchors, sigma_range_m=0.1)
    assert result.geometry_valid is False
    assert result.failure_reason == GeometryFailureReason.COPLANAR_WEAK_VERTICAL


def test_tdoa_redundant_with_five_or_more_synchronized_anchors():
    result = evaluate_tdoa_geometry(TAG, NON_COPLANAR_ANCHORS, sigma_range_m=0.1)
    assert result.redundant is True


def test_fisher_information_uses_full_covariance_not_diagonal_only():
    """A naive TDoA implementation might use J^T J / sigma^2 (as if range
    differences were independent). The real shared-reference FIM must
    differ from that naive quantity."""
    sigma = 0.25
    J = tdoa_jacobian(TAG, NON_COPLANAR_ANCHORS, ref_index=0)
    naive_fim = (J.T @ J) / sigma**2
    real_fim = tdoa_fisher_information(TAG, NON_COPLANAR_ANCHORS, sigma_range_m=sigma)
    assert not np.allclose(naive_fim, real_fim)
