"""Geometry validity, Jacobian/FIM rank, CRLB, DOP, and convex-hull checks.

These tests use small hand-checkable anchor layouts so the numbers can be
verified by inspection, not just by re-running the code that produced them.
"""
import numpy as np
import pytest

from locbench3d.core.geometry_bounds import (
    GeometryFailureReason,
    condition_number,
    convex_hull_contains,
    coplanar,
    dop_from_jacobian,
    evaluate_geometry,
    range_crlb,
    range_jacobian,
)


COPLANAR_ANCHORS = np.array(
    [
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
    ]
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


def test_coplanar_detects_four_flat_anchors():
    assert coplanar(COPLANAR_ANCHORS) is True


def test_coplanar_false_for_five_anchor_layout_with_height_spread():
    assert coplanar(NON_COPLANAR_ANCHORS) is False


def test_range_jacobian_shape_is_n_by_3():
    J = range_jacobian(TAG, NON_COPLANAR_ANCHORS)
    assert J.shape == (5, 3)


def test_range_jacobian_rows_are_unit_vectors():
    J = range_jacobian(TAG, NON_COPLANAR_ANCHORS)
    norms = np.linalg.norm(J, axis=1)
    np.testing.assert_allclose(norms, np.ones(5), atol=1e-9)


def test_three_anchors_cannot_resolve_3d_rank():
    """3 anchors give a Jacobian with rank at most 3, but with 3 anchors and
    unknowns (x, y, z) the geometry is not over-determined and, for a flat
    triangle, height is degenerate."""
    flat_three = COPLANAR_ANCHORS[:3]
    result = evaluate_geometry(TAG, flat_three, sigma_range_m=0.1)
    assert result.jacobian_rank <= 3
    assert result.geometry_valid is False
    assert result.failure_reason == GeometryFailureReason.INSUFFICIENT_REFERENCES


def test_four_coplanar_anchors_flagged_as_weak_vertical_geometry():
    result = evaluate_geometry(TAG, COPLANAR_ANCHORS, sigma_range_m=0.1)
    assert result.jacobian_rank == 3  # mathematically full row-rank possible
    assert result.geometry_valid is False
    assert result.failure_reason == GeometryFailureReason.COPLANAR_WEAK_VERTICAL


def test_five_non_coplanar_anchors_are_geometry_valid_and_redundant():
    result = evaluate_geometry(TAG, NON_COPLANAR_ANCHORS, sigma_range_m=0.1)
    assert result.jacobian_rank == 3
    assert result.geometry_valid is True
    assert result.failure_reason is None
    assert result.redundant is True  # 5 anchors > 4 minimum


def test_crlb_matches_closed_form_for_symmetric_layout():
    """For 4 anchors arranged so the FIM is a multiple of the identity, the
    CRLB has a simple closed form we can check by hand."""
    anchors = np.array(
        [
            [10.0, 0.0, 0.0],
            [-10.0, 0.0, 0.0],
            [0.0, 10.0, 0.0],
            [0.0, -10.0, 0.0],
        ]
    )
    tag = np.array([0.0, 0.0, 0.0])
    sigma = 0.2
    crlb = range_crlb(tag, anchors, sigma_range_m=sigma)
    # Each unit vector from the origin points straight at its anchor along a
    # single axis, so J^T J = diag(2/sigma^2, 2/sigma^2, 0) for x, y and a
    # singular z. z is unobservable here, matching a coplanar ring at z=0.
    assert crlb.crlb_x_m == pytest.approx(sigma / np.sqrt(2), rel=1e-6)
    assert crlb.crlb_y_m == pytest.approx(sigma / np.sqrt(2), rel=1e-6)
    assert crlb.crlb_z_m is None  # unobservable, must not be silently zero


def test_condition_number_worsens_for_near_collinear_anchors():
    good = NON_COPLANAR_ANCHORS
    collinear = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.01, 0.0],
            [2.0, -0.01, 0.0],
            [3.0, 0.01, 0.0],
        ]
    )
    cn_good = condition_number(range_jacobian(TAG, good))
    cn_bad = condition_number(range_jacobian(TAG, collinear))
    assert cn_bad > cn_good


def test_convex_hull_containment_true_when_tag_inside_anchor_volume():
    assert convex_hull_contains(TAG, NON_COPLANAR_ANCHORS) is True


def test_convex_hull_containment_false_when_tag_outside():
    outside = np.array([100.0, 100.0, 100.0])
    assert convex_hull_contains(outside, NON_COPLANAR_ANCHORS) is False


def test_dop_values_are_positive_and_pdop_combines_h_and_v():
    J = range_jacobian(TAG, NON_COPLANAR_ANCHORS)
    dop = dop_from_jacobian(J)
    assert dop.hdop > 0
    assert dop.vdop > 0
    assert dop.pdop == pytest.approx(np.sqrt(dop.hdop**2 + dop.vdop**2), rel=1e-9)
