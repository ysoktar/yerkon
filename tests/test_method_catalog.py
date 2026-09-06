"""Method catalog and applicability matrix.

Distinguishes methods with a native simulator here from methods that rely
on sourced/imported evidence, and records mathematical-minimum vs
preferred-benchmark anchor counts separately.
"""
from locbench3d.methods.catalog import (
    METHOD_CATALOG,
    applicability_matrix,
    get_method,
)


def test_catalog_covers_required_local_radio_methods():
    required = {
        "SX1280_RANGING",
        "UWB_SS_TWR",
        "UWB_DS_TWR",
        "TDOA",
        "TOA",
        "TOF",
        "GENERIC_RTT",
        "WIFI_RTT_FTM",
        "BLE_AOA",
        "BLE_AOD",
        "RSSI_TRILATERATION",
        "FINGERPRINTING",
        "RFID",
        "ACOUSTIC_RANGING",
    }
    assert required.issubset(METHOD_CATALOG.keys())


def test_twr_minimum_and_preferred_anchor_counts():
    m = get_method("UWB_SS_TWR")
    assert m.mathematical_minimum_anchors == 4
    assert m.preferred_benchmark_anchors == 5


def test_pairwise_ranging_minimum_is_two_radios():
    m = get_method("SX1280_RANGING")
    assert m.mathematical_minimum_anchors == 2
    assert m.preferred_benchmark_anchors == 2


def test_fingerprinting_has_no_trilateration_minimum():
    m = get_method("FINGERPRINTING")
    assert m.mathematical_minimum_anchors is None
    assert m.has_native_simulator is False


def test_methods_without_native_simulator_require_sourced_evidence():
    for name, method in METHOD_CATALOG.items():
        if not method.has_native_simulator:
            assert method.evidence_note, f"{name} needs a note on sourced evidence"


def test_applicability_matrix_distinguishes_anchor_based_from_gnss():
    matrix = applicability_matrix()
    assert matrix["UWB_SS_TWR"]["anchor_count"] is True
    assert matrix["GNSS_SPP"]["anchor_count"] is False
    assert matrix["GNSS_SPP"]["satellite_count"] is True
    assert matrix["UWB_SS_TWR"]["satellite_count"] is False


def test_applicability_matrix_rtk_convergence_only_for_rtk():
    matrix = applicability_matrix()
    assert matrix["GNSS_RTK_FIXED"]["rtk_convergence"] is True
    assert matrix["GNSS_SPP"]["rtk_convergence"] is False


def test_applicability_matrix_airtime_only_for_active_radio_methods():
    matrix = applicability_matrix()
    assert matrix["UWB_SS_TWR"]["radio_airtime"] is True
    assert matrix["GNSS_SPP"]["radio_airtime"] is False
    assert matrix["FINGERPRINTING"]["radio_airtime"] is False
