"""WGS84 geodetic to local ENU conversion, for comparing GNSS fixes to a
common local 3D frame when ground truth is available."""
import numpy as np
import pytest

from locbench3d.gnss.geodesy import lla_to_ecef, lla_to_local_enu


def test_origin_maps_to_zero_enu():
    lat0, lon0, alt0 = 47.0, 8.0, 500.0
    enu = lla_to_local_enu(lat0, lon0, alt0, lat0, lon0, alt0)
    np.testing.assert_allclose(enu, [0.0, 0.0, 0.0], atol=1e-6)


def test_altitude_change_maps_mostly_to_up():
    lat0, lon0, alt0 = 47.0, 8.0, 500.0
    enu = lla_to_local_enu(lat0, lon0, alt0 + 10.0, lat0, lon0, alt0)
    assert enu[2] == pytest.approx(10.0, abs=1e-3)
    assert abs(enu[0]) < 1e-6
    assert abs(enu[1]) < 1e-6


def test_one_degree_longitude_at_equator_is_about_111_km_east():
    enu = lla_to_local_enu(0.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    assert enu[0] == pytest.approx(111_320.0, rel=0.01)
    assert abs(enu[1]) < 1000  # mostly east, not north, at the equator


def test_one_degree_latitude_is_about_111_km_north():
    enu = lla_to_local_enu(1.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert enu[1] == pytest.approx(111_320.0, rel=0.01)
    assert abs(enu[0]) < 1000


def test_ecef_round_trip_scale_is_earth_sized():
    x, y, z = lla_to_ecef(0.0, 0.0, 0.0)
    r = np.hypot(np.hypot(x, y), z)
    assert r == pytest.approx(6_378_137.0, rel=1e-6)  # WGS84 equatorial radius
