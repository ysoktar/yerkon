"""The fast forms of the link budget give the slow forms' answers exactly.

ADR-0082 rewrote the hottest loops as array arithmetic. The promise was
not "close": it was the same number to the last bit, so that no
published figure moves because the code got faster. The loops they
replaced are kept here, as they were, and the new code is held to them
with `==` rather than `approx`.
"""

import math

import numpy as np
import pytest

from yerkon.hardware import SPEED_OF_LIGHT_M_S
from yerkon.rf import (
    EFFECTIVE_EARTH_KM,
    bullington_db,
    earth_bulge_m,
    first_fresnel_radius_m,
    knife_edge_db,
    smooth_earth_heights_m,
)


# --- The loops as they were -----------------------------------------------


def _bullington_loop(profile, tx_height_m, rx_height_m, distance_m,
                     frequency_hz, curved=True):
    if distance_m <= 0.0:
        return 0.0
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    span_km = distance_m / 1000.0
    bulge = ((lambda km: 500.0 * km * (span_km - km) / EFFECTIVE_EARTH_KM)
             if curved else (lambda km: 0.0))
    inner = [(fraction * span_km, height) for fraction, height in profile
             if 0.0 < fraction < 1.0]
    if not inner:
        return 0.0
    straight = (rx_height_m - tx_height_m) / span_km
    from_tx = max(((height + bulge(km) - tx_height_m) / km)
                  for km, height in inner)

    def over(km, height):
        sight = (tx_height_m * (span_km - km) + rx_height_m * km) / span_km
        return (height + bulge(km) - sight) * math.sqrt(
            0.002 * span_km / (wavelength_m * km * (span_km - km)))

    from_rx = max(((height + bulge(km) - rx_height_m) / (span_km - km))
                  for km, height in inner)
    if from_tx < straight or abs(from_tx + from_rx) < 1e-12:
        worst = max(over(km, height) for km, height in inner)
    else:
        crossing_km = ((rx_height_m - tx_height_m + from_rx * span_km)
                       / (from_tx + from_rx))
        if not 0.0 < crossing_km < span_km:
            return 0.0
        sight = ((tx_height_m * (span_km - crossing_km)
                  + rx_height_m * crossing_km) / span_km)
        worst = (tx_height_m + from_tx * crossing_km - sight) * math.sqrt(
            0.002 * span_km / (wavelength_m * crossing_km
                               * (span_km - crossing_km)))
    plain = knife_edge_db(worst)
    return plain + (1.0 - math.exp(-plain / 6.0)) * (10.0 + 0.02 * span_km)


def _smooth_earth_loop(profile, distance_m, tx_height_m, rx_height_m):
    span_km = distance_m / 1000.0
    points = [(fraction * span_km, height) for fraction, height in profile]
    if len(points) < 2 or span_km <= 0.0:
        return (0.0, 0.0)
    first = second = 0.0
    for (km_a, height_a), (km_b, height_b) in zip(points, points[1:]):
        step = km_b - km_a
        first += step * (height_b + height_a)
        second += step * (height_b * (2.0 * km_b + km_a)
                          + height_a * (km_b + 2.0 * km_a))
    at_tx = (2.0 * first * span_km - second) / span_km ** 2
    at_rx = (second - first * span_km) / span_km ** 2
    return (min(at_tx, points[0][1], tx_height_m),
            min(at_rx, points[-1][1], rx_height_m))


def _worst_and_blocked_loop(a, b, profile):
    distance_m = math.dist(a, b)
    worst_fraction, worst_ratio, worst_ground = 0.5, math.inf, a[2]
    for fraction, ground_m in profile:
        if fraction <= 0.0 or fraction >= 1.0:
            continue
        sight_m = a[2] + (b[2] - a[2]) * fraction
        zone_m = first_fresnel_radius_m(distance_m, 2450e6, fraction)
        ratio = (sight_m - ground_m) / zone_m
        if ratio < worst_ratio:
            worst_ratio, worst_fraction, worst_ground = ratio, fraction, ground_m
    blocked = False
    for fraction, ground_m in profile:
        if fraction <= 0.0 or fraction >= 1.0:
            continue
        sight_m = a[2] + (b[2] - a[2]) * fraction
        if ground_m + earth_bulge_m(distance_m, fraction) > sight_m:
            blocked = True
            break
    return worst_fraction, worst_ground, blocked


def _ground_point_walk(road, distance_m, offset_m=0.0):
    travelled = 0.0
    segments = list(zip(road.centreline_m, road.centreline_m[1:]))
    for index, (a, b) in enumerate(segments):
        segment = math.dist(a, b)
        last = index == len(segments) - 1
        if travelled + segment >= distance_m or last:
            f = 0.0 if segment == 0.0 else (distance_m - travelled) / segment
            f = min(max(f, 0.0), 1.0)
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            if offset_m and segment > 0.0:
                nx, ny = -(b[1] - a[1]) / segment, (b[0] - a[0]) / segment
                x += nx * offset_m
                y += ny * offset_m
            return (x, y)
        travelled += segment
    raise AssertionError("past the end")


# --- Held to them ---------------------------------------------------------


def _profiles(count=300, seed=11):
    rng = np.random.default_rng(seed)
    for _ in range(count):
        n = int(rng.integers(2, 400))
        fractions = [i / (n - 1) for i in range(n)]
        heights = [float(h) for h in rng.normal(0.0, 15.0, n)]
        yield (list(zip(fractions, heights)), float(rng.uniform(20.0, 25000.0)),
               float(rng.uniform(-5.0, 45.0)), float(rng.uniform(-5.0, 45.0)))


@pytest.mark.parametrize("curved", (True, False))
def test_the_equivalent_edge_is_the_loops_to_the_last_bit(curved):
    for profile, distance, tx, rx in _profiles():
        assert bullington_db(profile, tx, rx, distance, 2.45e9, curved) == \
            _bullington_loop(profile, tx, rx, distance, 2.45e9, curved)


def test_a_path_with_no_inner_points_still_costs_nothing():
    for profile in ([], [(0.0, 5.0), (1.0, 5.0)]):
        assert bullington_db(profile, 10.0, 10.0, 1000.0, 2.45e9) == 0.0


def test_the_smooth_earth_is_the_loops_to_the_last_bit():
    for profile, distance, tx, rx in _profiles():
        assert smooth_earth_heights_m(profile, distance, tx, rx) == \
            _smooth_earth_loop(profile, distance, tx, rx)


def test_the_worst_point_and_the_blocked_ray_are_the_loops_over_real_ground():
    """Over Kızılay, where the profile has roofs in it, and on paths of
    every length the town has."""
    from yerkon.scenarios import CHOICES

    terrain = CHOICES["urban"].scenario.terrain
    rng = np.random.default_rng(3)
    for _ in range(200):
        a = (float(rng.uniform(0, 2900)), float(rng.uniform(0, 2900)), 0.0)
        b = (float(rng.uniform(0, 2900)), float(rng.uniform(0, 2900)), 0.0)
        a = (a[0], a[1], terrain.height_at(a[0], a[1]) + 12.0)
        b = (b[0], b[1], terrain.height_at(b[0], b[1]) + 1.5)
        if math.dist(a, b) < 1.0:
            continue
        found = terrain.obstruction_between(a, b)
        fraction, ground, blocked = _worst_and_blocked_loop(
            a, b, terrain.profile_between(a, b))
        assert (found.peak_at_fraction, found.peak_terrain_m) == (fraction, ground)
        expected_shadow = (terrain.shadowing.between(a, b, obstructed=blocked)
                           if terrain.shadowing is not None else 0.0)
        assert found.shadow_db == expected_shadow
        # The array the budget reads is the profile it describes.
        assert [tuple(row) for row in found.profile_array.tolist()] == \
            list(found.profile)


def test_a_point_along_a_road_is_the_walks_answer():
    from yerkon.scenarios import CHOICES

    for deployed in CHOICES.values():
        road = deployed.scenario.deployment.receivers[0].journey.road
        for along in np.linspace(0.0, road.length_m, 400).tolist():
            for offset in (0.0, 3.5):
                assert road._ground_point(along, offset) == \
                    _ground_point_walk(road, along, offset)
        # Exactly on a joint between two segments, where the walk takes
        # the earlier one.
        _, _, ends = road._segments
        for joint in ends[:-1][:50]:
            assert road._ground_point(joint) == _ground_point_walk(road, joint)
