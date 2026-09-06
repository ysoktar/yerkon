"""Raw SX1280 measurement schema, CSV import, and failed-attempt handling."""
import io

import pytest

from locbench3d.core.evidence import EvidenceType
from locbench3d.hardware.sx1280_measurements import (
    RANGING_MEASUREMENT_FIELDS,
    RangingMeasurement,
    load_measurements_csv,
)


def test_measurement_field_list_covers_required_fields():
    required = {
        "timestamp",
        "measurement_id",
        "experiment_id",
        "test_id",
        "anchor_id",
        "tag_id",
        "hardware_profile_anchor",
        "hardware_profile_tag",
        "hardware_revision_anchor",
        "hardware_revision_tag",
        "radio_ic_anchor",
        "radio_ic_tag",
        "software_or_driver_identity",
        "firmware_identity",
        "true_range_m",
        "raw_ranging_value",
        "reported_range_m",
        "corrected_range_m",
        "range_error_m",
        "range_error_pct",
        "center_freq_hz",
        "measured_freq_error_hz",
        "bandwidth_hz",
        "spreading_factor",
        "coding_rate",
        "tx_power_dbm",
        "calibration_value",
        "calibration_profile",
        "ranging_rssi_dbm",
        "packet_rssi_dbm",
        "snr_db",
        "los_state",
        "environment",
        "temperature_c",
        "antenna_info",
        "orientation_anchor",
        "orientation_tag",
        "success",
        "timeout",
        "exchange_duration_s",
        "ground_truth_system",
        "ground_truth_uncertainty_m",
        "notes",
    }
    assert required.issubset(set(RANGING_MEASUREMENT_FIELDS))


SAMPLE_CSV = """measurement_id,timestamp,true_range_m,reported_range_m,success,timeout,center_freq_hz,bandwidth_hz,spreading_factor,evidence_type,source_name,source_scope
m1,2026-01-01T00:00:00Z,100.0,103.0,true,false,2445000000,406250,10,PUBLISHED_EXPERIMENT,example,example scope
m2,2026-01-01T00:00:05Z,100.0,,false,true,2445000000,406250,10,PUBLISHED_EXPERIMENT,example,example scope
"""


def test_load_measurements_csv_round_trips_and_keeps_failed_rows():
    measurements = load_measurements_csv(io.StringIO(SAMPLE_CSV))
    assert len(measurements) == 2
    ok, timed_out = measurements
    assert ok.success is True
    assert ok.reported_range_m == pytest.approx(103.0)
    assert timed_out.success is False
    assert timed_out.timeout is True
    # A timed-out exchange has no reported range; it must stay None, not 0.
    assert timed_out.reported_range_m is None


def test_missing_optional_field_is_none_not_zero():
    measurements = load_measurements_csv(io.StringIO(SAMPLE_CSV))
    for m in measurements:
        if m.snr_db is None:
            continue
        assert m.snr_db != 0 or "snr_db" in SAMPLE_CSV  # guard: no invented 0s


def test_range_error_is_computed_when_missing_and_possible():
    measurements = load_measurements_csv(io.StringIO(SAMPLE_CSV))
    ok = measurements[0]
    assert ok.range_error_m == pytest.approx(3.0)
    assert ok.range_error_pct == pytest.approx(3.0)


def test_evidence_type_round_trips_from_csv():
    measurements = load_measurements_csv(io.StringIO(SAMPLE_CSV))
    for m in measurements:
        assert m.evidence.evidence_type == EvidenceType.PUBLISHED_EXPERIMENT


def test_failed_attempts_are_not_dropped_by_the_loader():
    measurements = load_measurements_csv(io.StringIO(SAMPLE_CSV))
    failures = [m for m in measurements if not m.success]
    assert len(failures) == 1
