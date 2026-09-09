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

from dataclasses import dataclass, replace
from typing import Optional

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
from yerkon.evaluate import Deployment, Journey, Receiver, Scenario, coverage
from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280, Radio, W24P_U
from yerkon.ranging import DOUBLE_SIDED, SINGLE_SIDED, Scheme
from yerkon.regulatory import TURKEY
from yerkon.world import (
    BILLBOARD,
    LIGHTING_COLUMN,
    MountingOption,
    Road,
    TALL_MAST,
    TUNNEL_BRACKET,
    Terrain,
    flat_terrain,
    graded_alignment,
    rolling_terrain,
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
          antenna_height_m=1.5, product="vehicle"):
    return Receiver(
        identifier=identifier,
        journey=Journey(
            road=road, speed_m_s=speed_m_s, duration_s=duration_s,
            start_m=start_m, antenna_height_m=antenna_height_m,
        ),
        radios=BOTH_MODULES,
        antenna=W24P_U,
        product=product,
    )


# --- Urban ----------------------------------------------------------------

#: Absorption by buildings, vegetation and traffic that height does not
#: clear, in decibels per kilometre at 2,4 GHz.
#:
#: Nothing in the report measures this. Thirty is the middle of the range
#: published for dense built-up areas at this frequency, and it is the
#: single number that decides how far an urban anchor reaches.
URBAN_CLUTTER_DB_PER_KM = 30.0

URBAN_TERRAIN = flat_terrain(
    clutter_loss_db_per_km=URBAN_CLUTTER_DB_PER_KM,
    micro_roughness_m=0.5,
)

URBAN_ROAD = _straight_road(6000.0, URBAN_TERRAIN, step_m=200.0)

URBAN = Deployed(
    scenario=Scenario(
        name="Şehir içi",
        terrain=URBAN_TERRAIN,
        deployment=Deployment(
            anchors=_anchors_along(
                6000.0, 400.0, 25.0, LIGHTING_COLUMN, URBAN_TERRAIN,
                radio=SX1280,
            ),
            receivers=(
                _unit("araç", URBAN_ROAD, 13.9, 400.0),
                _unit("yaya", URBAN_ROAD, 1.4, 400.0, start_m=2000.0,
                      antenna_height_m=1.6, product="pedestrian"),
            ),
            scheme=SINGLE_SIDED,
            region=TURKEY,
        ),
        seed=101,
        accept_sigma_m=15.0,
    ),
    product=URBAN_ANCHOR,
    mounting=LIGHTING_COLUMN,
    route_km=6.0,
    weight=0.5,
    environment="Dış",
    technology="Karasal PNT (SX1280/LoRa TWR)",
    coverage_margin_m=2000.0,
    coverage_resolution_m=100.0,
)


# --- Rural ----------------------------------------------------------------

RURAL_TERRAIN = rolling_terrain(
    amplitude_m=40.0, wavelength_m=3000.0, micro_roughness_m=0.2
)

RURAL_ROAD = _straight_road(24_000.0, RURAL_TERRAIN)

RURAL = Deployed(
    scenario=Scenario(
        name="Kırsal",
        terrain=RURAL_TERRAIN,
        deployment=Deployment(
            anchors=_anchors_along(
                24_000.0, 2000.0, 400.0, TALL_MAST, RURAL_TERRAIN,
                radio=E28_2G4M27S,
            ),
            receivers=(
                _unit("araç", RURAL_ROAD, 27.8, 800.0),
                _unit("kamyon", RURAL_ROAD, 22.2, 800.0, start_m=6000.0),
            ),
            scheme=SINGLE_SIDED,
            region=TURKEY,
        ),
        seed=202,
        accept_sigma_m=30.0,
    ),
    product=RURAL_ANCHOR,
    mounting=TALL_MAST,
    route_km=24.0,
    weight=0.4,
    environment="Dış",
    technology="Karasal PNT (E28-SX1280 TWR)",
    coverage_margin_m=8000.0,
    coverage_resolution_m=250.0,
)


# --- Tunnel ---------------------------------------------------------------

#: A tunnel is a waveguide, and a waveguide loses less than open ground.
#:
#: This project models the bore as level ground with no obstruction, which
#: understates what a real tunnel delivers rather than overstating it. The
#: numbers that come out are therefore conservative, and the model would
#: need a waveguide term to claim otherwise.
TUNNEL_TERRAIN = flat_terrain(micro_roughness_m=0.05)

TUNNEL_ROAD = _straight_road(2000.0, TUNNEL_TERRAIN, step_m=100.0)

TUNNEL = Deployed(
    scenario=Scenario(
        name="Tünel",
        terrain=TUNNEL_TERRAIN,
        deployment=Deployment(
            anchors=_anchors_along(
                2000.0, 150.0, 4.0, TUNNEL_BRACKET, TUNNEL_TERRAIN,
                radio=DWM3000,
            ),
            receivers=(
                _unit("araç", TUNNEL_ROAD, 22.2, 85.0),
                _unit("yaya", TUNNEL_ROAD, 1.4, 85.0, start_m=600.0,
                      antenna_height_m=1.6, product="pedestrian"),
            ),
            scheme=DOUBLE_SIDED,
            region=TURKEY,
        ),
        seed=303,
        accept_sigma_m=2.0,
    ),
    product=TUNNEL_ANCHOR,
    mounting=TUNNEL_BRACKET,
    route_km=2.0,
    weight=0.1,
    environment="İç + dış",
    technology="Karasal PNT (UWB/DWM3000 TWR)",
    confined_width_m=12.0,
)


ALL = (URBAN, RURAL, TUNNEL)

CHOICES = {"urban": URBAN, "rural": RURAL, "tunnel": TUNNEL}


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
