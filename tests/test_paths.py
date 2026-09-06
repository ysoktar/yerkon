"""3D path generators.

Every path is native 3D: even a flat path carries a z column that is
constant, rather than being represented as a 2D path with height added on
afterward.
"""
import io

import numpy as np
import pytest

from locbench3d.paths.trajectories import (
    PathType,
    box_perimeter_path,
    custom_path_from_csv,
    diagonal_line_path,
    drone_like_path,
    figure_eight_3d_path,
    helix_path,
    multi_floor_path,
    random_waypoint_path,
    ramp_path,
    staircase_path,
    static_points_path,
    straight_line_path,
    uniform_volume_samples_path,
    vertical_line_path,
    volume_sweep_path,
)


def _assert_valid_path(path, expect_path_type):
    assert path.path_type == expect_path_type
    n = len(path.t_s)
    assert n >= 2
    assert len(path.x_m) == n
    assert len(path.y_m) == n
    assert len(path.z_m) == n
    assert np.all(np.diff(path.t_s) >= 0)


def test_static_points_path_has_zero_dt_between_points():
    points = [(0.0, 0.0, 1.0), (5.0, 5.0, 1.0), (5.0, 0.0, 2.0)]
    path = static_points_path("static-1", points, dwell_s=2.0)
    _assert_valid_path(path, PathType.STATIC)
    assert len(path.t_s) == 3
    np.testing.assert_allclose(path.z_m, [1.0, 1.0, 2.0])


def test_uniform_volume_samples_stay_within_bounds():
    path = uniform_volume_samples_path(
        "uniform-1", n_samples=200, bounds=(10.0, 20.0, 5.0), seed=0
    )
    _assert_valid_path(path, PathType.UNIFORM_VOLUME)
    assert np.all(path.x_m >= 0) and np.all(path.x_m <= 10.0)
    assert np.all(path.y_m >= 0) and np.all(path.y_m <= 20.0)
    assert np.all(path.z_m >= 0) and np.all(path.z_m <= 5.0)


def test_straight_line_path_interpolates_linearly():
    path = straight_line_path(
        "line-1", p0=(0.0, 0.0, 0.0), p1=(10.0, 0.0, 0.0), n_samples=11, duration_s=10.0
    )
    _assert_valid_path(path, PathType.STRAIGHT_LINE)
    np.testing.assert_allclose(path.x_m, np.linspace(0, 10, 11))
    np.testing.assert_allclose(path.z_m, np.zeros(11))


def test_vertical_line_path_changes_only_z():
    path = vertical_line_path("vert-1", x=1.0, y=2.0, z0=0.0, z1=9.0, n_samples=10, duration_s=9.0)
    _assert_valid_path(path, PathType.VERTICAL_LINE)
    assert np.all(path.x_m == 1.0)
    assert np.all(path.y_m == 2.0)
    assert path.z_m[0] == pytest.approx(0.0)
    assert path.z_m[-1] == pytest.approx(9.0)


def test_diagonal_line_path_changes_all_three_axes():
    path = diagonal_line_path(
        "diag-1", p0=(0.0, 0.0, 0.0), p1=(10.0, 10.0, 5.0), n_samples=6, duration_s=5.0
    )
    _assert_valid_path(path, PathType.DIAGONAL_LINE)
    assert path.x_m[-1] == pytest.approx(10.0)
    assert path.y_m[-1] == pytest.approx(10.0)
    assert path.z_m[-1] == pytest.approx(5.0)


def test_box_perimeter_path_returns_to_start():
    path = box_perimeter_path(
        "box-1", width_m=10.0, length_m=6.0, z_m=2.0, n_samples_per_edge=5, duration_s=20.0
    )
    _assert_valid_path(path, PathType.BOX_PERIMETER)
    assert path.x_m[0] == pytest.approx(path.x_m[-1], abs=1e-9)
    assert path.y_m[0] == pytest.approx(path.y_m[-1], abs=1e-9)
    assert np.all(path.z_m == 2.0)


def test_volume_sweep_path_covers_multiple_z_layers():
    path = volume_sweep_path(
        "sweep-1",
        bounds=(10.0, 10.0, 6.0),
        n_layers=3,
        lines_per_layer=4,
        points_per_line=5,
        duration_s=60.0,
    )
    _assert_valid_path(path, PathType.VOLUME_SWEEP)
    assert len(set(np.round(path.z_m, 6))) == 3


def test_helix_path_increases_z_monotonically_and_stays_on_radius():
    path = helix_path(
        "helix-1",
        radius_m=5.0,
        n_turns=3,
        pitch_m_per_turn=2.0,
        z0_m=0.0,
        n_samples=120,
        duration_s=30.0,
    )
    _assert_valid_path(path, PathType.HELIX)
    assert np.all(np.diff(path.z_m) >= -1e-9)
    r = np.hypot(path.x_m, path.y_m)
    np.testing.assert_allclose(r, 5.0, atol=1e-6)
    assert path.z_m[-1] == pytest.approx(3 * 2.0)


def test_figure_eight_3d_path_oscillates_in_z():
    path = figure_eight_3d_path(
        "fig8-1", a_m=5.0, b_m=3.0, z_amplitude_m=1.0, n_samples=100, duration_s=20.0
    )
    _assert_valid_path(path, PathType.FIGURE_EIGHT_3D)
    assert path.z_m.max() > 0
    assert path.z_m.min() < 0


def test_staircase_path_has_discrete_z_levels():
    path = staircase_path(
        "stair-1",
        step_length_m=1.0,
        step_height_m=0.2,
        n_steps=10,
        samples_per_step=3,
        duration_s=30.0,
    )
    _assert_valid_path(path, PathType.STAIRCASE)
    assert path.z_m[-1] == pytest.approx(10 * 0.2)
    assert path.x_m[-1] == pytest.approx(10 * 1.0)


def test_ramp_path_rises_linearly_with_horizontal_distance():
    path = ramp_path("ramp-1", length_m=20.0, height_gain_m=4.0, n_samples=21, duration_s=20.0)
    _assert_valid_path(path, PathType.RAMP)
    assert path.z_m[-1] == pytest.approx(4.0)
    assert path.x_m[-1] == pytest.approx(20.0)


def test_multi_floor_path_visits_each_floor_height():
    path = multi_floor_path(
        "multi-1",
        floor_height_m=3.0,
        floor_count=4,
        waypoints_per_floor=[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)],
        transition_duration_s=5.0,
        waypoint_duration_s=10.0,
    )
    _assert_valid_path(path, PathType.MULTI_FLOOR)
    z_levels = sorted(set(np.round(path.z_m, 6)))
    assert z_levels == [0.0, 3.0, 6.0, 9.0]


def test_random_waypoint_path_respects_bounds_and_speed():
    path = random_waypoint_path(
        "rwp-1",
        bounds=(20.0, 20.0, 5.0),
        n_waypoints=8,
        speed_m_s=1.5,
        seed=1,
    )
    _assert_valid_path(path, PathType.RANDOM_WAYPOINT)
    assert np.all(path.x_m >= 0) and np.all(path.x_m <= 20.0)
    assert np.all(path.z_m >= 0) and np.all(path.z_m <= 5.0)


def test_drone_like_path_has_bounded_vertical_speed():
    path = drone_like_path(
        "drone-1",
        bounds=(50.0, 50.0, 20.0),
        n_waypoints=10,
        max_speed_m_s=8.0,
        max_vertical_speed_m_s=2.0,
        seed=2,
    )
    _assert_valid_path(path, PathType.DRONE_LIKE)
    dz = np.diff(path.z_m)
    dt = np.diff(path.t_s)
    dt[dt == 0] = np.inf
    vertical_speed = np.abs(dz / dt)
    assert np.all(vertical_speed <= 2.0 + 1e-6)


CUSTOM_CSV = """t,x,y,z,velocity,yaw
0.0,0.0,0.0,1.0,0.0,0.0
1.0,1.0,0.0,1.2,1.0,10.0
2.0,2.0,1.0,1.5,1.2,25.0
"""


def test_custom_path_requires_time_and_xyz():
    path = custom_path_from_csv("custom-1", io.StringIO(CUSTOM_CSV))
    _assert_valid_path(path, PathType.CUSTOM)
    assert path.velocity_m_s is not None
    np.testing.assert_allclose(path.velocity_m_s, [0.0, 1.0, 1.2])
    assert path.yaw_deg is not None


def test_custom_path_missing_required_column_raises():
    bad_csv = "t,x,y\n0,0,0\n1,1,1\n"
    with pytest.raises(ValueError):
        custom_path_from_csv("custom-bad", io.StringIO(bad_csv))
