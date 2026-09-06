"""Evidence provenance for every reported result.

The benchmark compares numbers from very different sources: a datasheet
value, a published field test, a Monte Carlo simulation, a hardware
measurement. These are not interchangeable. Every result in this project
carries an :class:`EvidenceRecord` so a reader can tell what kind of claim
they are looking at, and no code path is allowed to merge two evidence
types into one without saying so.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EvidenceType(str, Enum):
    """Controlled vocabulary for where a number came from.

    Do not add a new member without also adding it to every place that
    enumerates the vocabulary (see test_evidence.py).
    """

    MEASURED_HARDWARE = "MEASURED_HARDWARE"
    SIMULATED_MONTE_CARLO = "SIMULATED_MONTE_CARLO"
    HARDWARE_CALIBRATED_MODEL = "HARDWARE_CALIBRATED_MODEL"
    MATLAB_WAVEFORM = "MATLAB_WAVEFORM"
    ANALYTIC_BOUND = "ANALYTIC_BOUND"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    OFFICIAL_SPECIFICATION = "OFFICIAL_SPECIFICATION"
    PUBLISHED_EXPERIMENT = "PUBLISHED_EXPERIMENT"
    SOFTWARE_REFERENCE = "SOFTWARE_REFERENCE"
    COMMUNITY_REFERENCE = "COMMUNITY_REFERENCE"


# Evidence types below this authority level must never overwrite or silently
# resolve a conflict against a type above it. This is guidance data, not an
# ordering the code enforces on its own; see ProvenanceConflict below for the
# actual conflict-flagging mechanism.
AUTHORITY_RANK = {
    EvidenceType.MEASURED_HARDWARE: 9,
    EvidenceType.OFFICIAL_SPECIFICATION: 8,
    EvidenceType.HARDWARE_CALIBRATED_MODEL: 7,
    EvidenceType.PUBLISHED_EXPERIMENT: 6,
    EvidenceType.MATLAB_WAVEFORM: 5,
    EvidenceType.ANALYTIC_BOUND: 4,
    EvidenceType.ANALYTIC_MODEL: 4,
    EvidenceType.SIMULATED_MONTE_CARLO: 3,
    EvidenceType.SOFTWARE_REFERENCE: 2,
    EvidenceType.COMMUNITY_REFERENCE: 1,
}


@dataclass(frozen=True)
class EvidenceRecord:
    """Provenance attached to one result, row, or field value.

    Attributes:
        evidence_type: one member of :class:`EvidenceType`.
        source_name: short human-readable name of the source.
        source_url: URL of the source, if it has one. Empty string if the
            source is internal to this project (for example, our own
            Monte Carlo simulator).
        source_scope: what the source actually covers and does not cover.
            Required and must be non-empty: this is what stops a single
            long-range calibration result from being read as a universal
            accuracy claim.
        retrieved_date: ISO date the source was checked, if applicable.
        confidence: free-text confidence note, optional.
        caveats: free-text caveats beyond source_scope, optional.
    """

    evidence_type: EvidenceType
    source_name: str
    source_url: str = ""
    source_scope: str = ""
    retrieved_date: str = ""
    confidence: str = ""
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
            "retrieved_date": self.retrieved_date,
            "confidence": self.confidence,
            "caveats": self.caveats,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvidenceRecord":
        return cls(
            evidence_type=EvidenceType(d["evidence_type"]),
            source_name=d["source_name"],
            source_url=d.get("source_url", ""),
            source_scope=d["source_scope"],
            retrieved_date=d.get("retrieved_date", ""),
            confidence=d.get("confidence", ""),
            caveats=d.get("caveats", ""),
        )


@dataclass(frozen=True)
class ProvenanceConflict:
    """A flagged disagreement between two evidence records about the same fact.

    Used, for example, when a manufacturer claims ranging support for a part
    but a verified radio IC or firmware check disagrees.
    """

    field_name: str
    claimed_value: str
    verified_value: str
    note: str
    flagged: bool = field(default=True)
