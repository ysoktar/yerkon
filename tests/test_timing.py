"""Bandwidth, timing-resolution heuristics, and a deterministic-delay CRLB.

These are explicitly labeled heuristics/bounds in the spec, not positioning
accuracy claims, and this module keeps them separate from measured or
simulated accuracy metrics.
"""
import pytest

from locbench3d.core.timing import (
    SPEED_OF_LIGHT_M_S,
    beta_rms_bandwidth,
    clock_drift_time_s,
    clock_drift_distance_m,
    fractional_bandwidth,
    range_resolution_heuristic_m,
    signal_bandwidth,
    signal_center_frequency,
    time_of_arrival_crlb_s,
    wavelength_m,
)


def test_bandwidth_and_center_frequency():
    assert signal_bandwidth(f_high_hz=2.4835e9, f_low_hz=2.4000e9) == pytest.approx(
        8.35e7
    )
    assert signal_center_frequency(
        f_high_hz=2.4835e9, f_low_hz=2.4000e9
    ) == pytest.approx((2.4835e9 + 2.4000e9) / 2)


def test_fractional_bandwidth():
    assert fractional_bandwidth(bandwidth_hz=8.35e7, center_freq_hz=2.44e9) == pytest.approx(
        8.35e7 / 2.44e9
    )


def test_wavelength_uses_speed_of_light():
    lam = wavelength_m(center_freq_hz=2.44e9)
    assert lam == pytest.approx(SPEED_OF_LIGHT_M_S / 2.44e9)


def test_range_resolution_heuristic_scales_inversely_with_bandwidth():
    narrow = range_resolution_heuristic_m(bandwidth_hz=1e6)
    wide = range_resolution_heuristic_m(bandwidth_hz=500e6)
    assert narrow > wide
    assert wide == pytest.approx(SPEED_OF_LIGHT_M_S / 500e6)


def test_beta_rms_bandwidth_for_flat_spectrum():
    import math

    b = 500e6
    assert beta_rms_bandwidth(bandwidth_hz=b) == pytest.approx(b / math.sqrt(12))


def test_time_of_arrival_crlb_decreases_with_snr_and_bandwidth():
    low_snr = time_of_arrival_crlb_s(bandwidth_hz=500e6, snr_linear=10)
    high_snr = time_of_arrival_crlb_s(bandwidth_hz=500e6, snr_linear=1000)
    assert high_snr < low_snr

    narrow = time_of_arrival_crlb_s(bandwidth_hz=1e6, snr_linear=100)
    wide = time_of_arrival_crlb_s(bandwidth_hz=500e6, snr_linear=100)
    assert wide < narrow


def test_clock_drift_approximation():
    eps = 20e-6  # 20 ppm
    delta_t = 3600.0  # 1 hour
    drift_s = clock_drift_time_s(oscillator_tolerance=eps, elapsed_s=delta_t)
    assert drift_s == pytest.approx(eps * delta_t)
    drift_m = clock_drift_distance_m(oscillator_tolerance=eps, elapsed_s=delta_t)
    assert drift_m == pytest.approx(SPEED_OF_LIGHT_M_S * eps * delta_t)
