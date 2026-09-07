import os

import numpy as np
import pytest

from yerkon.evidence import EvidenceType
from yerkon.matlab_import import (
    REQUIRED_TRIAL_COLUMNS,
    build_model_from_cases,
    load_trials,
    summarise,
)

HEADER = ",".join(REQUIRED_TRIAL_COLUMNS)


def write_trials(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(HEADER + "\n")
        for row in rows:
            handle.write(",".join(str(v) for v in row) + "\n")


def sample_rows(case="uwb_los", radio="DWM3000", condition="LOS", bw=499200000.0, errors=None):
    errors = errors if errors is not None else [0.10, -0.05, 0.22, 0.01, -0.13]
    return [
        (case, radio, condition, bw, 20.0, 50.0, i + 1, e)
        for i, e in enumerate(errors)
    ]


def test_missing_export_says_how_to_produce_it(tmp_path):
    with pytest.raises(FileNotFoundError) as excinfo:
        load_trials(os.path.join(tmp_path, "absent.csv"))
    assert "yerkon_ranging_sim.m" in str(excinfo.value)


def test_a_csv_with_the_wrong_columns_is_refused(tmp_path):
    path = os.path.join(tmp_path, "wrong.csv")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("a,b,c\n1,2,3\n")
    with pytest.raises(ValueError) as excinfo:
        load_trials(path)
    assert "missing columns" in str(excinfo.value)


def test_trials_are_grouped_by_case(tmp_path):
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(path, sample_rows() + sample_rows(case="uwb_nlos", condition="NLOS"))
    cases = load_trials(path)
    assert set(cases) == {"uwb_los", "uwb_nlos"}
    assert cases["uwb_los"].errors_m.size == 5
    assert cases["uwb_nlos"].condition == "NLOS"
    assert cases["uwb_los"].bandwidth_hz == pytest.approx(499.2e6)


def test_case_reports_bias_and_spread_separately(tmp_path):
    # A constant offset is what calibration removes; the spread is what is
    # left. Folding them together would hide which is which.
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(path, sample_rows(errors=[2.0, 2.0, 2.0, 2.0]))
    case = load_trials(path)["uwb_los"]
    assert case.mean_bias_m == pytest.approx(2.0)
    assert case.sigma_m == pytest.approx(0.0)


def test_model_is_labelled_as_simulation_not_measurement(tmp_path):
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(path, sample_rows())
    cases = load_trials(path)
    model = build_model_from_cases(list(cases.values()), name="test")
    assert model.evidence.evidence_type is EvidenceType.WAVEFORM_SIMULATION
    assert "Nothing here was measured on hardware" in model.evidence.source_scope


def test_calibrated_model_removes_the_constant_offset(tmp_path):
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(path, sample_rows(errors=[3.0, 3.2, 2.8, 3.1]))
    cases = list(load_trials(path).values())
    calibrated = build_model_from_cases(cases, name="cal", calibrated=True)
    raw = build_model_from_cases(cases, name="raw", calibrated=False)
    assert np.mean(calibrated.population_errors_m) == pytest.approx(0.0, abs=1e-9)
    assert raw.mean_bias_m == pytest.approx(3.025, abs=1e-3)
    # Calibration removes an offset; it cannot make the radio quieter.
    assert np.std(calibrated.population_errors_m) == pytest.approx(
        np.std(raw.population_errors_m)
    )


def test_model_resamples_the_simulated_trials_rather_than_fitting_a_gaussian(tmp_path):
    # The tail is the interesting part: a narrowband receiver that locks to
    # a reflection produces occasional large errors that a fitted Gaussian
    # would smooth away.
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(path, sample_rows(errors=[0.0, 0.0, 0.0, 0.0, 40.0]))
    cases = list(load_trials(path).values())
    model = build_model_from_cases(cases, name="tail", calibrated=False, seed=3)
    drawn = model.sample(4000)
    assert set(np.unique(np.round(drawn, 6))) == {0.0, 40.0}


def test_summary_orders_cases_and_carries_the_bandwidth(tmp_path):
    path = os.path.join(tmp_path, "trials.csv")
    write_trials(
        path,
        sample_rows(case="sx1280_406k_los", radio="SX1280", bw=406000.0)
        + sample_rows(),
    )
    rows = summarise(load_trials(path))
    assert [r["radio"] for r in rows] == ["DWM3000", "SX1280"]
    assert rows[1]["bandwidth_mhz"] == pytest.approx(0.406)


def test_building_a_model_from_nothing_is_refused():
    with pytest.raises(ValueError):
        build_model_from_cases([], name="empty")


DRIFT_HEADER = (
    "outage_s,runs,position_drift_p50_m,position_drift_p95_m,"
    "position_drift_max_m,velocity_error_p50_m_s,velocity_error_p95_m_s"
)


def write_drift(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(DRIFT_HEADER + "\n")
        for row in rows:
            handle.write(",".join(str(v) for v in row) + "\n")


def test_missing_imu_export_says_how_to_produce_it(tmp_path):
    from yerkon.matlab_import import load_imu_drift

    with pytest.raises(FileNotFoundError) as excinfo:
        load_imu_drift(os.path.join(tmp_path, "absent.csv"))
    assert "yerkon_imu_char.m" in str(excinfo.value)


def test_drift_curve_is_sorted_by_outage_length(tmp_path):
    from yerkon.matlab_import import load_imu_drift

    path = os.path.join(tmp_path, "drift.csv")
    write_drift(path, [
        (5.0, 100, 1.20, 2.40, 3.0, 0.4, 0.8),
        (1.0, 100, 0.05, 0.11, 0.2, 0.1, 0.2),
        (2.0, 100, 0.20, 0.44, 0.6, 0.2, 0.4),
    ])
    drift = load_imu_drift(path)
    assert list(drift.outage_s) == [1.0, 2.0, 5.0]
    assert drift.drift_p50_m[0] == pytest.approx(0.05)


def test_drift_is_interpolated_between_the_measured_points(tmp_path):
    from yerkon.matlab_import import load_imu_drift

    path = os.path.join(tmp_path, "drift.csv")
    write_drift(path, [
        (1.0, 100, 0.10, 0.20, 0.3, 0.1, 0.2),
        (3.0, 100, 0.30, 0.60, 0.9, 0.3, 0.6),
    ])
    drift = load_imu_drift(path)
    assert drift.drift_at(2.0) == pytest.approx(0.20)
    assert drift.drift_at(2.0, percentile="p95") == pytest.approx(0.40)


def test_implied_acceleration_noise_inverts_the_drift(tmp_path):
    # Free-inertial position error grows as sigma*t^2/2, so a 1 s drift of
    # 0.04 m implies 0.08 m/s^2. That is the number the filter should use
    # instead of the one this project picked.
    from yerkon.matlab_import import load_imu_drift

    path = os.path.join(tmp_path, "drift.csv")
    write_drift(path, [(1.0, 100, 0.04, 0.08, 0.1, 0.05, 0.1)])
    drift = load_imu_drift(path)
    assert drift.implied_accel_noise_m_s2(1.0) == pytest.approx(0.08)


def test_a_drift_csv_with_the_wrong_columns_is_refused(tmp_path):
    from yerkon.matlab_import import load_imu_drift

    path = os.path.join(tmp_path, "drift.csv")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("a,b\n1,2\n")
    with pytest.raises(ValueError) as excinfo:
        load_imu_drift(path)
    assert "missing columns" in str(excinfo.value)
