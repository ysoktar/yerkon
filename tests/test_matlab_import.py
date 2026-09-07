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
