"""End-to-end benchmark run: an experiment design in, every result table out.

Methods without a native simulator (see ``methods.catalog``) are skipped
with their evidence note recorded, not silently dropped: they show up in
``BenchmarkOutputs.skipped_scenarios`` so a reader can see they need
sourced/imported evidence instead of a simulated result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from locbench3d.core.timing import fractional_bandwidth, range_resolution_heuristic_m, wavelength_m
from locbench3d.environment.environment3d import anchor_density_3d, poisson_expected_anchors_in_range
from locbench3d.experiment.generator import ExperimentDesign, generate_scenarios
from locbench3d.experiment.schema import ScenarioSpec
from locbench3d.feasibility.requirements import (
    HardRequirements,
    ScenarioMetricsForFeasibility,
    evaluate_feasibility,
)
from locbench3d.gnss.model import GnssFix
from locbench3d.hardware.profiles import HARDWARE_PROFILE_REGISTRY, get_profile
from locbench3d.metrics.gnss import summarize_gnss_session
from locbench3d.metrics.range_comparison import build_range_comparison_rows
from locbench3d.methods.catalog import get_method
from locbench3d.pareto.pareto import Objective, compute_pareto
from locbench3d.tables.master_row import build_gnss_master_row, build_master_row
from locbench3d.tables.pipeline import run_scenario
from locbench3d.tables.serialize import flatten_dataclass

_PARETO_OBJECTIVES = (
    Objective("error_3d_p95_m", minimize=True),
    Objective("achievable_fixes_per_second", minimize=False),
)


@dataclass
class BenchmarkOutputs:
    scenarios: list[ScenarioSpec] = field(default_factory=list)
    master_rows: list[dict] = field(default_factory=list)
    range_comparison_rows: list[dict] = field(default_factory=list)
    path_comparison_rows: list[dict] = field(default_factory=list)
    geometry_comparison_rows: list[dict] = field(default_factory=list)
    scalability_comparison_rows: list[dict] = field(default_factory=list)
    skipped_scenarios: list[dict] = field(default_factory=list)
    environment_comparison_rows: list[dict] = field(default_factory=list)
    volume_comparison_rows: list[dict] = field(default_factory=list)
    channel_comparison_rows: list[dict] = field(default_factory=list)
    gnss_rows: list[dict] = field(default_factory=list)
    gnss_summary_row: Optional[dict] = None
    evidence_records: list[dict] = field(default_factory=list)


def _environment_label(spec: ScenarioSpec) -> str:
    return f"{spec.width_m:g}x{spec.length_m:g}x{spec.height_m:g}m"


def run_benchmark(
    design: ExperimentDesign,
    n_repeats: int = 20,
    seed: int = 0,
    range_bin_edges_m: Optional[list[float]] = None,
    hard_requirements: Optional[HardRequirements] = None,
    gnss_fixes: Optional[list[GnssFix]] = None,
) -> BenchmarkOutputs:
    scenarios = generate_scenarios(design)
    bins = range_bin_edges_m or [0, 5, 10, 20, 40, 100]
    outputs = BenchmarkOutputs(scenarios=scenarios)

    pareto_ids: list[str] = []
    pareto_feasible_flags: list[bool] = []
    pareto_records: list[dict] = []

    seen_evidence_keys: set[tuple] = set()

    for spec in scenarios:
        method_def = get_method(spec.method)
        if not method_def.has_native_simulator:
            outputs.skipped_scenarios.append(
                {
                    "scenario_id": spec.scenario_id,
                    "method": spec.method,
                    "reason": method_def.evidence_note,
                }
            )
            continue

        result = run_scenario(spec, n_repeats=n_repeats, seed=seed)
        anchor_count = spec.anchor_count if spec.anchor_count is not None else 5
        hw = (
            get_profile(spec.hardware_profile)
            if spec.hardware_profile in HARDWARE_PROFILE_REGISTRY
            else None
        )
        row = build_master_row(result, hardware_profile=hw)

        if hard_requirements is not None:
            metrics = ScenarioMetricsForFeasibility(
                scenario_id=spec.scenario_id,
                method=spec.method,
                geometry_valid=result.representative_geometry.geometry_valid,
                overloaded=result.scalability.overloaded,
                error_3d_p95_m=result.accuracy.error_3d_p95_m,
                horizontal_p95_m=result.accuracy.horizontal_p95_m,
                vertical_p95_m=result.accuracy.vertical_p95_m,
                availability=result.reliability.valid_fix_rate,
                latency_s=result.sequential_fix_latency_s,
                achieved_update_rate_hz=result.scalability.achieved_per_tag_update_rate_hz,
                max_supported_tags=result.scalability.max_supported_tags,
                infrastructure_count=spec.anchor_count,
                total_cost=None,
                power_w=None,
                environment_class=None,
            )
            feas_result = evaluate_feasibility(metrics, hard_requirements)
            row.update(flatten_dataclass(feas_result, prefix="feas_"))

            has_objectives = (
                result.accuracy.error_3d_p95_m is not None
                and result.scalability.achievable_fixes_per_second is not None
            )
            pareto_ids.append(spec.scenario_id)
            pareto_feasible_flags.append(feas_result.feasible and has_objectives)
            pareto_records.append(
                {
                    "error_3d_p95_m": result.accuracy.error_3d_p95_m,
                    "achievable_fixes_per_second": result.scalability.achievable_fixes_per_second,
                }
            )

        outputs.master_rows.append(row)

        range_rows = build_range_comparison_rows(
            spec.scenario_id,
            spec.method,
            spec.hardware_profile or "unspecified",
            _environment_label(spec),
            result.fixes,
            bins,
            result.error_model_evidence,
        )
        for r in range_rows:
            outputs.range_comparison_rows.append(flatten_dataclass(r))

        path_row = {"scenario_id": spec.scenario_id, "method": spec.method}
        path_row.update(flatten_dataclass(result.path_metrics))
        outputs.path_comparison_rows.append(path_row)

        geometry_row = {
            "scenario_id": spec.scenario_id,
            "method": spec.method,
            "geometry_valid_fraction": result.geometry_valid_fraction,
        }
        geometry_row.update(flatten_dataclass(result.representative_geometry))
        geometry_row.update(flatten_dataclass(result.representative_crlb, prefix="crlb_"))
        outputs.geometry_comparison_rows.append(geometry_row)

        scalability_row = {"scenario_id": spec.scenario_id, "method": spec.method}
        scalability_row.update(flatten_dataclass(result.scalability))
        outputs.scalability_comparison_rows.append(scalability_row)

        floor_area_m2 = spec.width_m * spec.length_m
        volume_m3 = floor_area_m2 * spec.height_m
        outputs.environment_comparison_rows.append(
            {
                "scenario_id": spec.scenario_id,
                "width_m": spec.width_m,
                "length_m": spec.length_m,
                "height_m": spec.height_m,
                "floor_area_m2": floor_area_m2,
                "volume_m3": volume_m3,
                "anchor_count": anchor_count,
                "anchors_per_sqm": anchor_count / floor_area_m2,
                "anchors_per_cubic_m": anchor_count / volume_m3,
                "nlos_probability": spec.nlos_probability,
                "nlos_bias_m": spec.nlos_bias_m,
                "packet_loss_probability": spec.packet_loss_probability,
            }
        )

        density = anchor_density_3d(anchor_count, volume_m3)
        radius_m = max(spec.width_m, spec.length_m, spec.height_m) / 2.0
        outputs.volume_comparison_rows.append(
            {
                "scenario_id": spec.scenario_id,
                "anchor_count": anchor_count,
                "volume_m3": volume_m3,
                "radius_m": radius_m,
                "anchor_density_3d_per_m3": density,
                "expected_anchors_in_range": poisson_expected_anchors_in_range(density, radius_m),
                "planning_approximation": True,
            }
        )

        if spec.center_freq_hz is not None and spec.bandwidth_hz is not None:
            outputs.channel_comparison_rows.append(
                {
                    "scenario_id": spec.scenario_id,
                    "center_freq_hz": spec.center_freq_hz,
                    "bandwidth_hz": spec.bandwidth_hz,
                    "fractional_bandwidth": fractional_bandwidth(
                        spec.bandwidth_hz, spec.center_freq_hz
                    ),
                    "wavelength_m": wavelength_m(spec.center_freq_hz),
                    "range_resolution_heuristic_m": range_resolution_heuristic_m(
                        spec.bandwidth_hz
                    ),
                    "resolution_heuristic_note": (
                        "delta_d ~ c/B is a resolution heuristic, not a "
                        "positioning accuracy figure."
                    ),
                }
            )

        ev = result.error_model_evidence
        key = (ev.evidence_type.value, ev.source_name, ev.source_url)
        if key not in seen_evidence_keys:
            seen_evidence_keys.add(key)
            outputs.evidence_records.append(ev.to_dict() | {"used_by_scenario": spec.scenario_id})

    if hard_requirements is not None and pareto_ids:
        pareto_results = compute_pareto(pareto_records, pareto_feasible_flags, list(_PARETO_OBJECTIVES))
        by_id = {sid: pr for sid, pr in zip(pareto_ids, pareto_results)}
        for row in outputs.master_rows:
            pr = by_id.get(row["scenario_id"])
            if pr is not None:
                row.update(flatten_dataclass(pr, prefix="pareto_"))

    if gnss_fixes:
        for i, fix in enumerate(gnss_fixes):
            outputs.gnss_rows.append(build_gnss_master_row(f"gnss-{i:05d}", fix))
            if fix.evidence is not None:
                key = (fix.evidence.evidence_type.value, fix.evidence.source_name, fix.evidence.source_url)
                if key not in seen_evidence_keys:
                    seen_evidence_keys.add(key)
                    outputs.evidence_records.append(
                        fix.evidence.to_dict() | {"used_by_scenario": f"gnss-{i:05d}"}
                    )
        outputs.gnss_summary_row = flatten_dataclass(
            summarize_gnss_session(gnss_fixes), prefix="gnss_session_"
        )

    return outputs
