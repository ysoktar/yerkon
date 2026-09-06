"""Scalability composition: occupancy, overload, achievable rate, ALOHA delivery.

An overloaded scenario must be marked infeasible, not silently under-report
an achieved rate as if everything were fine.
"""
import pytest

from locbench3d.metrics.scalability import evaluate_scalability
from locbench3d.protocol.traffic import RangingMethod


def test_scheduled_model_matches_requested_rate_when_not_overloaded():
    result = evaluate_scalability(
        method=RangingMethod.SS_TWR,
        anchor_count=5,
        tag_count=2,
        requested_update_rate_hz=1.0,
        frame_duration_s=0.001,
        guard_duration_s=0.0005,
        scheduling_model="scheduled",
    )
    assert result.overloaded is False
    assert result.achievable_fixes_per_second == pytest.approx(
        result.requested_fixes_per_second
    )
    assert result.achieved_per_tag_update_rate_hz == pytest.approx(1.0)
    assert result.collision_probability is None
    assert result.packet_delivery_probability is None
    assert result.max_supported_tags is not None


def test_scheduled_model_marks_overloaded_and_caps_achievable_rate():
    result = evaluate_scalability(
        method=RangingMethod.SS_TWR,
        anchor_count=8,
        tag_count=500,
        requested_update_rate_hz=10.0,
        frame_duration_s=0.001,
        guard_duration_s=0.0002,
        scheduling_model="scheduled",
    )
    assert result.overloaded is True
    assert result.achievable_fixes_per_second < result.requested_fixes_per_second
    assert result.achieved_per_tag_update_rate_hz < 10.0


def test_frames_per_fix_scales_with_anchor_count_in_scalability_result():
    r4 = evaluate_scalability(
        RangingMethod.SS_TWR, 4, 1, 1.0, 0.001, 0.0, "scheduled"
    )
    r8 = evaluate_scalability(
        RangingMethod.SS_TWR, 8, 1, 1.0, 0.001, 0.0, "scheduled"
    )
    assert r8.frames_per_fix == 2 * r4.frames_per_fix


def test_tdoa_frames_per_fix_is_one_not_twr_style():
    r = evaluate_scalability(
        RangingMethod.TDOA, 10, 1, 1.0, 0.001, 0.0, "scheduled"
    )
    assert r.frames_per_fix == 1


def test_aloha_model_reports_collision_and_delivery_probability():
    result = evaluate_scalability(
        method=RangingMethod.TDOA,
        anchor_count=6,
        tag_count=20,
        requested_update_rate_hz=2.0,
        frame_duration_s=0.001,
        guard_duration_s=0.0,
        scheduling_model="aloha",
        packet_loss_probability=0.05,
    )
    assert result.collision_probability is not None
    assert result.packet_delivery_probability is not None
    assert 0 <= result.packet_delivery_probability <= 1
    assert result.max_supported_tags is None  # no deterministic cap under ALOHA


def test_aloha_delivery_probability_accounts_for_configured_packet_loss():
    no_loss = evaluate_scalability(
        RangingMethod.TDOA, 6, 20, 2.0, 0.001, 0.0, "aloha", packet_loss_probability=0.0
    )
    with_loss = evaluate_scalability(
        RangingMethod.TDOA, 6, 20, 2.0, 0.001, 0.0, "aloha", packet_loss_probability=0.2
    )
    assert with_loss.packet_delivery_probability < no_loss.packet_delivery_probability


def test_overloaded_scheduled_scenario_is_flagged_infeasible_for_feasibility_layer():
    result = evaluate_scalability(
        RangingMethod.DS_TWR, 10, 1000, 20.0, 0.001, 0.0002, "scheduled"
    )
    assert result.overloaded is True
    assert result.scheduled_occupancy > 1.0


def test_invalid_scheduling_model_rejected():
    with pytest.raises(ValueError):
        evaluate_scalability(RangingMethod.TDOA, 4, 1, 1.0, 0.001, 0.0, "not-a-model")
