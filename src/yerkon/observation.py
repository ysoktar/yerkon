"""The only thing the estimator is allowed to see. See ADR-0003.

This module exists to be shallow. It imports nothing from the rest of the
project, so a module that imports it gains no path to the world, the
truth, or the link budget that produced the number. The previous
codebase's estimator could read the receiver's true position and passed
its tests anyway; keeping the observation type in its own module is what
makes that impossible to repeat by accident.

If a quantity is not on one of these records, the estimator cannot use
it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RangeObservation:
    """One distance measurement, as the receiver knows it.

    Carries the anchor's *surveyed* position, which is a published fact
    about a fixed installation, not a secret about where anything is
    moving. Carries a variance rather than a standard deviation because
    that is what a weighted solve wants and converting on every use
    invites the square root being forgotten.
    """

    #: Receiver clock time of the measurement, in seconds. Measurements
    #: in one round are not simultaneous and this is how far apart they
    #: are.
    at_s: float
    #: Where the anchor stands, from the survey.
    anchor_position_m: tuple[float, float, float]
    #: Distance the exchange reported, in metres. Includes whatever error
    #: the exchange had; nothing here is corrected against truth.
    measured_range_m: float
    #: The measurement's own uncertainty, in square metres.
    variance_m2: float
    #: Which anchor, for bookkeeping. Never a position.
    anchor_id: str = ""

    def __post_init__(self) -> None:
        if self.measured_range_m < 0.0:
            raise ValueError("a measured range cannot be negative")
        if self.variance_m2 <= 0.0:
            raise ValueError(
                "a measurement with no uncertainty would be weighted infinitely"
            )

    @property
    def sigma_m(self) -> float:
        return self.variance_m2 ** 0.5
