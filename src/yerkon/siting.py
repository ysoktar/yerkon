"""Placing anchors for a target accuracy at the lowest cost.

Deferred until everything else existed, on purpose: an optimiser is only
as good as what it optimises, and until the link budget, the exchange,
the estimator and the costing were all built and tested, any siting
algorithm would have been minimising a number nobody could defend.

What it optimises is the thing the cost module found. The radios are
about one percent of a mast-based deployment's capital, so this does not
search over modules to save money — it searches over *where the anchors
go and what they are bolted to*, which is the rest of it.

The method is deliberately not clever. A corridor is a line, the decision
at each point is which structure to use, and the search is over spacings
and mixes, evaluated by the same coverage sweep and link budget the table
uses. Every candidate is a real deployment that could be built, priced by
the real bill of materials, and the answer comes with the runner-up so a
person can see how close the decision was.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Callable, Optional, Sequence

import numpy as np

from yerkon.cost import DEFAULT_RATES, Costing, Inventory, OperatingRates, anchor_product, AnchorSite, price
from yerkon.evaluate import Deployment, Receiver, coverage_grid
from yerkon.hardware import Radio, SX1280
from yerkon.numbers import decimal_comma
from yerkon.world import (
    BILLBOARD,
    LIGHTING_COLUMN,
    MountingOption,
    ROADSIDE_SIGN,
    SIGN_GANTRY,
    TALL_MAST,
    Anchor,
    Terrain,
)


@dataclass(frozen=True)
class Availability:
    """Which structures already stand where, and how far apart.

    This is the constraint that decides everything. A lighting column
    costs a twenty-fifth of a mast and reaches two thirds as far, so a
    corridor with columns along it is a different problem from one
    without. Nobody supplied a survey, so this is configuration: the
    numbers say what a stretch of road is assumed to carry, and a real
    deployment would replace them with what is actually there.
    """

    mounting: MountingOption
    #: Metres between existing structures of this kind. Infinite when
    #: there are none.
    every_m: float
    #: Where along the corridor they start and stop, in metres.
    from_m: float = 0.0
    to_m: float = math.inf

    def positions(self, corridor_m: float) -> list[float]:
        if not math.isfinite(self.every_m) or self.every_m <= 0.0:
            return []
        start = max(self.from_m, 0.0)
        stop = min(self.to_m, corridor_m)
        if stop <= start:
            return []
        return [
            float(x) for x in np.arange(start, stop + 1e-6, self.every_m)
        ]


#: What a stretch of Turkish highway is assumed to carry.
#:
#: Signs are everywhere, gantries and billboards are occasional, lighting
#: columns exist near junctions and settlements and not in open country.
#: A mast can be built anywhere, at a price. None of this was supplied
#: and all of it is configuration.
TYPICAL_ROADSIDE = (
    Availability(ROADSIDE_SIGN, every_m=250.0),
    Availability(SIGN_GANTRY, every_m=4000.0),
    Availability(BILLBOARD, every_m=3000.0),
    Availability(LIGHTING_COLUMN, every_m=60.0, from_m=0.0, to_m=3000.0),
    Availability(TALL_MAST, every_m=math.inf),
)


@dataclass(frozen=True)
class Requirement:
    """What the deployment has to achieve before cost is even considered."""

    #: Ranging error a link may have and still count toward a fix.
    target_sigma_m: float = 5.0
    #: Anchors that must be reachable for a position to exist.
    anchors_required: int = 4
    #: Share of the corridor that must have that many in reach.
    corridor_covered: float = 0.95
    #: How far either side of the road has to be served, in metres. Zero
    #: asks only for the carriageway.
    served_width_m: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 < self.corridor_covered <= 1.0:
            raise ValueError("coverage is a share of the corridor")
        if self.anchors_required < 4:
            raise ValueError("fewer than four ranges cannot place a point")


@dataclass(frozen=True)
class Candidate:
    """One deployment that could be built, and what it comes to."""

    label: str
    anchors: tuple[Anchor, ...]
    costing: Costing
    #: Share of the corridor with enough anchors in reach.
    corridor_covered: float
    #: Ground served, in square kilometres.
    served_km2: float

    @property
    def meets(self) -> bool:
        return self._meets

    _meets: bool = True

    def describe(self) -> str:
        return (
            "{:<26} {:>4} anchors  {:>12} TL  {:>7} covered  {:>8} km²".format(
                self.label,
                len(self.anchors),
                decimal_comma(self.costing.capex_tl, 0),
                "%{}".format(decimal_comma(100.0 * self.corridor_covered, 1)),
                decimal_comma(self.served_km2, 2),
            )
        )


def _corridor_cover(
    deployment: Deployment,
    terrain: Terrain,
    corridor_m: float,
    requirement: Requirement,
    receiver_height_m: float,
    samples: int = 60,
) -> float:
    """Share of the road with enough anchors in reach.

    Sampled along the carriageway rather than over a grid, because that
    is what the requirement is about and it is thirty times cheaper. The
    area sweep is run once, on the winner.
    """
    from yerkon.evaluate import _reaches
    from yerkon.rf import Terminal

    anchors = deployment.terminals()
    radios = tuple({radio for unit in deployment.receivers for radio in unit.radios}) or (
        SX1280,
    )
    met = 0
    for x in np.linspace(0.0, corridor_m, samples):
        for offset in ({0.0} | ({requirement.served_width_m} if requirement.served_width_m else set())):
            here = (
                float(x), float(offset),
                terrain.height_at(float(x), float(offset)) + receiver_height_m,
            )
            reached = 0
            for _, anchor in anchors:
                radio = next(
                    (
                        r for r in radios
                        if float(r.ranging_bandwidth_hz.value)
                        == float(anchor.radio.ranging_bandwidth_hz.value)
                    ),
                    None,
                )
                if radio is None:
                    continue
                if _reaches(
                    anchor,
                    Terminal(radio, deployment.antenna, here),
                    terrain,
                    deployment,
                    requirement.target_sigma_m,
                ):
                    reached += 1
                    if reached >= requirement.anchors_required:
                        break
            if reached < requirement.anchors_required:
                break
        else:
            met += 1
    return met / samples


def _build(
    plan: Sequence[tuple[MountingOption, float, float, float]],
    terrain: Terrain,
    radio: Radio,
    offset_m: float,
) -> tuple[Anchor, ...]:
    """Anchors from a plan of (mounting, from, to, spacing)."""
    anchors = []
    index = 0
    for mounting, from_m, to_m, spacing_m in plan:
        if spacing_m <= 0.0 or to_m <= from_m:
            continue
        for step, x in enumerate(np.arange(from_m, to_m + 1e-6, spacing_m)):
            anchors.append(
                Anchor(
                    "S{}".format(index),
                    (float(x), offset_m if step % 2 == 0 else -offset_m),
                    mounting,
                    terrain,
                    radio=radio,
                )
            )
            index += 1
    return tuple(anchors)


def _structure_near(
    position_m: float,
    reach_m: float,
    available: Sequence[Availability],
    corridor_m: float,
    cache: dict,
    prefer: str,
) -> Optional[tuple[MountingOption, float]]:
    """A structure standing near a wanted position, by one preference.

    This is the whole of the mixing. At every point the deployment wants
    an anchor, it takes whatever already stands there and only builds
    where nothing does.

    Which one it takes is a real trade-off rather than an obvious choice.
    The *cheapest* structure at each site gives the lowest price per
    anchor and, being short, needs more of them. The *tallest* costs more
    each and may need far fewer. Neither wins in general, so both are
    searched and the answer is whichever came out cheaper overall.
    """
    best = None
    for availability in available:
        key = id(availability)
        if key not in cache:
            cache[key] = availability.positions(corridor_m)
        standing = cache[key]

        if not standing:
            # Nothing of this kind stands anywhere, so it has to be
            # built, and it can be built exactly where it is wanted.
            candidate = (availability.mounting, position_m)
        else:
            nearest = min(standing, key=lambda x: abs(x - position_m))
            if abs(nearest - position_m) > reach_m:
                continue
            candidate = (availability.mounting, nearest)

        if prefer == "tallest":
            score = -float(candidate[0].height_m.value)
        else:
            score = float(candidate[0].site_cost_tl.value)
        if best is None or score < best[0]:
            best = (score, candidate)
    return None if best is None else best[1]


def cheapest(
    terrain: Terrain,
    corridor_m: float,
    receivers: Sequence[Receiver],
    radio: Radio = SX1280,
    requirement: Requirement = Requirement(),
    available: Sequence[Availability] = TYPICAL_ROADSIDE,
    rates: OperatingRates = DEFAULT_RATES,
    offset_m: float = 60.0,
    receiver_height_m: float = 1.5,
    region=None,
    spacings_m: Sequence[float] = (
        4000.0, 3000.0, 2500.0, 2000.0, 1500.0, 1200.0, 1000.0,
        800.0, 600.0, 500.0, 400.0, 300.0, 250.0, 200.0, 150.0, 100.0,
    ),
    measure_area: bool = True,
    on_candidate: Optional[Callable[[Candidate], None]] = None,
) -> tuple[Optional[Candidate], tuple[Candidate, ...]]:
    """The least expensive deployment that meets the requirement.

    Two families of candidate. A **mixed** one takes, at every point it
    wants an anchor, whatever structure already stands nearest, and only
    builds where nothing does — which is what the report's mixed mounting
    strategy means and what the cost module says the money turns on. A
    **single-structure** one uses one kind throughout, and is searched
    alongside so the mixed answer can be seen to beat it rather than
    asserted to.

    Spacings are tried from sparse to dense and the search stops at the
    first that meets, because denser is dearer and never covers less. The
    first one that meets is therefore the cheapest of its family, and
    trying the dense end first would have found an answer that works and
    costs several times too much.

    Returns the winner and every candidate in cost order, so a person can
    see how close the decision was and what it turned on.
    """
    from yerkon.evaluate import Deployment as Build

    candidates: list[Candidate] = []
    standing: dict = {}

    def evaluate(label: str, anchors: tuple[Anchor, ...]) -> Optional[Candidate]:
        if len(anchors) < requirement.anchors_required:
            return None
        deployment = Build(
            anchors=anchors,
            receivers=tuple(receivers),
            **({"region": region} if region is not None else {}),
        )
        covered = _corridor_cover(
            deployment, terrain, corridor_m, requirement, receiver_height_m
        )
        candidate = Candidate(
            label=label,
            anchors=anchors,
            costing=price(
                _inventory(anchors, corridor_m, max(corridor_m / 1000.0 * 0.1, 0.01)),
                rates,
            ),
            corridor_covered=covered,
            served_km2=0.0,
            _meets=covered >= requirement.corridor_covered,
        )
        candidates.append(candidate)
        if on_candidate is not None:
            on_candidate(candidate)
        return candidate

    # --- take whatever already stands there ------------------------------
    for prefer in ("cheapest", "tallest"):
        for spacing_m in spacings_m:
            if spacing_m > corridor_m:
                continue
            plan = []
            for position in np.arange(0.0, corridor_m + 1e-6, spacing_m):
                found = _structure_near(
                    float(position), spacing_m * 0.5, available, corridor_m,
                    standing, prefer,
                )
                if found is not None:
                    plan.append(found)
            # Two wanted positions can land on the same existing structure.
            seen = set()
            anchors = tuple(
                Anchor(
                    "X{}".format(index),
                    (at_m, offset_m if index % 2 == 0 else -offset_m),
                    mounting,
                    terrain,
                    radio=radio,
                )
                for index, (mounting, at_m) in enumerate(
                    item for item in plan
                    if not (item[1] in seen or seen.add(item[1]))
                )
            )
            candidate = evaluate(
                "mixed ({}), every {} m".format(
                    prefer, decimal_comma(spacing_m, 0)
                ),
                anchors,
            )
            if candidate is not None and candidate.meets:
                break

    # --- one kind throughout, for comparison ------------------------------
    for availability in available:
        existing = availability.positions(corridor_m)
        if existing:
            steps = sorted(
                {availability.every_m * multiple
                 for multiple in (32, 24, 16, 12, 8, 6, 4, 3, 2, 1)},
                reverse=True,
            )
        else:
            steps = sorted(spacings_m, reverse=True)

        for spacing_m in steps:
            if spacing_m > corridor_m:
                continue
            from_m = availability.from_m if existing else 0.0
            to_m = min(availability.to_m, corridor_m) if existing else corridor_m
            candidate = evaluate(
                "{} every {} m".format(
                    availability.mounting.kind, decimal_comma(spacing_m, 0)
                ),
                _build(
                    [(availability.mounting, from_m, to_m, spacing_m)],
                    terrain, radio, offset_m,
                ),
            )
            if candidate is not None and candidate.meets:
                break

    ordered = sorted(candidates, key=lambda c: c.costing.capex_tl)
    winner = next((c for c in ordered if c.meets), None)

    if winner is not None and measure_area:
        # The area sweep is the slowest thing in the project, so it runs
        # once, on the deployment that won, rather than on every one that
        # was tried.
        grid = coverage_grid(
            Build(
                anchors=winner.anchors,
                receivers=tuple(receivers),
                **({"region": region} if region is not None else {}),
            ),
            terrain,
            receiver_height_m=receiver_height_m,
            target_sigma_m=requirement.target_sigma_m,
            resolution_m=500.0,
            margin_m=6000.0,
        )
        served = grid.area_reached_by(requirement.anchors_required)
        measured = replace(
            winner,
            served_km2=served,
            costing=price(
                _inventory(winner.anchors, corridor_m, served), rates
            ),
        )
        ordered = [measured if c is winner else c for c in ordered]
        winner = measured

    return winner, tuple(ordered)


def _inventory(
    anchors: Sequence[Anchor], corridor_m: float, service_area_km2: float
) -> Inventory:
    return Inventory(
        anchors=tuple(
            AnchorSite(
                product=anchor_product(anchor.radio.part),
                structure=anchor.mounting.kind,
                site_cost_tl=anchor.mounting.site_cost_tl,
                has_power=anchor.mounting.has_power,
                has_backhaul=anchor.mounting.has_backhaul,
            )
            for anchor in anchors
        ),
        service_area_km2=max(service_area_km2, 0.01),
        route_km=corridor_m / 1000.0,
    )
