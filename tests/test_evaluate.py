"""Driving a receiver past a deployment and counting how wrong it was."""

import math

import numpy as np
import pytest

from yerkon.evaluate import (
    Coverage,
    Deployment,
    Journey,
    Receiver,
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


def anchors_every(spacing_m, terrain=ROLLING, mounting=TALL_MAST,
                  length_m=12_000.0, radio=None):
    from yerkon.hardware import SX1280

    return tuple(
        Anchor(
            "M{}".format(index),
            (float(x), 400.0 if index % 2 == 0 else -400.0),
            mounting,
            terrain,
            radio=radio or SX1280,
        )
        for index, x in enumerate(np.arange(0.0, length_m + 1.0, spacing_m))
    )


def a_unit(identifier="araç", terrain=ROLLING, speed_m_s=27.8, duration_s=60.0,
           radios=None, **journey):
    from yerkon.hardware import DWM3000, SX1280

    return Receiver(
        identifier=identifier,
        journey=Journey(road=a_road(terrain), speed_m_s=speed_m_s,
                        duration_s=duration_s, **journey),
        radios=radios or (SX1280, DWM3000),
    )


def a_deployment(spacing_m=2000.0, terrain=ROLLING, mounting=TALL_MAST,
                 units=None, **kwargs):
    return Deployment(
        anchors=anchors_every(spacing_m, terrain, mounting),
        receivers=units if units is not None else (a_unit(terrain=terrain),),
        **kwargs,
    )


def a_scenario(spacing_m=2000.0, duration_s=60.0, seed=1, terrain=ROLLING,
               units=None, mounting=TALL_MAST, **kwargs):
    return Scenario(
        name="test",
        terrain=terrain,
        deployment=Deployment(
            anchors=anchors_every(spacing_m, terrain, mounting),
            receivers=units if units is not None
            else (a_unit(terrain=terrain, duration_s=duration_s),),
        ),
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
    few = a_deployment(6000.0)
    many = a_deployment(1500.0)
    assert many.round_duration_s() > few.round_duration_s()


def test_a_duty_limit_stretches_the_round():
    full = a_deployment(4000.0)
    limited = a_deployment(4000.0, duty_cycle=0.5)
    assert limited.round_duration_s() == pytest.approx(
        2.0 * full.round_duration_s()
    )


def test_a_second_unit_doubles_the_wait_rather_than_halving_the_work():
    """The medium is shared. Every unit queues at the same anchors."""
    one = a_deployment(2000.0, units=(a_unit("a"),))
    two = a_deployment(2000.0, units=(a_unit("a"), a_unit("b")))
    assert two.round_duration_s() == pytest.approx(2.0 * one.round_duration_s())


def test_a_unit_only_hears_anchors_it_shares_a_waveform_with():
    """A road unit carrying one module cannot range against a tunnel anchor."""
    from yerkon.hardware import DWM3000, SX1280

    mixed = anchors_every(4000.0) + tuple(
        Anchor("T{}".format(i), (float(i) * 200.0, 6.0), TALL_MAST, ROLLING,
               radio=DWM3000)
        for i in range(5)
    )
    spread_only = a_unit("spread", radios=(SX1280,))
    both = a_unit("both", radios=(SX1280, DWM3000))
    deployment = Deployment(anchors=mixed, receivers=(spread_only, both))

    assert len(deployment.anchors_heard_by(spread_only)) == len(
        anchors_every(4000.0)
    )
    assert len(deployment.anchors_heard_by(both)) == len(mixed)


def test_a_deployment_reports_the_waveforms_it_carries():
    """Two parts on the same silicon are one waveform, not two."""
    from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280

    spread = anchors_every(4000.0, radio=E28_2G4M27S)
    impulse = tuple(
        Anchor("T{}".format(i), (float(i) * 200.0, 6.0), TALL_MAST, ROLLING,
               radio=DWM3000)
        for i in range(3)
    )
    deployment = Deployment(
        anchors=spread + impulse, receivers=(a_unit(radios=(SX1280,)),)
    )
    assert len(deployment.radios()) == 2


def test_two_receivers_cannot_share_an_identifier():
    with pytest.raises(ValueError, match="two receivers share an identifier"):
        Deployment(anchors=anchors_every(4000.0),
                   receivers=(a_unit("a"), a_unit("a")))


def test_a_receiver_with_no_radio_hears_nothing_and_is_refused():
    with pytest.raises(ValueError, match="hears nothing"):
        Receiver(
            identifier="deaf",
            journey=Journey(road=a_road(), speed_m_s=10.0, duration_s=10.0),
            radios=(),
        )


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
    masts = run_scenario(a_scenario(spacing_m=4000.0, mounting=TALL_MAST, seed=2))
    signs = run_scenario(a_scenario(spacing_m=4000.0, mounting=ROADSIDE_SIGN, seed=2))
    assert signs.availability < masts.availability


def test_a_second_unit_splits_the_fixes_rather_than_adding_any():
    """The air is the constraint, not the number of vehicles.

    A second unit doubles the round, so half as many rounds fit in the
    same journey and each unit is fixed half as often. The deployment's
    total fix rate barely moves: it was already spending all its air.
    """
    one = run_scenario(a_scenario(units=(a_unit("a"),)))
    two = run_scenario(a_scenario(units=(a_unit("a"), a_unit("b"))))

    assert two.attempted == pytest.approx(one.attempted, rel=0.1)
    assert two.attempted_links == pytest.approx(one.attempted_links, rel=0.1)


def test_a_scenario_needs_a_receiver():
    with pytest.raises(ValueError, match="at least one receiver"):
        Scenario("empty", ROLLING, Deployment(anchors=anchors_every(4000.0)))


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
        a_deployment(4000.0),
        ROLLING,
        resolution_m=1000.0,
        margin_m=6000.0,
    )
    assert isinstance(result, Coverage)
    assert result.fixable_km2 < result.reached_km2 / 2.0


def test_more_anchors_serve_more_ground():
    dense = coverage(
        a_deployment(1500.0), ROLLING,
        resolution_m=1000.0, margin_m=6000.0,
    )
    sparse = coverage(
        a_deployment(4000.0), ROLLING,
        resolution_m=1000.0, margin_m=6000.0,
    )
    assert dense.fixable_km2 > sparse.fixable_km2


def test_a_position_needs_four_ranges():
    with pytest.raises(ValueError, match="fewer than four"):
        coverage(a_deployment(4000.0), ROLLING, anchors_required=3)


# --- Errors that do not average out ---------------------------------------


def precise_scenario(survey_sigma_m, seed=3):
    """A deployment whose ranging is good enough to see a survey error.

    An impulse radio ranges to a tenth of a metre, so what the anchors'
    own positions are worth stops being a rounding error and starts
    being the answer.
    """
    from yerkon.hardware import DWM3000

    terrain = flat_terrain(micro_roughness_m=0.05)
    centreline = [(float(x), 0.0) for x in range(0, 2001, 100)]
    road = Road(centreline_m=centreline, terrain=terrain)
    anchors = tuple(
        Anchor("T{}".format(index), (float(x), 4.0 if index % 2 else -4.0),
               TALL_MAST, terrain, radio=DWM3000)
        for index, x in enumerate(range(0, 2001, 150))
    )
    return Scenario(
        name="precise",
        terrain=terrain,
        deployment=Deployment(
            anchors=anchors,
            receivers=(
                Receiver(
                    "araç",
                    Journey(road=road, speed_m_s=15.0, duration_s=60.0),
                    radios=(DWM3000,),
                ),
            ),
        ),
        seed=seed,
        accept_sigma_m=2.0,
        anchor_survey_sigma_m=survey_sigma_m,
    )


def test_a_survey_error_puts_a_floor_under_the_horizontal_error():
    """You cannot position better than you surveyed the anchors.

    And the geometry amplifies it. Anchors lining a bore turn a tenth of
    a metre of survey error into metres of position error, for the same
    reason they leave the vertical unobservable (ADR-0019).
    """
    perfect = run_scenario(precise_scenario(0.0))
    surveyed = run_scenario(precise_scenario(0.30))
    assert surveyed.percentile(50)[0] > 3.0 * perfect.percentile(50)[0]


def test_the_floor_rises_with_the_survey_error_rather_than_saturating():
    """A bias is not something a filter averages away, however many
    measurements it takes."""
    small = run_scenario(precise_scenario(0.05)).percentile(50)[0]
    large = run_scenario(precise_scenario(0.40)).percentile(50)[0]
    assert large > small * 2.0


def test_a_survey_error_hides_under_a_noisier_radio():
    """Which is why it was invisible until the tunnel row got good.

    A spread radio ranges to about three metres, and a tenth of a metre
    of survey error disappears underneath that. The floor is real
    everywhere and only binding where the rest is better than it.
    """
    quiet = run_scenario(a_scenario(anchor_survey_sigma_m=0.0, seed=3))
    surveyed = run_scenario(a_scenario(anchor_survey_sigma_m=0.3, seed=3))
    assert surveyed.percentile(50)[0] == pytest.approx(
        quiet.percentile(50)[0], rel=0.5
    )


def test_lost_packets_cost_availability():
    """Interference and collisions are not in the link budget and are in
    the band, so they are counted here instead."""
    quiet = run_scenario(a_scenario(packet_loss=0.0))
    busy = run_scenario(a_scenario(packet_loss=0.4))
    assert busy.availability < quiet.availability
    assert busy.lost_links > quiet.lost_links


def test_a_survey_error_is_the_same_for_every_measurement_to_one_anchor():
    """Fixed at installation. If it were redrawn per exchange the filter
    would average it away and the floor would vanish, which is the whole
    error this models."""
    once = run_scenario(precise_scenario(0.4, seed=11))
    again = run_scenario(precise_scenario(0.4, seed=11))
    assert np.array_equal(once.horizontal_error_m, again.horizontal_error_m)
