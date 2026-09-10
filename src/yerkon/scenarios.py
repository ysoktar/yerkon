"""The three deployments the report's table describes, as configuration.

Urban, rural and tunnel. Each is a site, a set of anchors on structures
that suit it, the module the bill of materials assigns to it, and a
journey through it. Nothing here computes anything; it is the arrangement
the rest of the project is pointed at, kept in one place so that changing
what is being studied does not mean editing the study.

Every number in this file is a choice somebody could disagree with. The
physics is elsewhere.
"""

from __future__ import annotations

import math
import pathlib
from functools import lru_cache
from dataclasses import dataclass, replace
from typing import Optional, TYPE_CHECKING

import numpy as np

from yerkon.cost import (
    PEDESTRIAN_RECEIVER,
    anchor_product,
    RURAL_ANCHOR,
    TUNNEL_ANCHOR,
    URBAN_ANCHOR,
    VEHICLE_RECEIVER,
    AnchorSite,
    Inventory,
    Product,
)
from yerkon.evaluate import Deployment, Journey, Receiver, Scenario
from yerkon.hardware import DWM3000, SX1280, Radio, W24P_U, radios
from yerkon.ranging import SINGLE_SIDED
from yerkon.regulatory import TURKEY
from yerkon.settings import DEFAULTS, Settings
from yerkon.site.cache import SiteCache

if TYPE_CHECKING:  # pragma: no cover
    from yerkon.site.model import Site
from yerkon.world import (
    bore_terrain,
    mountings,
    patchwork,
    MountingOption,
    Road,
    Terrain,
    graded_alignment,
    rolling_terrain,
    terrain_from_site,
)


@dataclass(frozen=True)
class Deployed:
    """A scenario and the bill it comes with, kept together.

    Splitting them invites a table whose accuracy column and cost column
    describe different deployments, which is a mistake that would not
    announce itself.
    """

    scenario: Scenario
    product: Product
    mounting: MountingOption
    route_km: float
    #: Default share of a receiver's travel spent in this environment.
    #:
    #: Used only for the weighted row. Nobody supplied a journey mix, so
    #: this is a starting point rather than a finding: it is overridden
    #: per run from the command line or the viewer, and the row prints
    #: the weights it used.
    weight: float
    #: What the report calls the environment: inside, outside, or both.
    environment: str
    technology: str
    #: Units of each kind the deployment is priced with.
    receivers: int = 100
    #: How far beyond the anchors the coverage sweep looks, in metres.
    coverage_margin_m: float = 8000.0
    #: Cell size of that sweep, in metres.
    coverage_resolution_m: float = 250.0
    #: Width of the bore, for a deployment that serves a confined space.
    #:
    #: A tunnel is not a plane. Sweeping a grid around one would measure
    #: ground the deployment cannot serve and this model does not
    #: represent, so where this is set the served area is the carriageway
    #: itself: its length times its width. It is a smaller number than a
    #: sweep would give, and the true one.
    confined_width_m: Optional[float] = None

    @property
    def serves_a_corridor(self) -> bool:
        """Whether this deployment serves a line or an area.

        A tunnel is a bore: it has a length and a width and cost per
        route kilometre is the figure that means something. A town and a
        stretch of open country are areas, and their route kilometres are
        the length of a test journey through them rather than a
        dimension of the service. Reporting one as the other invited
        exactly that confusion.
        """
        return self.confined_width_m is not None

    def served_km2(self) -> Optional[float]:
        """Area served, where it follows from the geometry rather than a sweep."""
        if self.confined_width_m is None:
            return None
        return self.route_km * self.confined_width_m / 1000.0

    def inventory(self, service_area_km2: float) -> Inventory:
        units: dict = {}
        for unit in self.scenario.deployment.receivers:
            product = RECEIVER_PRODUCTS.get(unit.product, VEHICLE_RECEIVER)
            units[product] = units.get(product, 0) + self.receivers
        return Inventory(
            anchors=tuple(
                AnchorSite(
                    # Each anchor is priced as the module inside it. A
                    # corridor carrying three modules is three products,
                    # and pricing it as one puts hundreds of lira per
                    # anchor in the wrong place.
                    product=anchor_product(anchor.radio.part),
                    structure=anchor.mounting.kind,
                    site_cost_tl=anchor.mounting.site_cost_tl,
                    has_power=anchor.mounting.has_power,
                    has_backhaul=anchor.mounting.has_backhaul,
                )
                for anchor in self.scenario.deployment.anchors
            ),
            receivers=tuple(units.items()),
            service_area_km2=service_area_km2,
            route_km=self.route_km,
        )


#: Which line of the bill of materials a unit is.
RECEIVER_PRODUCTS = {
    "vehicle": VEHICLE_RECEIVER,
    "pedestrian": PEDESTRIAN_RECEIVER,
}


#: What both receivers in the bill of materials actually contain.
#:
#: "Yaya alıcısı: SX1280, DWM3000, ESP32-S3..." and "Kara aracı alıcısı:
#: SX1280, DWM3000, STM32...". Two radios in each, which is what lets one
#: unit work against town anchors on the road and against tunnel anchors
#: inside a bore without anything about the unit changing.
BOTH_MODULES = (SX1280, DWM3000)


def _straight_road(length_m: float, terrain: Terrain, step_m: float = 500.0) -> Road:
    centreline = [(float(x), 0.0) for x in np.arange(0.0, length_m + 1.0, step_m)]
    return Road(
        centreline_m=centreline,
        terrain=terrain,
        surface_m=graded_alignment(centreline, terrain),
    )


def _anchors_over(
    width_m: float,
    height_m: float,
    spacing_m: float,
    mounting: MountingOption,
    terrain: Terrain,
    radio: Radio = SX1280,
    prefix: str = "A",
    stagger_m: float = 0.0,
):
    """Anchors across an area rather than along a line.

    A town and a stretch of open country are not corridors. Anchors go
    where the structures are, which over a built-up area is a rough grid
    of streets, and the geometry that gives a receiver is nothing like
    the geometry of a line: a corridor leaves the cross-track direction
    barely observable, and an area does not.

    ``stagger_m`` offsets alternate rows, because a perfect grid puts
    every anchor a receiver can see on one of two lines through it, which
    is a worse arrangement than anything real.
    """
    from yerkon.world import Anchor

    placed = []
    index = 0
    for row, y in enumerate(np.arange(0.0, height_m + 1.0, spacing_m)):
        offset = stagger_m if row % 2 else 0.0
        for x in np.arange(offset, width_m + 1.0, spacing_m):
            placed.append(
                Anchor(
                    "{}{}".format(prefix, index),
                    (float(x), float(y)),
                    mounting,
                    terrain,
                    radio=radio,
                )
            )
            index += 1
    return tuple(placed)


def _circuit(
    width_m: float, height_m: float, terrain: Terrain, inset_m: float = 0.0,
    step_m: float = 200.0,
) -> Road:
    """A route around and across an area, rather than a straight line.

    A vehicle in a town turns. A journey that only ever runs east is a
    journey whose cross-track geometry never changes, and it would make
    an area deployment look like a corridor.
    """
    left, right = inset_m, width_m - inset_m
    bottom, top = inset_m, height_m - inset_m
    corners = [
        (left, bottom), (right, bottom), (right, top), (left, top),
        (left, bottom), (right, top),
    ]

    centreline = []
    for start, finish in zip(corners, corners[1:]):
        span = math.dist(start, finish)
        steps = max(int(span / step_m), 1)
        for step in range(steps):
            fraction = step / steps
            centreline.append((
                start[0] + (finish[0] - start[0]) * fraction,
                start[1] + (finish[1] - start[1]) * fraction,
            ))
    centreline.append(corners[-1])
    return Road(
        centreline_m=centreline, terrain=terrain,
        surface_m=graded_alignment(centreline, terrain),
    )


def _anchors_along(
    length_m: float,
    spacing_m: float,
    offset_m: float,
    mounting: MountingOption,
    terrain: Terrain,
    radio: Radio = SX1280,
    prefix: str = "N",
):
    from yerkon.world import Anchor

    return tuple(
        Anchor(
            "{}{}".format(prefix, index),
            (float(x), offset_m if index % 2 == 0 else -offset_m),
            mounting,
            terrain,
            radio=radio,
        )
        for index, x in enumerate(np.arange(0.0, length_m + 1.0, spacing_m))
    )


def _unit(identifier, road, speed_m_s, duration_s, start_m=0.0,
          antenna_height_m=1.5, product="vehicle", radios=None):
    return Receiver(
        identifier=identifier,
        journey=Journey(
            road=road, speed_m_s=speed_m_s, duration_s=duration_s,
            start_m=start_m, antenna_height_m=antenna_height_m,
        ),
        radios=radios or BOTH_MODULES,
        antenna=W24P_U,
        product=product,
    )


# --- Urban ----------------------------------------------------------------

# --- Ground -------------------------------------------------------------

#: Fetched Ankara ground, shipped with the package.
#:
#: Four directories, each a `yerkon fetch` of a real place: the town the
#: urban row describes, the open country the rural row describes, the
#: mountain the tunnel row goes through, and the hills that say what
#: happens when the open country is not gentle. Committing them is the
#: point of ADR-0008 — a cache directory is a self-contained artefact, so
#: anybody who clones this repository gets the same ground and therefore
#: the same numbers, with no network.
SITES = pathlib.Path(__file__).resolve().parent / "site" / "ankara"

#: Which fetched site each row stands on.
#:
#: The rural row stands on the Polatlı plain rather than on the hills at
#: Gölbaşı, and the choice is a finding rather than a convenience. Both
#: are fetched and both ship. On Gölbaşı's 907 m of relief the same
#: thirty-three masts produce a position 45 % of the time, and closing
#: the grid to 1,5 km — one hundred and eighty-nine masts, five and a
#: half times the capital — only reaches 61 %. That is not a spacing
#: problem. It is that an intercity road does not cross a mountain range
#: on a rectangle, and neither does the network beside it: roads follow
#: the gentler ground, which is why the towns are there. Polatlı's 486 m
#: over the same twenty kilometres is the ground this deployment is for,
#: and Gölbaşı stays in the package as the case that says what happens
#: when it is not (ADR-0021).
#: What each row stands on when nobody has said otherwise.
#:
#: The settings file is the authority — `<row>.site` — so an option or a
#: slider can move a row onto other ground, including anything fetched
#: from the viewer (ADR-0027). These remain as the shipped answer and as
#: what the tests name.
URBAN_SITE = "kizilay"
RURAL_SITE = "polatli"
HARD_RURAL_SITE = "golbasi"
TUNNEL_SITE = "kizilcahamam"

#: Where the tunnel's bore runs through the fetched mountain, in metres.
#:
#: Found by searching the fetched grid for a two kilometre line that
#: keeps rock above it the whole way and falls at a gradient a road
#: tunnel is actually built to. This one keeps between nine and a hundred
#: and fifty-six metres of overburden and falls 1,79 %, so its portal
#: elevations are a real mountain's rather than a choice.
TUNNEL_BORE = ((435.0, 870.0), (2435.0, 870.0))


@lru_cache(maxsize=16)
def fetched(name: str) -> Optional["Site"]:
    """The ground for one row, or nothing if it was never fetched.

    Cached, because the viewer asks for it on every drag and a fetched
    grid is a megabyte off disk. A cache directory does not change while
    a process runs; the only thing that would is a `yerkon fetch` in
    another terminal, and that is a restart either way.
    """
    if not name:
        return None
    cache = SiteCache(SITES / name)
    return cache.load() if cache.exists else None


def _patched(terrain: Terrain, settings: Settings, row: str) -> Terrain:
    """Give a terrain ground that is not the same everywhere.

    The site's roughness stays its typical figure — the patchwork is
    centred on it — and the reflection asks what the ground is like where
    it lands rather than taking one number for the whole place
    (ADR-0026). Its seed is the row's own, kept apart from the
    measurement seed so a run can hold the landscape and vary the noise,
    or the reverse.
    """
    spread = settings.number("{}.ground_roughness_spread".format(row))
    if spread <= 0.0:
        return terrain
    return replace(terrain, patches=patchwork(
        typical_m=terrain.micro_roughness_m,
        patch_m=settings.number("{}.ground_patch_m".format(row)),
        spread=spread,
        levels=int(settings.number("{}.ground_levels".format(row))),
        seed=int(settings.number("{}.ground_seed".format(row))),
    ))


def urban_ground(settings: Settings, clutter_db_per_km: float) -> Terrain:
    """Real Ankara if it is on hand, and rolling ground if it is not.

    Never flat. Ankara's centre rises and falls ninety-one metres across
    the three kilometres this row covers, and a plane would put every
    anchor and every receiver at one height — which is not a
    simplification of that town but a different one, and a favourable
    one: a level plane hands every reflection the specular angle the
    two-ray model assumes (ADR-0021).
    """
    site = fetched(settings.text("urban.site"))
    if site is not None:
        return _patched(
            terrain_from_site(site, clutter_loss_db_per_km=clutter_db_per_km),
            settings, "urban",
        )
    return _patched(rolling_terrain(
        amplitude_m=settings.number("site.urban_relief_m"),
        wavelength_m=settings.number("site.urban_relief_wavelength_m"),
        clutter_loss_db_per_km=clutter_db_per_km,
        micro_roughness_m=0.5,
        seed=101,
    ), settings, "urban")


def rural_ground(settings: Settings) -> Terrain:
    """The same, over open country, where the relief is an order larger."""
    site = fetched(settings.text("rural.site"))
    if site is not None:
        return _patched(terrain_from_site(site), settings, "rural")
    return _patched(rolling_terrain(
        amplitude_m=settings.number("site.rural_relief_m"),
        wavelength_m=settings.number("site.rural_relief_wavelength_m"),
        micro_roughness_m=0.4,
        seed=202,
    ), settings, "rural")


def tunnel_ground(
    settings: Settings, length_m: float, site_name: Optional[str] = None
) -> Terrain:
    """The floor of the bore, which slopes because every bore does.

    Not the mountain's surface: a tunnel goes through a hill rather than
    over it, so this is a straight line between two portals and not
    terrain draped over ground. Where the mountain has been fetched, the
    portal elevations are its own and the gradient follows from them.
    Where it has not, the gradient is the one that alignment measured.
    """
    if site_name is None:
        site_name = settings.text("tunnel.site")
    site = fetched(site_name) if site_name else None
    (entry_x, entry_y), _ = TUNNEL_BORE
    # The far portal moves with the bore's length, so shortening the
    # tunnel gives the gradient of that shorter line rather than a two
    # kilometre one's applied to it. A bore longer than the fetched
    # mountain has no second portal to read, and inventing one by
    # clamping would spread a real fall over an unreal distance, so that
    # case takes the measured gradient instead.
    if site is not None and entry_x + length_m <= site.width_m:
        return _patched(bore_terrain(
            entry_elevation_m=site.height_at(entry_x, entry_y),
            exit_elevation_m=site.height_at(entry_x + length_m, entry_y),
            length_m=length_m,
            description="bore through {}, portals from {}".format(
                site_name, site.manifest.elevation_source
            ),
        ), settings, "tunnel")
    grade = settings.number("site.tunnel_grade")
    return _patched(bore_terrain(
        entry_elevation_m=0.0,
        exit_elevation_m=-grade * length_m,
        length_m=length_m,
    ), settings, "tunnel")


#: Absorption by buildings, vegetation and traffic that height does not
#: clear, in decibels per kilometre at 2,4 GHz.
#:
#: A figure nobody supplied, and the single number that decides how far
#: an urban anchor reaches. It comes from the settings file.
URBAN_CLUTTER_DB_PER_KM = DEFAULTS.number("site.urban_clutter_db_per_km")


def catalogue(settings: Settings = DEFAULTS) -> dict:
    """The three deployments the table describes, from a settings file.

    Built rather than written down, so that a run with real mounting
    heights, real site costs or a real urban clutter figure gets
    scenarios made of those instead of the shipped placeholders
    (ADR-0016).
    """
    mounting = mountings(settings)
    module = radios(settings)
    # The modules a unit carries, rebuilt from this run's own figures.
    #
    # Not `BOTH_MODULES`. The link budget takes its noise figure from the
    # *receiving* terminal, so a unit holding the shipped part made every
    # edit to a radio figure invisible to link closure: the anchors moved
    # and the thing deciding whether the packet arrived did not.
    both = (module["sx1280"], module["dwm3000"])
    clutter = settings.number("site.urban_clutter_db_per_km")


    URBAN_TERRAIN = urban_ground(settings, clutter)

    # Every number that shapes a deployment comes from the settings file,
    # so one file changes every figure in the table and the viewer can
    # move any of them while it is running (ADR-0023).
    URBAN_M = settings.number("urban.extent_m")
    URBAN_ROAD = _circuit(URBAN_M, URBAN_M, URBAN_TERRAIN, inset_m=300.0,
                          step_m=150.0)

    URBAN = Deployed(
        scenario=Scenario(
            name="Şehir içi",
            terrain=URBAN_TERRAIN,
            deployment=Deployment(
                anchors=_anchors_over(
                    URBAN_M, URBAN_M,
                    settings.number("urban.anchor_spacing_m"),
                    mounting["lighting_column"], URBAN_TERRAIN,
                    radio=module["sx1280"], prefix="C",
                    stagger_m=settings.number("urban.anchor_stagger_m"),
                ),
                receivers=(
                    _unit("araç", URBAN_ROAD, 13.9, 600.0, radios=both),
                    _unit("yaya", URBAN_ROAD, 1.4, 600.0, start_m=2000.0,
                          antenna_height_m=1.6, product="pedestrian",
                          radios=both),
                ),
                max_anchors_per_round=int(
                    settings.number("urban.anchors_per_round")
                ),
                scheme=SINGLE_SIDED,
                region=TURKEY,
            ),
            seed=101,
            accept_sigma_m=settings.number("urban.accept_sigma_m"),
            anchor_survey_sigma_m=settings.number("ranging.anchor_survey_sigma_m"),
            # A town's share of the band is spoken for, so more exchanges
            # are lost here than anywhere else in the study.
            packet_loss=settings.number("site.urban_packet_loss"),
        ),
        product=URBAN_ANCHOR,
        mounting=mounting["lighting_column"],
        route_km=URBAN_ROAD.length_m / 1000.0,
        weight=0.5,
        environment="Dış",
        technology="Karasal PNT (SX1280/LoRa TWR)",
        coverage_margin_m=1500.0,
        coverage_resolution_m=100.0,
    )


    # --- Rural ----------------------------------------------------------------

    RURAL_TERRAIN = rural_ground(settings)

    RURAL_M = settings.number("rural.extent_m")
    RURAL_ROAD = _circuit(RURAL_M, RURAL_M, RURAL_TERRAIN, inset_m=2000.0)

    RURAL = Deployed(
        scenario=Scenario(
            name="Kırsal",
            terrain=RURAL_TERRAIN,
            deployment=Deployment(
                anchors=_anchors_over(
                    RURAL_M, RURAL_M,
                    settings.number("rural.anchor_spacing_m"),
                    mounting["tall_mast"], RURAL_TERRAIN,
                    radio=module["e28"], prefix="M",
                    stagger_m=settings.number("rural.anchor_stagger_m"),
                ),
                receivers=(
                    _unit("araç", RURAL_ROAD, 27.8, 2400.0, radios=both),
                    _unit("kamyon", RURAL_ROAD, 22.2, 2400.0,
                          start_m=20_000.0, radios=both),
                ),
                # Twelve, not the eight the other rows use, and the
                # difference is worth 6,8 points of availability without
                # a single extra mast (ADR-0022).
                #
                # Eight was chosen when a position needs four and a
                # little margin looked generous. Over real relief that
                # reasoning fails: every rural link that fails, fails to
                # terrain rather than to distance, so roughly half the
                # anchors polled never answer and eight attempts yield
                # about four replies — exactly the number a cold fix
                # needs, with nothing spare. The round has to be sized by
                # how many anchors answer, not by how many a position
                # needs. Sixteen buys only another 0,8 points and costs
                # more than it returns.
                max_anchors_per_round=int(
                    settings.number("rural.anchors_per_round")
                ),
                scheme=SINGLE_SIDED,
                region=TURKEY,
            ),
            seed=202,
            accept_sigma_m=settings.number("rural.accept_sigma_m"),
            anchor_survey_sigma_m=settings.number("ranging.anchor_survey_sigma_m"),
            packet_loss=settings.number("ranging.packet_loss"),
        ),
        product=RURAL_ANCHOR,
        mounting=mounting["tall_mast"],
        route_km=RURAL_ROAD.length_m / 1000.0,
        weight=0.4,
        environment="Dış",
        technology="Karasal PNT (E28-SX1280 TWR)",
        coverage_margin_m=8000.0,
        coverage_resolution_m=500.0,
    )


    # --- Tunnel ---------------------------------------------------------------

    #: A tunnel is a waveguide, and a waveguide loses less than open ground.
    #:
    #: This project models the bore with no waveguide term, which understates
    #: what a real tunnel delivers rather than overstating it. The numbers
    #: that come out are therefore conservative, and the model would need
    #: that term to claim otherwise. What it does not do any more is model
    #: the floor as level: the bore falls 1,79 % between real portals, so
    #: anchors and receivers sit at different heights along it (ADR-0021).
    TUNNEL_M = settings.number("tunnel.length_m")
    TUNNEL_TERRAIN = tunnel_ground(settings, TUNNEL_M)

    TUNNEL_ROAD = _straight_road(TUNNEL_M, TUNNEL_TERRAIN, step_m=100.0)

    TUNNEL = Deployed(
        scenario=Scenario(
            name="Tünel",
            terrain=TUNNEL_TERRAIN,
            deployment=Deployment(
                anchors=_anchors_along(
                    TUNNEL_M,
                    settings.number("tunnel.anchor_spacing_m"),
                    settings.number("tunnel.anchor_offset_m"),
                    mounting["tunnel_bracket"], TUNNEL_TERRAIN,
                    radio=module["dwm3000"],
                ),
                receivers=(
                    _unit("araç", TUNNEL_ROAD, 22.2, 85.0, radios=both),
                    _unit("yaya", TUNNEL_ROAD, 1.4, 85.0, start_m=600.0,
                          antenna_height_m=1.6, product="pedestrian",
                          radios=both),
                ),
                # Single-sided, on the strength of a measurement rather
                # than a preference. At the residual offset this project
                # assumed, the third frame earned its place on this radio.
                # Measured, the clock term is 1,6 cm against a 10 cm
                # floor, so the frame buys nothing and costs a third of
                # the air: 0,72 m at the ninety-fifth percentile instead
                # of 1,00, and half again as many fixes. See ADR-0010.
                max_anchors_per_round=int(
                    settings.number("tunnel.anchors_per_round")
                ),
                scheme=SINGLE_SIDED,
                region=TURKEY,
            ),
            seed=303,
            accept_sigma_m=settings.number("tunnel.accept_sigma_m"),
            anchor_survey_sigma_m=settings.number("ranging.anchor_survey_sigma_m"),
            # A bore is a shielded box: nothing outside it is competing
            # for the band, and ultra-wideband does not share one anyway.
            packet_loss=0.0,
        ),
        product=TUNNEL_ANCHOR,
        mounting=mounting["tunnel_bracket"],
        route_km=TUNNEL_M / 1000.0,
        weight=0.1,
        environment="İç + dış",
        technology="Karasal PNT (UWB/DWM3000 TWR)",
        confined_width_m=settings.number("tunnel.width_m"),
    )


    return {"urban": URBAN, "rural": RURAL, "tunnel": TUNNEL}


CHOICES = catalogue()

URBAN = CHOICES["urban"]
RURAL = CHOICES["rural"]
TUNNEL = CHOICES["tunnel"]
ALL = (URBAN, RURAL, TUNNEL)


#: The default journey mix for the weighted row, by scenario key.
#:
#: Half a receiver's travel in town, most of the rest between towns, a
#: tenth in tunnels and other confined stretches. Nobody supplied these
#: and no result should rest on them, so they are configuration: pass
#: --weight to the command line or move the sliders in the viewer.
DEFAULT_WEIGHTS = {name: deployed.weight for name, deployed in CHOICES.items()}


def reweighted(
    deployments: "tuple[Deployed, ...]", weights: "Optional[dict[str, float]]"
) -> "tuple[Deployed, ...]":
    """The same deployments under a different journey mix.

    Keyed by the same short names the command line and the viewer use, so
    a weight can travel from a slider to a table row without anything in
    between having to know what a scenario is.
    """
    if not weights:
        return deployments
    unknown = set(weights) - set(CHOICES)
    if unknown:
        raise ValueError(
            "no scenario called {}. Choose from: {}".format(
                ", ".join(sorted(unknown)), ", ".join(sorted(CHOICES))
            )
        )
    if any(value < 0.0 for value in weights.values()):
        raise ValueError("a share of a journey is not negative")
    if sum(weights.values()) <= 0.0:
        raise ValueError("the weights must add to something positive")

    by_name = {
        deployed.scenario.name: name for name, deployed in CHOICES.items()
    }
    return tuple(
        replace(d, weight=weights.get(by_name.get(d.scenario.name, ""), d.weight))
        for d in deployments
    )
