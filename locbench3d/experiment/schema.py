"""Experiment scenario schema.

``ScenarioTemplate`` holds the fixed base configuration for an experiment;
``ScenarioSpec`` is one fully-resolved scenario (template values merged
with one point from the experiment's variable grid). Every optional field
left unset stays ``None`` through generation; nothing here invents a
default numeric value for a dimension the caller did not configure.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Optional


@dataclass(frozen=True)
class ScenarioTemplate:
    width_m: float
    length_m: float
    height_m: float
    frame_duration_s: float
    guard_duration_s: float
    hardware_profile: Optional[str] = None
    oscillator_profile: Optional[str] = None
    calibration_profile: Optional[str] = None
    anchor_layout: Optional[str] = None
    anchor_altitude_spread_m: Optional[float] = None
    path: Optional[str] = None
    speed_m_s: Optional[float] = None
    timing_uncertainty_m: Optional[float] = None
    clock_quality_ppm: Optional[float] = None
    synchronization_interval_s: Optional[float] = None
    reply_delay_s: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    center_freq_hz: Optional[float] = None
    snr_db: Optional[float] = None
    nlos_probability: Optional[float] = None
    nlos_bias_m: Optional[float] = None
    additional_measurement_uncertainty_m: Optional[float] = None
    packet_loss_probability: Optional[float] = None
    tx_power_dbm: Optional[float] = None
    scheduling_model: str = "scheduled"


TEMPLATE_FIELD_NAMES: tuple[str, ...] = tuple(f.name for f in fields(ScenarioTemplate))


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    method: str
    anchor_count: Optional[int]
    tag_count: Optional[int]
    update_rate_hz: Optional[float]
    width_m: float
    length_m: float
    height_m: float
    frame_duration_s: float
    guard_duration_s: float
    hardware_profile: Optional[str] = None
    oscillator_profile: Optional[str] = None
    calibration_profile: Optional[str] = None
    anchor_layout: Optional[str] = None
    anchor_altitude_spread_m: Optional[float] = None
    path: Optional[str] = None
    speed_m_s: Optional[float] = None
    timing_uncertainty_m: Optional[float] = None
    clock_quality_ppm: Optional[float] = None
    synchronization_interval_s: Optional[float] = None
    reply_delay_s: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    center_freq_hz: Optional[float] = None
    snr_db: Optional[float] = None
    nlos_probability: Optional[float] = None
    nlos_bias_m: Optional[float] = None
    additional_measurement_uncertainty_m: Optional[float] = None
    packet_loss_probability: Optional[float] = None
    tx_power_dbm: Optional[float] = None
    scheduling_model: str = "scheduled"
