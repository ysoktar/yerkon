"""The map's height as a measurement in the filter (ADR-0088)."""

import math
from dataclasses import replace

import numpy as np
import pytest

from yerkon.estimator import Fix, TrackingFilter
from yerkon.evaluate import _MapError, run_scenario
from yerkon.scenarios import CHOICES
from yerkon.settings import DEFAULTS


def _briefly(scenario, seconds=120.0, **changes):
    units = tuple(
        replace(unit, journey=replace(unit.journey, duration_s=min(
            unit.journey.duration_s, seconds)))
        for unit in scenario.deployment.receivers)
    return replace(scenario, deployment=replace(
        scenario.deployment, receivers=units), **changes)


def test_the_map_s_height_pulls_the_filter_and_narrows_it():
    covariance = np.diag([4.0, 4.0, 900.0])
    tracker = TrackingFilter(Fix(at_s=0.0, position_m=(0.0, 0.0, 40.0),
                                 covariance_m2=covariance, used=4))
    tracker.absorb_height(0.0, 10.0, 2.43 ** 2)
    assert tracker.position_m[2] == pytest.approx(10.0, abs=0.3)
    assert tracker.covariance[2, 2] < 2.43 ** 2
    # The horizontal is not told anything by a height.
    assert tracker.position_m[:2] == pytest.approx((0.0, 0.0))
    with pytest.raises(ValueError):
        tracker.absorb_height(0.0, 10.0, 0.0)


def test_the_map_is_wrong_by_what_it_says_everywhere_along_the_road():
    """Not smaller between the draws, which a straight blend would be."""
    errors = np.array([
        [_MapError.drawn(20000.0, 2.43, 500.0, seed, 0).at(d)
         for d in np.linspace(0.0, 19000.0, 77)]
        for seed in range(400)])
    spread = errors.std(axis=0)
    assert spread.mean() == pytest.approx(2.43, rel=0.08)
    assert spread.min() > 2.43 * 0.8
    # And it comes in patches: two points 50 m apart nearly agree.
    one = _MapError.drawn(20000.0, 2.43, 500.0, 1, 0)
    assert abs(one.at(1000.0) - one.at(1050.0)) < 1.0


def test_the_nearest_point_on_a_road_is_found():
    road = CHOICES["urban"].scenario.deployment.receivers[0].journey.road
    # On a loop another lap can be as near, so what is checked is that
    # the point found is on the road where the question was asked.
    for along in (0.0, 1234.5, road.length_m / 2.0):
        x, y, _ = road.point_at(along)
        found = road.nearest_along(x + 3.0, y - 2.0)
        assert math.dist(road.point_at(found)[:2], (x, y)) < 4.0


def test_switching_the_aid_on_leaves_every_ranging_draw_where_it_was():
    urban = CHOICES["urban"].scenario
    off = run_scenario(_briefly(urban, height_aid_sigma_m=0.0))
    on = run_scenario(_briefly(urban))
    assert on.attempted == off.attempted
    assert on.lost_links == off.lost_links
    assert on.attempted_links == off.attempted_links


def test_the_map_brings_the_vertical_down_from_tens_of_metres():
    """What the deck promised as a map constraint."""
    urban = CHOICES["urban"].scenario
    off = run_scenario(_briefly(urban, 300.0, height_aid_sigma_m=0.0))
    on = run_scenario(_briefly(urban, 300.0))
    assert np.percentile(off.vertical_error_m, 95) > 20.0
    assert np.percentile(on.vertical_error_m, 95) < 8.0
    assert np.percentile(on.horizontal_error_m, 95) <= np.percentile(
        off.horizontal_error_m, 95) * 1.05


def test_the_rows_use_the_map_at_its_stated_accuracy():
    assert DEFAULTS.number("estimator.height_aid_sigma_m") == pytest.approx(
        4.0 / 1.645, abs=0.005)
    for deployed in CHOICES.values():
        assert deployed.scenario.height_aid_sigma_m == pytest.approx(2.43)
