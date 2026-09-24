"""Where a receiver drives, and why one route is not the same as another.

A journey used to be one shape per tab: a straight line down a corridor,
a circuit round an area. Every unit followed it, differing only in where
it started and how fast it went. That is one arrangement, not a choice,
and it quietly decides something the table reports — a route that only
ever runs east is a route whose cross-track geometry never changes, and
on a corridor that is the difference between a deployment that looks
adequate and one that is (ADR-0011).

The same seam as `layout`: the whole interface is `trace(trip, course)`,
which hands back a centreline in local metres. Adding a route is a
function and a name; no caller changes, and the viewer's chooser is a
string it got from the engine.

The shapes are the ones this field already uses. A **figure of eight**
is what inertial and GNSS receivers are driven through on test, because
it takes the vehicle round every heading. A **lawnmower** — boustrophedon
— is the standard survey pattern for covering an area evenly rather than
round its edge. **Random waypoint** is the mobility model from Johnson
and Maltz (1996) that mobile networking has used ever since. **Out and
back** is how a survey vehicle actually drives a corridor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

#: Every route, by name. The viewer's chooser is this list.
METHODS = (
    "line",
    "out-and-back",
    "circuit",
    "figure-eight",
    "lawnmower",
    "waypoints",
    "road",
)

#: Routes that need the site to have width. On a corridor they fall back,
#: the same way an area layout falls back to a corridor (ADR-0040).
NEED_WIDTH = ("circuit", "figure-eight", "lawnmower", "waypoints")

#: How far in from the edge a route runs by default, as a fraction of the
#: shorter side. Nothing drives along the boundary fence.
INSET_SHARE = 0.1


@dataclass(frozen=True)
class Course:
    """The ground a journey runs over.

    `road`, where a fetch brought real road geometry, is the actual
    carriageway; the `road` method needs it and the others ignore it. It
    is empty until a fetch brings one, and the viewer greys that method
    until it is not — a control that does nothing is not a control
    (ADR-0036).
    """

    length_m: float
    width_m: float
    #: The real road network in local metres: one polyline per segment,
    #: as the fetch found them. A network rather than a path — Kızılay's
    #: three kilometres square hold 1 638 segments, split at every
    #: junction — so the `road` route has to make a drivable path out of
    #: it rather than drive the list.
    road: Sequence[Sequence[tuple[float, float]]] = ()

    @property
    def is_a_line(self) -> bool:
        return self.width_m <= 0.0

    @property
    def inset_m(self) -> float:
        """How far in from the edge a route runs. Nothing on a corridor,
        which has no width to come in from."""
        if self.is_a_line:
            return 0.0
        return min(self.length_m, self.width_m) * INSET_SHARE


def area_step_m(length_m: float, width_m: float) -> float:
    """How finely a site's own route is sampled.

    Fine enough to be a shape, coarse enough that a forty kilometre site
    is not ten thousand points: 500 m down a corridor, a twentieth of the
    shorter side over an area. The table's rows and the simulator's tabs
    both ask this, so the road a row publishes and the road its tab
    drives are the same road (ADR-0084).
    """
    if width_m <= 0.0:
        return 500.0
    return max(min(length_m, width_m) / 20.0, 50.0)


@dataclass(frozen=True)
class Trip:
    """What route to drive, and the handful of figures that shape it."""

    method: str = "line"
    #: How finely the centreline is sampled. It is a polyline, and the
    #: journey reads positions off it by distance.
    step_m: float = 200.0
    #: Passes across the site, for the lawnmower.
    passes: int = 4
    #: Waypoints to visit, for the random model.
    stops: int = 8
    #: Which random walk. Named so the same figure comes back twice.
    seed: int = 1


def trace(trip: Trip, course: Course) -> tuple[tuple[float, float], ...]:
    """The centreline of this route over this ground.

    Points in local metres, never fewer than two, and never outside the
    site: a receiver on ground nobody measured is being scored against
    the boundary row extruded into a plane (ADR-0037).
    """
    method = trip.method
    if method not in METHODS:
        raise ValueError(
            "no route called {!r}. There are: {}".format(
                method, ", ".join(METHODS))
        )
    if method == "road" and not course.road:
        raise ValueError(
            "the real road is not on this ground. Fetch a place with road "
            "geometry, or pick another route."
        )
    # An area route over a corridor is a line, so it says so by being
    # one. Out and back rather than a plain line, because it is the
    # richest thing a corridor allows and the fallback should not throw
    # away what the person asked for more than it has to.
    if method in NEED_WIDTH and course.is_a_line:
        method = "out-and-back"

    drawn = _SHAPES[method](trip, course)
    kept = _inside(drawn, course)
    if len(kept) < 2:
        raise ValueError("a route needs at least two points")
    return kept


# --- The shapes -----------------------------------------------------------


def _line(trip: Trip, course: Course):
    """Straight down the corridor. What a corridor is."""
    return _along([(0.0, 0.0), (course.length_m, 0.0)], trip.step_m)


def _out_and_back(trip: Trip, course: Course):
    """Down and back again.

    How a survey vehicle actually drives a corridor, and it is not the
    same journey twice: every point is observed once heading each way, so
    a bias that depends on which side the anchors are on shows up instead
    of averaging into the answer.
    """
    end = course.length_m
    return _along([(0.0, 0.0), (end, 0.0), (0.0, 0.0)], trip.step_m)


def _circuit(trip: Trip, course: Course):
    """Round the edge and across the middle.

    A vehicle in a town turns. A journey that only ever runs east is a
    journey whose cross-track geometry never changes, and it would make
    an area deployment look like a corridor.
    """
    inset = course.inset_m
    left, right = inset, course.length_m - inset
    bottom, top = inset, course.width_m - inset
    return _along([
        (left, bottom), (right, bottom), (right, top), (left, top),
        (left, bottom), (right, top),
    ], trip.step_m)


def _figure_eight(trip: Trip, course: Course):
    """The pattern receivers are driven through on test.

    It crosses itself, so the vehicle passes every heading — which is
    what makes it the standard shape for shaking out a positioning error
    that depends on geometry rather than on distance. A loop in one
    direction never turns the other way and can hide exactly that.

    Drawn as a lemniscate rather than as two joined circles, because the
    curvature is continuous and a real vehicle's is too.
    """
    inset = course.inset_m
    half_x = (course.length_m - 2 * inset) / 2.0
    half_y = (course.width_m - 2 * inset) / 2.0
    middle = (course.length_m / 2.0, course.width_m / 2.0)
    # Enough samples that the step is about what was asked for, measured
    # against the loop's rough circumference.
    around = max(int(2 * math.pi * max(half_x, half_y) / max(trip.step_m, 1.0)),
                 24)
    turns = np.linspace(0.0, 2 * math.pi, around, endpoint=True)
    # `sin(t)cos(t)` is `sin(2t)/2`, so written the obvious way the loop
    # uses half the width it was given. Doubled, it fills the ground.
    return tuple(
        (middle[0] + half_x * math.sin(t),
         middle[1] + half_y * math.sin(2.0 * t))
        for t in turns
    )


def _lawnmower(trip: Trip, course: Course):
    """Parallel passes with a turn at each end. Boustrophedon.

    The standard survey pattern, and the one that samples an area evenly
    instead of round its edge: a circuit tells you about the boundary and
    the middle and nothing about the ground between them.
    """
    inset = course.inset_m
    left, right = inset, course.length_m - inset
    bottom, top = inset, course.width_m - inset
    passes = max(int(trip.passes), 2)
    lanes = np.linspace(bottom, top, passes)

    corners = []
    for index, y in enumerate(lanes):
        near, far = (left, right) if index % 2 == 0 else (right, left)
        corners.append((near, float(y)))
        corners.append((far, float(y)))
    return _along(corners, trip.step_m)


def _waypoints(trip: Trip, course: Course):
    """Random waypoint: go somewhere, then somewhere else.

    Johnson and Maltz (1996), and the model mobile networking has used
    ever since. Seeded, so the same journey comes back twice.

    Its faults are published and worth naming, because this is a model
    and not a measurement. Waypoints drawn uniformly put a vehicle in the
    middle of the site far more often than at its edges, and the average
    speed of a random-waypoint walk decays over time unless the speed is
    bounded away from zero — Yoon, Liu and Noble, *Random waypoint
    considered harmful* (2003). The speed here comes from the unit rather
    than from the model, which avoids the second; the first is real and
    this route over-samples the middle.
    """
    inset = course.inset_m
    rng = np.random.default_rng(trip.seed)
    stops = max(int(trip.stops), 2)
    xs = rng.uniform(inset, course.length_m - inset, stops)
    ys = rng.uniform(inset, course.width_m - inset, stops)
    return _along([(float(x), float(y)) for x, y in zip(xs, ys)], trip.step_m)


def _road(trip: Trip, course: Course):
    """The carriageway a fetch actually brought.

    The only route here that is a measurement rather than a shape. Every
    other one is a pattern somebody would drive; this is where the road
    goes.

    What arrives is a network, not a path: a road is split at every
    junction, so Kızılay is 1 638 segments and driving the list in the
    order it was stored would teleport a vehicle between roads that do
    not meet. This walks the network instead — joining segments that
    share an end — and drives the longest continuous run it can find.

    Segments are first cut to the site, because a segment whose box
    overlaps the site can run a long way past it and nothing drives on
    ground nobody measured (ADR-0037). Cut rather than clamped: a road
    pulled back to the boundary is a road that bends where it does not.
    """
    pieces = []
    for line in course.road:
        pieces.extend(_within(line, course))
    if not pieces:
        raise ValueError(
            "the road this ground carries does not run inside the site. "
            "Widen the site, or pick another route."
        )
    return _along(_longest_run(pieces), trip.step_m)


def drivable(course: Course) -> bool:
    """Whether the `road` route can actually be made on this ground.

    Carrying a road network is not the same as having one to drive: the
    tunnel row's fetch brought four segments and none of them runs inside
    its two-kilometre corridor. The page asks this rather than asking
    whether the network is empty, because a method offered and then
    refused is the control that looks live and does nothing (ADR-0036).

    Cheap on purpose — it asks whether any segment has two points on the
    site, and does not walk the network to find the longest path.
    """
    return any(_within(line, course) for line in course.road)


def _within(line, course: Course):
    """The runs of this line that are on the site, as separate pieces."""
    top = max(course.width_m, 0.0)
    out, run = [], []
    for x, y in line:
        if 0.0 <= x <= course.length_m and 0.0 <= y <= top:
            run.append((float(x), float(y)))
        else:
            if len(run) >= 2:
                out.append(run)
            run = []
    if len(run) >= 2:
        out.append(run)
    return out


def _longest_run(pieces, join_m: float = 1.0):
    """The longest drivable path through these segments.

    Greedy: start from the longest piece and keep extending whichever end
    can be extended, by any segment that begins or finishes where this
    one does. Greedy rather than exhaustive because the longest path
    through a graph is NP-hard and this is choosing a test route, not
    planning a delivery.
    """
    remaining = list(pieces)
    remaining.sort(key=_walked, reverse=True)
    path = list(remaining.pop(0))

    joined = True
    while joined and remaining:
        joined = False
        for index, piece in enumerate(remaining):
            for end, points in ((path[-1], piece), (path[-1], piece[::-1])):
                if math.dist(end, points[0]) <= join_m:
                    path.extend(points[1:])
                    remaining.pop(index)
                    joined = True
                    break
            if joined:
                break
            for start, points in ((path[0], piece), (path[0], piece[::-1])):
                if math.dist(start, points[-1]) <= join_m:
                    path[:0] = points[:-1]
                    remaining.pop(index)
                    joined = True
                    break
            if joined:
                break
    return path


def _walked(points) -> float:
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


_SHAPES = {
    "line": _line,
    "out-and-back": _out_and_back,
    "circuit": _circuit,
    "figure-eight": _figure_eight,
    "lawnmower": _lawnmower,
    "waypoints": _waypoints,
    "road": _road,
}


# --- Plumbing -------------------------------------------------------------


def _along(corners, step_m: float):
    """A polyline through these corners, sampled about every `step_m`."""
    step = max(float(step_m), 1.0)
    out = []
    for start, finish in zip(corners, corners[1:]):
        span = math.dist(start, finish)
        steps = max(int(span / step), 1)
        for index in range(steps):
            share = index / steps
            out.append((start[0] + (finish[0] - start[0]) * share,
                        start[1] + (finish[1] - start[1]) * share))
    out.append(tuple(float(v) for v in corners[-1]))
    return tuple((float(x), float(y)) for x, y in out)


def _inside(points, course: Course):
    """Every point brought within the site, and duplicates dropped.

    Clamped rather than refused: a shape drawn from a formula can graze
    the edge by a metre, and losing the route over that would be worse
    than moving it back. Anything standing or driving outside the
    measurement is the thing ADR-0037 exists to stop.
    """
    top = max(course.width_m, 0.0)
    kept = []
    for x, y in points:
        here = (min(max(float(x), 0.0), course.length_m),
                min(max(float(y), 0.0), top))
        if not kept or math.dist(kept[-1], here) > 1e-6:
            kept.append(here)
    return tuple(kept)
