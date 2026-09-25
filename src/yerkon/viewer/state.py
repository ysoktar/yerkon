"""What the viewer lets a person change, and what that becomes.

The browser sends one of these back as JSON on every edit. This module
turns it into the same objects the table is built from, so the numbers on
screen and the numbers in the report come from one engine (ADR-0001).

Nothing here computes physics. It arranges.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

import json
import math
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
    catalogue,
    fetched,
    fits_on,
    tunnel_ground,
    varying,
)
from yerkon.design import Design, REGION_CHOICES
from yerkon.rf import Terminal, closure_range_m, usable_range_m
from yerkon.language import DEFAULT_LANGUAGE, say
from yerkon.layout import ENOUGH_TO_BE_SERVED, SEARCHES, Spot
from yerkon.routes import Course, Trip, trace
from yerkon.layout import Ground as LayoutGround, Plan, bar_of, place
from yerkon.settings import Settings, defaults_in
from yerkon.world import (
    Anchor,
    Road,
    Terrain,
    graded_alignment,
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


# --- What a run's anchors are, in the vocabulary the model uses -----------
#
# These read nothing but the state, so they live beside it rather than in
# the scene that used to hold them. The searching layouts need the same
# reach the reach ring is drawn from, and two ways of working out one
# number is how a picture and a run come to disagree with nothing on
# screen to say which is the deployment.


def design_of(state: ViewState, run=None) -> Design:
    """One anchor run's settings, as the confirmation panel understands them.

    The panel talks about a radio on a mounting at a tolerance, and a
    corridor now carries more than one of those, so it is asked about one
    run at a time and the panel says which.
    """
    run = run or (state.runs[0] if state.runs else None)
    # From the state's own catalogues, so that editing a mounting height
    # or a noise figure by hand moves what the panel says it moves.
    mounting_of, radio_of = state.catalogues()
    return Design(
        region=chosen(REGION_CHOICES, state.region, "region"),
        anchor_radio=chosen(radio_of, run.radio if run else "sx1280", "radio"),
        mounting=chosen(
            mounting_of, run.mounting if run else "mast", "mounting"
        ),
        receiver_height_m=_lowest_unit(state),
        # From the ground the simulation will actually stand on, not
        # from the slider. A fetched grid brings its own roughness and
        # ignores that slider, so reading it here would draw a reach
        # ring the run does not agree with — and nothing on screen
        # would say which of the two was the deployment.
        surface_roughness_m=state.terrain().micro_roughness_m,
        target_ranging_sigma_m=state.tolerance_m,
    )


def _lowest_unit(state: ViewState) -> float:
    """The worst case among the units, which is the one range is quoted for."""
    if not state.units:
        return 1.5
    return min(unit.antenna_height_m for unit in state.units)


def reach_of(state: ViewState, run) -> float:
    """How far one run's anchors range within tolerance, over open ground.

    A flat-ground figure, drawn as a ring. Real terrain moves it either
    way and the sweep is what actually decides coverage; the ring is an
    intuition, not a claim.
    """
    design = design_of(state, run)
    anchor = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m)
    )
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.receiver_height_m)
    )
    return usable_range_m(
        anchor, receiver, design.anchor_radio,
        target_sigma_m=state.tolerance_m, region=design.region,
    )


#: How many rays the measured reach samples, and how much of them has to
#: close for a distance to count as reachable.
#:
#: Two hundred is enough to place the threshold within a hundred metres
#: and costs a fraction of a second; a sweep costs seconds. Ninety per
#: cent because the search treats the disc as a hard edge, so the edge
#: belongs where links are still reliable rather than where the last one
#: happened to get through.
#: How finely the sampling states an answer, and how much evidence each
#: band gets.
#:
#: Eight bands put the whole answer in one of eight values, and over
#: Kızılay that made the band 478 m wide: two grounds as different as a
#: town and open rolling country came back with the identical figure to
#: a tenth of a metre, because both failed in the same band. Thirty-two
#: bands and four hundred rays each cost a second over a town and four
#: through a bore, once per arrangement, and the searches place against
#: the answer (ADR-0057).
REACH_BANDS = 32
RAYS_PER_BAND = 400
REACH_SHARE = 0.9

#: Measured reaches already worked out this process.
#:
#: Two hundred link budgets over real terrain is a fraction of a second
#: and `anchors` is called on every drag, which is not. Keyed by
#: everything the answer depends on, so a figure edited by hand or a
#: change of ground is a different question rather than a stale one.
_REACHES: dict = {}

#: How many placements are kept at once.
#:
#: Each is a few hundred anchors, so the limit is not about the size of
#: any one answer: it is that a session left open for an afternoon
#: should not grow a dictionary for an afternoon.
PLACEMENTS_KEPT = 12

#: Anchors already placed this process, keyed by what placed them.
#:
#: A search is not cheap. `greedy-dop` scores every candidate against
#: every cell for every anchor it adds, which over Kızılay's two hundred
#: and thirty-two mountable structures is nine seconds — and the page
#: asks for a scene and then a sweep, and the scene placed a second time
#: on its own, so one press of a dropdown paid for it three times over
#: while showing the previous arrangement's numbers throughout.
_PLACED: dict = {}


def run_key(state: ViewState, terrain: Terrain) -> tuple:
    """Everything a simulated run's answer depends on.

    Wider than `_placement_key`, which drops the three fields that cannot
    move an anchor. A run is driven along a route for a length of time
    over a sweep of some resolution, so all three are back in: the only
    field left out is which language the page reads in.
    """
    asked = state.as_json()
    asked.pop("language", None)
    return (
        json.dumps(asked, sort_keys=True, default=str),
        round(terrain.height_at(0.0, 0.0), 6),
        round(terrain.height_at(1000.0, 0.0), 6),
        round(terrain.height_at(0.0, 1000.0), 6),
        round(getattr(terrain, "micro_roughness_m", 0.0), 6),
    )


def _placement_key(state: ViewState, terrain: Terrain) -> tuple:
    """Everything an anchor's position depends on, and nothing else.

    A key that is too wide costs a recomputation; one that is too narrow
    hands back anchors for a site that is no longer on screen. So it is
    written as the state itself minus the three fields that cannot move
    an anchor — which language it reads in, how long a journey lasts,
    how fine the sweep is — rather than as a list of the fields that
    can: a field added later is then in the key by being a field, not by
    somebody remembering to add it (ADR-0035).

    The ground is asked directly rather than taken on trust from the
    state, because `anchors` is handed a terrain and a caller is free to
    hand it one the state would not have built.
    """
    asked = state.as_json()
    for name in ("language", "journey_s", "sweep_m"):
        asked.pop(name, None)
    # A unit's route and its speed are not an anchor's business. Its
    # antenna height is: the reach every run is placed against is quoted
    # to the lowest one.
    asked["units"] = sorted(unit.antenna_height_m for unit in state.units)
    return (
        json.dumps(asked, sort_keys=True, default=str),
        round(terrain.height_at(0.0, 0.0), 6),
        round(terrain.height_at(1000.0, 0.0), 6),
        round(terrain.height_at(0.0, 1000.0), 6),
        round(getattr(terrain, "micro_roughness_m", 0.0), 6),
    )


@dataclass(frozen=True)
class Reach:
    """How far a run's anchors reach on this ground, and whether that
    figure is a measurement.

    ``measured`` is false when not even the closest band held enough
    links to clear the bar. The distance is then the closest band's own
    far edge, which is a ceiling rather than a reading: the reach is
    somewhere below it and this sampling cannot say where. Reported as a
    distance without that flag, it is a number nothing measured, and
    every search on the site places its anchors against it (ADR-0057).
    """

    metres: float
    measured: bool


def measured_reach_m(state: ViewState, run) -> float:
    """The distance alone, for the callers that only place against it."""
    return reach_on(state, run).metres


def reach_on(state: ViewState, run) -> Reach:
    """How far this run's anchors reach *on this ground*, by sampling it.

    `reach_of` is a flat-ground figure and says so: "the ring is an
    intuition, not a claim". That is fine for a ring and wrong for a
    decision, and the searching layouts were treating it as a hard edge.
    Over Kızılay it says 3 825 m while the furthest link that closes is
    1 937 m and half of them fail past a kilometre — 5 231 buildings
    stand in between. So a search placed four anchors in the corners,
    believed they covered everything, and served 0,12 km² of the 8,92
    a lattice serves (ADR-0047).

    Measured rather than derated by a rule: the number that matters is
    what the link budget does over *these* buildings and *this* relief,
    and the budget is right there.

    Rays from the middle of the site, because an anchor placed by a
    search could be anywhere on it and the middle is the least unfair
    single choice. The answer is a band rather than a distance, so it is
    reported as the far edge of the last band where enough links still
    close.
    """
    from yerkon.rf import evaluate_link, ranging_sigma_m

    remember = (
        state.site, state.bore, state.scenario,
        round(state.corridor_m, 3), round(state.width_m, 3),
        round(state.relief_m, 3), round(state.hill_spacing_m, 3),
        round(state.roughness_m, 4), round(state.clutter_db_per_km, 3),
        round(state.tolerance_m, 4), state.seed, state.region,
        run.radio, run.mounting,
        # The reach is quoted to the lowest antenna on the site, so
        # raising a receiver's antenna asks a different question. Left
        # out, it was answered with the previous one.
        round(_lowest_unit(state), 4),
        json.dumps(state.overrides, sort_keys=True, default=str),
    )
    if remember in _REACHES:
        return _REACHES[remember]


    terrain = state.terrain()
    design = design_of(state, run)
    open_ground = reach_of(state, run)
    if open_ground <= 0.0:
        return Reach(metres=open_ground, measured=False)

    length = max(state.corridor_m, 1.0)
    width = max(state.width_m, 0.0)
    middle = (length / 2.0, width / 2.0)
    # No further than the ground goes: a ray off the site is a link over
    # terrain nobody measured (ADR-0037).
    furthest = min(open_ground, math.hypot(length, width))
    edges = np.linspace(0.0, furthest, REACH_BANDS + 1)

    rng = np.random.default_rng(state.seed)
    here = (middle[0], middle[1],
            terrain.height_at(*middle) + design.anchor_height_m)
    # A corridor has no width to aim into. Rays at a random bearing all
    # land off a site one metre wide, so the tunnel row measured nothing
    # at all and took the floor instead (ADR-0057).
    a_line = width <= 0.0

    reached = 0.0
    for band in range(REACH_BANDS):
        closed = tried = attempts = 0
        # Each band gets the same evidence. Drawn across the whole disc,
        # the outer bands got the fewest rays, because a long ray from
        # the middle leaves a square site more often than a short one —
        # and the outer bands are where the answer is decided.
        while tried < RAYS_PER_BAND and attempts < RAYS_PER_BAND * 12:
            attempts += 1
            angle = (rng.choice((0.0, math.pi)) if a_line
                     else rng.uniform(0.0, 2.0 * math.pi))
            far = rng.uniform(max(float(edges[band]), 1.0),
                              float(edges[band + 1]))
            x = middle[0] + far * math.cos(angle)
            y = middle[1] + far * math.sin(angle)
            if not (0.0 <= x <= length and 0.0 <= y <= max(width, 0.0)):
                continue
            tried += 1
            there = (x, y, terrain.height_at(x, y) + design.receiver_height_m)
            budget = evaluate_link(
                Terminal(design.anchor_radio, design.antenna, here),
                Terminal(design.anchor_radio, design.antenna, there),
                obstruction=terrain.obstruction_between(here, there),
                region=design.region,
            )
            if budget.closes and ranging_sigma_m(
                budget, design.anchor_radio
            ) <= state.tolerance_m:
                closed += 1

        # A band nobody could sample is not evidence either way, so it
        # neither extends nor stops the answer.
        if tried == 0:
            continue
        if closed / tried < REACH_SHARE:
            break
        reached = float(edges[band + 1])

    # Nothing passed, not even the first band. The honest answer is
    # "shorter than this", and the floor is reported as the ceiling it
    # is rather than as a distance something measured (ADR-0057).
    answer = (Reach(metres=reached, measured=True) if reached > 0.0
              else Reach(metres=float(edges[1]), measured=False))
    _REACHES[remember] = answer
    return answer


def closure_of(state: ViewState, run) -> float:
    design = design_of(state, run)
    anchor = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m)
    )
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.receiver_height_m)
    )
    return closure_range_m(anchor, receiver, region=design.region)




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
    #: Which method lays this run out. See `yerkon.layout`.
    #:
    #: The square lattice by default, because that is what this project
    #: shipped before there was a choice and every other method is read
    #: against it.
    method: str = "grid"
    #: What the searching methods read. Unused by the lattices, and kept
    #: here rather than in a second record so that switching methods on a
    #: dropdown does not lose what somebody set under the other one.
    most: int = 60
    #: How many anchors `k-cover` puts over every cell.
    #:
    #: The engine's own figure rather than a third copy of it: this said
    #: 3 while `layout.Plan` said 4, and a run carries its own value into
    #: `place`, so the default here silently won. An urban k-cover
    #: deployment covered to three, the area column counts four, and the
    #: service area came out nought (ADR-0047).
    cover_k: int = ENOUGH_TO_BE_SERVED
    target_dop: float = 2.0
    #: How far an anchor of this kind reaches, in metres.
    #:
    #: Supplied rather than worked out here: a run must not do its own
    #: link budget (ADR-0009), and the searching methods need a number to
    #: score discs against. The viewer passes what the budget said.
    reach_m: float = 0.0
    #: Where the `placed` method puts anchors: (x, y, mounting) triples
    #: the placement search wrote (ADR-0081). Empty for every other
    #: method.
    spots: tuple = ()

    def anchors(self, terrain: Terrain, catalogues=None, width_m: float = 0.0,
                route=(), furniture=()) -> list:
        """Where this run's anchors stand, by whichever method it names.

        A thin adapter over `yerkon.layout`: this turns a run into that
        module's `Plan` and `Ground` and names the results. The geometry
        lives there because a corridor, a lattice and a search are the
        same question asked three ways, and because the answer is worth
        testing without a viewer, a terrain or a catalogue in the way.
        """
        mounting_of, radio_of = catalogues or (MOUNTING_CHOICES, RADIO_CHOICES)
        fallback = chosen(mounting_of, self.mounting, "mounting")
        radio = chosen(radio_of, self.radio, "radio")

        start = self.from_m
        plan, ground = self.asked_for(width_m, route, furniture)
        spots = place(plan, ground)
        out = []
        for index, spot in enumerate(spots):
            # A spot that landed on a structure already standing keeps
            # that structure; anything this run put down itself is bolted
            # to what the run says (ADR-0015).
            standing = (
                chosen(mounting_of, spot.mounting, "mounting")
                if spot.mounting and spot.mounting in mounting_of
                else fallback
            )
            out.append((
                "{}{}".format(self.identifier, index),
                (spot.x_m + start, spot.y_m),
                standing,
                radio,
            ))
        return out

    def asked_for(self, width_m: float = 0.0, route=(), furniture=()):
        """The `Plan` and `Ground` this run hands to `yerkon.layout`.

        Built in one place because two callers need the same pair: the
        one that places the anchors and the one that asks whether the
        arrangement cleared the bar. Building it twice is how the scene
        came to recognise fifty-two of the sixty anchors it was drawing
        (ADR-0049).
        """
        start = self.from_m
        return (
            Plan(
                method=self.method or "grid",
                spacing_m=max(self.spacing_m, 25.0),
                offset_m=self.offset_m,
                stagger_m=self.stagger_m,
                most=int(self.most),
                cover_k=int(self.cover_k),
                target_dop=self.target_dop,
                mounting=self.mounting,
                spots=tuple(
                    (x - start, y, mounting) for x, y, mounting in self.spots
                ),
            ),
            LayoutGround(
                length_m=max(self.to_m, self.from_m) - start,
                width_m=max(width_m, 0.0),
                reach_m=self.reach_m or max(self.spacing_m, 25.0) * 1.5,
                route=tuple((x - start, y) for x, y in route),
                furniture=tuple(
                    replace(spot, x_m=spot.x_m - start) for spot in furniture
                ),
            ),
        )

    def within(self, length_m: float) -> "AnchorRun":
        """This run, with its ends brought inside a site of that length.

        An anchor standing past the end of the site is an anchor on
        ground the study does not model and a unit never drives past.
        """
        start = min(max(self.from_m, 0.0), length_m)
        finish = min(max(self.to_m, start), length_m)
        if (start, finish) == (self.from_m, self.to_m):
            return self
        return replace(self, from_m=start, to_m=finish)

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
    #: Which route it drives, by name (`yerkon.routes`).
    #:
    #: Empty means the site's own shape, which is what every unit did
    #: before there was a choice: a line down a corridor, a circuit over
    #: an area. Kept as the default so an arrangement saved before this
    #: existed loads as the arrangement it was (ADR-0043), and last in
    #: the field list because a field added in the middle shifts every
    #: positional argument after it (ADR-0035).
    route: str = ""

    def as_json(self) -> dict:
        return {
            name: (list(getattr(self, name)) if name == "radios"
                   else getattr(self, name))
            for name in UnitPlan.__dataclass_fields__
        }


#: Mountings the placement search may use and a whole run may not.
#:
#: A roof is only where a building stands, and its height comes from the
#: footprint under it; a lattice of "roof" anchors would put brackets on
#: bare ground (ADR-0081).
ONLY_WHERE_PLACED = ("roof",)

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

    #: Which language the figures, the notes and the ground read in.
    #:
    #: Nothing else about the row depends on it: the same deployment,
    #: the same numbers, the same table (ADR-0035).
    language: str = DEFAULT_LANGUAGE

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
        return defaults_in(self.language).with_values(self.overrides)

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
                "pole": by_key["distribution_pole"],
                # Only where a building stands: the placement search puts
                # it on a roof, and the roof's height comes from the
                # footprint (ADR-0081). Not offered for a whole run.
                "roof": by_key["rooftop"],
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
        return self._varying(self._even_ground())

    def _varying(self, ground: Terrain) -> Terrain:
        """The same ground, with what it is not the same about.

        Ground that varies from patch to patch (ADR-0026) and a spread
        around what the model carries (ADR-0055) are facts about a place
        rather than about how its elevation was arrived at, so they are
        attached here for every kind of ground at once — and through the
        same function the table's own rows go through, because a page
        and a run disagreeing about which ground the deployment stands
        on is the thing this project keeps catching.
        """
        row = self.scenario if self.scenario in ("urban", "rural", "tunnel") \
            else "urban"
        return varying(ground, self.settings(), row)

    def _even_ground(self) -> Terrain:
        if self.bore:
            return tunnel_ground(
                self.settings(), max(self.corridor_m, 100.0), self.site,
                language=self.language,
            )
        if self.site:
            site = fetched(self.site)
            if site is None:
                raise ValueError(
                    "no site fetched at {}. Run `yerkon fetch --into {}` "
                    "first; see ADR-0008.".format(SITES / self.site, SITES / self.site)
                )
            return terrain_from_site(
                site, clutter_loss_db_per_km=self.clutter_db_per_km,
                language=self.language,
            )
        return rolling_terrain(
            amplitude_m=max(self.relief_m, 1.0),
            wavelength_m=max(self.hill_spacing_m, 100.0),
            clutter_loss_db_per_km=self.clutter_db_per_km,
            micro_roughness_m=self.roughness_m,
            seed=self.seed,
            language=self.language,
        )

    def furniture(self) -> tuple:
        """Structures a fetch found that an anchor could be bolted to.

        Empty on modelled ground and on a fetch that did not look. Where
        there are any, the searching layouts score these instead of a
        lattice: an anchor on a traffic signal that already stands costs
        the signal nothing, and a purpose-built mast costs eighty-five
        thousand lira (ADR-0015, ADR-0040).
        """
        found = getattr(self.measured(), "furniture", None)
        if found is None or not len(found):
            return ()
        kinds = found.kind or ("column",) * len(found)
        return tuple(
            Spot(float(x), float(y), kind)
            for x, y, kind in zip(found.x_m, found.y_m, kinds)
        )

    def anchors(self, terrain: Terrain) -> tuple[Anchor, ...]:
        """Every run's anchors, with anything dragged or deleted applied."""
        return tuple(anchor for _, anchor in self.placed(terrain))

    def placed(self, terrain: Terrain) -> tuple[tuple[str, Anchor], ...]:
        """The same anchors, each beside the run that put it there.

        Which run an anchor came from is known here and nowhere else: a
        search decides where its anchors go by reading the route, the
        structures already standing and the reach measured over this
        ground, so working it out again anywhere else means running the
        search again with whatever arguments that caller happened to
        have. The scene did exactly that, and over Kızılay it recognised
        fifty-two of the sixty anchors it was drawing — the other eight
        were drawn in no colour, given no reach ring and counted on no
        card (ADR-0049).
        """
        return self._laid_out(terrain)[0]

    def bars(self, terrain: Terrain) -> dict:
        """Whether each run cleared what its method was asked for.

        Nothing under a run whose method carries no bar. Measured
        against the anchors actually standing, so deleting three by hand
        can take an arrangement back under its bar and say so
        (ADR-0056).
        """
        return self._laid_out(terrain)[1]

    def _laid_out(self, terrain: Terrain) -> tuple:
        remember = _placement_key(self, terrain)
        if remember in _PLACED:
            return _PLACED[remember]

        answer = self._place(terrain)
        # Oldest out. A session that drags a slider all afternoon should
        # not grow a dictionary all afternoon.
        while len(_PLACED) >= PLACEMENTS_KEPT:
            _PLACED.pop(next(iter(_PLACED)))
        _PLACED[remember] = answer
        return answer

    def _place(self, terrain: Terrain) -> tuple:
        catalogues = self.catalogues()
        route = tuple(
            (float(x), float(y)) for x, y in self.road(terrain).centreline_m
        )
        standing = self.furniture()
        placed: list = []
        bars: dict = {}
        for run in self.runs:
            # The reach the ring is drawn from, so a search scores its
            # candidates against the same disc a person is looking at.
            # A search treats the disc as a hard edge, so it gets the
            # reach measured on this ground; a lattice never reads it
            # and keeps the open-ground figure the ring is drawn from
            # (ADR-0047).
            disc = run.reach_m or (
                measured_reach_m(self, run) if run.method in SEARCHES
                else reach_of(self, run)
            )
            reaching = replace(run, reach_m=disc)
            for identifier, ground, mounting, radio in reaching.anchors(
                terrain, catalogues, self.width_m, route=route,
                furniture=standing,
            ):
                if identifier in self.removed:
                    continue
                x, y = self.moved.get(identifier, ground)
                placed.append((
                    run.identifier,
                    Anchor(identifier, (float(x), float(y)), mounting,
                           terrain, radio=radio),
                ))

            # Asked of what is standing rather than of what was placed:
            # the same plan and the same ground the search used, and the
            # anchors that survived being dragged and deleted.
            plan, layout_ground = reaching.asked_for(
                self.width_m, route, standing)
            here = tuple(
                Spot(anchor.ground_position_m[0] - run.from_m,
                     anchor.ground_position_m[1])
                for run_id, anchor in placed if run_id == run.identifier
            )
            bars[run.identifier] = bar_of(plan, layout_ground, here)
        return tuple(placed), bars

    def course(self) -> Course:
        """The ground a journey runs over, for `yerkon.routes`."""
        measured = self.measured()
        return Course(
            length_m=self.corridor_m,
            width_m=self.width_m,
            # Empty until a fetch brings road geometry, which greys the
            # `road` route rather than offering one that cannot be drawn
            # (ADR-0036, ADR-0045).
            road=getattr(measured, "roads_m", ()) or (),
        )

    def road(self, terrain: Terrain, route: str = "") -> Road:
        """The route a unit takes, as a road with its own alignment.

        The site's own shape by default — a line down a corridor, a
        circuit over an area — which is what every unit drove before
        there was a choice. A named route overrides it.

        This is also the spine anchors are placed along, and that is
        asked for without a route on purpose: where the anchors go is a
        fact about the site, not about which pattern one receiver was
        told to drive (ADR-0045).
        """
        shape = route or ("line" if self.width_m <= 0.0 else "circuit")
        centreline = trace(
            Trip(method=shape, step_m=self._route_step_m()), self.course())
        return Road(
            centreline_m=centreline,
            terrain=terrain,
            surface_m=graded_alignment(list(centreline), terrain),
        )

    def _route_step_m(self) -> float:
        """How finely a route is sampled.

        Fine enough to be a shape, coarse enough that a forty kilometre
        site is not ten thousand points. The figures are the ones the two
        shapes this replaced already used — 500 m down a corridor, a
        twentieth of the shorter side over an area — so a unit that names
        no route drives exactly the road it drove before there was a
        choice, point for point.
        """
        from yerkon.routes import area_step_m

        return area_step_m(self.corridor_m, self.width_m)

    def receivers(self, terrain: Terrain) -> tuple[Receiver, ...]:
        """Each unit on its own route.

        Built per unit rather than once, because a unit that drives a
        lawnmower over a town and one that runs the ring road are asking
        different questions of the same anchors — and a single road for
        all of them was an arrangement rather than a choice (ADR-0045).
        """
        from yerkon.scenarios import unit_antenna

        _, radio_of = self.catalogues()
        row = self.scenario if self.scenario in MODES else "rural"
        roads = {}
        for unit in self.units:
            if unit.route not in roads:
                roads[unit.route] = self.road(terrain, unit.route)
        return tuple(
            Receiver(
                identifier=unit.identifier,
                journey=Journey(
                    road=roads[unit.route],
                    speed_m_s=unit.speed_km_h / 3.6,
                    duration_s=max(self.journey_s, 5.0),
                    start_m=unit.start_m,
                    antenna_height_m=unit.antenna_height_m,
                ),
                radios=tuple(
                    chosen(radio_of, name, "radio") for name in unit.radios
                ),
                antenna=unit_antenna(row, unit.kind),
                product=unit.kind,
            )
            for unit in self.units
        )

    def deployment(self, terrain: Terrain) -> Deployment:
        """This tab as something that can be evaluated.

        Refuses an arrangement with nothing in it, which `anchors` used
        to do and should not have: a tab with no anchors is perfectly
        drawable — it is the blank sheet an empty arrangement starts
        from (ADR-0043) — and merely has no result to report. A
        positioning network with no transmitters produces no position,
        so the refusal belongs where a number would be produced rather
        than where a picture is.

        `Deployment` refuses an empty one too, and says "a deployment
        needs anchors". Said here first because the person reading it is
        looking at a viewer and wants to know what to do about it.
        """
        anchors = self.anchors(terrain)
        if not anchors:
            raise ValueError(say("deployment.no_anchors", self.language))
        from yerkon.scenarios import row_deployment_figures

        row = self.scenario if self.scenario in MODES else "rural"
        region = chosen(REGION_CHOICES, self.region, "region")
        return Deployment(
            anchors=anchors,
            receivers=self.receivers(terrain),
            # The scheme is the tab's own: the page offers it. How many
            # anchors a round polls is the row's (ADR-0084).
            scheme=SCHEMES[self.scheme],
            region=region,
            # The rest an adaptive rule asks for after each occupancy,
            # as the table's rows take it (ADR-0094).
            duty_cycle=region.channel_share,
            max_anchors_per_round=row_deployment_figures(
                row, self.settings())["max_anchors_per_round"],
            # The row's antennas, so a tab hears as its row does (ADR-0091).
            antenna=row_deployment_figures(row, self.settings())["antenna"],
        )

    def scenario_object(self) -> Scenario:
        terrain = self.terrain()
        return Scenario(
            # The row's own name, so a table run from the page prints the
            # same heading the report does rather than the tab's key.
            name=mode_labels(self.language).get(
                self.scenario, self.scenario
            ),
            terrain=terrain,
            deployment=self.deployment(terrain),
            **self._row_figures(),
        )

    def _row_figures(self) -> dict:
        """What the scenario runs with beyond where things stand.

        The row's own figures, read where the table reads them, so a tab
        runs the row it shows. Only the seed stays the tab's, because the
        page lets a person change it (ADR-0084).
        """
        from yerkon.scenarios import row_figures

        row = self.scenario if self.scenario in MODES else "rural"
        figures = row_figures(row, self.settings())
        figures["seed"] = self.seed
        return figures

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
                run if isinstance(run, AnchorRun) else AnchorRun(**{
                    **run,
                    # JSON has no tuples, and a run is hashed.
                    "spots": tuple(
                        (float(x), float(y), str(mounting))
                        for x, y, mounting in run.get("spots", ())
                    ),
                })
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

    def measured(self):
        """The ground fetched for this row, or nothing where it is modelled."""
        return fetched(self.site) if self.site else None

    def on_measured_ground(self) -> "ViewState":
        """This state, with the site no larger than the ground measured.

        A fetched grid stops where the fetch stopped. `Site.height_at`
        clamps past its edge rather than raising, which is right for a
        link path grazing the boundary and wrong for a deployment: the
        clamp extrudes the edge row into a plane, and a plane is the most
        favourable ground this model can draw (ADR-0021). So a site
        longer or wider than the ground under it puts anchors on a number
        nobody measured, and this brings it in (ADR-0037).

        A bore is not bounded here. It goes through the hill rather than
        over it, so its floor is a line between two portals and its
        length is checked against the mountain where the portals are read
        (`tunnel_ground`).
        """
        if self.bore:
            return self
        length, width = fits_on(self.measured(), self.corridor_m, self.width_m)
        if (length, width) == (self.corridor_m, self.width_m):
            return self
        return replace(self, corridor_m=length, width_m=width)

    def on_new_ground(self, before: "ViewState") -> "ViewState":
        """This state after being put on different ground.

        Clipping only ever makes a site smaller (ADR-0037), which is
        right when the ground shrinks under it and leaves it behind when
        the ground grows. Fetch nineteen kilometres by twelve, press
        Use, and the site was still the three kilometres of the town it
        had been on: one and a half per cent of what had just been
        downloaded, with no sign that anything had been left out
        (ADR-0054).

        So a site that was the whole of its ground becomes the whole of
        the new ground, and a site somebody had deliberately made
        smaller than its ground keeps the size they gave it. A corridor
        stays a corridor: it takes the new length and no width, because
        a width of nothing is the thing that makes it one.

        Modelled ground has no measured extent to have filled, so
        arriving from it keeps the numbers and lets the clip decide.
        """
        if self.bore or self.site == before.site:
            return self
        ground = self.measured()
        if ground is None:
            return self

        was = before.measured()
        if was is None:
            return self
        filled = (before.corridor_m >= was.width_m - 1e-6
                  and (before.width_m <= 0.0
                       or before.width_m >= was.height_m - 1e-6))
        if not filled:
            return self
        return replace(
            self,
            corridor_m=float(ground.width_m),
            width_m=0.0 if before.width_m <= 0.0 else float(ground.height_m),
        )

    def within_site(self) -> "ViewState":
        """This state, with everything standing on it brought inside it.

        The site's width already shapes the anchors directly — a grid
        runs from the road out to it — but its length did not, because a
        run carries its own start and end. So one of the two sliders
        moved the deployment and the other moved nothing, which is not a
        distinction either of them makes on screen.

        The site itself is brought inside the measured ground first, so
        that shortening for that reason clips the runs the same way
        shortening by hand does.

        Only the length slider, the width slider and the ground picker
        call this. Typing an end into a run is a person being explicit
        about that run, and clipping it under them would be answering a
        question they did not ask.
        """
        bounded = self.on_measured_ground()
        length = max(bounded.corridor_m, 0.0)
        clipped = tuple(run.within(length) for run in bounded.runs)
        return bounded if clipped == bounded.runs else replace(
            bounded, runs=clipped)

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

    Each row is written as the extent it wants and then brought inside
    the ground fetched for it, rather than with the measurement written
    into the literal: 2970 by 2940 is what kizilay came back as, and a
    figure like that belongs to the fetch rather than to the code
    (ADR-0037).
    """
    return _template(name).within_site()


#: How long each row's journey runs, in seconds.
#:
#: Read off the deployment the table evaluates rather than written here
#: again. The urban tab used to carry its own 240 against the table's
#: 600, so pressing run gave a different answer to the published row
#: and the panel looked like it disagreed with the table (ADR-0076).
def _journey_s(name: str) -> float:
    from yerkon.scenarios import CHOICES

    return max(unit.journey.duration_s
               for unit in CHOICES[name].scenario.deployment.receivers)


#: The spacing and stagger each row lays its anchors out on.
#:
#: From the settings, for the same reason: these are the figures that
#: decide the row, and a second copy of them in this file is a copy
#: that drifts. The tunnel's spacing moved from 150 m to 225 m and this
#: file did not hear about it (ADR-0023, ADR-0076).
def _grid(prefix: str, stagger: bool = True) -> tuple:
    from yerkon.settings import DEFAULTS

    spacing = DEFAULTS.number("{}.anchor_spacing_m".format(prefix))
    if not stagger:
        return (spacing, 0.0)
    return (spacing, DEFAULTS.number("{}.anchor_stagger_m".format(prefix)))


def _units(name: str) -> tuple:
    """The row's own units, from the one list both sides read (ADR-0084)."""
    from yerkon.scenarios import ROW_UNITS, unit_radios

    return tuple(
        UnitPlan(name_, kind, speed_km_h, start_m, height_m,
                 radios=unit_radios(name, kind))
        for name_, kind, speed_km_h, start_m, height_m in ROW_UNITS[name]
    )


def _radio(name: str) -> str:
    """The row's anchor module, by key (ADR-0094)."""
    from yerkon.scenarios import ROW_RADIOS

    return ROW_RADIOS[name][0]


def _region(name: str) -> str:
    """The row's spectrum rule, by key (ADR-0094)."""
    from yerkon.scenarios import ROW_REGIONS

    return ROW_REGIONS[name]


def _seed(name: str) -> int:
    from yerkon.scenarios import ROW_SEEDS

    return ROW_SEEDS[name]


def _sweep_m(name: str) -> float:
    """The cell size the table sweeps the row's area at."""
    from yerkon.scenarios import CHOICES

    return CHOICES[name].coverage_resolution_m


def _template(name: str) -> ViewState:
    if name == "urban":
        return ViewState(
            scenario="urban", corridor_m=3000.0, width_m=3000.0,
            site="kizilay", region=_region("urban"),
            clutter_db_per_km=30.0, roughness_m=0.5, tolerance_m=5.0,
            sweep_m=_sweep_m("urban"), journey_s=_journey_s("urban"),
            runs=(
                AnchorRun("C", _radio("urban"), "column", 0.0, 3000.0,
                          _grid("urban")[0], 0.0,
                          stagger_m=_grid("urban")[1]),
            ),
            units=_units("urban"),
            seed=_seed("urban"),
        )
    if name == "tunnel":
        return ViewState(
            scenario="tunnel", corridor_m=2000.0,
            site="kizilcahamam", bore=True, region=_region("tunnel"),
            clutter_db_per_km=0.0, roughness_m=0.05, tolerance_m=1.0,
            # Single-sided, as the table runs it (ADR-0010). The tab
            # carried double-sided after the table moved (ADR-0084).
            sweep_m=100.0, journey_s=_journey_s("tunnel"), scheme="single",
            runs=(AnchorRun("T", _radio("tunnel"), "tunnel", 0.0, 2000.0,
                            _grid("tunnel", stagger=False)[0], 4.0),),
            units=_units("tunnel"),
            seed=_seed("tunnel"),
        )
    if name == "rural":
        return ViewState(
            scenario="rural", corridor_m=20_000.0, width_m=20_000.0,
            site="polatli", region=_region("rural"), roughness_m=0.2,
            tolerance_m=5.0, sweep_m=_sweep_m("rural"),
            journey_s=_journey_s("rural"),
            runs=(
                AnchorRun("M", _radio("rural"), "pole", 0.0, 20_000.0,
                          _grid("rural")[0], 0.0,
                          stagger_m=_grid("rural")[1]),
            ),
            units=_units("rural"),
            seed=_seed("rural"),
        )
    raise ValueError(
        "no row called {!r}. There are: {}".format(name, ", ".join(MODES))
    )


#: The three rows of the table, in the order the report prints them.
#:
#: Three, always. They are tabs rather than a menu: each holds a prepared
#: deployment and a run takes either the one showing or all of them
#: (ADR-0028). The mixed corridor that used to sit alongside them is gone
#: as a preset. Nothing is lost in kind, because any tab can still carry
#: several anchor runs of different modules, which is what made it a
#: mixed corridor.
MODES = ("urban", "rural", "tunnel")

def mode_labels(language: Optional[str] = None) -> dict:
    """What each row is called on its tab, in one language."""
    return {name: say("row." + name, language) for name in MODES}


#: What each row is called, in the default language.
MODE_LABELS = mode_labels()


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
