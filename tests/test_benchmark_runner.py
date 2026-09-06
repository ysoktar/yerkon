"""End-to-end benchmark run: config -> scenarios -> every result table."""
import pandas as pd
import pytest

from locbench3d.benchmark.runner import run_benchmark
from locbench3d.experiment.generator import ExperimentDesign
from locbench3d.experiment.schema import ScenarioTemplate
from locbench3d.feasibility.requirements import HardRequirements


def _design():
    return ExperimentDesign(
        template=ScenarioTemplate(
            width_m=10.0, length_m=10.0, height_m=4.0,
            frame_duration_s=0.001, guard_duration_s=0.0002,
        ),
        variables={
            "method": ["UWB_SS_TWR", "TDOA", "FINGERPRINTING"],
            "anchor_count": [5],
            "tag_count": [1],
            "update_rate_hz": [1.0],
        },
    )


def test_run_benchmark_produces_master_rows_for_simulated_methods():
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    methods = {row["method"] for row in outputs.master_rows}
    assert methods == {"UWB_SS_TWR", "TDOA"}


def test_run_benchmark_skips_methods_without_native_simulator_with_a_reason():
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    skipped_methods = {s["method"] for s in outputs.skipped_scenarios}
    assert "FINGERPRINTING" in skipped_methods
    assert all(s["reason"] for s in outputs.skipped_scenarios)


def test_run_benchmark_scenario_ids_are_unique_across_all_outputs():
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    ids = [row["scenario_id"] for row in outputs.master_rows]
    assert len(ids) == len(set(ids))


def test_run_benchmark_range_comparison_rows_have_no_empty_bins():
    outputs = run_benchmark(_design(), n_repeats=20, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    for row in outputs.range_comparison_rows:
        assert row["attempted_fixes"] > 0


def test_run_benchmark_applies_feasibility_and_pareto_when_requirements_given():
    requirements = HardRequirements(max_3d_p95_m=5.0, min_availability=0.5)
    outputs = run_benchmark(
        _design(), n_repeats=10, seed=0, range_bin_edges_m=[0, 5, 10, 20],
        hard_requirements=requirements,
    )
    for row in outputs.master_rows:
        assert "feas_feasible" in row
        assert "pareto_pareto_optimal" in row


def test_run_benchmark_tables_convert_to_dataframes_cleanly():
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    df = pd.DataFrame(outputs.master_rows)
    assert len(df) == len(outputs.master_rows)
