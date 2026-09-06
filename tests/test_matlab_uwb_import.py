"""Import of MATLAB UWB waveform ranging results.

This project has no MATLAB license, so these tests exercise the importer
against a synthetic CSV matching the schema matlab/uwb_waveform_ranging.m
is documented to produce (matlab/README.md), not real MATLAB output. Every
imported row must be tagged MATLAB_WAVEFORM, never MEASURED_HARDWARE or
SIMULATED_MONTE_CARLO, and the "never executed" caveat must travel with
the evidence, not just live in a doc file.
"""
import io

import pytest

from locbench3d.core.evidence import EvidenceType
from locbench3d.hardware.matlab_uwb_import import (
    MATLAB_UWB_FIELDS,
    load_matlab_uwb_csv,
)

SAMPLE_CSV = """measurement_id,true_range_m,estimated_range_m,error_m,bandwidth_hz,center_freq_hz,snr_db,sample_rate_hz,multipath_profile,trial,seed
1,1,1.02,0.02,499200000,6489600000,15,40000000000,"[3 7] ns @ [0.6 0.3]",1,100101
2,1,0.95,-0.05,499200000,6489600000,15,40000000000,"[3 7] ns @ [0.6 0.3]",2,100102
3,51,NaN,NaN,499200000,6489600000,15,40000000000,"[3 7] ns @ [0.6 0.3]",1,126001
"""


def test_field_list_covers_the_documented_schema():
    required = {
        "measurement_id", "true_range_m", "estimated_range_m", "error_m",
        "bandwidth_hz", "center_freq_hz", "snr_db", "sample_rate_hz",
        "multipath_profile", "trial", "seed",
    }
    assert required.issubset(set(MATLAB_UWB_FIELDS))


def test_load_matlab_uwb_csv_parses_rows():
    records = load_matlab_uwb_csv(io.StringIO(SAMPLE_CSV))
    assert len(records) == 3
    assert records[0].true_range_m == pytest.approx(1.0)
    assert records[0].estimated_range_m == pytest.approx(1.02)
    assert records[0].error_m == pytest.approx(0.02)


def test_nan_estimate_becomes_none_not_a_float_nan():
    """A failed detection (NaN in MATLAB) must not silently become 0 or
    propagate as an unfilterable float NaN; it becomes an explicit None,
    consistent with every other importer in this project."""
    records = load_matlab_uwb_csv(io.StringIO(SAMPLE_CSV))
    failed = records[2]
    assert failed.estimated_range_m is None
    assert failed.error_m is None
    assert failed.true_range_m == pytest.approx(51.0)


def test_every_record_is_tagged_matlab_waveform_evidence():
    records = load_matlab_uwb_csv(io.StringIO(SAMPLE_CSV))
    for r in records:
        assert r.evidence.evidence_type == EvidenceType.MATLAB_WAVEFORM


def test_evidence_scope_states_the_script_was_never_executed():
    records = load_matlab_uwb_csv(io.StringIO(SAMPLE_CSV))
    for r in records:
        scope = r.evidence.source_scope.lower()
        assert "never" in scope and "executed" in scope


def test_evidence_type_is_not_measured_hardware_or_simulated_monte_carlo():
    records = load_matlab_uwb_csv(io.StringIO(SAMPLE_CSV))
    for r in records:
        assert r.evidence.evidence_type != EvidenceType.MEASURED_HARDWARE
        assert r.evidence.evidence_type != EvidenceType.SIMULATED_MONTE_CARLO


def test_missing_required_column_raises():
    bad_csv = "true_range_m,error_m\n1,0.02\n"
    with pytest.raises(ValueError):
        load_matlab_uwb_csv(io.StringIO(bad_csv))
