"""GNSS fix schema and CSV import.

Constellation set, signal bands, positioning mode, and fix state must stay
separate fields, never collapsed into one category, and signal-in-space
error must never be reported under the same field as user position error.
"""
import io

import pytest

from locbench3d.gnss.model import (
    FixState,
    GnssConstellation,
    PositioningMode,
    load_gnss_log_csv,
)


SAMPLE_CSV = """timestamp,receiver_hardware,constellation_set,signal_bands,positioning_mode,fix_state,satellites_tracked,satellites_used,hdop,vdop,pdop,lat_deg,lon_deg,alt_m,horizontal_error_m,vertical_error_m,evidence_type,source_name,source_scope
2026-01-01T00:00:00Z,u-blox ZED-F9P,GPS|GALILEO,L1|L5,RTK_FIXED,RTK_FIXED,22,18,0.7,1.1,1.3,47.0,8.0,500.0,0.02,0.04,SIMULATED_MONTE_CARLO,example,synthetic example log for import testing only
2026-01-01T00:00:01Z,u-blox ZED-F9P,GPS|GALILEO,L1|L5,RTK_FIXED,RTK_FLOAT,21,17,0.8,1.2,1.4,47.0,8.0,500.0,,,SIMULATED_MONTE_CARLO,example,synthetic example log for import testing only
"""


def test_load_gnss_log_parses_constellation_set_as_list():
    fixes = load_gnss_log_csv(io.StringIO(SAMPLE_CSV))
    assert fixes[0].constellation_set == [
        GnssConstellation.GPS,
        GnssConstellation.GALILEO,
    ]


def test_positioning_mode_and_fix_state_are_independent_fields():
    fixes = load_gnss_log_csv(io.StringIO(SAMPLE_CSV))
    first, second = fixes
    assert first.positioning_mode == PositioningMode.RTK_FIXED
    assert first.fix_state == FixState.RTK_FIXED
    # Second epoch: still configured for RTK_FIXED mode, but the actual
    # achieved fix state has dropped to float. These must not be forced
    # to match.
    assert second.positioning_mode == PositioningMode.RTK_FIXED
    assert second.fix_state == FixState.RTK_FLOAT


def test_missing_error_fields_stay_none_not_zero():
    fixes = load_gnss_log_csv(io.StringIO(SAMPLE_CSV))
    assert fixes[1].horizontal_error_m is None
    assert fixes[1].vertical_error_m is None


def test_dop_values_are_parsed():
    fixes = load_gnss_log_csv(io.StringIO(SAMPLE_CSV))
    assert fixes[0].hdop == pytest.approx(0.7)
    assert fixes[0].vdop == pytest.approx(1.1)
    assert fixes[0].pdop == pytest.approx(1.3)


def test_evidence_survives_import():
    fixes = load_gnss_log_csv(io.StringIO(SAMPLE_CSV))
    for fix in fixes:
        assert fix.evidence is not None
        assert fix.evidence.source_scope


def test_gps_and_rtk_are_not_the_same_category():
    """GPS is a constellation; RTK_FIXED is a positioning mode. A fix using
    GPS alone in standalone mode and a fix using GPS with RTK must be
    distinguishable by positioning_mode, not conflated as both 'GPS'."""
    assert GnssConstellation.GPS != PositioningMode.RTK_FIXED
    assert "GPS" not in [m.value for m in PositioningMode]
