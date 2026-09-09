"""What the viewer lets a person change, and what that becomes.

The browser sends one of these back as JSON on every edit. This module
turns it into the same objects the table is built from, so the numbers on
screen and the numbers in the report come from one engine (ADR-0001).

Nothing here computes physics. It arranges.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np

from yerkon.design import (
    MOUNTING_CHOICES,
    RADIO_CHOICES,
    REGION_CHOICES,
    chosen,
)
from yerkon.evaluate import Deployment, Journey, Scenario
from yerkon.ranging import SCHEMES
from yerkon.scenarios import CHOICES, Deployed, _straight_road
from yerkon.world import Anchor, Terrain, flat_terrain, rolling_terrain


@dataclass(frozen=True)
class ViewState:
    """Every knob the viewer offers, in the vocabulary the CLI uses.

    Keyed by name rather than by object so a slider can move a setting
    without the browser knowing what a SpectrumRule is.
    """

    scenario: str = "rural"
    region: str = "TR"
    radio: str = "e28"
    mounting: str = "mast"
    scheme: str = "single"

    corridor_m: float = 24_000.0
    spacing_m: float = 2000.0
    offset_m: float = 400.0

    #: Height of the rolling ground, peak to trough. Zero is flat.
    relief_m: float = 40.0
    #: How far apart the hills are.
    hill_spacing_m: float = 3000.0
    #: Height scatter the elevation model is too coarse to carry.
    roughness_m: float = 0.2
    #: Absorption by things standing on the ground, per kilometre.
    clutter_db_per_km: float = 0.0

    tolerance_m: float = 5.0
    speed_km_h: float = 100.0
    receiver_height_m: float = 1.5
    journey_s: float = 240.0
    seed: int = 1

    #: Anchors moved by hand, as identifier -> (x, y) in metres.
    #:
    #: Kept apart from the spacing so that regenerating the chain does not
    #: silently discard somebody's dragging, and so the page can show
    #: which anchors were placed rather than computed.
    moved: dict = field(default_factory=dict)
    #: Anchors deleted by hand.
    removed: tuple = ()

    #: Cell size of the coverage sweep, in metres. The sweep is the
    #: slowest thing in the project, so the viewer runs it coarse while a
    #: slider is moving and fine when asked.
    sweep_m: float = 500.0

    def terrain(self) -> Terrain:
        if self.relief_m <= 0.0:
            return flat_terrain(
                clutter_loss_db_per_km=self.clutter_db_per_km,
                micro_roughness_m=self.roughness_m,
            )
        return rolling_terrain(
            amplitude_m=self.relief_m,
            wavelength_m=max(self.hill_spacing_m, 100.0),
            clutter_loss_db_per_km=self.clutter_db_per_km,
            micro_roughness_m=self.roughness_m,
            seed=self.seed,
        )

    def anchors(self, terrain: Terrain) -> tuple[Anchor, ...]:
        """The chain, with anything dragged or deleted taken into account."""
        mounting = chosen(MOUNTING_CHOICES, self.mounting, "mounting")
        spacing = max(self.spacing_m, 50.0)
        placed = []
        for index, x in enumerate(
            np.arange(0.0, self.corridor_m + 1.0, spacing)
        ):
            identifier = "N{}".format(index)
            if identifier in self.removed:
                continue
            ground = self.moved.get(
                identifier,
                (float(x), self.offset_m if index % 2 == 0 else -self.offset_m),
            )
            placed.append(
                Anchor(
                    identifier,
                    (float(ground[0]), float(ground[1])),
                    mounting,
                    terrain,
                )
            )
        if not placed:
            raise ValueError("every anchor has been removed")
        return tuple(placed)

    def deployment(self, terrain: Terrain) -> Deployment:
        radio = chosen(RADIO_CHOICES, self.radio, "radio")
        return Deployment(
            anchors=self.anchors(terrain),
            anchor_radio=radio,
            # The receiver carries whichever module can hear the anchor.
            # Pairing a spread radio with an impulse one is refused
            # downstream, so it is not offered here.
            receiver_radio=radio,
            scheme=SCHEMES[self.scheme],
            region=chosen(REGION_CHOICES, self.region, "region"),
        )

    def scenario_object(self) -> Scenario:
        terrain = self.terrain()
        deployment = self.deployment(terrain)
        road = _straight_road(self.corridor_m, terrain)
        return Scenario(
            name=self.scenario,
            terrain=terrain,
            deployment=deployment,
            journeys=(
                Journey(
                    road=road,
                    speed_m_s=self.speed_km_h / 3.6,
                    duration_s=max(self.journey_s, 5.0),
                    antenna_height_m=self.receiver_height_m,
                ),
            ),
            seed=self.seed,
            accept_sigma_m=max(self.tolerance_m * 4.0, 5.0),
        )

    def deployed(self) -> Deployed:
        """The scenario dressed as a table row, for pricing and reporting."""
        template = CHOICES.get(self.scenario, CHOICES["rural"])
        return replace(
            template,
            scenario=self.scenario_object(),
            mounting=chosen(MOUNTING_CHOICES, self.mounting, "mounting"),
            route_km=self.corridor_m / 1000.0,
            coverage_resolution_m=self.sweep_m,
            confined_width_m=template.confined_width_m,
        )

    def merged(self, changes: dict) -> "ViewState":
        """A copy with some fields replaced, refusing names it does not have."""
        known = set(ViewState.__dataclass_fields__)
        unknown = set(changes) - known
        if unknown:
            raise ValueError(
                "not a setting: {}".format(", ".join(sorted(unknown)))
            )
        cleaned = dict(changes)
        if "moved" in cleaned:
            cleaned["moved"] = {
                str(k): (float(v[0]), float(v[1]))
                for k, v in cleaned["moved"].items()
            }
        if "removed" in cleaned:
            cleaned["removed"] = tuple(str(v) for v in cleaned["removed"])
        return replace(self, **cleaned)

    def as_json(self) -> dict:
        return {
            name: (
                dict(self.moved) if name == "moved"
                else list(self.removed) if name == "removed"
                else getattr(self, name)
            )
            for name in ViewState.__dataclass_fields__
        }


#: Which ViewState fields are Design settings, so an edit to one has to
#: go through the confirmation panel (ADR-0009). Everything else — moving
#: an anchor, changing the terrain, dragging a slider — applies at once.
CASCADING = {
    "region": "region",
    "radio": "anchor_radio",
    "mounting": "mounting",
    "tolerance_m": "target_ranging_sigma_m",
    "roughness_m": "surface_roughness_m",
    "receiver_height_m": "receiver_height_m",
}
