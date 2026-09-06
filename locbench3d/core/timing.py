"""Bandwidth, timing-resolution heuristics, and a deterministic-delay CRLB.

Two kinds of numbers live here and must not be confused:

* Heuristics (``range_resolution_heuristic_m``): quick rule-of-thumb values
  such as ``delta_d ~ c/B``. These describe a resolution scale, not an
  achievable positioning accuracy, and are always labeled as such wherever
  they are reported.
* A textbook CRLB (``time_of_arrival_crlb_s``): a deterministic-delay AWGN
  bound for a flat rectangular spectrum. It is a bound, evidence type
  ``ANALYTIC_BOUND``, not a measured or simulated accuracy.
"""
from __future__ import annotations

import math

SPEED_OF_LIGHT_M_S = 299_792_458.0


def signal_bandwidth(f_high_hz: float, f_low_hz: float) -> float:
    """B = f_H - f_L"""
    return f_high_hz - f_low_hz


def signal_center_frequency(f_high_hz: float, f_low_hz: float) -> float:
    """f_c = (f_H + f_L) / 2"""
    return (f_high_hz + f_low_hz) / 2.0


def fractional_bandwidth(bandwidth_hz: float, center_freq_hz: float) -> float:
    """fractionalBW = B / f_c"""
    if center_freq_hz <= 0:
        raise ValueError("center_freq_hz must be positive")
    return bandwidth_hz / center_freq_hz


def wavelength_m(center_freq_hz: float) -> float:
    """lambda = c / f_c"""
    if center_freq_hz <= 0:
        raise ValueError("center_freq_hz must be positive")
    return SPEED_OF_LIGHT_M_S / center_freq_hz


def range_resolution_heuristic_m(bandwidth_hz: float) -> float:
    """delta_d ~ c / B.

    This is a resolution heuristic, not a positioning accuracy figure. Two
    scatterers or multipath components closer than roughly this distance
    are hard to resolve in delay; it says nothing about the final position
    RMSE of a working ranging system.
    """
    if bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive")
    return SPEED_OF_LIGHT_M_S / bandwidth_hz


def time_resolution_heuristic_s(bandwidth_hz: float) -> float:
    """delta_t ~ 1 / B"""
    if bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive")
    return 1.0 / bandwidth_hz


def beta_rms_bandwidth(bandwidth_hz: float) -> float:
    """RMS bandwidth of a flat rectangular spectrum of width B.

    beta = B / sqrt(12)
    """
    return bandwidth_hz / math.sqrt(12.0)


def time_of_arrival_crlb_s(bandwidth_hz: float, snr_linear: float) -> float:
    """Deterministic-delay AWGN CRLB for a flat rectangular spectrum.

    sigma_tau >= 1 / sqrt(8 * pi^2 * beta^2 * SNR)

    ``snr_linear`` is a linear (not dB) signal-to-noise ratio. This is an
    analytic lower bound (evidence type ANALYTIC_BOUND), not a measured or
    achievable timing error for any specific receiver implementation.
    """
    if snr_linear <= 0:
        raise ValueError("snr_linear must be positive")
    beta = beta_rms_bandwidth(bandwidth_hz)
    return 1.0 / math.sqrt(8.0 * math.pi**2 * beta**2 * snr_linear)


def range_crlb_from_toa_m(bandwidth_hz: float, snr_linear: float) -> float:
    """sigma_r = c * sigma_tau, from the deterministic-delay TOA CRLB."""
    return SPEED_OF_LIGHT_M_S * time_of_arrival_crlb_s(bandwidth_hz, snr_linear)


def clock_drift_time_s(oscillator_tolerance: float, elapsed_s: float) -> float:
    """delta_t_clock ~ epsilon * delta_T.

    ``oscillator_tolerance`` is a dimensionless fractional frequency error
    (e.g. 20 ppm = 20e-6), not a percentage.
    """
    return oscillator_tolerance * elapsed_s


def clock_drift_distance_m(oscillator_tolerance: float, elapsed_s: float) -> float:
    """Distance-equivalent timing error: c * |epsilon| * delta_T."""
    return SPEED_OF_LIGHT_M_S * abs(oscillator_tolerance) * elapsed_s
