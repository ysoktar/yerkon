"""TDoA range-difference geometry.

TDoA measures differences of arrival time against a reference anchor,
which convert to range differences ``r_i - r_ref``, not absolute ranges.
Every non-reference measurement shares the reference anchor's noise term,
so the measurement covariance is not diagonal: it has variance
``2*sigma^2`` on the diagonal (own-anchor noise plus reference noise) and
``sigma^2`` on the off-diagonals (the shared reference term). This module
builds the TDoA-specific Jacobian and covariance and never falls back to
``core.geometry_bounds``'s absolute-range, independent-noise assumptions
for the actual TDoA Fisher information or CRLB. Only two general-purpose
primitives are reused from there: ``range_jacobian`` (per-anchor unit
vectors, a genuinely shared building block for both the absolute-range and
differenced case) and ``coplanar`` (a property of the anchor layout, not
of the measurement model).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from locbench3d.core.geometry_bounds import (
    CRLBResult,
    GeometryFailureReason,
    GeometryResult,
    coplanar,
    range_jacobian,
)

Vec3 = np.ndarray


def tdoa_range_differences(
    position: Vec3, anchors: np.ndarray, ref_index: int = 0
) -> np.ndarray:
    """Range differences r_i - r_ref for every anchor except the reference."""
    from locbench3d.core.geometry3d import true_ranges

    ranges = true_ranges(position, anchors)
    ref = ranges[ref_index]
    diffs = ranges - ref
    return np.delete(diffs, ref_index)


def tdoa_jacobian(
    position: Vec3, anchors: np.ndarray, ref_index: int = 0
) -> np.ndarray:
    """Jacobian of range-difference measurements: row i = u_i - u_ref.

    Each row is the difference of two absolute-range unit-vector gradients,
    which is the correct derivative of ``r_i - r_ref`` with respect to
    position. This is not the same object as the absolute-range Jacobian:
    it has one fewer row (no row for the reference anchor itself) and its
    rows are differences, not single unit vectors.
    """
    J_abs = range_jacobian(position, anchors)
    ref_row = J_abs[ref_index]
    mask = np.ones(len(anchors), dtype=bool)
    mask[ref_index] = False
    return J_abs[mask] - ref_row


def tdoa_measurement_covariance(
    n_anchors: int, sigma_range_m: float, ref_index: int = 0
) -> np.ndarray:
    """Shared-reference covariance for n_anchors-1 range-difference measurements.

    Assumes i.i.d. range noise of standard deviation ``sigma_range_m`` at
    every anchor including the reference. Diagonal = 2*sigma^2 (own noise
    plus reference noise); off-diagonal = sigma^2 (the shared reference
    term correlates every pair of differenced measurements).
    """
    if sigma_range_m <= 0:
        raise ValueError("sigma_range_m must be positive")
    m = n_anchors - 1
    if m < 1:
        raise ValueError("need at least 2 anchors to form 1 range difference")
    cov = np.full((m, m), sigma_range_m**2)
    np.fill_diagonal(cov, 2.0 * sigma_range_m**2)
    return cov


def tdoa_fisher_information(
    position: Vec3, anchors: np.ndarray, sigma_range_m: float, ref_index: int = 0
) -> np.ndarray:
    """Weighted Fisher information FIM = J^T Cov^-1 J for TDoA measurements."""
    J = tdoa_jacobian(position, anchors, ref_index)
    cov = tdoa_measurement_covariance(len(anchors), sigma_range_m, ref_index)
    cov_inv = np.linalg.inv(cov)
    return J.T @ cov_inv @ J


def tdoa_crlb(
    position: Vec3, anchors: np.ndarray, sigma_range_m: float, ref_index: int = 0
) -> CRLBResult:
    """Per-axis CRLB from TDoA (range-difference, shared-covariance) Fisher information."""
    fim = tdoa_fisher_information(position, anchors, sigma_range_m, ref_index)
    eps = 1e-9 * max(1.0, float(np.max(np.abs(fim))))
    rank = int(np.linalg.matrix_rank(fim, tol=1e-8))
    if rank == 3:
        cov = np.linalg.inv(fim)
        return CRLBResult(
            crlb_x_m=float(np.sqrt(cov[0, 0])),
            crlb_y_m=float(np.sqrt(cov[1, 1])),
            crlb_z_m=float(np.sqrt(cov[2, 2])),
        )
    diag = np.diag(fim)
    zero_axes = [i for i in range(3) if diag[i] < eps]
    observable_axes = [i for i in range(3) if i not in zero_axes]
    decoupled = all(
        abs(fim[i, j]) < eps for i in zero_axes for j in observable_axes
    )
    values: dict[int, Optional[float]] = {i: None for i in range(3)}
    if decoupled and observable_axes:
        sub = fim[np.ix_(observable_axes, observable_axes)]
        if np.linalg.matrix_rank(sub, tol=1e-8) == len(observable_axes):
            sub_cov = np.linalg.inv(sub)
            for idx, axis in enumerate(observable_axes):
                values[axis] = float(np.sqrt(sub_cov[idx, idx]))
    return CRLBResult(crlb_x_m=values[0], crlb_y_m=values[1], crlb_z_m=values[2])


def evaluate_tdoa_geometry(
    position: Vec3,
    anchors: np.ndarray,
    sigma_range_m: float = 1.0,
    minimum_anchors: int = 4,
    condition_number_threshold: float = 1.0e6,
    ref_index: int = 0,
) -> GeometryResult:
    """Classify a synchronized TDoA anchor layout for a given tag position.

    Minimum is 4 synchronized non-coplanar anchors plus tag, matching the
    requirements table; the Jacobian rank and condition number used here
    are the TDoA-specific (differenced) ones, not the absolute-range ones.
    """
    a = np.asarray(anchors, dtype=float)
    n = a.shape[0]

    if n < 3:
        return GeometryResult(
            jacobian_rank=0,
            geometry_valid=False,
            failure_reason=GeometryFailureReason.INSUFFICIENT_REFERENCES,
            redundant=False,
            reference_count=n,
            condition_number=None,
        )

    J = tdoa_jacobian(position, a, ref_index)
    rank = int(np.linalg.matrix_rank(J, tol=1e-8))
    cond = float(np.linalg.cond(J)) if J.shape[0] >= 3 else float("inf")

    if n < minimum_anchors:
        return GeometryResult(
            jacobian_rank=rank,
            geometry_valid=False,
            failure_reason=GeometryFailureReason.INSUFFICIENT_REFERENCES,
            redundant=False,
            reference_count=n,
            condition_number=cond,
        )

    if coplanar(a):
        return GeometryResult(
            jacobian_rank=rank,
            geometry_valid=False,
            failure_reason=GeometryFailureReason.COPLANAR_WEAK_VERTICAL,
            redundant=False,
            reference_count=n,
            condition_number=cond,
        )

    if rank < 3:
        return GeometryResult(
            jacobian_rank=rank,
            geometry_valid=False,
            failure_reason=GeometryFailureReason.RANK_DEFICIENT,
            redundant=False,
            reference_count=n,
            condition_number=cond,
        )

    if cond > condition_number_threshold:
        return GeometryResult(
            jacobian_rank=rank,
            geometry_valid=False,
            failure_reason=GeometryFailureReason.ILL_CONDITIONED,
            redundant=False,
            reference_count=n,
            condition_number=cond,
        )

    return GeometryResult(
        jacobian_rank=rank,
        geometry_valid=True,
        failure_reason=None,
        redundant=n > minimum_anchors,
        reference_count=n,
        condition_number=cond,
    )
