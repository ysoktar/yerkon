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

from yerkon.hardware import SPEED_OF_LIGHT_M_S, Antenna, Radio
from yerkon.regulatory import TURKEY, SpectrumRule

BOLTZMANN_NOISE_DBM_PER_HZ = -174.0
"""Thermal noise density at room temperature."""

EARTH_RADIUS_M = 6371000.0
FOUR_THIRDS_EARTH = 4.0 / 3.0
"""Standard refraction factor. Radio bends slightly toward the ground, so
the horizon sits further away than the geometric one."""

FRESNEL_CLEARANCE_FRACTION = 0.6
"""Fraction of the first Fresnel zone that must be clear for the link to
behave as free space. Below this, diffraction loss sets in."""

DEFAULT_REGION = TURKEY
"""Which rulebook applies when a caller does not say.

Turkey, because that is where the deployment is. Every range figure this
module produces is a statement about a region, and the region has to be
visible rather than assumed; see ``SpectrumRule``.
"""


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

    Three separate things, and keeping them apart is the point.

    ``peak_terrain_m`` is the ground that comes closest to blocking the
    path, and it drives diffraction.

    ``reflection_surface_m`` is the ground elevation where the link's
    specular reflection lands, which is somewhere else entirely. Antenna
    heights for the two-ray model are measured above this, not above sea
    level and not above the obstacle. It is what makes a mast on a ridge
    behave like a much taller mast.

    ``surface_roughness_m`` is the root-mean-square height deviation of
    that reflecting patch. Rough ground scatters the reflection instead of
    returning it, which weakens the cancellation. The effect is strong at
    steep grazing angles and weak at shallow ones, so it matters at 2 km
    and barely at 10 km.

    ``reflection_at_fraction`` is where along the path it lands, which
    with a mast at one end and a vehicle at the other is nowhere near the
    middle.

    ``reflection_tilt_rad`` is how far that patch tilts along the path.
    A tilted mirror is still a mirror: it does not scatter the ray, it
    aims it somewhere else. Two degrees of slope swings the reflection by
    four, which over a few hundred metres puts it clear of the receiver
    entirely — and on real ground most patches are tilted (ADR-0026).
    Keeping it apart from roughness matters because they are different
    physics with the same symptom: one scatters the ray and the other
    misses with it.

    ``clutter_loss_db`` is everything the elevation model does not carry:
    buildings, vegetation, traffic.
    """

    peak_terrain_m: float = 0.0
    peak_at_fraction: float = 0.5
    clutter_loss_db: float = 0.0
    reflection_surface_m: float = 0.0
    surface_roughness_m: float = 0.0
    reflection_tilt_rad: float = 0.0
    reflection_at_fraction: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 < self.peak_at_fraction < 1.0:
            raise ValueError("peak_at_fraction must lie strictly inside the path")
        if self.clutter_loss_db < 0.0:
            raise ValueError("clutter cannot add signal")
        if self.surface_roughness_m < 0.0:
            raise ValueError("roughness is a magnitude")


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
    #: How much further than the straight line the signal actually
    #: travelled, in metres.
    #:
    #: Zero when the direct ray is clear. When something stands in the
    #: way the signal goes over it, and a range measurement times that
    #: longer path. It is a bias and it is always positive, which is what
    #: makes obstruction so much worse for positioning than the loss
    #: alone suggests: noise averages out over repeated measurements and
    #: this does not. See ADR-0019.
    excess_path_m: float = 0.0

    @property
    def effective_snr_db(self) -> float:
        """Signal-to-noise ratio after the receiver's correlation gain."""
        return self.snr_db + self._processing_gain_db

    _processing_gain_db: float = 0.0
    _threshold_db: float = 0.0
    _threshold_is_in_band: bool = True

    @property
    def closes(self) -> bool:
        """Whether the receiver can demodulate this at all.

        Compared against whichever ratio the part's threshold is quoted
        on. A LoRa figure is in-band and already assumes despreading; an
        impulse radio's is quoted after accumulation. Adding the
        correlation gain to a threshold that already contains it grants
        the link thirty decibels it does not have (ADR-0017).
        """
        return self._demodulation_snr_db >= self._threshold_db

    @property
    def _demodulation_snr_db(self) -> float:
        return (
            self.snr_db if self._threshold_is_in_band else self.effective_snr_db
        )

    @property
    def margin_db(self) -> float:
        """How much the link has to spare before it stops working."""
        return self._demodulation_snr_db - self._threshold_db

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


def specular_fraction(
    distance_m: float,
    tx_height_m: float,
    rx_height_m: float,
    roughness_m: float,
    frequency_hz: float,
) -> float:
    """How much of the reflection survives as a coherent ray, 0 to 1.

    The Ament factor, ``exp(-2 * (2 * pi * sigma * sin(psi) / lambda)^2)``,
    with ``psi`` the grazing angle. A surface is smooth relative to a very
    shallow angle however lumpy it looks from standing height, which is
    why this saves a 2 km link and not a 10 km one: at 10 km the grazing
    angle is under a tenth of a degree and it takes 10 m of roughness to
    scatter the reflection away.

    Returning a fraction rather than a yes or no lets the model sit
    between the two-ray and free-space extremes, which is where real
    ground sits.
    """
    if roughness_m <= 0.0:
        return 1.0
    grazing = (tx_height_m + rx_height_m) / distance_m
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    g = 2.0 * math.pi * roughness_m * grazing / wavelength_m
    return math.exp(-2.0 * g * g)


def aimed_fraction(
    distance_m: float,
    tilt_rad: float,
    frequency_hz: float,
    at_fraction: float = 0.5,
) -> float:
    """How much of the reflection still arrives where it can interfere.

    Roughness scatters a ray. Tilt does not: a sloping patch is a mirror
    that works perfectly and points somewhere else. A surface tilted by
    ``tau`` swings the reflected ray by ``2*tau``, which over half the
    path displaces it by ``2*tau*d/2``. If that displacement is large
    against the first Fresnel radius at the reflection point, the ray
    arrives too far off to cancel anything and the link is effectively
    free-space.

    ``at_fraction`` is where along the path the reflection lands, and it
    is not the middle. A 25 m mast talking to a receiver at 1,5 m puts it
    at 93 % of the way along, a few hundred metres from the receiver
    rather than kilometres, so the swung ray has far less room to drift
    off. Assuming the midpoint overstated the miss sevenfold on exactly
    the geometry this study is made of.

    Rolled off smoothly rather than cut, because the zone edge is not a
    wall: the contribution falls away over it rather than stopping.

    This is not a small correction on real ground. Reflecting patches
    under the Ankara scenarios are tilted a degree or two, and at those
    distances a degree or two is three to eight Fresnel radii of miss:
    between 84 % and 96 % of links, depending on the row (ADR-0026).
    """
    if tilt_rad == 0.0 or distance_m <= 0.0:
        return 1.0
    zone_m = first_fresnel_radius_m(distance_m, frequency_hz, at_fraction)
    if zone_m <= 0.0:
        return 1.0
    # The reflected ray still has to reach the receiver: how far it
    # travels after bouncing is what the swing acts over.
    to_receiver_m = distance_m * max(1.0 - at_fraction, 1e-6)
    missed_by = abs(2.0 * math.tan(abs(tilt_rad))) * to_receiver_m / zone_m
    return math.exp(-(missed_by ** 2))


def two_ray_path_loss_db(
    distance_m: float,
    tx_height_m: float,
    rx_height_m: float,
    frequency_hz: float,
    roughness_m: float = 0.0,
    tilt_rad: float = 0.0,
    reflection_at: float = 0.5,
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

    smooth = free_space_path_loss_db(breakpoint_m, frequency_hz) + 40.0 * math.log10(
        distance_m / breakpoint_m
    )
    rho = specular_fraction(
        distance_m, tx_height_m, rx_height_m, roughness_m, frequency_hz
    ) * aimed_fraction(distance_m, tilt_rad, frequency_hz, reflection_at)
    # Scattered ground returns no coherent ray to cancel with, so the
    # excess over free space is only paid for the part that stays
    # specular.
    return free_space + rho * (smooth - free_space)


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


def excess_path_m(
    clearance_m: float, distance_m: float, peak_at_fraction: float
) -> float:
    """How much further the signal goes when something is in the way.

    A knife edge standing ``h`` metres above the line of sight forces the
    ray over the top, and the detour is ``h^2/2 * (1/d1 + 1/d2)`` for the
    two leg lengths. Small for a gentle rise on a long link, and metres
    for a ridge across a short one.

    Zero when the path is clear. Partial Fresnel obstruction attenuates
    without lengthening: the direct ray still arrives first and a
    receiver times that, so only a blocked path is delayed.
    """
    if clearance_m >= 0.0 or distance_m <= 0.0:
        return 0.0
    first = distance_m * peak_at_fraction
    second = distance_m - first
    if first <= 0.0 or second <= 0.0:
        return 0.0
    height = -clearance_m
    return height * height / 2.0 * (1.0 / first + 1.0 / second)


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


def regulatory_eirp_limit_dbm(
    bandwidth_hz: float,
    antenna_gain_dbi: float = 0.0,
    radio_max_dbm: float = 99.0,
    region: SpectrumRule = DEFAULT_REGION,
) -> float:
    """Highest legal radiated power for this configuration, in dBm.

    Delegates to the region's rule. Under the Turkish and European rules
    the density cap binds at every SX1280 bandwidth, so legal power rises
    with bandwidth; thermal noise rises with it by the same factor, which
    is why widening the ranging bandwidth costs no range. Under the
    American rule the ceiling is on conducted power instead and does not
    move with bandwidth at all.
    """
    return region.permitted_eirp_dbm(bandwidth_hz, antenna_gain_dbi, radio_max_dbm)


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
    region: SpectrumRule = DEFAULT_REGION,
) -> LinkBudget:
    """The whole chain, for one pair of terminals at one instant.

    ``region`` decides how much the transmitter may radiate, and it moves
    the answer by more than twenty decibels between jurisdictions. Pass it
    explicitly wherever the result is reported.
    """
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
        eirp_dbm = min(
            eirp_dbm,
            regulatory_eirp_limit_dbm(
                float(radio.ranging_bandwidth_hz.value),
                antenna_gain_dbi=tx_gain,
                radio_max_dbm=output_dbm,
                region=region,
            ),
            # An ultra-wideband rating is already an emission limit rather
            # than a conducted power, so antenna gain cannot be added on
            # top of it.
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
    # Heights for the reflection are measured above the surface the
    # reflection actually lands on, which is why a mast on a ridge over a
    # valley behaves like a far taller mast on the flat.
    surface_m = obstruction.reflection_surface_m
    spread_db = two_ray_path_loss_db(
        distance_m,
        max(tx[2] - surface_m, 0.1),
        max(rx[2] - surface_m, 0.1),
        frequency_hz,
        roughness_m=obstruction.surface_roughness_m,
        tilt_rad=obstruction.reflection_tilt_rad,
        reflection_at=obstruction.reflection_at_fraction,
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
        excess_path_m=excess_path_m(clearance_m, distance_m, fraction),
        _processing_gain_db=float(radio.processing_gain_db.value),
        _threshold_db=float(radio.demodulation_threshold_db.value),
        _threshold_is_in_band=radio.threshold_is_in_band,
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


#: How far the range searches look before giving up.
#:
#: A result sitting exactly on this is a search that ran out of room, not
#: a link that stopped there, and anything reporting one should say so.
DEFAULT_SEARCH_LIMIT_M = 60_000.0


def closure_range_m(
    transmitter: Terminal,
    receiver_prototype: Terminal,
    frequency_hz: float = 2450e6,
    obstruction: Optional[Obstruction] = None,
    search_limit_m: float = DEFAULT_SEARCH_LIMIT_M,
    region: SpectrumRule = TURKEY,
) -> float:
    """Farthest distance at which the link still demodulates at all.

    Always at least ``usable_range_m`` and usually far beyond it. The gap
    between the two is the whole of ADR-0007: a link that still carries
    packets has long since stopped carrying a useful measurement, and
    quoting the closure distance as coverage is the error this pair of
    functions exists to make impossible to hide.
    """
    def closes_at(distance_m: float) -> bool:
        _, y, z = receiver_prototype.position_m
        moved = Terminal(
            receiver_prototype.radio,
            receiver_prototype.antenna,
            (transmitter.position_m[0] + distance_m, y, z),
        )
        return evaluate_link(
            transmitter, moved, frequency_hz, obstruction=obstruction, region=region
        ).closes

    low, high = 10.0, search_limit_m
    if not closes_at(low):
        return 0.0
    if closes_at(high):
        return high
    for _ in range(60):
        mid = 0.5 * (low + high)
        if closes_at(mid):
            low = mid
        else:
            high = mid
    return low


def usable_range_m(
    transmitter: Terminal,
    receiver_prototype: Terminal,
    radio: Radio,
    target_sigma_m: float,
    frequency_hz: float = 2450e6,
    obstruction: Optional[Obstruction] = None,
    search_limit_m: float = DEFAULT_SEARCH_LIMIT_M,
    region: SpectrumRule = TURKEY,
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
            transmitter, moved, frequency_hz, obstruction=obstruction, region=region
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
