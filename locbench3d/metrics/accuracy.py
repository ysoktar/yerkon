"""Axis, horizontal, vertical, and full-3D accuracy metrics.

Computed only over fixes with ``success is True``. A scenario with zero
successful fixes returns ``None`` for every metric here, never a
fabricated ``0``, since a zero would be indistinguishable from "perfect
accuracy".

CEP50/CEP95 and SEP50/SEP95 are computed as empirical percentiles of the
observed horizontal/3D radial error (this project has per-fix error
samples, so the direct percentile is used rather than the Gaussian-sigma
approximation formulas sometimes used when only summary statistics are
available).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from locbench3d.simulate.monte_carlo import FixResult


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
