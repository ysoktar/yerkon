"""Native 3D nonlinear least-squares position solvers.

Both solvers estimate x, y, and z jointly in one nonlinear system. Neither
solves a 2D problem first and refines height afterward.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares


def _default_initial_guess(anchors: np.ndarray) -> np.ndarray:
    centroid = anchors.mean(axis=0)
    # Nudge off the anchor centroid so the Jacobian is not degenerate at the
    # very first iteration when the centroid happens to coincide with an
    # anchor or a symmetry point.
    return centroid + np.array([0.1, 0.1, 1.0])


def solve_position_3d(
    anchors: np.ndarray,
    ranges: np.ndarray,
    initial_guess: np.ndarray | None = None,
) -> tuple[np.ndarray, bool, float]:
    """Estimate [x, y, z] from absolute ranges to each anchor (TWR/ToA/ToF/RSSI style).

    Returns (estimate, success, final_cost). ``estimate`` is only meaningful
    when ``success`` is True; callers must not use it otherwise.
    """
    anchors = np.asarray(anchors, dtype=float)
    ranges = np.asarray(ranges, dtype=float)
    if anchors.shape[0] != ranges.shape[0]:
        raise ValueError("anchors and ranges must have the same length")
    x0 = initial_guess if initial_guess is not None else _default_initial_guess(anchors)

    def residuals(p):
        return np.linalg.norm(anchors - p[None, :], axis=1) - ranges

    result = least_squares(residuals, x0, method="lm", max_nfev=2000)
    return result.x, bool(result.success), float(result.cost)


def solve_position_tdoa_3d(
    anchors: np.ndarray,
    range_differences: np.ndarray,
    ref_index: int = 0,
    initial_guess: np.ndarray | None = None,
) -> tuple[np.ndarray, bool, float]:
    """Estimate [x, y, z] from TDoA range differences against a reference anchor."""
    anchors = np.asarray(anchors, dtype=float)
    range_differences = np.asarray(range_differences, dtype=float)
    if anchors.shape[0] - 1 != range_differences.shape[0]:
        raise ValueError("range_differences must have len(anchors) - 1 entries")
    x0 = initial_guess if initial_guess is not None else _default_initial_guess(anchors)
    mask = np.ones(anchors.shape[0], dtype=bool)
    mask[ref_index] = False

    def residuals(p):
        ranges = np.linalg.norm(anchors - p[None, :], axis=1)
        diffs = ranges[mask] - ranges[ref_index]
        return diffs - range_differences

    result = least_squares(residuals, x0, method="lm", max_nfev=2000)
    return result.x, bool(result.success), float(result.cost)
