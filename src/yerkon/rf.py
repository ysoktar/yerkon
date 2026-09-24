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
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

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

    ``profile`` is the whole ground between the two ends, as (fraction
    along the path, surface height) pairs — the surface, so over a
    fetched site a roof is what it reports (ADR-0046). Diffraction is
    worked out from this rather than from the single worst point,
    because a path across a town is not one obstacle: over Kızılay the
    median link has three edges blocking it (ADR-0053). Empty for an
    obstruction somebody built by hand, and then the single peak above
    stands in for it.
    """

    peak_terrain_m: float = 0.0
    peak_at_fraction: float = 0.5
    clutter_loss_db: float = 0.0
    reflection_surface_m: float = 0.0
    surface_roughness_m: float = 0.0
    reflection_tilt_rad: float = 0.0
    reflection_at_fraction: float = 0.5
    profile: tuple = ()
    #: How much this particular link differs from the median the rest of
    #: this describes, in dB. Positive is more loss, and it is a fact
    #: about this link rather than a draw, so the same receiver at the
    #: same spot meets the same shadow every round (ADR-0055).
    shadow_db: float = 0.0
    #: The same profile as an (n, 2) array, where whoever built this had
    #: one to hand. A copy for speed rather than a second fact: it is left
    #: out of equality and of the printed form, and the budget falls back
    #: on ``profile`` when it is absent (ADR-0082).
    profile_array: Optional[np.ndarray] = field(
        default=None, compare=False, repr=False)

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
    # The same J(v) the whole-profile method is built from, said once
    # (ITU-R P.526-15 equation 31).
    return knife_edge_db(-clearance_m * math.sqrt(2.0) / fresnel_radius_m)


# --- Diffraction over the whole profile (ITU-R P.526-15 4.5) -------------
#
# One knife edge is one obstacle, and a path across a town is not one
# obstacle. Measured over Kızılay at 6 m to 1,5 m: of 215 links between
# 200 m and 1,2 km, only 15 % have a clear line of sight, the median has
# three separate edges blocking it, and the worst has sixteen. Taking
# the single worst of those and ignoring the rest is optimistic exactly
# where this project's urban row lives (ADR-0053).
#
# The method is the Recommendation's, not an invention here: Bullington's
# equivalent edge over the real profile, plus whatever a smooth earth of
# the same length would have cost beyond the same construction. The
# second term is what stops a long, gently curving path from coming back
# clear when the earth itself is the obstacle.


#: Effective earth radius in kilometres, for the standard atmosphere.
#: Refraction bends a ray downward, which is worth about a third more
#: radius than the geometric one.
EFFECTIVE_EARTH_KM = FOUR_THIRDS_EARTH * EARTH_RADIUS_M / 1000.0

#: Ground constants for the spherical-earth term, ITU-R P.527 "medium
#: dry ground": relative permittivity and conductivity in S/m. Land
#: rather than sea, because this project sites anchors beside roads.
GROUND_PERMITTIVITY = 22.0
GROUND_CONDUCTIVITY_S_M = 0.003


def knife_edge_db(v: float) -> float:
    """Loss over a single edge, by the Fresnel parameter ``v``.

    ITU-R P.526-15 equation (31), the approximation to the Fresnel
    integral that every one of these methods is built from. Zero below
    -0,78, where the edge is clear of the zone that matters.
    """
    if v <= -0.78:
        return 0.0
    return 6.9 + 20.0 * math.log10(math.sqrt((v - 0.1) ** 2 + 1.0) + v - 0.1)


def bullington_db(
    profile: Sequence[tuple[float, float]],
    tx_height_m: float,
    rx_height_m: float,
    distance_m: float,
    frequency_hz: float,
    curved: bool = True,
) -> float:
    """Loss over the whole profile, as one equivalent edge.

    ITU-R P.526-15 4.5.1. Bullington's construction: take the steepest
    line from each end to anything in between, and where those two lines
    cross is a single edge that stands for the lot. It is the oldest of
    the multiple-edge methods and it is the one the Recommendation
    builds on, because the alternatives that add each edge separately
    (Epstein-Peterson, Deygout) over-count when the edges are close
    together or of similar height — which over a town they always are.

    ``profile`` is (fraction along the path, surface height in metres),
    the same pairs the terrain hands out, and the surface includes
    whatever stands on it: over a fetched site a roof is the surface,
    which is why this sees buildings without being told about them.

    The empirical term at the end is the Recommendation's own, and it is
    what separates this from a bare knife edge: a path that is only just
    obstructed pays a little more than the single-edge answer, and one
    that is deeply obstructed pays up to ten decibels more.
    """
    if distance_m <= 0.0:
        return 0.0
    wavelength_m = SPEED_OF_LIGHT_M_S / frequency_hz
    span_km = distance_m / 1000.0

    # As arrays rather than a loop over pairs. Each line below is the
    # same arithmetic, in the same order, as the scalar form it replaced,
    # so the answer is identical to the last bit; only the per-point call
    # overhead is gone, and that overhead was most of what a simulation
    # spent its time on.
    pairs = np.asarray(profile, dtype=float).reshape(-1, 2)
    inside = (pairs[:, 0] > 0.0) & (pairs[:, 0] < 1.0)
    if not inside.any():
        return 0.0
    km = pairs[inside, 0] * span_km
    height = pairs[inside, 1]
    # Curvature enters as a correction to each profile height rather than
    # as a separate obstacle: over 20 km the earth itself rises 23 m into
    # the path, which is more than most of Ankara's buildings.
    bulge = (500.0 * km * (span_km - km) / EFFECTIVE_EARTH_KM if curved
             else np.zeros_like(km))

    straight = (rx_height_m - tx_height_m) / span_km
    from_tx = float(np.max((height + bulge - tx_height_m) / km))
    from_rx = float(np.max((height + bulge - rx_height_m) / (span_km - km)))
    # Exactly grazing: the two steepest lines are parallel and never
    # cross, so there is no equivalent edge to put anywhere and the
    # answer is the worst single intrusion — which is the same thing the
    # clear-path branch works out.
    if from_tx < straight or abs(from_tx + from_rx) < 1e-12:
        # Nothing rises above the line between the ends, so the worst
        # intrusion into the zone is the edge that stands for the path.
        sight = (tx_height_m * (span_km - km) + rx_height_m * km) / span_km
        worst = float(np.max((height + bulge - sight) * np.sqrt(
            0.002 * span_km / (wavelength_m * km * (span_km - km)))))
    else:
        crossing_km = ((rx_height_m - tx_height_m + from_rx * span_km)
                       / (from_tx + from_rx))
        if not 0.0 < crossing_km < span_km:
            return 0.0
        sight = ((tx_height_m * (span_km - crossing_km)
                  + rx_height_m * crossing_km) / span_km)
        worst = (tx_height_m + from_tx * crossing_km - sight) * math.sqrt(
            0.002 * span_km / (wavelength_m * crossing_km
                               * (span_km - crossing_km)))

    plain = knife_edge_db(worst)
    return plain + (1.0 - math.exp(-plain / 6.0)) * (10.0 + 0.02 * span_km)


def spherical_earth_db(
    distance_m: float, tx_height_m: float, rx_height_m: float,
    frequency_hz: float,
) -> float:
    """Loss over a smooth earth of this length, in dB.

    ITU-R P.526-15 4.2, the first term of the residue series. Nothing
    obstructs this path; the earth's own curve does. It is what a long
    link over open water or flat steppe actually pays, and it is here
    because the construction above cannot see it: a smooth profile has
    no edge to put an equivalent edge at.
    """
    span_km = distance_m / 1000.0
    ghz = frequency_hz / 1e9
    if span_km <= 0.0 or ghz <= 0.0:
        return 0.0

    # Horizontal polarisation, which is what these antennas are: the
    # vertical case differs by a factor this K does not carry.
    k = 0.036 * (EFFECTIVE_EARTH_KM * ghz) ** (-1.0 / 3.0) * (
        (GROUND_PERMITTIVITY - 1.0) ** 2
        + (18.0 * GROUND_CONDUCTIVITY_S_M / ghz) ** 2
    ) ** (-0.25)
    beta = ((1.0 + 1.6 * k ** 2 + 0.67 * k ** 4)
            / (1.0 + 4.5 * k ** 2 + 1.53 * k ** 4))

    x = 21.88 * beta * (ghz / EFFECTIVE_EARTH_KM ** 2) ** (1.0 / 3.0) * span_km
    if x < 1.6:
        distance_term = -20.0 * math.log10(x) - 5.6488 * x ** 1.425
    else:
        distance_term = 11.0 + 10.0 * math.log10(x) - 17.6 * x

    def height_term(height_m: float) -> float:
        y = 0.9575 * beta * (ghz ** 2 / EFFECTIVE_EARTH_KM) ** (
            1.0 / 3.0) * max(height_m, 0.0)
        if y > 2.0:
            return 17.6 * math.sqrt(y - 1.1) - 5.0 * math.log10(y - 1.1) - 8.0
        gained = 20.0 * math.log10(y + 0.1 * y ** 3) if y > 0.0 else -99.0
        # The Recommendation's floor: below it the height contributes
        # nothing that can be told from nothing.
        return max(gained, 2.0 + 20.0 * math.log10(k))

    loss = -distance_term - height_term(tx_height_m) - height_term(rx_height_m)
    return max(loss, 0.0)


def smooth_earth_heights_m(
    profile: Sequence[tuple[float, float]], distance_m: float,
    tx_height_m: float, rx_height_m: float,
) -> tuple[float, float]:
    """The two ends of the smooth earth this profile sits on.

    ITU-R P.452-16 equations (165) and (166): a least-squares line
    through the terrain, which is the surface the spherical-earth term
    is measured above. Held at or below the ground under each terminal,
    because a fitted line that rises above the ground it was fitted to
    would lift an antenna off its own mounting.
    """
    span_km = distance_m / 1000.0
    pairs = np.asarray(profile, dtype=float).reshape(-1, 2)
    if len(pairs) < 2 or span_km <= 0.0:
        return (0.0, 0.0)
    km = pairs[:, 0] * span_km
    height = pairs[:, 1]

    # Segment by segment, as arrays; the running sums are accumulated in
    # order, the way the loop added them, so the fit is the same number.
    step = km[1:] - km[:-1]
    first = float(np.cumsum(step * (height[1:] + height[:-1]))[-1])
    second = float(np.cumsum(step * (
        height[1:] * (2.0 * km[1:] + km[:-1])
        + height[:-1] * (km[1:] + 2.0 * km[:-1])))[-1])
    at_tx = (2.0 * first * span_km - second) / span_km ** 2
    at_rx = (second - first * span_km) / span_km ** 2
    return (min(at_tx, float(height[0]), tx_height_m),
            min(at_rx, float(height[-1]), rx_height_m))


def delta_bullington_db(
    profile: Sequence[tuple[float, float]],
    tx_height_m: float,
    rx_height_m: float,
    distance_m: float,
    frequency_hz: float,
) -> float:
    """Diffraction loss over this ground, in dB.

    ITU-R P.526-15 4.5.2. Two Bullington constructions and a smooth
    earth: the real profile's answer, plus however much a smooth earth
    of the same length would have cost over the same construction. The
    difference is the *delta*, and it is what keeps a long path over
    gentle ground from coming back clear when the horizon is the thing
    in the way.

    Heights are metres in the profile's own datum, which for a fetched
    site is metres above sea level with roofs folded in (ADR-0046).
    """
    # Read into an array once, for the three things below that use it.
    pairs = np.asarray(profile, dtype=float).reshape(-1, 2)
    on_the_ground = bullington_db(pairs, tx_height_m, rx_height_m,
                                  distance_m, frequency_hz)
    at_tx, at_rx = smooth_earth_heights_m(pairs, distance_m,
                                          tx_height_m, rx_height_m)
    above_tx = max(tx_height_m - at_tx, 0.0)
    above_rx = max(rx_height_m - at_rx, 0.0)

    flat = np.column_stack((pairs[:, 0], np.zeros(len(pairs))))
    on_a_smooth_earth = bullington_db(flat, above_tx, above_rx,
                                      distance_m, frequency_hz)
    curving = spherical_earth_db(distance_m, above_tx, above_rx,
                                 frequency_hz)
    return on_the_ground + max(curving - on_a_smooth_earth, 0.0)


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

    # Over the whole profile where there is one, and over the single
    # worst point where there is not. The Recommendation's method needs
    # ground to walk along; an Obstruction built by hand from two
    # numbers has none, and one edge is then the honest reading of what
    # it says (ADR-0053).
    if obstruction.profile:
        diffraction_db = delta_bullington_db(
            obstruction.profile if obstruction.profile_array is None
            else obstruction.profile_array,
            tx[2], rx[2], distance_m, frequency_hz)
    else:
        diffraction_db = diffraction_loss_db(clearance_m, fresnel_m)

    # Two effects, and they are not the same one. Ground reflection acts
    # even over perfectly flat ground, because the reflected ray cancels
    # the direct one. Diffraction acts when something rises into the path.
    # A flat site has the first and not the second.
    # Heights for the reflection are measured above the surface the
    # reflection actually lands on, which is why a mast on a ridge over a
    # valley behaves like a far taller mast on the flat.
    #
    # They are also not both payable at once, which is the next thing.
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
    # The larger of the two excesses over free space, not their sum.
    #
    # Both describe what the same ground does to the same link, and
    # adding them charges a link twice for one piece of ground. The
    # cancellation two-ray describes needs a direct ray to cancel; where
    # something blocks the path there is no direct ray, and the field
    # that arrives came over the edge. The Recommendation's own
    # structure builds the loss as free space plus diffraction (ITU-R
    # P.452, P.1812) and never adds a reflection term on top.
    #
    # So: over a clear path the reflection term is the larger and wins,
    # over a blocked one the diffraction is, and near the boundary the
    # answer is whichever is worse. Summed, a blocked path at range paid
    # 65 dB where the two terms were 40 and 25 (ADR-0058).
    free_space_db = free_space_path_loss_db(distance_m, frequency_hz)
    path_loss_db = (free_space_db
                    + max(spread_db - free_space_db, diffraction_db)
                    + obstruction.clutter_loss_db
                    + obstruction.shadow_db)

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
