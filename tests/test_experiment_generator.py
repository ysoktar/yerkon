"""Experiment configuration and combinatorial scenario generation.

The count preview must match the actual number of generated scenarios
before any simulation runs, and validation must catch structurally invalid
values before the benchmark starts.
"""
import pytest

from locbench3d.experiment.generator import (
    ExperimentDesign,
    generate_scenarios,
    preview_scenario_count,
    validate_design,
)
from locbench3d.experiment.schema import ScenarioTemplate


def _design(**overrides):
    variables = dict(
        method=["UWB_SS_TWR", "UWB_DS_TWR"],
        anchor_count=[4, 5],
        tag_count=[1],
        update_rate_hz=[1.0],
    )
    variables.update(overrides)
    return ExperimentDesign(
        template=ScenarioTemplate(
            width_m=10.0, length_m=10.0, height_m=3.0,
            frame_duration_s=0.001, guard_duration_s=0.0002,
        ),
        variables=variables,
    )


def test_preview_count_matches_cartesian_product_size():
    design = _design()
    assert preview_scenario_count(design) == 2 * 2 * 1 * 1


def test_generated_scenario_count_matches_preview():
    design = _design()
    scenarios = generate_scenarios(design)
    assert len(scenarios) == preview_scenario_count(design)


def test_generated_scenarios_have_unique_ids():
    design = _design()
    scenarios = generate_scenarios(design)
    ids = [s.scenario_id for s in scenarios]
    assert len(ids) == len(set(ids))


def test_each_scenario_carries_its_own_variable_combination():
    design = _design(anchor_count=[4, 5, 8])
    scenarios = generate_scenarios(design)
    anchor_counts = sorted({s.anchor_count for s in scenarios})
    assert anchor_counts == [4, 5, 8]


def test_validate_design_rejects_non_positive_update_rate():
    design = _design(update_rate_hz=[0.0])
    with pytest.raises(ValueError):
        validate_design(design)


def test_validate_design_rejects_negative_anchor_count():
    design = _design(anchor_count=[-1])
    with pytest.raises(ValueError):
        validate_design(design)


def test_validate_design_rejects_unknown_variable_name():
    design = _design(not_a_real_variable=[1, 2])
    with pytest.raises(ValueError):
        validate_design(design)


def test_validate_design_accepts_a_well_formed_design():
    design = _design()
    validate_design(design)  # must not raise
