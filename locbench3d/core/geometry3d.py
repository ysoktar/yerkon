"""Native 3D position, range, and error model.

All positions are 3-vectors ``[x, y, z]``. Nothing here solves a 2D problem
and adds height afterward: the true range is the full 3D Euclidean distance,
and every solver in ``locbench3d.simulate.solver`` estimates x, y and z
together in one nonlinear system.

Horizontal and vertical errors are reported as separate, first-class views
of the same 3D estimate, not as a substitute for the 3D error.
"""
from __future__ import annotations

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
