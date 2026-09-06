"""Session-level GNSS summary statistics.

Fix-state rates (RTK fixed / float / standalone) and error RMSE are
computed only over fixes that actually carry the relevant field. An empty
input, or a field no fix in the session reports, yields ``None``, never a
fabricated ``0``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from locbench3d.gnss.model import FixState, GnssFix


@dataclass(frozen=True)
class GnssSessionSummary:
    fix_count: int
    rtk_fixed_rate: Optional[float]
    rtk_float_rate: Optional[float]
    standalone_rate: Optional[float]
    horizontal_rmse_m: Optional[float]
    vertical_rmse_m: Optional[float]
    error_3d_rmse_m: Optional[float]
    mean_hdop: Optional[float]
    mean_vdop: Optional[float]
    mean_pdop: Optional[float]


def _rate(fixes: list[GnssFix], state: FixState) -> Optional[float]:
    with_state = [f for f in fixes if f.fix_state is not None]
    if not with_state:
        return None
    return sum(1 for f in with_state if f.fix_state == state) / len(with_state)


def _rmse(values: list[Optional[float]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    arr = np.asarray(present, dtype=float)
    return float(np.sqrt(np.mean(arr**2)))


def _mean(values: list[Optional[float]]) -> Optional[float]:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return float(np.mean(present))


def summarize_gnss_session(fixes: list[GnssFix]) -> GnssSessionSummary:
    return GnssSessionSummary(
        fix_count=len(fixes),
        rtk_fixed_rate=_rate(fixes, FixState.RTK_FIXED),
        rtk_float_rate=_rate(fixes, FixState.RTK_FLOAT),
        standalone_rate=_rate(fixes, FixState.STANDALONE),
        horizontal_rmse_m=_rmse([f.horizontal_error_m for f in fixes]),
        vertical_rmse_m=_rmse([f.vertical_error_m for f in fixes]),
        error_3d_rmse_m=_rmse([f.error_3d_m for f in fixes]),
        mean_hdop=_mean([f.hdop for f in fixes]),
        mean_vdop=_mean([f.vdop for f in fixes]),
        mean_pdop=_mean([f.pdop for f in fixes]),
    )
