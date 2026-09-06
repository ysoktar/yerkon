"""Hard requirements and the feasibility decision order.

Decision order (see docs/EQUATIONS.md for the full seven-step version used
by the ranking layer):

1. Applicability - is this metric/method combination meaningful at all.
2. 3D geometry validity.
3. Hard requirements.

Absolute performance, capacity/energy/cost ranking, and Pareto comparison
happen only among scenarios that pass all three of the above (see
``locbench3d.pareto.pareto``). A scenario that fails any of these three is
marked infeasible with a concrete reason and must never be ranked above a
feasible scenario by an aggregate score.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class HardRequirements:
    max_3d_p95_m: Optional[float] = None
    max_horizontal_p95_m: Optional[float] = None
    max_vertical_p95_m: Optional[float] = None
    min_availability: Optional[float] = None
    max_latency_s: Optional[float] = None
    min_update_rate_hz: Optional[float] = None
    min_supported_tags: Optional[int] = None
    max_infrastructure_count: Optional[int] = None
    max_cost: Optional[float] = None
    max_power_w: Optional[float] = None
    required_environment_support: Optional[list[str]] = None


@dataclass(frozen=True)
class ScenarioMetricsForFeasibility:
    scenario_id: str
    method: str
    geometry_valid: bool
    overloaded: bool
    error_3d_p95_m: Optional[float] = None
    horizontal_p95_m: Optional[float] = None
    vertical_p95_m: Optional[float] = None
    availability: Optional[float] = None
    latency_s: Optional[float] = None
    achieved_update_rate_hz: Optional[float] = None
    max_supported_tags: Optional[int] = None
    infrastructure_count: Optional[int] = None
    total_cost: Optional[float] = None
    power_w: Optional[float] = None
    environment_class: Optional[str] = None


@dataclass(frozen=True)
class FeasibilityResult:
    scenario_id: str
    applicable: bool
    geometry_valid: bool
    overloaded: bool
    failed_requirements: list[str] = field(default_factory=list)
    unknown_requirements: list[str] = field(default_factory=list)
    feasible: bool = False
    infeasibility_reason: Optional[str] = None


# (requirement field name, metric field name, comparator: True if metric VIOLATES requirement)
_UPPER_BOUND_CHECKS = [
    ("max_3d_p95_m", "error_3d_p95_m"),
    ("max_horizontal_p95_m", "horizontal_p95_m"),
    ("max_vertical_p95_m", "vertical_p95_m"),
    ("max_latency_s", "latency_s"),
    ("max_infrastructure_count", "infrastructure_count"),
    ("max_cost", "total_cost"),
    ("max_power_w", "power_w"),
]
_LOWER_BOUND_CHECKS = [
    ("min_availability", "availability"),
    ("min_update_rate_hz", "achieved_update_rate_hz"),
    ("min_supported_tags", "max_supported_tags"),
]


def evaluate_feasibility(
    metrics: ScenarioMetricsForFeasibility,
    requirements: HardRequirements,
    applicable: bool = True,
) -> FeasibilityResult:
    if not applicable:
        return FeasibilityResult(
            scenario_id=metrics.scenario_id,
            applicable=False,
            geometry_valid=metrics.geometry_valid,
            overloaded=metrics.overloaded,
            feasible=False,
            infeasibility_reason="NOT_APPLICABLE",
        )

    if not metrics.geometry_valid:
        return FeasibilityResult(
            scenario_id=metrics.scenario_id,
            applicable=True,
            geometry_valid=False,
            overloaded=metrics.overloaded,
            feasible=False,
            infeasibility_reason="GEOMETRY_INVALID",
        )

    if metrics.overloaded:
        return FeasibilityResult(
            scenario_id=metrics.scenario_id,
            applicable=True,
            geometry_valid=True,
            overloaded=True,
            feasible=False,
            infeasibility_reason="OVERLOADED",
        )

    failed: list[str] = []
    unknown: list[str] = []

    for req_name, metric_name in _UPPER_BOUND_CHECKS:
        limit = getattr(requirements, req_name)
        if limit is None:
            continue
        value = getattr(metrics, metric_name)
        if value is None:
            unknown.append(req_name)
        elif value > limit:
            failed.append(req_name)

    for req_name, metric_name in _LOWER_BOUND_CHECKS:
        limit = getattr(requirements, req_name)
        if limit is None:
            continue
        value = getattr(metrics, metric_name)
        if value is None:
            unknown.append(req_name)
        elif value < limit:
            failed.append(req_name)

    if requirements.required_environment_support:
        if metrics.environment_class is None:
            unknown.append("required_environment_support")
        elif metrics.environment_class not in requirements.required_environment_support:
            failed.append("required_environment_support")

    feasible = not failed and not unknown
    reason = None
    if failed:
        reason = "HARD_REQUIREMENT_FAILED"
    elif unknown:
        reason = "INSUFFICIENT_EVIDENCE"

    return FeasibilityResult(
        scenario_id=metrics.scenario_id,
        applicable=True,
        geometry_valid=True,
        overloaded=False,
        failed_requirements=failed,
        unknown_requirements=unknown,
        feasible=feasible,
        infeasibility_reason=reason,
    )
