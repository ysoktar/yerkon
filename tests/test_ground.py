"""Real Ankara ground, and the rule that nothing here stands on a plane."""

import math

import pytest

from yerkon.scenarios import (
    CHOICES,
    HARD_RURAL_SITE,
    RURAL_SITE,
    SITES,
    TUNNEL_BORE,
    TUNNEL_SITE,
    URBAN_SITE,
    fetched,
    rural_ground,
    tunnel_ground,
    urban_ground,
)
from yerkon.settings import DEFAULTS
from yerkon.world import bore_terrain, flat_terrain


# --- What ships -----------------------------------------------------------


@pytest.mark.parametrize(
    "name", [URBAN_SITE, RURAL_SITE, HARD_RURAL_SITE, TUNNEL_SITE]
)
def test_the_ground_each_row_stands_on_ships_with_the_package(name):
    """ADR-0008, finally taken at its word.

    A cache directory is a self-contained artefact, so a clone reproduces
    every number in the table with no network. A megabyte of Copernicus
    grid is a small price for that.
    """
    site = fetched(name)
    assert site is not None, "{} was never fetched into {}".format(name, SITES)
    assert site.manifest.elevation_source
    assert site.manifest.fetched_at
    assert site.relief_m > 0.0


def test_the_fetched_ground_covers_the_scenario_that_stands_on_it():
    """A grid smaller than its scenario silently clamps at the edge.

    Which would put a row of anchors on the last known contour and look
    like terrain rather than like the artefact it is.
    """
    for name, extent_m in ((URBAN_SITE, 2900.0), (RURAL_SITE, 19_800.0)):
        site = fetched(name)
        assert site.width_m >= extent_m, name
        assert site.height_m >= extent_m, name


# --- Nowhere is flat ------------------------------------------------------


def _spread_of(terrain, extent_m, samples=9):
    step = extent_m / (samples - 1)
    heights = [
        terrain.height_at(i * step, j * step)
        for i in range(samples)
        for j in range(samples)
    ]
    return max(heights) - min(heights)


@pytest.mark.parametrize("name", sorted(CHOICES))
def test_no_scenario_stands_on_a_level_surface(name):
    """ADR-0021. A plane is the most favourable ground this model can draw.

    Every reflection off it arrives at exactly the specular angle the
    two-ray term assumes, nothing can obstruct anything, and every
    terminal sits at one height. It looks like the assumption-free choice
    and it is the opposite of one.
    """
    deployed = CHOICES[name]
    extent = max(
        max(a.ground_position_m[0] for a in deployed.scenario.deployment.anchors),
        1.0,
    )
    assert _spread_of(deployed.scenario.terrain, extent) > 1.0
    assert "flat" not in deployed.scenario.terrain.description


def test_the_modelled_fallback_is_not_flat_either():
    """The place a run lands when nobody has fetched anything.

    If the fallback were a plane, a machine with no network would be
    running a different and friendlier study than one with a cache, and
    nothing would say so.
    """
    for terrain, extent in (
        (urban_ground(DEFAULTS, 30.0), 3000.0),
        (rural_ground(DEFAULTS), 20_000.0),
        (tunnel_ground(DEFAULTS, 2000.0, site_name=""), 2000.0),
    ):
        assert "flat" not in terrain.description
        assert _spread_of(terrain, extent) > 1.0


def test_the_relief_the_fallback_uses_was_measured_not_guessed():
    """ADR-0016 and ADR-0021 together.

    The fallback exists so a run without a cache is still not a plane.
    That is only worth anything if its shape came from the real grids
    rather than from somebody's idea of a landscape.
    """
    for key in ("site.urban_relief_m", "site.rural_relief_m", "site.tunnel_grade"):
        entry = DEFAULTS.entry(key)
        assert not entry.is_assumed, key
        assert "Copernicus" in entry.sourced.source, key


# --- The bore -------------------------------------------------------------


def test_the_bore_goes_through_the_mountain_rather_than_over_it():
    """A tunnel cannot be built by draping a road over terrain.

    Its floor is a straight line between two portals, and the mountain
    is above it the whole way. Sampling the surface instead would give a
    road that climbs a hill nobody drives over.
    """
    site = fetched(TUNNEL_SITE)
    (entry_x, entry_y), (exit_x, _) = TUNNEL_BORE
    length = exit_x - entry_x
    bore = tunnel_ground(DEFAULTS, length)

    cover = [
        site.height_at(entry_x + f * length, entry_y) - bore.height_at(f * length, 0.0)
        for f in [i / 40.0 for i in range(2, 39)]
    ]
    assert min(cover) > 0.0, "the bore surfaces partway along; that is a cutting"
    assert max(cover) > 50.0, "no mountain above it; that is not a tunnel"


def test_the_bore_falls_at_a_gradient_a_road_tunnel_is_built_to():
    """Between half a percent and three, for drainage.

    A level floor is not a simplification of a tunnel. It is a tunnel no
    highway authority would accept, and it puts every anchor and every
    receiver at one height, which is the arrangement least able to say
    anything about the vertical.
    """
    bore = CHOICES["tunnel"].scenario.terrain
    fall = abs(bore.height_at(2000.0, 0.0) - bore.height_at(0.0, 0.0))
    assert 0.004 <= fall / 2000.0 <= 0.030


def test_the_bore_is_straight():
    bore = bore_terrain(1168.5, 1132.7, 2000.0)
    assert bore.height_at(1000.0, 0.0) == pytest.approx(1150.6)
    # And it is a plane, so the cross-section is level whatever y is.
    assert bore.height_at(500.0, -6.0) == bore.height_at(500.0, 6.0)


def test_a_bore_of_no_length_is_refused():
    with pytest.raises(ValueError, match="a bore has a length"):
        bore_terrain(100.0, 90.0, 0.0)


# --- The instrument that is left ------------------------------------------


def test_flat_terrain_survives_as_a_test_instrument_and_says_so():
    """It is still the right tool for isolating one variable.

    What it is not is a description of anywhere, and its docstring is
    where that has to be said, because nothing else in the codebase
    reaches it any more.
    """
    assert flat_terrain(elevation_m=900.0).height_at(1e6, -1e6) == 900.0
    assert "laboratory" in flat_terrain.__doc__


# --- What a round is sized by ---------------------------------------------


def test_no_rural_link_fails_for_distance():
    """ADR-0022. Every rural failure is ground in the way, not range.

    The two look identical in the availability column and have opposite
    remedies: more masts fix distance, and nothing about spacing fixes a
    ridge. If this ever stops holding, the rural row's whole cost
    argument changes and somebody should have to notice.
    """
    import numpy as np

    from yerkon.rf import Terminal, evaluate_link

    deployed = CHOICES["rural"]
    deployment = deployed.scenario.deployment
    terrain = deployed.scenario.terrain
    unit = deployment.receivers[0]

    closed = blocked = out_of_range = 0
    for at_s in np.linspace(0.0, unit.journey.duration_s - 1.0, 40):
        here = unit.journey.position_at(float(at_s))
        for _, anchor, radio in deployment.nearest_to(unit, here):
            receiver = Terminal(radio, deployment.antenna, here)
            over_ground = evaluate_link(
                anchor, receiver,
                obstruction=terrain.obstruction_between(
                    anchor.position_m, receiver.position_m
                ),
                region=deployment.region,
            )
            if over_ground.closes:
                closed += 1
            elif evaluate_link(
                anchor, receiver, obstruction=None, region=deployment.region
            ).closes:
                blocked += 1
            else:
                out_of_range += 1

    assert closed and blocked, "this sample shows neither outcome"
    assert out_of_range == 0, (
        "{} rural links failed for distance; the row's remedy is no longer "
        "line of sight".format(out_of_range)
    )


def test_the_rural_round_polls_more_anchors_than_a_fix_needs():
    """ADR-0022. Eight attempts over blocked ground yield four replies.

    Which is exactly what a cold fix needs and nothing spare, and it is
    why the rural row sat in the low eighties. A round is sized by how
    many anchors answer, not by how many a position needs — and those are
    the same number only over ground that hides nothing.
    """
    rural = CHOICES["rural"].scenario.deployment
    assert rural.max_anchors_per_round >= 12

    # The other two rows poll almost nothing that fails, so a longer
    # round would buy them nothing and cost update rate.
    for name in ("urban", "tunnel"):
        assert CHOICES[name].scenario.deployment.max_anchors_per_round == 8


@pytest.mark.slow
def test_a_longer_rural_round_buys_availability_on_every_seed():
    """The check the neighbour list failed, applied to what replaced it.

    A change measured on one seed is a change measured on nothing: the
    ordering trick this replaced gave +2,57 points on the first seed it
    was tried on and −1,24 on the third. This one is positive on all of
    them, and the test says so rather than trusting the run that
    happened to be shipped.
    """
    from dataclasses import replace

    from yerkon.evaluate import run_scenario

    base = CHOICES["rural"].scenario
    for seed in (202, 404):
        longer = replace(base, seed=seed)
        shorter = replace(
            longer,
            deployment=replace(longer.deployment, max_anchors_per_round=8),
        )
        assert (
            run_scenario(longer).availability
            > run_scenario(shorter).availability
        ), seed
