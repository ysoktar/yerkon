"""The link budget, and the two conclusions it overturned."""
import math

import pytest

from yerkon import link_snr as ls
from yerkon.regulatory import psd_limited_power_dbm


def budget(bandwidth_hz=1625e3, exponent=2.7, eirp_dbm=None):
    return ls.LinkBudget(
        bandwidth_hz=bandwidth_hz,
        frequency_hz=2450e6,
        exponent=exponent,
        eirp_dbm=eirp_dbm,
    )


def test_free_space_loss_matches_the_closed_form():
    """80.2 dB at 100 m and 2.45 GHz, checked against 20log10(4*pi*d/lambda)."""
    assert ls.free_space_path_loss_db(100.0, 2450e6) == pytest.approx(80.24, abs=0.05)


def test_path_loss_reduces_to_free_space_at_exponent_two():
    for d in (1.0, 50.0, 3000.0):
        assert ls.path_loss_db(d, 2450e6, 2.0) == pytest.approx(
            ls.free_space_path_loss_db(d, 2450e6)
        )


def test_the_two_models_meet_at_one_metre():
    """Anchoring at 1 m is what makes the exponents comparable."""
    for n in (1.8, 2.0, 2.7, 3.0):
        assert ls.path_loss_db(1.0, 2450e6, n) == pytest.approx(
            ls.free_space_path_loss_db(1.0, 2450e6)
        )


def test_thermal_noise_floor():
    """-174 dBm/Hz over 1.625 MHz with a 6 dB noise figure is -106 dBm."""
    assert ls.thermal_noise_dbm(1625e3) == pytest.approx(-105.89, abs=0.05)


def test_snr_does_not_depend_on_ranging_bandwidth():
    """The claim the whole bandwidth recommendation rests on.

    Under the density cap the legal power rises with bandwidth by exactly
    the amount thermal noise does, so the SNR at any distance is the same
    at 203 kHz as at 1625 kHz. Widening the ranging bandwidth therefore
    costs no range, which is why it is a free choice.
    """
    reference = budget(bandwidth_hz=203e3, exponent=3.0).snr_db(400.0)
    for bw in (406e3, 812e3, 1625e3):
        assert budget(bandwidth_hz=bw, exponent=3.0).snr_db(400.0) == pytest.approx(
            reference, abs=1e-9
        )


def test_default_power_is_the_legal_maximum():
    for bw in (203e3, 406e3, 812e3, 1625e3):
        assert budget(bandwidth_hz=bw).transmit_eirp_dbm == pytest.approx(
            psd_limited_power_dbm(bw)
        )


def test_spreading_gain_is_thirty_db_at_sf10():
    assert ls.spreading_gain_db(10) == pytest.approx(30.1, abs=0.05)
    assert ls.spreading_gain_db(11) - ls.spreading_gain_db(10) == pytest.approx(
        3.01, abs=0.01
    )


def test_the_rural_link_closes_at_legal_power():
    """The correction. Reading the raw SNR alone says this link is dead.

    A 3000 m rural link arrives about 14 dB below the noise floor. An
    earlier pass concluded from that alone that the rural row needed a
    quarter of the range and four times the nodes. With SF10's 30 dB of
    spreading gain the link resolves, and the legal configuration reaches
    roughly 5 km, so the 3000 m the scenario models is well inside it.
    """
    b = budget()
    assert b.snr_db(3000.0) < 0.0
    assert ls.link_closes(b, 3000.0)
    assert ls.max_range_m(b) > 3000.0
    assert ls.max_range_m(b) == pytest.approx(4956.0, rel=0.02)


def test_the_extra_power_of_the_oversized_module_is_not_needed():
    """27 dBm buys range the corridor never asks for."""
    legal = ls.max_range_m(budget())
    oversized = ls.max_range_m(budget(eirp_dbm=27.0))
    assert oversized > legal
    assert legal > 3000.0, "the legal configuration already covers the corridor"


def test_range_at_snr_inverts_snr_db():
    b = budget()
    for target in (-15.0, 0.0, 10.0):
        assert b.snr_db(b.range_at_snr_m(target)) == pytest.approx(target, abs=0.01)


def test_nearest_simulated_snr_picks_the_right_row():
    b = budget(exponent=3.0)
    rows = [-20, -12, -6, 0, 6, 12, 18, 25]
    # 50 m urban delivers about +29 dB, so the top row is the right one.
    assert ls.nearest_simulated_snr(b, 50.0, rows) == 25
    # A long link lands on a low row rather than being pooled with the rest.
    assert ls.nearest_simulated_snr(b, 3000.0, rows) <= -12


@pytest.mark.parametrize("bad", [0.0, -5.0])
def test_distance_must_be_positive(bad):
    with pytest.raises(ValueError):
        ls.free_space_path_loss_db(bad, 2450e6)
