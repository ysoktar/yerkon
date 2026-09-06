"""Range comparison table: one row per scenario and non-empty distance bin.

"Range" here is the true distance from a reference point (by default the
origin) to the true fix position; for a pairwise-ranging scenario this is
the anchor-tag range directly. Bins with no attempts are never emitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from locbench3d.core.evidence import EvidenceRecord
from locbench3d.simulate.monte_carlo import FixResult


@dataclass(frozen=True)
class RangeComparisonRow:
    scenario_id: str
    method: str
    hardware_profile: str
    environment: str
    range_bin_lower_m: float
    range_bin_upper_m: float
    attempted_fixes: int
    valid_fixes: int
    measurement_bias_m: Optional[float]
    measurement_rmse_m: Optional[float]
    horizontal_rmse_m: Optional[float]
    vertical_rmse_m: Optional[float]
    error_3d_rmse_m: Optional[float]
    p50_m: Optional[float]
    p90_m: Optional[float]
    p95_m: Optional[float]
    p99_m: Optional[float]
    availability: float
    dropout_rate: float
    los_fraction: Optional[float]
    nlos_fraction: Optional[float]
    evidence: EvidenceRecord


def build_range_comparison_rows(
    scenario_id: str,
    method: str,
    hardware_profile: str,
    environment: str,
    fixes: list[FixResult],
    bin_edges_m: list[float],
    evidence: EvidenceRecord,
    reference_point: tuple[float, float, float] = (0.0, 0.0, 0.0),
    los_flags: Optional[list[bool]] = None,
) -> list[RangeComparisonRow]:
    if len(bin_edges_m) < 2:
        raise ValueError("bin_edges_m needs at least two edges to form one bin")
    ref = np.array(reference_point)
    ranges = np.array(
        [np.linalg.norm(np.array([f.true_x_m, f.true_y_m, f.true_z_m]) - ref) for f in fixes]
    )

    rows: list[RangeComparisonRow] = []
    for lower, upper in zip(bin_edges_m[:-1], bin_edges_m[1:]):
        mask = (ranges >= lower) & (ranges < upper)
        bin_fixes = [f for f, keep in zip(fixes, mask) if keep]
        if not bin_fixes:
            continue

        attempted = len(bin_fixes)
        valid = [f for f in bin_fixes if f.success]
        dropouts = sum(1 for f in bin_fixes if f.timeout)

        bias = rmse = h_rmse = v_rmse = e3d_rmse = None
        p50 = p90 = p95 = p99 = None
        if valid:
            range_errors = np.array([f.estimated_x - f.true_x_m for f in valid])
            bias = float(np.mean(range_errors))
            rmse = float(np.sqrt(np.mean(range_errors**2)))
            h = np.array([f.error_horizontal_m for f in valid])
            v = np.array([f.error_vertical_m for f in valid])
            e3 = np.array([f.error_3d_m for f in valid])
            h_rmse = float(np.sqrt(np.mean(h**2)))
            v_rmse = float(np.sqrt(np.mean(v**2)))
            e3d_rmse = float(np.sqrt(np.mean(e3**2)))
            p50, p90, p95, p99 = (float(np.percentile(e3, q)) for q in (50, 90, 95, 99))

        los_fraction = nlos_fraction = None
        if los_flags is not None:
            bin_los = [is_los for f, is_los, keep in zip(fixes, los_flags, mask) if keep]
            if bin_los:
                los_fraction = sum(bin_los) / len(bin_los)
                nlos_fraction = 1.0 - los_fraction

        rows.append(
            RangeComparisonRow(
                scenario_id=scenario_id,
                method=method,
                hardware_profile=hardware_profile,
                environment=environment,
                range_bin_lower_m=lower,
                range_bin_upper_m=upper,
                attempted_fixes=attempted,
                valid_fixes=len(valid),
                measurement_bias_m=bias,
                measurement_rmse_m=rmse,
                horizontal_rmse_m=h_rmse,
                vertical_rmse_m=v_rmse,
                error_3d_rmse_m=e3d_rmse,
                p50_m=p50,
                p90_m=p90,
                p95_m=p95,
                p99_m=p99,
                availability=len(valid) / attempted,
                dropout_rate=dropouts / attempted,
                los_fraction=los_fraction,
                nlos_fraction=nlos_fraction,
                evidence=evidence,
            )
        )
    return rows
