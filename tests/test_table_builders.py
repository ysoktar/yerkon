"""DataFrame builders for the workbook's required tables."""
import pandas as pd

from locbench3d.tables import builders


def test_hardware_profiles_table_has_expected_columns():
    df = builders.build_hardware_profiles_table()
    assert "manufacturer" in df.columns
    assert "verified_ranging_support" in df.columns
    assert len(df) >= 6


def test_sx1280_published_observations_table():
    df = builders.build_sx1280_published_observations_table()
    assert len(df) == 6
    assert "true_range_m" in df.columns
    assert "evidence_type" in df.columns
    assert set(df["evidence_type"]) == {"PUBLISHED_EXPERIMENT"}


def test_sx1280_calibration_notes_table_flags_non_ranging_results():
    df = builders.build_sx1280_calibration_notes_table()
    assert "is_verified_ranging_result" in df.columns
    assert (df["is_verified_ranging_result"] == False).any()


def test_method_catalog_table_and_applicability_matrix_table():
    catalog_df = builders.build_method_catalog_table()
    assert "mathematical_minimum_anchors" in catalog_df.columns
    matrix_df = builders.build_applicability_matrix_table()
    assert "method" in matrix_df.columns
    assert "anchor_count" in matrix_df.columns


def test_official_references_table():
    df = builders.build_official_references_table()
    assert "verified_this_session" in df.columns
    assert "source_url" in df.columns
    assert len(df) >= 10


def test_environment_comparison_table():
    from locbench3d.environment.environment3d import Environment3D

    envs = [
        Environment3D(
            environment_id="e1", width_m=10, length_m=10, height_m=4,
            floor_count=1, floor_height_m=4, indoor_outdoor="indoor",
            environment_class="office", los_fraction=0.9, nlos_fraction=0.1,
            anchor_count=6,
        )
    ]
    df = builders.build_environment_comparison_table(envs)
    assert df.loc[0, "volume_m3"] == 400.0
    assert df.loc[0, "anchors_per_cubic_m"] == 6 / 400.0


def test_volume_comparison_table_uses_poisson_planning_approximation():
    df = builders.build_volume_comparison_table(
        [{"environment_id": "e1", "anchor_count": 8, "volume_m3": 600.0, "radius_m": 10.0}]
    )
    assert "planning_approximation" in df.columns
    assert bool(df.loc[0, "planning_approximation"]) is True
    assert df.loc[0, "expected_anchors_in_range"] > 0


def test_channel_comparison_table():
    df = builders.build_channel_comparison_table(
        [{"config_id": "c1", "f_low_hz": 2.4e9, "f_high_hz": 2.4835e9}]
    )
    assert df.loc[0, "bandwidth_hz"] > 0
    assert df.loc[0, "wavelength_m"] > 0


def test_master_comparison_table_from_rows():
    df = builders.rows_to_dataframe([{"a": 1}, {"a": 2, "b": 3}])
    assert len(df) == 2
    assert list(df.columns) == ["a", "b"] or set(df.columns) == {"a", "b"}


def test_matlab_uwb_waveform_table_from_records():
    from locbench3d.hardware.matlab_uwb_import import load_matlab_uwb_csv
    import io

    csv_text = (
        "true_range_m,estimated_range_m,error_m\n"
        "1,1.02,0.02\n"
    )
    records = load_matlab_uwb_csv(io.StringIO(csv_text))
    df = builders.build_matlab_uwb_waveform_table(records)
    assert len(df) == 1
    assert df.loc[0, "evidence_type"] == "MATLAB_WAVEFORM"


def test_matlab_uwb_waveform_table_empty_when_no_records():
    df = builders.build_matlab_uwb_waveform_table([])
    assert df.empty


def test_empty_rows_produce_empty_dataframe_not_error():
    df = builders.rows_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
