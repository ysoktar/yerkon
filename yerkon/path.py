"""Test trajectories through a coverage area.

A path is where the receiver actually is when a fix is attempted. It
matters more than it looks: if the path only follows the road centreline
while the table claims a 2 km-wide coverage swath, the reported accuracy
describes a strip, not the area in the table's ``Alan`` column. The rural
scenario therefore crosses its swath diagonally rather than driving down
the middle of it. See docs/SCENARIOS.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Path3D:
    """A sampled 3D trajectory. Height is a first-class column, never
    something added to a 2D path afterwards."""

    path_id: str
    t_s: np.ndarray
    x_m: np.ndarray
    y_m: np.ndarray
    z_m: np.ndarray

    @property
    def n_samples(self) -> int:
        return len(self.t_s)

    def points(self) -> np.ndarray:
        return np.column_stack([self.x_m, self.y_m, self.z_m])


def straight_line_path(
    path_id: str,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    n_samples: int,
    duration_s: float,
) -> Path3D:
    """Evenly spaced samples along the segment from ``p0`` to ``p1``."""
    if n_samples < 1:
        raise ValueError("n_samples must be at least 1")
    return Path3D(
        path_id=path_id,
        t_s=np.linspace(0.0, duration_s, n_samples),
        x_m=np.linspace(p0[0], p1[0], n_samples),
        y_m=np.linspace(p0[1], p1[1], n_samples),
        z_m=np.linspace(p0[2], p1[2], n_samples),
    )


def zigzag_path(
    path_id: str,
    x_start: float,
    x_end: float,
    y_amplitude: float,
    z_m: float,
    n_samples: int,
    duration_s: float,
    n_crossings: int = 3,
) -> Path3D:
    """A path that advances along x while sweeping across the corridor in y.

    Used for the rural corridor so the sampled positions span the full
    claimed coverage width instead of hugging the road centreline.
    """
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2")
    x = np.linspace(x_start, x_end, n_samples)
    phase = np.linspace(0.0, n_crossings * np.pi, n_samples)
    y = y_amplitude * np.sin(phase)
    return Path3D(
        path_id=path_id,
        t_s=np.linspace(0.0, duration_s, n_samples),
        x_m=x,
        y_m=y,
        z_m=np.full(n_samples, float(z_m)),
    )


@dataclass(frozen=True)
class Track:
    """A driven or walked route, sampled in time, with velocity.

    A single-epoch study only needs positions. A filter needs motion: the
    process model propagates velocity between fixes, and the odometry and
    heading updates measure it. Speed and heading are therefore carried
    rather than differenced back out of the positions.
    """

    track_id: str
    dt_s: float
    t_s: np.ndarray
    x_m: np.ndarray
    y_m: np.ndarray
    z_m: np.ndarray
    vx_m_s: np.ndarray
    vy_m_s: np.ndarray
    vz_m_s: np.ndarray
    ax_m_s2: np.ndarray
    ay_m_s2: np.ndarray
    az_m_s2: np.ndarray

    @property
    def n_steps(self) -> int:
        return len(self.t_s)

    def positions(self) -> np.ndarray:
        return np.column_stack([self.x_m, self.y_m, self.z_m])

    def velocities(self) -> np.ndarray:
        return np.column_stack([self.vx_m_s, self.vy_m_s, self.vz_m_s])

    def speeds(self) -> np.ndarray:
        return np.linalg.norm(self.velocities(), axis=1)

    def accelerations(self) -> np.ndarray:
        """What an inertial unit on board would sense, before its own errors.

        A vehicle rounding a bend at 50 km/h pulls about 0.6 m/s2 sideways,
        several times any consumer IMU's noise. A filter that treats that
        as unmodelled disturbance instead of measuring it falls behind on
        every corner, so the accelerations are carried explicitly.
        """
        return np.column_stack([self.ax_m_s2, self.ay_m_s2, self.az_m_s2])


def _track_from_positions(track_id: str, dt_s: float, points: np.ndarray) -> Track:
    """Build a track, deriving velocity from the sampled positions.

    Velocity is taken with a central difference so it is consistent with
    the path the filter is asked to follow, rather than an independently
    invented profile that the positions would then contradict.
    """
    n = len(points)
    if n < 2:
        raise ValueError("a track needs at least two samples")
    velocities = np.gradient(points, dt_s, axis=0)
    accelerations = np.gradient(velocities, dt_s, axis=0)
    return Track(
        track_id=track_id,
        dt_s=dt_s,
        t_s=np.arange(n) * dt_s,
        x_m=points[:, 0],
        y_m=points[:, 1],
        z_m=points[:, 2],
        vx_m_s=velocities[:, 0],
        vy_m_s=velocities[:, 1],
        vz_m_s=velocities[:, 2],
        ax_m_s2=accelerations[:, 0],
        ay_m_s2=accelerations[:, 1],
        az_m_s2=accelerations[:, 2],
    )


def driving_track(
    track_id: str,
    start: tuple[float, float, float],
    heading_deg: float,
    speed_m_s: float,
    duration_s: float,
    dt_s: float,
    lane_change_amplitude_m: float = 0.0,
    lane_change_period_s: float = 25.0,
    turn_rate_deg_s: float = 0.0,
    grade_percent: float = 0.0,
) -> Track:
    """A vehicle driving at a set speed, optionally turning and changing lane.

    Turning matters to the result: a receiver that only ever travels in a
    straight line never exercises the heading error, and a filter tuned on
    straight running flatters itself. ``turn_rate_deg_s`` bends the route,
    and the lane-change term adds the small lateral motion that a real
    vehicle makes within its carriageway.
    """
    n = int(round(duration_s / dt_s)) + 1
    t = np.arange(n) * dt_s
    heading = np.radians(heading_deg + turn_rate_deg_s * t)

    # Integrate velocity along the (possibly turning) heading. Rotating the
    # whole displacement vector instead would sweep an arc far longer than
    # the vehicle actually drives.
    step_x = speed_m_s * np.cos(heading) * dt_s
    step_y = speed_m_s * np.sin(heading) * dt_s
    centreline_x = start[0] + np.concatenate([[0.0], np.cumsum(step_x[:-1])])
    centreline_y = start[1] + np.concatenate([[0.0], np.cumsum(step_y[:-1])])

    lateral = (
        lane_change_amplitude_m * np.sin(2.0 * np.pi * t / lane_change_period_s)
        if lane_change_amplitude_m
        else np.zeros(n)
    )
    x = centreline_x - lateral * np.sin(heading)
    y = centreline_y + lateral * np.cos(heading)
    z = start[2] + speed_m_s * t * (grade_percent / 100.0)
    return _track_from_positions(track_id, dt_s, np.column_stack([x, y, z]))


def walking_track(
    track_id: str,
    start: tuple[float, float, float],
    speed_m_s: float,
    duration_s: float,
    dt_s: float,
    turn_period_s: float = 40.0,
    radius_m: float = 30.0,
) -> Track:
    """A pedestrian walking a curved route at walking pace."""
    n = int(round(duration_s / dt_s)) + 1
    t = np.arange(n) * dt_s
    omega = 2.0 * np.pi / turn_period_s
    x = start[0] + radius_m * np.sin(omega * t)
    y = start[1] + radius_m * (1.0 - np.cos(omega * t))
    scale = speed_m_s / max(radius_m * omega, 1e-6)
    x = start[0] + scale * (x - start[0])
    y = start[1] + scale * (y - start[1])
    z = np.full(n, float(start[2]))
    return _track_from_positions(track_id, dt_s, np.column_stack([x, y, z]))
