"""Energy metrics: per-fix energy budget and battery-life estimation.

Sleep power is always included in a battery-life estimate; a duty-cycled
device spends most of its life asleep, and omitting sleep power from a
"long battery life" claim is exactly the kind of error this project's
requirements call out.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EnergyBudget:
    tx_energy_per_fix_j: float
    rx_energy_per_fix_j: float
    processing_energy_per_fix_j: float
    synchronization_energy_per_fix_j: float
    idle_energy_per_fix_j: float
    sleep_energy_per_fix_j: float
    peak_power_w: Optional[float] = None  # only set when actually measured

    @property
    def total_energy_per_fix_j(self) -> float:
        return (
            self.tx_energy_per_fix_j
            + self.rx_energy_per_fix_j
            + self.processing_energy_per_fix_j
            + self.synchronization_energy_per_fix_j
            + self.idle_energy_per_fix_j
            + self.sleep_energy_per_fix_j
        )

    def energy_per_valid_fix_j(self, valid_fix_rate: float) -> float:
        """Energy spent per valid fix, accounting for attempts that fail.

        Every *attempted* fix spends energy; only a fraction become valid,
        so the energy cost per valid fix is higher than the per-attempt
        energy whenever the valid-fix rate is below 1.
        """
        if not (0.0 < valid_fix_rate <= 1.0):
            raise ValueError("valid_fix_rate must be in (0, 1]")
        return self.total_energy_per_fix_j / valid_fix_rate

    def average_power_w(self, fixes_per_second: float) -> float:
        if fixes_per_second < 0:
            raise ValueError("fixes_per_second must not be negative")
        return self.total_energy_per_fix_j * fixes_per_second


def estimate_battery_life(
    battery_capacity_wh: float,
    active_power_w: float,
    sleep_power_w: float,
    duty_cycle: float,
) -> float:
    """Estimated battery life in hours, including sleep-mode power draw.

    duty_cycle is the fraction of time spent active (not asleep), in
    [0, 1]. Average power = active_power*duty_cycle + sleep_power*(1-duty_cycle).
    """
    if battery_capacity_wh <= 0:
        raise ValueError("battery_capacity_wh must be positive")
    if not (0.0 <= duty_cycle <= 1.0):
        raise ValueError("duty_cycle must be in [0, 1]")
    average_power_w = active_power_w * duty_cycle + sleep_power_w * (1.0 - duty_cycle)
    if average_power_w <= 0:
        raise ValueError("average power must be positive to estimate battery life")
    return battery_capacity_wh / average_power_w


def estimate_battery_life_days(
    battery_capacity_wh: float,
    active_power_w: float,
    sleep_power_w: float,
    duty_cycle: float,
) -> float:
    return (
        estimate_battery_life(battery_capacity_wh, active_power_w, sleep_power_w, duty_cycle)
        / 24.0
    )
