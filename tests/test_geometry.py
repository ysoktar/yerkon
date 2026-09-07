import numpy as np
import pytest

from yerkon.geometry import (
    GeometryFailureReason,
    coplanar,
    dop_from_jacobian,
    error_horizontal,
    error_vertical,
    evaluate_geometry,
    range_jacobian,
    true_ranges,
)


def test_true_ranges_are_full_3d_distances_not_ground_distances():
    anchors = np.array([[3.0, 4.0, 12.0]])
    assert true_ranges(np.zeros(3), anchors)[0] == pytest.approx(13.0)


def test_horizontal_and_vertical_errors_are_reported_separately():
    estimate = np.array([3.0, 4.0, 10.0])
    truth = np.array([0.0, 0.0, 0.0])
    assert error_horizontal(estimate, truth) == pytest.approx(5.0)
    assert error_vertical(estimate, truth) == pytest.approx(10.0)


def test_two_parallel_lines_of_anchors_are_coplanar():
    # The trap the tunnel layout has to avoid: anchors alternating between
    # two fixed (y, z) mounts trace two parallel lines, and two parallel
    # lines always share a plane no matter how many anchors are on them.
    xs = np.arange(0.0, 1000.0, 50.0)
    anchors = np.array(
        [(x, 2.0, 1.0) if i % 2 == 0 else (x, 18.0, 4.0) for i, x in enumerate(xs)]
    )
    assert coplanar(anchors)


def test_four_step_tunnel_cycle_is_not_coplanar():
    from yerkon.scenarios import tunnel_layout

    assert not coplanar(tunnel_layout(length_m=3000.0).positions)


def test_coplanar_anchor_set_is_rejected_with_a_named_reason():
    anchors = np.array([[0.0, 0.0, 5.0], [100.0, 0.0, 5.0],
                        [0.0, 100.0, 5.0], [100.0, 100.0, 5.0]])
    result = evaluate_geometry(np.array([50.0, 50.0, 1.5]), anchors)
    assert not result.geometry_valid
    assert result.failure_reason is GeometryFailureReason.COPLANAR_WEAK_VERTICAL


def test_too_few_anchors_is_reported_as_insufficient_not_as_bad_geometry():
    anchors = np.array([[0.0, 0.0, 5.0], [100.0, 0.0, 8.0]])
    result = evaluate_geometry(np.array([50.0, 50.0, 1.5]), anchors)
    assert not result.geometry_valid
    assert result.failure_reason is GeometryFailureReason.INSUFFICIENT_REFERENCES


def test_vdop_is_worse_when_anchors_sit_at_shallow_elevation_angles():
    # This is the whole vertical story of the study, as a test: the same
    # four anchors give a far worse VDOP when they are spread wide and
    # mounted low than when they surround the receiver at height.
    tag = np.array([50.0, 50.0, 1.5])
    steep = np.array([[0.0, 0.0, 35.0], [100.0, 0.0, 30.0],
                      [0.0, 100.0, 33.0], [100.0, 100.0, 38.0]])
    shallow = np.array([[0.0, 0.0, 6.0], [2000.0, 0.0, 6.5],
                        [0.0, 2000.0, 5.5], [2000.0, 2000.0, 7.0]])
    steep_vdop = dop_from_jacobian(range_jacobian(tag, steep)).vdop
    shallow_vdop = dop_from_jacobian(range_jacobian(tag, shallow)).vdop
    assert shallow_vdop > 10 * steep_vdop


def test_dop_refuses_to_report_a_number_for_rank_deficient_geometry():
    tag = np.array([50.0, 50.0, 1.5])
    collinear = np.array([[0.0, 0.0, 5.0], [10.0, 0.0, 5.0],
                          [20.0, 0.0, 5.0], [30.0, 0.0, 5.0]])
    with pytest.raises(ValueError):
        dop_from_jacobian(range_jacobian(tag, collinear))
