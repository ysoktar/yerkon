"""Evidence provenance must be preserved and never silently mixed."""
import pytest

from locbench3d.core.evidence import EvidenceRecord, EvidenceType


def test_evidence_type_is_controlled_vocabulary():
    names = {e.value for e in EvidenceType}
    assert names == {
        "MEASURED_HARDWARE",
        "SIMULATED_MONTE_CARLO",
        "HARDWARE_CALIBRATED_MODEL",
        "MATLAB_WAVEFORM",
        "ANALYTIC_BOUND",
        "ANALYTIC_MODEL",
        "OFFICIAL_SPECIFICATION",
        "PUBLISHED_EXPERIMENT",
        "SOFTWARE_REFERENCE",
        "COMMUNITY_REFERENCE",
    }


def test_evidence_record_requires_source_scope():
    with pytest.raises(ValueError):
        EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson SX1280 field test",
            source_url="https://stuartsprojects.github.io/2019/04/26/"
            "Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html",
            source_scope="",  # empty scope is rejected
        )


def test_evidence_record_round_trips_to_dict():
    rec = EvidenceRecord(
        evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
        source_name="Semtech SX1280 product page",
        source_url="https://www.semtech.com/products/wireless-rf/lora-connect/sx1280",
        source_scope="Datasheet nominal values only, not a project measurement.",
        retrieved_date="2026-09-06",
        confidence="high",
    )
    d = rec.to_dict()
    assert d["evidence_type"] == "OFFICIAL_SPECIFICATION"
    assert d["source_url"].startswith("https://www.semtech.com")
    back = EvidenceRecord.from_dict(d)
    assert back == rec


def test_evidence_types_are_not_equivalence_classes():
    """A CRLB is not measured accuracy and a spec is not a project measurement."""
    crlb = EvidenceType.ANALYTIC_BOUND
    measured = EvidenceType.MEASURED_HARDWARE
    spec = EvidenceType.OFFICIAL_SPECIFICATION
    assert crlb != measured
    assert spec != measured
    assert EvidenceType.PUBLISHED_EXPERIMENT != measured
