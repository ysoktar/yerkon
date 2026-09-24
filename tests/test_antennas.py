"""The chip's official sensitivity and the antennas that win it back (ADR-0091)."""

import math

import pytest

from yerkon.hardware import HGV_2409U, SX1280, TL_ANT2412D, W24P_U


def test_the_sensitivity_is_the_one_semtech_publishes_carried_to_sf10():
    """-132 dBm at SF12 and 203 kHz, +9,03 dB to 1625 kHz, +5 dB to SF10."""
    bandwidth = float(SX1280.ranging_bandwidth_hz.value)
    closes_at = (-174.0 + 10.0 * math.log10(bandwidth)
                 + float(SX1280.noise_figure_db.value)
                 + float(SX1280.demodulation_threshold_db.value))
    carried = -132.0 + 10.0 * math.log10(1625.0 / 203.125) + 5.0
    assert closes_at == pytest.approx(carried, abs=0.05)
    assert closes_at == pytest.approx(-118.0, abs=0.1)


def test_a_mast_antenna_is_strong_on_the_horizon_and_weak_under_itself():
    """A collinear buys gain by flattening its beam; right under the pole
    the vehicle sits in the part it gave up."""
    assert TL_ANT2412D.gain_dbi(0.0) == pytest.approx(TL_ANT2412D.peak_dbi)
    half = TL_ANT2412D.vertical_beamwidth_deg / 2.0
    assert TL_ANT2412D.gain_dbi(half) == pytest.approx(
        TL_ANT2412D.peak_dbi - 3.0)
    assert TL_ANT2412D.gain_dbi(45.0) == pytest.approx(
        TL_ANT2412D.peak_dbi - 20.0)
    # And the beam is the narrower reading, not the datasheet's "at most".
    assert TL_ANT2412D.vertical_beamwidth_deg < 12.0


def test_the_cable_costs_what_the_datasheet_says():
    """0,3 m of LMR-200 at 0,554 dB/m and two connectors."""
    assert TL_ANT2412D.feed_loss_db == pytest.approx(0.47, abs=0.01)
    assert HGV_2409U.feed_loss_db == TL_ANT2412D.feed_loss_db


def test_the_rows_hear_with_mast_antennas_and_a_pedestrian_does_not():
    from yerkon.scenarios import CHOICES

    for row in ("urban", "rural"):
        deployment = CHOICES[row].scenario.deployment
        assert deployment.antenna is TL_ANT2412D
        for unit in deployment.receivers:
            expected = HGV_2409U if unit.product == "vehicle" else W24P_U
            assert unit.antenna is expected, (row, unit.identifier)
    tunnel = CHOICES["tunnel"].scenario.deployment
    assert tunnel.antenna is W24P_U
    assert all(unit.antenna is W24P_U for unit in tunnel.receivers)


def test_a_tab_hears_with_the_antennas_its_row_does():
    from yerkon.viewer.state import from_scenario

    for row in ("urban", "rural", "tunnel"):
        state = from_scenario(row)
        deployment = state.deployment(state.terrain())
        from yerkon.scenarios import CHOICES

        assert deployment.antenna is CHOICES[row].scenario.deployment.antenna
        assert [u.antenna for u in deployment.receivers] == [
            u.antenna for u in CHOICES[row].scenario.deployment.receivers]
