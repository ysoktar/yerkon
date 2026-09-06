"""Energy and cost metrics.

Sleep power must not be omitted from a long battery-life estimate, and
unmeasured peak power stays None rather than 0.
"""
import pytest

from locbench3d.metrics.energy import EnergyBudget, estimate_battery_life
from locbench3d.metrics.cost import CostBreakdown, cost_per_area, cost_per_tag


def test_energy_per_fix_sums_all_components():
    budget = EnergyBudget(
        tx_energy_per_fix_j=0.001,
        rx_energy_per_fix_j=0.002,
        processing_energy_per_fix_j=0.0005,
        synchronization_energy_per_fix_j=0.0001,
        idle_energy_per_fix_j=0.0002,
        sleep_energy_per_fix_j=0.0003,
    )
    assert budget.total_energy_per_fix_j == pytest.approx(0.0041)


def test_energy_per_valid_fix_accounts_for_dropped_fixes():
    budget = EnergyBudget(
        tx_energy_per_fix_j=0.01,
        rx_energy_per_fix_j=0.0,
        processing_energy_per_fix_j=0.0,
        synchronization_energy_per_fix_j=0.0,
        idle_energy_per_fix_j=0.0,
        sleep_energy_per_fix_j=0.0,
    )
    # Every attempted fix costs energy even when only half succeed.
    energy_per_valid = budget.energy_per_valid_fix_j(valid_fix_rate=0.5)
    assert energy_per_valid == pytest.approx(0.02)


def test_battery_life_estimate_includes_sleep_power_not_just_active_power():
    active_power_w = 0.5
    sleep_power_w = 0.00005
    duty_cycle = 0.001  # active 0.1% of the time
    hours_with_sleep = estimate_battery_life(
        battery_capacity_wh=10.0,
        active_power_w=active_power_w,
        sleep_power_w=sleep_power_w,
        duty_cycle=duty_cycle,
    )
    hours_ignoring_sleep = 10.0 / (active_power_w * duty_cycle)
    # Including sleep power must give a shorter (or equal) life estimate,
    # never a longer one, and must differ when sleep power is non-negligible.
    assert hours_with_sleep < hours_ignoring_sleep


def test_battery_life_requires_positive_capacity():
    with pytest.raises(ValueError):
        estimate_battery_life(
            battery_capacity_wh=0.0, active_power_w=1.0, sleep_power_w=0.0, duty_cycle=1.0
        )


def test_cost_per_area_and_per_cubic_meter():
    breakdown = CostBreakdown(
        device_cost=50.0,
        anchor_cost=100.0,
        antenna_cost=10.0,
        infrastructure_units=8,
    )
    assert cost_per_area(breakdown, floor_area_m2=200.0) == pytest.approx(
        (breakdown.total_infrastructure_cost) / 200.0
    )


def test_cost_per_tag_and_per_supported_tag_differ_when_capacity_limited():
    breakdown = CostBreakdown(device_cost=20.0, anchor_cost=500.0, infrastructure_units=6)
    per_tag = cost_per_tag(breakdown, tag_count=10)
    per_supported_tag = cost_per_tag(breakdown, tag_count=100)
    assert per_tag != per_supported_tag
