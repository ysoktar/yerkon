"""Whether a link closes, and how well it measures. One calculation, one seam.

This is the module ADR-0002 exists for. The previous codebase decided
reachability from hardcoded distances and measurement quality from a
separate signal-to-noise calculation, so an antenna change moved one and
not the other. Here a single function answers both, which means antenna
gain, mounting height, terrain and transmit power all move node count,
accuracy and cost together.

The chain, in order:

    EIRP -> path loss -> received power -> noise -> signal-to-noise ratio
    -> does it close? -> how precisely can it time an arrival?

The last step is the Cramer-Rao bound for delay estimation. It says the
best achievable timing precision depends on the waveform's root-mean-square
bandwidth and the signal-to-noise ratio, and nothing else. That is why
bandwidth appears in the accuracy answer at all.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import Provenance, Sourced
from yerkon.hardware import SPEED_OF_LIGHT_M_S, Antenna, Radio

BOLTZMANN_NOISE_DBM_PER_HZ = -174.0
"""Thermal noise density at room temperature."""

EARTH_RADIUS_M = 6371000.0
FOUR_THIRDS_EARTH = 4.0 / 3.0
"""Standard refraction factor. Radio bends slightly toward the ground, so
the horizon sits further away than the geometric one."""

FRESNEL_CLEARANCE_FRACTION = 0.6
"""Fraction of the first Fresnel zone that must be clear for the link to
behave as free space. Below this, diffraction loss sets in."""

REGULATORY_MAX_EIRP_DBM = Sourced(
    20.0, "dBm", Provenance.STANDARD,
    "ETSI EN 300 328 V2.2.2, as adopted by the Turkish KET regulation",
)
REGULATORY_MAX_EIRP_DENSITY_DBM_PER_MHZ = Sourced(
    10.0, "dBm/MHz", Provenance.STANDARD,
    "ETSI EN 300 328 V2.2.2, non-FHSS wideband modulation",
)


@dataclass(frozen=True)
class Terminal:
    """One end of a link: what radiates, and from where."""

    radio: Radio
    antenna: Antenna
    position_m: tuple[float, float, float]

    @property
    def height_m(self) -> float:
        return self.position_m[2]


@dataclass(frozen=True)
class Obstruction:
    """What the ground does to a link between two terminals.

    ``peak_terrain_m`` is the highest ground elevation between the two
    ends. ``clutter_loss_db`` is everything the terrain model does not
    carry as geometry: buildings, vegetation, vehicles.
    """

    peak_terrain_m: float = 0.0
    peak_at_fraction: float = 0.5
    clutter_loss_db: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.peak_at_fraction < 1.0:
            raise ValueError("peak_at_fraction must lie strictly inside the path")
        if self.clutter_loss_db < 0.0:
            raise ValueError("clutter cannot add signal")


@dataclass(frozen=True)
class LinkBudget:
    """What a link delivers, and why."""

    distance_m: float
    eirp_dbm: float
    path_loss_db: float
    received_dbm: float
    noise_dbm: float
    snr_db: float
    clearance_m: float
    required_clearance_m: float
    diffraction_loss_db: float

    @property
    def effective_snr_db(self) -> float:
        """Signal-to-noise ratio after the receiver's correlation gain."""
        return self.snr_db + self._processing_gain_db

    _processing_gain_db: float = 0.0
    _threshold_db: float = 0.0

    @property
    def closes(self) -> bool:
        return self.effective_snr_db >= self._threshold_db

    @property
    def margin_db(self) -> float:
        """How much the link has to spare before it stops working."""
        return self.effective_snr_db - self._threshold_db

    @property
    def has_fresnel_clearance(self) -> bool:
        return self.clearance_m >= self.required_clearance_m


def breakpoint_distance_m(
    tx_height_m: float, rx_height_m: float, frequency_hz: float
) -> float:
    """Where ground reflection starts to dominate, in metres.

    Below this the direct and ground-reflected rays add roughly in phase
    and the link behaves like free space. Beyond it they arrive in
    opposition and cancel, and loss grows with the fourth power of
    distance instead of the second.

    The breakpoint is ``4 * h1 * h2 / wavelength``, so it moves with
    antenna height. A unit on a 3 m sign talking to a 2 m vehicle antenna
    is already past it at 200 m; a 25 m mast holds free space out to
    1,6 km.
    """
    if tx_height_m <= 0.0 or rx_height_m <= 0.0:
        raise ValueError("both antennas must be above the ground")
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    return 4.0 * tx_height_m * rx_height_m / wavelength_m


def two_ray_path_loss_db(
    distance_m: float,
    tx_height_m: float,
    rx_height_m: float,
    frequency_hz: float,
) -> float:
    """Loss over reflecting ground, in dB.

    A dual-slope model: free space up to the breakpoint, then 40 dB per
    decade beyond it. This is the standard engineering form of the two-ray
    result and it is what makes low mounting expensive.

    Leaving it out was the largest error in this module's first version.
    Free space understates the loss of a 3 m roadside mount at 10 km by
    34 dB, which is the difference between a design that works and one
    that does not.
    """
    free_space = free_space_path_loss_db(distance_m, frequency_hz)
    breakpoint_m = breakpoint_distance_m(tx_height_m, rx_height_m, frequency_hz)
    if distance_m <= breakpoint_m:
        return free_space
    return free_space_path_loss_db(breakpoint_m, frequency_hz) + 40.0 * math.log10(
        distance_m / breakpoint_m
    )


def free_space_path_loss_db(distance_m: float, frequency_hz: float) -> float:
    if distance_m <= 0.0:
        raise ValueError("distance_m must be positive")
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    return 20.0 * math.log10(4.0 * math.pi * distance_m / wavelength_m)


def first_fresnel_radius_m(
    distance_m: float, frequency_hz: float, at_fraction: float = 0.5
) -> float:
    """Radius of the first Fresnel zone at a point along the path.

    A radio link is not a ray. It needs an ellipsoid of clear space around
    the straight line, and this is that ellipsoid's radius. At 2,45 GHz
    over 10 km the widest point is about 17 m, which is why long links need
    tall masts even over flat ground.
    """
    if not 0.0 < at_fraction < 1.0:
        raise ValueError("at_fraction must lie strictly inside the path")
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    d1 = distance_m * at_fraction
    d2 = distance_m - d1
    return math.sqrt(wavelength_m * d1 * d2 / distance_m)


def earth_bulge_m(distance_m: float, at_fraction: float = 0.5) -> float:
    """How far the ground rises into the path through its own curvature."""
    d1 = distance_m * at_fraction
    d2 = distance_m - d1
    return (d1 * d2) / (2.0 * FOUR_THIRDS_EARTH * EARTH_RADIUS_M)


def diffraction_loss_db(clearance_m: float, fresnel_radius_m: float) -> float:
    """Loss from an obstacle intruding into the Fresnel zone.

    Uses the knife-edge approximation over the Fresnel parameter. Zero
    while the required clearance holds, then rising steeply. An obstacle
    level with the line of sight costs about 6 dB, which is the classic
    knife-edge result and what the test checks.
    """
    if fresnel_radius_m <= 0.0:
        return 0.0
    v = -clearance_m * math.sqrt(2.0) / fresnel_radius_m
    if v <= -0.78:
        return 0.0
    return 6.9 + 20.0 * math.log10(math.sqrt((v - 0.1) ** 2 + 1.0) + v - 0.1)


def regulatory_eirp_limit_dbm(bandwidth_hz: float) -> float:
    """Highest legal radiated power at a given occupied bandwidth.

    Two caps apply and the lower wins. Across every SX1280 bandwidth the
    density cap binds, so legal power rises with bandwidth. Thermal noise
    rises by the same factor, which is why widening the ranging bandwidth
    costs no range.
    """
    if bandwidth_hz <= 0.0:
        raise ValueError("bandwidth_hz must be positive")
    density_limited = float(
        REGULATORY_MAX_EIRP_DENSITY_DBM_PER_MHZ.value
    ) + 10.0 * math.log10(bandwidth_hz / 1e6)
    return min(float(REGULATORY_MAX_EIRP_DBM.value), density_limited)


def _elevation_deg(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> float:
    ground = math.hypot(b[0] - a[0], b[1] - a[1])
    if ground == 0.0:
        return 90.0 if b[2] >= a[2] else -90.0
    return math.degrees(math.atan2(b[2] - a[2], ground))


def evaluate_link(
    transmitter: Terminal,
    receiver: Terminal,
    frequency_hz: float = 2450e6,
    obstruction: Optional[Obstruction] = None,
    respect_regulatory_limit: bool = True,
) -> LinkBudget:
    """The whole chain, for one pair of terminals at one instant."""
    obstruction = obstruction or Obstruction()
    tx, rx = transmitter.position_m, receiver.position_m
    distance_m = math.dist(tx, rx)
    if distance_m <= 0.0:
        raise ValueError("terminals must be at different positions")

    radio = transmitter.radio
    output_dbm = float(radio.max_output_dbm.value)
    tx_gain = transmitter.antenna.gain_dbi(_elevation_deg(tx, rx))
    rx_gain = receiver.antenna.gain_dbi(_elevation_deg(rx, tx))

    eirp_dbm = output_dbm + tx_gain
    if respect_regulatory_limit:
        # The ultra-wideband rating is already an emission limit rather
        # than a conducted power, so antenna gain cannot be added on top
        # of it. Capping against the same limit expresses that without a
        # special case: the cap simply binds immediately.
        eirp_dbm = min(
            eirp_dbm,
            regulatory_eirp_limit_dbm(float(radio.ranging_bandwidth_hz.value)),
            output_dbm if radio.max_output_dbm.unit.endswith("/MHz") else eirp_dbm,
        )

    # Geometry of the obstruction: how far the path clears the highest
    # ground between the ends, once the earth's own curvature is added to
    # that ground.
    fraction = obstruction.peak_at_fraction
    line_of_sight_m = tx[2] + (rx[2] - tx[2]) * fraction
    obstacle_m = obstruction.peak_terrain_m + earth_bulge_m(distance_m, fraction)
    clearance_m = line_of_sight_m - obstacle_m
    fresnel_m = first_fresnel_radius_m(distance_m, frequency_hz, fraction)
    required_m = FRESNEL_CLEARANCE_FRACTION * fresnel_m

    diffraction_db = diffraction_loss_db(clearance_m, fresnel_m)

    # Two effects, and they are not the same one. Ground reflection acts
    # even over perfectly flat ground, because the reflected ray cancels
    # the direct one. Diffraction acts when something rises into the path.
    # A flat site has the first and not the second.
    ground_reference_m = obstruction.peak_terrain_m
    spread_db = two_ray_path_loss_db(
        distance_m,
        max(tx[2] - ground_reference_m, 0.1),
        max(rx[2] - ground_reference_m, 0.1),
        frequency_hz,
    )
    path_loss_db = spread_db + diffraction_db + obstruction.clutter_loss_db

    received_dbm = eirp_dbm + rx_gain - path_loss_db
    noise_dbm = (
        BOLTZMANN_NOISE_DBM_PER_HZ
        + 10.0 * math.log10(float(radio.ranging_bandwidth_hz.value))
        + float(receiver.radio.noise_figure_db.value)
    )

    return LinkBudget(
        distance_m=distance_m,
        eirp_dbm=eirp_dbm,
        path_loss_db=path_loss_db,
        received_dbm=received_dbm,
        noise_dbm=noise_dbm,
        snr_db=received_dbm - noise_dbm,
        clearance_m=clearance_m,
        required_clearance_m=required_m,
        diffraction_loss_db=diffraction_db,
        _processing_gain_db=float(radio.processing_gain_db.value),
        _threshold_db=float(radio.demodulation_threshold_db.value),
    )


def cramer_rao_sigma_m(budget: LinkBudget, radio: Radio) -> float:
    """The floor the waveform permits, one sigma, in metres.

        sigma_tau >= 1 / (2 * pi * beta * sqrt(2 * SNR))

    with ``beta`` the root-mean-square bandwidth and SNR a ratio rather
    than decibels. Nothing about the receiver enters, which is exactly why
    this is a bound and not a prediction.
    """
    if not budget.closes:
        raise ValueError("a link that does not close has no ranging precision")
    snr_linear = 10.0 ** (budget.effective_snr_db / 10.0)
    sigma_tau_s = 1.0 / (
        2.0 * math.pi * radio.rms_bandwidth_hz * math.sqrt(2.0 * snr_linear)
    )
    return sigma_tau_s * SPEED_OF_LIGHT_M_S


def usable_range_m(
    transmitter: Terminal,
    receiver_prototype: Terminal,
    radio: Radio,
    target_sigma_m: float,
    frequency_hz: float = 2450e6,
    obstruction: Optional[Obstruction] = None,
    search_limit_m: float = 60_000.0,
) -> float:
    """Farthest distance whose ranging precision still meets a target.

    This is the number siting needs, and it is not the distance at which
    the link closes. A spread-spectrum link keeps demodulating far past
    the point where its timing precision has become useless: a 25 m mast
    still closes at 15 km with 28 dB to spare while ranging to 30 m, which
    would put a position solution tens of metres out.

    Answers "how far can this anchor usefully range", by bisection on the
    ranging sigma. Returns zero when the target is not met even at 10 m.
    """
    if target_sigma_m <= 0.0:
        raise ValueError("target_sigma_m must be positive")

    def sigma_at(distance_m: float) -> float:
        x, y, z = receiver_prototype.position_m
        moved = Terminal(
            receiver_prototype.radio,
            receiver_prototype.antenna,
            (transmitter.position_m[0] + distance_m, y, z),
        )
        budget = evaluate_link(
            transmitter, moved, frequency_hz, obstruction=obstruction
        )
        if not budget.closes:
            return math.inf
        return ranging_sigma_m(budget, radio)

    low, high = 10.0, search_limit_m
    if sigma_at(low) > target_sigma_m:
        return 0.0
    if sigma_at(high) <= target_sigma_m:
        return high
    for _ in range(60):
        mid = 0.5 * (low + high)
        if sigma_at(mid) <= target_sigma_m:
            low = mid
        else:
            high = mid
    return low


def ranging_sigma_m(budget: LinkBudget, radio: Radio) -> float:
    """Ranging precision this part reaches on this link, one sigma, metres.

    The larger of two things: what the waveform permits at this
    signal-to-noise ratio, and the floor the part does not beat however
    good the signal gets. At long range the first binds and precision
    degrades with distance. At short range the second binds, which is why
    a narrowband radio does not deliver centimetres just because it is
    standing next to the anchor.

    Multipath is not in here. It belongs to the channel, not the waveform,
    and the channel model adds it.
    """
    return max(
        cramer_rao_sigma_m(budget, radio),
        float(radio.implementation_floor_m.value),
    )
