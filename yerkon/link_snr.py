"""What signal-to-noise ratio a link of a given length actually delivers.

The waveform simulation sweeps SNR as a free parameter, because that is
the honest thing for it to do: it models the receiver, not the propagation
path. But the error model built from those results has to be pooled over
something, and pooling the full SNR x distance grid uniformly says a
3000 m link is as likely to arrive at 25 dB as at 5 dB. It is not. A long
link arrives weak; that is what makes it long.

This module closes the grid with a link budget, so each simulated distance
draws on the SNR rows it would really see. Everything in it is standard
radio arithmetic, and each term is named so it can be argued with:

    SNR = EIRP + G_rx - PL(d) - (kTB + NF)

The transmit power is not a free choice either. It comes from
``regulatory.psd_limited_power_dbm``: in this band the density cap sets it,
and it rises with bandwidth. So a wider ranging bandwidth is allowed more
power, which is why widening it does not shorten the link.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from yerkon.evidence import EvidenceRecord, EvidenceType
from yerkon.regulatory import psd_limited_power_dbm

#: Thermal noise density at room temperature, dBm/Hz.
THERMAL_NOISE_DBM_PER_HZ = -174.0

#: Receiver noise figure, dB. Integrated 2.4 GHz transceivers of this class
#: sit in the 6-10 dB range; 6 dB is the optimistic end, chosen so the
#: budget does not manufacture a pessimistic result by accident.
RECEIVER_NOISE_FIGURE_DB = 6.0

#: Receive antenna gain, dBi. A small vehicle or roadside antenna.
RECEIVE_ANTENNA_GAIN_DBI = 2.0

#: The spreading factor Semtech's ranging mode and Robinson's published
#: measurements both use.
SX1280_RANGING_SPREADING_FACTOR = 10

#: Lowest raw SNR at which an SF10 LoRa link still demodulates, dB. LoRa
#: works well below the noise floor: the chirp spreads over 2^SF chips and
#: the correlator recovers that as gain.
SF10_DEMODULATION_FLOOR_DB = -20.0

#: Path loss exponents. Free space is 2.0 by definition; the others are
#: this project's assumptions for the two outdoor cases, and the rural
#: figure is the one ``regulatory.RURAL_PATH_LOSS_EXPONENT`` also uses.
PATH_LOSS_EXPONENTS = {
    "free_space": 2.0,
    "rural": 2.7,
    "urban": 3.0,
    "tunnel": 1.8,   # a tunnel guides rather than spreads; loss is sub-free-space
}

LINK_BUDGET_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
    source_name="Link budget closing the SNR-distance grid",
    source_scope=(
        "SNR = EIRP + G_rx - PL(d) - (kTB + NF), with EIRP set by the "
        "band's power spectral density cap, PL a log-distance model, and "
        "kTB thermal noise over the ranging bandwidth."
    ),
    caveats=(
        "The noise figure (6 dB), receive antenna gain (2 dBi) and the "
        "urban and rural path loss exponents (3.0 and 2.7) are this "
        "project's assumptions, not measurements. They set which simulated "
        "SNR applies at which distance, so they move the pooled error "
        "model; they do not change any simulated point itself."
    ),
)


def free_space_path_loss_db(distance_m: float, frequency_hz: float) -> float:
    """Free-space loss, dB. Undefined at zero distance."""
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    wavelength_m = 299792458.0 / frequency_hz
    return 20.0 * math.log10(4.0 * math.pi * distance_m / wavelength_m)


def path_loss_db(distance_m: float, frequency_hz: float, exponent: float) -> float:
    """Log-distance path loss, dB, anchored to free space at one metre.

    Above one metre the excess over free space is ``10*(n-2)*log10(d)``, so
    an exponent of 2.0 returns free space exactly.
    """
    if exponent < 2.0:
        # A guided environment can beat free space; allow it but still
        # anchor at 1 m so the two branches meet there.
        pass
    base = free_space_path_loss_db(distance_m, frequency_hz)
    return base + 10.0 * (exponent - 2.0) * math.log10(distance_m)


def spreading_gain_db(spreading_factor: int) -> float:
    """Correlation gain of a LoRa chirp of 2^SF chips, dB.

    This is the term that decides whether the long rural links exist at
    all. At SF10 it is 30 dB, so a link arriving 14 dB below the noise
    floor still resolves. Reading the raw SNR alone would say that link is
    dead; it is not, and an earlier version of this analysis got that
    wrong before the gain was written down.

    It buys sensitivity, not resolution: the timing precision still comes
    from the bandwidth, which is why the bandwidth argument and this one
    are separate.
    """
    if spreading_factor < 1:
        raise ValueError("spreading_factor must be positive")
    return 10.0 * math.log10(2 ** spreading_factor)


def thermal_noise_dbm(bandwidth_hz: float, noise_figure_db: float = RECEIVER_NOISE_FIGURE_DB) -> float:
    """Receiver noise floor over the ranging bandwidth, dBm."""
    if bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive")
    return THERMAL_NOISE_DBM_PER_HZ + 10.0 * math.log10(bandwidth_hz) + noise_figure_db


@dataclass(frozen=True)
class LinkBudget:
    """A configuration whose SNR at any distance can be evaluated."""

    bandwidth_hz: float
    frequency_hz: float
    exponent: float
    eirp_dbm: float | None = None
    rx_gain_dbi: float = RECEIVE_ANTENNA_GAIN_DBI
    noise_figure_db: float = RECEIVER_NOISE_FIGURE_DB

    @property
    def transmit_eirp_dbm(self) -> float:
        """Radiated power, defaulting to the highest the band allows."""
        if self.eirp_dbm is not None:
            return self.eirp_dbm
        return psd_limited_power_dbm(self.bandwidth_hz)

    def snr_db(self, distance_m: float) -> float:
        """Received SNR at ``distance_m``, dB."""
        loss = path_loss_db(distance_m, self.frequency_hz, self.exponent)
        noise = thermal_noise_dbm(self.bandwidth_hz, self.noise_figure_db)
        return self.transmit_eirp_dbm + self.rx_gain_dbi - loss - noise

    def range_at_snr_m(self, snr_db: float, tol_m: float = 0.01) -> float:
        """Distance at which the link delivers ``snr_db``, in metres.

        Solved by bisection rather than inverted in closed form, so the
        path loss model can change shape without this needing to follow.
        """
        lo, hi = 0.1, 1.0
        while self.snr_db(hi) > snr_db:
            hi *= 2.0
            if hi > 1e7:
                return hi
        while hi - lo > tol_m:
            mid = 0.5 * (lo + hi)
            if self.snr_db(mid) > snr_db:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)


def nearest_simulated_snr(budget: LinkBudget, distance_m: float, available_db) -> float:
    """The simulated SNR row closest to what this distance really delivers.

    Clamped to the sweep: a distance whose true SNR falls below everything
    simulated returns the lowest row, and the caller is expected to notice
    that the link does not actually close there rather than to read the
    clamped value as a result. ``link_closes`` is that check.
    """
    predicted = budget.snr_db(distance_m)
    return min(available_db, key=lambda s: abs(s - predicted))


def link_closes(
    budget: LinkBudget,
    distance_m: float,
    floor_db: float = SF10_DEMODULATION_FLOOR_DB,
) -> bool:
    """Whether the link still demodulates at this distance.

    Compares the raw SNR against the demodulation floor, both in raw
    terms, so the spreading gain is accounted for by the floor being
    negative rather than by adding it to the signal.
    """
    return budget.snr_db(distance_m) >= floor_db


def max_range_m(
    budget: LinkBudget,
    floor_db: float = SF10_DEMODULATION_FLOOR_DB,
) -> float:
    """Farthest distance at which the link still demodulates, in metres."""
    return budget.range_at_snr_m(floor_db)
