"""Monte Carlo scenario simulation over a 3D path.

Produces one :class:`FixResult` per (path sample, repeat). Every attempt is
kept, including timeouts and solver failures, because reliability analysis
needs them. Positions are solved natively in 3D by
``locbench3d.simulate.solver``.

The delivery/timeout model here is a Bernoulli trial per attempt driven by
a caller-supplied probability (typically from
``locbench3d.metrics.scalability`` or a configured packet-loss value); this
module does not invent its own traffic model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from locbench3d.core.evidence import EvidenceRecord
from locbench3d.core.geometry3d import error_3d, error_horizontal, error_vertical, true_ranges
from locbench3d.core.geometry_bounds import GeometryFailureReason, evaluate_geometry
from locbench3d.methods.tdoa import evaluate_tdoa_geometry
from locbench3d.paths.trajectories import Path3D
from locbench3d.protocol.traffic import RangingMethod
from locbench3d.simulate.solver import solve_position_3d, solve_position_tdoa_3d

ErrorSampler = Callable[[int], np.ndarray]


@dataclass(frozen=True)
class FixResult:
    scenario_id: str
    path_id: str
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
    error_3d_m: Optional[float]
    error_horizontal_m: Optional[float]
    error_vertical_m: Optional[float]
    geometry_valid: bool
    geometry_failure_reason: Optional[GeometryFailureReason]
    jacobian_rank: int
    condition_number: Optional[float]
    evidence: EvidenceRecord

    def to_dict(self) -> dict:
        d = {
            "scenario_id": self.scenario_id,
            "path_id": self.path_id,
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
            "error_3d_m": self.error_3d_m,
            "error_horizontal_m": self.error_horizontal_m,
            "error_vertical_m": self.error_vertical_m,
            "geometry_valid": self.geometry_valid,
            "geometry_failure_reason": (
                self.geometry_failure_reason.value
                if self.geometry_failure_reason
                else None
            ),
            "jacobian_rank": self.jacobian_rank,
            "condition_number": self.condition_number,
        }
        d.update(self.evidence.to_dict())
        return d


def simulate_path_fixes(
    scenario_id: str,
    method: RangingMethod,
    anchors: np.ndarray,
    path: Path3D,
    error_sampler: ErrorSampler,
    evidence: EvidenceRecord,
    n_repeats: int = 1,
    seed: int = 0,
    delivery_probability: float = 1.0,
    minimum_anchors: int = 4,
    sigma_for_geometry_check_m: float = 1.0,
    ref_index: int = 0,
) -> list[FixResult]:
    """Run a Monte Carlo simulation of range-based fixes over a 3D path.

    For each path sample and each repeat: draw per-anchor range noise from
    ``error_sampler``, apply it to the true ranges (or, for TDoA, to the
    ranges before differencing, so the differenced measurement noise
    naturally shares the reference anchor's noise term), decide delivery
    via a Bernoulli trial, and solve for position when delivered.
    """
    if not (0.0 <= delivery_probability <= 1.0):
        raise ValueError("delivery_probability must be in [0, 1]")
    anchors = np.asarray(anchors, dtype=float)
    rng = np.random.default_rng(seed)
    method = RangingMethod(method)
    results: list[FixResult] = []

    for idx in range(path.n_samples):
        true_p = np.array([path.x_m[idx], path.y_m[idx], path.z_m[idx]])

        if method == RangingMethod.TDOA:
            geom = evaluate_tdoa_geometry(
                true_p, anchors, sigma_range_m=sigma_for_geometry_check_m,
                minimum_anchors=minimum_anchors, ref_index=ref_index,
            )
        else:
            geom = evaluate_geometry(
                true_p, anchors, sigma_range_m=sigma_for_geometry_check_m,
                minimum_anchors=minimum_anchors,
            )

        for rep in range(n_repeats):
            delivered = rng.random() < delivery_probability
            base = dict(
                scenario_id=scenario_id,
                path_id=path.path_id,
                sample_index=idx,
                repeat_index=rep,
                t_s=float(path.t_s[idx]),
                true_x_m=float(true_p[0]),
                true_y_m=float(true_p[1]),
                true_z_m=float(true_p[2]),
                geometry_valid=geom.geometry_valid,
                geometry_failure_reason=geom.failure_reason,
                jacobian_rank=geom.jacobian_rank,
                condition_number=geom.condition_number,
                evidence=evidence,
            )
            if not delivered:
                results.append(
                    FixResult(
                        **base,
                        estimated_x=None,
                        estimated_y=None,
                        estimated_z=None,
                        success=False,
                        timeout=True,
                        error_3d_m=None,
                        error_horizontal_m=None,
                        error_vertical_m=None,
                    )
                )
                continue

            true_range_vec = true_ranges(true_p, anchors)
            errors = np.asarray(error_sampler(len(anchors)), dtype=float)
            measured_ranges = true_range_vec + errors

            if method == RangingMethod.TDOA:
                mask = np.ones(len(anchors), dtype=bool)
                mask[ref_index] = False
                measured_diffs = measured_ranges[mask] - measured_ranges[ref_index]
                estimate, solved, _ = solve_position_tdoa_3d(
                    anchors, measured_diffs, ref_index=ref_index
                )
            else:
                estimate, solved, _ = solve_position_3d(anchors, measured_ranges)

            if solved:
                results.append(
                    FixResult(
                        **base,
                        estimated_x=float(estimate[0]),
                        estimated_y=float(estimate[1]),
                        estimated_z=float(estimate[2]),
                        success=True,
                        timeout=False,
                        error_3d_m=error_3d(estimate, true_p),
                        error_horizontal_m=error_horizontal(estimate, true_p),
                        error_vertical_m=error_vertical(estimate, true_p),
                    )
                )
            else:
                results.append(
                    FixResult(
                        **base,
                        estimated_x=None,
                        estimated_y=None,
                        estimated_z=None,
                        success=False,
                        timeout=False,
                        error_3d_m=None,
                        error_horizontal_m=None,
                        error_vertical_m=None,
                    )
                )
    return results
