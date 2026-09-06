"""Feasibility decision order: applicability, geometry, hard requirements.

A configuration failing a hard requirement (or geometry, or applicability)
must be marked infeasible with a concrete reason, never silently passed
through because some other score looked good.
"""
from locbench3d.feasibility.requirements import (
    HardRequirements,
    ScenarioMetricsForFeasibility,
    evaluate_feasibility,
)


def _metrics(**overrides):
    base = dict(
        scenario_id="s1",
        method="UWB_SS_TWR",
        geometry_valid=True,
        overloaded=False,
        error_3d_p95_m=1.0,
        horizontal_p95_m=0.8,
        vertical_p95_m=0.6,
        availability=0.99,
        latency_s=0.05,
        achieved_update_rate_hz=5.0,
        max_supported_tags=50,
        infrastructure_count=6,
        total_cost=1000.0,
        power_w=1.0,
        environment_class="indoor",
    )
    base.update(overrides)
    return ScenarioMetricsForFeasibility(**base)


def test_feasible_scenario_passes_all_checks():
    result = evaluate_feasibility(_metrics(), HardRequirements(max_3d_p95_m=2.0))
    assert result.feasible is True
    assert result.failed_requirements == []


def test_geometry_invalid_is_infeasible_before_hard_requirements_checked():
    result = evaluate_feasibility(
        _metrics(geometry_valid=False, error_3d_p95_m=0.01),
        HardRequirements(max_3d_p95_m=100.0),
    )
    assert result.feasible is False
    assert result.infeasibility_reason == "GEOMETRY_INVALID"


def test_overloaded_scenario_is_infeasible_regardless_of_accuracy():
    result = evaluate_feasibility(
        _metrics(overloaded=True, error_3d_p95_m=0.001),
        HardRequirements(max_3d_p95_m=100.0),
    )
    assert result.feasible is False
    assert result.infeasibility_reason == "OVERLOADED"


def test_hard_requirement_failure_is_recorded_with_reason():
    result = evaluate_feasibility(_metrics(error_3d_p95_m=5.0), HardRequirements(max_3d_p95_m=2.0))
    assert result.feasible is False
    assert "max_3d_p95_m" in result.failed_requirements


def test_unmet_requirement_from_missing_metric_is_not_silently_passed():
    result = evaluate_feasibility(
        _metrics(availability=None), HardRequirements(min_availability=0.9)
    )
    assert result.feasible is False
    assert "min_availability" in result.unknown_requirements


def test_not_applicable_scenario_is_infeasible_with_applicability_reason():
    result = evaluate_feasibility(_metrics(), HardRequirements(), applicable=False)
    assert result.feasible is False
    assert result.infeasibility_reason == "NOT_APPLICABLE"


def test_multiple_hard_requirements_all_checked():
    result = evaluate_feasibility(
        _metrics(power_w=5.0, total_cost=2000.0),
        HardRequirements(max_power_w=1.0, max_cost=1000.0),
    )
    assert set(result.failed_requirements) == {"max_power_w", "max_cost"}


def test_required_environment_support_checked():
    result = evaluate_feasibility(
        _metrics(environment_class="outdoor"),
        HardRequirements(required_environment_support=["indoor"]),
    )
    assert "required_environment_support" in result.failed_requirements
