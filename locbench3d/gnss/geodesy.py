"""WGS84 geodetic <-> ECEF <-> local ENU conversion.

Used to put GNSS fixes, reported natively in an ellipsoidal lat/lon/alt
frame, into the same local 3D frame as range-based methods when ground
truth in that local frame is available. The GNSS coordinate-frame identity
(WGS84 ellipsoidal) is preserved on every fix (see ``gnss.model.GnssFix``);
this conversion is applied only when a caller explicitly supplies a local
frame origin, never silently.
"""
from __future__ import annotations

import math

import numpy as np

_WGS84_A = 6_378_137.0  # semi-major axis, m
_WGS84_F = 1.0 / 298.257223563  # flattening
_WGS84_E2 = _WGS84_F * (2.0 - _WGS84_F)  # eccentricity squared


def lla_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> tuple[float, float, float]:
    """WGS84 geodetic (lat, lon, alt) to Earth-centered, Earth-fixed (X, Y, Z)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    n = _WGS84_A / math.sqrt(1.0 - _WGS84_E2 * sin_lat**2)
    x = (n + alt_m) * cos_lat * cos_lon
    y = (n + alt_m) * cos_lat * sin_lon
    z = (n * (1.0 - _WGS84_E2) + alt_m) * sin_lat
    return x, y, z


def lla_to_local_enu(
    lat_deg: float,
    lon_deg: float,
    alt_m: float,
    ref_lat_deg: float,
    ref_lon_deg: float,
    ref_alt_m: float,
) -> np.ndarray:
    """Convert a geodetic point to a local East-North-Up frame at a reference point.

    Returns ``[east_m, north_m, up_m]``. This is the standard ECEF-to-ENU
    rotation about the reference point, exact for the WGS84 ellipsoid (not
    a flat-earth approximation), so it stays accurate over multi-kilometer
    baselines, not just short indoor/local ranges.
    """
    x, y, z = lla_to_ecef(lat_deg, lon_deg, alt_m)
    x0, y0, z0 = lla_to_ecef(ref_lat_deg, ref_lon_deg, ref_alt_m)
    dx, dy, dz = x - x0, y - y0, z - z0

    lat0 = math.radians(ref_lat_deg)
    lon0 = math.radians(ref_lon_deg)
    sin_lat0, cos_lat0 = math.sin(lat0), math.cos(lat0)
    sin_lon0, cos_lon0 = math.sin(lon0), math.cos(lon0)

    r = np.array(
        [
            [-sin_lon0, cos_lon0, 0.0],
            [-sin_lat0 * cos_lon0, -sin_lat0 * sin_lon0, cos_lat0],
            [cos_lat0 * cos_lon0, cos_lat0 * sin_lon0, sin_lat0],
        ]
    )
    enu = r @ np.array([dx, dy, dz])
    return enu
