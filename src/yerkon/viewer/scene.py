"""Turning a state into something a browser can draw and read.

Everything here is JSON. The geometry the page renders and the numbers it
prints come from the same objects the report is built from, so a figure
on screen and a figure in the table cannot disagree (ADR-0001).

Three jobs, deliberately separate, because they cost wildly different
amounts of time and the page asks for them independently: the scene is
instant, the sweep takes seconds, and the run takes longer still.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Optional
from urllib.parse import quote

import numpy as np

from yerkon.cost import DEFAULT_RATES, price
from yerkon.design import Design, REGION_CHOICES, chosen
from yerkon.evaluate import coverage_grid, pooled, run_scenario
from yerkon.rf import Terminal, closure_range_m, usable_range_m
from yerkon.language import LANGUAGES, LANGUAGE_NAMES, say
from yerkon.layout import (
    FEWEST_FOR_A_FIX,
    METHODS as LAYOUT_METHODS,
    SEARCHES as LAYOUT_SEARCHES,
)
from yerkon.parallel import spread
from yerkon.report import AREA_DRAWS, draws_of
from yerkon.routes import METHODS as ROUTE_METHODS, drivable
from yerkon.site.fetch import missing_for_a_fetch
from yerkon.viewer.state import (
    _lowest_unit,
    run_key,
    closure_of,
    design_of,
    reach_of,
    reach_on,
    mode_labels,
    ViewState,
    ONLY_WHERE_PLACED,
    fetched_sites,
)

#: Which of the chooser's four groups each layout method sits under.
#: A method missing here is a ready pattern, the plainest of the four.
_LAYOUT_GROUP = {
    "greedy-coverage": "search",
    "greedy-dop": "search",
    "k-cover": "search",
    "placed": "standing",
    "manual": "hand",
}

#: About how many quads the ground mesh is allowed.
#:
#: Enough that hills three kilometres apart read as hills, and few enough
#: that the browser redraws them while a slider is still moving.
MESH_QUADS = 4200

#: How coarse and how fine the mesh may get along one axis.
MESH_LEAST = 24
MESH_MOST = 150


def mesh_shape(span_x: float, span_y: float) -> tuple[int, int]:
    """How many samples along each axis, for cells that are roughly square.

    A fixed hundred by forty spread the same budget over any site, so a
    twenty by twenty kilometre one was sampled every 460 m along and
    every 1100 m across: the ground came out in stripes, and a hill read
    as a ridge because the mesh could only resolve it in one direction.
    The count follows the site's own proportions instead, which keeps a
    cell square whether the site is a square or a corridor.
    """
    span_x = max(span_x, 1.0)
    span_y = max(span_y, 1.0)
    aspect = span_x / span_y

    def fit(count: float) -> int:
        return int(min(MESH_MOST, max(MESH_LEAST, round(count))))

    return fit((MESH_QUADS * aspect) ** 0.5), fit((MESH_QUADS / aspect) ** 0.5)


def ground(
    state: ViewState,
    west: float,
    east: float,
    south: float,
    north: float,
) -> dict:
    """A mesh over one window of the site, at the same budget as the whole.

    The scene's mesh is spread over everything there is, which over a
    forty kilometre site is a sample every seven hundred metres. Zoom in
    on one mast and the hill it stands on is two flat facets — under a
    thirty metre elevation model, so the detail is measured and simply
    was not asked for. This asks for it: the same few thousand samples,
    over the ground actually on screen.
    """
    terrain = state.terrain()
    west, east, south, north = drawable(terrain, west, east, south, north)
    columns, rows = mesh_shape(east - west, north - south)
    xs = np.linspace(west, east, columns)
    ys = np.linspace(south, north, rows)
    bare = bare_height(terrain)
    return {
        "xs": [float(x) for x in xs],
        "ys": [float(y) for y in ys],
        "heights": [[bare(float(x), float(y)) for x in xs] for y in ys],
    }


def sweep_margin_m(state: ViewState) -> float:
    """How far past the anchors both the sweep and the mesh reach.

    One function, because a mesh smaller than the sweep paints coverage
    cells over nothing. The mesh may be larger — it also has to hold the
    route, and a road outside the anchors is ground with no coverage on
    it rather than coverage with no ground under it.
    """
    # A bore is swept across its own width and no further: nobody stands
    # in the rock, and four kilometres of it either side made the tunnel's
    # sweep a hundred times the work at a tenth of the detail.
    if getattr(state, "bore", False):
        return state.settings().number("tunnel.width_m") / 2.0
    widest = max((run.spacing_m for run in state.runs), default=2000.0)
    return max(widest * 3.0, 4000.0)


def drawable(terrain, west: float, east: float,
             south: float, north: float) -> tuple:
    """A window on the ground, with anything unmeasured trimmed off it.

    The mesh is drawn a sweep's margin past everything on screen, so that
    coverage is never painted over ground that is not there. Where the
    ground is measured that margin runs off the edge of the grid, and
    past the edge `height_at` clamps: the boundary row extruded into a
    plane. Over kizilay that was a 10,7 km sheet around a 3,0 km site —
    ninety-two per cent of the ground on screen invented, drawn in the
    same green as the hills that were real (ADR-0038).

    Asked of the terrain rather than of the site, because the terrain is
    what knows how far it is real: modelled ground has no edge, and a
    bore is a line between two portals rather than a surface, so neither
    is trimmed.
    """
    if terrain.extent_m is None:
        return west, east, south, north
    left, bottom, right, top = terrain.extent_m
    return (max(west, left), min(east, right),
            max(south, bottom), min(north, top))


#: The map the place picker draws, as a one-item list so that `--map-tiles`
#: can replace it without the page and the server disagreeing about which
#: copy is real. OpenStreetMap's own tiles by default: picking a place is
#: the handful of tiles their policy describes as ordinary use, unlike
#: draping a city (ADR-0041, ADR-0042).
MAP_TILES = ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"]


def bare_height(terrain):
    """The ground without what stands on it, for drawing.

    The link budget reads a roof where a footprint stands (`Fetched`), and
    a mesh sampling that draws every building as a spike from wherever a
    sample happened to land. The page draws the bare ground and the
    buildings on it as blocks instead (`site_blocks`).
    """
    from yerkon.world import Fetched

    elevation = terrain.elevation_m
    if isinstance(elevation, Fetched):
        return elevation.site.height_at
    return terrain.height_at


@lru_cache(maxsize=4)
def site_blocks(name: str) -> tuple:
    """Every fetched building of a site, largest first, for the page.

    Each as [x, y, half side, height, lowest ground, highest ground,
    outline]. The outline is the footprint the fetch brought and the link
    budget reads (ADR-0097), a flat run of whole metres x0, y0, x1, y1...;
    where there is none it is empty, and the page draws the disc the
    link budget reads instead as the square of the same area. The page stands a block from the lowest ground under
    it, so on a slope it is sunk rather than hanging off the hill.

    Asked for once per site rather than sent with every scene: Polatlı's
    twenty thousand outlines are a megabyte and a half, and the scene is
    rebuilt on every drag.
    """
    from yerkon.scenarios import fetched

    site = fetched(name) if name else None
    buildings = getattr(site, "buildings", None)
    if buildings is None or buildings.is_empty:
        return ()
    xs = np.asarray(buildings.centre_x_m, dtype=float)
    ys = np.asarray(buildings.centre_y_m, dtype=float)
    radii = np.asarray(buildings.radius_m, dtype=float)
    heights = np.asarray(buildings.height_m, dtype=float)
    share = math.sqrt(math.pi) / 2.0
    rings = [_drawn_outline(buildings.outline(i)) for i in range(len(xs))]
    # One pass over the ground for every corner and vertex there is.
    corners_x, corners_y, owner = [], [], []
    for i, ring in enumerate(rings):
        if ring:
            corners_x += ring[0::2]
            corners_y += ring[1::2]
            owner += [i] * (len(ring) // 2)
        else:
            half = radii[i] * share
            for dx in (-half, half):
                for dy in (-half, half):
                    corners_x.append(xs[i] + dx)
                    corners_y.append(ys[i] + dy)
                    owner.append(i)
    under = site.heights_at(np.asarray(corners_x, dtype=float),
                            np.asarray(corners_y, dtype=float))
    owner = np.asarray(owner, dtype=int)
    low = np.full(len(xs), np.inf)
    high = np.full(len(xs), -np.inf)
    np.minimum.at(low, owner, under)
    np.maximum.at(high, owner, under)
    return tuple(
        (int(round(xs[i])), int(round(ys[i])), round(float(radii[i] * share), 1),
         round(float(heights[i]), 1), int(math.floor(low[i])),
         int(math.ceil(high[i])), rings[i])
        for i in np.argsort(-radii)
    )


def _drawn_outline(points) -> list:
    """A footprint to whole metres, with the points a metre from their
    neighbour dropped: a flat x0, y0, x1, y1... run, or empty."""
    if points is None or len(points) < 3:
        return []
    kept = []
    for px, py in points:
        here = (int(round(float(px))), int(round(float(py))))
        if not kept or abs(here[0] - kept[-1][0]) + abs(here[1] - kept[-1][1]) >= 1:
            kept.append(here)
    if len(kept) > 1 and kept[0] == kept[-1]:
        kept.pop()
    if len(kept) < 3:
        return []
    return [value for point in kept for value in point]


#: How far apart the drawn road network's points stand, at least, in
#: metres, and as a share of the drawn ground's longer side. A fetched
#: network is thousands of vertices; this keeps every bend a person can
#: see at that scale, and a twenty kilometre site's streets under a
#: hundred and fifty kilobytes.
ROAD_STEP_M = 20.0
ROAD_STEP_SHARE = 1.0 / 150.0


def _roads(measured, terrain, box) -> list:
    """The fetched road network over the drawn ground, for the page.

    Drawn, never read: the units drive the route, and this is the
    streets around it, so a layout can be judged against where the
    roads actually are. Empty where the ground is modelled or the fetch
    brought no roads, and the page greys its switch (ADR-0036).
    """
    if measured is None:
        return []
    west, east, south, north = box
    step = max(ROAD_STEP_M, max(east - west, north - south) * ROAD_STEP_SHARE)
    drawn = []

    def point(x, y):
        return [round(float(x), 1), round(float(y), 1),
                round(terrain.height_at(float(x), float(y)), 1)]

    def close(run, tail):
        # A street's last point always, so a short one is still a line.
        if tail is not None and (not run or run[-1][:2] != point(*tail)[:2]):
            run.append(point(*tail))
        # A stub shorter than a step is a driveway at this scale.
        if len(run) >= 2 and math.dist(run[0][:2], run[-1][:2]) >= step:
            drawn.append(run)

    for line in getattr(measured, "roads_m", ()) or ():
        run, last, tail = [], None, None
        for x, y in line:
            if not (west <= x <= east and south <= y <= north):
                close(run, tail)
                run, last, tail = [], None, None
                continue
            tail = (x, y)
            if last is not None and math.dist(last, (x, y)) < step:
                continue
            run.append(point(x, y))
            last = (x, y)
        close(run, tail)
    return drawn


def _aerial(state: ViewState, measured) -> Optional[dict]:
    """Where the site's photograph is and what ground it covers.

    Nothing where none was fetched, and the page greys its switch: a
    control that does nothing is not a control (ADR-0036).

    The address carries the site's name so that the browser caches one
    picture per site and changing ground fetches the new one, rather than
    both sites sharing an address and whichever loaded first winning.
    """
    if measured is None:
        return None
    drape = getattr(measured, "drape", None)
    if measured.aerial is None and drape is not None:
        # The page stitches this one from the provider's tiles; it gets
        # which tiles and where they sit, and the key it caches under
        # (ADR-0087).
        west, south, east, north = measured.drape_extent_m
        return {
            "url": "drape:{}:{}".format(quote(state.site), drape.zoom),
            "tiles": {"template": drape.template, "zoom": drape.zoom,
                      "west_x": drape.west_x, "north_y": drape.north_y,
                      "east_x": drape.east_x, "south_y": drape.south_y},
            "extent_m": [west, south, east, north],
            "source": drape.source,
            "zoom": drape.zoom,
        }
    if measured.aerial is None:
        return None
    west, south, east, north = measured.aerial_extent_m
    return {
        "url": "/api/aerial.png?site={}".format(quote(state.site)),
        "extent_m": [west, south, east, north],
        "metres_per_pixel": measured.aerial.metres_per_pixel,
        "source": measured.aerial.source,
        "zoom": measured.aerial.zoom,
    }


def _disc_json(state: ViewState, run) -> Optional[dict]:
    """The reach a search placed against, and whether it was measured."""
    if run.method not in LAYOUT_SEARCHES:
        return None
    if run.reach_m:
        # Set by hand, so it is neither measured nor a ceiling.
        return {"metres": float(run.reach_m), "measured": True, "by_hand": True}
    reach = reach_on(state, run)
    return {"metres": float(reach.metres), "measured": bool(reach.measured),
            "by_hand": False}


def _bar_json(bar) -> Optional[dict]:
    """One run's bar, as the page reads it. Nothing where there is no bar."""
    if bar is None:
        return None
    return {
        "name": bar.name,
        "wanted": float(bar.wanted),
        "got": float(bar.got),
        "met": bool(bar.met),
        "spent_the_budget": bool(bar.spent_the_budget),
        "short": int(bar.short),
        "served_share": float(bar.served_share),
    }


@lru_cache(maxsize=512)
def _both_ways(pole: Terminal, unit: Terminal, region, target_sigma_m: float):
    """How far a pole and a unit reach each other, over open ground.

    Both ways: an exchange is a question and an answer, so a range
    counts only where the pole reaches the unit and the unit's reply
    reaches the pole. Flat ground with nothing on it, so the most this
    pairing gives; the run itself stands on the real ground.
    """
    closes = min(closure_range_m(pole, unit, region=region),
                 closure_range_m(unit, pole, region=region))
    precise = min(
        usable_range_m(pole, unit, pole.radio, target_sigma_m, region=region),
        usable_range_m(unit, pole, pole.radio, target_sigma_m, region=region))
    return closes, precise


def unit_ranges(state: ViewState, deployment) -> list:
    """Every unit against every group of anchors, with the radios,
    antennas and heights the run itself uses.

    Not the group's reach ring above it, which is quoted for a stock
    antenna at both ends: this is what this unit and these anchors do.
    A unit carrying no radio the group speaks gets no range.
    """
    from yerkon.ranging import share_a_waveform

    if deployment is None:
        return []
    mounting_of, radio_of = state.catalogues()
    out = []
    for run in state.runs:
        radio = chosen(radio_of, run.radio, "radio")
        mounting = chosen(mounting_of, run.mounting, "mounting")
        pole = Terminal(radio, deployment.antenna,
                        (0.0, 0.0, float(mounting.height_m.value)))
        for unit in deployment.receivers:
            spoken = [r for r in unit.radios if share_a_waveform(radio, r)]
            entry = {"run": run.identifier, "unit": unit.identifier,
                     "radio": spoken[0].part if spoken else None,
                     "antenna": unit.antenna.part,
                     "closes_m": None, "precise_m": None}
            if spoken:
                me = Terminal(spoken[0], unit.antenna,
                              (0.0, 0.0, unit.journey.antenna_height_m))
                closes, precise = _both_ways(pole, me, deployment.region,
                                             float(state.tolerance_m))
                entry.update(closes_m=closes, precise_m=precise)
            out.append(entry)
    return out


#: Ways of equipping a tab's 2,4 GHz anchors and units, all at once: the
#: pole's module, the vehicle's and the pedestrian's, the pole and
#: vehicle antennas, and the spectrum rule. The same five the local
#: hardware comparison runs (`tools/hardware.py`). An empty antenna is
#: the row's own, the 5 dBi rod.
HARDWARE_SETUPS = (
    ("e28-20s", "e28", "e28", "e28", "", "", "TR-FHSS"),
    ("e28-12s", "sx1280", "e28", "e28", "", "", "TR-FHSS"),
    ("e28-27s", "e28-27s", "e28", "e28", "", "", "TR-FHSS"),
    ("e28-12s-uncertified", "sx1280", "e28", "e28", "", "", "TR"),
    ("o4", "sx1280", "sx1280", "sx1280", "mast", "roof", "TR"),
)


def setups(state: ViewState) -> list:
    """Each hardware setup as the edit it makes to this tab.

    Only the 2,4 GHz groups and units move; a UWB group keeps its module.
    A tab with no 2,4 GHz group is offered none, because a setup would
    only change its spectrum rule.
    """
    if not any(run.radio != "dwm3000" for run in state.runs):
        return []
    out = []
    for key, pole, vehicle, pedestrian, pole_ant, vehicle_ant, rule in HARDWARE_SETUPS:
        runs = [
            {**run.as_json(), "radio": pole} if run.radio != "dwm3000"
            else run.as_json()
            for run in state.runs
        ]
        units = []
        for unit in state.units:
            module = vehicle if unit.kind == "vehicle" else pedestrian
            radios = [module] + [r for r in unit.radios if r == "dwm3000"]
            units.append({**unit.as_json(), "radios": radios})
        changes = {"runs": runs, "units": units, "region": rule,
                   "pole_antenna": pole_ant, "vehicle_antenna": vehicle_ant}
        current = (
            state.region == rule
            and state.pole_antenna in (pole_ant, "rod" if not pole_ant else pole_ant)
            and state.vehicle_antenna in (vehicle_ant, "rod" if not vehicle_ant else vehicle_ant)
            and all(run.radio == pole for run in state.runs if run.radio != "dwm3000")
            and all(list(u.radios) == c["radios"] for u, c in zip(state.units, units))
        )
        out.append({"key": key, "changes": changes, "current": current})
    return out


def boards(state: ViewState, deployment) -> list:
    """What every group's units and every receiver are built from, and
    what one costs at one, a hundred and a thousand."""
    from yerkon.bom import TIERS
    from yerkon.cost import anchor_board, receiver_board

    if deployment is None:
        return []
    _, radio_of = state.catalogues()
    out = []
    for run in state.runs:
        radio = chosen(radio_of, run.radio, "radio")
        board = anchor_board(radio.part, deployment.antenna.part)
        out.append({"of": "run", "name": run.identifier,
                    "parts": [part.name for part in board.parts],
                    "tl": [board.at(tier) for tier in TIERS]})
    for unit in deployment.receivers:
        board = receiver_board(unit.product,
                               tuple(radio.part for radio in unit.radios),
                               unit.antenna.part)
        out.append({"of": "unit", "name": unit.identifier,
                    "parts": [part.name for part in board.parts],
                    "tl": [board.at(tier) for tier in TIERS]})
    return out


def scene(state: ViewState) -> dict:
    """Ground, road, anchors and units. Cheap enough to redraw on every drag."""
    terrain = state.terrain()
    # An empty arrangement is drawable and not evaluable (ADR-0043), so
    # the thing that refuses to be empty is built only when there is
    # something in it. What it is still asked for — who can hear whom,
    # how long a round takes — is real engine logic and stays there
    # rather than being written out a second time here.
    standing = state.placed(terrain)
    bars = state.bars(terrain)
    anchors_here = tuple(anchor for _, anchor in standing)
    receivers_here = state.receivers(terrain)
    deployment = state.deployment(terrain) if anchors_here else None
    mounting_of, radio_of = state.catalogues()

    # The route the units actually take, not a line drawn along x. Over
    # an area that is a circuit round the edge and across the middle, and
    # drawing a straight line instead showed a deployment nobody was
    # simulating — the picture and the run disagreeing with nothing on
    # screen to say which was real.
    driven = state.road(
        terrain, state.units[0].route if state.units else "")
    route = [
        driven.point_at(along)
        for along in np.linspace(0.0, driven.length_m, 160)
    ]

    # Ground under everything on screen: the anchors and the route both.
    #
    # From the anchors alone, the corridor length moved nothing a person
    # could see. An anchor run keeps its own start and end, so lengthening
    # the site stretched the road and left the mesh where it was — the
    # ground stayed exactly the shape it had been and the road drove off
    # the edge of it into nothing. The site is what is drawn, and the
    # route is half of the site.
    margin = sweep_margin_m(state)
    seen = [a.position_m[:2] for a in anchors_here]
    seen += [(point[0], point[1]) for point in route]
    west, east = min(p[0] for p in seen), max(p[0] for p in seen)
    south, north = min(p[1] for p in seen), max(p[1] for p in seen)
    west, east, south, north = drawable(
        terrain, west - margin, east + margin, south - margin, north + margin)
    columns, rows = mesh_shape(east - west, north - south)
    xs = np.linspace(west, east, columns)
    ys = np.linspace(south, north, rows)
    bare = bare_height(terrain)
    heights = [[bare(float(x), float(y)) for x in xs] for y in ys]

    # One reach per run, because a UWB bracket and a mast on the same
    # corridor do not cover remotely the same ground.
    reach = {run.identifier: reach_of(state, run) for run in state.runs}
    closure = {run.identifier: closure_of(state, run) for run in state.runs}
    # Read off the placement rather than worked out by placing again.
    #
    # This used to call `run.anchors` a second time to see which run had
    # produced which anchor, and a second call is a second question: it
    # went without the route a corridor follows, without the structures
    # a search bolts to and without the reach measured over this ground,
    # so it recognised six of the twenty-six anchors a corridor placed
    # and fifty-two of the sixty `greedy-dop` placed. The rest were
    # drawn in no colour, given no reach ring and counted on no card
    # (ADR-0049).
    run_of = {anchor.identifier: run_id for run_id, anchor in standing}

    anchors = []
    for anchor in anchors_here:
        x, y = anchor.ground_position_m
        run_id = run_of.get(anchor.identifier, "")
        anchors.append({
            "id": anchor.identifier,
            "run": run_id,
            "x": float(x),
            "y": float(y),
            "ground_z": terrain.height_at(x, y),
            # The ground without the building under a roof anchor, which
            # the page draws as a block on it.
            "bare_z": bare_height(terrain)(x, y),
            "z": anchor.position_m[2],
            "mounting": anchor.mounting.kind,
            "radio": anchor.radio.part,
            "height_m": float(anchor.mounting.height_m.value),
            "moved": anchor.identifier in state.moved,
            "reach_m": reach.get(run_id, 0.0),
        })

    road = [
        {"x": float(x), "y": float(y), "z": float(z)} for x, y, z in route
    ]

    units = []
    for unit in receivers_here:
        trail = [
            unit.journey.position_at(at_s)
            for at_s in np.linspace(0.0, unit.journey.duration_s, 40)
        ]
        units.append({
            "id": unit.identifier,
            "kind": unit.product,
            "hears": 0 if deployment is None
                     else len(deployment.anchors_heard_by(unit)),
            "radios": [radio.part for radio in unit.radios],
            "at": list(unit.journey.position_at(0.0)),
            "trail": [list(point) for point in trail],
        })

    return {
        "terrain": {
            "xs": [float(x) for x in xs],
            "ys": [float(y) for y in ys],
            "heights": heights,
            "description": terrain.description,
            # What ground is on hand, found rather than listed, so a
            # fourth `yerkon fetch` appears in the menu on its own.
            "sites": list(fetched_sites()),
            # How far the fetch actually reached, so the sliders cannot
            # offer a site larger than the ground under it (ADR-0037).
            # Absent where the ground is modelled, which has no edge.
            "measured_m": (
                [measured.width_m, measured.height_m]
                if (measured := state.measured()) is not None else None
            ),
            # How many buildings the fetch brought. Where there are any,
            # the blanket clutter figure is not charged — the obstruction
            # is in the ground itself — so the page has to grey it rather
            # than leave a slider that moves nothing (ADR-0036, ADR-0038).
            "buildings": (
                0 if measured is None or measured.buildings is None
                else len(measured.buildings)
            ),
            # The photograph, as a place to fetch it from rather than as
            # colours in this payload. A mesh node is three bytes of
            # colour and there are twenty-two thousand of them, so
            # sending the picture pixel by pixel would put a quarter of a
            # megabyte on the wire on every drag, to say what one PNG the
            # browser caches says once.
            "aerial": _aerial(state, measured),
            # The buildings, as blocks on the bare ground, and the streets
            # beside the route the units drive. None inside a bore: what
            # stands on the mountain is not in the tunnel.
            # Which site's buildings stand on this ground, asked for once
            # from `/api/blocks` (`site_blocks`); nothing inside a bore.
            "blocks_site": "" if state.bore or measured is None else state.site,
            "roads": [] if state.bore else _roads(
                measured, terrain,
                (float(xs[0]), float(xs[-1]), float(ys[0]), float(ys[-1]))),
        },
        # Where the map picker fetches its tiles. Named by the engine
        # rather than written into the page, so `--map-tiles` can point
        # it at a self-hosted server — or at nothing, on a machine with
        # no way out, where the picker then says so instead of showing a
        # grey rectangle (ADR-0042).
        "map_tiles": MAP_TILES[0],
        # What the model actually offers. Hardcoded in the page before,
        # and it had drifted: the tunnel bracket was missing entirely, so
        # the one mounting the tunnel row uses could not be chosen and
        # its dropdown silently showed a roadside sign instead.
        "choices": {
            # Named here rather than in the page, like every other list
            # the engine owns: a method that exists can be chosen and one
            # that does not cannot be offered (ADR-0028).
            # Each with the kind it is grouped under in the chooser.
            "layouts": [
                [name, say("layout." + name, state.language),
                 say("layout.group." + _LAYOUT_GROUP.get(name, "pattern"),
                     state.language)]
                for name in LAYOUT_METHODS
            ],
            # Routes a unit can drive. The empty one first, because it is
            # what every unit did before there was a choice and is still
            # the honest default: the site's own shape.
            "routes": (
                [["", say("route.site", state.language)]]
                + [[name, say("route." + name, state.language)]
                   for name in ROUTE_METHODS]
            ),
            # Which routes this ground can actually carry. The real road
            # needs road geometry a fetch has not brought yet, and a
            # control that does nothing is not a control (ADR-0036).
            "routes_live": [
                name for name in ROUTE_METHODS
                if name != "road" or drivable(state.course())
            ],
            "mountings": [
                [key, "{} ({:.0f} m)".format(
                    option.kind.title(), float(option.height_m.value))]
                for key, option in sorted(
                    mounting_of.items(),
                    key=lambda pair: float(pair[1].height_m.value))
                # A roof is only where a building stands, so a whole run
                # on "roof" would put brackets on bare ground (ADR-0081).
                if key not in ONLY_WHERE_PLACED
            ],
            "radios": [
                [key, radio.part] for key, radio in sorted(radio_of.items())
            ],
            "modes": [
                [name, label]
                for name, label in mode_labels(state.language).items()
            ],
            # Served rather than written into the page, like everything
            # else it offers: the page should never hold a second list
            # that can drift from the engine's.
            "languages": [[name, LANGUAGE_NAMES[name]] for name in LANGUAGES],
            # What this install cannot fetch with, so the page can say so
            # before somebody picks a place rather than after it has
            # gone looking for one (ADR-0036, ADR-0051).
            "fetch_missing": list(missing_for_a_fetch()),
        },
        "road": road,
        "anchors": anchors,
        "units": units,
        "runs": [
            {
                **run.as_json(),
                "reach_m": reach[run.identifier],
                "closure_m": closure[run.identifier],
                "count": sum(
                    1 for a in anchors if a["run"] == run.identifier
                ),
                # Whether the search cleared what it was asked for, or
                # stopped for one of the two reasons that look the same
                # from outside (ADR-0056). Nothing under a lattice: a
                # spacing is not a target.
                "bar": _bar_json(bars.get(run.identifier)),
                # The disc a search actually placed against, which is
                # not the ring beside it: the ring is the open-ground
                # figure and the search uses what this ground measures
                # (ADR-0047, ADR-0057). Nothing under a lattice, which
                # never reads it.
                "disc": _disc_json(state, run),
            }
            for run in state.runs
        ],
        # Absent rather than zero.
        #
        # Zero looked safer and was not: the panel divides by it to get
        # fixes a second, and an empty arrangement printed "1000000000,00
        # /s" — a number that looks like a finding and is a division by
        # nothing. There is no round when there is nothing to take a turn
        # at, and the panel draws a dash for what does not exist.
        "round_s": None if deployment is None else deployment.round_duration_s(),
        "ranges": unit_ranges(state, deployment),
        "setups": setups(state),
        "boards": boards(state, deployment),
        "assumed": len(state.settings().assumed),
        "assumed_total": len(state.settings().entries),
        "state": state.as_json(),
    }


#: How the figures are grouped in the panel, and what to call each group.
#:
#: A figure whose group is missing from here is sent to the page and
#: never drawn, which is how the sixteen deployment figures spent a whole
#: release "editable in the viewer" without appearing in it. The test
#: below the panel checks every group present in the file has a heading.
GROUPS = (
    ("urban", "Şehir içi yerleşimi"),
    ("rural", "Kırsal yerleşim"),
    ("tunnel", "Tünel yerleşimi"),
    ("mounting", "Montaj yapıları"),
    ("operating", "İşletme giderleri"),
    ("radio", "Modüllerin yayımlanmamış değerleri"),
    ("clock", "Saatler"),
    ("ranging", "Ölçüm alışverişi"),
    ("site", "Saha"),
    ("estimator", "Kestirici"),
)


def figures(state: ViewState) -> dict:
    """Every figure nobody supplied, as the panel needs it.

    Sent whole rather than by group, because the thing a person wants to
    see is how much of the study is still resting on guesses, and that is
    a property of the list rather than of any part of it.
    """
    from yerkon.viewer.costing import UNITS

    def unit_named(unit, language):
        return UNITS.get(unit, (unit, unit))[language == "en"]

    settings = state.settings()
    listed = []
    for key, entry in sorted(settings.entries.items()):
        head = key.split(".")[0]
        listed.append({
            "key": key,
            "group": head,
            "value": entry.sourced.value if entry.sourced.is_text
            else float(entry.sourced.value),
            "is_text": entry.sourced.is_text,
            "unit": unit_named(entry.sourced.unit, state.language),
            "provenance": entry.sourced.provenance.value,
            "source": entry.sourced.source,
            "note": entry.sourced.note,
            "affects": entry.affects,
            "sensitivity": entry.sensitivity,
            "assumed": entry.is_assumed,
            "edited": key in state.overrides,
        })
    return {
        "figures": listed,
        "groups": [
            {"key": key, "label": label}
            for key, label in GROUPS
            if any(f["group"] == key for f in listed)
        ],
        "assumed": len(settings.assumed),
        "total": len(settings.entries),
    }


def swept_cells(state: ViewState) -> tuple:
    """Where `sweep` will paint, without running it.

    The same axes the sweep uses, from the same function, so a check that
    the ground mesh covers them is a check on the sweep itself.
    """
    from yerkon.evaluate import sweep_axes

    terrain = state.terrain()
    if not state.anchors(terrain):
        return [], []
    xs, ys = sweep_axes(state.deployment(terrain), terrain,
                        resolution_m=state.sweep_m,
                        margin_m=sweep_margin_m(state))
    return [float(x) for x in xs], [float(y) for y in ys]


def sweep(state: ViewState) -> dict:
    """How many anchors reach each cell of the ground. Seconds, not milliseconds."""
    terrain = state.terrain()
    # An arrangement with nothing in it reaches nowhere, which is an
    # answer rather than an error: this paints an overlay on a picture,
    # and a blank sheet is a picture (ADR-0043). The refusal belongs to
    # the run, which is where a number would be published.
    if not state.anchors(terrain):
        # Said rather than left out. A missing key and a key that says
        # "there is no such number" read the same to a page that checks,
        # and differently to one that does not.
        return {"xs": [], "ys": [], "counts": [], "resolution_m": state.sweep_m,
                "served_km2": None, "reached_km2": None,
                "layers": {}, "bands": _bands(state)}
    deployment = state.deployment(terrain)

    grid = coverage_grid(
        deployment,
        terrain,
        receiver_height_m=_lowest_unit(state),
        target_sigma_m=state.tolerance_m,
        resolution_m=state.sweep_m,
        margin_m=sweep_margin_m(state),
    )

    return {
        "xs": [float(x) for x in grid.xs],
        "ys": [float(y) for y in grid.ys],
        "counts": grid.counts.tolist(),
        "resolution_m": grid.resolution_m,
        "reached_km2": grid.area_reached_by(1),
        "served_km2": grid.area_reached_by(4),
        # Four readings of the same sweep. The link budget behind them
        # is run either way — keeping its answer rather than reducing it
        # to a boolean costs about three percent (ADR-0044).
        "layers": {
            "anchors": grid.counts.tolist(),
            "margin_db": _sendable(grid.margin_db),
            "dilution": _sendable(grid.dilution),
            "error_m": _sendable(grid.error_m),
        },
        "bands": _bands(state),
    }


def _sendable(layer) -> list:
    """A float grid as JSON, with `null` where there is no number.

    NaN is not JSON. `json.dumps` writes it as a bare `NaN`, which is not
    in the specification, which `JSON.parse` refuses, and which would
    therefore turn one unreachable cell into a page that stopped
    updating.
    """
    if layer is None:
        return []
    return [[None if value != value else float(value) for value in row]
            for row in layer]


#: Where each layer's colours change.
#:
#: Four bands and no more. A continuous ramp looks like more information
#: than a swept grid contains and invites reading a boundary off a
#: gradient; these are the thresholds somebody would actually name.
#:
#: A layer that reads better as it grows takes **four** thresholds: the
#: first is the floor below which there is nothing worth painting, and
#: the other three split what is left. A layer that reads worse as it
#: grows takes **three**, because "nothing here" arrives as a null rather
#: than as a small number — there is no dilution at all until three
#: anchors reach, and no error to estimate without one.
#:
#: The margins are the usual link-design ones — under 6 dB is thin, 20 dB
#: is comfortable. The dilutions are the GNSS convention, where under 2
#: is what "good geometry" means (ADR-0040 uses the same figure as its
#: default bar). The errors are multiples of *this row's own tolerance*,
#: because the question this project asks is whether ground meets the
#: bar, not how it scores against an abstract scale (ADR-0015).
def _bands(state: ViewState) -> dict:
    bar = max(state.tolerance_m, 0.1)
    return {
        "anchors": [1, FEWEST_FOR_A_FIX, 4, 6],
        "margin_db": [0.0, 6.0, 12.0, 20.0],
        "dilution": [1.5, 2.0, 4.0],
        "error_m": [bar, bar * 2.0, bar * 4.0],
    }


#: Draws already run this process, keyed by what produced them.
#:
#: The page asks for one draw and then for the rest, and the rest are
#: only worth asking for if the first one is not thrown away. Bounded
#: the way placements are, for the same reason.
_DRAWS: dict = {}

#: How many draws are kept at once. Two arrangements' worth of eight,
#: so moving back to the previous layout does not pay for it again.
DRAWS_KEPT = 16


def _one_draw(job: tuple) -> tuple:
    """One draw, computed. Runs in a worker process, so it takes only
    what pickles and reaches for nothing on this side."""
    state, scenario, with_area = job
    samples = run_scenario(scenario)
    if not with_area:
        return samples, (math.nan, math.nan)
    grid = coverage_grid(
        state.deployment(scenario.terrain), scenario.terrain,
        receiver_height_m=_lowest_unit(state),
        target_sigma_m=state.tolerance_m,
        resolution_m=state.sweep_m,
        margin_m=sweep_margin_m(state),
    )
    return samples, (grid.area_reached_by(4), grid.area_reached_by(1))


def _keep(key: tuple, answer: tuple) -> tuple:
    """Hold a draw, dropping the oldest once there are too many."""
    while len(_DRAWS) >= DRAWS_KEPT:
        _DRAWS.pop(next(iter(_DRAWS)))
    _DRAWS[key] = answer
    return answer


def _numbers(state: ViewState, deployed, samples, served_km2, reached_km2,
             done: int, wanted: int) -> dict:
    """One dictionary of figures, however many draws went into it."""
    costing = price(deployed.inventory(served_km2), DEFAULT_RATES)
    hpe_p50, _ = samples.percentile(50)
    hpe_p95, vpe_p95 = samples.percentile(95)

    return {
        "draws_done": done,
        "draws_wanted": wanted,
        "hpe_p50_m": hpe_p50,
        "hpe_p95_m": hpe_p95,
        "vpe_p95_m": vpe_p95,
        "availability": samples.availability,
        "fixes": samples.produced,
        "attempted": samples.attempted,
        "lost_links": samples.lost_links,
        "attempted_links": samples.attempted_links,
        "served_km2": served_km2,
        "reached_km2": reached_km2,
        "anchors": len(deployed.scenario.deployment.anchors),
        "capex_tl": costing.capex_tl,
        "opex_tl_per_year": costing.opex_tl_per_year,
        "capex_tl_per_km2": costing.capex_tl_per_km2,
        "opex_tl_per_km2_year": costing.opex_tl_per_km2_year,
        "capex_tl_per_route_km": costing.capex_tl_per_route_km,
        "assumed_share": costing.assumed_share,
        "round_s": deployed.scenario.deployment.round_duration_s(),
        "units": len(deployed.scenario.deployment.receivers),
    }


def simulate(state: ViewState) -> dict:
    """Drive the journey once and price the deployment. The slow one.

    One draw of the shadows, which is what a simulation is (ADR-0055).
    The table pools eight of them, so this is the first of eight rather
    than the answer, and it says so in ``draws_done``: the page shows it
    at once and asks for the rest (ADR-0050).
    """
    deployed = state.deployed()
    terrain = state.terrain()
    scenarios = draws_of(deployed)
    key = (run_key(state, terrain), 0, True)
    samples, (served_km2, reached_km2) = (
        _DRAWS[key] if key in _DRAWS
        else _keep(key, _one_draw((state, scenarios[0], True))))
    return _numbers(state, deployed, samples, served_km2, reached_km2,
                    done=1, wanted=len(scenarios))


def pool(state: ViewState) -> dict:
    """The same arrangement over every draw of the shadows.

    What the table publishes, by the same arithmetic (`report.folded`):
    the samples pool because a percentile is a statement about a
    population, and the areas average because an area is an answer per
    draw. Draws already worked out are taken from the store, so the
    press after `simulate` pays for the rest and not for all of them.

    The areas stop at ``AREA_DRAWS`` the way the table's do. Over
    Kızılay's eight draws the covered area ran 6,280 to 6,760 km², which
    is 7,3 % of its mean, where the rural row's ninety-fifth percentile
    ran 9,67 to 18,75 m, which is 94 %. An area settles and a tail does
    not.
    """
    deployed = state.deployed()
    terrain = state.terrain()
    scenarios = draws_of(deployed)
    if len(scenarios) <= 1:
        return simulate(state)

    here = run_key(state, terrain)
    wanted = [(index, index < AREA_DRAWS) for index in range(len(scenarios))]
    missing = [job for job in wanted if (here, *job) not in _DRAWS]
    if missing:
        jobs = [(state, scenarios[index], with_area)
                for index, with_area in missing]
        for job, answer in zip(missing, spread(_one_draw, jobs)):
            _keep((here, *job), answer)

    drawn = [_DRAWS[(here, *job)] for job in wanted]
    served = [areas[0] for _, areas in drawn if math.isfinite(areas[0])]
    reached = [areas[1] for _, areas in drawn if math.isfinite(areas[1])]
    return _numbers(
        state, deployed,
        pooled([samples for samples, _ in drawn], deployed.scenario.name),
        sum(served) / len(served) if served else math.nan,
        sum(reached) / len(reached) if reached else math.nan,
        done=len(scenarios), wanted=len(scenarios),
    )
