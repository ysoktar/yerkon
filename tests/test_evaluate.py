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
    coverage,
    run_scenario,
)
from yerkon.world import (
    Anchor,
    Road,
    ROADSIDE_SIGN,
    TALL_MAST,
    TUNNEL_BRACKET,
    flat_terrain,
    graded_alignment,
    rolling_terrain,
)

ROLLING = rolling_terrain(amplitude_m=40.0, wavelength_m=3000.0, micro_roughness_m=0.2)

#: Ground a deployment actually works over, for the claims that are not
#: about terrain.
#:
#: `ROLLING` is forty metres of hill every three kilometres, which since
#: diffraction is counted over the whole profile rather than over its
#: worst single point (ADR-0053) leaves about half the rounds without
#: the four ranges a fix needs — a receiver in one trough cannot see out
#: of it. That is a fair thing to measure and a useless place to measure
#: anything else from: a claim about survey error or packet loss cannot
#: be seen through a deployment that is already failing for another
#: reason. This is the same hill a quarter as tall.
GENTLE = rolling_terrain(amplitude_m=10.0, wavelength_m=3000.0,
                         micro_roughness_m=0.2)
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

    from yerkon.hardware import HGV_2409U

    # The vehicle's roof antenna, as the open-country row fits (ADR-0091).
    return Receiver(
        identifier=identifier,
        journey=Journey(road=a_road(terrain), speed_m_s=speed_m_s,
                        duration_s=duration_s, **journey),
        radios=radios or (SX1280, DWM3000),
        antenna=HGV_2409U,
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
    from yerkon.hardware import TL_ANT2412D

    return Scenario(
        name="test",
        terrain=terrain,
        deployment=Deployment(
            # The pole antenna the open-country row fits (ADR-0091).
            antenna=TL_ANT2412D,
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
    """And past some spacing they do not place it at all.

    Since diffraction is worked out over the whole profile rather than
    over its worst single point (ADR-0053), four kilometres of spacing
    over this rolling terrain produces no fix whatsoever: every link is
    behind a hill. That is not a missing answer, it is the strongest
    form of the answer this test is about, so it is scored as worse than
    any error rather than compared against as a number. NaN is not less
    than anything, including itself.

    The claim is about a wide gap and not about each step, because the
    walk from one spacing to the next is not monotone. Median error over
    eight seeds:

        aralık    1000   1500   2000   2500   3000
        ortanca   2,01   2,52   5,45    yok   6,87

    Nothing is placed at 2500 m on any of the eight, and something is
    placed again at 3000 m on all eight. That is this fixture's ground
    rather than a fact about spacing: `ROLLING` has one hill wavelength,
    3000 m, so a 3000 m spacing puts every anchor at the same point on
    the hill and a 2500 m spacing spreads them over five different
    points, some of them troughs. An earlier version of this test
    asserted the step-by-step order and passed on one arrangement.
    """
    def worst_of(samples):
        median = samples.percentile(50)[0]
        return median if math.isfinite(median) else math.inf

    close = run_scenario(a_scenario(spacing_m=1500.0))
    sparse = run_scenario(a_scenario(spacing_m=4000.0))
    assert worst_of(close) < worst_of(sparse)
    assert math.isfinite(worst_of(close)), "the close one still works"

    # The gap that survives the arrangement: a kilometre apart against
    # three. On the eight seeds the near one wins every time, by 2,0 m
    # against 6,9 m on the median, and by 1,75 against 6,64 on this one.
    near = worst_of(run_scenario(a_scenario(spacing_m=1000.0)))
    far = worst_of(run_scenario(a_scenario(spacing_m=3000.0)))
    assert near < far / 2.0, (near, far)


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
    """Three metres of mounting height against twenty-five.

    Two kilometres of spacing rather than four: over forty-metre hills
    with diffraction counted along the whole profile (ADR-0053), four
    kilometres leaves neither mounting with a single fix, and nothing is
    worse than nothing. At two the masts still serve and the signs do
    not, which is the claim.
    """
    masts = run_scenario(a_scenario(spacing_m=2000.0, mounting=TALL_MAST, seed=2))
    signs = run_scenario(a_scenario(spacing_m=2000.0, mounting=ROADSIDE_SIGN, seed=2))
    assert signs.availability < masts.availability
    assert masts.availability > 0.0, "the taller mounting has to work here"


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
               TUNNEL_BRACKET, terrain, radio=DWM3000)
        for index, x in enumerate(range(0, 2001, 40))
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


def test_a_survey_error_does_not_hide_where_the_geometry_amplifies_it():
    """The two errors do not meet on equal terms, and this is a corridor.

    Ranging noise is zero-mean, so a filter running across many rounds
    averages it down. A survey error is fixed at installation, so it does
    not average at all — and a corridor multiplies what it does not
    average (ADR-0019, ADR-0020). Thirty centimetres of it therefore
    shows straight through a radio that ranges to nearly eight metres.

    This used to assert the opposite: that a small survey error hides
    under a noisy radio. That is true where the geometry does not
    amplify — an area, where the multiplier is under one — and false
    here, which is the whole reason the tunnel row is the least accurate
    in the study despite the best hardware.
    """
    import statistics

    def over_twelve_journeys(sigma_m):
        return statistics.median(
            run_scenario(a_scenario(terrain=GENTLE, anchor_survey_sigma_m=sigma_m,
                                    seed=seed, duration_s=180.0)
                         ).percentile(50)[0]
            for seed in range(1, 13)
        )

    ranging = run_scenario(a_scenario(terrain=GENTLE)).median_range_sigma_m
    assert ranging > 2.0, (
        "the survey error is meant to compete against real ranging noise, "
        "and this radio ranges to {:.2f} m".format(ranging))

    none, small, large = (over_twelve_journeys(0.0), over_twelve_journeys(0.3),
                          over_twelve_journeys(1.0))
    assert none < small < large, (none, small, large)
    assert large > none * 1.2, (
        "a metre of survey error should show plainly: {:.2f} m against "
        "{:.2f} m".format(large, none))


def test_lost_packets_are_absorbed_until_suddenly_they_are_not():
    """Interference and collisions are not in the link budget and are in
    the band, so they are counted here instead.

    They do not cost availability smoothly. A round attempts several
    ranges and a running filter survives on one, so losing four in ten
    costs nothing at all — the same redundancy that lets the urban row
    lose 27 % of its exchanges and still fix every round. Past that the
    margin runs out and it collapses: seven in ten halves availability,
    nine in ten leaves none.

    Written as the shape of the curve rather than as one comparison,
    because the old version asserted that 40 % loss costs availability
    and it does not — it was passing on a scenario whose links were
    marginal for an unrelated reason.
    """
    absorbed = run_scenario(a_scenario(terrain=GENTLE, packet_loss=0.4))
    quiet = run_scenario(a_scenario(terrain=GENTLE, packet_loss=0.0))
    strained = run_scenario(a_scenario(terrain=GENTLE, packet_loss=0.7))
    swamped = run_scenario(a_scenario(terrain=GENTLE, packet_loss=0.9))

    assert absorbed.lost_links > quiet.lost_links, "the losses are real"
    # Nearly all of it, rather than exactly all: a round attempts several
    # ranges and a running filter survives on one, so four in ten costs
    # about a point of availability where seven in ten costs half of it.
    assert absorbed.availability > quiet.availability * 0.95, (
        "four in ten should be absorbed by the redundancy in a round: "
        "{:.3f} against {:.3f}".format(absorbed.availability,
                                       quiet.availability)
    )
    assert strained.availability < quiet.availability / 1.5
    assert swamped.availability < 0.05


def test_a_survey_error_is_the_same_for_every_measurement_to_one_anchor():
    """Fixed at installation. If it were redrawn per exchange the filter
    would average it away and the floor would vanish, which is the whole
    error this models."""
    once = run_scenario(precise_scenario(0.4, seed=11))
    again = run_scenario(precise_scenario(0.4, seed=11))
    assert np.array_equal(once.horizontal_error_m, again.horizontal_error_m)


def test_the_coverage_sweep_stops_where_the_measurement_stops():
    """ADR-0037, applied to the column it decides.

    The sweep runs a margin past the anchors so ground reached from the
    edge ones is counted. Over measured ground that margin runs off the
    grid, and past the grid `height_at` clamps — cells of served ground
    nobody surveyed. The urban row reported 31,72 km² of service over a
    site 8,73 km² in size.
    """
    import numpy as np

    from yerkon.evaluate import coverage_grid
    from yerkon.scenarios import catalogue
    from yerkon.settings import DEFAULTS

    deployed = catalogue(DEFAULTS)["urban"]
    terrain = deployed.scenario.terrain
    assert terrain.extent_m is not None, "the urban row stands on a fetch"
    left, bottom, right, top = terrain.extent_m

    grid = coverage_grid(
        deployed.scenario.deployment, terrain,
        resolution_m=500.0, margin_m=12_000.0, count_up_to=1,
    )
    assert grid.xs.min() >= left and grid.xs.max() <= right
    assert grid.ys.min() >= bottom and grid.ys.max() <= top


def test_modelled_ground_has_no_edge_for_the_sweep_to_stop_at():
    """It is a function, not a grid, so it answers everywhere."""
    from yerkon.world import rolling_terrain

    assert rolling_terrain(amplitude_m=40.0, wavelength_m=800.0).extent_m is None


# --- One run is one draw (ADR-0055) ---------------------------------------


def test_a_percentile_is_taken_over_the_population_not_over_percentiles():
    """The same refusal this project already makes for the weighted row
    (ADR-0005), applied to draws of one row.

    Shadowing makes a run one arrangement of the vans and hedges the
    model does not carry. Over eight of them the rural row's ninety-fifth
    percentile came out anywhere between 14,6 m and 279,6 m, because at
    that availability the surviving fixes are few and a percentile is a
    tail. Averaging eight tails is not a tail of anything.
    """
    from yerkon.evaluate import Samples, pooled

    def draw(name, errors):
        return Samples(name=name,
                       horizontal_error_m=np.array(errors, dtype=float),
                       vertical_error_m=np.array(errors, dtype=float) * 2.0,
                       attempted=len(errors) * 2, lost_links=1,
                       attempted_links=10, median_range_sigma_m=3.0)

    quiet = [draw("a", list(range(1, 101))) for _ in range(7)]
    wild = draw("b", list(range(1, 100)) + [5000.0])
    together = pooled(quiet + [wild], "pooled")

    averaged = sum(d.percentile(95)[0] for d in quiet + [wild]) / 8
    assert together.percentile(95)[0] < averaged, (
        "one wild draw must not drag the answer by an eighth of its tail")
    assert together.produced == 800
    assert together.attempted == 8 * 200
    assert together.lost_links == 8 and together.attempted_links == 80
    # Availability pools too, because it is the same question asked of
    # more attempts.
    assert together.availability == pytest.approx(quiet[0].availability)


def test_one_draw_pools_to_itself():
    """So that nothing changes for a caller that asks for no pooling."""
    from yerkon.evaluate import pooled

    alone = run_scenario(a_scenario(terrain=GENTLE))
    same = pooled([alone], "alone")
    assert np.array_equal(same.horizontal_error_m, alone.horizontal_error_m)
    assert same.attempted == alone.attempted


def test_a_row_is_run_over_the_arrangements_of_shadows_it_asks_for():
    """Seeds running upward from the one the settings name, so the first
    draw is the arrangement a single run would have used."""
    from dataclasses import replace

    from yerkon.report import draws_of
    from yerkon.scenarios import CHOICES

    urban = CHOICES["urban"]
    assert urban.shadow_draws > 1, "the shipped rows pool"
    drawn = draws_of(urban)
    assert len(drawn) == urban.shadow_draws
    seeds = [one.terrain.shadowing.seed for one in drawn]
    assert seeds == sorted(seeds) and len(set(seeds)) == len(seeds)
    assert seeds[0] == urban.scenario.terrain.shadowing.seed

    # And `run` takes one of them rather than all of them: the pooling
    # is the report's, because a simulation is one arrangement.
    from yerkon.report import run
    assert run.__defaults__[1] == 0, "run is one draw by default"

    # Nothing to draw from, nothing drawn.
    assert len(draws_of(replace(urban, shadow_draws=1))) == 1
    unshadowed = replace(urban, scenario=replace(
        urban.scenario, terrain=replace(urban.scenario.terrain,
                                        shadowing=None)))
    assert len(draws_of(unshadowed)) == 1


def test_the_vehicle_reply_is_held_only_toward_anchors_above_it():
    """ETSI EN 302 065-3, 4.3.4.2: the plane is the device's own mounting
    height, and it moves with the vehicle, so the gradient does not
    count: only the heights above the road do."""
    from yerkon.evaluate import _reply_ceiling_dbm
    from yerkon.hardware import DWM3000, SX1280
    from yerkon.scenarios import catalogue
    from yerkon.settings import DEFAULTS

    deployment = catalogue(DEFAULTS)["tunnel"].scenario.deployment
    vehicle = next(u for u in deployment.receivers if u.product == "vehicle")
    walker = next(u for u in deployment.receivers if u.product == "pedestrian")

    assert _reply_ceiling_dbm(vehicle, 4.5, DWM3000) is not None
    assert _reply_ceiling_dbm(vehicle, 1.2, DWM3000) is None
    assert _reply_ceiling_dbm(walker, 4.5, DWM3000) is None
    assert _reply_ceiling_dbm(vehicle, 4.5, SX1280) is None
