"""Driving a receiver past a deployment and counting how wrong it was."""

import math

import numpy as np
import pytest

from yerkon.evaluate import (
    Coverage,
    Deployment,
    Journey,
    Samples,
    Scenario,
    combine,
    coverage,
    run_scenario,
)
from yerkon.world import (
    Anchor,
    Road,
    ROADSIDE_SIGN,
    TALL_MAST,
    flat_terrain,
    graded_alignment,
    rolling_terrain,
)

ROLLING = rolling_terrain(amplitude_m=40.0, wavelength_m=3000.0, micro_roughness_m=0.2)
CENTRELINE = [(float(x), 0.0) for x in range(0, 12_001, 500)]


def a_road(terrain=ROLLING):
    return Road(
        centreline_m=CENTRELINE,
        terrain=terrain,
        surface_m=graded_alignment(CENTRELINE, terrain),
    )


def anchors_every(spacing_m, terrain=ROLLING, mounting=TALL_MAST, length_m=12_000.0):
    return tuple(
        Anchor(
            "M{}".format(index),
            (float(x), 400.0 if index % 2 == 0 else -400.0),
            mounting,
            terrain,
        )
        for index, x in enumerate(np.arange(0.0, length_m + 1.0, spacing_m))
    )


def a_scenario(spacing_m=2000.0, duration_s=60.0, seed=1, terrain=ROLLING, **kwargs):
    return Scenario(
        name="test",
        terrain=terrain,
        deployment=Deployment(anchors=anchors_every(spacing_m, terrain)),
        journeys=(Journey(road=a_road(terrain), speed_m_s=27.8,
                          duration_s=duration_s),),
        seed=seed,
        **kwargs,
    )


# --- Journeys -------------------------------------------------------------


def test_a_receiver_climbs_with_the_road():
    """ADR-0004. No road in this codebase sits at a constant elevation."""
    journey = Journey(road=a_road(), speed_m_s=27.8, duration_s=300.0)
    heights = [journey.position_at(t)[2] for t in range(0, 300, 10)]
    assert max(heights) - min(heights) > 5.0


def test_a_receiver_stands_above_the_road_surface():
    road = a_road()
    journey = Journey(road=road, speed_m_s=0.0, duration_s=1.0,
                      antenna_height_m=1.5)
    assert journey.position_at(0.0)[2] == pytest.approx(
        road.surface_height_at(0.0) + 1.5
    )


def test_a_journey_stops_at_the_end_of_its_road_rather_than_running_off_it():
    journey = Journey(road=a_road(), speed_m_s=100.0, duration_s=10_000.0)
    far = journey.position_at(9_999.0)
    assert far[0] <= CENTRELINE[-1][0] + 1.0


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("speed_m_s", -1.0, "backwards"),
        ("duration_s", 0.0, "takes time"),
        ("antenna_height_m", 0.0, "above the road"),
    ],
)
def test_an_impossible_journey_is_refused(field, value, message):
    fields = dict(road=a_road(), speed_m_s=10.0, duration_s=10.0)
    fields[field] = value
    with pytest.raises(ValueError, match=message):
        Journey(**fields)


# --- Deployments ----------------------------------------------------------


def test_a_deployment_needs_anchors():
    with pytest.raises(ValueError, match="needs anchors"):
        Deployment(anchors=())


def test_two_anchors_cannot_share_an_identifier():
    """They would be indistinguishable in an observation."""
    one = anchors_every(4000.0)[0]
    with pytest.raises(ValueError, match="share an identifier"):
        Deployment(anchors=(one, one))


def test_a_round_takes_longer_with_more_anchors():
    few = Deployment(anchors=anchors_every(6000.0))
    many = Deployment(anchors=anchors_every(1500.0))
    assert many.round_duration_s > few.round_duration_s


def test_a_duty_limit_stretches_the_round():
    full = Deployment(anchors=anchors_every(4000.0))
    limited = Deployment(anchors=anchors_every(4000.0), duty_cycle=0.5)
    assert limited.round_duration_s == pytest.approx(2.0 * full.round_duration_s)


# --- Running --------------------------------------------------------------


def test_a_run_produces_fixes_and_counts_the_ones_it_did_not():
    samples = run_scenario(a_scenario())
    assert samples.produced > 10
    assert samples.attempted >= samples.produced
    assert 0.0 < samples.availability <= 1.0


def test_the_same_seed_gives_the_same_run():
    first = run_scenario(a_scenario(seed=5))
    again = run_scenario(a_scenario(seed=5))
    assert np.array_equal(first.horizontal_error_m, again.horizontal_error_m)


def test_a_different_seed_gives_a_different_run():
    first = run_scenario(a_scenario(seed=5))
    other = run_scenario(a_scenario(seed=6))
    assert not np.array_equal(first.horizontal_error_m, other.horizontal_error_m)


def test_one_run_does_not_contaminate_the_next():
    """The bug that invalidated every swept comparison in the old repository.

    A generator held across scenarios meant the second run in a process
    drew from wherever the first stopped, so a sweep measured the order
    of its own loop as much as the thing it varied.
    """
    first = run_scenario(a_scenario(seed=5))
    run_scenario(a_scenario(seed=99))
    third = run_scenario(a_scenario(seed=5))
    assert np.array_equal(first.horizontal_error_m, third.horizontal_error_m)


def test_closer_anchors_place_the_receiver_better():
    close = run_scenario(a_scenario(spacing_m=1500.0))
    sparse = run_scenario(a_scenario(spacing_m=4000.0))
    assert close.percentile(50)[0] < sparse.percentile(50)[0]


def test_the_vertical_stays_far_worse_than_the_horizontal():
    """ADR-0011. Roadside anchors cannot determine a height."""
    samples = run_scenario(a_scenario())
    horizontal, vertical = samples.percentile(50)
    assert vertical > 3.0 * horizontal


def test_a_measurement_too_poor_to_help_is_not_used():
    """A range with thirty metres of error drags a fix rather than fixing it."""
    strict = run_scenario(a_scenario(accept_sigma_m=4.0))
    loose = run_scenario(a_scenario(accept_sigma_m=1000.0))
    assert strict.produced <= loose.produced


def test_anchors_on_signs_serve_worse_than_anchors_on_masts():
    """Three metres of mounting height against twenty-five."""
    def scenario(mounting):
        return Scenario(
            name=mounting.kind,
            terrain=ROLLING,
            deployment=Deployment(anchors=anchors_every(4000.0, mounting=mounting)),
            journeys=(Journey(road=a_road(), speed_m_s=27.8, duration_s=60.0),),
            seed=2,
        )

    masts = run_scenario(scenario(TALL_MAST))
    signs = run_scenario(scenario(ROADSIDE_SIGN))
    assert signs.availability < masts.availability


def test_a_scenario_needs_a_journey():
    with pytest.raises(ValueError, match="at least one journey"):
        Scenario("empty", ROLLING, Deployment(anchors=anchors_every(4000.0)), ())


# --- Combining ------------------------------------------------------------


def made_up(name, horizontal, vertical=None, attempted=None):
    horizontal = np.asarray(horizontal, dtype=float)
    vertical = np.asarray(
        horizontal * 10.0 if vertical is None else vertical, dtype=float
    )
    return Samples(
        name=name,
        horizontal_error_m=horizontal,
        vertical_error_m=vertical,
        attempted=horizontal.size if attempted is None else attempted,
    )


def test_the_weighted_row_combines_samples_and_not_percentiles():
    """ADR-0005. Averaging three P95 values does not produce a P95.

    One scenario at a steady one metre and another with a long tail: the
    average of their ninety-fifth percentiles is not the ninety-fifth
    percentile of the pair, and this is the arrangement that shows it.
    """
    steady = made_up("steady", np.ones(1000))
    tailed = made_up("tailed", np.concatenate([np.ones(900), np.full(100, 50.0)]))

    average_of_percentiles = 0.5 * (
        steady.percentile(95)[0] + tailed.percentile(95)[0]
    )
    combined = combine([(steady, 0.5), (tailed, 0.5)], "weighted")

    assert combined.percentile(95)[0] != pytest.approx(
        average_of_percentiles, rel=0.05
    )


def test_a_heavier_weight_pulls_the_combination_toward_that_scenario():
    good = made_up("good", np.ones(500))
    bad = made_up("bad", np.full(500, 20.0))

    mostly_good = combine([(good, 0.9), (bad, 0.1)], "mostly good")
    mostly_bad = combine([(good, 0.1), (bad, 0.9)], "mostly bad")

    assert mostly_good.percentile(50)[0] < mostly_bad.percentile(50)[0]


def test_combining_carries_availability_across():
    half = made_up("half", np.ones(100), attempted=200)
    whole = made_up("whole", np.ones(100), attempted=100)
    combined = combine([(half, 0.5), (whole, 0.5)], "both")
    assert 0.6 < combined.availability < 0.8


def test_a_scenario_with_no_fixes_cannot_be_weighted_in():
    empty = made_up("empty", np.array([]))
    with pytest.raises(ValueError, match="no fixes"):
        combine([(empty, 1.0)], "impossible")


def test_combining_nothing_is_refused():
    with pytest.raises(ValueError, match="nothing to combine"):
        combine([], "empty")


def test_percentiles_of_an_empty_run_are_not_a_number():
    """Better than a zero, which would read as a perfect result."""
    horizontal, vertical = made_up("empty", np.array([])).percentile(50)
    assert math.isnan(horizontal) and math.isnan(vertical)


# --- Coverage -------------------------------------------------------------


def test_ground_a_packet_reaches_is_not_ground_a_receiver_can_be_placed_on():
    """The distinction the service area column turns on.

    One anchor in range means a packet arrives. Four means a position.
    On a corridor deployment the second area is a fraction of the first,
    and quoting the first as coverage overstates it several times over.
    """
    result = coverage(
        Deployment(anchors=anchors_every(4000.0)),
        ROLLING,
        resolution_m=1000.0,
        margin_m=6000.0,
    )
    assert isinstance(result, Coverage)
    assert result.fixable_km2 < result.reached_km2 / 2.0


def test_more_anchors_serve_more_ground():
    dense = coverage(
        Deployment(anchors=anchors_every(1500.0)), ROLLING,
        resolution_m=1000.0, margin_m=6000.0,
    )
    sparse = coverage(
        Deployment(anchors=anchors_every(4000.0)), ROLLING,
        resolution_m=1000.0, margin_m=6000.0,
    )
    assert dense.fixable_km2 > sparse.fixable_km2


def test_a_position_needs_four_ranges():
    with pytest.raises(ValueError, match="fewer than four"):
        coverage(
            Deployment(anchors=anchors_every(4000.0)), ROLLING,
            anchors_required=3,
        )
