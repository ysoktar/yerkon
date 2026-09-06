"""Combinatorial experiment generation with a count preview and validation.

``preview_scenario_count`` must be checkable before running anything, and
must equal the number of scenarios ``generate_scenarios`` actually
produces (checked directly in tests, and again as a result invariant in
``locbench3d.validate.invariants``).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, replace

from locbench3d.experiment.schema import ScenarioSpec, ScenarioTemplate, TEMPLATE_FIELD_NAMES

_EXTRA_VARIABLE_NAMES = {"method", "anchor_count", "tag_count", "update_rate_hz"}
ALLOWED_VARIABLE_NAMES = _EXTRA_VARIABLE_NAMES | set(TEMPLATE_FIELD_NAMES)


@dataclass(frozen=True)
class ExperimentDesign:
    template: ScenarioTemplate
    variables: dict[str, list]


def preview_scenario_count(design: ExperimentDesign) -> int:
    count = 1
    for values in design.variables.values():
        count *= len(values)
    return count


def validate_design(design: ExperimentDesign) -> None:
    if design.template.width_m <= 0 or design.template.length_m <= 0 or design.template.height_m <= 0:
        raise ValueError("template environment dimensions must be positive")
    if design.template.frame_duration_s < 0 or design.template.guard_duration_s < 0:
        raise ValueError("frame/guard durations must not be negative")
    if not design.variables:
        raise ValueError("experiment design must vary at least one dimension")

    for name, values in design.variables.items():
        if name not in ALLOWED_VARIABLE_NAMES:
            raise ValueError(
                f"unknown experiment variable {name!r}; allowed: {sorted(ALLOWED_VARIABLE_NAMES)}"
            )
        if not values:
            raise ValueError(f"variable {name!r} has no values to vary over")
        if name == "update_rate_hz" and any(v <= 0 for v in values):
            raise ValueError("update_rate_hz values must be positive")
        if name == "anchor_count" and any(v < 0 for v in values):
            raise ValueError("anchor_count values must not be negative")
        if name == "tag_count" and any(v < 0 for v in values):
            raise ValueError("tag_count values must not be negative")

    if "method" not in design.variables:
        raise ValueError("experiment design must vary 'method' (even with a single value)")


def generate_scenarios(design: ExperimentDesign) -> list[ScenarioSpec]:
    validate_design(design)

    names = sorted(design.variables.keys())
    value_lists = [design.variables[name] for name in names]

    base_kwargs = {name: getattr(design.template, name) for name in TEMPLATE_FIELD_NAMES}

    scenarios: list[ScenarioSpec] = []
    for i, combo in enumerate(itertools.product(*value_lists)):
        overrides = dict(zip(names, combo))
        kwargs = dict(base_kwargs)
        kwargs.update({k: v for k, v in overrides.items() if k != "method"})
        kwargs.setdefault("anchor_count", None)
        kwargs.setdefault("tag_count", None)
        kwargs.setdefault("update_rate_hz", None)
        scenario_id = f"scenario-{i:06d}"
        scenarios.append(
            ScenarioSpec(
                scenario_id=scenario_id,
                method=overrides["method"],
                **kwargs,
            )
        )
    return scenarios
