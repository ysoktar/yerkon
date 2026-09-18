"""Where the anchors go, by one of several named methods.

Placing transmitters is an old problem with a literature, and this
module names the standard answers rather than inventing one. Three
families, because they answer different questions:

*Lattices* — a square grid, a hexagonal grid, a line along a corridor, a
ring round the edge. Geometry only: they read the site's shape and a
reach, and put anchors down. Fast, predictable, and the thing every real
deployment starts from. The hexagonal one is not a stylistic choice: a
triangular lattice is the fewest equal discs that cover a plane
(Kershner, 1939), and it is the model cellular planning has used for the
same reason since.

*Greedy searches* — from a set of candidate positions, add the one that
buys the most, repeat. This is the standard treatment of the Maximal
Covering Location Problem (Church and ReVelle, 1974): the exact problem
is NP-hard, and greedy is what planning tools actually run. What "buys
the most" means is the interesting part, and this module offers three
answers, because for a positioning network the obvious one is wrong.

*By hand* — none at all. The empty arrangement somebody builds from.

## Why coverage is the wrong score here, and what replaces it

A comms network wants signal everywhere. A positioning network wants
*geometry*: four anchors in a row give a receiver almost nothing across
the line, however loudly they arrive. The standard measure of that is
dilution of precision — how much anchor geometry amplifies the ranging
error — and it is why `greedy-dop` exists beside `greedy-coverage`.

The dilution here is computed for two unknowns, x and y, not the three
or four a GNSS receiver solves. Two-way ranging measures a distance
directly, so there is no clock offset in the state (ADR-0010), and the
vertical is not observable from a road at all (ADR-0011). So the
geometry matrix rows are the horizontal unit vectors to each anchor and
HDOP is `sqrt(trace((GᵀG)⁻¹))`, with no clock column.

## What a layout is allowed to know

A layout proposes; the simulation judges. These methods score candidates
against a *reach disc* — a radius the caller works out once from the
link budget — rather than running a link budget per candidate, because a
greedy pass over a few hundred candidates would otherwise be minutes and
the answer would still have to be checked by the real thing. Nothing
here decides a published number: `yerkon table` re-runs the arrangement
through the same budget, terrain and estimator as every other row
(ADR-0001), and that is the verdict.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np

#: The methods this module knows, in the order a chooser should offer
#: them: the cheap geometric ones first, then the ones that measure.
METHODS = (
    "grid",
    "hex",
    "corridor",
    "perimeter",
    "greedy-coverage",
    "greedy-dop",
    "k-cover",
    "manual",
)

#: How many anchors it takes before *dilution* means anything.
#:
#: Three, because `dilution_at` inverts a two-by-two geometry matrix:
#: two unknowns, x and y, since two-way ranging measures distance
#: directly and leaves no clock column (ADR-0010) and the vertical is
#: not observable from a road (ADR-0011). Two ranges put a receiver on
#: one of two points; three is the first count with a unique answer.
#:
#: This is a property of the arithmetic below it and not a policy. What
#: a *deployment* needs is the next constant, and conflating the two is
#: what made a search stop at three.
FEWEST_FOR_A_FIX = 3

#: How many anchors have to reach a place before it counts as served.
#:
#: Four, which is what the rest of this project already requires and
#: refuses to go below: `coverage()` and `siting.Requirement` both raise
#: "fewer than four ranges cannot place a point", and the published area
#: column is `area_reached_by(4)`. The estimator solves three unknowns
#: without a height constraint, so a fourth range is what makes the
#: system determined rather than exactly determined with nothing left
#: over to check it.
#:
#: The searches used `FEWEST_FOR_A_FIX` for this and it was wrong: a
#: search would declare itself finished at a count its own estimator
#: cannot produce a position from. On Kızılay that put four anchors in
#: the corners of the site, where no point saw all four, and the service
#: area came out at 0,08 km² against a lattice's 8,92 (ADR-0047).
ENOUGH_TO_BE_SERVED = 4

#: Dilution past which the geometry is reported as useless rather than
#: as a number. A horizontal dilution of twenty turns a 3 m range error
#: into 60 m, and beyond that the arithmetic stops being informative.
DILUTION_CEILING = 20.0


#: The methods that choose where to put an anchor by scoring candidates
#: against a reach disc, rather than laying one out on a lattice.
#:
#: Named here because what the disc should be differs: a lattice never
#: reads it, and a search treats it as a hard edge, so a search wants the
#: reach measured on the ground it is on rather than the open-ground
#: figure a ring is drawn from (ADR-0047).
SEARCHES = ("greedy-coverage", "greedy-dop", "k-cover")


@dataclass(frozen=True)
class Spot:
    """One place an anchor stands, and what it is bolted to.

    The mounting travels with the position because a layout that puts
    anchors on lighting columns and one that builds masts are different
    deployments at the same coordinates, and the costing reads the
    difference (ADR-0015).
    """

    x_m: float
    y_m: float
    mounting: str = ""


@dataclass(frozen=True)
class Ground:
    """What a layout may read about the place it is filling.

    Deliberately small. A layout gets the shape of the site, the route
    through it, a reach to work with, and whatever structures already
    stand there; it does not get the terrain object, the link budget or
    the settings, because a method that reached for those would be doing
    physics the engine does properly a moment later.
    """

    length_m: float
    width_m: float = 0.0
    reach_m: float = 1000.0
    #: The route a receiver takes, as (x, y) in local metres. Empty over
    #: an area with no road drawn yet.
    route: Sequence[tuple[float, float]] = ()
    #: Structures already standing: lighting columns, sign gantries,
    #: roadside signs. Empty until a fetch brings road furniture, which
    #: is why the methods that need it say so rather than inventing it.
    furniture: Sequence[Spot] = ()

    @property
    def is_a_line(self) -> bool:
        """A corridor rather than an area. Width decides, not length."""
        return self.width_m <= 0.0


@dataclass(frozen=True)
class Plan:
    """Which method, and the figures it reads.

    One record for every method rather than one per method, because the
    viewer switches between them on a dropdown and a person who has set
    a spacing expects it to still be there when they come back.
    """

    method: str = "grid"
    spacing_m: float = 2000.0
    #: Distance from the route, for the methods that follow one.
    offset_m: float = 0.0
    #: How far alternate rows shift along, for the square lattice. A
    #: perfect grid puts every anchor a receiver can see on one of two
    #: lines through it, which is worse geometry than anything anybody
    #: would build.
    stagger_m: float = 0.0
    #: Ceiling on how many anchors a greedy method may place. The
    #: searches stop when adding one buys nothing, so this is a budget
    #: rather than a target.
    most: int = 60
    #: How many anchors `k-cover` insists reach every cell.
    cover_k: int = ENOUGH_TO_BE_SERVED
    #: The dilution `greedy-dop` stops at.
    #:
    #: Cheapest that meets, not best — the rule this project already
    #: settled for its other searches (ADR-0015, ADR-0023). Without a bar
    #: to clear, a search scored on a continuous quality returns the
    #: densest arrangement it was offered, because one more anchor always
    #: helps a little. Two is the figure GNSS practice calls good
    #: geometry, and it means a 3 m range error lands as about 6 m of
    #: position.
    target_dop: float = 2.0
    mounting: str = "mast"

    def with_method(self, method: str) -> "Plan":
        from dataclasses import replace

        return replace(self, method=method)


def place(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """Anchors for this plan on this ground. The whole interface.

    Every method is reached through here, so a caller learns one
    function and the viewer's dropdown is a string. Adding a method is a
    function and a name in `METHODS`; no caller changes.
    """
    method = plan.method or "grid"
    if method not in METHODS:
        raise ValueError(
            "no placement called {!r}. There are: {}".format(
                method, ", ".join(METHODS)
            )
        )
    return _METHODS[method](plan, ground)


# --- Lattices -------------------------------------------------------------


def _grid(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """A square lattice, with alternate rows shifted along.

    What this project shipped before there was a choice, kept as the
    baseline every other method is read against.
    """
    if ground.is_a_line:
        return _corridor(plan, ground)
    spacing = max(plan.spacing_m, 25.0)
    out = []
    for row, y in enumerate(np.arange(0.0, ground.width_m + 1.0, spacing)):
        shift = plan.stagger_m if row % 2 else 0.0
        for x in np.arange(0.0, ground.length_m + 1.0, spacing):
            out.append(Spot(float(x) + shift, float(y) + plan.offset_m,
                            plan.mounting))
    return tuple(_inside(out, ground))


def _hex(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """A triangular lattice: rows a half-spacing apart, √3/2 between them.

    The fewest equal discs that cover a plane (Kershner, 1939), and the
    lattice cellular planning is drawn on for that reason. Against a
    square grid of the same spacing it puts about fifteen per cent fewer
    anchors on the same ground, and every point has three anchors at
    similar range rather than two.
    """
    if ground.is_a_line:
        return _corridor(plan, ground)
    spacing = max(plan.spacing_m, 25.0)
    between = spacing * math.sqrt(3.0) / 2.0
    out = []
    for row, y in enumerate(np.arange(0.0, ground.width_m + 1.0, between)):
        shift = spacing / 2.0 if row % 2 else 0.0
        for x in np.arange(0.0, ground.length_m + 1.0, spacing):
            out.append(Spot(float(x) + shift, float(y) + plan.offset_m,
                            plan.mounting))
    return tuple(_inside(out, ground))


def _corridor(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """Along the route, alternating sides.

    Alternating rather than one side throughout, because a line of
    anchors all to the left of a road leaves the cross-track direction
    barely observable — which is the geometry ADR-0011 is about.
    """
    spacing = max(plan.spacing_m, 25.0)
    offset = plan.offset_m or 0.0
    if ground.route:
        spots = []
        for index, (x, y) in enumerate(_along(ground.route, spacing)):
            side = offset if index % 2 == 0 else -offset
            spots.append(Spot(x, y + side, plan.mounting))
        return tuple(_inside(spots, ground))
    return tuple(
        Spot(float(x), offset if index % 2 == 0 else -offset, plan.mounting)
        for index, x in enumerate(
            np.arange(0.0, ground.length_m + 1.0, spacing))
    )


def _perimeter(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """A ring round the edge of the site.

    Worth having as a method rather than as a curiosity: it is what a
    deployment that may not build in the middle of an area looks like,
    and it is the arrangement with the worst dilution in the centre, so
    it makes the point that coverage and geometry are different things.
    """
    if ground.is_a_line:
        return _corridor(plan, ground)
    spacing = max(plan.spacing_m, 25.0)
    inset = plan.offset_m
    left, right = inset, max(ground.length_m - inset, inset)
    bottom, top = inset, max(ground.width_m - inset, inset)
    out = []
    for x in np.arange(left, right + 1.0, spacing):
        out.append(Spot(float(x), bottom, plan.mounting))
        out.append(Spot(float(x), top, plan.mounting))
    for y in np.arange(bottom + spacing, top, spacing):
        out.append(Spot(left, float(y), plan.mounting))
        out.append(Spot(right, float(y), plan.mounting))
    return tuple(_inside(out, ground))


def _manual(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """None. The empty arrangement somebody builds by hand."""
    return ()


# --- Greedy searches ------------------------------------------------------


def _greedy_coverage(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """Add the candidate that newly covers the most ground, and repeat.

    The Maximal Covering Location Problem's greedy, which is what radio
    planning tools run because the exact problem is NP-hard. Correct for
    a network that wants signal everywhere, and *wrong here* — it is
    offered so the difference against `greedy-dop` can be measured
    rather than asserted.
    """
    cells, candidates = _field(plan, ground)
    if not len(candidates):
        return ()
    reach = max(ground.reach_m, 1.0)
    covered = np.zeros(len(cells), dtype=bool)
    chosen: list[int] = []

    for _ in range(max(plan.most, 0)):
        best, gain = -1, 0
        for index in range(len(candidates)):
            if index in chosen:
                continue
            within = _within(cells, candidates[index], reach)
            new = int(np.count_nonzero(within & ~covered))
            if new > gain:
                best, gain = index, new
        if best < 0:
            break
        chosen.append(best)
        covered |= _within(cells, candidates[best], reach)
        if covered.all():
            break
    return tuple(_spot(candidates[index], plan, ground) for index in chosen)


def _greedy_dop(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """Add the candidate that most improves the worst dilution, and repeat.

    The score is the mean horizontal dilution over the cells, counting a
    cell with too few anchors in reach at the ceiling. That makes the
    first few picks behave like coverage — a cell nobody reaches is the
    worst cell there is — and the later ones behave like geometry, which
    is the order a person would place them in anyway.
    """
    cells, candidates = _field(plan, ground)
    if not len(candidates):
        return ()
    reach = max(ground.reach_m, 1.0)
    chosen: list[int] = []
    standing = np.zeros((0, 2))
    score = _fixable_then_dilution(cells, standing, reach)

    for _ in range(max(plan.most, 0)):
        short, dilution = score
        if short == 0 and dilution <= plan.target_dop:
            break
        best, best_score = -1, score
        for index in range(len(candidates)):
            if index in chosen:
                continue
            tried = np.vstack([standing, candidates[index][None, :]])
            here = _fixable_then_dilution(cells, tried, reach)
            if here < best_score:
                best, best_score = index, here
        if best < 0:
            break
        chosen.append(best)
        standing = np.vstack([standing, candidates[best][None, :]])
        score = best_score
    return tuple(_spot(candidates[index], plan, ground) for index in chosen)


def _seen_and_dilution(cells: np.ndarray, anchors: np.ndarray,
                       reach_m: float) -> tuple[np.ndarray, np.ndarray]:
    """How many anchors reach each cell, and the dilution there.

    Vectorised over every cell and anchor at once, because the loop this
    replaces took twenty-two seconds for one press of a dropdown. The
    2x2 inverse has a closed form, so there is no matrix to invert per
    cell: with G the unit vectors to the anchors in reach, GᵀG is
    [[a, b], [b, c]] and trace of its inverse is (a + c) / (ac - b²).

    Dilution comes back as the ceiling where fewer than three anchors
    reach, or where the geometry is singular — anchors in a straight
    line through the cell, which is exactly the arrangement a road
    produces and the reason this measure is here at all (ADR-0011).
    """
    if not len(anchors):
        return (np.zeros(len(cells), dtype=int),
                np.full(len(cells), DILUTION_CEILING))

    dx = anchors[None, :, 0] - cells[:, None, 0]
    dy = anchors[None, :, 1] - cells[:, None, 1]
    ranges = np.hypot(dx, dy)
    near = (ranges <= reach_m) & (ranges > 1e-6)
    seen = near.sum(axis=1)

    safe = np.where(near, ranges, 1.0)
    ux = np.where(near, dx / safe, 0.0)
    uy = np.where(near, dy / safe, 0.0)
    a = (ux * ux).sum(axis=1)
    b = (ux * uy).sum(axis=1)
    c = (uy * uy).sum(axis=1)

    determinant = a * c - b * b
    enough = (seen >= FEWEST_FOR_A_FIX) & (determinant > 1e-12)
    dilution = np.full(len(cells), DILUTION_CEILING)
    with np.errstate(invalid="ignore", divide="ignore"):
        value = np.sqrt(np.where(enough, (a + c) / np.where(
            determinant > 1e-12, determinant, 1.0), DILUTION_CEILING ** 2))
    dilution = np.where(enough, np.minimum(value, DILUTION_CEILING),
                        DILUTION_CEILING)
    return seen, dilution


def _fixable_then_dilution(cells: np.ndarray, anchors: np.ndarray,
                           reach_m: float) -> tuple[int, float]:
    """How many anchor-sightings the site is still short of, then how good
    the geometry is where it has enough.

    Ordered rather than blended, because the two are not commensurable
    and any weighting between them would be a number nobody could
    defend.

    The shortfall is counted in sightings rather than in cells — the sum
    over cells of how many more anchors each still needs — and that is
    what makes the search start. Dilution is undefined until three
    anchors reach a cell, and "cells that can be fixed" is zero until
    four overlap, so either of those alone would rate the first picks
    identically and the search would stop before it began. Sightings
    fall with the very first anchor, and once nothing is short the
    dilution takes over.

    What counts as "not short" is `ENOUGH_TO_BE_SERVED`, which is four:
    the number the published area column counts and the number this
    project refuses to go below elsewhere. It used to be three — the
    minimum for the dilution arithmetic — and a search that stopped
    there stopped at a count its own estimator cannot fix from
    (ADR-0047).
    """
    seen, dilution = _seen_and_dilution(cells, anchors, reach_m)
    short = int(np.maximum(ENOUGH_TO_BE_SERVED - seen, 0).sum())
    enough = seen >= ENOUGH_TO_BE_SERVED
    mean = float(dilution[enough].mean()) if enough.any() else DILUTION_CEILING
    return short, mean


@dataclass(frozen=True)
class Bar:
    """What a search was asked to clear, and where it stopped.

    A search stops for one of three reasons: it cleared its bar, it ran
    out of budget, or no candidate left would help. Only the first is a
    result, and from the outside all three look the same. Over Kızılay,
    a dilution target of two cannot be met with a measured reach of
    478 m, so the search ran until it had bolted an anchor to every one
    of the 232 mountable structures on the site and reported them the
    way it reports an arrangement that worked (ADR-0056).

    Worked out from the spots rather than reported by the search itself,
    so that `place` keeps the one signature every method shares
    (ADR-0040) and a hand-edited arrangement can be asked the same
    question as a searched one.
    """

    #: Which quantity the bar is on, as a key the page names.
    name: str
    wanted: float
    got: float
    met: bool
    #: Whether it placed every anchor it was allowed. A search that hit
    #: its budget may clear the bar with a larger one; a search that ran
    #: out of candidates will not.
    spent_the_budget: bool
    #: Anchor sightings the site is still short of, where that applies.
    #: Above zero means somewhere cannot be fixed at all, which is a
    #: different failure from geometry that is merely poor.
    short: int = 0


def bar_of(plan: Plan, ground: Ground,
           spots: Sequence[Spot]) -> Optional[Bar]:
    """Whether this arrangement clears what its method was asked for.

    Nothing for a method that carries no bar. A lattice is a spacing
    rather than a target, and asking whether a grid "met" anything would
    invent a claim it never made.
    """
    if plan.method not in SEARCHES:
        return None

    cells, _ = _field(plan, ground)
    standing = (
        np.array([[spot.x_m, spot.y_m] for spot in spots], dtype=float)
        if len(spots) else np.zeros((0, 2))
    )
    reach = max(ground.reach_m, 1.0)
    spent = len(spots) >= max(int(plan.most), 0)
    if not len(cells):
        return Bar(name="cells", wanted=1.0, got=0.0, met=False,
                   spent_the_budget=spent)

    if plan.method == "greedy-dop":
        short, dilution = _fixable_then_dilution(cells, standing, reach)
        return Bar(
            name="dilution", wanted=float(plan.target_dop),
            got=float(dilution),
            met=short == 0 and dilution <= plan.target_dop,
            spent_the_budget=spent, short=short,
        )

    # Counted the way the methods that carry this bar count, which is
    # not the way the dilution arithmetic counts. `_seen_and_dilution`
    # drops an anchor sitting exactly on a cell centre, because the unit
    # vector to it is undefined; for "how many anchors are in reach" it
    # is plainly one of them, and using the geometry count here made the
    # bar disagree with the search by one anchor at every candidate that
    # happened to land on a cell centre.
    seen = np.zeros(len(cells), dtype=int)
    for point in standing:
        seen += _within(cells, point, reach).astype(int)

    if plan.method == "k-cover":
        wanted = float(max(int(plan.cover_k), 1))
        fewest = float(seen.min()) if len(seen) else 0.0
        return Bar(
            name="anchors_in_reach", wanted=wanted, got=fewest,
            met=fewest >= wanted, spent_the_budget=spent,
            short=int(np.maximum(wanted - seen, 0).sum()),
        )

    # greedy-coverage asks only that a packet arrives, which is one
    # anchor and not four: it is the communications question and this
    # project keeps it to measure the difference (ADR-0040).
    reached = float(np.count_nonzero(seen >= 1)) / float(len(cells))
    return Bar(
        name="covered_share", wanted=1.0, got=reached,
        met=reached >= 1.0 - 1e-9, spent_the_budget=spent,
        short=int(np.count_nonzero(seen < 1)),
    )


def dilution_field(cells: np.ndarray, anchors: Sequence[tuple],
                   reach_m: float) -> np.ndarray:
    """Dilution at every one of these points. What the map colours by."""
    return _seen_and_dilution(
        np.asarray(cells, dtype=float),
        np.array([[a[0], a[1]] for a in anchors], dtype=float).reshape(-1, 2),
        reach_m,
    )[1]


def dilution_at(point: tuple[float, float], anchors: Sequence[tuple],
                reach_m: float) -> float:
    """Horizontal dilution of precision at one point.

    Returns the ceiling where too few anchors reach, so a caller drawing
    a field of these gets a number everywhere rather than holes.
    """
    return float(dilution_field([point], anchors, reach_m)[0])


def _k_cover(plan: Plan, ground: Ground) -> tuple[Spot, ...]:
    """Add until every cell has k anchors in reach.

    Set cover for k rather than for one, because a position needs three
    ranges before it has a unique answer and four before it has any
    redundancy. Stops early when nothing left to add raises the count of
    the cells still short, which is what "the site cannot be covered
    with this reach" looks like.
    """
    cells, candidates = _field(plan, ground)
    if not len(candidates):
        return ()
    reach = max(ground.reach_m, 1.0)
    wanted = max(int(plan.cover_k), 1)
    counts = np.zeros(len(cells), dtype=int)
    chosen: list[int] = []

    for _ in range(max(plan.most, 0)):
        short = counts < wanted
        if not short.any():
            break
        best, gain = -1, 0
        for index in range(len(candidates)):
            if index in chosen:
                continue
            helps = int(np.count_nonzero(
                _within(cells, candidates[index], reach) & short))
            if helps > gain:
                best, gain = index, helps
        if best < 0:
            break
        chosen.append(best)
        counts += _within(cells, candidates[best], reach).astype(int)
    return tuple(_spot(candidates[index], plan, ground) for index in chosen)


# --- The field the searches work over -------------------------------------

#: How many cells a greedy pass scores against, and how many positions it
#: may choose from. Both are deliberately coarse: this is a proposal that
#: the real simulation re-runs, and a person waiting on a dropdown will
#: not wait thirty seconds for a better guess.
CELLS_ACROSS = 24
CANDIDATES_ACROSS = 12


def _field(plan: Plan, ground: Ground) -> tuple[np.ndarray, np.ndarray]:
    """The cells to serve and the positions that may serve them.

    Candidates come from the road furniture where a fetch brought any,
    because an anchor on a structure that already stands costs the
    structure nothing (ADR-0015), and from a coarse lattice over the site
    where it did not.
    """
    length = max(ground.length_m, 1.0)
    width = max(ground.width_m, length / 10.0)
    xs = np.linspace(0.0, length, CELLS_ACROSS)
    ys = np.linspace(0.0, width, max(int(CELLS_ACROSS * width / length), 2))
    grid_x, grid_y = np.meshgrid(xs, ys)
    cells = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    if ground.furniture:
        candidates = np.array(
            [[spot.x_m, spot.y_m] for spot in ground.furniture], dtype=float)
        return cells, candidates

    if ground.is_a_line and ground.route:
        along = _along(ground.route, max(length / CANDIDATES_ACROSS, 25.0))
        return cells, np.array(along, dtype=float)

    cx = np.linspace(0.0, length, CANDIDATES_ACROSS)
    cy = np.linspace(0.0, width, max(int(CANDIDATES_ACROSS * width / length), 2))
    mesh_x, mesh_y = np.meshgrid(cx, cy)
    return cells, np.column_stack([mesh_x.ravel(), mesh_y.ravel()])


def _within(cells: np.ndarray, at: np.ndarray, reach_m: float) -> np.ndarray:
    return ((cells[:, 0] - at[0]) ** 2
            + (cells[:, 1] - at[1]) ** 2) <= reach_m ** 2


# --- Small shared pieces --------------------------------------------------


def _along(route: Sequence[tuple[float, float]],
           spacing_m: float) -> list[tuple[float, float]]:
    """Points every `spacing_m` along a polyline.

    By arc length rather than by vertex, because a route's vertices are
    wherever it happened to turn and a spacing measured in vertices is a
    spacing in nothing.
    """
    if len(route) < 2:
        return [tuple(point) for point in route]
    out = [(float(route[0][0]), float(route[0][1]))]
    carried = 0.0
    for (x0, y0), (x1, y1) in zip(route, route[1:]):
        leg = math.dist((x0, y0), (x1, y1))
        if leg <= 0.0:
            continue
        walked = spacing_m - carried
        while walked <= leg:
            share = walked / leg
            out.append((x0 + (x1 - x0) * share, y0 + (y1 - y0) * share))
            walked += spacing_m
        carried = (carried + leg) % spacing_m
    return out


def _inside(spots: Sequence[Spot], ground: Ground) -> list[Spot]:
    """Anything past the site's edge stands on ground nobody measured."""
    if ground.is_a_line:
        return [spot for spot in spots if 0.0 <= spot.x_m <= ground.length_m]
    return [
        spot for spot in spots
        if 0.0 <= spot.x_m <= ground.length_m
        and 0.0 <= spot.y_m <= ground.width_m
    ]


def _spot(at: np.ndarray, plan: Plan, ground: Ground) -> Spot:
    """A chosen candidate as a Spot, keeping the structure it stands on."""
    for standing in ground.furniture:
        if abs(standing.x_m - at[0]) < 1e-6 and abs(standing.y_m - at[1]) < 1e-6:
            return standing
    return Spot(float(at[0]), float(at[1]), plan.mounting)


_METHODS: dict = {
    "grid": _grid,
    "hex": _hex,
    "corridor": _corridor,
    "perimeter": _perimeter,
    "greedy-coverage": _greedy_coverage,
    "greedy-dop": _greedy_dop,
    "k-cover": _k_cover,
    "manual": _manual,
}
