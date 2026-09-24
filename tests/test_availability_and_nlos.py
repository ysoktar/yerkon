"""What counts as a position, and what a blocked path does to a range (ADR-0084)."""

import math
from dataclasses import replace

import numpy as np
import pytest

from yerkon.estimator import Fix, TrackingFilter
from yerkon.evaluate import run_scenario
from yerkon.hardware import SX1280
from yerkon.observation import RangeObservation
from yerkon.ranging import measure
from yerkon.rf import Obstruction, Terminal
from yerkon.hardware import W24P_U
from yerkon.scenarios import CHOICES
from yerkon.evidence import Provenance, Sourced


def _briefly(scenario, seconds=60.0, **changes):
    units = tuple(
        replace(unit, journey=replace(unit.journey, duration_s=min(
            unit.journey.duration_s, seconds)))
        for unit in scenario.deployment.receivers)
    return replace(scenario, deployment=replace(
        scenario.deployment, receivers=units), **changes)


# --- Availability ---------------------------------------------------------


def test_the_bar_comes_from_the_ten_metre_p95_target():
    """10 m at 95 % over two equal axes is 4,08 m a side, 5,78 m in all."""
    from yerkon.settings import DEFAULTS

    per_axis = 10.0 / math.sqrt(-2.0 * math.log(0.05))
    assert DEFAULTS.number("site.fix_horizontal_sigma_m") == pytest.approx(
        per_axis * math.sqrt(2.0), abs=0.005)


def test_an_uncertain_position_is_an_outage_not_a_sample():
    """The receiver keeps tracking; it just has nothing to offer."""
    urban = CHOICES["urban"].scenario
    loose = run_scenario(_briefly(urban, fix_sigma_m=math.inf))
    gated = run_scenario(_briefly(urban))
    strict = run_scenario(_briefly(urban, fix_sigma_m=0.01))

    assert loose.attempted == gated.attempted == strict.attempted
    assert strict.produced == 0
    assert gated.produced <= loose.produced
    # Every sample the gate keeps is one the loose run also has: the
    # gate removes positions, it does not move them.
    assert set(np.round(gated.horizontal_error_m, 9)) <= set(
        np.round(loose.horizontal_error_m, 9))


def test_the_rows_use_the_gate():
    for deployed in CHOICES.values():
        assert deployed.scenario.fix_sigma_m == pytest.approx(5.78)


# --- The filter's gate ----------------------------------------------------


def _filter(gate):
    start = Fix(at_s=0.0, position_m=(0.0, 0.0, 0.0),
                covariance_m2=np.eye(3) * 4.0, used=4)
    return TrackingFilter(start, gate_sigmas=gate)


def _range(true_m, measured_m, at_s=0.1):
    return RangeObservation(at_s=at_s, anchor_position_m=(true_m, 0.0, 0.0),
                            measured_range_m=measured_m, variance_m2=9.0)


def test_a_range_the_prediction_cannot_explain_is_turned_away():
    gated = _filter(3.0)
    gated.absorb(_range(200.0, 200.0 + 80.0))
    assert gated.gated == 1
    assert gated.position_m[0] == pytest.approx(0.0, abs=1e-6)

    gated.absorb(_range(200.0, 201.0, at_s=0.2))
    assert gated.gated == 1
    assert gated.used == 5


def test_with_no_gate_every_range_is_taken():
    open_ = _filter(0.0)
    open_.absorb(_range(200.0, 280.0))
    assert open_.gated == 0
    assert abs(open_.position_m[0]) > 1.0


# --- The blocked path -----------------------------------------------------


def _pair(bias_m):
    radio = replace(SX1280, nlos_bias_mean_m=Sourced(
        bias_m, "m", Provenance.ASSUMPTION, "test", note="a test figure"))
    anchor = Terminal(radio, W24P_U, (0.0, 0.0, 10.0))
    receiver = Terminal(radio, W24P_U, (300.0, 0.0, 1.5))
    return anchor, receiver


def _ranges(bias_m, blocked, count=400):
    anchor, receiver = _pair(bias_m)
    rng = np.random.default_rng(5)
    out = []
    for _ in range(count):
        found = measure(anchor, receiver, 0.0, rng,
                        obstruction=Obstruction(blocked=blocked))
        out.append(found.measured_range_m)
    return np.array(out), rng.random()


def test_a_blocked_path_reads_long_by_about_the_mean():
    clear, _ = _ranges(10.0, blocked=False)
    blocked, _ = _ranges(10.0, blocked=True)
    assert np.mean(blocked) - np.mean(clear) == pytest.approx(10.0, rel=0.2)
    # Exponential, so it only ever lengthens and it spreads the ranges.
    assert np.std(blocked) > np.std(clear)


def test_with_the_bias_off_nothing_is_drawn():
    """So a run with the option off is the run it was, draw for draw."""
    off_blocked, after_blocked = _ranges(0.0, blocked=True)
    off_clear, after_clear = _ranges(0.0, blocked=False)
    assert after_blocked == after_clear
    assert np.array_equal(off_blocked, off_clear)


def test_the_option_ships_switched_off():
    from yerkon.settings import DEFAULTS

    assert DEFAULTS.number("radio.sx1280.nlos_bias_mean_m") == 0.0
    assert DEFAULTS.number("radio.dwm3000.nlos_bias_mean_m") == 0.0
    assert DEFAULTS.number("estimator.gate_sigmas") == 0.0


def test_a_round_the_gate_turns_away_entirely_restarts_the_filter():
    """The lockout every gated filter has to guard against (ADR-0084).

    A filter that has wandered disagrees with every range and keeps
    coasting, so it disagrees with the next round too. Ranges that agree
    with each other and not with the filter start it again.
    """
    from yerkon.evaluate import _fix_from

    lost = _filter(3.0)
    lost.state[:3] = (500.0, 500.0, 0.0)
    anchors = ((0.0, 0.0, 10.0), (100.0, 0.0, 10.0),
               (0.0, 100.0, 10.0), (100.0, 100.0, 10.0))
    truth = np.array((40.0, 60.0, 1.5))
    round_ = [
        RangeObservation(at_s=0.5, anchor_position_m=a,
                         measured_range_m=float(np.linalg.norm(truth - a)),
                         variance_m2=1.0)
        for a in anchors]
    tracker, position = _fix_from(round_, lost, 1.0, 3.0)
    assert tracker is not lost
    assert np.linalg.norm(np.array(position[:2]) - truth[:2]) < 1.0
