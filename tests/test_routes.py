"""Where a receiver drives, and why one route is not the same as another.

A journey used to be one shape per tab and every unit followed it. That
is an arrangement rather than a choice, and it quietly decides something
the table reports: a route that only ever runs east never changes its
cross-track geometry, which is the whole of ADR-0011.
"""

import math

import numpy as np
import pytest

from yerkon.routes import METHODS, NEED_WIDTH, Course, Trip, trace

AREA = Course(length_m=3000.0, width_m=2000.0)
LINE = Course(length_m=4000.0, width_m=0.0)


# --- The seam -------------------------------------------------------------


@pytest.mark.parametrize("method", [m for m in METHODS if m != "road"])
def test_every_route_is_reached_through_one_function(method):
    """The whole interface is `trace(trip, course)`, the same shape as
    `place(plan, ground)`. Adding a route is a function and a name."""
    drawn = trace(Trip(method=method, step_m=150.0), AREA)
    assert isinstance(drawn, tuple) and len(drawn) >= 2
    assert all(len(point) == 2 for point in drawn)


@pytest.mark.parametrize("method", [m for m in METHODS if m != "road"])
def test_no_route_leaves_the_site(method):
    """Past the edge is ground nobody measured, and a receiver scored out
    there is being scored against the boundary row extruded into a plane
    (ADR-0037)."""
    for x, y in trace(Trip(method=method, step_m=150.0), AREA):
        assert -1e-6 <= x <= AREA.length_m + 1e-6, (method, x)
        assert -1e-6 <= y <= AREA.width_m + 1e-6, (method, y)


def test_a_route_nobody_has_lists_the_ones_that_exist():
    with pytest.raises(ValueError, match="lawnmower"):
        trace(Trip(method="teleport"), AREA)


@pytest.mark.parametrize("method", NEED_WIDTH)
def test_an_area_route_over_a_corridor_becomes_one(method):
    """A corridor has no width to turn in. Out and back rather than a
    plain line, because it is the richest thing a corridor allows."""
    assert trace(Trip(method=method), LINE) == trace(
        Trip(method="out-and-back"), LINE)


def test_the_real_road_says_it_is_not_there_rather_than_drawing_nothing():
    """Greyed in the page, refused in the engine. A fetch has to bring
    road geometry first (ADR-0036)."""
    with pytest.raises(ValueError, match="real road"):
        trace(Trip(method="road"), AREA)

    with_road = Course(length_m=3000.0, width_m=2000.0,
                       road=((0.0, 500.0), (1500.0, 700.0), (3000.0, 400.0)))
    drawn = trace(Trip(method="road", step_m=200.0), with_road)
    assert len(drawn) > 3
    assert drawn[0] == pytest.approx((0.0, 500.0))


# --- What each shape is for ----------------------------------------------


def test_a_straight_line_never_changes_its_cross_track_geometry():
    """Which is exactly why it is not the only route on offer: on a
    corridor it is the arrangement that makes a deployment look better
    than it is (ADR-0011)."""
    drawn = trace(Trip(method="line", step_m=250.0), LINE)
    assert {round(y, 6) for _, y in drawn} == {0.0}


def test_out_and_back_returns_to_where_it_started():
    """Every point observed once heading each way, so a bias that depends
    on which side the anchors are on shows up instead of averaging into
    the answer."""
    drawn = trace(Trip(method="out-and-back", step_m=250.0), LINE)
    assert drawn[0] == pytest.approx(drawn[-1])
    assert max(x for x, _ in drawn) == pytest.approx(LINE.length_m)


def test_a_figure_of_eight_turns_both_ways():
    """The pattern receivers are driven through on test: it crosses
    itself, so the vehicle passes every heading. A loop that only ever
    turns one way can hide an error that depends on which way it turns.
    """
    drawn = trace(Trip(method="figure-eight", step_m=120.0), AREA)
    headings = [
        math.atan2(b[1] - a[1], b[0] - a[0]) for a, b in zip(drawn, drawn[1:])
    ]
    turns = [
        math.atan2(math.sin(b - a), math.cos(b - a))
        for a, b in zip(headings, headings[1:])
    ]
    assert any(t > 1e-6 for t in turns), "it never turns left"
    assert any(t < -1e-6 for t in turns), "it never turns right"

    # And it uses the ground it was given rather than half of it: written
    # the obvious way, `sin(t)cos(t)` peaks at a half.
    ys = [y for _, y in drawn]
    inset = AREA.inset_m
    assert max(ys) == pytest.approx(AREA.width_m - inset, abs=1.0)
    assert min(ys) == pytest.approx(inset, abs=1.0)


def test_the_lawnmower_samples_the_middle_and_the_circuit_does_not():
    """The distinction that makes both worth having. A circuit tells you
    about the boundary and one diagonal; a boustrophedon sweep tells you
    about the ground between them."""
    lanes = 6
    mown = trace(Trip(method="lawnmower", passes=lanes, step_m=100.0), AREA)
    round_it = trace(Trip(method="circuit", step_m=100.0), AREA)

    # How many distinct bands across the site each route visits.
    def bands(points):
        return len({int(y // (AREA.width_m / 10)) for _, y in points})

    assert bands(mown) >= bands(round_it)
    assert len({round(y, 3) for _, y in mown}) >= lanes


def test_more_passes_is_a_longer_journey_over_the_same_ground():
    def walked(points):
        return sum(math.dist(a, b) for a, b in zip(points, points[1:]))

    few = trace(Trip(method="lawnmower", passes=3, step_m=100.0), AREA)
    many = trace(Trip(method="lawnmower", passes=9, step_m=100.0), AREA)
    assert walked(many) > walked(few)


def test_the_random_walk_is_the_same_walk_twice():
    """Seeded, because a route that changed between two runs would make
    two tables differ for a reason nobody could see."""
    once = trace(Trip(method="waypoints", seed=7, stops=6), AREA)
    again = trace(Trip(method="waypoints", seed=7, stops=6), AREA)
    other = trace(Trip(method="waypoints", seed=8, stops=6), AREA)
    assert once == again
    assert once != other


def test_random_waypoint_favours_the_middle_which_is_its_known_fault():
    """Named rather than hidden. Waypoints drawn uniformly put a vehicle
    in the middle of the site far more often than at its edges — Yoon,
    Liu and Noble, *Random waypoint considered harmful* (2003) — and this
    model has that property, so a reader should know it does.
    """
    inside = 0
    edge = 0
    for seed in range(40):
        for x, y in trace(Trip(method="waypoints", seed=seed, stops=8), AREA):
            middle = (abs(x - AREA.length_m / 2) < AREA.length_m / 4
                      and abs(y - AREA.width_m / 2) < AREA.width_m / 4)
            inside += 1 if middle else 0
            edge += 0 if middle else 1
    # The middle quarter is a quarter of the area and collects rather
    # more than a quarter of the time.
    assert inside / (inside + edge) > 0.25


# --- Each unit on its own route ------------------------------------------


def test_two_receivers_can_drive_two_different_routes():
    """The point of the whole module. A van on the ring road and a survey
    vehicle mowing the town are asking different questions of the same
    anchors (ADR-0045)."""
    from dataclasses import replace

    from yerkon.viewer.state import from_scenario

    state = from_scenario("urban")
    two = replace(state, units=(
        replace(state.units[0], identifier="a", route="line"),
        replace(state.units[0], identifier="b", route="lawnmower"),
    ))
    terrain = two.terrain()
    first, second = two.receivers(terrain)

    assert first.journey.road.centreline_m != second.journey.road.centreline_m
    assert {round(y, 6) for _, y in first.journey.road.centreline_m} == {0.0}
    assert len({round(y, 3) for _, y in second.journey.road.centreline_m}) > 1


@pytest.mark.parametrize("mode", ["urban", "rural", "tunnel"])
def test_a_unit_that_names_no_route_drives_what_it_always_drove(mode):
    """Point for point, against the code this replaced.

    Comparing the default against the new `circuit` would prove only that
    the new code agrees with itself. The two shapes that were here before
    are still in `scenarios`, so the comparison is against them — and it
    has to be exact, because every published row is a journey along one
    of these and a route that moved by a metre would move the table with
    no visible reason.
    """
    from yerkon.scenarios import _circuit, _straight_road
    from yerkon.viewer.state import from_scenario

    state = from_scenario(mode)
    terrain = state.terrain()
    assert all(unit.route == "" for unit in state.units)

    if state.width_m <= 0.0:
        was = _straight_road(state.corridor_m, terrain)
    else:
        was = _circuit(
            state.corridor_m, state.width_m, terrain,
            inset_m=min(state.corridor_m, state.width_m) * 0.1,
            step_m=max(min(state.corridor_m, state.width_m) / 20.0, 50.0),
        )
    drove = state.receivers(terrain)[0].journey.road.centreline_m
    assert len(drove) == len(was.centreline_m)
    for mine, theirs in zip(drove, was.centreline_m):
        assert mine == pytest.approx(theirs, abs=1e-9)


def test_where_the_anchors_go_does_not_move_with_one_units_route():
    """The spine is a fact about the site, not about which pattern a
    receiver was told to drive."""
    from dataclasses import replace

    from yerkon.viewer.state import from_scenario

    state = from_scenario("rural")
    terrain = state.terrain()
    before = [a.ground_position_m for a in state.anchors(terrain)]

    wandering = replace(state, units=(
        replace(state.units[0], route="waypoints"),
    ))
    after = [a.ground_position_m for a in wandering.anchors(terrain)]
    assert np.allclose(np.array(before), np.array(after))


def test_the_engine_names_the_routes_and_says_which_this_ground_carries():
    """A control that does nothing is not a control (ADR-0036). The real
    road needs geometry a fetch has not brought."""
    from yerkon.viewer.scene import scene
    from yerkon.viewer.state import from_scenario

    choices = scene(from_scenario("urban"))["choices"]
    offered = [name for name, _ in choices["routes"]]
    assert offered[0] == "", "the site's own shape comes first"
    assert set(offered[1:]) == set(METHODS)
    assert "road" not in choices["routes_live"]
    assert set(choices["routes_live"]) == set(METHODS) - {"road"}
