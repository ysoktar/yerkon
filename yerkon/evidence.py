"""Where every number in the output table came from.

The comparison table mixes numbers of very different standing: a resampled
real measurement, a value copied out of the YERKON presentation, and a
parameter this project chose because nobody published one. Those are not
interchangeable, and a table that prints them in the same font without
saying which is which invites the reader to trust all of them equally.

Every scenario parameter and every simulated result therefore carries an
:class:`EvidenceRecord`. ``docs/EVIDENCE.md`` lists what each type covers.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceType(str, Enum):
    """Controlled vocabulary for the standing of a number.

    Ordered here from strongest to weakest. Nothing in the code enforces an
    ordering; the vocabulary exists so a reader can apply their own.
    """

    PUBLISHED_EXPERIMENT = "PUBLISHED_EXPERIMENT"
    """Someone measured it and published the measurement."""

    HARDWARE_CALIBRATED_MODEL = "HARDWARE_CALIBRATED_MODEL"
    """A model whose error distribution is drawn from real measurements."""

    DESIGN_DOCUMENT = "DESIGN_DOCUMENT"
    """Taken from the YERKON presentation: prices, node counts, target specs.
    A design target is a statement of intent, not a measured result."""

    SIMULATED_MONTE_CARLO = "SIMULATED_MONTE_CARLO"
    """Produced by this project's simulation, from a configured (not
    hardware-calibrated) error model."""

    ENGINEERING_ASSUMPTION = "ENGINEERING_ASSUMPTION"
    """Chosen by this project because no source supplies it: link ranges,
    NLOS rates, mounting heights, anchor spacing. Defensible, unverified."""


@dataclass(frozen=True)
class EvidenceRecord:
    """Provenance attached to one parameter or one result.

    ``source_scope`` is required and must be non-empty. It states what the
    source covers and, more importantly, what it does not: it is the field
    that stops one short-range hobbyist dataset from being read as a
    general accuracy claim.
    """

    evidence_type: EvidenceType
    source_name: str
    source_url: str = ""
    source_scope: str = ""
    caveats: str = ""

    def __post_init__(self) -> None:
        if not self.source_scope or not self.source_scope.strip():
            raise ValueError(
                "EvidenceRecord.source_scope must state what the source "
                "covers; empty scope is not allowed"
            )
        if not self.source_name or not self.source_name.strip():
            raise ValueError("EvidenceRecord.source_name must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_type": self.evidence_type.value,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_scope": self.source_scope,
            "caveats": self.caveats,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvidenceRecord":
        return cls(
            evidence_type=EvidenceType(d["evidence_type"]),
            source_name=d["source_name"],
            source_url=d.get("source_url", ""),
            source_scope=d["source_scope"],
            caveats=d.get("caveats", ""),
        )


def assumption(name: str, scope: str) -> EvidenceRecord:
    """Shorthand for a parameter this project chose itself."""
    return EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name=name,
        source_scope=scope,
    )


def from_deck(name: str, scope: str) -> EvidenceRecord:
    """Shorthand for a value taken from the YERKON presentation."""
    return EvidenceRecord(
        evidence_type=EvidenceType.DESIGN_DOCUMENT,
        source_name=name,
        source_scope=scope,
    )
