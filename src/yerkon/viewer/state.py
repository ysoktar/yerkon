"""What the viewer lets a person change, and what that becomes.

The browser sends one of these back as JSON on every edit. This module
turns it into the same objects the table is built from, so the numbers on
screen and the numbers in the report come from one engine (ADR-0001).

Nothing here computes physics. It arranges.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from yerkon.design import (
    MOUNTING_CHOICES,
    RADIO_CHOICES,
    REGION_CHOICES,
    chosen,
)
from yerkon.evaluate import Deployment, Journey, Receiver, Scenario
from yerkon.hardware import radios
from yerkon.ranging import SCHEMES
from yerkon.scenarios import (
    Deployed,
    SITES,
    _circuit,
    _straight_road,
    catalogue,
    fetched,
    tunnel_ground,
)
from yerkon.settings import DEFAULTS, Settings
from yerkon.world import (
    Anchor,
    Road,
    Terrain,
    mountings,
    rolling_terrain,
    terrain_from_site,
)


#: Fetched ground a person can drop the deployment onto, by directory name.
#:
#: Whatever `yerkon fetch` has written into the package's own site folder,
#: found rather than listed, so fetching a fourth place puts it in the
#: menu without anything here changing.
def fetched_sites() -> tuple[str, ...]:
    if not SITES.exists():
        return ()
    return tuple(sorted(
        directory.name for directory in SITES.iterdir()
        if (directory / "manifest.json").exists()
    ))


#: A group of anchors of one kind, laid over part of the site.
#:
#: A site does not carry one kind of anchor, so the viewer does not model
#: one. Each run is a group of these, and they may overlap: town columns
#: over the first few square kilometres, masts across open country, UWB
#: brackets through a bore.
@dataclass(frozen=True)
class AnchorRun:
    identifier: str = "A"
    radio: str = "e28"
    mounting: str = "mast"
    from_m: float = 0.0
    to_m: float = 24_000.0
    spacing_m: float = 2000.0
    offset_m: float = 400.0
    #: How far alternate rows are shifted along, in metres.
    #:
    #: Only used over an area. A perfect grid puts every anchor a
    #: receiver can see on one of two lines through it, which is a worse
    #: arrangement than anything anybody would build.
    stagger_m: float = 0.0

    def anchors(self, terrain: Terrain, catalogues=None, width_m: float = 0.0) -> list:
        """Where this run's anchors stand.

        Along a line when the site has no width, and over a staggered
        grid when it has. The two produce entirely different geometry
        for a receiver — a line leaves the cross-track direction barely
        observable and an area does not — which is why the viewer can
        show both rather than assuming one (ADR-0014).
        """
        mounting_of, radio_of = catalogues or (MOUNTING_CHOICES, RADIO_CHOICES)
        mounting = chosen(mounting_of, self.mounting, "mounting")
        radio = chosen(radio_of, self.radio, "radio")
        spacing = max(self.spacing_m, 25.0)
        along = np.arange(self.from_m, max(self.to_m, self.from_m) + 1.0, spacing)

        if width_m <= 0.0:
            return [
                (
                    "{}{}".format(self.identifier, index),
                    (float(x), self.offset_m if index % 2 == 0 else -self.offset_m),
                    mounting,
                    radio,
                )
                for index, x in enumerate(along)
            ]

        out = []
        for row, y in enumerate(np.arange(0.0, width_m + 1.0, spacing)):
            shift = self.stagger_m if row % 2 else 0.0
            for x in along:
                out.append((
                    "{}{}".format(self.identifier, len(out)),
                    (float(x) + shift, float(y) + self.offset_m),
                    mounting,
                    radio,
                ))
        return out

    def as_json(self) -> dict:
        return {name: getattr(self, name) for name in AnchorRun.__dataclass_fields__}


#: One moving unit: where it starts, how fast, and what it carries.
@dataclass(frozen=True)
class UnitPlan:
    identifier: str = "araç"
    kind: str = "vehicle"
    speed_km_h: float = 100.0
    start_m: float = 0.0
    antenna_height_m: float = 1.5
    #: Which modules it carries. Both, for either receiver in the bill.
    radios: tuple = ("sx1280", "dwm3000")

    def as_json(self) -> dict:
        return {
            name: (list(getattr(self, name)) if name == "radios"
                   else getattr(self, name))
            for name in UnitPlan.__dataclass_fields__
        }


DEFAULT_RUNS = (
    AnchorRun("M", "e28", "mast", 0.0, 24_000.0, 2000.0, 400.0),
)

DEFAULT_UNITS = (
    UnitPlan("araç", "vehicle", 100.0, 0.0, 1.5),
)


@dataclass(frozen=True)
class ViewState:
    """Every knob the viewer offers, in the vocabulary the CLI uses.

    Keyed by name rather than by object so a slider can move a setting
    without the browser knowing what a SpectrumRule is.
    """

    scenario: str = "rural"
    region: str = "TR"
    scheme: str = "single"

    corridor_m: float = 24_000.0

    #: How far the site extends across, in metres. Zero is a corridor.
    #:
    #: The single knob that decides whether this is a line or an area,
    #: because it decides both at once: anchors go on a grid rather than
    #: down one side, and a unit drives a circuit rather than east. Two
    #: separate knobs could disagree, and a scene showing gridded anchors
    #: driven past in a straight line would be neither arrangement.
    width_m: float = 0.0

    #: Anchors, as one or more runs of a single kind.
    runs: tuple = DEFAULT_RUNS
    #: The units driving through them.
    units: tuple = DEFAULT_UNITS

    #: Fetched ground to stand on, by directory name. Empty is modelled.
    #:
    #: A real grid brings its own relief, its own roughness and its own
    #: obstructions, so when one is named the three sliders below it stop
    #: applying — the page says so rather than leaving them looking live.
    site: str = ""

    #: Whether the units run through the ground rather than over it.
    #:
    #: A bore is the one arrangement that cannot be built by draping a
    #: road over terrain, because it goes through the hill. Its floor is
    #: a straight line between two portals, and it slopes, because every
    #: road tunnel is built to a drainage gradient.
    bore: bool = False

    #: Height of the modelled ground, peak to trough.
    #:
    #: Ankara's centre moves ninety-one metres over three kilometres and
    #: its open country most of a kilometre over twenty. Nowhere is flat,
    #: so nothing here offers flat: this is what the ground does when no
    #: fetched grid is standing in for it (ADR-0021). The default pair is
    #: gentler than either fetched place — rolling farmland rather than
    #: the steppe or the town — because it is the ground a person sees
    #: before choosing any, and the fetched grids are there to be harder.
    relief_m: float = 91.0
    #: How far apart the hills are.
    hill_spacing_m: float = 6000.0
    #: Height scatter the elevation model is too coarse to carry.
    roughness_m: float = 0.2
    #: Absorption by things standing on the ground, per kilometre.
    clutter_db_per_km: float = 0.0

    tolerance_m: float = 5.0
    journey_s: float = 240.0
    seed: int = 1

    #: Anchors moved by hand, as identifier -> (x, y) in metres.
    moved: dict = field(default_factory=dict)
    #: Anchors deleted by hand.
    removed: tuple = ()

    #: Cell size of the coverage sweep, in metres.
    sweep_m: float = 500.0

    #: Figures changed by hand, keyed as `defaults.toml` keys them.
    #:
    #: Every number nobody supplied is editable while the viewer is
    #: running, and everything is rebuilt from it: the mounting
    #: catalogue, the radios, the clocks, the rates, the scenarios. A
    #: value alone is still a guess; one given a source stops counting as
    #: an assumption (ADR-0016).
    overrides: dict = field(default_factory=dict)

    # -- the world --------------------------------------------------------

    def settings(self) -> Settings:
        """The figures this run uses: the shipped file, plus any edits."""
        return DEFAULTS.with_values(self.overrides)

    def catalogues(self):
        """Mountings and radios built from this run's own figures."""
        settings = self.settings()
        by_key = mountings(settings)
        return (
            {
                "sign": by_key["roadside_sign"],
                "gantry": by_key["sign_gantry"],
                "billboard": by_key["billboard"],
                "column": by_key["lighting_column"],
                "mast": by_key["tall_mast"],
                "tunnel": by_key["tunnel_bracket"],
            },
            radios(settings),
        )

    def terrain(self) -> Terrain:
        """Real ground where a site is named, modelled ground where none is.

        Never a plane either way. A level surface hands every reflection
        the specular angle the two-ray model assumes, which makes it the
        most favourable ground this project can draw and the least like
        anywhere a receiver will actually be (ADR-0021).
        """
        if self.bore:
            return tunnel_ground(
                self.settings(), max(self.corridor_m, 100.0), self.site
            )
        if self.site:
            site = fetched(self.site)
            if site is None:
                raise ValueError(
                    "no site fetched at {}. Run `yerkon fetch --into {}` "
                    "first; see ADR-0008.".format(SITES / self.site, SITES / self.site)
                )
            return terrain_from_site(
                site, clutter_loss_db_per_km=self.clutter_db_per_km
            )
        return rolling_terrain(
            amplitude_m=max(self.relief_m, 1.0),
            wavelength_m=max(self.hill_spacing_m, 100.0),
            clutter_loss_db_per_km=self.clutter_db_per_km,
            micro_roughness_m=self.roughness_m,
            seed=self.seed,
        )

    def anchors(self, terrain: Terrain) -> tuple[Anchor, ...]:
        """Every run's anchors, with anything dragged or deleted applied."""
        catalogues = self.catalogues()
        placed = []
        for run in self.runs:
            for identifier, ground, mounting, radio in run.anchors(
                terrain, catalogues, self.width_m
            ):
                if identifier in self.removed:
                    continue
                x, y = self.moved.get(identifier, ground)
                placed.append(
                    Anchor(identifier, (float(x), float(y)), mounting,
                           terrain, radio=radio)
                )
        if not placed:
            raise ValueError("every anchor has been removed")
        return tuple(placed)

    def road(self, terrain: Terrain) -> Road:
        """The route the units take: a line down a corridor, a circuit over an area."""
        if self.width_m <= 0.0:
            return _straight_road(self.corridor_m, terrain)
        return _circuit(
            self.corridor_m, self.width_m, terrain,
            inset_m=min(self.corridor_m, self.width_m) * 0.1,
            step_m=max(min(self.corridor_m, self.width_m) / 20.0, 50.0),
        )

    def receivers(self, terrain: Terrain) -> tuple[Receiver, ...]:
        road = self.road(terrain)
        _, radio_of = self.catalogues()
        return tuple(
            Receiver(
                identifier=unit.identifier,
                journey=Journey(
                    road=road,
                    speed_m_s=unit.speed_km_h / 3.6,
                    duration_s=max(self.journey_s, 5.0),
                    start_m=unit.start_m,
                    antenna_height_m=unit.antenna_height_m,
                ),
                radios=tuple(
                    chosen(radio_of, name, "radio") for name in unit.radios
                ),
                product=unit.kind,
            )
            for unit in self.units
        )

    def deployment(self, terrain: Terrain) -> Deployment:
        return Deployment(
            anchors=self.anchors(terrain),
            receivers=self.receivers(terrain),
            scheme=SCHEMES[self.scheme],
            region=chosen(REGION_CHOICES, self.region, "region"),
        )

    def scenario_object(self) -> Scenario:
        terrain = self.terrain()
        return Scenario(
            # The row's own name, so a table run from the page prints the
            # same heading the report does rather than the tab's key.
            name=MODE_LABELS.get(self.scenario, self.scenario),
            terrain=terrain,
            deployment=self.deployment(terrain),
            seed=self.seed,
            accept_sigma_m=max(self.tolerance_m * 4.0, 5.0),
        )

    def deployed(self) -> Deployed:
        """The scenario dressed as a table row, for pricing and reporting."""
        template = catalogue(self.settings()).get(
            self.scenario, catalogue(self.settings())["rural"]
        )
        mounting_of, _ = self.catalogues()
        return replace(
            template,
            scenario=self.scenario_object(),
            mounting=chosen(
                mounting_of, self.runs[0].mounting if self.runs else "mast",
                "mounting",
            ),
            route_km=self.road(self.terrain()).length_m / 1000.0,
            coverage_resolution_m=self.sweep_m,
            confined_width_m=template.confined_width_m,
        )

    # -- editing ----------------------------------------------------------

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
        if "runs" in cleaned:
            cleaned["runs"] = tuple(
                run if isinstance(run, AnchorRun) else AnchorRun(**run)
                for run in cleaned["runs"]
            )
        if "overrides" in cleaned:
            cleaned["overrides"] = {
                str(key): value for key, value in cleaned["overrides"].items()
            }
        if "units" in cleaned:
            cleaned["units"] = tuple(
                unit if isinstance(unit, UnitPlan)
                else UnitPlan(**{**unit, "radios": tuple(unit.get("radios", ()))})
                for unit in cleaned["units"]
            )
        return replace(self, **cleaned)

    def as_json(self) -> dict:
        out = {}
        for name in ViewState.__dataclass_fields__:
            value = getattr(self, name)
            if name == "runs":
                out[name] = [run.as_json() for run in value]
            elif name == "units":
                out[name] = [unit.as_json() for unit in value]
            elif name in ("moved", "overrides"):
                out[name] = dict(value)
            elif name == "removed":
                out[name] = list(value)
            else:
                out[name] = value
        return out


#: Which ViewState fields are Design settings, so an edit to one has to
#: go through the confirmation panel (ADR-0009). Everything else — moving
#: an anchor, changing the terrain, dragging a slider — applies at once.
def from_scenario(name: str) -> ViewState:
    """The viewer's own state for one of the report's modes.

    Rebuilt here rather than lifted from `scenarios`, because the viewer
    edits a site of runs and units and the report's scenarios are frozen
    arrangements. What is shared is the thing that matters: the module,
    the mounting, the spacing and the shape each mode uses — a town and a
    stretch of open country are areas, and only a bore is a line.
    """
    if name == "urban":
        return ViewState(
            scenario="urban", corridor_m=3000.0, width_m=3000.0,
            site="kizilay",
            clutter_db_per_km=30.0, roughness_m=0.5, tolerance_m=5.0,
            sweep_m=200.0, journey_s=240.0,
            runs=(
                AnchorRun("C", "sx1280", "column", 0.0, 3000.0, 500.0, 0.0,
                          stagger_m=250.0),
            ),
            units=(
                UnitPlan("araç", "vehicle", 50.0, 0.0, 1.5),
                UnitPlan("yaya", "pedestrian", 5.0, 2000.0, 1.6),
            ),
        )
    if name == "tunnel":
        return ViewState(
            scenario="tunnel", corridor_m=2000.0,
            site="kizilcahamam", bore=True,
            clutter_db_per_km=0.0, roughness_m=0.05, tolerance_m=1.0,
            sweep_m=100.0, journey_s=85.0, scheme="double",
            runs=(AnchorRun("T", "dwm3000", "tunnel", 0.0, 2000.0, 150.0, 4.0),),
            units=(
                UnitPlan("araç", "vehicle", 80.0, 0.0, 1.5),
                UnitPlan("yaya", "pedestrian", 5.0, 600.0, 1.6),
            ),
        )
    if name == "rural":
        return ViewState(
            scenario="rural", corridor_m=20_000.0, width_m=20_000.0,
            site="polatli", roughness_m=0.2,
            tolerance_m=5.0, sweep_m=500.0, journey_s=2400.0,
            runs=(
                AnchorRun("M", "e28", "mast", 0.0, 20_000.0, 4000.0, 0.0,
                          stagger_m=2000.0),
            ),
            units=(
                UnitPlan("araç", "vehicle", 100.0, 0.0, 1.5),
                UnitPlan("kamyon", "vehicle", 80.0, 20_000.0, 2.8),
            ),
        )
    raise ValueError(
        "no row called {!r}. There are: {}".format(name, ", ".join(MODES))
    )


#: The three rows of the table, in the order the report prints them.
#:
#: Three, always. They are tabs rather than a menu: each holds a prepared
#: deployment and a run takes either the one showing or all of them and
#: the weighted row they make (ADR-0028). The mixed corridor that used to
#: sit alongside them is gone as a preset — nothing is lost in kind,
#: because any tab can still carry several anchor runs of different
#: modules, which is what made it a mixed corridor.
MODES = ("urban", "rural", "tunnel")

#: What each row is called on its tab.
MODE_LABELS = {
    "urban": "Şehir içi",
    "rural": "Kırsal",
    "tunnel": "Tünel",
}


CASCADING = {
    "region": "region",
    "tolerance_m": "target_ranging_sigma_m",
    "roughness_m": "surface_roughness_m",
}

#: Fields of an anchor run that cascade when they change.
#:
#: Kept apart because they belong to one run rather than to the whole
#: state, and the panel has to say which run it is talking about.
CASCADING_RUN = {
    "radio": "anchor_radio",
    "mounting": "mounting",
}
