"""3D geometry validity, Jacobian/Fisher-information rank, CRLB, and DOP.

This module distinguishes three separate questions that the requirements
call out explicitly:

1. Is the problem mathematically solvable (enough independent equations)?
2. Is the geometry non-degenerate (not four coplanar anchors giving weak
   vertical observability)?
3. Is the geometry good enough to *recommend* for benchmarking (redundant,
   well-conditioned)?

A sufficient anchor count alone answers only the first question. This module
answers all three and keeps a concrete failure reason attached to the
result, rather than collapsing everything to a single pass/fail flag.

Scope note: everything here is range-based (TWR / ToA / RSSI trilateration)
geometry, using absolute ranges. TDoA uses range differences and a
different covariance structure; see ``locbench3d.methods.tdoa`` for the
TDoA-specific geometry, which does not reuse this module's Jacobian.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

Vec3 = np.ndarray


class GeometryFailureReason(str, Enum):
    INSUFFICIENT_REFERENCES = "INSUFFICIENT_REFERENCES"
    COPLANAR_WEAK_VERTICAL = "COPLANAR_WEAK_VERTICAL"
    RANK_DEFICIENT = "RANK_DEFICIENT"
    ILL_CONDITIONED = "ILL_CONDITIONED"
    OUTSIDE_REFERENCE_HULL = "OUTSIDE_REFERENCE_HULL"


@dataclass(frozen=True)
class GeometryResult:
    jacobian_rank: int
    geometry_valid: bool
    failure_reason: Optional[GeometryFailureReason]
    redundant: bool
    reference_count: int
    condition_number: Optional[float]
    hull_contains_tag: Optional[bool] = None


@dataclass(frozen=True)
class CRLBResult:
    """Cramer-Rao lower bound on position standard deviation, per axis.

    A value of ``None`` means that axis is not observable from the given
    geometry at the given noise level, not that its bound is zero.
    """

    crlb_x_m: Optional[float]
    crlb_y_m: Optional[float]
    crlb_z_m: Optional[float]

    @property
    def crlb_horizontal_m(self) -> Optional[float]:
        if self.crlb_x_m is None or self.crlb_y_m is None:
            return None
        return float(np.hypot(self.crlb_x_m, self.crlb_y_m))

    @property
    def crlb_3d_rms_m(self) -> Optional[float]:
        if None in (self.crlb_x_m, self.crlb_y_m, self.crlb_z_m):
            return None
        return float(
            np.sqrt(self.crlb_x_m**2 + self.crlb_y_m**2 + self.crlb_z_m**2)
        )


@dataclass(frozen=True)
class DOPResult:
    hdop: float
    vdop: float
    pdop: float
    gdop: Optional[float] = None  # only meaningful when a clock term is included


def range_jacobian(position: Vec3, anchors: np.ndarray) -> np.ndarray:
    """Jacobian of range wrt position: row i = unit vector from anchor i to p.

    d r_i / d p = (p - a_i) / r_i
    """
    p = np.asarray(position, dtype=float)
    a = np.asarray(anchors, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3:
        raise ValueError("anchors must be an (N, 3) array")
    diffs = p[None, :] - a
    ranges = np.linalg.norm(diffs, axis=1)
    if np.any(ranges < 1e-9):
        raise ValueError("position coincides with an anchor; range undefined")
    return diffs / ranges[:, None]


def fisher_information(jacobian: np.ndarray, sigma_range_m: float) -> np.ndarray:
    """FIM = J^T J / sigma^2 for i.i.d. Gaussian range noise of given sigma."""
    if sigma_range_m <= 0:
        raise ValueError("sigma_range_m must be positive")
    return (jacobian.T @ jacobian) / (sigma_range_m**2)


def condition_number(jacobian: np.ndarray) -> float:
    return float(np.linalg.cond(jacobian))


def coplanar(anchors: np.ndarray, atol: float = 1e-6) -> bool:
    """True if all anchor points lie in a common plane (or line/point).

    Fewer than 4 points are trivially coplanar.
    """
    a = np.asarray(anchors, dtype=float)
    if a.shape[0] < 4:
        return True
    centered = a - a.mean(axis=0)
    # Singular values of the centered point matrix; a true 3D spread needs
    # 3 non-negligible singular values.
    s = np.linalg.svd(centered, compute_uv=False)
    scale = max(s[0], 1.0)
    return bool(s[2] < atol * scale)


def convex_hull_contains(point: Vec3, anchors: np.ndarray) -> bool:
    """True if point lies inside the convex hull of a non-coplanar anchor set.

    Returns False (rather than raising) for a degenerate (coplanar) anchor
    set, since a 3D hull cannot be formed from it.
    """
    from scipy.spatial import Delaunay

    p = np.asarray(point, dtype=float)
    a = np.asarray(anchors, dtype=float)
    if coplanar(a):
        return False
    try:
        hull = Delaunay(a)
    except Exception:
        return False
    return bool(hull.find_simplex(p) >= 0)


def range_crlb(
    position: Vec3, anchors: np.ndarray, sigma_range_m: float
) -> CRLBResult:
    """Per-axis CRLB standard deviation from range-only Fisher information.

    When the full 3x3 FIM is singular, an axis is only reported (not
    ``None``) if it is decoupled from the deficient axes, i.e. its row and
    column of the FIM show no cross-coupling with the unobservable
    direction(s). This avoids inventing an axis-aligned bound for a
    deficiency that is not actually axis-aligned.
    """
    J = range_jacobian(position, anchors)
    fim = fisher_information(J, sigma_range_m)
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
    return CRLBResult(
        crlb_x_m=values[0], crlb_y_m=values[1], crlb_z_m=values[2]
    )


def dop_from_jacobian(jacobian: np.ndarray) -> DOPResult:
    """HDOP/VDOP/PDOP from a unit-weighted (sigma=1) range Jacobian.

    This is the DOP analogue used for local range-based geometry, following
    the same normal-equations structure as GNSS DOP. GDOP additionally
    requires a clock-bias column and is left ``None`` unless one is
    supplied by the caller's own Jacobian (methods with a shared clock
    unknown should augment the Jacobian with a fourth column before calling
    this function, and pass gdop separately).
    """
    fim = jacobian.T @ jacobian
    rank = int(np.linalg.matrix_rank(fim, tol=1e-8))
    if rank < 3:
        raise ValueError(
            "DOP requires full-rank 3D geometry; check geometry_valid first"
        )
    q = np.linalg.inv(fim)
    hdop = float(np.sqrt(q[0, 0] + q[1, 1]))
    vdop = float(np.sqrt(q[2, 2]))
    pdop = float(np.sqrt(hdop**2 + vdop**2))
    return DOPResult(hdop=hdop, vdop=vdop, pdop=pdop)


def evaluate_geometry(
    position: Vec3,
    anchors: np.ndarray,
    sigma_range_m: float = 1.0,
    minimum_anchors: int = 4,
    condition_number_threshold: float = 1.0e6,
) -> GeometryResult:
    """Classify a range-based anchor layout for a given tag position.

    Distinguishes mathematically-insufficient, coplanar-degenerate,
    rank-deficient, ill-conditioned, and geometry-valid/redundant cases.
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

    J = range_jacobian(position, a)
    rank = int(np.linalg.matrix_rank(J, tol=1e-8))
    cond = condition_number(J)

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

    hull_ok = convex_hull_contains(position, a)
    return GeometryResult(
        jacobian_rank=rank,
        geometry_valid=True,
        failure_reason=None,
        redundant=n > minimum_anchors,
        reference_count=n,
        condition_number=cond,
        hull_contains_tag=hull_ok,
    )
