"""3D range geometry: true ranges, error decomposition, and geometry quality.

Two questions are answered separately here, because a comparison table that
merges them hides the reason a scenario performs badly:

1. Can this anchor layout observe all three axes at all (rank, coplanarity)?
2. How well does it observe each axis (condition number, HDOP/VDOP)?

VDOP is the number that explains YERKON's vertical results. A roadside or
tunnel layout puts every anchor at a shallow elevation angle from the tag,
which leaves the vertical axis weakly observed even when the horizontal
axes are well observed. See docs/METHOD.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

Vec3 = np.ndarray


def true_range(position: Vec3, anchor: Vec3) -> float:
    """3D Euclidean distance between a position and a reference node.

    r_i = sqrt((x-x_i)^2 + (y-y_i)^2 + (z-z_i)^2)
    """
    p = np.asarray(position, dtype=float)
    a = np.asarray(anchor, dtype=float)
    if p.shape != (3,) or a.shape != (3,):
        raise ValueError("true_range requires 3-vectors [x, y, z]")
    return float(np.linalg.norm(p - a))


def true_ranges(position: Vec3, anchors: np.ndarray) -> np.ndarray:
    """True range from one position to each row of an (N, 3) anchor array."""
    p = np.asarray(position, dtype=float)
    a = np.asarray(anchors, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3:
        raise ValueError("anchors must be an (N, 3) array")
    return np.linalg.norm(a - p[None, :], axis=1)


def error_3d(estimate: Vec3, truth: Vec3) -> float:
    """Full 3D position error.

    e_3D = sqrt((x_hat-x)^2 + (y_hat-y)^2 + (z_hat-z)^2)
    """
    est = np.asarray(estimate, dtype=float)
    tru = np.asarray(truth, dtype=float)
    if est.shape != (3,) or tru.shape != (3,):
        raise ValueError("error_3d requires 3-vectors [x, y, z]")
    return float(np.linalg.norm(est - tru))


def error_horizontal(estimate: Vec3, truth: Vec3) -> float:
    """Horizontal (x, y only) position error.

    e_H = sqrt((x_hat-x)^2 + (y_hat-y)^2)
    """
    est = np.asarray(estimate, dtype=float)
    tru = np.asarray(truth, dtype=float)
    return float(np.linalg.norm(est[:2] - tru[:2]))


def error_vertical(estimate: Vec3, truth: Vec3) -> float:
    """Vertical position error, absolute value.

    e_V = |z_hat - z|
    """
    est = np.asarray(estimate, dtype=float)
    tru = np.asarray(truth, dtype=float)
    return float(abs(est[2] - tru[2]))


def error_vector(estimate: Vec3, truth: Vec3) -> tuple[float, float, float]:
    """Signed per-axis error (x_hat - x, y_hat - y, z_hat - z), for bias metrics."""
    est = np.asarray(estimate, dtype=float)
    tru = np.asarray(truth, dtype=float)
    d = est - tru
    return float(d[0]), float(d[1]), float(d[2])


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
