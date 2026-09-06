"""Reliability metrics: counts, rates, outages, and threshold availability.

Every rate is computed over ``attempted_fixes`` (which includes timeouts
and solver failures), and every field is ``None`` rather than a fabricated
``0`` when there is nothing to compute it from (empty input, or no
threshold/outlier limit supplied by the caller).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from locbench3d.simulate.monte_carlo import FixResult


@dataclass(frozen=True)
class ReliabilityResult:
    attempted_fixes: int
    valid_fixes: int
    invalid_fixes: int
    valid_fix_rate: Optional[float]
    dropout_rate: Optional[float]
    solver_failure_rate: Optional[float]
    outlier_rate: Optional[float]
    severe_outlier_rate: Optional[float]
    continuity: Optional[float]
    longest_outage_fixes: Optional[int]
    reacquisition_time_s: Optional[float]
    availability_by_threshold: dict[float, float] = field(default_factory=dict)
    los_availability: Optional[float] = None
    nlos_availability: Optional[float] = None


def compute_reliability_metrics(
    fixes: list[FixResult],
    accuracy_thresholds_m: Optional[list[float]] = None,
    outlier_threshold_m: Optional[float] = None,
    severe_outlier_threshold_m: Optional[float] = None,
    los_flags: Optional[list[bool]] = None,
) -> ReliabilityResult:
    n = len(fixes)
    if n == 0:
        return ReliabilityResult(
            attempted_fixes=0,
            valid_fixes=0,
            invalid_fixes=0,
            valid_fix_rate=None,
            dropout_rate=None,
            solver_failure_rate=None,
            outlier_rate=None,
            severe_outlier_rate=None,
            continuity=None,
            longest_outage_fixes=None,
            reacquisition_time_s=None,
        )

    valid = [f for f in fixes if f.success]
    dropouts = [f for f in fixes if f.timeout]
    solver_failures = [f for f in fixes if (not f.success) and (not f.timeout)]

    valid_fix_rate = len(valid) / n
    dropout_rate = len(dropouts) / n
    solver_failure_rate = len(solver_failures) / n

    outlier_rate = None
    if outlier_threshold_m is not None:
        errs = [f.error_3d_m for f in valid if f.error_3d_m is not None]
        outlier_rate = sum(1 for e in errs if e > outlier_threshold_m) / n
    severe_outlier_rate = None
    if severe_outlier_threshold_m is not None:
        errs = [f.error_3d_m for f in valid if f.error_3d_m is not None]
        severe_outlier_rate = sum(1 for e in errs if e > severe_outlier_threshold_m) / n

    # Longest run of consecutive invalid attempts, in list order.
    longest_outage = 0
    current = 0
    transitions_valid_to_invalid = 0
    prev_valid: Optional[bool] = None
    for f in fixes:
        is_valid = f.success
        if not is_valid:
            current += 1
            longest_outage = max(longest_outage, current)
        else:
            current = 0
        if prev_valid is True and is_valid is False:
            transitions_valid_to_invalid += 1
        prev_valid = is_valid

    continuity = None
    if len(valid) > 0:
        continuity = 1.0 - (transitions_valid_to_invalid / len(valid))

    availability_by_threshold: dict[float, float] = {}
    if accuracy_thresholds_m:
        for threshold in accuracy_thresholds_m:
            met = sum(
                1 for f in fixes if f.success and f.error_3d_m is not None
                and f.error_3d_m <= threshold
            )
            availability_by_threshold[threshold] = met / n

    los_availability = None
    nlos_availability = None
    if los_flags is not None:
        if len(los_flags) != n:
            raise ValueError("los_flags must be the same length as fixes")
        los_fixes = [f for f, is_los in zip(fixes, los_flags) if is_los]
        nlos_fixes = [f for f, is_los in zip(fixes, los_flags) if not is_los]
        if los_fixes:
            los_availability = sum(1 for f in los_fixes if f.success) / len(los_fixes)
        if nlos_fixes:
            nlos_availability = sum(1 for f in nlos_fixes if f.success) / len(nlos_fixes)

    return ReliabilityResult(
        attempted_fixes=n,
        valid_fixes=len(valid),
        invalid_fixes=n - len(valid),
        valid_fix_rate=valid_fix_rate,
        dropout_rate=dropout_rate,
        solver_failure_rate=solver_failure_rate,
        outlier_rate=outlier_rate,
        severe_outlier_rate=severe_outlier_rate,
        continuity=continuity,
        longest_outage_fixes=longest_outage,
        # Reacquisition dynamics (time to regain a fix after an outage) are
        # not modeled by this project's Monte Carlo engine, which treats
        # each attempt independently; reporting a number here would be
        # invented, not measured or simulated.
        reacquisition_time_s=None,
        availability_by_threshold=availability_by_threshold,
        los_availability=los_availability,
        nlos_availability=nlos_availability,
    )
