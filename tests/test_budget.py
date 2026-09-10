"""Which error source made the position wrong, and by how much."""

import math

import pytest

from yerkon.budget import WEIGHTED, dissect, dissect_all
from yerkon.evaluate import Deployment, Journey, Receiver, Scenario, run_scenario
from yerkon.hardware import DWM3000, SX1280
from yerkon.ranging import (
    CRYSTAL,
    SINGLE_SIDED,
    measure,
    measurement_sigma_m,
    sigma_terms_m,
)
from yerkon.rf import Terminal, cramer_rao_sigma_m, evaluate_link
from yerkon.terms import ALL, LABELS, NAMES, REMEDIES, Terms
from yerkon.world import Anchor, Road, TALL_MAST, flat_terrain

import numpy as np

from yerkon.hardware import W24P_U


TERRAIN = flat_terrain(micro_roughness_m=0.05)


def a_scenario(seed=7, survey_sigma_m=0.0, packet_loss=0.0, duration_s=45.0):
    """A small, quick deployment with an impulse radio.

    Short enough to run sixteen times inside a test, and precise enough
    that a tenth of a metre of anything shows up rather than hiding under
    the ranging noise.
    """
    centreline = [(float(x), 0.0) for x in range(0, 1201, 100)]
    road = Road(centreline_m=centreline, terrain=TERRAIN)
    anchors = tuple(
        Anchor(
            "T{}".format(index),
            (float(x), 30.0 if index % 2 else -30.0),
            TALL_MAST,
            TERRAIN,
            radio=DWM3000,
        )
        for index, x in enumerate(range(0, 1201, 150))
    )
    return Scenario(
        name="deneme",
        terrain=TERRAIN,
        deployment=Deployment(
            anchors=anchors,
            receivers=(
                Receiver(
                    "araç",
                    Journey(road=road, speed_m_s=15.0, duration_s=duration_s),
                    radios=(DWM3000,),
                ),
            ),
        ),
        seed=seed,
        accept_sigma_m=2.0,
        anchor_survey_sigma_m=survey_sigma_m,
        packet_loss=packet_loss,
    )


# --- The split itself -----------------------------------------------------


def a_budget(distance_m=400.0, radio=DWM3000):
    anchor = Terminal(radio, W24P_U, (0.0, 0.0, 6.0))
    receiver = Terminal(radio, W24P_U, (distance_m, 0.0, 1.5))
    return evaluate_link(anchor, receiver), radio


#: Distances each radio actually closes at these antenna heights.
#:
#: Not a round number each: an impulse radio six metres up is spent well
#: inside a kilometre, and asking for its ranging precision beyond that
#: raises rather than returning a large number, which is the correct
#: behaviour and not something to test around.
CLOSES_AT = {DWM3000: (20.0, 50.0, 200.0), SX1280: (50.0, 200.0, 1000.0, 3000.0)}


@pytest.mark.parametrize(
    "radio,distance_m",
    [(radio, d) for radio, spread in CLOSES_AT.items() for d in spread],
)
def test_the_three_terms_reproduce_the_sigma_they_were_split_from(
    radio, distance_m
):
    """ADR-0020. Splitting the sigma must not have moved any published number.

    The floor is not a fourth error; it is whatever has to be added in
    quadrature to reach the measured floor, and zero where the physics is
    already above it. If that identity ever stops holding, every accuracy
    figure in the report moved without anybody asking.
    """
    budget, radio = a_budget(distance_m, radio)
    terms = sigma_terms_m(budget, radio, CRYSTAL, SINGLE_SIDED)

    waveform = cramer_rao_sigma_m(budget, radio)
    clock_m = terms["clock"]
    floor_m = float(radio.implementation_floor_m.value)
    expected = max(math.hypot(waveform, clock_m), floor_m)

    assert measurement_sigma_m(
        budget, radio, CRYSTAL, SINGLE_SIDED
    ) == pytest.approx(expected, rel=1e-12)


def test_the_floor_term_is_zero_where_the_physics_is_already_worse():
    """A part's floor is a limit on optimism, not an error of its own.

    Far enough out, the waveform bound alone exceeds what the bench
    measured, and the floor should stop contributing rather than piling
    on top of it.
    """
    near, radio = a_budget(20.0, SX1280)
    far, _ = a_budget(3000.0, SX1280)

    assert sigma_terms_m(near, radio)["floor"] > 0.0
    assert sigma_terms_m(far, radio)["floor"] == 0.0


# --- What a silenced source does, and does not, change --------------------


def test_silencing_a_source_does_not_change_what_the_receiver_believes():
    """ADR-0020. The variance stays whole so two runs stay comparable.

    A run that also narrowed the reported variance would retune the
    filter's gains, and the difference between two such runs would be
    partly the estimator adjusting to itself rather than the error under
    study.
    """
    radio = DWM3000
    anchor = Terminal(radio, W24P_U, (0.0, 0.0, 6.0))
    receiver = Terminal(radio, W24P_U, (300.0, 0.0, 1.5))

    whole = measure(anchor, receiver, 0.0, np.random.default_rng(1), terms=ALL)
    quiet = measure(
        anchor, receiver, 0.0, np.random.default_rng(1),
        terms=Terms.only("survey"),
    )
    assert whole.variance_m2 == pytest.approx(quiet.variance_m2)


def test_with_every_source_silenced_the_receiver_recovers_the_truth():
    """The residue is the model's own, and it should be nothing.

    This is the check that gives the rest of the dissection its meaning:
    if a run with no error sources still came out metres wrong, the
    difference between two dissected runs would be measuring that
    instead.
    """
    samples = run_scenario(a_scenario(), Terms.none())
    horizontal, vertical = samples.percentile(95)
    assert horizontal < 0.05
    assert vertical < 0.5


def test_a_source_that_is_not_there_costs_nothing():
    """Silencing a source the scenario never had must change no number.

    A survey error of zero and a packet loss of zero are the default. If
    switching them off moved the answer, the switch would be doing
    something other than what it says.
    """
    scenario = a_scenario(survey_sigma_m=0.0, packet_loss=0.0)
    whole = run_scenario(scenario, ALL).percentile(50)
    without = run_scenario(scenario, ALL.without("survey")).percentile(50)
    assert whole == pytest.approx(without)


def test_a_survey_error_is_the_only_thing_that_moves_when_only_it_is_live():
    """Isolation, checked from both sides.

    With every other source silenced, doubling the survey sigma should
    roughly double the error, because nothing else is in the way to
    absorb it.
    """
    small = run_scenario(a_scenario(survey_sigma_m=0.2), Terms.only("survey"))
    large = run_scenario(a_scenario(survey_sigma_m=0.4), Terms.only("survey"))
    ratio = large.percentile(50)[0] / small.percentile(50)[0]
    assert 1.7 < ratio < 2.3


# --- The dissection -------------------------------------------------------


def test_the_dissection_finds_the_source_that_was_planted():
    """A survey error large enough to dominate should come out dominant.

    Written from the arrangement rather than from a previous run's
    output: the scenario is built with a survey error twenty times the
    module's own floor, so anything but `survey` at the top would mean
    the isolation is not isolating.
    """
    dissection = dissect(_deployed(a_scenario(survey_sigma_m=2.0)))
    assert dissection.ranked()[0].source == "survey"
    assert dissection.dominant() is not None
    assert dissection.dominant().source == "survey"


def test_removing_the_dominant_source_saves_less_than_it_is_worth_alone():
    """Errors add in quadrature, which is the whole reason for two columns.

    Taking 0,5 m out of a 2,0 m total leaves 1,94 m, so the metres a
    purchase actually buys are always fewer than the source is worth on
    its own. A report that printed only the alone figure would oversell
    every improvement it recommended.
    """
    dissection = dissect(_deployed(a_scenario(survey_sigma_m=0.5)))
    dominant = dissection.dominant()
    assert dominant is not None
    assert 0.0 < dominant.saves_m(dissection.whole_p50_m) < dominant.alone_p50_m


def test_no_source_moves_the_answer_by_more_than_it_is_worth_or_by_noise():
    """The bound, with the run's own seed spread as the tolerance.

    Silencing a source redraws every subsequent random number, so a
    source worth nothing can still shift the fiftieth percentile by a
    centimetre or two. That shift is not a contribution and must not be
    mistaken for one, so this measures it — two whole runs at different
    seeds — rather than picking a tolerance out of the air.

    One source genuinely breaks the quadrature bound: `motion` is worth
    nothing on its own, because ranges taken from several points along a
    known path are perfectly consistent when they carry no error. It
    only does damage in company, by making *noisy* ranges disagree. That
    is a coupling term, not an independent error, and it is why the
    alone column is a reading rather than a share of a total.
    """
    scenario = a_scenario(survey_sigma_m=0.5)
    spread = abs(
        run_scenario(scenario, ALL).percentile(50)[0]
        - run_scenario(a_scenario(seed=8, survey_sigma_m=0.5), ALL).percentile(50)[0]
    )
    assert spread > 0.0, "two seeds gave identical percentiles; nothing is random"

    dissection = dissect(_deployed(scenario))
    for contribution in dissection.contributions:
        assert abs(contribution.saves_m(dissection.whole_p50_m)) <= max(
            contribution.alone_p50_m, spread
        ), contribution.source


def test_nothing_is_called_dominant_when_two_sources_are_close():
    """Two sources within a quarter of each other are a choice, not a ranking.

    Naming a winner between them would read as a finding when it is seed
    noise, so the dissection declines to name one.
    """
    dissection = dissect(_deployed(a_scenario(survey_sigma_m=0.0)))
    ranked = dissection.ranked()
    if ranked[1].alone_p50_m > 0.75 * ranked[0].alone_p50_m:
        assert dissection.dominant() is None
    else:
        assert dissection.dominant() is ranked[0]


def test_the_geometry_multiplier_is_the_position_error_over_a_range_error():
    """It answers "more anchors, or better anchors?" and nothing else."""
    dissection = dissect(_deployed(a_scenario()))
    assert dissection.range_sigma_m > 0.0
    assert dissection.geometry_gain == pytest.approx(
        dissection.whole_p50_m / dissection.range_sigma_m
    )


def test_every_source_has_a_name_and_something_to_do_about_it():
    """A contribution nobody can act on is the thing this module exists to fix."""
    for name in NAMES:
        assert LABELS[name].strip()
        assert REMEDIES[name].strip()


def test_asking_for_a_source_that_does_not_exist_says_so():
    with pytest.raises(ValueError, match="no error source called"):
        Terms.only("gremlins")


def test_only_leaves_one_source_live_and_without_leaves_the_rest():
    for name in NAMES:
        alone = Terms.only(name)
        assert getattr(alone, name)
        assert sum(getattr(alone, other) for other in NAMES) == 1

        rest = ALL.without(name)
        assert not getattr(rest, name)
        assert sum(getattr(rest, other) for other in NAMES) == len(NAMES) - 1


@pytest.mark.slow
def test_several_scenarios_get_a_weighted_row_built_from_their_samples():
    """ADR-0005 again: combined from raw samples, never from percentiles.

    A weighted row whose fiftieth percentile fell outside the range of
    the three it combines would be arithmetic on percentiles, which is
    what ADR-0005 forbids.
    """
    deployments = (
        _deployed(a_scenario(seed=11, survey_sigma_m=0.0), weight=0.7),
        _deployed(a_scenario(seed=12, survey_sigma_m=1.5), weight=0.3),
    )
    dissections = dissect_all(deployments, sources=("survey", "floor"))

    assert len(dissections) == 3
    assert dissections[-1].name == WEIGHTED
    each = [d.whole_p50_m for d in dissections[:-1]]
    assert min(each) <= dissections[-1].whole_p50_m <= max(each)


def _deployed(scenario, weight=1.0):
    """The scenario wrapped in the bill of materials the report pairs it with.

    The dissection only reads the scenario and the weight; the costing is
    the table's business and not this module's.
    """
    from yerkon.cost import TUNNEL_ANCHOR
    from yerkon.scenarios import Deployed

    return Deployed(
        scenario=scenario,
        product=TUNNEL_ANCHOR,
        mounting=TALL_MAST,
        route_km=1.2,
        weight=weight,
        environment="Dış",
        technology="deneme",
    )
