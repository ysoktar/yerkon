"""Scalability metrics: capacity, occupancy, overload, achievable rate.

Composes the traffic primitives in ``locbench3d.protocol.traffic`` into one
result per scenario. Two scheduling models are supported:

* ``"scheduled"``: TDMA-like, deterministic. Occupancy above 100% of a
  1-second channel-time budget is infeasible under this model, and the
  achievable aggregate fix rate is capped at the channel's capacity.
* ``"aloha"``: random access. Delivery probability degrades continuously
  with offered traffic (pure-ALOHA collision model) and combines with a
  configured packet-loss probability; there is no single deterministic
  "max tags" the way there is for scheduled access, so
  ``max_supported_tags`` is left ``None`` rather than guessed.

No queue-delay value is reported anywhere in this module, because no queue
model exists here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from locbench3d.protocol.traffic import (
    RangingMethod,
    aloha_collision_free_probability,
    aloha_delivery_probability,
    frames_per_fix,
    is_overloaded,
    max_supported_tags_scheduled,
    offered_load_fraction,
)

_CHANNEL_BUDGET_S = 1.0  # nominal 1-second normalized channel-time budget


@dataclass(frozen=True)
class ScalabilityResult:
    method: RangingMethod
    anchor_count: int
    tag_count: int
    requested_update_rate_hz: float
    frames_per_fix: int
    frame_duration_s: float
    guard_duration_s: float
    scheduling_model: str
    frames_per_second_offered: float
    airtime_fraction: float
    scheduled_occupancy: float
    overloaded: bool
    collision_probability: Optional[float]
    packet_delivery_probability: Optional[float]
    requested_fixes_per_second: float
    achievable_fixes_per_second: float
    achieved_per_tag_update_rate_hz: float
    max_supported_tags: Optional[int]
    energy_per_valid_fix_j: Optional[float] = None


def evaluate_scalability(
    method: RangingMethod,
    anchor_count: int,
    tag_count: int,
    requested_update_rate_hz: float,
    frame_duration_s: float,
    guard_duration_s: float,
    scheduling_model: str,
    packet_loss_probability: float = 0.0,
) -> ScalabilityResult:
    if scheduling_model not in ("scheduled", "aloha"):
        raise ValueError(
            f"scheduling_model must be 'scheduled' or 'aloha', got {scheduling_model!r}"
        )
    method = RangingMethod(method)
    fpf = frames_per_fix(method, anchor_count)
    frames_per_second_offered = tag_count * requested_update_rate_hz * fpf
    occupancy = offered_load_fraction(
        n_tags=tag_count,
        update_rate_hz=requested_update_rate_hz,
        frames_per_fix_count=fpf,
        frame_duration_s=frame_duration_s,
        guard_duration_s=guard_duration_s,
    )
    overloaded = is_overloaded(occupancy)
    requested_fixes_per_second = tag_count * requested_update_rate_hz

    if scheduling_model == "scheduled":
        per_fix_time = fpf * (frame_duration_s + guard_duration_s)
        capacity_fixes_per_second = (
            _CHANNEL_BUDGET_S / per_fix_time if per_fix_time > 0 else float("inf")
        )
        achievable_fixes_per_second = min(
            requested_fixes_per_second, capacity_fixes_per_second
        )
        max_supported_tags = max_supported_tags_scheduled(
            update_rate_hz=requested_update_rate_hz,
            frames_per_fix_count=fpf,
            frame_duration_s=frame_duration_s,
            guard_duration_s=guard_duration_s,
            channel_budget_s=_CHANNEL_BUDGET_S,
        )
        collision_probability = None
        packet_delivery_probability = None
    else:  # aloha
        p_frame_collision_free = aloha_collision_free_probability(
            attempts_per_second=frames_per_second_offered,
            frame_duration_s=frame_duration_s,
        )
        collision_probability = 1.0 - p_frame_collision_free
        p_frame_delivered = aloha_delivery_probability(
            attempts_per_second=frames_per_second_offered,
            frame_duration_s=frame_duration_s,
            packet_loss_probability=packet_loss_probability,
        )
        # A fix needs every one of its frames delivered; frames are treated
        # as independent trials on the shared channel.
        p_fix_delivered = p_frame_delivered**fpf
        packet_delivery_probability = p_fix_delivered
        achievable_fixes_per_second = requested_fixes_per_second * p_fix_delivered
        max_supported_tags = None  # no deterministic cap under random access

    achieved_per_tag_update_rate_hz = (
        achievable_fixes_per_second / tag_count if tag_count > 0 else 0.0
    )

    return ScalabilityResult(
        method=method,
        anchor_count=anchor_count,
        tag_count=tag_count,
        requested_update_rate_hz=requested_update_rate_hz,
        frames_per_fix=fpf,
        frame_duration_s=frame_duration_s,
        guard_duration_s=guard_duration_s,
        scheduling_model=scheduling_model,
        frames_per_second_offered=frames_per_second_offered,
        airtime_fraction=occupancy,
        scheduled_occupancy=occupancy,
        overloaded=overloaded,
        collision_probability=collision_probability,
        packet_delivery_probability=packet_delivery_probability,
        requested_fixes_per_second=requested_fixes_per_second,
        achievable_fixes_per_second=achievable_fixes_per_second,
        achieved_per_tag_update_rate_hz=achieved_per_tag_update_rate_hz,
        max_supported_tags=max_supported_tags,
    )
