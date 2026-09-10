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

    DESIGN = "DESIGN"
    """A deployment choice somebody made, not a quantity anybody measured.

    Anchor spacing, how much ground a row covers, how many anchors a
    round polls. These are not placeholders waiting for a measurement —
    measuring them is meaningless, because they are the thing being
    decided. They live in the same file as everything else so that one
    place changes every number in the table, and they are counted apart
    from the assumptions so that "99 % of this costing rests on figures
    nobody supplied" keeps meaning what it says.
    """

    ASSUMPTION = "ASSUMPTION"
    """This project chose it. No source exists."""


@dataclass(frozen=True)
class Sourced:
    """A value and the reason to believe it.

    Usually a number. Sometimes a name — which fetched ground a row
    stands on is as much a figure that shapes the study as the spacing of
    its anchors, and keeping it out of the file meant an option could
    claim to move a row onto other terrain and silently not (ADR-0027).
    """

    value: "float | str"
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
        if self.provenance is Provenance.DESIGN and not self.note.strip():
            raise ValueError(
                "a design choice needs a note saying why it was chosen"
            )

    @property
    def is_text(self) -> bool:
        return isinstance(self.value, str)

    def __float__(self) -> float:
        if self.is_text:
            raise TypeError(
                "{!r} is a name, not a number. Ask for its text."
                .format(self.value)
            )
        return float(self.value)
