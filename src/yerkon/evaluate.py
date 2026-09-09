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
from yerkon.hardware import Antenna, DWM3000, Radio, SX1280, W24P_U
from yerkon.observation import RangeObservation
from yerkon.ranging import (
    CRYSTAL,
    DOUBLE_SIDED,
    Clock,
    Scheme,
    audible,
    exchange_duration_s,
    measure,
    share_a_waveform,
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
class Receiver:
    """One moving unit, its journey, and the modules it carries.

    Both receivers in the report's bill of materials carry two radios: a
    spread module and an impulse one. That is not decoration. It is what
    lets one unit range against town anchors on the open road and against
    tunnel anchors inside a bore, without changing anything about the
    unit. A receiver therefore ranges against every anchor it shares a
    waveform with, and quietly ignores the rest.
    """

    identifier: str
    journey: Journey
    radios: tuple[Radio, ...] = (SX1280,)
    antenna: Antenna = W24P_U
    #: Which product in the bill of materials this is, for costing.
    product: str = "vehicle"

    def __post_init__(self) -> None:
        if not self.radios:
            raise ValueError("a receiver with no radio hears nothing")

    def terminal(self, radio: Radio, at_s: float) -> Terminal:
        return Terminal(radio, self.antenna, self.journey.position_at(at_s))


@dataclass(frozen=True)
class Deployment:
    """Anchors on the ground and receivers moving among them.

    Neither is required to be of one kind. A corridor that runs from a
    town through open country into a tunnel carries all three anchor
    modules, and the units driving along it carry two.
    """

    anchors: tuple[Anchor, ...]
    receivers: tuple[Receiver, ...] = ()
    antenna: Antenna = W24P_U
    scheme: Scheme = DOUBLE_SIDED
    clock: Clock = CRYSTAL
    region: SpectrumRule = TURKEY
    #: Share of the second this deployment's ranging may occupy.
    duty_cycle: float = 1.0

    def __post_init__(self) -> None:
        if not self.anchors:
            raise ValueError("a deployment needs anchors")
        for group, what in ((self.anchors, "anchors"), (self.receivers, "receivers")):
            identifiers = [item.identifier for item in group]
            if len(set(identifiers)) != len(identifiers):
                raise ValueError("two {} share an identifier".format(what))

    def terminals(self) -> tuple[tuple[str, Terminal], ...]:
        return tuple(
            (
                anchor.identifier,
                Terminal(anchor.radio, self.antenna, anchor.position_m),
            )
            for anchor in self.anchors
        )

    def radios(self) -> tuple[Radio, ...]:
        """Every distinct waveform in the deployment, anchors and units."""
        seen: list[Radio] = []
        for radio in [a.radio for a in self.anchors] + [
            r for receiver in self.receivers for r in receiver.radios
        ]:
            if not any(share_a_waveform(radio, known) for known in seen):
                seen.append(radio)
        return tuple(seen)

    def anchors_heard_by(self, receiver: Receiver) -> tuple[tuple[str, Terminal, Radio], ...]:
        """The anchors this unit could range against, and with which module."""
        return tuple(
            (identifier, terminal, radio)
            for identifier, terminal in self.terminals()
            for radio in [audible(terminal, receiver.radios)]
            if radio is not None
        )

    def round_duration_s(self) -> float:
        """How long between one unit's fixes, in seconds.

        The medium is shared. Every unit that can hear an anchor waits
        its turn at it, so a second unit does not halve the work, it
        doubles the wait. Anchors on a different waveform are on a
        different medium and cost nothing here, which is why a mixed
        corridor updates faster than its anchor count suggests.
        """
        if not self.receivers:
            # Nothing is driving yet, so price a single unit carrying
            # every waveform present. That is the deployment's own
            # worst case and the number a coverage map implies.
            demand_s = sum(
                exchange_duration_s(anchor.radio, self.scheme)
                for anchor in self.anchors
            )
            return demand_s / self.duty_cycle

        demand_s = sum(
            exchange_duration_s(anchor_radio, self.scheme)
            for unit in self.receivers
            for _, _, anchor_radio in self.anchors_heard_by(unit)
        )
        return demand_s / self.duty_cycle


@dataclass(frozen=True)
class Scenario:
    """One row of the report: a deployment, a site, and the units on it."""

    name: str
    terrain: Terrain
    deployment: Deployment
    seed: int = 0
    manoeuvre_m_s2: float = DEFAULT_MANOEUVRE_M_S2
    #: Ranging error a link may have and still be used, in metres.
    #:
    #: Beyond this the measurement is worse than useless: it drags a fix
    #: rather than improving it. Real receivers gate on signal quality
    #: for the same reason.
    accept_sigma_m: float = 30.0

    def __post_init__(self) -> None:
        if not self.deployment.receivers:
            raise ValueError("a scenario needs at least one receiver")


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
    """Drive every unit, fix as often as the medium allows, count errors.

    Units share the anchors, so a round takes as long as all of them
    together need, and every unit is fixed once per round. Errors from
    all of them land in one sample set: the table's rows are about a
    deployment, not about one vehicle.
    """
    rng = np.random.default_rng(scenario.seed)

    deployment = scenario.deployment
    round_s = deployment.round_duration_s()

    horizontal: list[float] = []
    vertical: list[float] = []
    attempted = 0
    attempted_links = 0
    lost_links = 0

    trackers: dict[str, Optional[TrackingFilter]] = {
        unit.identifier: None for unit in deployment.receivers
    }
    longest_s = max(
        unit.journey.duration_s for unit in deployment.receivers
    )

    at_s = 0.0
    while at_s + round_s <= longest_s:
        # One slot per exchange, laid end to end across every unit, so
        # nothing is measured at the same instant as anything else. That
        # is the whole reason the estimator is a filter (ADR-0010).
        slot_at_s = at_s
        for unit in deployment.receivers:
            if at_s + round_s > unit.journey.duration_s:
                continue
            attempted += 1
            observations = []
            for identifier, anchor, radio in deployment.anchors_heard_by(unit):
                attempted_links += 1
                receiver = unit.terminal(radio, slot_at_s)
                observation = measure(
                    anchor,
                    receiver,
                    slot_at_s,
                    rng,
                    anchor_id=identifier,
                    clock=deployment.clock,
                    scheme=deployment.scheme,
                    obstruction=scenario.terrain.obstruction_between(
                        anchor.position_m, receiver.position_m
                    ),
                    region=deployment.region,
                )
                slot_at_s += exchange_duration_s(
                    anchor.radio, deployment.scheme
                ) / deployment.duty_cycle
                if observation is None:
                    lost_links += 1
                elif observation.sigma_m <= scenario.accept_sigma_m:
                    observations.append(observation)

            fix = _fix_from(
                observations, trackers[unit.identifier], scenario.manoeuvre_m_s2
            )
            if fix is None:
                # A round that produced no position is an outage, and the
                # filter is not carried across it: a receiver that lost
                # the network does not know where it drifted to.
                trackers[unit.identifier] = None
                continue

            tracker, position = fix
            trackers[unit.identifier] = tracker
            truth = unit.journey.position_at(tracker.at_s)
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
    """Fold one round into a unit's filter, starting it if it is not running."""
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
class CoverageGrid:
    """How many anchors reach each cell of a swept grid.

    The count rather than a yes or no, because one anchor and four
    anchors mean entirely different things and a boolean would throw
    away the distinction ADR-0012 exists to make.
    """

    #: Anchors in reach at each cell, indexed [row, column].
    counts: np.ndarray
    #: Cell centres, in metres.
    xs: np.ndarray
    ys: np.ndarray
    resolution_m: float

    @property
    def cell_km2(self) -> float:
        return (self.resolution_m / 1000.0) ** 2

    def area_reached_by(self, anchors: int) -> float:
        return float(np.count_nonzero(self.counts >= anchors)) * self.cell_km2


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


def coverage_grid(
    deployment: Deployment,
    terrain: Terrain,
    receiver_height_m: float = 1.5,
    target_sigma_m: float = 5.0,
    resolution_m: float = 250.0,
    margin_m: float = 12_000.0,
    count_up_to: int = 8,
) -> CoverageGrid:
    """Sweep a grid and count reachable anchors at every cell.

    ``count_up_to`` stops counting once a cell has that many anchors in
    reach, because nothing downstream distinguishes eight from nine and
    the sweep is the slowest thing in the project.
    """
    positions = [anchor.position_m for anchor in deployment.anchors]
    xs = np.arange(
        min(p[0] for p in positions) - margin_m,
        max(p[0] for p in positions) + margin_m,
        resolution_m,
    )
    ys = np.arange(
        min(p[1] for p in positions) - margin_m,
        max(p[1] for p in positions) + margin_m,
        resolution_m,
    )

    anchors = deployment.terminals()
    # Ground is served for a unit carrying whatever the deployment's
    # units carry. A sweep against one waveform would call a tunnel
    # anchor unreachable from a road unit that in fact carries the
    # matching module.
    radios = _sweep_radios(deployment)
    counts = np.zeros((ys.size, xs.size), dtype=int)

    for row, y in enumerate(ys):
        for column, x in enumerate(xs):
            here = (
                float(x), float(y),
                terrain.height_at(float(x), float(y)) + receiver_height_m,
            )
            reached = 0
            for _, anchor in anchors:
                radio = audible(anchor, radios)
                if radio is None:
                    continue
                receiver = Terminal(radio, deployment.antenna, here)
                if math.dist(anchor.position_m, here) < 1.0:
                    reached += 1
                elif _reaches(
                    anchor, receiver, terrain, deployment, target_sigma_m
                ):
                    reached += 1
                if reached >= count_up_to:
                    break
            counts[row, column] = reached

    return CoverageGrid(counts=counts, xs=xs, ys=ys, resolution_m=resolution_m)


def _sweep_radios(deployment: Deployment) -> tuple[Radio, ...]:
    if deployment.receivers:
        seen = []
        for unit in deployment.receivers:
            for radio in unit.radios:
                if not any(share_a_waveform(radio, known) for known in seen):
                    seen.append(radio)
        return tuple(seen)
    return deployment.radios()


def _reaches(anchor, receiver, terrain, deployment, target_sigma_m) -> bool:
    budget = evaluate_link(
        anchor,
        receiver,
        obstruction=terrain.obstruction_between(
            anchor.position_m, receiver.position_m
        ),
        region=deployment.region,
    )
    return budget.closes and (
        ranging_sigma_m(budget, anchor.radio) <= target_sigma_m
    )


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

    grid = coverage_grid(
        deployment,
        terrain,
        receiver_height_m=receiver_height_m,
        target_sigma_m=target_sigma_m,
        resolution_m=resolution_m,
        margin_m=margin_m,
        count_up_to=anchors_required,
    )

    return Coverage(
        reached_km2=grid.area_reached_by(1),
        fixable_km2=grid.area_reached_by(anchors_required),
        resolution_m=resolution_m,
        anchors_required=anchors_required,
    )
