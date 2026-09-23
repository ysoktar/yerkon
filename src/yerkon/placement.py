"""Where anchors go when they do not have to go on a grid (ADR-0081).

The table's rows put anchors on a lattice: every 500 m in town, every
3 km in open country. A lattice is easy to describe and easy to cost,
and it ignores everything the ground offers. A town already has lighting
columns, signs and tall buildings; open country already has hills and a
distribution network along its roads. An anchor ten metres up on a hill
reaches further than one on a pole in a hollow, and a roof that is
already thirty metres up costs a bracket rather than a mast.

This module asks the question as an operations research problem:

* **Candidates** are places that are already high or already standing:
  the fetched street furniture, the roofs of the tallest buildings, the
  local high points of the ground, the road side where the network's
  poles run, and the lattice's own spots so the search can always fall
  back on the grid.
* **Coverage** is decided by the same link budget the simulator runs:
  a candidate covers a cell when the link to a receiver 1,5 m above it
  closes and ranges to within the tolerance, over the real terrain and
  buildings. Nothing here draws a disc.
* **The choice** is a budgeted maximum k-cover: a position needs four
  ranges, so a cell counts once four chosen anchors reach it. A greedy
  pass picks by coverage gained per lira of lifecycle cost, then a drop
  pass removes anchors the answer does not need, then an interchange
  pass (Teitz and Bart) swaps chosen anchors for cheaper ones wherever
  the coverage holds.

The answer is judged by running the full simulation on it beside the
grid, not by the search's own count. The search sees coverage; the
simulation sees geometry, rounds, shadows and noise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Optional, Sequence

import numpy as np

from yerkon.cost import AnchorSite, Inventory, OperatingRates, anchor_product, price
from yerkon.evaluate import _sweep_radios
from yerkon.ranging import audible
from yerkon.rf import Terminal, evaluate_link, ranging_sigma_m
from yerkon.settings import DEFAULTS, Settings
from yerkon.site.fetch import DEFAULT_BUILDING_HEIGHT_M
from yerkon.world import Anchor, MountingOption, mountings

#: What the fetched furniture calls a structure, and the mounting that is.
FURNITURE_MOUNTING = {
    "column": "lighting_column",
    "sign": "roadside_sign",
}

#: How each row's search is sized.
#:
#: ``reach_m`` is how far a candidate is tested: past it no link is
#: evaluated and the cell is counted as out of reach. It is wider than
#: any usable range the design panel derives for these mountings, so it
#: prunes work rather than coverage. ``cell_m`` is the demand lattice,
#: the same resolution the row's coverage sweep uses. ``road_step_m`` is
#: the lattice road-side candidates are thinned to; ``roof_min_m`` the
#: lowest building worth a roof candidate; ``hill_window_m`` the
#: neighbourhood a high point has to top.
SIZING = {
    "urban": dict(reach_m=1500.0, cell_m=100.0, road_step_m=150.0,
                  road_mounting="lighting_column", roof_min_m=15.0,
                  roof_step_m=150.0, hill_window_m=600.0, hills=12),
    "rural": dict(reach_m=9000.0, cell_m=500.0, road_step_m=750.0,
                  road_mounting="distribution_pole", roof_min_m=12.0,
                  roof_step_m=750.0, hill_window_m=3000.0, hills=30),
}

#: Four ranges place a point in three dimensions (ADR-0012).
ANCHORS_REQUIRED = 4
#: Quarters around a cell its anchors have to stand in (see `Cover`).
QUARTERS_REQUIRED = 3
#: The tolerance a range has to meet for the anchor to count, in metres.
TARGET_SIGMA_M = 5.0
RECEIVER_HEIGHT_M = 1.5


@dataclass(frozen=True)
class Candidate:
    """One place an anchor could go, and what it would cost there."""

    anchor: Anchor
    #: Where the candidate came from: furniture, rooftop, hilltop, road
    #: or grid. Said in the answer so a reader can see what the search
    #: actually used.
    origin: str
    #: Capital plus service life times the yearly operating cost.
    lifecycle_tl: float


@dataclass(frozen=True)
class Problem:
    """Candidates, demand cells, and which candidate reaches which cell."""

    candidates: tuple[Candidate, ...]
    #: Demand cells as (x, y), one row each.
    cells: np.ndarray
    #: ``reach[c, j]`` is true when candidate c ranges to cell j.
    reach: np.ndarray
    #: Indices of the candidates that are the incumbent grid.
    grid: tuple[int, ...]
    #: ``quarter[c, j]`` is which quarter around cell j candidate c
    #: stands in: 0 east, 1 north, 2 west, 3 south.
    quarter: np.ndarray

    def share(self, chosen: Sequence[int]) -> float:
        """Share of cells the chosen anchors serve (see `Cover`)."""
        return Cover(self, chosen).share()

    def cost(self, chosen: Sequence[int]) -> float:
        return float(sum(self.candidates[i].lifecycle_tl for i in chosen))


# --- Cost -----------------------------------------------------------------


def lifecycle_tl(mounting: MountingOption, part: str,
                 rates: OperatingRates, settings: Settings = DEFAULTS) -> float:
    """What one anchor costs over its service life, from the cost model.

    Priced through `cost.price` rather than added up here, so a change to
    any rate reaches the search the same way it reaches the table.
    """
    site = AnchorSite(
        product=anchor_product(part),
        structure=mounting.kind,
        site_cost_tl=mounting.site_cost_tl,
        has_power=mounting.has_power,
        has_backhaul=mounting.has_backhaul,
        rent_tl_per_year=(float(mounting.rent_tl_per_year.value)
                          if mounting.rent_tl_per_year is not None else 0.0),
    )
    costing = price(Inventory(anchors=(site,)), rates)
    life = float(rates.service_life_years.value)
    return costing.capex_tl + life * costing.opex_tl_per_year


# --- Candidates -----------------------------------------------------------


def _thinned(points: Sequence[tuple], step_m: float) -> list:
    """One point per lattice square, the first that falls in it.

    Callers sort by preference first, so "first" is "best".
    """
    kept, seen = [], set()
    for point in points:
        key = (int(point[0] // step_m), int(point[1] // step_m))
        if key not in seen:
            seen.add(key)
            kept.append(point)
    return kept


def _along_roads(roads: Sequence, step_m: float) -> list:
    """Points every ``step_m`` along each road centreline."""
    out = []
    for road in roads:
        line = np.asarray(road, dtype=float)
        if len(line) < 2:
            continue
        for (x0, y0), (x1, y1) in zip(line[:-1], line[1:]):
            span = math.hypot(x1 - x0, y1 - y0)
            for fraction in np.arange(0.0, 1.0, step_m / max(span, step_m)):
                out.append((x0 + (x1 - x0) * fraction,
                            y0 + (y1 - y0) * fraction))
    return out


def _high_points(site, window_m: float, how_many: int) -> list:
    """The bare ground's local summits, most prominent first.

    A cell is a summit when nothing within ``window_m`` of it is higher,
    and its prominence is how far it stands over the mean of that
    window. Bare ground rather than roofs: a roof is its own candidate.
    """
    grid = np.asarray(site.elevation_grid_m, dtype=float)
    radius = max(int(window_m / 2 / site.grid_spacing_m), 1)
    padded = np.pad(grid, radius, mode="edge")
    highest = np.full_like(grid, -np.inf)
    total = np.zeros_like(grid)
    rows, columns = grid.shape
    for dy in range(0, 2 * radius + 1, max(radius // 4, 1)):
        for dx in range(0, 2 * radius + 1, max(radius // 4, 1)):
            window = padded[dy:dy + rows, dx:dx + columns]
            highest = np.maximum(highest, window)
            total += window
    samples = len(range(0, 2 * radius + 1, max(radius // 4, 1))) ** 2
    prominence = grid - total / samples
    summits = np.argwhere((grid >= highest) & (prominence > 0.0))
    ranked = sorted(summits, key=lambda rc: -prominence[rc[0], rc[1]])
    return [
        (float(c * site.grid_spacing_m), float(r * site.grid_spacing_m))
        for r, c in ranked[:how_many]
    ]


def candidates(deployed, site, row: str, settings: Settings = DEFAULTS,
               rates: Optional[OperatingRates] = None) -> tuple[list, tuple]:
    """Every place the search may choose, and which of them are the grid.

    Kept inside the ground the row stands on: a candidate past the edge
    of the fetched grid would stand on the clamp (ADR-0037).
    """
    from yerkon.cost import operating_rates

    rates = rates or operating_rates(settings)
    sizing = SIZING[row]
    catalogue = mountings(settings)
    terrain = deployed.scenario.terrain
    incumbent = deployed.scenario.deployment.anchors
    radio = incumbent[0].radio
    xs = [a.ground_position_m[0] for a in incumbent]
    ys = [a.ground_position_m[1] for a in incumbent]
    west, east, south, north = min(xs), max(xs), min(ys), max(ys)

    def inside(x, y):
        return west <= x <= east and south <= y <= north

    priced = {}

    def cost_of(mounting):
        if mounting.kind not in priced:
            priced[mounting.kind] = lifecycle_tl(mounting, radio.part, rates,
                                                 settings)
        return priced[mounting.kind]

    out: list[Candidate] = []

    buildings = getattr(site, "buildings", None)
    built = buildings is not None and not buildings.is_empty

    def add(x, y, mounting, origin):
        if not inside(x, y):
            return
        # A column, a sign or a mast stands in the street, not inside a
        # building. The ground reports the roof inside a footprint
        # (ADR-0038), so a street structure there would be given the
        # building's height for free. Over Kızılay that is 21 of 304
        # road points and 7 of 120 fetched structures.
        if (origin != "rooftop" and built
                and buildings.tallest_at(float(x), float(y)) > 0.0):
            return
        identifier = "{}{}".format(origin[0].upper(), len(out))
        out.append(Candidate(
            Anchor(identifier, (float(x), float(y)), mounting, terrain,
                   radio=radio),
            origin, cost_of(mounting)))

    # The grid itself, so the search can always do at least as well.
    for anchor in incumbent:
        out.append(Candidate(replace(anchor), "grid", cost_of(anchor.mounting)))
    grid = tuple(range(len(out)))

    furniture = getattr(site, "furniture", None)
    if furniture is not None:
        for x, y, kind in zip(furniture.x_m, furniture.y_m, furniture.kind):
            key = FURNITURE_MOUNTING.get(kind)
            if key is not None:
                add(x, y, catalogue[key], "furniture")

    if built:
        # Only roofs whose height somebody measured. A footprint with no
        # height tag gets the fetch's default, and a roof at an invented
        # height is not a place that is already high: over Polatlı that
        # is all but twelve of 20899 buildings. A building tagged at
        # exactly the default is dropped with them, which errs towards
        # fewer roofs.
        tall = [
            (float(x), float(y), float(h))
            for x, y, h in zip(buildings.centre_x_m, buildings.centre_y_m,
                               buildings.height_m)
            if h >= sizing["roof_min_m"] and h != DEFAULT_BUILDING_HEIGHT_M
        ]
        tall.sort(key=lambda b: -(site.height_at(b[0], b[1]) + b[2]))
        for x, y, _ in _thinned(tall, sizing["roof_step_m"]):
            add(x, y, catalogue["rooftop"], "rooftop")

    for x, y in _high_points(site, sizing["hill_window_m"], sizing["hills"]):
        add(x, y, catalogue["tall_mast"], "hilltop")

    road = catalogue[sizing["road_mounting"]]
    for x, y in _thinned(_along_roads(site.roads_m, 50.0),
                         sizing["road_step_m"]):
        add(x, y, road, "road")

    return out, grid


# --- Coverage -------------------------------------------------------------


def demand_cells(deployed, cell_m: float) -> np.ndarray:
    """The lattice of places a receiver may be, over the grid's own area."""
    anchors = deployed.scenario.deployment.anchors
    xs = [a.ground_position_m[0] for a in anchors]
    ys = [a.ground_position_m[1] for a in anchors]
    gx = np.arange(min(xs) + cell_m / 2, max(xs), cell_m)
    gy = np.arange(min(ys) + cell_m / 2, max(ys), cell_m)
    return np.array([(x, y) for y in gy for x in gx], dtype=float)


def _reach_rows(task) -> np.ndarray:
    """Which cells each of a chunk of candidates ranges to.

    Top level so a worker process can import it. The test is the one
    `evaluate.coverage` applies to every swept cell.
    """
    anchors, deployment, terrain, cells, reach_m = task
    radios = _sweep_radios(deployment)
    rows = np.zeros((len(anchors), len(cells)), dtype=bool)
    grounds = np.array([terrain.height_at(float(x), float(y))
                        for x, y in cells])
    for c, anchor in enumerate(anchors):
        transmitter = Terminal(anchor.radio, deployment.antenna,
                               anchor.position_m)
        radio = audible(transmitter, radios)
        if radio is None:
            continue
        ax, ay, _ = transmitter.position_m
        near = np.hypot(cells[:, 0] - ax, cells[:, 1] - ay) <= reach_m
        for j in np.flatnonzero(near):
            here = (float(cells[j, 0]), float(cells[j, 1]),
                    float(grounds[j]) + RECEIVER_HEIGHT_M)
            if math.dist(transmitter.position_m, here) < 1.0:
                rows[c, j] = True
                continue
            receiver = Terminal(radio, deployment.antenna, here)
            budget = evaluate_link(
                transmitter, receiver,
                obstruction=terrain.obstruction_between(
                    transmitter.position_m, here),
                region=deployment.region,
            )
            rows[c, j] = budget.closes and (
                ranging_sigma_m(budget, transmitter.radio) <= TARGET_SIGMA_M)
    return rows


def problem(deployed, site, row: str, settings: Settings = DEFAULTS,
            processes: Optional[int] = None, watching=None) -> Problem:
    """Build the whole search problem for one row.

    ``watching`` is called with the share of candidates tested so far,
    as the reach matrix fills; it is the slow part.
    """
    from yerkon.parallel import spread, workers

    if row not in SIZING:
        raise ValueError("the placement search covers {}, not {!r}".format(
            " and ".join(SIZING), row))
    sizing = SIZING[row]
    found, grid = candidates(deployed, site, row, settings)
    cells = demand_cells(deployed, sizing["cell_m"])
    deployment = deployed.scenario.deployment
    terrain = deployed.scenario.terrain
    chunk = max(len(found) // (4 * workers(processes)), 1)
    tasks = [
        (tuple(c.anchor for c in found[at:at + chunk]), deployment, terrain,
         cells, sizing["reach_m"])
        for at in range(0, len(found), chunk)
    ]
    done = [0]

    def counted(rows):
        done[0] += len(rows)
        if watching is not None:
            watching(done[0] / len(found))

    reach = np.vstack(spread(_reach_rows, tasks, processes=processes,
                             watching=counted))
    return Problem(tuple(found), cells, reach, grid,
                   quarters(found, cells))


def quarters(found: Sequence[Candidate], cells: np.ndarray) -> np.ndarray:
    """Which quarter around each cell each candidate stands in."""
    at = np.array([c.anchor.ground_position_m for c in found], dtype=float)
    bearing = np.arctan2(at[:, None, 1] - cells[None, :, 1],
                         at[:, None, 0] - cells[None, :, 0])
    return (np.floor((bearing + math.pi / 4) / (math.pi / 2)) % 4).astype(
        np.int8)


# --- The choice -----------------------------------------------------------


class Cover:
    """What a set of chosen anchors gives every cell.

    A count is not enough. Four anchors strung along one street reach a
    cell four times and fix it badly, because every range to them runs
    the same way and the cross-street direction goes unmeasured: the
    first version of this search counted only, and the simulation put its
    ninety-fifth percentile at nearly twice the grid's (ADR-0081). So a
    cell is served when four chosen anchors reach it *and* they stand in
    at least three of the four quarters around it.

    Kept as counts per quarter, so adding or removing one anchor is one
    array update and every candidate can be tried against the current
    state at once.
    """

    def __init__(self, p: Problem, chosen: Sequence[int] = ()):
        self.reach = p.reach
        self.quarter = p.quarter
        cells = p.reach.shape[1]
        self._cells = np.arange(cells)
        self.by_quarter = np.zeros((cells, 4), dtype=np.int16)
        for i in chosen:
            self.change(i, +1)

    def change(self, i: int, sign: int) -> None:
        hit = self.reach[i]
        self.by_quarter[self._cells[hit], self.quarter[i, hit]] += sign

    @staticmethod
    def _served(count, quarters):
        return (count >= ANCHORS_REQUIRED) & (quarters >= QUARTERS_REQUIRED)

    @staticmethod
    def _progress(count, quarters):
        return (np.minimum(count, ANCHORS_REQUIRED)
                + np.minimum(quarters, QUARTERS_REQUIRED))

    def _state(self, by_quarter=None):
        by_quarter = self.by_quarter if by_quarter is None else by_quarter
        return by_quarter.sum(axis=1), (by_quarter > 0).sum(axis=1)

    def share(self, by_quarter=None) -> float:
        return float(self._served(*self._state(by_quarter)).mean())

    def _with(self, options: np.ndarray, by_quarter=None):
        """Count and quarters at every cell, with each option added."""
        by_quarter = self.by_quarter if by_quarter is None else by_quarter
        count, quarters = self._state(by_quarter)
        hit = self.reach[options]
        empty = by_quarter[self._cells[None, :], self.quarter[options]] == 0
        return (count[None, :] + hit,
                quarters[None, :] + (hit & empty)), (count, quarters)

    def gains(self, options: np.ndarray) -> np.ndarray:
        """How much nearer served the cells get with each option added."""
        (count, quarters), before = self._with(options)
        return (self._progress(count, quarters)
                - self._progress(*before)[None, :]).sum(axis=1)

    def shares_with(self, options: np.ndarray, by_quarter=None) -> np.ndarray:
        (count, quarters), _ = self._with(options, by_quarter)
        return self._served(count, quarters).mean(axis=1)

    def without(self, i: int) -> np.ndarray:
        """The per-quarter counts with anchor ``i`` taken out."""
        out = self.by_quarter.copy()
        hit = self.reach[i]
        out[self._cells[hit], self.quarter[i, hit]] -= 1
        return out


def _costs(p: Problem) -> np.ndarray:
    return np.array([c.lifecycle_tl for c in p.candidates])


def cheapest_cover(p: Problem, target_share: float) -> list[int]:
    """The least lifecycle cost that serves ``target_share`` of the cells.

    Greedy by progress per lira, then drop, then interchange.
    """
    costs = _costs(p)
    cover = Cover(p)
    chosen: list[int] = []
    free = np.ones(len(costs), dtype=bool)
    while cover.share() < target_share:
        options = np.flatnonzero(free)
        gain = cover.gains(options)
        if not options.size or gain.max() <= 0:
            break
        pick = int(options[np.argmax(gain / costs[options])])
        chosen.append(pick)
        free[pick] = False
        cover.change(pick, +1)
    return _cheapen(p, chosen, min(target_share, cover.share()), costs)


def _cheapen(p: Problem, chosen: list[int], goal: float,
             costs: np.ndarray) -> list[int]:
    """Drop what is not needed, then swap for cheaper while the cover holds."""
    chosen = list(chosen)
    cover = Cover(p, chosen)
    changed = True
    while changed:
        changed = False
        # Drop, the dearest first.
        for i in sorted(chosen, key=lambda k: -costs[k]):
            if cover.share(cover.without(i)) >= goal:
                chosen.remove(i)
                cover.change(i, -1)
                changed = True
        # Interchange (Teitz and Bart): each chosen anchor against every
        # cheaper one not chosen, taking the cheapest that keeps the cover.
        free = np.ones(len(costs), dtype=bool)
        free[chosen] = False
        for i in list(chosen):
            options = np.flatnonzero(free & (costs < costs[i] - 1e-6))
            if not options.size:
                continue
            shares = cover.shares_with(options, cover.without(i))
            fits = options[shares >= goal]
            if fits.size:
                j = int(fits[np.argmin(costs[fits])])
                chosen[chosen.index(i)] = j
                cover.change(i, -1)
                cover.change(j, +1)
                free[i], free[j] = True, False
                changed = True
    return chosen


def best_within(p: Problem, budget_tl: float) -> list[int]:
    """The most cover a lifecycle budget buys.

    Greedy by progress per lira while the budget lasts, then interchange:
    swap a chosen anchor for any other that raises the cover and still
    fits the budget.
    """
    costs = _costs(p)
    cover = Cover(p)
    chosen: list[int] = []
    spent = 0.0
    free = np.ones(len(costs), dtype=bool)
    while True:
        options = np.flatnonzero(free & (costs <= budget_tl - spent + 1e-6))
        if not options.size:
            break
        gain = cover.gains(options)
        if gain.max() <= 0:
            break
        pick = int(options[np.argmax(gain / costs[options])])
        chosen.append(pick)
        free[pick] = False
        spent += costs[pick]
        cover.change(pick, +1)
    changed = True
    while changed:
        changed = False
        for i in list(chosen):
            room = budget_tl - (spent - costs[i]) + 1e-6
            options = np.flatnonzero(free & (costs <= room))
            if not options.size:
                continue
            shares = cover.shares_with(options, cover.without(i))
            best = int(np.argmax(shares))
            if shares[best] > cover.share() + 1e-9:
                j = int(options[best])
                chosen[chosen.index(i)] = j
                cover.change(i, -1)
                cover.change(j, +1)
                free[i], free[j] = True, False
                spent += costs[j] - costs[i]
                changed = True
    return chosen


#: What a search can be asked for. "better" spends what the grid spends
#: and serves as much as it can; "cheaper" serves what the grid serves
#: for as little as it can.
AIMS = ("better", "cheaper")


@dataclass(frozen=True)
class Answer:
    """What a search chose, beside the grid it is read against."""

    problem: Problem
    aim: str
    chosen: tuple[int, ...]

    @property
    def share(self) -> float:
        return self.problem.share(self.chosen)

    @property
    def grid_share(self) -> float:
        return self.problem.share(self.problem.grid)

    @property
    def lifecycle_tl(self) -> float:
        return self.problem.cost(self.chosen)

    @property
    def grid_lifecycle_tl(self) -> float:
        return self.problem.cost(self.problem.grid)


def search(deployed, site, row: str, aim: str = "better",
           settings: Settings = DEFAULTS, processes: Optional[int] = None,
           watching=None) -> Answer:
    """Place this row's anchors by the search rather than on the grid."""
    if aim not in AIMS:
        raise ValueError("no aim called {!r}. There are: {}".format(
            aim, ", ".join(AIMS)))
    p = problem(deployed, site, row, settings, processes, watching)
    grid = list(p.grid)
    chosen = (best_within(p, p.cost(grid)) if aim == "better"
              else cheapest_cover(p, p.share(grid)))
    return Answer(p, aim, tuple(chosen))


# --- Putting the answer to the simulator ----------------------------------


def deployed_with(deployed, p: Problem, chosen: Sequence[int]):
    """The row, with its anchors replaced by the chosen ones.

    Everything else stays: the receivers, the journey, the round size,
    the seeds. The only thing that differs from the grid row is where the
    anchors stand and what they stand on.
    """
    anchors = tuple(
        replace(p.candidates[i].anchor, identifier="P{}".format(n))
        for n, i in enumerate(chosen)
    )
    scenario = deployed.scenario
    return replace(deployed, scenario=replace(
        scenario, deployment=replace(scenario.deployment, anchors=anchors)))


def mix(p: Problem, chosen: Sequence[int]) -> dict:
    """How many of the chosen anchors came from each kind of place."""
    out: dict = {}
    for i in chosen:
        origin = p.candidates[i].origin
        out[origin] = out.get(origin, 0) + 1
    return out
