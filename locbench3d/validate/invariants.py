"""Result invariant checks run against real generated tables.

These are a defense-in-depth pass over actual DataFrame output, on top of
(not instead of) the unit tests that pin the underlying rules (frame
scaling, TDoA range-difference semantics, and so on) at the function
level. A violation here means something got through the pipeline that
should not have.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from locbench3d.metrics.scalability import ScalabilityResult


@dataclass(frozen=True)
class InvariantViolation:
    check: str
    message: str
    row_index: object = None


def check_no_duplicate_scenario_ids(df: pd.DataFrame) -> list[InvariantViolation]:
    if "scenario_id" not in df.columns:
        return []
    dupes = df["scenario_id"][df["scenario_id"].duplicated()].unique().tolist()
    if not dupes:
        return []
    return [
        InvariantViolation(
            "no_duplicate_scenario_ids", f"duplicate scenario_id values: {dupes}"
        )
    ]


def _check_le(df, lo_col, hi_col, check_name, message):
    if lo_col not in df.columns or hi_col not in df.columns:
        return []
    sub = df[[lo_col, hi_col]].dropna()
    bad = sub[sub[lo_col] > sub[hi_col]]
    if bad.empty:
        return []
    return [InvariantViolation(check_name, message, row_index=list(bad.index))]


def _check_range_0_1(df: pd.DataFrame, col: str) -> list[InvariantViolation]:
    if col not in df.columns:
        return []
    vals = df[col].dropna()
    bad = vals[(vals < -1e-9) | (vals > 1.0 + 1e-9)]
    if bad.empty:
        return []
    return [
        InvariantViolation(
            "percentage_in_valid_range",
            f"{col} has values outside [0, 1]: {bad.tolist()}",
        )
    ]


def _check_nonnegative(df: pd.DataFrame, col: str) -> list[InvariantViolation]:
    if col not in df.columns:
        return []
    vals = df[col].dropna()
    bad = vals[vals < 0]
    if bad.empty:
        return []
    return [InvariantViolation("counts_not_negative", f"{col} has negative values: {bad.tolist()}")]


_RATE_LIKE_SUFFIXES = ("_rate", "_fraction", "_probability", "_availability")
_COUNT_LIKE_SUFFIXES = ("_count", "_fixes", "_samples")
# Utilization/load ratios are legitimately unbounded above 1 (that is what
# "overloaded" means); they must not be checked against the [0, 1] range a
# true rate/fraction/probability is checked against.
_UNBOUNDED_LOAD_SUBSTRINGS = ("airtime", "occupancy")

_PERCENTILE_TRIPLES = [
    ("acc_error_3d_p50_m", "acc_error_3d_p95_m", "acc_error_3d_p99_m"),
    ("acc_horizontal_p50_m", "acc_horizontal_p95_m", "acc_horizontal_p99_m"),
    ("acc_vertical_p50_m", "acc_vertical_p95_m", "acc_vertical_p99_m"),
]


def check_master_table(df: pd.DataFrame) -> list[InvariantViolation]:
    violations: list[InvariantViolation] = []
    violations += check_no_duplicate_scenario_ids(df)
    violations += _check_le(
        df, "rel_valid_fixes", "rel_attempted_fixes",
        "valid_le_attempted", "rel_valid_fixes exceeds rel_attempted_fixes",
    )

    for p50, p95, p99 in _PERCENTILE_TRIPLES:
        violations += _check_le(df, p50, p95, "p95_ge_p50", f"{p95} is below {p50}")
        violations += _check_le(df, p95, p99, "p99_ge_p95", f"{p99} is below {p95}")

    for col in df.columns:
        if col.endswith(_RATE_LIKE_SUFFIXES) and not any(
            s in col for s in _UNBOUNDED_LOAD_SUBSTRINGS
        ):
            violations += _check_range_0_1(df, col)
        if col.endswith(_COUNT_LIKE_SUFFIXES):
            violations += _check_nonnegative(df, col)

    if "scale_overloaded" in df.columns and "feas_feasible" in df.columns:
        bad = df[(df["scale_overloaded"] == True) & (df["feas_feasible"] == True)]  # noqa: E712
        if not bad.empty:
            violations.append(
                InvariantViolation(
                    "overloaded_marked_infeasible",
                    "rows marked overloaded but also marked feasible",
                    row_index=list(bad.index),
                )
            )

    return violations


def check_range_comparison_table(df: pd.DataFrame) -> list[InvariantViolation]:
    violations: list[InvariantViolation] = []
    if "attempted_fixes" in df.columns:
        empty = df[df["attempted_fixes"] <= 0]
        if not empty.empty:
            violations.append(
                InvariantViolation(
                    "no_empty_range_bins",
                    "range comparison table contains an empty bin (zero attempted fixes)",
                    row_index=list(empty.index),
                )
            )
    violations += _check_le(
        df, "valid_fixes", "attempted_fixes",
        "valid_le_attempted", "valid_fixes exceeds attempted_fixes",
    )
    for col in ("p50_m", "p90_m", "p95_m", "p99_m", "availability", "dropout_rate",
                "los_fraction", "nlos_fraction"):
        if col in ("availability", "dropout_rate", "los_fraction", "nlos_fraction"):
            violations += _check_range_0_1(df, col)
    violations += _check_le(df, "p50_m", "p90_m", "p90_ge_p50", "p90_m below p50_m")
    violations += _check_le(df, "p90_m", "p95_m", "p95_ge_p90", "p95_m below p90_m")
    violations += _check_le(df, "p95_m", "p99_m", "p99_ge_p95", "p99_m below p95_m")
    return violations


def check_scalability_results(results: list[ScalabilityResult]) -> list[InvariantViolation]:
    violations = []
    for r in results:
        if r.scheduled_occupancy > 1.0 and not r.overloaded:
            violations.append(
                InvariantViolation(
                    "overloaded_flag_matches_occupancy",
                    f"scenario with method={r.method} anchors={r.anchor_count} "
                    f"tags={r.tag_count} has occupancy {r.scheduled_occupancy:.3f} "
                    "> 1.0 but overloaded=False",
                )
            )
        expected_frames = None
        from locbench3d.protocol.traffic import RangingMethod, frames_per_fix

        expected_frames = frames_per_fix(r.method, r.anchor_count)
        if r.frames_per_fix != expected_frames:
            violations.append(
                InvariantViolation(
                    "twr_frame_count_scales_with_anchor_count",
                    f"frames_per_fix={r.frames_per_fix} does not match the expected "
                    f"{expected_frames} for method={r.method}, anchors={r.anchor_count}",
                )
            )
    return violations
