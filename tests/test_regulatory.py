"""The spectrum limits, and the two conclusions drawn from them."""
import math

import pytest

from yerkon import regulatory as reg


def test_density_cap_binds_at_every_sx1280_bandwidth():
    """The 20 dBm total cap never decides; the density cap always does.

    This is why the bandwidth argument works at all. If the total cap bound
    first, every bandwidth would be allowed the same power and the wider
    ones really would trade range for resolution.
    """
    for bw in reg.SX1280_BANDWIDTHS_HZ:
        density_limited = reg.MAX_EIRP_DENSITY_DBM_PER_MHZ + 10.0 * math.log10(bw / 1e6)
        assert density_limited < reg.MAX_EIRP_DBM
        assert reg.psd_limited_power_dbm(bw) == pytest.approx(density_limited)


def test_widest_bandwidth_matches_published_deployment_power():
    """1625 kHz allows 12.1 dBm, and published work runs it at 12 dBm.

    An independent check that the limit is read correctly: a deployed
    SX1280 localisation system settled on the number this function returns.
    """
    assert reg.psd_limited_power_dbm(1625e3) == pytest.approx(12.1, abs=0.05)


def test_legal_power_and_thermal_noise_scale_together():
    """Doubling the bandwidth adds 3 dB of allowed power and 3 dB of noise.

    So the received SNR at a fixed distance is bandwidth-independent, which
    is the claim ``bandwidth_is_snr_neutral`` makes and the reason the
    MATLAB sweep runs one SNR set across all four bandwidths.
    """
    for narrow, wide in zip(reg.SX1280_BANDWIDTHS_HZ, reg.SX1280_BANDWIDTHS_HZ[1:]):
        power_gain_db = reg.psd_limited_power_dbm(wide) - reg.psd_limited_power_dbm(narrow)
        noise_gain_db = 10.0 * math.log10(wide / narrow)
        assert power_gain_db == pytest.approx(noise_gain_db, abs=1e-9)
    assert reg.bandwidth_is_snr_neutral()


def test_the_rural_module_is_over_the_licence_exempt_cap():
    assert not reg.E28_COMPLIANCE.compliant
    assert reg.E28_COMPLIANCE.excess_db == pytest.approx(7.0)


def test_range_scale_is_a_quarter_at_highway_exponent():
    """Bringing 27 dBm down to the 1625 kHz limit costs about 15 dB.

    At the rural path loss exponent that leaves roughly a quarter of the
    quoted reference distance, which is what makes this a design finding
    rather than a footnote.
    """
    excess = 27.0 - reg.psd_limited_power_dbm(1625e3)
    assert excess == pytest.approx(14.9, abs=0.05)
    scale = reg.range_scale_for_power_cut(excess, reg.RURAL_PATH_LOSS_EXPONENT)
    assert scale == pytest.approx(0.28, abs=0.01)


def test_range_scale_is_unity_when_nothing_is_given_up():
    assert reg.range_scale_for_power_cut(0.0, 2.7) == pytest.approx(1.0)


def test_robinson_used_the_bandwidth_the_simulation_matches():
    """Recorded so the 406 kHz agreement is not re-read as a coincidence."""
    assert reg.ROBINSON_BANDWIDTH_HZ in reg.SX1280_BANDWIDTHS_HZ
    assert reg.ROBINSON_BANDWIDTH_HZ == 406e3


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_bandwidth_must_be_positive(bad):
    with pytest.raises(ValueError):
        reg.psd_limited_power_dbm(bad)
