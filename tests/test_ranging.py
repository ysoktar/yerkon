"""Two-way ranging: the exchange, its clocks, and what it costs in time."""

import math

import numpy as np
import pytest

from yerkon.evidence import Provenance
from yerkon.hardware import DWM3000, SPEED_OF_LIGHT_M_S, SX1280, W24P_U
from yerkon.observation import RangeObservation
from yerkon.ranging import (
    CRYSTAL,
    DOUBLE_SIDED,
    SINGLE_SIDED,
    TCXO,
    Clock,
    exchange_duration_s,
    frame_duration_s,
    measure,
    measurement_sigma_m,
    ranges_per_second,
    reply_delay_s,
    round_robin,
)
from yerkon.rf import Terminal, evaluate_link


def budget_at(distance_m, radio=SX1280, anchor_height_m=25.0):
    anchor = Terminal(radio, W24P_U, (0.0, 0.0, anchor_height_m))
    receiver = Terminal(radio, W24P_U, (distance_m, 0.0, 1.5))
    return evaluate_link(anchor, receiver)


# --- Clocks ---------------------------------------------------------------


def test_correcting_a_clock_cannot_leave_it_worse_than_it_started():
    with pytest.raises(ValueError, match="further out than it started"):
        Clock("bad", CRYSTAL.residual_ppm, CRYSTAL.tolerance_ppm)


def test_an_uncorrected_clock_is_the_one_the_crystal_specifies():
    """The corrected figure is measured now and the raw one is not."""
    assert CRYSTAL.offset_ppm(corrected=False) == 10.0
    assert CRYSTAL.offset_ppm(corrected=True) < 1.0
    assert CRYSTAL.residual_ppm.provenance is not Provenance.ASSUMPTION


# --- What the clocks do to a range ---------------------------------------


def test_single_sided_ranging_multiplies_the_reply_delay():
    """A frame long, on a slow radio, is where this error comes from."""
    reply_s = reply_delay_s(SX1280)
    error_s = SINGLE_SIDED.clock_error_s(reply_s, 0.0, offset_ppm=10.0)
    assert error_s == pytest.approx(0.5 * 10e-6 * reply_s)
    assert error_s * SPEED_OF_LIGHT_M_S > 20.0, "twenty metres, from the clock alone"


def test_double_sided_ranging_multiplies_the_flight_time_instead():
    """A ten kilometre flight is thirty-three microseconds. The reply is
    sixteen milliseconds. Swapping which one carries the offset is worth
    a factor of a couple of hundred, at the longest link in the study."""
    reply_s = reply_delay_s(SX1280)
    flight_s = 10_000.0 / SPEED_OF_LIGHT_M_S

    single = SINGLE_SIDED.clock_error_s(reply_s, flight_s, 10.0)
    double = DOUBLE_SIDED.clock_error_s(reply_s, flight_s, 10.0)

    assert single / double > 200.0
    assert double * SPEED_OF_LIGHT_M_S < 0.2, "centimetres, not metres"


def test_the_double_sided_error_grows_with_distance_and_the_single_sided_does_not():
    """They fail in different directions, which is how to tell them apart."""
    reply_s = reply_delay_s(SX1280)
    near = 100.0 / SPEED_OF_LIGHT_M_S
    far = 10_000.0 / SPEED_OF_LIGHT_M_S

    assert DOUBLE_SIDED.clock_error_s(reply_s, far, 1.0) > 50.0 * (
        DOUBLE_SIDED.clock_error_s(reply_s, near, 1.0)
    )
    assert SINGLE_SIDED.clock_error_s(reply_s, far, 1.0) == pytest.approx(
        SINGLE_SIDED.clock_error_s(reply_s, near, 1.0)
    )


def test_frequency_correction_is_what_makes_single_sided_ranging_usable():
    """Uncorrected, the clock term alone is eight times the measured floor.

    This is the claim that says the correction is not optional.
    """
    budget = budget_at(1000.0)
    corrected = measurement_sigma_m(budget, SX1280, scheme=SINGLE_SIDED)
    raw = measurement_sigma_m(
        budget, SX1280, scheme=SINGLE_SIDED, corrected=False
    )
    assert corrected == pytest.approx(float(SX1280.implementation_floor_m.value))
    assert raw > 20.0


def test_a_better_clock_is_worth_nothing_on_the_long_links():
    """At 10 km the waveform bound is metres and the clock is millimetres.

    Buying a temperature-compensated oscillator to fix a range error that
    is not the clock's fault is the mistake this test exists to prevent.
    """
    budget = budget_at(10_000.0)
    crystal = measurement_sigma_m(budget, SX1280, clock=CRYSTAL)
    tcxo = measurement_sigma_m(budget, SX1280, clock=TCXO)
    assert tcxo == pytest.approx(crystal, rel=1e-6)


def test_the_measured_residual_makes_double_sided_ranging_pointless():
    """It was not, at the assumed 0,5 ppm.

    The impulse radio's floor is a tenth of a metre and a 0,5 ppm
    residual across its 1,4 ms reply was also a tenth of a metre, so the
    extra frame earned its place. Measured, the residual is 0,0793 ppm
    and that term is 1,6 cm, which the floor swallows whole. Neither
    radio now has a reason to spend the third frame.
    """
    for radio, height_m, distance_m in (
        (DWM3000, 6.0, 100.0), (SX1280, 25.0, 3000.0)
    ):
        budget = budget_at(distance_m, radio, anchor_height_m=height_m)
        single = measurement_sigma_m(budget, radio, scheme=SINGLE_SIDED)
        double = measurement_sigma_m(budget, radio, scheme=DOUBLE_SIDED)
        assert single == pytest.approx(double, rel=1e-6), radio.part


def test_the_clock_term_would_still_matter_if_the_residual_were_assumed():
    """The measurement is what settles it, not the model's shape.

    Held at the 0,5 ppm this project assumed for a fortnight, the
    impulse radio's single-sided term is a tenth of a metre and does
    reach its floor. The conclusion changed because a number did.
    """
    from dataclasses import replace

    from yerkon.evidence import Provenance, Sourced

    assumed = replace(
        CRYSTAL,
        residual_ppm=Sourced(
            0.5, "ppm", Provenance.ASSUMPTION, "the earlier default",
            note="what this project assumed before it was measured",
        ),
    )
    budget = budget_at(100.0, DWM3000, anchor_height_m=6.0)
    single = measurement_sigma_m(
        budget, DWM3000, clock=assumed, scheme=SINGLE_SIDED
    )
    double = measurement_sigma_m(
        budget, DWM3000, clock=assumed, scheme=DOUBLE_SIDED
    )
    assert single > double


def test_the_model_never_beats_the_only_measurement_of_the_part():
    """At 100 m the waveform bound says two centimetres. The part does not."""
    sigma = measurement_sigma_m(budget_at(100.0), SX1280)
    assert sigma == pytest.approx(float(SX1280.implementation_floor_m.value))


def test_the_floor_does_not_rescue_a_bad_configuration():
    """It is a floor under the physics, not a cap over it."""
    raw = measurement_sigma_m(
        budget_at(1000.0), SX1280, scheme=SINGLE_SIDED, corrected=False
    )
    assert raw > float(SX1280.implementation_floor_m.value)


# --- Airtime ---------------------------------------------------------------


def test_a_slow_frame_is_slow_because_its_symbols_are_long():
    assert frame_duration_s(SX1280) > 10.0 * frame_duration_s(DWM3000)


def test_the_preamble_a_frame_pays_for_is_the_one_the_gain_comes_from():
    """A radio cannot have cheap airtime and a generous processing gain."""
    preamble_s = (
        float(DWM3000.preamble_symbols.value)
        * float(DWM3000.symbol_duration_s.value)
    )
    assert preamble_s / frame_duration_s(DWM3000) > 0.9
    assert float(DWM3000.processing_gain_db.value) == pytest.approx(
        10.0 * math.log10(float(DWM3000.preamble_symbols.value)), abs=0.1
    )


def test_double_sided_ranging_costs_half_again_the_airtime():
    single = exchange_duration_s(SX1280, SINGLE_SIDED)
    double = exchange_duration_s(SX1280, DOUBLE_SIDED)
    assert 1.4 < double / single < 1.6


def test_a_duty_limit_takes_its_cut_of_the_update_rate():
    full = ranges_per_second(SX1280)
    tenth = ranges_per_second(SX1280, duty_cycle=0.1)
    assert tenth == pytest.approx(full / 10.0)


def test_the_slow_radio_manages_only_tens_of_ranges_a_second():
    """Which is what makes a round against six anchors take a quarter second."""
    assert 10.0 < ranges_per_second(SX1280) < 40.0
    assert ranges_per_second(DWM3000) > 100.0


# --- One measurement -------------------------------------------------------


def test_a_measurement_is_the_true_distance_plus_noise_of_the_stated_size():
    rng = np.random.default_rng(11)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))

    draws = [
        measure(anchor, receiver, 0.0, rng).measured_range_m for _ in range(2000)
    ]
    truth = math.dist(anchor.position_m, receiver.position_m)
    sigma = measure(anchor, receiver, 0.0, rng).sigma_m

    assert np.mean(draws) == pytest.approx(truth, abs=0.2)
    assert np.std(draws) == pytest.approx(sigma, rel=0.1)


def test_the_same_seed_gives_the_same_measurement():
    """A previous version held a module-level generator and every swept
    comparison it published was contaminated by the run before it."""
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))

    first = measure(anchor, receiver, 0.0, np.random.default_rng(4))
    again = measure(anchor, receiver, 0.0, np.random.default_rng(4))
    assert first == again


def test_a_link_that_does_not_close_produces_nothing_rather_than_a_guess():
    rng = np.random.default_rng(3)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 3.0))
    far = Terminal(SX1280, W24P_U, (55_000.0, 0.0, 1.5))
    assert measure(anchor, far, 0.0, rng) is None


def test_two_radios_that_cannot_hear_each_other_are_refused():
    """An impulse radio and a spread one produce no exchange at all."""
    rng = np.random.default_rng(3)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(DWM3000, W24P_U, (100.0, 0.0, 1.5))

    with pytest.raises(ValueError, match="do not share a ranging waveform"):
        measure(anchor, receiver, 0.0, rng)


def test_a_measurement_carries_the_anchor_and_not_the_receiver():
    rng = np.random.default_rng(5)
    anchor = Terminal(SX1280, W24P_U, (10.0, 20.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))

    observation = measure(anchor, receiver, 1.5, rng, anchor_id="A7")

    assert isinstance(observation, RangeObservation)
    assert observation.anchor_position_m == (10.0, 20.0, 25.0)
    assert observation.anchor_id == "A7"
    assert observation.at_s == 1.5


# --- A round of them -------------------------------------------------------


def moving_receiver(speed_m_s, start_m=2500.0):
    def where(at_s):
        return Terminal(SX1280, W24P_U, (start_m + speed_m_s * at_s, 0.0, 1.5))

    return where


def anchors_along(count, spacing_m=2000.0):
    return [
        ("A{}".format(i), Terminal(SX1280, W24P_U, (i * spacing_m, 0.0, 25.0)))
        for i in range(count)
    ]


def test_the_ranges_in_a_round_are_taken_one_after_another():
    rng = np.random.default_rng(2)
    observations = round_robin(
        anchors_along(4), moving_receiver(0.0), 0.0, rng, SX1280
    )
    times = [o.at_s for o in observations]
    assert times == sorted(times)
    assert len(set(times)) == len(times), "no two exchanges share an instant"


def test_a_vehicle_moves_further_between_ranges_than_the_ranging_error():
    """The reason the estimator has to be a filter and not a snapshot.

    Six anchors at SF10 take a quarter of a second. At a hundred
    kilometres an hour that is nearly seven metres, against a ranging
    sigma of three.
    """
    rng = np.random.default_rng(2)
    speed_m_s = 27.8

    observations = round_robin(
        anchors_along(6), moving_receiver(speed_m_s), 0.0, rng, SX1280
    )

    spread_s = observations[-1].at_s - observations[0].at_s
    travelled_m = speed_m_s * spread_s
    assert travelled_m > 2.0 * observations[0].sigma_m


def test_a_duty_limit_stretches_the_round_out():
    rng = np.random.default_rng(2)
    full = round_robin(anchors_along(4), moving_receiver(0.0), 0.0, rng, SX1280)
    limited = round_robin(
        anchors_along(4), moving_receiver(0.0), 0.0, rng, SX1280, duty_cycle=0.5
    )
    assert limited[-1].at_s == pytest.approx(2.0 * full[-1].at_s)


def test_an_anchor_out_of_reach_is_absent_rather_than_wrong():
    rng = np.random.default_rng(2)
    reachable = anchors_along(2)
    out_of_reach = [("far", Terminal(SX1280, W24P_U, (90_000.0, 0.0, 3.0)))]

    observations = round_robin(
        reachable + out_of_reach, moving_receiver(0.0), 0.0, rng, SX1280
    )
    assert [o.anchor_id for o in observations] == ["A0", "A1"]


# --- Errors that are not noise --------------------------------------------


def test_a_blocked_link_measures_long_and_stays_long():
    """A detour is a bias. Averaging more measurements does not remove it,
    which is why obstruction hurts positioning more than its loss says."""
    from yerkon.rf import Obstruction

    rng = np.random.default_rng(4)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))
    truth = 3000.0

    def mean_over(obstruction):
        draws = [
            measure(anchor, receiver, 0.0, rng, obstruction=obstruction)
            for _ in range(3000)
        ]
        return float(np.mean([d.measured_range_m for d in draws if d]))

    clear = mean_over(None)
    blocked = mean_over(Obstruction(peak_terrain_m=25.0))

    assert clear == pytest.approx(truth, abs=0.2)
    assert blocked > clear


def test_a_survey_error_is_carried_rather_than_drawn():
    """It is a property of an installation, fixed for its life, so it is
    passed in already drawn. Drawing it per measurement would let it
    average away, which a survey error does not do."""
    rng = np.random.default_rng(5)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))

    draws = [
        measure(anchor, receiver, 0.0, rng, survey_error_m=2.0).measured_range_m
        for _ in range(2000)
    ]
    assert float(np.mean(draws)) == pytest.approx(3002.0, abs=0.2)


def test_a_lost_packet_produces_nothing_just_like_a_dead_link():
    """Interference, a collision, a fade. The receiver does not get a
    range, and it does not get a bad one either."""
    rng = np.random.default_rng(6)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (2000.0, 0.0, 1.5))

    lost = sum(
        measure(anchor, receiver, 0.0, rng, packet_loss=0.2) is None
        for _ in range(4000)
    )
    assert 0.17 < lost / 4000 < 0.23


def test_none_of_the_biases_change_what_the_receiver_believes():
    """A receiver does not know it is being lied to. Inflating the
    variance to cover a bias would model one that did."""
    rng = np.random.default_rng(7)
    anchor = Terminal(SX1280, W24P_U, (0.0, 0.0, 25.0))
    receiver = Terminal(SX1280, W24P_U, (3000.0, 0.0, 1.5))

    plain = measure(anchor, receiver, 0.0, rng)
    biased = measure(anchor, receiver, 0.0, rng, survey_error_m=5.0)
    assert biased.variance_m2 == pytest.approx(plain.variance_m2)
