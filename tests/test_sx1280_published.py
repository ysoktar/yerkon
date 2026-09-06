"""Stuart Robinson's published SX1280 ranging field observations.

These are PUBLISHED_EXPERIMENT evidence, not project measurements, and one
long-range calibrated result must not be read as a universal accuracy
claim.
"""
from locbench3d.core.evidence import EvidenceType
from locbench3d.hardware.sx1280_published import (
    ROBINSON_CALIBRATION_NOTES,
    ROBINSON_RANGING_OBSERVATIONS,
)


def test_short_range_table_has_six_observations():
    assert len(ROBINSON_RANGING_OBSERVATIONS) == 6


def test_observations_match_published_table():
    expected = [
        (0.0, 4.4, 4.4),
        (50.0, 57.6, 7.6),
        (100.0, 103.0, 3.0),
        (150.0, 148.0, -2.0),
        (200.0, 201.0, 1.0),
        (250.0, 253.0, 3.0),
    ]
    for obs, (truth, indicated, err) in zip(ROBINSON_RANGING_OBSERVATIONS, expected):
        assert obs.true_range_m == truth
        assert obs.indicated_range_m == indicated
        assert obs.error_m == err
        assert obs.evidence.evidence_type == EvidenceType.PUBLISHED_EXPERIMENT


def test_all_observations_share_the_same_primary_source():
    urls = {obs.evidence.source_url for obs in ROBINSON_RANGING_OBSERVATIONS}
    assert urls == {
        "https://stuartsprojects.github.io/2019/04/26/"
        "Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html"
    }


def test_long_range_calibration_notes_are_not_labeled_measured():
    for note in ROBINSON_CALIBRATION_NOTES:
        assert note.evidence.evidence_type == EvidenceType.PUBLISHED_EXPERIMENT
        assert note.evidence.evidence_type != EvidenceType.MEASURED_HARDWARE


def test_89km_reception_is_flagged_as_not_a_verified_ranging_result():
    matches = [
        n for n in ROBINSON_CALIBRATION_NOTES if "89.237" in n.description
        or "89.237" in n.label
    ]
    assert matches, "expected a note covering the ~89.237 km reception"
    for n in matches:
        assert n.is_verified_ranging_result is False


def test_4point4km_203kbps_is_a_communication_benchmark_not_ranging_accuracy():
    matches = [n for n in ROBINSON_CALIBRATION_NOTES if "203" in n.label]
    assert matches
    for n in matches:
        assert n.is_verified_ranging_result is False
        assert "communication" in n.description.lower()


def test_calibration_factor_note_present_with_scope():
    matches = [n for n in ROBINSON_CALIBRATION_NOTES if "0.1803" in n.description]
    assert matches
    for n in matches:
        assert n.evidence.source_scope


def test_one_calibration_result_does_not_generalize():
    """No note in this table may claim its number as a universal SX1280
    accuracy figure; each must carry scope text saying what it does and does
    not cover."""
    for n in ROBINSON_CALIBRATION_NOTES:
        assert n.evidence.source_scope.strip() != ""
