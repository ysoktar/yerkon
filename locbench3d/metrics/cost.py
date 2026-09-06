"""Cost metrics: CAPEX/OPEX breakdown and normalized cost figures."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CostBreakdown:
    device_cost: float = 0.0
    anchor_cost: float = 0.0
    antenna_cost: float = 0.0
    compute_cost: float = 0.0
    installation_cost: float = 0.0
    survey_cost: float = 0.0
    calibration_cost: float = 0.0
    correction_service_cost: float = 0.0
    annual_subscription: float = 0.0
    maintenance_cost: float = 0.0
    infrastructure_units: Optional[int] = None

    @property
    def capex(self) -> float:
        return (
            self.device_cost
            + self.anchor_cost
            + self.antenna_cost
            + self.compute_cost
            + self.installation_cost
            + self.survey_cost
            + self.calibration_cost
        )

    @property
    def opex_annual(self) -> float:
        return self.correction_service_cost + self.annual_subscription + self.maintenance_cost

    @property
    def total_infrastructure_cost(self) -> float:
        """CAPEX only; recurring OPEX is reported separately, not folded in."""
        return self.capex


def cost_per_area(breakdown: CostBreakdown, floor_area_m2: float) -> float:
    if floor_area_m2 <= 0:
        raise ValueError("floor_area_m2 must be positive")
    return breakdown.total_infrastructure_cost / floor_area_m2


def cost_per_volume(breakdown: CostBreakdown, volume_m3: float) -> float:
    if volume_m3 <= 0:
        raise ValueError("volume_m3 must be positive")
    return breakdown.total_infrastructure_cost / volume_m3


def cost_per_tag(breakdown: CostBreakdown, tag_count: int) -> float:
    if tag_count <= 0:
        raise ValueError("tag_count must be positive")
    return breakdown.total_infrastructure_cost / tag_count


def infrastructure_units_per_1000_sqm(breakdown: CostBreakdown, floor_area_m2: float) -> Optional[float]:
    if breakdown.infrastructure_units is None:
        return None
    if floor_area_m2 <= 0:
        raise ValueError("floor_area_m2 must be positive")
    return breakdown.infrastructure_units / floor_area_m2 * 1000.0


def infrastructure_units_per_1000_m3(breakdown: CostBreakdown, volume_m3: float) -> Optional[float]:
    if breakdown.infrastructure_units is None:
        return None
    if volume_m3 <= 0:
        raise ValueError("volume_m3 must be positive")
    return breakdown.infrastructure_units / volume_m3 * 1000.0
