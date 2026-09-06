"""Master comparison row builder and field catalog.

The field catalog documents the real columns the master table produces
(no parallel, disconnected schema), and the table is broad enough to
reach several hundred defined fields across method families.
"""
from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.hardware.profiles import get_profile
from locbench3d.tables.master_fields import build_field_catalog
from locbench3d.tables.master_row import build_master_row
from locbench3d.tables.pipeline import run_scenario
from locbench3d.experiment.schema import ScenarioSpec

_GNSS_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.SIMULATED_MONTE_CARLO, source_name="t", source_scope="t"
)


def _radio_spec():
    return ScenarioSpec(
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
        hardware_profile="Semtech SX1280",
    )


def test_master_row_from_radio_scenario_contains_identity_and_accuracy_fields():
    result = run_scenario(_radio_spec(), n_repeats=10, seed=0)
    hw = get_profile("Semtech SX1280")
    row = build_master_row(result, hardware_profile=hw)
    assert row["scenario_id"] == "scenario-000001"
    assert row["method"] == "UWB_SS_TWR"
    assert "acc_error_3d_rmse_m" in row
    assert "rel_valid_fix_rate" in row
    assert "hw_manufacturer" in row
    assert row["hw_manufacturer"] == "Semtech"


def test_master_row_gnss_fields_are_independent_of_radio_fields():
    from locbench3d.gnss.model import FixState, GnssFix, PositioningMode
    from locbench3d.tables.master_row import build_gnss_master_row

    fix = GnssFix(
        fix_state=FixState.RTK_FIXED,
        positioning_mode=PositioningMode.RTK_FIXED,
        horizontal_error_m=0.02,
        evidence=_GNSS_EVIDENCE,
    )
    row = build_gnss_master_row("scenario-gnss-1", fix)
    assert row["gnss_fix_state"] == "RTK_FIXED"
    assert row["gnss_positioning_mode"] == "RTK_FIXED"
    assert "acc_error_3d_rmse_m" not in row


def test_field_catalog_has_several_hundred_defined_fields():
    from locbench3d.environment.environment3d import Environment3D
    from locbench3d.feasibility.requirements import HardRequirements, ScenarioMetricsForFeasibility, evaluate_feasibility
    from locbench3d.gnss.model import FixState, GnssFix, PositioningMode
    from locbench3d.metrics.cost import CostBreakdown
    from locbench3d.metrics.energy import EnergyBudget
    from locbench3d.metrics.gnss import summarize_gnss_session
    from locbench3d.metrics.range_comparison import build_range_comparison_rows
    from locbench3d.pareto.pareto import Objective, compute_pareto
    from locbench3d.tables.master_row import build_gnss_master_row
    from locbench3d.tables.serialize import flatten_dataclass

    result = run_scenario(_radio_spec(), n_repeats=5, seed=0)
    hw = get_profile("Semtech SX1280")
    radio_row = build_master_row(result, hardware_profile=hw)

    gnss_fix = GnssFix(
        fix_state=FixState.RTK_FIXED,
        positioning_mode=PositioningMode.RTK_FIXED,
        satellites_used=20,
        hdop=0.8,
        evidence=_GNSS_EVIDENCE,
    )
    gnss_row = build_gnss_master_row("scenario-gnss-1", gnss_fix)
    gnss_summary_row = flatten_dataclass(
        summarize_gnss_session([gnss_fix]), prefix="gnss_session_"
    )

    cost_row = flatten_dataclass(CostBreakdown(device_cost=10.0, anchor_cost=100.0), prefix="cost_")
    energy_row = flatten_dataclass(
        EnergyBudget(0.001, 0.001, 0.0001, 0.0001, 0.0001, 0.0001), prefix="energy_"
    )
    feas_row = flatten_dataclass(
        evaluate_feasibility(
            ScenarioMetricsForFeasibility(
                scenario_id="s", method="m", geometry_valid=True, overloaded=False
            ),
            HardRequirements(),
        ),
        prefix="feas_",
    )
    pareto_row = flatten_dataclass(
        compute_pareto([{"cost": 1.0}], [True], [Objective("cost")])[0], prefix="pareto_"
    )
    req_row = flatten_dataclass(HardRequirements(max_3d_p95_m=1.0), prefix="req_")
    range_row = flatten_dataclass(
        build_range_comparison_rows(
            "s", "m", "h", "e", result.fixes, [0, 100], result.error_model_evidence
        )[0]
        if build_range_comparison_rows(
            "s", "m", "h", "e", result.fixes, [0, 100], result.error_model_evidence
        )
        else None,
        prefix="range_",
    )
    env_row = flatten_dataclass(
        Environment3D(
            environment_id="e1", width_m=10, length_m=10, height_m=4,
            floor_count=1, floor_height_m=4, indoor_outdoor="indoor",
            environment_class="office", los_fraction=0.9, nlos_fraction=0.1,
        ),
        prefix="env_",
    )

    catalog = build_field_catalog(
        [radio_row, gnss_row, gnss_summary_row, cost_row, energy_row, feas_row,
         pareto_row, req_row, range_row, env_row]
    )
    assert len(catalog) >= 300
    for entry in catalog:
        assert entry.description.strip() != ""
        assert entry.unit.strip() != ""


def test_field_catalog_entries_have_a_category():
    result = run_scenario(_radio_spec(), n_repeats=5, seed=0)
    row = build_master_row(result, hardware_profile=None)
    catalog = build_field_catalog([row])
    categories = {e.category for e in catalog}
    assert "accuracy" in categories
    assert "reliability" in categories
    assert "identity" in categories
