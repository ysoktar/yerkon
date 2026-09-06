"""Protocol traffic rules for multi-anchor 3D ranging fixes.

Frame counts and latency for a *complete* multi-anchor fix, not for a
single two-node exchange. It is a common modeling mistake to charge a
whole N-anchor TWR fix only 2 or 3 frames (the cost of one exchange); this
module scales both frame count and, for sequential exchanges, latency with
the number of participating anchors.

TDoA and one-way ToA/ToF are structurally different: the tag sends (or
anchors passively receive) one frame per fix, and anchor synchronization
or backhaul traffic is a separate concern this module does not fold in
unless the caller explicitly adds it (see ``sync_traffic_frames`` usage in
the experiment layer).
"""
from __future__ import annotations

import math
from enum import Enum


class RangingMethod(str, Enum):
    SS_TWR = "SS_TWR"
    DS_TWR = "DS_TWR"
    TDOA = "TDOA"
    TOA = "TOA"
    TOF = "TOF"


def frames_per_fix(method: RangingMethod, n_anchors: int) -> int:
    """Frames required for one complete multi-anchor 3D position fix.

    SS-TWR: framesPerFix = 2 * n_anchors
    DS-TWR: framesPerFix = 3 * n_anchors
    TDoA (tag-side blink model): framesPerFix = 1
    ToA / ToF (one-way): framesPerFix = 1
    """
    if n_anchors < 0:
        raise ValueError("n_anchors must not be negative")
    method = RangingMethod(method)
    if method is RangingMethod.SS_TWR:
        return 2 * n_anchors
    if method is RangingMethod.DS_TWR:
        return 3 * n_anchors
    if method in (RangingMethod.TDOA, RangingMethod.TOA, RangingMethod.TOF):
        return 1
    raise ValueError(f"unhandled ranging method {method!r}")


def sequential_fix_latency_s(
    method: RangingMethod,
    n_anchors: int,
    frame_duration_s: float,
    guard_duration_s: float = 0.0,
) -> float:
    """Latency of one complete fix when exchanges happen sequentially.

    For TWR variants, exchanges with each anchor happen one after another,
    so latency scales with the number of participating anchors (frames
    per fix times per-frame time). For TDoA and one-way ToA/ToF, the tag
    side only sends (or the receiver only processes) one frame regardless
    of how many anchors are listening, so latency does not scale with
    anchor count here; anchor synchronization/backhaul latency for TDoA is
    a separate, explicitly-modeled concern (see the TDoA method module),
    not folded into this tag-side latency.
    """
    if frame_duration_s < 0 or guard_duration_s < 0:
        raise ValueError("durations must not be negative")
    method = RangingMethod(method)
    per_frame = frame_duration_s + guard_duration_s
    if method in (RangingMethod.SS_TWR, RangingMethod.DS_TWR):
        return frames_per_fix(method, n_anchors) * per_frame
    # TDoA / TOA / TOF: one frame's worth of airtime, independent of anchor count.
    return 1 * per_frame


def offered_load_fraction(
    n_tags: int,
    update_rate_hz: float,
    frames_per_fix_count: int,
    frame_duration_s: float,
    guard_duration_s: float = 0.0,
) -> float:
    """Fraction of a 1-second channel-time budget consumed by all tags.

    load = n_tags * update_rate_hz * frames_per_fix * (frame + guard duration)

    A value above 1.0 means the offered traffic exceeds what a single
    shared channel can carry in scheduled (TDMA-like) operation; see
    ``is_overloaded``.
    """
    if n_tags < 0 or update_rate_hz < 0 or frames_per_fix_count < 0:
        raise ValueError("counts and rates must not be negative")
    return n_tags * update_rate_hz * frames_per_fix_count * (
        frame_duration_s + guard_duration_s
    )


def is_overloaded(occupancy_fraction: float) -> bool:
    """True when scheduled channel occupancy exceeds 100%.

    A scenario at or below 1.0 is not, by itself, marked overloaded here;
    the caller's feasibility layer may still apply a stricter margin.
    """
    return occupancy_fraction > 1.0


def max_supported_tags_scheduled(
    update_rate_hz: float,
    frames_per_fix_count: int,
    frame_duration_s: float,
    guard_duration_s: float = 0.0,
    channel_budget_s: float = 1.0,
) -> int:
    """Maximum tags a scheduled (TDMA-like) channel can support at this rate.

    Floor division: a partially-fitting tag is not counted as supported.
    """
    per_tag_load = update_rate_hz * frames_per_fix_count * (
        frame_duration_s + guard_duration_s
    )
    if per_tag_load <= 0:
        raise ValueError("per-tag load must be positive to bound tag count")
    return math.floor(channel_budget_s / per_tag_load)


def aloha_collision_free_probability(
    attempts_per_second: float, frame_duration_s: float
) -> float:
    """Pure-ALOHA probability a single frame survives without collision.

    P = exp(-2G), where G = attempts_per_second * frame_duration_s is the
    offered traffic normalized to frame-times, and the factor of 2 reflects
    pure ALOHA's vulnerable period of two frame times.
    """
    if attempts_per_second < 0 or frame_duration_s < 0:
        raise ValueError("rate and duration must not be negative")
    g = attempts_per_second * frame_duration_s
    return math.exp(-2.0 * g)


def aloha_delivery_probability(
    attempts_per_second: float,
    frame_duration_s: float,
    packet_loss_probability: float,
) -> float:
    """End-to-end delivery probability under ALOHA-style random access.

    Combines collision loss (pure-ALOHA model) with an independently
    configured packet-loss probability (e.g. from fading or interference).
    Both loss sources are multiplied together; neither is dropped.
    """
    if not (0.0 <= packet_loss_probability <= 1.0):
        raise ValueError("packet_loss_probability must be in [0, 1]")
    p_collision_free = aloha_collision_free_probability(
        attempts_per_second, frame_duration_s
    )
    return p_collision_free * (1.0 - packet_loss_probability)
