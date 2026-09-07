"""Accuracy, reliability, and cost metrics over a set of simulated fixes.

Accuracy metrics are computed only over fixes that actually succeeded.
A scenario with no successful fix reports ``None``, never ``0``: a zero
would be indistinguishable from a perfect result. Reliability rates are
computed over every attempt, including the ones that failed, because the
availability column of the comparison table is exactly the fraction of
attempts that produced a usable fix.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from yerkon.simulate import FixResult


@dataclass(frozen=True)
class AccuracyResult:
    n_success: int
    x_bias_m: Optional[float]
    y_bias_m: Optional[float]
    z_bias_m: Optional[float]
    x_mae_m: Optional[float]
    y_mae_m: Optional[float]
    z_mae_m: Optional[float]
    x_rmse_m: Optional[float]
    y_rmse_m: Optional[float]
    z_rmse_m: Optional[float]
    x_std_m: Optional[float]
    y_std_m: Optional[float]
    z_std_m: Optional[float]

    horizontal_mae_m: Optional[float]
    horizontal_rmse_m: Optional[float]
    horizontal_p50_m: Optional[float]
    horizontal_p68_m: Optional[float]
    horizontal_p90_m: Optional[float]
    horizontal_p95_m: Optional[float]
    horizontal_p99_m: Optional[float]
    horizontal_max_m: Optional[float]
    cep50_m: Optional[float]
    cep95_m: Optional[float]

    vertical_mae_m: Optional[float]
    vertical_rmse_m: Optional[float]
    vertical_p50_m: Optional[float]
    vertical_p68_m: Optional[float]
    vertical_p90_m: Optional[float]
    vertical_p95_m: Optional[float]
    vertical_p99_m: Optional[float]
    vertical_max_m: Optional[float]

    error_3d_mae_m: Optional[float]
    error_3d_rmse_m: Optional[float]
    error_3d_std_m: Optional[float]
    error_3d_p50_m: Optional[float]
    error_3d_p68_m: Optional[float]
    error_3d_p75_m: Optional[float]
    error_3d_p90_m: Optional[float]
    error_3d_p95_m: Optional[float]
    error_3d_p99_m: Optional[float]
    error_3d_max_m: Optional[float]
    sep50_m: Optional[float]
    sep95_m: Optional[float]
    error_ellipsoid_volume_m3: Optional[float]


def _pct(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q))


def compute_accuracy_metrics(fixes: list[FixResult]) -> AccuracyResult:
    successes = [f for f in fixes if f.success]
    n = len(successes)
    if n == 0:
        none_fields = {
            f: None for f in AccuracyResult.__dataclass_fields__ if f != "n_success"
        }
        return AccuracyResult(n_success=0, **none_fields)

    dx = np.array([f.estimated_x - f.true_x_m for f in successes])
    dy = np.array([f.estimated_y - f.true_y_m for f in successes])
    dz = np.array([f.estimated_z - f.true_z_m for f in successes])
    eh = np.array([f.error_horizontal_m for f in successes])
    ev = np.array([f.error_vertical_m for f in successes])
    e3 = np.array([f.error_3d_m for f in successes])

    ellipsoid_volume: Optional[float] = None
    if n >= 4:
        cov = np.cov(np.column_stack([dx, dy, dz]), rowvar=False)
        eigvals = np.linalg.eigvalsh(cov)
        eigvals = np.clip(eigvals, a_min=0.0, a_max=None)
        axes = np.sqrt(eigvals)
        if np.all(axes > 0):
            ellipsoid_volume = float((4.0 / 3.0) * np.pi * np.prod(axes))

    return AccuracyResult(
        n_success=n,
        x_bias_m=float(np.mean(dx)),
        y_bias_m=float(np.mean(dy)),
        z_bias_m=float(np.mean(dz)),
        x_mae_m=float(np.mean(np.abs(dx))),
        y_mae_m=float(np.mean(np.abs(dy))),
        z_mae_m=float(np.mean(np.abs(dz))),
        x_rmse_m=float(np.sqrt(np.mean(dx**2))),
        y_rmse_m=float(np.sqrt(np.mean(dy**2))),
        z_rmse_m=float(np.sqrt(np.mean(dz**2))),
        x_std_m=float(np.std(dx)),
        y_std_m=float(np.std(dy)),
        z_std_m=float(np.std(dz)),
        horizontal_mae_m=float(np.mean(eh)),
        horizontal_rmse_m=float(np.sqrt(np.mean(eh**2))),
        horizontal_p50_m=_pct(eh, 50),
        horizontal_p68_m=_pct(eh, 68),
        horizontal_p90_m=_pct(eh, 90),
        horizontal_p95_m=_pct(eh, 95),
        horizontal_p99_m=_pct(eh, 99),
        horizontal_max_m=float(np.max(eh)),
        cep50_m=_pct(eh, 50),
        cep95_m=_pct(eh, 95),
        vertical_mae_m=float(np.mean(ev)),
        vertical_rmse_m=float(np.sqrt(np.mean(ev**2))),
        vertical_p50_m=_pct(ev, 50),
        vertical_p68_m=_pct(ev, 68),
        vertical_p90_m=_pct(ev, 90),
        vertical_p95_m=_pct(ev, 95),
        vertical_p99_m=_pct(ev, 99),
        vertical_max_m=float(np.max(ev)),
        error_3d_mae_m=float(np.mean(e3)),
        error_3d_rmse_m=float(np.sqrt(np.mean(e3**2))),
        error_3d_std_m=float(np.std(e3)),
        error_3d_p50_m=_pct(e3, 50),
        error_3d_p68_m=_pct(e3, 68),
        error_3d_p75_m=_pct(e3, 75),
        error_3d_p90_m=_pct(e3, 90),
        error_3d_p95_m=_pct(e3, 95),
        error_3d_p99_m=_pct(e3, 99),
        error_3d_max_m=float(np.max(e3)),
        sep50_m=_pct(e3, 50),
        sep95_m=_pct(e3, 95),
        error_ellipsoid_volume_m3=ellipsoid_volume,
    )


@dataclass(frozen=True)
class ReliabilityResult:
    """Why attempts failed, not just how many.

    The three failure modes are kept apart because they call for different
    fixes: a coverage gap means more anchors or more range, a dropout means
    a link-layer problem, and a solver failure means the geometry defeated
    the estimator.
    """

    attempted_fixes: int
    valid_fixes: int
    invalid_fixes: int
    valid_fix_rate: Optional[float]
    coverage_gap_rate: Optional[float]
    dropout_rate: Optional[float]
    solver_failure_rate: Optional[float]
    longest_outage_fixes: Optional[int]
    availability_by_threshold: dict[float, float] = field(default_factory=dict)


def compute_reliability_metrics(
    fixes: list[FixResult],
    accuracy_thresholds_m: Optional[list[float]] = None,
) -> ReliabilityResult:
    """Rates over every attempt, including the ones that produced nothing."""
    n = len(fixes)
    if n == 0:
        return ReliabilityResult(
            attempted_fixes=0,
            valid_fixes=0,
            invalid_fixes=0,
            valid_fix_rate=None,
            coverage_gap_rate=None,
            dropout_rate=None,
            solver_failure_rate=None,
            longest_outage_fixes=None,
        )

    valid = [f for f in fixes if f.success]
    coverage_gaps = [f for f in fixes if f.out_of_coverage]
    dropouts = [f for f in fixes if f.timeout]
    solver_failures = [
        f for f in fixes
        if not f.success and not f.timeout and not f.out_of_coverage
    ]

    longest_outage = 0
    current = 0
    for f in fixes:
        if f.success:
            current = 0
        else:
            current += 1
            longest_outage = max(longest_outage, current)

    availability_by_threshold: dict[float, float] = {}
    for threshold in accuracy_thresholds_m or []:
        met = sum(
            1 for f in fixes
            if f.success and f.error_3d_m is not None and f.error_3d_m <= threshold
        )
        availability_by_threshold[threshold] = met / n

    return ReliabilityResult(
        attempted_fixes=n,
        valid_fixes=len(valid),
        invalid_fixes=n - len(valid),
        valid_fix_rate=len(valid) / n,
        coverage_gap_rate=len(coverage_gaps) / n,
        dropout_rate=len(dropouts) / n,
        solver_failure_rate=len(solver_failures) / n,
        longest_outage_fixes=longest_outage,
        availability_by_threshold=availability_by_threshold,
    )


@dataclass(frozen=True)
class CostBreakdown:
    device_cost: float = 0.0
    anchor_cost: float = 0.0
    antenna_cost: float = 0.0
    compute_cost: float = 0.0
    installation_cost: float = 0.0
    survey_cost: float = 0.0
    calibration_cost: float = 0.0
    correction_service_cost: float = 0.0
    annual_subscription: float = 0.0
    maintenance_cost: float = 0.0
    infrastructure_units: Optional[int] = None

    @property
    def capex(self) -> float:
        return (
            self.device_cost
            + self.anchor_cost
            + self.antenna_cost
            + self.compute_cost
            + self.installation_cost
            + self.survey_cost
            + self.calibration_cost
        )

    @property
    def opex_annual(self) -> float:
        return self.correction_service_cost + self.annual_subscription + self.maintenance_cost

    @property
    def total_infrastructure_cost(self) -> float:
        """CAPEX only; recurring OPEX is reported separately, not folded in."""
        return self.capex


def cost_per_area(breakdown: CostBreakdown, floor_area_m2: float) -> float:
    if floor_area_m2 <= 0:
        raise ValueError("floor_area_m2 must be positive")
    return breakdown.total_infrastructure_cost / floor_area_m2

