"""Protocol traffic rules: frames per fix, sequential latency, capacity.

These encode the requirements that are easy to get wrong: SS-TWR/DS-TWR
frame counts must scale with anchor count (not be a fixed 2 or 3 for a
whole multi-anchor fix), sequential latency must scale with anchor count,
TDoA and one-way ToA/ToF must not be charged TWR frame counts, and an
overloaded scenario must be marked infeasible rather than silently
under-reporting achieved rate.
"""
import math

import pytest

from locbench3d.protocol.traffic import (
    RangingMethod,
    aloha_delivery_probability,
    frames_per_fix,
    is_overloaded,
    max_supported_tags_scheduled,
    offered_load_fraction,
    sequential_fix_latency_s,
)


@pytest.mark.parametrize("n_anchors", [4, 5, 8, 20])
def test_ss_twr_frames_scale_with_anchor_count(n_anchors):
    assert frames_per_fix(RangingMethod.SS_TWR, n_anchors) == 2 * n_anchors


@pytest.mark.parametrize("n_anchors", [4, 5, 8, 20])
def test_ds_twr_frames_scale_with_anchor_count(n_anchors):
    assert frames_per_fix(RangingMethod.DS_TWR, n_anchors) == 3 * n_anchors


def test_ss_twr_frames_are_not_fixed_at_two_for_multi_anchor_fix():
    """A complete multi-anchor fix must not be charged only 2 frames total."""
    assert frames_per_fix(RangingMethod.SS_TWR, 10) == 20
    assert frames_per_fix(RangingMethod.SS_TWR, 10) != 2


def test_tdoa_tag_side_is_one_frame_regardless_of_anchor_count():
    assert frames_per_fix(RangingMethod.TDOA, 4) == 1
    assert frames_per_fix(RangingMethod.TDOA, 50) == 1


def test_toa_one_way_is_one_frame():
    assert frames_per_fix(RangingMethod.TOA, 6) == 1
    assert frames_per_fix(RangingMethod.TOF, 6) == 1


def test_sequential_twr_latency_scales_with_anchor_count():
    frame_s = 0.001
    guard_s = 0.0005
    latency_4 = sequential_fix_latency_s(RangingMethod.SS_TWR, 4, frame_s, guard_s)
    latency_8 = sequential_fix_latency_s(RangingMethod.SS_TWR, 8, frame_s, guard_s)
    assert latency_8 == pytest.approx(2 * latency_4)
    assert latency_4 == pytest.approx(2 * 4 * (frame_s + guard_s))


def test_tdoa_latency_does_not_scale_with_anchor_count_for_tag_side_blink():
    frame_s = 0.001
    guard_s = 0.0002
    latency_a = sequential_fix_latency_s(RangingMethod.TDOA, 4, frame_s, guard_s)
    latency_b = sequential_fix_latency_s(RangingMethod.TDOA, 40, frame_s, guard_s)
    assert latency_a == pytest.approx(latency_b)


def test_offered_load_and_overload_flag():
    load = offered_load_fraction(
        n_tags=10,
        update_rate_hz=5,
        frames_per_fix_count=8,
        frame_duration_s=0.001,
        guard_duration_s=0.0002,
    )
    assert load == pytest.approx(10 * 5 * 8 * 0.0012)
    assert is_overloaded(load) == (load > 1.0)


def test_scenario_marked_infeasible_when_occupancy_exceeds_100_percent():
    load = offered_load_fraction(
        n_tags=1000,
        update_rate_hz=10,
        frames_per_fix_count=8,
        frame_duration_s=0.001,
        guard_duration_s=0.0,
    )
    assert load > 1.0
    assert is_overloaded(load) is True


def test_max_supported_tags_scheduled_is_capacity_floor():
    max_tags = max_supported_tags_scheduled(
        update_rate_hz=5,
        frames_per_fix_count=8,
        frame_duration_s=0.001,
        guard_duration_s=0.0002,
        channel_budget_s=1.0,
    )
    per_tag_load = 5 * 8 * 0.0012
    assert max_tags == math.floor(1.0 / per_tag_load)


def test_aloha_delivery_probability_includes_collision_and_packet_loss():
    p_no_loss = aloha_delivery_probability(
        attempts_per_second=50,
        frame_duration_s=0.001,
        packet_loss_probability=0.0,
    )
    p_with_loss = aloha_delivery_probability(
        attempts_per_second=50,
        frame_duration_s=0.001,
        packet_loss_probability=0.1,
    )
    assert 0 < p_with_loss < p_no_loss < 1
    # Matches classic pure-ALOHA collision-free probability exp(-2G).
    g = 50 * 0.001
    expected_collision_free = math.exp(-2 * g)
    assert p_no_loss == pytest.approx(expected_collision_free)
    assert p_with_loss == pytest.approx(expected_collision_free * 0.9)


def test_aloha_delivery_probability_worsens_with_more_offered_traffic():
    low = aloha_delivery_probability(10, 0.001, 0.0)
    high = aloha_delivery_probability(500, 0.001, 0.0)
    assert high < low


def test_unknown_method_rejected():
    with pytest.raises(ValueError):
        frames_per_fix("not-a-method", 4)  # type: ignore[arg-type]
