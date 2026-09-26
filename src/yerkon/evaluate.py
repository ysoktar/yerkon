"""Driving a receiver past a deployment and counting how wrong it was.

This is where the parts meet: a road with a grade, anchors on structures
beside it, a ranging exchange over real ground, an estimator that sees
only what the exchange produced, and truth that only this module and the
world are allowed to read.

What comes out is raw per-fix error samples, not summary statistics. A
row pools the samples of its shadow draws and computes its percentiles
from the pool, which is impossible from percentiles alone. See ADR-0055.

Every run reseeds. A previous version of this project held a generator
across scenarios, so the second one in a process drew from wherever the
first stopped, and every swept comparison it published was contaminated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Optional, Sequence

import numpy as np

from yerkon.estimator import DEFAULT_MANOEUVRE_M_S2, TrackingFilter, trilaterate
from yerkon.hardware import Antenna, Radio, SX1280, W24P_U
# A leaf: `layout` imports nothing from this package, so reading its
# geometry here adds no cycle and no path to a receiver's true
# position. Dilution is the same arithmetic whether it is scoring a
# candidate mast or colouring a cell (ADR-0040, ADR-0044).
from yerkon.layout import DILUTION_CEILING, dilution_at
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
from yerkon.regulatory import TURKEY, SpectrumRule, vehicle_uwb_ceiling_dbm
from yerkon.rf import Terminal, evaluate_link, ranging_sigma_m
from yerkon.terms import ALL as ALL_TERMS, Terms
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
    #: Most anchors a unit will range against in one round.
    #:
    #: A receiver over an area can hear far more anchors than it has time
    #: to range against: sixty-four of them at thirty milliseconds each is
    #: a round every two seconds, by which point a vehicle has moved
    #: thirty metres. Real systems range against the nearest few and
    #: ignore the rest, so this does too. Eight is more than enough for a
    #: position and cheap enough to repeat.
    max_anchors_per_round: int = 8

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

    def nearest_to(
        self, receiver: Receiver, at_m: tuple[float, float, float]
    ) -> tuple[tuple[str, Terminal, Radio], ...]:
        """The anchors a unit will actually range against this round.

        The closest it can hear, up to the round's limit. Distance is the
        right ordering because a nearer anchor gives both a stronger link
        and, on a corridor, better geometry than a distant one strung out
        along the same line.
        """
        heard = self.anchors_heard_by(receiver)
        if len(heard) <= self.max_anchors_per_round:
            return heard
        return tuple(
            sorted(heard, key=lambda item: math.dist(item[1].position_m, at_m))
        )[: self.max_anchors_per_round]

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

        demand_s = 0.0
        for unit in self.receivers:
            heard = self.anchors_heard_by(unit)
            # Only the ones a round has room for. Which they are depends
            # on where the unit is; how many there are does not, and the
            # duration only needs the count.
            for _, _, anchor_radio in heard[: self.max_anchors_per_round]:
                demand_s += exchange_duration_s(anchor_radio, self.scheme)
        return demand_s / self.duty_cycle


@dataclass(frozen=True)
class Scenario:
    """One row of the report: a deployment, a site, and the units on it."""

    name: str
    terrain: Terrain
    deployment: Deployment
    seed: int = 0
    manoeuvre_m_s2: float = DEFAULT_MANOEUVRE_M_S2
    #: How well each anchor's own position is known, one sigma in metres.
    #:
    #: Drawn once per anchor at the top of a run and held for the whole
    #: of it, because a survey error is a property of an installation and
    #: not of a measurement. It therefore does not average out, and it
    #: puts a floor under the horizontal error that no amount of ranging
    #: removes (ADR-0019).
    anchor_survey_sigma_m: float = 0.0
    #: Share of exchanges lost to everything the link budget omits.
    packet_loss: float = 0.0
    #: Ranging error a link may have and still be used, in metres.
    #:
    #: Beyond this the measurement is worse than useless: it drags a fix
    #: rather than improving it. Real receivers gate on signal quality
    #: for the same reason.
    accept_sigma_m: float = 30.0
    #: The largest horizontal uncertainty the filter may report for a
    #: position to count as available, in metres (square root of the
    #: horizontal covariance's trace). Above it the receiver keeps
    #: tracking but has no position to offer, so the round counts as an
    #: outage and its error is not sampled (ADR-0084). Infinite means any
    #: position the filter holds counts, which is what the table did
    #: before.
    fix_sigma_m: float = math.inf
    #: How many sigmas from what the filter expects a range may land and
    #: still be used. Zero takes every range (ADR-0084).
    gate_sigmas: float = 0.0
    #: How well the unit's map knows the road's height, one sigma in
    #: metres. Each round the filter takes the map's height at the place
    #: it thinks it is as a measurement. Zero leaves the height to the
    #: ranges alone, which is what the table did before (ADR-0088).
    height_aid_sigma_m: float = 0.0
    #: How far along a road the map's error stays alike, in metres. A
    #: height model is wrong in patches, not independently at every
    #: metre, so the error is drawn every this many metres and joined.
    height_aid_correlation_m: float = 500.0

    def __post_init__(self) -> None:
        if not self.deployment.receivers:
            raise ValueError("a scenario needs at least one receiver")


@dataclass(frozen=True)
class Samples:
    """Raw per-fix errors, and how many fixes were not produced at all.

    Percentiles are computed on demand rather than stored, because a row
    pools the samples of its draws and takes the percentile of the pool
    (ADR-0055).
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
    #: Median sigma the receiver believed its own ranges had, in metres.
    #:
    #: What one measurement was worth, before geometry and the filter had
    #: their say. Carried so a dissection can report how much the
    #: arrangement of the anchors multiplies it (ADR-0020).
    median_range_sigma_m: float = 0.0

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


def pooled(draws: Sequence[Samples], name: str) -> Samples:
    """One set of samples from several draws of the same arrangement.

    Shadowing makes a run one draw: the same deployment over the same
    ground, with the vans and hedges and building corners the model does
    not carry arranged one way rather than another (ADR-0055). Measured
    over eight draws, the rural row's ninety-fifth percentile came out
    anywhere between 14,6 m and 279,6 m — because at that availability
    the surviving fixes are few and the percentile is a tail.

    A percentile is a statement about a population, so it is taken over
    the population: the draws' own samples together, rather than an
    average of eight percentiles, which is not a percentile of anything.
    Averaging percentiles is what this refuses, here and anywhere else
    the question comes up.
    """
    if not draws:
        raise ValueError("nothing to pool")
    if len(draws) == 1:
        return replace(draws[0], name=name)
    produced = [d for d in draws if d.produced]
    return Samples(
        name=name,
        horizontal_error_m=(np.concatenate([d.horizontal_error_m for d in produced])
                            if produced else np.array([])),
        vertical_error_m=(np.concatenate([d.vertical_error_m for d in produced])
                          if produced else np.array([])),
        attempted=sum(d.attempted for d in draws),
        lost_links=sum(d.lost_links for d in draws),
        attempted_links=sum(d.attempted_links for d in draws),
        median_range_sigma_m=(
            float(np.median([d.median_range_sigma_m for d in draws]))
            if draws else 0.0
        ),
    )


def _reply_ceiling_dbm(unit: "Receiver", anchor_above_road_m: float,
                       radio: Radio):
    """What a unit may send back to this anchor, where a rule holds it.

    A vehicle's UWB radio may send above its own mounting plane only at
    the exterior limit (ETSI EN 302 065-3, 4.3.4.2). That plane moves with
    the vehicle, so on a graded road what counts is the height above the
    road: an anchor mounted higher than the vehicle's antenna is above
    it, one mounted lower is below it, whatever the gradient between.
    """
    if unit.product != "vehicle":
        return None
    if anchor_above_road_m <= unit.journey.antenna_height_m:
        return None
    return vehicle_uwb_ceiling_dbm(radio)


def run_scenario(scenario: Scenario, terms: Terms = ALL_TERMS) -> Samples:
    """Drive every unit, fix as often as the medium allows, count errors.

    Units share the anchors, so a round takes as long as all of them
    together need, and every unit is fixed once per round. Errors from
    all of them land in one sample set: the table's rows are about a
    deployment, not about one vehicle.

    ``terms`` says which error sources are live. Everything is, unless a
    caller is dissecting the result; see `yerkon.budget`. Silencing a
    source changes what the world does to the measurements and nothing
    about how the deployment is arranged or how the estimator weighs
    them, which is what makes two such runs comparable.
    """
    rng = np.random.default_rng(scenario.seed)

    deployment = scenario.deployment
    round_s = deployment.round_duration_s()

    # One survey error per anchor, drawn now and held. Three components,
    # because an anchor is wrong in three dimensions and the estimator is
    # told all three as though they were exact.
    survey = {
        anchor.identifier: rng.normal(
            0.0, scenario.anchor_survey_sigma_m, size=3
        )
        if scenario.anchor_survey_sigma_m > 0.0 else np.zeros(3)
        for anchor in deployment.anchors
    }

    horizontal: list[float] = []
    vertical: list[float] = []
    sigmas: list[float] = []
    attempted = 0
    attempted_links = 0
    lost_links = 0

    trackers: dict[str, Optional[TrackingFilter]] = {
        unit.identifier: None for unit in deployment.receivers
    }
    # The map each unit carries: the road's height, wrong in patches.
    # Drawn from its own stream so that switching the aid on or off
    # leaves every ranging draw where it was (ADR-0088).
    maps = {
        unit.identifier: _MapError.drawn(
            unit.journey.road.length_m, scenario.height_aid_sigma_m,
            scenario.height_aid_correlation_m, scenario.seed, index)
        for index, unit in enumerate(deployment.receivers)
    } if scenario.height_aid_sigma_m > 0.0 else {}
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
            # Where the unit is when the round begins. With motion
            # silenced the whole round happens here: every range in it is
            # measured from one place at one instant, which is the
            # snapshot a round only approximates.
            here = unit.journey.position_at(slot_at_s)
            for identifier, anchor, radio in deployment.nearest_to(unit, here):
                attempted_links += 1
                measured_at_s = slot_at_s if terms.motion else at_s
                receiver = unit.terminal(radio, measured_at_s)
                # The survey error is an error in the anchor's position,
                # so what it does to a range is its component along the
                # line to the receiver.
                offset = np.array(receiver.position_m) - np.array(
                    anchor.position_m
                )
                span = float(np.linalg.norm(offset))
                along = (
                    float(np.dot(survey[identifier], offset / span))
                    if span > 0.0 else 0.0
                )

                observation = measure(
                    anchor,
                    receiver,
                    measured_at_s,
                    rng,
                    anchor_id=identifier,
                    clock=deployment.clock,
                    scheme=deployment.scheme,
                    obstruction=scenario.terrain.obstruction_between(
                        anchor.position_m, receiver.position_m
                    ),
                    region=deployment.region,
                    survey_error_m=along,
                    packet_loss=scenario.packet_loss,
                    terms=terms,
                    reply_ceiling_dbm=_reply_ceiling_dbm(
                        unit,
                        anchor.position_m[2] - scenario.terrain.height_at(
                            anchor.position_m[0], anchor.position_m[1]),
                        radio),
                )
                slot_at_s += exchange_duration_s(
                    anchor.radio, deployment.scheme
                ) / deployment.duty_cycle
                if observation is None:
                    lost_links += 1
                elif observation.sigma_m <= scenario.accept_sigma_m:
                    observations.append(observation)
                    sigmas.append(observation.sigma_m)

            fix = _fix_from(
                observations, trackers[unit.identifier], scenario.manoeuvre_m_s2,
                scenario.gate_sigmas,
            )
            if fix is None:
                # A round that produced no position is an outage, and the
                # filter is not carried across it: a receiver that lost
                # the network does not know where it drifted to.
                trackers[unit.identifier] = None
                continue

            tracker, position = fix
            trackers[unit.identifier] = tracker
            if maps:
                # The map's height where the filter thinks the unit is.
                road = unit.journey.road
                along = road.nearest_along(*tracker.state[:2])
                tracker.absorb_height(
                    tracker.at_s,
                    road.surface_height_at(along)
                    + unit.journey.antenna_height_m
                    + maps[unit.identifier].at(along),
                    scenario.height_aid_sigma_m ** 2)
                position = tracker.position_m
            # A position the receiver itself would not stand behind is not
            # offered. It keeps tracking, so the next good round starts
            # from here, but this round is an outage (ADR-0084).
            if tracker.horizontal_sigma_m > scenario.fix_sigma_m:
                continue
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
        median_range_sigma_m=float(np.median(sigmas)) if sigmas else 0.0,
    )


@dataclass(frozen=True)
class _MapError:
    """A map's height error along one road: drawn every ``step_m`` and
    joined smoothly, the same draw for the whole journey.

    Joined with quarter-circle weights rather than a straight line,
    because a straight blend of two independent draws is smaller than
    either halfway between them, and the map would be better there than
    its stated accuracy (ADR-0088)."""

    knots_m: np.ndarray
    step_m: float

    @classmethod
    def drawn(cls, length_m: float, sigma_m: float, step_m: float,
              seed: int, index: int) -> "_MapError":
        count = int(math.ceil(length_m / max(step_m, 1.0))) + 2
        stream = np.random.default_rng([int(seed), 88, int(index)])
        return cls(stream.normal(0.0, sigma_m, size=count), max(step_m, 1.0))

    def at(self, along_m: float) -> float:
        position = max(along_m, 0.0) / self.step_m
        left = min(int(position), len(self.knots_m) - 2)
        turn = (position - left) * math.pi / 2.0
        return float(self.knots_m[left] * math.cos(turn)
                     + self.knots_m[left + 1] * math.sin(turn))


def _fix_from(
    observations: Sequence[RangeObservation],
    tracker: Optional[TrackingFilter],
    manoeuvre_m_s2: float,
    gate_sigmas: float = 0.0,
):
    """Fold one round into a unit's filter, starting it if it is not running."""
    if tracker is None:
        start = trilaterate(observations)
        if start is None:
            return None
        return (TrackingFilter(start, manoeuvre_m_s2=manoeuvre_m_s2,
                               gate_sigmas=gate_sigmas),
                start.position_m)

    if not observations:
        return None
    before = tracker.used
    for observation in observations:
        tracker.absorb(observation)
    if tracker.used == before:
        # Every range was turned away. A filter that disagrees with all of
        # them is more likely the one that is wrong, and one that keeps
        # coasting only drifts further and turns away the next round too:
        # the lockout every gated filter has to guard against. Start again
        # from what this round measured (ADR-0084).
        start = trilaterate(observations)
        if start is None:
            return None
        return (TrackingFilter(start, manoeuvre_m_s2=manoeuvre_m_s2,
                               gate_sigmas=gate_sigmas),
                start.position_m)
    return tracker, tracker.position_m


# --- Where the deployment works at all ------------------------------------


@dataclass(frozen=True)
class CoverageGrid:
    """What each cell of a swept grid gets, by four readings of it.

    The count rather than a yes or no, because one anchor and four
    anchors mean entirely different things and a boolean would throw
    away the distinction ADR-0012 exists to make.

    The other three used to be computed and discarded. The sweep runs a
    full link budget for every anchor at every cell — that is what makes
    it the slowest thing in the project — and then kept one bit of it.
    Keeping the rest costs the bookkeeping and nothing else, and it is
    the difference between a picture of where packets arrive and a
    picture of what a position there would actually be worth (ADR-0044).

    Every layer but `counts` is NaN where there is nothing to report:
    no anchor reaches, or too few for a fix. NaN rather than zero,
    because zero decibels of margin and zero dilution are both answers
    and neither of them is "nothing here".
    """

    #: Anchors in reach at each cell, indexed [row, column].
    counts: np.ndarray
    #: Cell centres, in metres.
    xs: np.ndarray
    ys: np.ndarray
    resolution_m: float
    #: Margin of the strongest link reaching this cell, in dB. This is
    #: the signal question: is there anything audible here, and by how
    #: much. NaN where nothing reaches.
    margin_db: Optional[np.ndarray] = None
    #: Typical ranging sigma among the anchors that reach, in metres —
    #: the median rather than the best, because a fix uses several and
    #: the best one flatters it. NaN where nothing reaches.
    sigma_m: Optional[np.ndarray] = None
    #: Horizontal dilution of precision from the geometry of the anchors
    #: that reach. NaN where fewer than three do, because there is no
    #: dilution until there is a fix (ADR-0040).
    dilution: Optional[np.ndarray] = None

    @property
    def cell_km2(self) -> float:
        return (self.resolution_m / 1000.0) ** 2

    def area_reached_by(self, anchors: int) -> float:
        return float(np.count_nonzero(self.counts >= anchors)) * self.cell_km2

    @property
    def error_m(self) -> Optional[np.ndarray]:
        """What a fix at each cell would be worth, in metres.

        Ranging sigma times dilution: the standard reading of what
        geometry does to a range error, and the same two quantities the
        published HPE column is made of.

        An estimate from geometry, not a simulation. It has no clock
        drift, no packet loss, no solver that failed to settle, and no
        receiver actually driving through. `yerkon table` has all four,
        and this must not be read as agreeing with it (ADR-0001) — it is
        a picture of which ground is hard, drawn from what the sweep
        already knows.
        """
        if self.sigma_m is None or self.dilution is None:
            return None
        return self.sigma_m * self.dilution


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


def sweep_axes(
    deployment: Deployment,
    terrain: Terrain,
    resolution_m: float = 250.0,
    margin_m: float = 12_000.0,
) -> tuple[np.ndarray, np.ndarray]:
    """The cells a coverage sweep will visit, as its x and y axes.

    Apart from the sweep so that whoever needs to know where it will
    paint — the ground mesh drawn under it — can ask without paying for
    the link budget at every cell (ADR-0082).
    """
    positions = [anchor.position_m for anchor in deployment.anchors]
    west = min(p[0] for p in positions) - margin_m
    east = max(p[0] for p in positions) + margin_m
    south = min(p[1] for p in positions) - margin_m
    north = max(p[1] for p in positions) + margin_m
    # The margin is there so that ground reached from the edge anchors is
    # counted. Where the terrain was measured it also runs off the end of
    # the grid, and past the end `height_at` clamps: cells of served
    # ground that nobody surveyed. The urban row reported 31,72 km² of
    # service over a site 8,73 km² in size before this (ADR-0037).
    if terrain.extent_m is not None:
        left, bottom, right, top = terrain.extent_m
        west, east = max(west, left), min(east, right)
        south, north = max(south, bottom), min(north, top)
    return np.arange(west, east, resolution_m), np.arange(south, north, resolution_m)


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
    xs, ys = sweep_axes(deployment, terrain, resolution_m, margin_m)

    anchors = deployment.terminals()
    # Ground is served for a unit carrying whatever the deployment's
    # units carry. A sweep against one waveform would call a tunnel
    # anchor unreachable from a road unit that in fact carries the
    # matching module.
    radios = _sweep_radios(deployment)
    counts = np.zeros((ys.size, xs.size), dtype=int)
    margins = np.full((ys.size, xs.size), np.nan)
    sigmas = np.full((ys.size, xs.size), np.nan)
    dilutions = np.full((ys.size, xs.size), np.nan)

    for row, y in enumerate(ys):
        for column, x in enumerate(xs):
            here = (
                float(x), float(y),
                terrain.height_at(float(x), float(y)) + receiver_height_m,
            )
            reached = 0
            # What the link budget said, rather than only whether it
            # closed. The budget is run either way; this keeps it.
            best_margin = -math.inf
            reaching_sigmas = []
            reaching_at = []
            for _, anchor in anchors:
                radio = audible(anchor, radios)
                if radio is None:
                    continue
                receiver = Terminal(radio, deployment.antenna, here)
                if math.dist(anchor.position_m, here) < 1.0:
                    # Standing on the anchor. No budget to run and no
                    # direction to it either, so it counts towards the
                    # fix and contributes no geometry.
                    reached += 1
                else:
                    budget = evaluate_link(
                        anchor, receiver,
                        obstruction=terrain.obstruction_between(
                            anchor.position_m, receiver.position_m),
                        region=deployment.region,
                    )
                    if budget.closes:
                        best_margin = max(best_margin, budget.margin_db)
                        # Asked only of a link that closes: one that does
                        # not has no ranging precision, and `rf` refuses
                        # to invent one rather than returning a large
                        # number somebody could read as a result.
                        sigma = ranging_sigma_m(budget, anchor.radio)
                        if sigma <= target_sigma_m:
                            reached += 1
                            reaching_sigmas.append(sigma)
                            reaching_at.append(anchor.position_m)
                if reached >= count_up_to:
                    break
            counts[row, column] = reached
            if best_margin > -math.inf:
                margins[row, column] = best_margin
            if reaching_sigmas:
                sigmas[row, column] = float(np.median(reaching_sigmas))
            dilutions[row, column] = dilution_at(
                (float(x), float(y)),
                [(p[0], p[1]) for p in reaching_at],
                math.inf,
            )

    # The ceiling is what "no fix here" looks like inside the dilution
    # module, and NaN is what it looks like everywhere else in this
    # grid. Converted once rather than asking every reader to know both.
    dilutions[dilutions >= DILUTION_CEILING] = np.nan

    return CoverageGrid(counts=counts, xs=xs, ys=ys, resolution_m=resolution_m,
                        margin_db=margins, sigma_m=sigmas,
                        dilution=dilutions)


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
