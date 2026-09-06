"""Path-level metrics: length, speed, tracking error, dropouts.

Length and speed come from the true trajectory (``Path3D``); error metrics
come from the fix results for that path. Cross-track/along-track error
uses a numerically estimated local tangent direction from the true path,
which is an approximation for paths without an analytic tangent (most of
them); it is still reported since it only needs the true trajectory, not a
fitted or filtered one.

No tracking-lag metric is computed here, because no tracking/filtering
model exists in this project (a lag figure would have to come from
comparing filtered output timing to true timing, which nothing here does).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from locbench3d.paths.trajectories import Path3D
from locbench3d.simulate.monte_carlo import FixResult


@dataclass(frozen=True)
class PathMetricsResult:
    path_id: str
    path_type: str
    sample_count: int
    path_3d_length_m: float
    horizontal_path_length_m: float
    vertical_travel_m: float
    duration_s: float
    mean_speed_m_s: Optional[float]
    max_speed_m_s: Optional[float]
    vertical_speed_m_s: Optional[float]
    horizontal_rmse_m: Optional[float]
    vertical_rmse_m: Optional[float]
    error_3d_rmse_m: Optional[float]
    error_3d_p95_m: Optional[float]
    cross_track_rmse_m: Optional[float]
    along_track_rmse_m: Optional[float]
    dropouts: int
    longest_outage: int


def _path_length_and_speed(path: Path3D):
    pts = path.points()
    diffs = np.diff(pts, axis=0)
    seg_3d = np.linalg.norm(diffs, axis=1)
    seg_h = np.linalg.norm(diffs[:, :2], axis=1)
    dt = np.diff(path.t_s)
    dt_safe = np.where(dt > 0, dt, np.nan)
    speeds = seg_3d / dt_safe
    vertical_speeds = np.abs(diffs[:, 2]) / dt_safe
    duration = float(path.t_s[-1] - path.t_s[0])
    mean_speed = float(np.nanmean(speeds)) if np.any(~np.isnan(speeds)) else None
    max_speed = float(np.nanmax(speeds)) if np.any(~np.isnan(speeds)) else None
    vertical_speed = (
        float(np.nanmean(vertical_speeds)) if np.any(~np.isnan(vertical_speeds)) else None
    )
    return (
        float(np.sum(seg_3d)),
        float(np.sum(seg_h)),
        float(np.sum(np.abs(diffs[:, 2]))),
        duration,
        mean_speed,
        max_speed,
        vertical_speed,
    )


def _tangents(path: Path3D) -> np.ndarray:
    pts = path.points()
    n = len(pts)
    tangents = np.zeros_like(pts)
    for i in range(n):
        lo = max(i - 1, 0)
        hi = min(i + 1, n - 1)
        vec = pts[hi] - pts[lo]
        norm = np.linalg.norm(vec)
        tangents[i] = vec / norm if norm > 1e-12 else np.array([1.0, 0.0, 0.0])
    return tangents


def compute_path_metrics(path: Path3D, fixes: list[FixResult]) -> PathMetricsResult:
    (
        length_3d,
        length_h,
        vertical_travel,
        duration,
        mean_speed,
        max_speed,
        vertical_speed,
    ) = _path_length_and_speed(path)

    successes = [f for f in fixes if f.success]
    horizontal_rmse = vertical_rmse = e3d_rmse = e3d_p95 = None
    cross_track_rmse = along_track_rmse = None

    if successes:
        eh = np.array([f.error_horizontal_m for f in successes])
        ev = np.array([f.error_vertical_m for f in successes])
        e3 = np.array([f.error_3d_m for f in successes])
        horizontal_rmse = float(np.sqrt(np.mean(eh**2)))
        vertical_rmse = float(np.sqrt(np.mean(ev**2)))
        e3d_rmse = float(np.sqrt(np.mean(e3**2)))
        e3d_p95 = float(np.percentile(e3, 95))

        tangents = _tangents(path)
        along_errs = []
        cross_errs = []
        for f in successes:
            idx = f.sample_index
            tangent = tangents[idx]
            err_vec = np.array(
                [
                    f.estimated_x - f.true_x_m,
                    f.estimated_y - f.true_y_m,
                    f.estimated_z - f.true_z_m,
                ]
            )
            along = float(np.dot(err_vec, tangent))
            cross_vec = err_vec - along * tangent
            cross = float(np.linalg.norm(cross_vec))
            along_errs.append(along)
            cross_errs.append(cross)
        along_track_rmse = float(np.sqrt(np.mean(np.square(along_errs))))
        cross_track_rmse = float(np.sqrt(np.mean(np.square(cross_errs))))

    dropouts = sum(1 for f in fixes if f.timeout or not f.success)
    longest_outage = 0
    current = 0
    for f in fixes:
        if not f.success:
            current += 1
            longest_outage = max(longest_outage, current)
        else:
            current = 0

    return PathMetricsResult(
        path_id=path.path_id,
        path_type=path.path_type.value,
        sample_count=path.n_samples,
        path_3d_length_m=length_3d,
        horizontal_path_length_m=length_h,
        vertical_travel_m=vertical_travel,
        duration_s=duration,
        mean_speed_m_s=mean_speed,
        max_speed_m_s=max_speed,
        vertical_speed_m_s=vertical_speed,
        horizontal_rmse_m=horizontal_rmse,
        vertical_rmse_m=vertical_rmse,
        error_3d_rmse_m=e3d_rmse,
        error_3d_p95_m=e3d_p95,
        cross_track_rmse_m=cross_track_rmse,
        along_track_rmse_m=along_track_rmse,
        dropouts=dropouts,
        longest_outage=longest_outage,
    )
