import numpy as np
import pytest

from yerkon.evidence import EvidenceType
from yerkon.geometry import coplanar, dop_from_jacobian, range_jacobian
from yerkon.scenarios import (
    all_scenarios,
    critical_zone_scenario,
    roadside_layout,
    run_scenario,
    tunnel_layout,
    urban_grid_layout,
    urban_scenario,
    rural_scenario,
)
from yerkon.simulate import anchors_in_range


def test_every_scenario_covers_at_least_one_square_kilometre():
    for scenario in all_scenarios():
        assert scenario.area_km2 >= 1.0, scenario.key


def test_the_four_rows_are_two_outdoor_urban_one_rural_and_one_indoor_outdoor():
    scenarios = all_scenarios()
    assert [s.environment for s in scenarios] == ["Dış", "Dış", "Dış", "İç + dış"]
    assert [s.key for s in scenarios] == [
        "urban_calibrated", "urban_uncalibrated", "rural", "critical",
    ]


def test_roadside_units_come_in_facing_pairs_across_the_carriageway():
    group = roadside_layout(length_m=1000.0, sign_spacing_m=200.0)
    y = group.positions[:, 1]
    assert set(np.round(np.unique(y), 6)) == {-12.0, 12.0}
    assert np.sum(y > 0) == np.sum(y < 0)


def test_the_rural_layout_mixes_sign_height_and_mast_height_anchors():
    scenario = rural_scenario()
    heights = scenario.anchors[:, 2]
    assert heights.min() < 8.0        # sign mounts
    assert heights.max() > 30.0       # masts
    assert not coplanar(scenario.anchors)


def test_urban_grid_is_not_flat():
    # A grid at one height cannot resolve the vertical axis at all, so the
    # layout has to place neighbouring anchors at different heights.
    group = urban_grid_layout(side_m=600.0, spacing_m=150.0)
    assert not coplanar(group.positions)
    assert np.ptp(group.positions[:, 2]) > 20.0


def test_tunnel_nodes_alternate_over_four_steps_not_two():
    group = tunnel_layout(length_m=2000.0, spacing_m=150.0)
    assert not coplanar(group.positions)


def test_every_scenario_keeps_enough_anchors_in_range_along_its_path():
    for scenario in all_scenarios():
        counts = [
            int(anchors_in_range(p, scenario.anchors, scenario.max_link_range_m).sum())
            for p in scenario.path.points()
        ]
        assert min(counts) >= 4, (scenario.key, min(counts))


def test_calibration_only_changes_the_error_model_not_the_deployment():
    calibrated = urban_scenario(calibrated=True)
    raw = urban_scenario(calibrated=False)
    assert np.array_equal(calibrated.anchors, raw.anchors)
    assert calibrated.area_km2 == raw.area_km2
    assert calibrated.capex_total_tl == raw.capex_total_tl


def test_capex_is_anchor_count_times_the_deck_unit_price():
    scenario = critical_zone_scenario()
    group = scenario.groups[0]
    assert scenario.capex_total_tl == pytest.approx(group.count * 1634.44)


def test_corridor_scenarios_also_report_cost_per_kilometre():
    # Cost per km² flatters an area deployment and punishes a ribbon, so a
    # corridor has to carry the per-km figure alongside it.
    result = run_scenario(critical_zone_scenario(), n_repeats=2, n_track_runs=1)
    assert result.capex_per_km_tl is not None
    urban = run_scenario(urban_scenario(), n_repeats=2, n_track_runs=1)
    assert urban.capex_per_km_tl is None


def test_tunnel_row_is_not_presented_as_hardware_calibrated():
    scenario = critical_zone_scenario()
    assert (
        scenario.error_model.evidence.evidence_type
        is EvidenceType.SIMULATED_MONTE_CARLO
    )


def test_geometry_profile_reports_how_far_links_run_past_the_calibrated_range():
    result = run_scenario(rural_scenario(), n_repeats=2, n_track_runs=1)
    beyond = result.geometry.links_beyond_calibrated_envelope
    # The rural links are kilometre-scale while the source data stops at
    # 250 m. That extrapolation has to be visible, not silent.
    assert beyond is not None and beyond > 0.5


def test_uwb_scenario_has_no_calibrated_envelope_to_compare_against():
    result = run_scenario(critical_zone_scenario(), n_repeats=2, n_track_runs=1)
    assert result.geometry.links_beyond_calibrated_envelope is None


def test_denser_urban_grid_buys_vertical_accuracy_not_horizontal():
    tag = np.array([517.0, 428.0, 1.5])
    dops = {}
    for spacing in (150.0, 250.0):
        anchors = urban_grid_layout(side_m=1000.0, spacing_m=spacing).positions
        visible = anchors[anchors_in_range(tag, anchors, 400.0)]
        dops[spacing] = dop_from_jacobian(range_jacobian(tag, visible))
    assert dops[150.0].vdop < 0.8 * dops[250.0].vdop
    assert dops[150.0].hdop < dops[250.0].hdop


def test_running_a_scenario_produces_metrics_for_every_attempt():
    result = run_scenario(urban_scenario(), n_repeats=5, n_track_runs=1)
    expected = urban_scenario().path.n_samples * 5
    assert result.reliability.attempted_fixes == expected
    assert result.accuracy.horizontal_p50_m is not None
    assert result.geometry.median_vdop is not None


def test_every_scenario_declares_the_sources_behind_its_parameters():
    for scenario in all_scenarios():
        records = scenario.evidence_records
        # error model + at least one anchor group + the parameter assumptions
        assert len(records) >= 4, scenario.key
        assert all(r.source_scope.strip() for r in records)
        kinds = {r.evidence_type for r in records}
        # Every scenario rests on assumptions this project made, and has to
        # say so rather than presenting them as sourced values.
        assert EvidenceType.ENGINEERING_ASSUMPTION in kinds, scenario.key
