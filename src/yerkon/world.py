"""The physical situation: ground, structures, roads, and what moves on them.

This module owns truth. Nothing in `estimator` may import it, and
`tests/test_architecture.py` enforces that, because the previous codebase's
worst defect was a filter reading the receiver's true position through a
"map" measurement.

Two things here decide the whole study. The terrain, because ADR-0002
makes range an outcome of geometry and the ground is most of that
geometry. And the mounting catalogue, because the owner's deployment mixes
cheap low structures that already exist with expensive tall ones that do
not, and the ratio between them is the design question.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from yerkon.evidence import Provenance, Sourced
from yerkon.hardware import Radio, SX1280
from yerkon.settings import DEFAULTS, Settings
from yerkon.rf import Obstruction, first_fresnel_radius_m

Metres = float


# --- Ground ---------------------------------------------------------------


@dataclass(frozen=True)
class Terrain:
    """Ground elevation over the site, and what sits on top of it.

    ``elevation_m`` is the bare earth, the shape a survey would give.

    ``micro_roughness_m`` is the height scatter the elevation model is too
    coarse to carry: furrows, verge vegetation, kerbs, parked vehicles. It
    does not change where the ground is, but it decides how much of a
    grazing reflection comes back as a coherent ray, so it belongs to the
    surface rather than to the clutter budget.

    ``clutter_loss_db_per_km`` is absorption by things standing on the
    ground, which height does not clear.
    """

    elevation_m: Callable[[float, float], float] = field(repr=False)
    clutter_loss_db_per_km: float = 0.0
    micro_roughness_m: float = 0.0
    description: str = "flat"

    def __post_init__(self) -> None:
        if self.clutter_loss_db_per_km < 0.0:
            raise ValueError("clutter cannot add signal")
        if self.micro_roughness_m < 0.0:
            raise ValueError("roughness is a magnitude")

    def height_at(self, x: float, y: float) -> float:
        return float(self.elevation_m(x, y))

    def profile_between(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        samples: int = 64,
    ) -> list[tuple[float, float]]:
        """Ground elevation along the path, as (fraction, elevation) pairs.

        Sampled rather than analytic because a real site arrives as a
        raster and this keeps the interface the same either way.
        """
        if samples < 2:
            raise ValueError("a profile needs at least two samples")
        out = []
        for i in range(samples + 1):
            f = i / samples
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            out.append((f, self.height_at(x, y)))
        return out

    def obstruction_between(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        samples: int = 64,
    ) -> Obstruction:
        """The worst intrusion into this path, for the link budget.

        Reports the point that comes closest to blocking the link, which
        is not the point with the least clearance and not the highest
        ground. The Fresnel zone is narrow at the ends and wide in the
        middle, so a gap is only meaningful next to the zone radius there.
        A hill 50 m under the path beside the transmitter, where the zone
        is 2 m wide, obstructs nothing; the same gap at the midpoint,
        where the zone is 17 m wide, is clear too, but a 5 m gap there is
        not.

        Comparing raw gaps instead would pick the hill by the
        transmitter and report a clear path as blocked.
        """
        distance_m = math.dist(a, b)
        frequency_hz = 2450e6
        profile = self.profile_between(a, b, samples)

        worst_fraction = 0.5
        worst_ratio = math.inf
        worst_ground = a[2]

        for fraction, ground_m in profile:
            if fraction <= 0.0 or fraction >= 1.0:
                continue
            sight_m = a[2] + (b[2] - a[2]) * fraction
            zone_m = first_fresnel_radius_m(distance_m, frequency_hz, fraction)
            ratio = (sight_m - ground_m) / zone_m
            if ratio < worst_ratio:
                worst_ratio, worst_fraction, worst_ground = ratio, fraction, ground_m

        surface_m, roughness_m = self._reflection_surface(a, b, profile)

        return Obstruction(
            peak_terrain_m=worst_ground,
            peak_at_fraction=worst_fraction,
            clutter_loss_db=self.clutter_loss_db_per_km * distance_m / 1000.0,
            reflection_surface_m=surface_m,
            surface_roughness_m=roughness_m,
        )

    def _reflection_surface(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        profile: Sequence[tuple[float, float]],
    ) -> tuple[float, float]:
        """Where the specular reflection lands, and how rough it is there.

        Over a flat plane the reflection point sits at the fraction
        ``h1 / (h1 + h2)`` along the path. Over real ground the heights
        that decide that fraction are themselves heights above the
        reflecting surface, so this iterates: guess the surface, find the
        point, re-read the surface, repeat. It settles in a few rounds.

        Roughness is the scatter of the ground around the reflecting
        patch, added to the terrain's own micro-roughness. A patch on a
        smooth valley floor returns a clean ray; one straddling a ridge
        does not.
        """
        heights = [h for _, h in profile]
        surface_m = sum(heights) / len(heights)

        for _ in range(4):
            h1 = max(a[2] - surface_m, 0.1)
            h2 = max(b[2] - surface_m, 0.1)
            fraction = min(max(h1 / (h1 + h2), 0.02), 0.98)
            surface_m = self._interpolate(profile, fraction)

        # Scatter over the patch the reflection illuminates, taken as the
        # middle fifth of the path around the reflection point.
        h1 = max(a[2] - surface_m, 0.1)
        h2 = max(b[2] - surface_m, 0.1)
        centre = min(max(h1 / (h1 + h2), 0.02), 0.98)
        window = [
            h for f, h in profile if abs(f - centre) <= 0.1
        ] or [surface_m]
        mean = sum(window) / len(window)
        spread = math.sqrt(sum((h - mean) ** 2 for h in window) / len(window))

        return surface_m, math.hypot(spread, self.micro_roughness_m)

    @staticmethod
    def _interpolate(profile: Sequence[tuple[float, float]], fraction: float) -> float:
        for (f0, h0), (f1, h1) in zip(profile, profile[1:]):
            if f0 <= fraction <= f1:
                if f1 == f0:
                    return h0
                t = (fraction - f0) / (f1 - f0)
                return h0 + (h1 - h0) * t
        return profile[-1][1]


def flat_terrain(
    elevation_m: float = 0.0,
    clutter_loss_db_per_km: float = 0.0,
    micro_roughness_m: float = 0.0,
) -> Terrain:
    """Perfectly level ground. The worst case for ground reflection."""
    return Terrain(
        elevation_m=lambda x, y: elevation_m,
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=micro_roughness_m,
        description="flat at {:.0f} m".format(elevation_m),
    )


def terrain_from_site(site: "Site", clutter_loss_db_per_km: float = 0.0) -> Terrain:
    """Turn fetched ground into terrain the link budget can use.

    Roughness comes from the site's own detrended scatter rather than
    being chosen, so real ground brings its own reflection behaviour with
    it. Where the site has buildings, a point inside a footprint reports
    the roof rather than the ground, because that is the surface a path
    over it has to clear.

    Folding buildings into the elevation rather than handling them
    separately keeps one answer to "how high is the obstacle here", which
    is the only question the link budget asks.
    """
    buildings = site.buildings
    have_buildings = buildings is not None and not buildings.is_empty

    def elevation(x: float, y: float) -> float:
        ground = site.height_at(x, y)
        if not have_buildings:
            return ground
        inside = (
            (x - buildings.centre_x_m) ** 2 + (y - buildings.centre_y_m) ** 2
        ) <= buildings.radius_m**2
        if not inside.any():
            return ground
        return ground + float(buildings.height_m[inside].max())

    return Terrain(
        elevation_m=elevation,
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=site.roughness_m(),
        description=site.manifest.describe(),
    )


def rolling_terrain(
    amplitude_m: float,
    wavelength_m: float,
    clutter_loss_db_per_km: float = 0.0,
    micro_roughness_m: float = 0.0,
    seed: int = 0,
) -> Terrain:
    """Smooth hills. Deterministic given the seed.

    Two sine components at incommensurate wavelengths, so the profile does
    not repeat over a corridor and no anchor sits at a lucky spot by
    construction.
    """
    phase = (seed % 360) * math.pi / 180.0

    def elevation(x: float, y: float) -> float:
        long_wave = math.sin(2.0 * math.pi * x / wavelength_m + phase)
        short_wave = 0.35 * math.sin(
            2.0 * math.pi * x / (wavelength_m * 0.37) + 2.0 * phase
        )
        across = 0.2 * math.sin(2.0 * math.pi * y / (wavelength_m * 0.6))
        return amplitude_m * (long_wave + short_wave + across) / 1.55

    return Terrain(
        elevation_m=elevation,
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=micro_roughness_m,
        description="rolling, {:.0f} m over {:.0f} m".format(amplitude_m, wavelength_m),
    )


# --- Structures -----------------------------------------------------------


@dataclass(frozen=True)
class MountingOption:
    """Somewhere an anchor can go, and what putting one there costs.

    The deployment mixes structures that already stand beside the road
    with structures that have to be built. They differ in three ways that
    all matter: how high they are, what they cost beyond the radio, and
    whether power and a data connection are already there.
    """

    kind: str
    height_m: Sourced
    #: Cost of the structure and its installation, beyond the anchor's own
    #: bill of materials. Zero for a structure that already exists and can
    #: carry the unit as-is.
    site_cost_tl: Sourced
    #: True when the structure already has mains power, so the anchor does
    #: not need its own supply and its energy is someone else's line item.
    has_power: bool
    #: True when the structure already carries a data connection.
    has_backhaul: bool

    def __post_init__(self) -> None:
        if float(self.height_m.value) <= 0.0:
            raise ValueError("a mounting height must be positive")
        if float(self.site_cost_tl.value) < 0.0:
            raise ValueError("a site cannot pay you to use it")


def mountings(settings: Settings = DEFAULTS) -> dict:
    """The catalogue, built from a settings file.

    Heights and costs are figures nobody supplied, so they are not
    written here. A run that has real ones loads its own file and builds
    its own catalogue from it; see `yerkon.settings`.
    """
    def option(key: str, kind: str, has_power: bool, has_backhaul: bool):
        return MountingOption(
            kind=kind,
            height_m=settings.sourced("mounting.{}.height_m".format(key)),
            site_cost_tl=settings.sourced("mounting.{}.site_cost_tl".format(key)),
            has_power=has_power,
            has_backhaul=has_backhaul,
        )

    return {
        "roadside_sign": option("roadside_sign", "roadside sign", False, False),
        "sign_gantry": option("sign_gantry", "sign gantry", True, False),
        "billboard": option("billboard", "billboard", True, False),
        "lighting_column": option("lighting_column", "lighting column", True, False),
        "tall_mast": option("tall_mast", "tall mast", False, False),
        # A tunnel already has power and a communications spine along its
        # length, for lighting, ventilation and its own systems. That is
        # most of why a tunnel deployment costs less per anchor to run
        # than an open-road one, despite needing far more anchors.
        "tunnel_bracket": option("tunnel_bracket", "tunnel bracket", True, True),
    }


MOUNTINGS = mountings()

ROADSIDE_SIGN = MOUNTINGS["roadside_sign"]
SIGN_GANTRY = MOUNTINGS["sign_gantry"]
BILLBOARD = MOUNTINGS["billboard"]
LIGHTING_COLUMN = MOUNTINGS["lighting_column"]
TALL_MAST = MOUNTINGS["tall_mast"]
TUNNEL_BRACKET = MOUNTINGS["tunnel_bracket"]
"""Inside a tunnel, where power and backhaul already run the length of it."""


EXISTING_STRUCTURES = (ROADSIDE_SIGN, SIGN_GANTRY, BILLBOARD, LIGHTING_COLUMN)
"""Structures already beside a Turkish highway. Fitting a unit to one of
these avoids building anything, which is why the owner wants them used."""


# --- Placed hardware ------------------------------------------------------


@dataclass(frozen=True)
class Anchor:
    """One transmitter, where it is, what it is bolted to, and what is in it.

    The radio belongs to the anchor rather than to the deployment,
    because a real corridor does not carry one kind. The report names
    three: a spread module for towns, the same silicon behind an
    amplifier for open country, and an impulse radio for tunnels and
    other confined places. A deployment that runs through all three
    carries all three, and a receiver ranges only against the ones it
    shares a waveform with.
    """

    identifier: str
    ground_position_m: tuple[float, float]
    mounting: MountingOption
    terrain: Terrain = field(repr=False)
    radio: Radio = SX1280

    @property
    def position_m(self) -> tuple[float, float, float]:
        x, y = self.ground_position_m
        return (x, y, self.terrain.height_at(x, y) + float(self.mounting.height_m.value))


MAX_HIGHWAY_GRADE = 0.06
"""Steepest sustained grade a motorway is built to, as a fraction.

Turkish motorway design follows the usual 6% ceiling for main
carriageways. It matters here because a road is not draped over the bare
ground: it is cut through the high points and filled across the low ones
until it meets this limit. Sampling raw terrain instead produces 10% and
steeper, which no vehicle scenario should be built on.
"""


@dataclass(frozen=True)
class Road:
    """A carriageway with its own vertical alignment.

    ADR-0004: no road in this codebase sits at a constant elevation. A
    vehicle's true height is the road surface under it plus its antenna
    offset, and the estimator is never told either.

    ``surface_m`` is the built road surface, which is not the terrain.
    Build it with :func:`graded_alignment` so the result respects a
    maximum grade, or pass the terrain directly for a road that follows
    the ground exactly.
    """

    centreline_m: Sequence[tuple[float, float]]
    terrain: Terrain = field(repr=False)
    half_width_m: float = 12.0
    surface_m: Optional[Callable[[float], float]] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if len(self.centreline_m) < 2:
            raise ValueError("a road needs at least two points")

    def surface_height_at(self, distance_m: float) -> float:
        """Height of the road surface at a distance along it."""
        if self.surface_m is not None:
            return float(self.surface_m(distance_m))
        x, y = self._ground_point(distance_m)
        return self.terrain.height_at(x, y)

    @property
    def length_m(self) -> float:
        return sum(
            math.dist(a, b)
            for a, b in zip(self.centreline_m, self.centreline_m[1:])
        )

    def _ground_point(self, distance_m: float, offset_m: float = 0.0) -> tuple[float, float]:
        if distance_m < 0.0:
            raise ValueError("distance along a road cannot be negative")
        if distance_m > self.length_m + 1e-6:
            raise ValueError("distance beyond the end of the road")
        travelled = 0.0
        segments = list(zip(self.centreline_m, self.centreline_m[1:]))
        for index, (a, b) in enumerate(segments):
            segment = math.dist(a, b)
            last = index == len(segments) - 1
            if travelled + segment >= distance_m or last:
                f = 0.0 if segment == 0.0 else (distance_m - travelled) / segment
                f = min(max(f, 0.0), 1.0)
                x = a[0] + (b[0] - a[0]) * f
                y = a[1] + (b[1] - a[1]) * f
                if offset_m and segment > 0.0:
                    nx, ny = -(b[1] - a[1]) / segment, (b[0] - a[0]) / segment
                    x += nx * offset_m
                    y += ny * offset_m
                return (x, y)
            travelled += segment
        raise ValueError("distance beyond the end of the road")

    def point_at(self, distance_m: float, offset_m: float = 0.0) -> tuple[float, float, float]:
        """A point on the carriageway, ``distance_m`` along and offset across."""
        x, y = self._ground_point(distance_m, offset_m)
        return (x, y, self.surface_height_at(distance_m))

    def grade_at(self, distance_m: float, step_m: float = 10.0) -> float:
        """Slope of the carriageway, as a fraction. Rise over run."""
        ahead_m = min(distance_m + step_m, self.length_m)
        run = ahead_m - distance_m
        if run <= 0.0:
            return 0.0
        rise = self.surface_height_at(ahead_m) - self.surface_height_at(distance_m)
        return rise / run


def graded_alignment(
    centreline_m: Sequence[tuple[float, float]],
    terrain: Terrain,
    max_grade: float = MAX_HIGHWAY_GRADE,
    step_m: float = 50.0,
) -> Callable[[float], float]:
    """A road surface that follows the ground within a grade limit.

    Walks the terrain forwards and then backwards, each pass lowering any
    point that would need a steeper climb than ``max_grade`` to reach.
    What survives both passes is the highest profile that stays at or
    below the ground and meets the grade limit everywhere.

    This cuts through hills. It does not fill valleys, so where a real
    road would run across an embankment or a viaduct this one dives into
    the hollow and climbs out at the limiting grade. That makes the
    modelled road longer in the vertical and its receiver lower in dips
    than the real thing, which is the conservative direction for a study
    about whether links stay clear. Add a fill pass if a scenario needs
    embankments.
    """
    if max_grade <= 0.0:
        raise ValueError("max_grade must be positive")

    length_m = sum(
        math.dist(a, b) for a, b in zip(centreline_m, centreline_m[1:])
    )
    n = max(int(length_m / step_m), 1)
    spacing = length_m / n

    road = Road(centreline_m=centreline_m, terrain=terrain)
    ground = [
        terrain.height_at(*road._ground_point(min(i * spacing, length_m)))
        for i in range(n + 1)
    ]

    limit = max_grade * spacing
    profile = list(ground)
    for i in range(1, n + 1):
        profile[i] = min(profile[i], profile[i - 1] + limit)
    for i in range(n - 1, -1, -1):
        profile[i] = min(profile[i], profile[i + 1] + limit)

    def surface(distance_m: float) -> float:
        d = min(max(distance_m, 0.0), length_m)
        position = d / spacing
        index = min(int(position), n - 1)
        f = position - index
        return profile[index] + (profile[index + 1] - profile[index]) * f

    return surface
