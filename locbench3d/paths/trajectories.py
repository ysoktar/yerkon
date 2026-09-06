"""3D path generators for benchmark scenarios.

Every generator produces a :class:`Path3D` with explicit ``t_s``, ``x_m``,
``y_m``, ``z_m`` columns. A flat path (constant z) still carries a z
column; nothing here is a 2D path with height bolted on afterward.
Optional trajectory fields (velocity, acceleration, yaw, pitch, roll) are
``None`` unless the generator or a custom CSV actually supplies them.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from typing import IO, Optional, Sequence

import numpy as np


class PathType(str, Enum):
    STATIC = "STATIC"
    UNIFORM_VOLUME = "UNIFORM_VOLUME"
    STRAIGHT_LINE = "STRAIGHT_LINE"
    VERTICAL_LINE = "VERTICAL_LINE"
    DIAGONAL_LINE = "DIAGONAL_LINE"
    BOX_PERIMETER = "BOX_PERIMETER"
    VOLUME_SWEEP = "VOLUME_SWEEP"
    HELIX = "HELIX"
    FIGURE_EIGHT_3D = "FIGURE_EIGHT_3D"
    STAIRCASE = "STAIRCASE"
    RAMP = "RAMP"
    MULTI_FLOOR = "MULTI_FLOOR"
    CORRIDOR_FLOOR_CHANGE = "CORRIDOR_FLOOR_CHANGE"
    RANDOM_WAYPOINT = "RANDOM_WAYPOINT"
    DRONE_LIKE = "DRONE_LIKE"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class Path3D:
    path_id: str
    path_type: PathType
    t_s: np.ndarray
    x_m: np.ndarray
    y_m: np.ndarray
    z_m: np.ndarray
    velocity_m_s: Optional[np.ndarray] = None
    acceleration_m_s2: Optional[np.ndarray] = None
    yaw_deg: Optional[np.ndarray] = None
    pitch_deg: Optional[np.ndarray] = None
    roll_deg: Optional[np.ndarray] = None

    @property
    def n_samples(self) -> int:
        return len(self.t_s)

    def points(self) -> np.ndarray:
        return np.column_stack([self.x_m, self.y_m, self.z_m])


def _make(path_id, path_type, t, x, y, z, **optional) -> Path3D:
    return Path3D(
        path_id=path_id,
        path_type=path_type,
        t_s=np.asarray(t, dtype=float),
        x_m=np.asarray(x, dtype=float),
        y_m=np.asarray(y, dtype=float),
        z_m=np.asarray(z, dtype=float),
        **optional,
    )


def static_points_path(
    path_id: str, points: Sequence[tuple[float, float, float]], dwell_s: float = 1.0
) -> Path3D:
    """One or more fixed 3D test locations, each held for ``dwell_s``."""
    n = len(points)
    t = np.arange(n) * dwell_s
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    z = [p[2] for p in points]
    return _make(path_id, PathType.STATIC, t, x, y, z)


def uniform_volume_samples_path(
    path_id: str,
    n_samples: int,
    bounds: tuple[float, float, float],
    seed: int = 0,
) -> Path3D:
    """Uniformly random 3D points inside a ``width x length x height`` box."""
    rng = np.random.default_rng(seed)
    width, length, height = bounds
    x = rng.uniform(0.0, width, n_samples)
    y = rng.uniform(0.0, length, n_samples)
    z = rng.uniform(0.0, height, n_samples)
    t = np.arange(n_samples, dtype=float)
    return _make(path_id, PathType.UNIFORM_VOLUME, t, x, y, z)


def straight_line_path(
    path_id: str,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    n_samples: int,
    duration_s: float,
    path_type: PathType = PathType.STRAIGHT_LINE,
) -> Path3D:
    t = np.linspace(0.0, duration_s, n_samples)
    x = np.linspace(p0[0], p1[0], n_samples)
    y = np.linspace(p0[1], p1[1], n_samples)
    z = np.linspace(p0[2], p1[2], n_samples)
    return _make(path_id, path_type, t, x, y, z)


def vertical_line_path(
    path_id: str, x: float, y: float, z0: float, z1: float, n_samples: int, duration_s: float
) -> Path3D:
    return straight_line_path(
        path_id, (x, y, z0), (x, y, z1), n_samples, duration_s, path_type=PathType.VERTICAL_LINE
    )


def diagonal_line_path(
    path_id: str,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    n_samples: int,
    duration_s: float,
) -> Path3D:
    return straight_line_path(
        path_id, p0, p1, n_samples, duration_s, path_type=PathType.DIAGONAL_LINE
    )


def box_perimeter_path(
    path_id: str,
    width_m: float,
    length_m: float,
    z_m: float,
    n_samples_per_edge: int,
    duration_s: float,
) -> Path3D:
    """Loop around the four edges of a rectangle at a fixed height."""
    corners = [
        (0.0, 0.0),
        (width_m, 0.0),
        (width_m, length_m),
        (0.0, length_m),
        (0.0, 0.0),
    ]
    xs: list[float] = []
    ys: list[float] = []
    for (x0, y0), (x1, y1) in zip(corners[:-1], corners[1:]):
        xs.extend(np.linspace(x0, x1, n_samples_per_edge))
        ys.extend(np.linspace(y0, y1, n_samples_per_edge))
    n = len(xs)
    t = np.linspace(0.0, duration_s, n)
    z = np.full(n, z_m)
    return _make(path_id, PathType.BOX_PERIMETER, t, xs, ys, z)


def volume_sweep_path(
    path_id: str,
    bounds: tuple[float, float, float],
    n_layers: int,
    lines_per_layer: int,
    points_per_line: int,
    duration_s: float,
) -> Path3D:
    """Boustrophedon (lawnmower) sweep of the full volume, layer by layer."""
    width, length, height = bounds
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    z_levels = np.linspace(0.0, height, n_layers) if n_layers > 1 else [0.0]
    y_lines = np.linspace(0.0, length, lines_per_layer) if lines_per_layer > 1 else [0.0]
    for z in z_levels:
        for line_idx, y in enumerate(y_lines):
            x_vals = (
                np.linspace(0.0, width, points_per_line)
                if line_idx % 2 == 0
                else np.linspace(width, 0.0, points_per_line)
            )
            for x in x_vals:
                xs.append(x)
                ys.append(y)
                zs.append(z)
    n = len(xs)
    t = np.linspace(0.0, duration_s, n)
    return _make(path_id, PathType.VOLUME_SWEEP, t, xs, ys, zs)


def helix_path(
    path_id: str,
    radius_m: float,
    n_turns: float,
    pitch_m_per_turn: float,
    z0_m: float,
    n_samples: int,
    duration_s: float,
    center_xy: tuple[float, float] = (0.0, 0.0),
) -> Path3D:
    theta = np.linspace(0.0, 2 * np.pi * n_turns, n_samples)
    cx, cy = center_xy
    x = cx + radius_m * np.cos(theta)
    y = cy + radius_m * np.sin(theta)
    z = z0_m + pitch_m_per_turn * (theta / (2 * np.pi))
    t = np.linspace(0.0, duration_s, n_samples)
    return _make(path_id, PathType.HELIX, t, x, y, z)


def figure_eight_3d_path(
    path_id: str,
    a_m: float,
    b_m: float,
    z_amplitude_m: float,
    n_samples: int,
    duration_s: float,
    center_xy: tuple[float, float] = (0.0, 0.0),
    z0_m: float = 0.0,
) -> Path3D:
    """A Lissajous figure-eight in x/y with an independent vertical oscillation."""
    theta = np.linspace(0.0, 2 * np.pi, n_samples)
    cx, cy = center_xy
    x = cx + a_m * np.sin(theta)
    y = cy + b_m * np.sin(theta) * np.cos(theta)
    z = z0_m + z_amplitude_m * np.sin(2 * theta)
    t = np.linspace(0.0, duration_s, n_samples)
    return _make(path_id, PathType.FIGURE_EIGHT_3D, t, x, y, z)


def staircase_path(
    path_id: str,
    step_length_m: float,
    step_height_m: float,
    n_steps: int,
    samples_per_step: int,
    duration_s: float,
) -> Path3D:
    """Alternating horizontal tread / vertical riser, like a real staircase."""
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for i in range(n_steps):
        x0, x1 = i * step_length_m, (i + 1) * step_length_m
        z0, z1 = i * step_height_m, (i + 1) * step_height_m
        # tread: horizontal, constant z
        xs.extend(np.linspace(x0, x1, samples_per_step))
        ys.extend([0.0] * samples_per_step)
        zs.extend([z0] * samples_per_step)
        # riser: vertical, constant x
        xs.extend([x1] * samples_per_step)
        ys.extend([0.0] * samples_per_step)
        zs.extend(np.linspace(z0, z1, samples_per_step))
    n = len(xs)
    t = np.linspace(0.0, duration_s, n)
    return _make(path_id, PathType.STAIRCASE, t, xs, ys, zs)


def ramp_path(
    path_id: str, length_m: float, height_gain_m: float, n_samples: int, duration_s: float
) -> Path3D:
    t = np.linspace(0.0, duration_s, n_samples)
    x = np.linspace(0.0, length_m, n_samples)
    y = np.zeros(n_samples)
    z = np.linspace(0.0, height_gain_m, n_samples)
    return _make(path_id, PathType.RAMP, t, x, y, z)


def multi_floor_path(
    path_id: str,
    floor_height_m: float,
    floor_count: int,
    waypoints_per_floor: Sequence[tuple[float, float]],
    transition_duration_s: float,
    waypoint_duration_s: float,
) -> Path3D:
    """Horizontal waypoints on each floor, connected by vertical transitions."""
    if not waypoints_per_floor:
        raise ValueError("waypoints_per_floor must not be empty")
    ts: list[float] = []
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    t_cursor = 0.0
    for floor in range(floor_count):
        z = floor * floor_height_m
        for wx, wy in waypoints_per_floor:
            ts.append(t_cursor)
            xs.append(wx)
            ys.append(wy)
            zs.append(z)
            t_cursor += waypoint_duration_s
        if floor < floor_count - 1:
            last_x, last_y = waypoints_per_floor[-1]
            z_next = (floor + 1) * floor_height_m
            ts.append(t_cursor)
            xs.append(last_x)
            ys.append(last_y)
            zs.append(z)
            t_cursor += transition_duration_s
            ts.append(t_cursor)
            xs.append(last_x)
            ys.append(last_y)
            zs.append(z_next)
    return _make(path_id, PathType.MULTI_FLOOR, ts, xs, ys, zs)


def corridor_floor_change_path(
    path_id: str,
    corridor_length_m: float,
    n_samples_corridor: int,
    floor_height_m: float,
    n_samples_transition: int,
    duration_s: float,
) -> Path3D:
    """Walk down a corridor, then change floor (stairs/elevator) at its end."""
    corridor = straight_line_path(
        path_id,
        (0.0, 0.0, 0.0),
        (corridor_length_m, 0.0, 0.0),
        n_samples_corridor,
        duration_s * (n_samples_corridor / (n_samples_corridor + n_samples_transition)),
        path_type=PathType.CORRIDOR_FLOOR_CHANGE,
    )
    transition_t = np.linspace(
        corridor.t_s[-1],
        duration_s,
        n_samples_transition,
    )
    transition_z = np.linspace(0.0, floor_height_m, n_samples_transition)
    t = np.concatenate([corridor.t_s, transition_t[1:]])
    x = np.concatenate([corridor.x_m, np.full(n_samples_transition - 1, corridor_length_m)])
    y = np.concatenate([corridor.y_m, np.zeros(n_samples_transition - 1)])
    z = np.concatenate([corridor.z_m, transition_z[1:]])
    return _make(path_id, PathType.CORRIDOR_FLOOR_CHANGE, t, x, y, z)


def random_waypoint_path(
    path_id: str,
    bounds: tuple[float, float, float],
    n_waypoints: int,
    speed_m_s: float,
    seed: int = 0,
    pause_s: float = 0.0,
) -> Path3D:
    """Classic random-waypoint mobility model, extended to 3D."""
    if speed_m_s <= 0:
        raise ValueError("speed_m_s must be positive")
    rng = np.random.default_rng(seed)
    width, length, height = bounds
    waypoints = np.column_stack(
        [
            rng.uniform(0.0, width, n_waypoints),
            rng.uniform(0.0, length, n_waypoints),
            rng.uniform(0.0, height, n_waypoints),
        ]
    )
    t = np.zeros(n_waypoints)
    for i in range(1, n_waypoints):
        dist = float(np.linalg.norm(waypoints[i] - waypoints[i - 1]))
        t[i] = t[i - 1] + dist / speed_m_s + pause_s
    return _make(
        path_id,
        PathType.RANDOM_WAYPOINT,
        t,
        waypoints[:, 0],
        waypoints[:, 1],
        waypoints[:, 2],
    )


def drone_like_path(
    path_id: str,
    bounds: tuple[float, float, float],
    n_waypoints: int,
    max_speed_m_s: float,
    max_vertical_speed_m_s: float,
    seed: int = 0,
) -> Path3D:
    """Randomized 3D waypoints with separate horizontal/vertical speed limits."""
    if max_speed_m_s <= 0 or max_vertical_speed_m_s <= 0:
        raise ValueError("speed limits must be positive")
    rng = np.random.default_rng(seed)
    width, length, height = bounds
    waypoints = np.column_stack(
        [
            rng.uniform(0.0, width, n_waypoints),
            rng.uniform(0.0, length, n_waypoints),
            rng.uniform(0.0, height, n_waypoints),
        ]
    )
    t = np.zeros(n_waypoints)
    for i in range(1, n_waypoints):
        dx, dy, dz = waypoints[i] - waypoints[i - 1]
        horiz = float(np.hypot(dx, dy))
        dt_h = horiz / max_speed_m_s
        dt_v = abs(float(dz)) / max_vertical_speed_m_s
        t[i] = t[i - 1] + max(dt_h, dt_v)
    return _make(
        path_id,
        PathType.DRONE_LIKE,
        t,
        waypoints[:, 0],
        waypoints[:, 1],
        waypoints[:, 2],
    )


_CUSTOM_REQUIRED = ("t", "x", "y", "z")
_CUSTOM_OPTIONAL = ("velocity", "acceleration", "yaw", "pitch", "roll")
_CUSTOM_OPTIONAL_ATTR = {
    "velocity": "velocity_m_s",
    "acceleration": "acceleration_m_s2",
    "yaw": "yaw_deg",
    "pitch": "pitch_deg",
    "roll": "roll_deg",
}


def custom_path_from_csv(path_id: str, source: IO[str]) -> Path3D:
    """Load a custom 3D path from CSV. Requires columns t, x, y, z.

    Optional columns velocity, acceleration, yaw, pitch, roll are attached
    when present and left unset otherwise.
    """
    reader = csv.DictReader(source)
    if reader.fieldnames is None:
        raise ValueError("custom path CSV has no header row")
    missing = [c for c in _CUSTOM_REQUIRED if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"custom path CSV missing required columns: {missing}")

    rows = list(reader)
    t = [float(r["t"]) for r in rows]
    x = [float(r["x"]) for r in rows]
    y = [float(r["y"]) for r in rows]
    z = [float(r["z"]) for r in rows]

    optional: dict = {}
    for col in _CUSTOM_OPTIONAL:
        if col in reader.fieldnames:
            optional[_CUSTOM_OPTIONAL_ATTR[col]] = np.array(
                [float(r[col]) for r in rows]
            )

    return _make(path_id, PathType.CUSTOM, t, x, y, z, **optional)
