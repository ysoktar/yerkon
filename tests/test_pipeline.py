"""End-to-end scenario pipeline: spec -> anchors/path -> fixes -> metrics.

This wires together the solver, Monte Carlo engine, and metrics modules
into one scenario result, the unit the table builders consume.
"""
import numpy as np
import pytest

from locbench3d.experiment.schema import ScenarioSpec
from locbench3d.tables.pipeline import run_scenario


def _spec(**overrides):
    base = dict(
        scenario_id="scenario-000001",
        method="UWB_SS_TWR",
        anchor_count=5,
        tag_count=1,
        update_rate_hz=1.0,
        width_m=10.0,
        length_m=10.0,
        height_m=4.0,
        frame_duration_s=0.001,
        guard_duration_s=0.0002,
    )
    base.update(overrides)
    return ScenarioSpec(**base)


def test_run_scenario_produces_successful_fixes_for_valid_geometry():
    result = run_scenario(_spec(), n_repeats=20, seed=0)
    assert result.reliability.attempted_fixes == 20 * result.n_path_samples
    assert result.accuracy.n_success > 0
    assert result.geometry_valid_fraction == pytest.approx(1.0)


def test_run_scenario_is_deterministic_given_seed():
    a = run_scenario(_spec(), n_repeats=10, seed=5)
    b = run_scenario(_spec(), n_repeats=10, seed=5)
    assert a.accuracy.error_3d_rmse_m == pytest.approx(b.accuracy.error_3d_rmse_m)


def test_run_scenario_rejects_methods_without_native_simulator():
    with pytest.raises(ValueError):
        run_scenario(_spec(method="FINGERPRINTING"), n_repeats=5, seed=0)


def test_sx1280_ranging_uses_hardware_calibrated_evidence():
    from locbench3d.core.evidence import EvidenceType

    result = run_scenario(
        _spec(method="SX1280_RANGING", anchor_count=5, hardware_profile="Semtech SX1280"),
        n_repeats=5,
        seed=0,
    )
    assert result.error_model_evidence.evidence_type == EvidenceType.HARDWARE_CALIBRATED_MODEL


def test_tdoa_scenario_uses_tdoa_geometry_not_absolute_range():
    result = run_scenario(_spec(method="TDOA"), n_repeats=5, seed=0)
    # Exact numeric comparison against absolute-range CRLB is covered in
    # test_tdoa.py; here we just confirm the pipeline actually produced a
    # representative CRLB via the TDoA path, not a crash or a None.
    assert result.representative_crlb is not None


def test_overloaded_scenario_flagged_in_scalability():
    result = run_scenario(
        _spec(tag_count=1000, update_rate_hz=50.0), n_repeats=1, seed=0
    )
    assert result.scalability.overloaded is True
