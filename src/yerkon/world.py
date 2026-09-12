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
from typing import Callable, Optional, Sequence, TYPE_CHECKING

from yerkon.evidence import Sourced
from yerkon.hardware import Radio, SX1280
from yerkon.language import say
from yerkon.numbers import decimal_comma
from yerkon.settings import DEFAULTS, Settings
from yerkon.rf import Obstruction, first_fresnel_radius_m

if TYPE_CHECKING:  # pragma: no cover
    from yerkon.site.model import Site

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

    ``patches`` makes that roughness vary from place to place instead of
    being one number for the whole site. Where it is set,
    ``micro_roughness_m`` remains the site's typical figure — the
    patchwork is centred on it — and the reflection asks what the ground
    is like *there* (ADR-0026).
    """

    elevation_m: Callable[[float, float], float] = field(repr=False)
    clutter_loss_db_per_km: float = 0.0
    micro_roughness_m: float = 0.0
    description: str = ""
    patches: Optional["Patchwork"] = None

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

        surface_m, roughness_m, tilt_rad, at_fraction = (
            self._reflection_surface(a, b, profile, distance_m)
        )

        return Obstruction(
            peak_terrain_m=worst_ground,
            peak_at_fraction=worst_fraction,
            clutter_loss_db=self.clutter_loss_db_per_km * distance_m / 1000.0,
            reflection_surface_m=surface_m,
            surface_roughness_m=roughness_m,
            reflection_tilt_rad=tilt_rad,
            reflection_at_fraction=at_fraction,
        )

    def _reflection_surface(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        profile: Sequence[tuple[float, float]],
        distance_m: float = 0.0,
    ) -> tuple[float, float, float, float]:
        """Where the specular reflection lands, how rough it is, and its tilt.

        Over a flat plane the reflection point sits at the fraction
        ``h1 / (h1 + h2)`` along the path. Over real ground the heights
        that decide that fraction are themselves heights above the
        reflecting surface, so this iterates: guess the surface, find the
        point, re-read the surface, repeat. It settles in a few rounds.

        Roughness is the scatter of the ground around the reflecting
        patch, added to the terrain's own micro-roughness. A patch on a
        smooth valley floor returns a clean ray; one straddling a ridge
        does not.

        Where the site has a patchwork, the micro-roughness is read at
        the reflection point rather than taken as one figure for
        everywhere: tarmac and a ploughed field scatter a grazing ray
        very differently, and which one the reflection lands on is a fact
        about that place rather than about the measurement (ADR-0026).
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
            (f, h) for f, h in profile if abs(f - centre) <= 0.1
        ] or [(centre, surface_m)]

        here_x = a[0] + (b[0] - a[0]) * centre
        here_y = a[1] + (b[1] - a[1]) * centre
        spread, slope = _plane_through(window)
        # Along the path rather than per unit fraction, which is what an
        # angle needs.
        tilt_rad = math.atan(slope / distance_m) if distance_m > 0.0 else 0.0
        micro_m = (
            self.patches(here_x, here_y) if self.patches is not None
            else self.micro_roughness_m
        )
        return surface_m, math.hypot(spread, micro_m), tilt_rad, centre

    @staticmethod
    def _interpolate(profile: Sequence[tuple[float, float]], fraction: float) -> float:
        for (f0, h0), (f1, h1) in zip(profile, profile[1:]):
            if f0 <= fraction <= f1:
                if f1 == f0:
                    return h0
                t = (fraction - f0) / (f1 - f0)
                return h0 + (h1 - h0) * t
        return profile[-1][1]


def _plane_through(window: Sequence[tuple[float, float]]) -> tuple[float, float]:
    """The plane a stretch of ground sits on: how tilted, and how rough about it.

    Roughness means deviation from the surface, and a hillside is a
    surface. Measuring scatter about a window's *mean height* counts the
    tilt as roughness, which is not a small error: a 12 % grade over a
    reflecting patch reads as 2,8 m of scatter where the ground is
    actually smooth to 7 cm — a factor of forty, and enough to switch the
    coherent reflection off everywhere that is not level (ADR-0026).

    The site's own `roughness_m` already detrends for exactly this
    reason. This is the same thing, done where the reflection is — and it
    hands back the slope as well, because a tilted patch does not scatter
    the ray, it aims it elsewhere, and that is a separate term.
    """
    count = len(window)
    if count < 3:
        return 0.0, 0.0

    mean_f = sum(f for f, _ in window) / count
    mean_h = sum(h for _, h in window) / count
    across = sum((f - mean_f) ** 2 for f, _ in window)
    if across <= 0.0:
        return 0.0, 0.0

    slope = sum((f - mean_f) * (h - mean_h) for f, h in window) / across
    left = sum(
        (h - (mean_h + slope * (f - mean_f))) ** 2 for f, h in window
    )
    return math.sqrt(left / count), slope


# --- What the ground is made of, patch by patch ---------------------------


def _mixed(*numbers: int) -> int:
    """A stable hash of some integers. Not Python's.

    `hash()` is salted per process, so a patch would be smooth in one
    worker and rough in another the moment the work was spread over
    cores (ADR-0025). Ground that changed depending on how many
    processes were free would make every published figure a property of
    the machine.
    """
    mixed = 0x9E3779B97F4A7C15
    for number in numbers:
        mixed ^= (int(number) + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        mixed = (mixed * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        mixed ^= mixed >> 27
        mixed = (mixed * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        mixed ^= mixed >> 31
    return mixed


def _normal_at(*numbers: int) -> float:
    """A standard normal drawn from a position rather than from a stream.

    The distinction is the whole point. A patch of ground is rough or
    smooth as a fact about that place: a receiver ranging to the same
    anchor from the same spot meets the same reflection every time, so
    this must be a function of where, not a draw from a generator that
    moves on. Drawn as noise it would average out over a round, and this
    does not — like the survey error and the excess path before it
    (ADR-0019).
    """
    mixed = _mixed(*numbers)
    # Box-Muller from two halves of the mixed word. Nudged off zero so
    # the logarithm is finite.
    first = ((mixed & 0xFFFFFFFF) + 0.5) / 0x100000000
    second = (((mixed >> 32) & 0xFFFFFFFF) + 0.5) / 0x100000000
    return math.sqrt(-2.0 * math.log(first)) * math.cos(2.0 * math.pi * second)


@dataclass(frozen=True)
class Scale:
    """One scale at which ground cover changes, and by how much.

    ``size_m`` is how far you travel before the cover is something else:
    hundreds of metres for tarmac giving way to a field, tens for the
    texture within one. ``spread`` is how much the roughness varies
    between patches at that scale, as the width of a log-normal in
    multiples of the typical figure. Zero means every patch at this
    scale is the same.
    """

    size_m: float
    spread: float

    def __post_init__(self) -> None:
        if self.size_m <= 0.0:
            raise ValueError("a patch has a size")
        if self.spread < 0.0:
            raise ValueError("a spread is a magnitude")

    def multiplier(self, x: float, y: float, layer: int, seed: int) -> float:
        """How much rougher or smoother this patch is than typical.

        Log-normal, and centred so the *mean square* is one rather than
        the mean. Roughness enters the reflection through its square, so
        this leaves the site's measured roughness meaning exactly what it
        measured, and adds only the variation around it.
        """
        if self.spread <= 0.0:
            return 1.0
        cell_x = math.floor(x / self.size_m)
        cell_y = math.floor(y / self.size_m)
        z = _normal_at(cell_x, cell_y, layer, seed)
        return math.exp(self.spread * z - self.spread * self.spread)


@dataclass(frozen=True)
class Patchwork:
    """Ground that is not the same everywhere, at two or three scales.

    One roughness figure for a whole site says every reflection meets the
    same surface. Real ground is tarmac, then verge, then a ploughed
    field, and the Ament factor is exponential in roughness times the
    grazing angle: at three hundred metres, five centimetres of scatter
    leaves 97 % of the reflection coherent and half a metre leaves 7 %.
    Between them is the difference between a two-ray null and none, so a
    single number decides that question the same way everywhere and a
    patchwork lets it vary — which is what it does.

    Scales combine in quadrature, because independent height variations
    add as variances. With the multipliers centred on a mean square of
    one, the whole thing still averages to ``typical_m``.
    """

    typical_m: float
    scales: tuple = ()
    seed: int = 0

    def __post_init__(self) -> None:
        if self.typical_m < 0.0:
            raise ValueError("roughness is a magnitude")

    @property
    def levels(self) -> int:
        return len(self.scales)

    def __call__(self, x: float, y: float) -> float:
        """Roughness of the ground at a point, in metres."""
        if not self.scales or self.typical_m <= 0.0:
            return self.typical_m
        # Each scale carries an equal share of the variance, so adding a
        # third level splits the same total finer rather than making the
        # ground rougher.
        share = self.typical_m / math.sqrt(len(self.scales))
        total = 0.0
        for layer, scale in enumerate(self.scales):
            here = share * scale.multiplier(x, y, layer, self.seed)
            total += here * here
        return math.sqrt(total)

    def describe(self) -> str:
        if not self.scales:
            return "{:.2f} m everywhere".format(self.typical_m)
        return "{:.2f} m typical over {} scales: {}".format(
            self.typical_m, len(self.scales),
            ", ".join("{:.0f} m ±{:.0%}".format(s.size_m, s.spread)
                      for s in self.scales),
        )


def patchwork(
    typical_m: float,
    patch_m: float,
    spread: float,
    levels: int = 2,
    seed: int = 0,
) -> Patchwork:
    """A patchwork of the usual shape: each level six times finer.

    Six because it separates the scales enough that they do not beat
    against each other, and not so much that the third one is below
    anything the reflection integrates over.
    """
    if levels < 1:
        raise ValueError("a patchwork has at least one scale")
    return Patchwork(
        typical_m=typical_m,
        scales=tuple(
            Scale(size_m=patch_m / (6.0 ** level), spread=spread)
            for level in range(levels)
        ),
        seed=seed,
    )


# --- The shapes ground comes in -------------------------------------------
#
# Each of these is a callable rather than a closure, and the difference
# is not style. A closure cannot cross a process boundary, so a Terrain
# built from one drags the whole Scenario holding it into a single core:
# the table, the error dissection and the deployment search were all
# stuck on one, and each of them is dozens of independent simulations
# (ADR-0025). Written this way they pickle, and the work fans out.


@dataclass(frozen=True)
class Level:
    """One height everywhere. A laboratory instrument; see `flat_terrain`."""

    elevation_m: float = 0.0

    def __call__(self, x: float, y: float) -> float:
        return self.elevation_m


@dataclass(frozen=True)
class Rolling:
    """Smooth hills from two sine components at incommensurate wavelengths.

    They do not repeat over a corridor, so no anchor sits at a lucky spot
    by construction.
    """

    amplitude_m: float
    wavelength_m: float
    seed: int = 0

    @property
    def phase(self) -> float:
        return (self.seed % 360) * math.pi / 180.0

    def __call__(self, x: float, y: float) -> float:
        phase = self.phase
        long_wave = math.sin(2.0 * math.pi * x / self.wavelength_m + phase)
        short_wave = 0.35 * math.sin(
            2.0 * math.pi * x / (self.wavelength_m * 0.37) + 2.0 * phase
        )
        across = 0.2 * math.sin(2.0 * math.pi * y / (self.wavelength_m * 0.6))
        return self.amplitude_m * (long_wave + short_wave + across) / 1.55


@dataclass(frozen=True)
class Sloping:
    """A straight floor between two portals. The inside of a bore."""

    entry_elevation_m: float
    exit_elevation_m: float
    length_m: float

    def __call__(self, x: float, y: float) -> float:
        along = min(max(x / self.length_m, 0.0), 1.0)
        return self.entry_elevation_m + (
            self.exit_elevation_m - self.entry_elevation_m
        ) * along


@dataclass(frozen=True)
class Fetched:
    """Real ground, and whatever stands on it.

    A point inside a building's footprint reports the roof rather than
    the ground, because that is the surface a path over it has to clear.
    Folding the two together keeps one answer to "how high is the
    obstacle here", which is the only question the link budget asks.
    """

    site: "Site" = field(repr=False)

    def __call__(self, x: float, y: float) -> float:
        ground = self.site.height_at(x, y)
        buildings = self.site.buildings
        if buildings is None or buildings.is_empty:
            return ground
        inside = (
            (x - buildings.centre_x_m) ** 2 + (y - buildings.centre_y_m) ** 2
        ) <= buildings.radius_m**2
        if not inside.any():
            return ground
        return ground + float(buildings.height_m[inside].max())


def flat_terrain(
    elevation_m: float = 0.0,
    clutter_loss_db_per_km: float = 0.0,
    micro_roughness_m: float = 0.0,
    language: Optional[str] = None,
) -> Terrain:
    """Perfectly level ground, for isolating one variable in a test.

    Nowhere is flat, and no scenario in this project uses this: the three
    the table describes stand on fetched Ankara ground, and where no
    fetch has happened they fall back to rolling terrain rather than to
    this (ADR-0021). A perfectly level plane is a laboratory instrument.
    It is the worst case for ground reflection, because every reflection
    arrives at the specular angle the two-ray model assumes, and that
    makes it useful for asking what one term does — and misleading for
    asking what a deployment delivers.
    """
    return Terrain(
        elevation_m=Level(elevation_m),
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=micro_roughness_m,
        description=say("terrain.flat", language, elevation_m=elevation_m),
    )


def terrain_from_site(
    site: "Site",
    clutter_loss_db_per_km: float = 0.0,
    language: Optional[str] = None,
) -> Terrain:
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
    return Terrain(
        elevation_m=Fetched(site),
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=site.roughness_m(),
        description=site.manifest.describe(language),
    )


def rolling_terrain(
    amplitude_m: float,
    wavelength_m: float,
    clutter_loss_db_per_km: float = 0.0,
    micro_roughness_m: float = 0.0,
    seed: int = 0,
    language: Optional[str] = None,
) -> Terrain:
    """Smooth hills. Deterministic given the seed.

    Two sine components at incommensurate wavelengths, so the profile does
    not repeat over a corridor and no anchor sits at a lucky spot by
    construction.
    """
    return Terrain(
        elevation_m=Rolling(amplitude_m, wavelength_m, seed),
        clutter_loss_db_per_km=clutter_loss_db_per_km,
        micro_roughness_m=micro_roughness_m,
        description=say(
            "terrain.rolling", language,
            amplitude_m=amplitude_m, wavelength_m=wavelength_m,
        ),
    )


def bore_terrain(
    entry_elevation_m: float,
    exit_elevation_m: float,
    length_m: float,
    micro_roughness_m: float = 0.02,
    description: str = "",
    language: Optional[str] = None,
) -> Terrain:
    """The floor of a tunnel: straight, and never level.

    A bore is the one place in this study where the ground really is a
    plane, and even there it is a sloping one. Road tunnels are built to
    a drainage gradient — typically between half a percent and three —
    because water has to leave, and a floor modelled as level is a floor
    no highway authority would accept.

    The two portal elevations are the real ones where a site has been
    fetched, so the gradient is the mountain's rather than a choice.
    Between them the bore is straight: it goes through the hill, not over
    it, which is why this cannot be built by draping a road over terrain.
    """
    if length_m <= 0.0:
        raise ValueError("a bore has a length")
    fall_m = exit_elevation_m - entry_elevation_m
    grade = fall_m / length_m

    return Terrain(
        elevation_m=Sloping(entry_elevation_m, exit_elevation_m, length_m),
        clutter_loss_db_per_km=0.0,
        micro_roughness_m=micro_roughness_m,
        description=description or say(
            "terrain.bore", language,
            length_m=length_m, grade=decimal_comma(100.0 * grade),
        ),
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


@dataclass(frozen=True)
class Alignment:
    """A road surface as a sampled profile, read back by distance along.

    A callable rather than a closure so a Road — and everything holding
    one — can cross a process boundary (ADR-0025).
    """

    profile_m: tuple
    spacing_m: float
    length_m: float

    def __call__(self, distance_m: float) -> float:
        along = min(max(distance_m, 0.0), self.length_m)
        position = along / self.spacing_m
        index = min(int(position), len(self.profile_m) - 2)
        share = position - index
        here = self.profile_m[index]
        return here + (self.profile_m[index + 1] - here) * share


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

    return Alignment(tuple(profile), spacing, length_m)
