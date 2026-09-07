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
