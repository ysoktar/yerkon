"""Turning ranges into positions, seeing nothing else. See ADR-0003.

This module imports numpy and the observation record. It cannot reach the
world, the link budget, or the ranging exchange, so there is no path by
which it could read the answer it is supposed to be estimating. The
previous codebase's estimator could, and passed its tests anyway.

Two things it must get right, and both come from ADR-0010.

The ranges in a round are not simultaneous. Each exchange takes tens of
milliseconds, so a receiver at a hundred kilometres an hour has moved
metres between the first range and the last. Every measurement is
therefore applied at its own instant, against a state that has been
carried forward to meet it.

There is no height constraint. Anchors stand along a road at similar
heights, which leaves the vertical almost unobservable, and the honest
consequence is a large vertical error rather than a small one bought by
telling the filter an answer it was meant to find.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np

from yerkon.observation import RangeObservation
from yerkon.settings import DEFAULTS

#: Metres per second squared of unmodelled acceleration.
#:
#: A figure nobody supplied, so it comes from the settings file like the
#: rest of them. See `yerkon.settings`.
DEFAULT_MANOEUVRE_M_S2 = DEFAULTS.number("estimator.manoeuvre_m_s2")

#: How far a first fix may sit from the anchors before it is rejected.
#:
#: A least-squares solve on bad geometry can return a point on the far
#: side of the planet rather than failing outright, and a filter started
#: there never recovers.
IMPLAUSIBLE_M = 200_000.0


@dataclass(frozen=True)
class Fix:
    """One position estimate, and how sure of it the estimator is.

    ``covariance_m2`` is the estimator's own claim about its error, which
    is a different thing from the error it actually has. Evaluation
    compares the two; nothing in here does.
    """

    at_s: float
    position_m: tuple[float, float, float]
    covariance_m2: np.ndarray
    #: How many range measurements stand behind it.
    used: int

    @property
    def horizontal_sigma_m(self) -> float:
        return math.sqrt(max(self.covariance_m2[0, 0] + self.covariance_m2[1, 1], 0.0))

    @property
    def vertical_sigma_m(self) -> float:
        return math.sqrt(max(self.covariance_m2[2, 2], 0.0))


# --- A first position from nothing ----------------------------------------


#: Where the least-squares solve starts its damping.
#:
#: Anchors along a road sit at one height, and that leaves the vertical
#: not merely imprecise but ambiguous: a receiver below the anchors and
#: its mirror image above them fit the same ranges almost equally well.
#: An undamped Gauss-Newton step jumps between the two sides forever, so
#: a perfectly ordinary set of ranges comes back as a refusal. Levenberg
#: damping, raised whenever a step makes the fit worse, settles on
#: whichever side the solve started from, which is what a real receiver
#: does.
INITIAL_DAMPING = 1e-3

#: Largest horizontal uncertainty a fix may claim and still be a fix.
#:
#: A least-squares solve on geometry that cannot determine a horizontal
#: axis — anchors in a straight line, say — still returns a point, with
#: a variance that says the point means nothing. That is a failed fix and
#: the availability column should count it as one.
#:
#: The vertical is deliberately not held to this. Anchors on roadside
#: structures leave the height unobservable at kilometre ranges however
#: their mounting heights are mixed, because twenty metres of height
#: spread against four kilometres of baseline is no spread at all. That
#: shows up as a large VPE, which is the true answer, rather than as an
#: outage.
MAX_HORIZONTAL_SIGMA_M = 500.0

#: Absolute ridge on the covariance, in inverse square metres.
#:
#: The normal matrix is near singular in the vertical, and inverting it
#: raw gives either an exception or a number with no meaning. This caps a
#: reported sigma at a thousand metres, which reads as "unobservable"
#: without pretending to a figure.
COVARIANCE_RIDGE = 1e-6


def _weighted_cost(
    position: np.ndarray,
    anchors: np.ndarray,
    measured: np.ndarray,
    weights: np.ndarray,
) -> float:
    residual = measured - np.linalg.norm(position - anchors, axis=1)
    return float(np.sum(weights * residual * residual))


def trilaterate(
    observations: Sequence[RangeObservation],
    guess_m: Optional[tuple[float, float, float]] = None,
    iterations: int = 100,
    tolerance_m: float = 0.01,
) -> Optional[Fix]:
    """A position from one batch of ranges, by weighted least squares.

    Used to start the filter, and useful on its own for showing what a
    snapshot solution costs: it treats measurements taken tens of
    milliseconds apart as though they arrived together, which is exactly
    the assumption ADR-0010 says is wrong.

    Nothing here constrains the height. The solve is damped so that a
    barely observable vertical settles instead of oscillating, which is a
    statement about the arithmetic rather than about where the receiver
    is; the vertical error that comes out stays as large as the geometry
    makes it.

    Returns nothing when there are too few ranges, when the solve does
    not settle, or when it settles somewhere absurd. A refusal is a
    result: it is what the availability column counts.
    """
    if len(observations) < 4:
        # Three ranges pin a point in three dimensions only up to a
        # reflection through the plane of the anchors, and these anchors
        # are nearly in a plane.
        return None

    anchors = np.array([o.anchor_position_m for o in observations], dtype=float)
    measured = np.array([o.measured_range_m for o in observations], dtype=float)
    weights = np.array([1.0 / o.variance_m2 for o in observations], dtype=float)

    position = (
        np.array(guess_m, dtype=float)
        if guess_m is not None
        else anchors.mean(axis=0) + np.array([0.0, 0.0, -10.0])
    )

    cost = _weighted_cost(position, anchors, measured, weights)
    damping = INITIAL_DAMPING
    settled = False

    for _ in range(iterations):
        offsets = position - anchors
        distances = np.linalg.norm(offsets, axis=1)
        if np.any(distances < 1e-6):
            return None

        jacobian = offsets / distances[:, None]
        residual = measured - distances
        weighted = jacobian * weights[:, None]
        curvature = jacobian.T @ weighted
        gradient = weighted.T @ residual

        # Try a step. A step that makes the fit worse is not taken; the
        # damping goes up instead, which shortens the next one and turns
        # the search from Gauss-Newton toward gradient descent.
        for _ in range(12):
            normal = curvature + damping * np.diag(np.maximum(np.diag(curvature), 1e-12))
            try:
                step = np.linalg.solve(normal, gradient)
            except np.linalg.LinAlgError:
                return None

            candidate = position + step
            candidate_cost = _weighted_cost(candidate, anchors, measured, weights)
            if candidate_cost <= cost:
                position, cost = candidate, candidate_cost
                damping = max(damping / 3.0, 1e-9)
                break
            damping *= 5.0
        else:
            # No step of any length improved the fit. That is a minimum.
            settled = True
            break

        if float(np.linalg.norm(step)) < tolerance_m:
            settled = True
            break

    if not settled:
        return None

    if np.linalg.norm(position - anchors.mean(axis=0)) > IMPLAUSIBLE_M:
        return None

    offsets = position - anchors
    distances = np.linalg.norm(offsets, axis=1)
    jacobian = offsets / distances[:, None]
    normal = (
        jacobian.T @ (jacobian * weights[:, None]) + COVARIANCE_RIDGE * np.eye(3)
    )
    try:
        covariance = np.linalg.inv(normal)
    except np.linalg.LinAlgError:
        return None

    fix = Fix(
        at_s=observations[-1].at_s,
        position_m=tuple(float(value) for value in position),
        covariance_m2=covariance,
        used=len(observations),
    )
    if fix.horizontal_sigma_m > MAX_HORIZONTAL_SIGMA_M:
        return None
    return fix


# --- Carrying a position through time -------------------------------------


class TrackingFilter:
    """A constant-velocity filter fed one range at a time.

    Each measurement is a scalar update applied at its own instant, so
    ranges arriving forty-eight milliseconds apart are treated as the
    separate events they are rather than as a simultaneous set. Between
    them the state coasts and its uncertainty grows.

    The state is position and velocity in three dimensions. Nothing
    constrains the height: the vertical is left to whatever the geometry
    can support, which on a road is not much, and the filter reports a
    large vertical uncertainty rather than a small false one.
    """

    def __init__(
        self,
        start: Fix,
        manoeuvre_m_s2: float = DEFAULT_MANOEUVRE_M_S2,
        initial_speed_sigma_m_s: float = 30.0,
    ) -> None:
        if manoeuvre_m_s2 <= 0.0:
            raise ValueError("a filter that expects no surprises ignores its inputs")

        self.manoeuvre_m_s2 = manoeuvre_m_s2
        self.at_s = start.at_s
        self.state = np.zeros(6)
        self.state[:3] = start.position_m

        self.covariance = np.zeros((6, 6))
        self.covariance[:3, :3] = start.covariance_m2
        # Nothing is known about the velocity yet, so say so rather than
        # implying the receiver is stationary.
        self.covariance[3:, 3:] = np.eye(3) * initial_speed_sigma_m_s ** 2
        self.used = start.used

    # -- what a person asks it -------------------------------------------

    @property
    def position_m(self) -> tuple[float, float, float]:
        return tuple(float(value) for value in self.state[:3])

    @property
    def velocity_m_s(self) -> tuple[float, float, float]:
        return tuple(float(value) for value in self.state[3:])

    def fix(self) -> Fix:
        """Where it thinks the receiver is, at the last measurement."""
        return Fix(
            at_s=self.at_s,
            position_m=self.position_m,
            covariance_m2=self.covariance[:3, :3].copy(),
            used=self.used,
        )

    def fix_at(self, at_s: float) -> Fix:
        """Where it thinks the receiver is at some other instant.

        Coasting to a common time is how a round of measurements taken
        over a quarter of a second becomes one position that means
        something. The uncertainty grows with the gap, which is the
        honest cost of the coast.
        """
        state, covariance = self._coast(at_s - self.at_s)
        return Fix(
            at_s=at_s,
            position_m=tuple(float(value) for value in state[:3]),
            covariance_m2=covariance[:3, :3],
            used=self.used,
        )

    def absorb(self, observation: RangeObservation) -> None:
        """Take one range in, at the instant it was measured."""
        self.state, self.covariance = self._coast(observation.at_s - self.at_s)
        self.at_s = observation.at_s

        anchor = np.array(observation.anchor_position_m, dtype=float)
        offset = self.state[:3] - anchor
        distance = float(np.linalg.norm(offset))
        if distance < 1e-6:
            # The estimate has landed on the anchor; the range gradient is
            # undefined there and the update would be meaningless.
            return

        jacobian = np.zeros(6)
        jacobian[:3] = offset / distance

        innovation = observation.measured_range_m - distance
        innovation_variance = (
            float(jacobian @ self.covariance @ jacobian) + observation.variance_m2
        )
        gain = (self.covariance @ jacobian) / innovation_variance

        self.state = self.state + gain * innovation
        spread = np.eye(6) - np.outer(gain, jacobian)
        # Joseph form: stays symmetric and positive definite over
        # thousands of scalar updates, which the short form does not.
        self.covariance = (
            spread @ self.covariance @ spread.T
            + np.outer(gain, gain) * observation.variance_m2
        )
        self.used += 1

    # -- the model between measurements ----------------------------------

    def _coast(self, gap_s: float) -> tuple[np.ndarray, np.ndarray]:
        """Carry the state forward, and let the uncertainty grow."""
        if gap_s <= 0.0:
            return self.state.copy(), self.covariance.copy()

        transition = np.eye(6)
        transition[:3, 3:] = np.eye(3) * gap_s

        variance = self.manoeuvre_m_s2 ** 2
        process = np.zeros((6, 6))
        process[:3, :3] = np.eye(3) * (gap_s ** 4 / 4.0) * variance
        process[:3, 3:] = np.eye(3) * (gap_s ** 3 / 2.0) * variance
        process[3:, :3] = process[:3, 3:]
        process[3:, 3:] = np.eye(3) * (gap_s ** 2) * variance

        return (
            transition @ self.state,
            transition @ self.covariance @ transition.T + process,
        )


# --- The whole journey ----------------------------------------------------


def track(
    observations: Iterable[RangeObservation],
    round_size: int = 4,
    manoeuvre_m_s2: float = DEFAULT_MANOEUVRE_M_S2,
) -> tuple[Fix, ...]:
    """Every fix a stream of ranges supports, in order.

    Waits for enough ranges to place the receiver at all, then emits a
    fix after each subsequent measurement. Ranges arriving before the
    filter has started are used for the start and nothing else.

    Fixes stop being produced if the ranges do. Nothing here invents one:
    a gap in the observations is a gap in the track, which is what the
    availability column counts.
    """
    ordered = sorted(observations, key=lambda o: o.at_s)
    if round_size < 4:
        raise ValueError("fewer than four ranges cannot place a point in three axes")

    start = None
    for count in range(round_size, len(ordered) + 1):
        start = trilaterate(ordered[:count])
        if start is not None:
            break
    if start is None:
        return ()

    filter_ = TrackingFilter(start, manoeuvre_m_s2=manoeuvre_m_s2)
    fixes = [filter_.fix()]
    for observation in ordered[count:]:
        filter_.absorb(observation)
        fixes.append(filter_.fix())
    return tuple(fixes)
