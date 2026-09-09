"""Where a number came from, carried alongside the number.

Every constant in this project is one of four things, and a reader has to
be able to tell which without leaving the code. A datasheet figure and an
engineering guess should not look alike.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Provenance(str, Enum):
    """How much weight a number can carry."""

    DATASHEET = "DATASHEET"
    """Published by whoever makes the part. The strongest thing here."""

    MEASUREMENT = "MEASUREMENT"
    """Someone switched hardware on and wrote down what happened."""

    STANDARD = "STANDARD"
    """A regulation or a published standard."""

    DERIVED = "DERIVED"
    """Computed from other sourced numbers by stated physics."""

    ASSUMPTION = "ASSUMPTION"
    """This project chose it. No source exists."""


@dataclass(frozen=True)
class Sourced:
    """A value and the reason to believe it."""

    value: float
    unit: str
    provenance: Provenance
    source: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("a Sourced value needs a source")
        if self.provenance is Provenance.ASSUMPTION and not self.note.strip():
            raise ValueError(
                "an assumption needs a note saying what it rests on"
            )

    def __float__(self) -> float:
        return float(self.value)
