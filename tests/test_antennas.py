"""The chip's official sensitivity and the antennas that win it back
(ADR-0091), and the certificate and antennas the rows use (ADR-0094)."""

import math

import pytest

from yerkon.hardware import (
    DUCK_5DBI, E28_2G4M27S, HGV_2409U, SX1280, TL_ANT2412D, W24P_U)


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


def test_the_rows_hear_with_a_duck_and_a_pedestrian_does_not():
    from yerkon.scenarios import CHOICES

    for row in ("urban", "rural"):
        deployment = CHOICES[row].scenario.deployment
        assert deployment.antenna is DUCK_5DBI
        for unit in deployment.receivers:
            expected = DUCK_5DBI if unit.product == "vehicle" else W24P_U
            assert unit.antenna is expected, (row, unit.identifier)
    tunnel = CHOICES["tunnel"].scenario.deployment
    assert tunnel.antenna is W24P_U
    assert all(unit.antenna is W24P_U for unit in tunnel.receivers)


def test_the_town_and_the_open_country_are_certified_as_adaptive_hopping():
    """20 dBm with no density limit, and 5 % of each occupancy idle."""
    from yerkon.regulatory import TURKEY, TURKEY_FREQUENCY_HOPPING
    from yerkon.scenarios import CHOICES

    for row in ("urban", "rural"):
        deployment = CHOICES[row].scenario.deployment
        assert deployment.region is TURKEY_FREQUENCY_HOPPING
        assert deployment.duty_cycle == pytest.approx(1.0 / 1.05)
        assert all(a.radio.part == E28_2G4M27S.part
                   for a in deployment.anchors)
        for unit in deployment.receivers:
            wide_area = unit.radios[0].part
            if unit.product == "vehicle":
                assert wide_area == E28_2G4M27S.part, (row, unit.identifier)
            else:
                assert wide_area == SX1280.part, (row, unit.identifier)
    tunnel = CHOICES["tunnel"].scenario.deployment
    assert tunnel.region is TURKEY
    assert tunnel.duty_cycle == 1.0


def test_the_rest_after_each_occupancy_is_time_the_schedule_loses():
    from yerkon.regulatory import TURKEY, TURKEY_FREQUENCY_HOPPING

    assert TURKEY.channel_share == 1.0
    assert TURKEY_FREQUENCY_HOPPING.channel_share == pytest.approx(1.0 / 1.05)


def test_the_duck_reaches_the_ceiling_with_the_amplified_module():
    """20 dBm e.i.r.p. from a 27 dBm module through 5 dBi: the rule, not
    the hardware, binds."""
    from yerkon.regulatory import TURKEY_FREQUENCY_HOPPING

    eirp = TURKEY_FREQUENCY_HOPPING.permitted_eirp_dbm(
        1625e3, DUCK_5DBI.peak_dbi,
        float(E28_2G4M27S.max_output_dbm.value) - DUCK_5DBI.feed_loss_db)
    assert eirp == pytest.approx(20.0)


def test_a_tab_hears_with_the_antennas_its_row_does():
    from yerkon.viewer.state import from_scenario

    for row in ("urban", "rural", "tunnel"):
        state = from_scenario(row)
        deployment = state.deployment(state.terrain())
        from yerkon.scenarios import CHOICES

        table = CHOICES[row].scenario.deployment
        assert deployment.antenna is table.antenna
        assert [u.antenna for u in deployment.receivers] == [
            u.antenna for u in table.receivers]
        assert deployment.region is table.region
        assert deployment.duty_cycle == table.duty_cycle
        assert [a.radio.part for a in deployment.anchors][:1] == [
            a.radio.part for a in table.anchors][:1]
        assert [[r.part for r in u.radios] for u in deployment.receivers] == [
            [r.part for r in u.radios] for u in table.receivers]
