"""Monte Carlo fix simulation over a 3D path, with link-range gating.

One :class:`FixResult` is produced per (path sample, repeat), and failed
attempts are kept rather than dropped: the availability column of the
comparison table is the fraction of attempts that produced a usable fix,
so discarding failures would quietly turn a coverage hole into a perfect
score.

Link-range gating is the part that makes large coverage areas meaningful.
Only anchors within ``max_range_m`` of the receiver take part in a fix. A
node 40 km down a tunnel cannot be heard, and letting it contribute would
manufacture geometry that no real deployment has. Where fewer than
``minimum_anchors`` are in range, the attempt fails as a coverage hole.

Where enough anchors are in range, the fix is solved even if the geometry
is poor. That is deliberate. A receiver surrounded by nearly coplanar
anchors does return a position, and it is a bad one; refusing to solve
would move that error out of the accuracy columns and into the
availability column, hiding exactly the vertical weakness this study is
about.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import numpy as np
from scipy.optimize import least_squares

from yerkon.evidence import EvidenceRecord
from yerkon.geometry import (
    GeometryFailureReason,
    error_3d,
    error_horizontal,
    error_vertical,
    evaluate_geometry,
    true_ranges,
)
from yerkon.path import Path3D

ErrorSampler = Callable[[int], np.ndarray]


class RangingMethod(str, Enum):
    """Two-way ranging variants.

    YERKON specifies two-way ranging rather than TDoA precisely so that the
    network needs no common clock, so no TDoA path exists in this project.
    """

    SS_TWR = "SS_TWR"
    DS_TWR = "DS_TWR"


def solve_position_3d(
    anchors: np.ndarray,
    ranges: np.ndarray,
    initial_guess: np.ndarray | None = None,
) -> tuple[np.ndarray, bool]:
    """Estimate [x, y, z] jointly from absolute ranges.

    All three axes are solved in one nonlinear least-squares system. The
    height is never a second pass over a 2D solution. ``estimate`` is only
    meaningful when the returned success flag is True.
    """
    anchors = np.asarray(anchors, dtype=float)
    ranges = np.asarray(ranges, dtype=float)
    if anchors.shape[0] != ranges.shape[0]:
        raise ValueError("anchors and ranges must have the same length")
    if initial_guess is None:
        # Start from the centroid of the anchors that are actually in range,
        # nudged off it so the first Jacobian is not degenerate at a
        # symmetry point.
        initial_guess = anchors.mean(axis=0) + np.array([0.1, 0.1, 1.0])

    def residuals(p):
        return np.linalg.norm(anchors - p[None, :], axis=1) - ranges

    result = least_squares(residuals, initial_guess, method="lm", max_nfev=2000)
    return result.x, bool(result.success)


@dataclass(frozen=True)
class FixResult:
    scenario_id: str
    sample_index: int
    repeat_index: int
    t_s: float
    true_x_m: float
    true_y_m: float
    true_z_m: float
    estimated_x: Optional[float]
    estimated_y: Optional[float]
    estimated_z: Optional[float]
    success: bool
    timeout: bool
    out_of_coverage: bool
    anchors_in_range: int
    error_3d_m: Optional[float]
    error_horizontal_m: Optional[float]
    error_vertical_m: Optional[float]
    geometry_valid: bool
    geometry_failure_reason: Optional[GeometryFailureReason]
    condition_number: Optional[float]
    evidence: EvidenceRecord

    def to_dict(self) -> dict:
        d = {
            "scenario_id": self.scenario_id,
            "sample_index": self.sample_index,
            "repeat_index": self.repeat_index,
            "t_s": self.t_s,
            "true_x_m": self.true_x_m,
            "true_y_m": self.true_y_m,
            "true_z_m": self.true_z_m,
            "estimated_x": self.estimated_x,
            "estimated_y": self.estimated_y,
            "estimated_z": self.estimated_z,
            "success": self.success,
            "timeout": self.timeout,
            "out_of_coverage": self.out_of_coverage,
            "anchors_in_range": self.anchors_in_range,
            "error_3d_m": self.error_3d_m,
            "error_horizontal_m": self.error_horizontal_m,
            "error_vertical_m": self.error_vertical_m,
            "geometry_valid": self.geometry_valid,
            "geometry_failure_reason": (
                self.geometry_failure_reason.value
                if self.geometry_failure_reason
                else None
            ),
            "condition_number": self.condition_number,
        }
        d.update(self.evidence.to_dict())
        return d


def select_anchors(
    position: np.ndarray,
    anchors: np.ndarray,
    max_range_m: Optional[float],
    max_anchors: Optional[int] = None,
) -> np.ndarray:
    """The anchors a receiver actually ranges to, nearest first.

    Two filters, in order. Link range decides what can be heard at all.
    Then, because two-way ranging spends airtime on every anchor it talks
    to, a receiver ranges to a working subset rather than to everything
    audible; the report describes the receiver as talking to "enough"
    broadcast units, not to all of them.

    Taking the nearest ones costs a little geometry (fewer measurements to
    average) and buys a lot of evidence: the near links are the ones inside
    the range envelope the SX1280 error data actually covers.
    """
    mask = anchors_in_range(position, anchors, max_range_m)
    visible = anchors[mask]
    if max_anchors is None or len(visible) <= max_anchors:
        return visible
    distances = true_ranges(np.asarray(position, dtype=float), visible)
    return visible[np.argsort(distances)[:max_anchors]]


def anchors_in_range(
    position: np.ndarray, anchors: np.ndarray, max_range_m: Optional[float]
) -> np.ndarray:
    """Boolean mask of anchors within ``max_range_m`` of ``position``.

    ``None`` means no link-budget limit, in which case every anchor is
    reachable. That is only appropriate for areas small enough that it is
    true.
    """
    if max_range_m is None:
        return np.ones(len(anchors), dtype=bool)
    if max_range_m <= 0:
        raise ValueError("max_range_m must be positive")
    return true_ranges(np.asarray(position, dtype=float), anchors) <= max_range_m


def simulate_path_fixes(
    scenario_id: str,
    anchors: np.ndarray,
    path: Path3D,
    error_sampler: ErrorSampler,
    evidence: EvidenceRecord,
    method: RangingMethod = RangingMethod.DS_TWR,
    n_repeats: int = 1,
    seed: int = 0,
    delivery_probability: float = 1.0,
    minimum_anchors: int = 4,
    max_range_m: Optional[float] = None,
    max_anchors_per_fix: Optional[int] = None,
    sigma_for_geometry_check_m: float = 1.0,
) -> list[FixResult]:
    """Simulate repeated position fixes along a path.

    For each path sample: find the anchors within link range, judge the
    geometry they form, then for each repeat draw per-anchor range noise,
    decide delivery with a Bernoulli trial, and solve.
    """
    if not 0.0 <= delivery_probability <= 1.0:
        raise ValueError("delivery_probability must be in [0, 1]")
    if minimum_anchors < 4:
        raise ValueError(
            "a 3D fix from absolute ranges needs at least 4 anchors"
        )
    anchors = np.asarray(anchors, dtype=float)
    if anchors.ndim != 2 or anchors.shape[1] != 3:
        raise ValueError("anchors must be an (N, 3) array")
    RangingMethod(method)
    rng = np.random.default_rng(seed)
    results: list[FixResult] = []

    for idx in range(path.n_samples):
        true_p = np.array([path.x_m[idx], path.y_m[idx], path.z_m[idx]])
        visible = select_anchors(
            true_p, anchors, max_range_m, max_anchors_per_fix
        )
        n_visible = int(len(visible))
        solvable = n_visible >= minimum_anchors

        geom = evaluate_geometry(
            true_p,
            visible,
            sigma_range_m=sigma_for_geometry_check_m,
            minimum_anchors=minimum_anchors,
        )

        for rep in range(n_repeats):
            base = dict(
                scenario_id=scenario_id,
                sample_index=idx,
                repeat_index=rep,
                t_s=float(path.t_s[idx]),
                true_x_m=float(true_p[0]),
                true_y_m=float(true_p[1]),
                true_z_m=float(true_p[2]),
                anchors_in_range=n_visible,
                geometry_valid=geom.geometry_valid,
                geometry_failure_reason=geom.failure_reason,
                condition_number=geom.condition_number,
                evidence=evidence,
            )
            failed = dict(
                estimated_x=None,
                estimated_y=None,
                estimated_z=None,
                success=False,
                error_3d_m=None,
                error_horizontal_m=None,
                error_vertical_m=None,
            )

            if not solvable:
                results.append(
                    FixResult(**base, **failed, timeout=False, out_of_coverage=True)
                )
                continue

            if rng.random() >= delivery_probability:
                results.append(
                    FixResult(**base, **failed, timeout=True, out_of_coverage=False)
                )
                continue

            measured = true_ranges(true_p, visible) + np.asarray(
                error_sampler(n_visible), dtype=float
            )
            estimate, solved = solve_position_3d(visible, measured)

            if not solved:
                results.append(
                    FixResult(**base, **failed, timeout=False, out_of_coverage=False)
                )
                continue

            results.append(
                FixResult(
                    **base,
                    timeout=False,
                    out_of_coverage=False,
                    estimated_x=float(estimate[0]),
                    estimated_y=float(estimate[1]),
                    estimated_z=float(estimate[2]),
                    success=True,
                    error_3d_m=error_3d(estimate, true_p),
                    error_horizontal_m=error_horizontal(estimate, true_p),
                    error_vertical_m=error_vertical(estimate, true_p),
                )
            )
    return results
