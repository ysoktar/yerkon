import numpy as np
import pytest

from yerkon.fusion import (
    DEFAULT_BIAS_VARIANCE_FRACTION,
    FusionSettings,
    _range_error_split,
    run_filter,
)
from yerkon.path import driving_track
from yerkon.receiver import pedestrian_receiver, vehicle_receiver
from yerkon.scenarios import critical_zone_scenario, run_fused, urban_scenario


def test_error_split_preserves_the_total_spread():
    for fraction in (0.0, 0.25, 0.5, 1.0):
        bias, white = _range_error_split(3.0, fraction)
        assert bias**2 + white**2 == pytest.approx(9.0)


def test_error_split_rejects_a_fraction_outside_zero_to_one():
    with pytest.raises(ValueError):
        _range_error_split(3.0, 1.5)


def test_a_pure_bias_error_cannot_be_filtered_away():
    # The point of the split: if every metre of ranging error were
    # independent noise, a filter seeing hundreds of ranges would average
    # it to nothing and report centimetres from a metre-class radio.
    scenario = urban_scenario()
    averaging = run_fused(
        scenario, settings=FusionSettings(bias_variance_fraction=0.0), n_runs=4
    )
    fixed = run_fused(
        scenario, settings=FusionSettings(bias_variance_fraction=1.0), n_runs=4
    )
    assert fixed.hpe_p50_m > 2.0 * averaging.hpe_p50_m


def test_the_default_split_sits_between_those_two_extremes():
    assert 0.0 < DEFAULT_BIAS_VARIANCE_FRACTION < 1.0


def test_the_map_constraint_is_what_fixes_the_vertical_axis():
    # Radio geometry cannot resolve height in a terrestrial layout. The map
    # can, and the report's architecture says to use it.
    scenario = urban_scenario()
    with_map = run_fused(scenario, n_runs=4)
    without_map = run_fused(
        scenario, settings=FusionSettings(use_map_height=False), n_runs=4
    )
    assert with_map.vpe_p95_m < 0.25 * without_map.vpe_p95_m


def test_the_vertical_result_tracks_the_map_accuracy_not_the_radio():
    # Consequence of the above that has to be said out loud: once a map
    # height constraint is applied, the vertical number describes the map.
    scenario = urban_scenario()
    fused = run_fused(scenario, n_runs=6)
    map_sigma = scenario.receiver.map_constraint.height_sigma_m
    assert fused.vpe_p50_m < 2.0 * map_sigma
    assert fused.vpe_p95_m < 5.0 * map_sigma


def test_calibration_still_matters_after_fusion():
    calibrated = run_fused(urban_scenario(calibrated=True), n_runs=4)
    raw = run_fused(urban_scenario(calibrated=False), n_runs=4)
    # A common-mode offset sits on every anchor at once, so no amount of
    # geometry or filtering removes it.
    assert raw.hpe_p50_m > calibrated.hpe_p50_m


def test_aiding_helps_the_tunnel_most_in_the_vertical():
    # An earlier version of this test asserted that aiding rescued the
    # tunnel from divergence, on a tenfold margin. That was an artefact:
    # the error model was a Gaussian at the report's target sigma, the
    # outlier gate scaled to that sigma was tight enough to reject the NLOS
    # bias being layered on top, and the filter then coasted. With the
    # waveform-derived model, and with the NLOS term no longer counted
    # twice, radio-only holds in the tunnel. Aiding still helps, and where
    # it helps most is the axis the radio cannot see.
    scenario = critical_zone_scenario()
    aided = run_fused(scenario, n_runs=4)
    radio_only = run_fused(
        scenario,
        settings=FusionSettings(
            use_odometry=False, use_heading=False, use_map_height=False
        ),
        n_runs=4,
    )
    assert aided.vpe_p95_m < 0.3 * radio_only.vpe_p95_m
    assert aided.hpe_p95_m < radio_only.hpe_p95_m


def test_the_filter_follows_a_turn_rather_than_coasting_through_it():
    # A constant-velocity filter falls behind on a bend, its innovations
    # grow, and the outlier gate then rejects the ranges that would have
    # corrected it. Driving the propagation from the IMU is what prevents
    # that, so a turning track must not blow the gate.
    scenario = urban_scenario()
    result = run_fused(scenario, n_runs=4)
    assert result.gated_range_fraction < 0.05
    assert result.hpe_p95_m < 20.0


def test_a_receiver_without_odometry_is_modelled_differently():
    assert vehicle_receiver().odometry is not None
    assert pedestrian_receiver().odometry is None
    # Both still declare where their numbers came from.
    for receiver in (vehicle_receiver(), pedestrian_receiver()):
        assert receiver.evidence_records
        assert all(r.source_scope.strip() for r in receiver.evidence_records)


def test_filter_reports_nothing_when_it_never_gets_a_first_fix():
    # Anchors far out of range: no initial fix, so no track, and the result
    # must be empty rather than a fabricated zero-error run.
    track = driving_track("t", (0.0, 0.0, 1.5), 0.0, 10.0, 5.0, 0.1)
    far = np.array([[50_000.0, 0.0, 8.0], [50_100.0, 0.0, 9.0],
                    [50_200.0, 50.0, 10.0], [50_300.0, 80.0, 12.0]])
    result = run_filter(
        track=track,
        anchors=far,
        receiver=vehicle_receiver(),
        sigma_range_m=1.0,
        common_bias_m=0.0,
        max_range_m=300.0,
        max_anchors_per_fix=8,
        packet_loss_probability=0.0,
        nlos_probability=0.0,
        nlos_bias_m=0.0,
        seed=1,
    )
    assert result.error_3d_m.size == 0
    assert result.converged_after_s is None
