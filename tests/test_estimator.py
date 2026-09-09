"""Ranges into positions, seeing nothing else. See ADR-0003 and ADR-0010."""

import math

import numpy as np
import pytest

from yerkon.estimator import (
    DEFAULT_MANOEUVRE_M_S2,
    Fix,
    TrackingFilter,
    track,
    trilaterate,
)
from yerkon.observation import RangeObservation

#: Anchors as a road puts them: spread out sideways, all at one height.
ROADSIDE = [
    (0.0, 0.0, 25.0),
    (4000.0, 0.0, 25.0),
    (2000.0, 2500.0, 25.0),
    (6000.0, 1800.0, 25.0),
    (1000.0, -2200.0, 25.0),
    (5000.0, -2600.0, 25.0),
]

SIGMA_M = 2.94


def ranges_to(truth_m, anchors=ROADSIDE, sigma_m=SIGMA_M, rng=None, start_s=0.0,
              slot_s=0.0479):
    """One round of ranges to a receiver standing at truth_m."""
    truth = np.array(truth_m, dtype=float)
    observations = []
    for index, anchor in enumerate(anchors):
        distance = float(np.linalg.norm(truth - np.array(anchor)))
        error = 0.0 if rng is None else float(rng.normal(0.0, sigma_m))
        observations.append(
            RangeObservation(
                at_s=start_s + index * slot_s,
                anchor_position_m=anchor,
                measured_range_m=max(distance + error, 0.0),
                variance_m2=sigma_m ** 2,
                anchor_id="A{}".format(index),
            )
        )
    return observations


# --- A first position -----------------------------------------------------


def test_three_ranges_cannot_place_a_point_in_three_axes():
    """And these anchors are nearly coplanar, so the reflection is real."""
    assert trilaterate(ranges_to((2500.0, 500.0, 1.5))[:3]) is None


def test_clean_ranges_recover_the_position_they_came_from():
    fix = trilaterate(ranges_to((2500.0, 500.0, 1.5)))
    assert fix is not None
    assert fix.position_m[0] == pytest.approx(2500.0, abs=0.1)
    assert fix.position_m[1] == pytest.approx(500.0, abs=0.1)
    assert fix.position_m[2] == pytest.approx(1.5, abs=0.5)


def test_a_fix_counts_the_measurements_behind_it():
    fix = trilaterate(ranges_to((2500.0, 500.0, 1.5)))
    assert fix.used == len(ROADSIDE)


def test_the_vertical_is_far_worse_than_the_horizontal():
    """The consequence of leaving the height unconstrained, as chosen.

    Anchors along a road sit at one height, so the vertical is nearly
    unobservable. Telling the filter the answer would hide that; this
    project reports it instead.
    """
    rng = np.random.default_rng(3)
    fix = trilaterate(ranges_to((2500.0, 500.0, 1.5), rng=rng))
    assert fix.vertical_sigma_m > 5.0 * fix.horizontal_sigma_m


def test_a_horizontal_axis_nothing_determines_is_a_failed_fix():
    """Least squares on hopeless geometry returns a point, not an error.

    Anchors in a straight line say nothing about which side of the line
    the receiver is on. The solve still produces a position, with a
    variance saying the position means nothing, and that is an outage
    rather than a fix.
    """
    collinear = [(x, 0.0, 25.0) for x in (0.0, 10.0, 20.0, 30.0, 40.0)]
    observations = [
        RangeObservation(0.0, anchor, 1.0, SIGMA_M ** 2)
        for anchor in collinear
    ]
    assert trilaterate(observations) is None


def test_an_unobservable_height_is_a_large_error_and_not_an_outage():
    """The two failures are not the same and must not be counted alike.

    Roadside anchors leave the vertical unobservable at kilometre ranges
    however their mounting heights are mixed: twenty metres of height
    against four kilometres of baseline is no spread at all. The right
    answer is a fix with a bad VPE, not a missing fix.
    """
    mixed_heights = [
        (0.0, 0.0, 25.0), (4000.0, 0.0, 3.0), (2000.0, 2500.0, 25.0),
        (6000.0, 1800.0, 6.0), (1000.0, -2200.0, 25.0), (5000.0, -2600.0, 10.0),
    ]
    fix = trilaterate(
        ranges_to((2500.0, 500.0, 1.5), anchors=mixed_heights,
                  rng=np.random.default_rng(4))
    )
    assert fix is not None
    assert fix.horizontal_sigma_m < 10.0
    assert fix.vertical_sigma_m > 10.0


def test_an_estimate_sitting_on_an_anchor_is_refused_rather_than_dividing_by_zero():
    anchors = ROADSIDE[:4]
    observations = [
        RangeObservation(0.0, anchor, 0.0, SIGMA_M ** 2) for anchor in anchors
    ]
    assert trilaterate(observations, guess_m=anchors[0]) is None


# --- Carrying it through time ---------------------------------------------


def a_filter(at_m=(2500.0, 500.0, 1.5)):
    return TrackingFilter(trilaterate(ranges_to(at_m)))


def test_a_filter_that_expects_no_surprises_is_refused():
    with pytest.raises(ValueError, match="ignores its inputs"):
        TrackingFilter(trilaterate(ranges_to((2500.0, 500.0, 1.5))),
                       manoeuvre_m_s2=0.0)


def test_coasting_makes_the_estimate_less_certain_not_more():
    filter_ = a_filter()
    now = filter_.fix()
    later = filter_.fix_at(now.at_s + 2.0)
    assert later.horizontal_sigma_m > now.horizontal_sigma_m


def test_the_covariance_stays_a_covariance_over_thousands_of_updates():
    """The short Kalman form drifts asymmetric and eventually negative.

    This filter takes one scalar update per range and a journey is
    thousands of them, so it uses the Joseph form.
    """
    rng = np.random.default_rng(9)
    filter_ = a_filter()
    for round_index in range(300):
        for observation in ranges_to(
            (2500.0, 500.0, 1.5), rng=rng, start_s=round_index * 0.3
        ):
            filter_.absorb(observation)

    covariance = filter_.covariance
    assert np.allclose(covariance, covariance.T, atol=1e-6)
    assert np.all(np.linalg.eigvalsh(covariance) > 0.0)


def test_a_range_from_the_past_does_not_wind_the_clock_back():
    filter_ = a_filter()
    filter_.absorb(ranges_to((2500.0, 500.0, 1.5), start_s=10.0)[0])
    at_s = filter_.at_s
    filter_.absorb(ranges_to((2500.0, 500.0, 1.5), start_s=1.0)[0])
    assert filter_.at_s <= at_s or filter_.at_s == pytest.approx(1.0)


def test_measurements_move_the_estimate_toward_where_they_say_it_is():
    rng = np.random.default_rng(12)
    truth = (2500.0, 500.0, 1.5)
    filter_ = TrackingFilter(
        Fix(0.0, (2560.0, 540.0, 1.5), np.eye(3) * 400.0, 4)
    )

    before = math.dist(filter_.position_m[:2], truth[:2])
    for round_index in range(20):
        for observation in ranges_to(truth, rng=rng, start_s=round_index * 0.3):
            filter_.absorb(observation)
    after = math.dist(filter_.position_m[:2], truth[:2])

    assert after < before / 10.0


# --- A whole journey ------------------------------------------------------


def journey(rng, speed_m_s=27.8, rounds=40, slot_s=0.0479):
    """A receiver driving past the anchors, ranged round after round."""
    def truth_at(at_s):
        return (1500.0 + speed_m_s * at_s, 300.0, 1.5)

    observations = []
    start_s = 0.0
    for _ in range(rounds):
        for index, anchor in enumerate(ROADSIDE):
            at_s = start_s + index * slot_s
            observations.extend(
                ranges_to(truth_at(at_s), anchors=[anchor], rng=rng,
                          start_s=at_s, slot_s=0.0)
            )
        start_s += len(ROADSIDE) * slot_s
    return observations, truth_at


def errors(fixes, truth_at, skip=20):
    horizontal, vertical = [], []
    for fix in fixes[skip:]:
        truth = truth_at(fix.at_s)
        horizontal.append(math.dist(fix.position_m[:2], truth[:2]))
        vertical.append(abs(fix.position_m[2] - truth[2]))
    return np.array(horizontal), np.array(vertical)


def test_a_filter_beats_solving_each_round_as_though_it_were_simultaneous():
    """The payoff ADR-0010 predicted, measured.

    A round takes 287 ms and the vehicle covers eight metres in it. A
    snapshot solve blames that motion on the ranges; the filter knows the
    measurements happened at different times and does not.
    """
    rng = np.random.default_rng(20)
    observations, truth_at = journey(rng)

    filtered, _ = errors(track(observations, round_size=len(ROADSIDE)), truth_at)

    snapshots = []
    for start in range(0, len(observations) - len(ROADSIDE), len(ROADSIDE)):
        fix = trilaterate(observations[start:start + len(ROADSIDE)])
        if fix is not None:
            snapshots.append(fix)
    snapped, _ = errors(snapshots, truth_at, skip=3)

    assert np.median(filtered) < np.median(snapped) / 2.0


def test_a_moving_receiver_is_tracked_to_metres_horizontally():
    rng = np.random.default_rng(20)
    observations, truth_at = journey(rng)
    horizontal, vertical = errors(
        track(observations, round_size=len(ROADSIDE)), truth_at
    )

    assert np.percentile(horizontal, 95) < 10.0
    assert np.percentile(vertical, 95) > 3.0 * np.percentile(horizontal, 95), (
        "the unconstrained vertical must stay visibly worse"
    )


def test_the_same_observations_give_the_same_track():
    rng = np.random.default_rng(31)
    observations, _ = journey(rng, rounds=5)
    first = track(observations, round_size=len(ROADSIDE))
    again = track(observations, round_size=len(ROADSIDE))
    assert [f.position_m for f in first] == [f.position_m for f in again]


def test_ranges_are_used_in_time_order_however_they_arrive():
    rng = np.random.default_rng(31)
    observations, _ = journey(rng, rounds=5)
    shuffled = list(observations)
    np.random.default_rng(0).shuffle(shuffled)

    assert [f.at_s for f in track(shuffled, round_size=len(ROADSIDE))] == [
        f.at_s for f in track(observations, round_size=len(ROADSIDE))
    ]


def test_a_journey_that_never_gets_a_first_fix_produces_no_track():
    """A refusal is a result. It is what the availability column counts."""
    assert track([], round_size=4) == ()
    assert track(ranges_to((2500.0, 500.0, 1.5))[:2], round_size=4) == ()


def test_asking_for_a_fix_from_three_ranges_is_refused_up_front():
    with pytest.raises(ValueError, match="three axes"):
        track([], round_size=3)


def test_the_filter_does_not_claim_to_be_better_than_it_is():
    """A filter whose covariance is far under its real error is lying.

    Not a calibration proof, which needs many runs. It catches the case
    where the covariance collapses and the filter stops listening.
    """
    rng = np.random.default_rng(20)
    observations, truth_at = journey(rng)
    fixes = track(observations, round_size=len(ROADSIDE))
    horizontal, _ = errors(fixes, truth_at)

    claimed = np.median([f.horizontal_sigma_m for f in fixes[20:]])
    assert claimed > np.percentile(horizontal, 50) / 3.0
