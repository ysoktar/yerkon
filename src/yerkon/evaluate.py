"""Driving a receiver past a deployment and counting how wrong it was.

This is where the parts meet: a road with a grade, anchors on structures
beside it, a ranging exchange over real ground, an estimator that sees
only what the exchange produced, and truth that only this module and the
world are allowed to read.

What comes out is raw per-fix error samples, not summary statistics. The
weighted row of the report combines the samples of three scenarios and
recomputes its percentiles from the combination, which is impossible from
percentiles alone. See ADR-0005.

Every run reseeds. A previous version of this project held a generator
across scenarios, so the second one in a process drew from wherever the
first stopped, and every swept comparison it published was contaminated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from yerkon.estimator import DEFAULT_MANOEUVRE_M_S2, TrackingFilter, trilaterate
from yerkon.hardware import Antenna, Radio, SX1280, W24P_U
from yerkon.observation import RangeObservation
from yerkon.ranging import (
    CRYSTAL,
    DOUBLE_SIDED,
    Clock,
    Scheme,
    exchange_duration_s,
    round_robin,
)
from yerkon.regulatory import TURKEY, SpectrumRule
from yerkon.rf import Terminal, evaluate_link, ranging_sigma_m
from yerkon.world import Anchor, Road, Terrain


@dataclass(frozen=True)
class Journey:
    """A receiver travelling along a road.

    Height is the road surface plus the antenna's offset above it, so a
    graded road makes the receiver climb (ADR-0004). Nothing tells the
    estimator either number.
    """

    road: Road
    speed_m_s: float
    duration_s: float
    start_m: float = 0.0
    antenna_height_m: float = 1.5

    def __post_init__(self) -> None:
        if self.speed_m_s < 0.0:
            raise ValueError("a journey does not run backwards")
        if self.duration_s <= 0.0:
            raise ValueError("a journey takes time")
        if self.antenna_height_m <= 0.0:
            raise ValueError("an antenna stands above the road")

    def position_at(self, at_s: float) -> tuple[float, float, float]:
        """Where the receiver truly is. Truth, and only the world sees it."""
        along_m = min(
            self.start_m + self.speed_m_s * at_s, self.road.length_m - 1e-6
        )
        x, y, surface_m = self.road.point_at(max(along_m, 0.0))
        return (x, y, surface_m + self.antenna_height_m)


@dataclass(frozen=True)
class Deployment:
    """Anchors on the ground, and the radios at both ends of the link."""

    anchors: tuple[Anchor, ...]
    anchor_radio: Radio = SX1280
    receiver_radio: Radio = SX1280
    antenna: Antenna = W24P_U
    scheme: Scheme = DOUBLE_SIDED
    clock: Clock = CRYSTAL
    region: SpectrumRule = TURKEY
    #: Share of the second this deployment's ranging may occupy.
    duty_cycle: float = 1.0

    def __post_init__(self) -> None:
        if not self.anchors:
            raise ValueError("a deployment needs anchors")
        identifiers = [a.identifier for a in self.anchors]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("two anchors share an identifier")

    def terminals(self) -> tuple[tuple[str, Terminal], ...]:
        return tuple(
            (
                anchor.identifier,
                Terminal(self.anchor_radio, self.antenna, anchor.position_m),
            )
            for anchor in self.anchors
        )

    @property
    def round_duration_s(self) -> float:
        return (
            len(self.anchors)
            * exchange_duration_s(self.anchor_radio, self.scheme)
            / self.duty_cycle
        )


@dataclass(frozen=True)
class Scenario:
    """One row of the report: a deployment, a site, and some journeys."""

    name: str
    terrain: Terrain
    deployment: Deployment
    journeys: tuple[Journey, ...]
    seed: int = 0
    manoeuvre_m_s2: float = DEFAULT_MANOEUVRE_M_S2
    #: Ranging error a link may have and still be attempted, in metres.
    #:
    #: Beyond this the measurement is worse than useless: it drags a fix
    #: rather than improving it. Real receivers gate on signal quality
    #: for the same reason.
    accept_sigma_m: float = 30.0

    def __post_init__(self) -> None:
        if not self.journeys:
            raise ValueError("a scenario needs at least one journey")


@dataclass(frozen=True)
class Samples:
    """Raw per-fix errors, and how many fixes were not produced at all.

    Percentiles are computed on demand rather than stored, because the
    weighted row has to combine the samples themselves (ADR-0005).
    """

    name: str
    horizontal_error_m: np.ndarray
    vertical_error_m: np.ndarray
    #: Rounds of ranging attempted, whether or not they yielded a fix.
    attempted: int
    #: Ranging exchanges that produced no measurement at all.
    lost_links: int = 0
    #: Ranging exchanges attempted.
    attempted_links: int = 0

    @property
    def produced(self) -> int:
        return int(self.horizontal_error_m.size)

    @property
    def availability(self) -> float:
        """Share of attempted fixes that produced a position.

        Counts modelled failure causes only: a link that did not close, a
        round with too few ranges to solve, a solve that did not settle.
        It is not a service availability figure and must not be read
        against the GNSS rows as though it were.
        """
        if self.attempted == 0:
            return 0.0
        return self.produced / self.attempted

    def percentile(self, share: float) -> tuple[float, float]:
        """Horizontal and vertical error at a percentile, in metres."""
        if self.produced == 0:
            return (math.nan, math.nan)
        return (
            float(np.percentile(self.horizontal_error_m, share)),
            float(np.percentile(self.vertical_error_m, share)),
        )


def combine(weighted: Sequence[tuple[Samples, float]], name: str) -> Samples:
    """One set of samples from several, under fixed weights. ADR-0005.

    Averaging three ninety-fifth percentiles does not give a ninety-fifth
    percentile of anything, so this repeats each scenario's raw samples
    in proportion to its weight and lets the percentile be computed from
    the combination. Availability combines the same way.
    """
    if not weighted:
        raise ValueError("nothing to combine")
    total = sum(weight for _, weight in weighted)
    if total <= 0.0:
        raise ValueError("weights must add to something positive")

    smallest = min(
        (s.produced for s, _ in weighted if s.produced), default=0
    )
    if smallest == 0:
        raise ValueError("a scenario with no fixes cannot be weighted in")

    horizontal, vertical = [], []
    attempted = produced_weight = 0.0
    for samples, weight in weighted:
        share = weight / total
        # Draw the same proportion of each scenario's samples, so a
        # scenario that happened to be run longer does not weigh more
        # than the weights say.
        take = max(int(round(share * smallest * len(weighted))), 1)
        index = np.linspace(0, samples.produced - 1, take).astype(int)
        horizontal.append(samples.horizontal_error_m[index])
        vertical.append(samples.vertical_error_m[index])
        attempted += share * samples.attempted
        produced_weight += share * samples.produced

    combined_h = np.concatenate(horizontal)
    return Samples(
        name=name,
        horizontal_error_m=combined_h,
        vertical_error_m=np.concatenate(vertical),
        # Scale the attempt count so availability comes out as the
        # weighted average of the scenarios' own.
        attempted=int(round(combined_h.size * attempted / max(produced_weight, 1e-9))),
        lost_links=sum(s.lost_links for s, _ in weighted),
        attempted_links=sum(s.attempted_links for s, _ in weighted),
    )


def run_scenario(scenario: Scenario) -> Samples:
    """Drive every journey, fix as often as the ranging allows, count errors."""
    rng = np.random.default_rng(scenario.seed)

    deployment = scenario.deployment
    anchors = deployment.terminals()
    round_s = deployment.round_duration_s

    horizontal: list[float] = []
    vertical: list[float] = []
    attempted = 0
    attempted_links = 0
    lost_links = 0

    for journey in scenario.journeys:
        def receiver_at(at_s: float, journey=journey) -> Terminal:
            return Terminal(
                deployment.receiver_radio,
                deployment.antenna,
                journey.position_at(at_s),
            )

        def obstruction_between(anchor: Terminal, receiver: Terminal):
            return scenario.terrain.obstruction_between(
                anchor.position_m, receiver.position_m
            )

        tracker: Optional[TrackingFilter] = None
        at_s = 0.0
        while at_s + round_s <= journey.duration_s:
            attempted += 1
            attempted_links += len(anchors)

            observations = round_robin(
                anchors,
                receiver_at,
                at_s,
                rng,
                deployment.anchor_radio,
                clock=deployment.clock,
                scheme=deployment.scheme,
                duty_cycle=deployment.duty_cycle,
                obstruction_between=obstruction_between,
                region=deployment.region,
            )
            lost_links += len(anchors) - len(observations)

            usable = tuple(
                o for o in observations
                if o.sigma_m <= scenario.accept_sigma_m
            )

            fix = _fix_from(usable, tracker, scenario.manoeuvre_m_s2)
            if fix is None:
                # A round that produced no position is an outage, and the
                # filter is not carried across it: a receiver that lost
                # the network does not know where it drifted to.
                tracker = None
                at_s += round_s
                continue

            tracker, position = fix
            truth = journey.position_at(tracker.at_s)
            horizontal.append(math.dist(position[:2], truth[:2]))
            vertical.append(abs(position[2] - truth[2]))
            at_s += round_s

    return Samples(
        name=scenario.name,
        horizontal_error_m=np.array(horizontal),
        vertical_error_m=np.array(vertical),
        attempted=attempted,
        lost_links=lost_links,
        attempted_links=attempted_links,
    )


def _fix_from(
    observations: Sequence[RangeObservation],
    tracker: Optional[TrackingFilter],
    manoeuvre_m_s2: float,
):
    """Fold one round into the filter, starting it if it is not running."""
    if tracker is None:
        start = trilaterate(observations)
        if start is None:
            return None
        return TrackingFilter(start, manoeuvre_m_s2=manoeuvre_m_s2), start.position_m

    if not observations:
        return None
    for observation in observations:
        tracker.absorb(observation)
    return tracker, tracker.position_m


# --- Where the deployment works at all ------------------------------------


@dataclass(frozen=True)
class Coverage:
    """How much ground a deployment serves, by two different readings."""

    #: Ground reached by at least one anchor, in square kilometres.
    reached_km2: float
    #: Ground reached by enough anchors to produce a position.
    fixable_km2: float
    #: Cell size the two were measured on, in metres.
    resolution_m: float
    #: Anchors a position needs.
    anchors_required: int


def coverage(
    deployment: Deployment,
    terrain: Terrain,
    receiver_height_m: float = 1.5,
    target_sigma_m: float = 5.0,
    resolution_m: float = 250.0,
    anchors_required: int = 4,
    margin_m: float = 12_000.0,
) -> Coverage:
    """The area a deployment actually serves, swept rather than assumed.

    Two numbers, because they differ and the difference matters. Ground
    one anchor reaches is ground where a packet arrives. Ground four
    anchors reach is ground where a receiver knows where it is. Only the
    second is coverage of a positioning service, and it is much the
    smaller of the two.

    Both are measured by sweeping a grid and asking the link budget over
    the real terrain, which is what makes this the area range actually
    covers rather than a corridor drawn around the road.
    """
    if anchors_required < 4:
        raise ValueError("fewer than four ranges cannot place a point")

    positions = [anchor.position_m for anchor in deployment.anchors]
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]

    grid_x = np.arange(min(xs) - margin_m, max(xs) + margin_m, resolution_m)
    grid_y = np.arange(min(ys) - margin_m, max(ys) + margin_m, resolution_m)

    anchors = deployment.terminals()
    cell_km2 = (resolution_m / 1000.0) ** 2
    reached = fixable = 0

    for x in grid_x:
        for y in grid_y:
            here = (float(x), float(y), terrain.height_at(float(x), float(y))
                    + receiver_height_m)
            receiver = Terminal(deployment.receiver_radio, deployment.antenna, here)

            count = 0
            for _, anchor in anchors:
                if math.dist(anchor.position_m, here) < 1.0:
                    count += 1
                    continue
                budget = evaluate_link(
                    anchor,
                    receiver,
                    obstruction=terrain.obstruction_between(
                        anchor.position_m, here
                    ),
                    region=deployment.region,
                )
                if budget.closes and ranging_sigma_m(
                    budget, deployment.anchor_radio
                ) <= target_sigma_m:
                    count += 1
                    if count >= anchors_required:
                        break

            if count >= 1:
                reached += 1
            if count >= anchors_required:
                fixable += 1

    return Coverage(
        reached_km2=reached * cell_km2,
        fixable_km2=fixable * cell_km2,
        resolution_m=resolution_m,
        anchors_required=anchors_required,
    )
