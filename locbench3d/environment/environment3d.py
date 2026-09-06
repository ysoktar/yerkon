"""3D environment description and the density/coverage planning approximation.

``anchor_density_3d`` and ``poisson_expected_anchors_in_range`` are a
simple planning approximation (uniform Poisson-distributed anchor
placement), not a geometry-validity claim. Actual geometry validity comes
from ``core.geometry_bounds.evaluate_geometry``, which accounts for real
anchor positions, coplanarity, and conditioning; a volume with plenty of
anchors by this density formula can still fail geometry validity if they
are badly placed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Environment3D:
    environment_id: str
    width_m: float
    length_m: float
    height_m: float
    floor_count: int
    floor_height_m: float
    indoor_outdoor: str  # "indoor" | "outdoor" | "mixed"
    environment_class: str  # free text: "office", "warehouse", "urban canyon", ...
    los_fraction: float
    nlos_fraction: float
    nlos_bias_m: Optional[float] = None
    extra_uncertainty_m: Optional[float] = None
    packet_loss_probability: Optional[float] = None
    obstacle_profile: Optional[str] = None
    material_profile: Optional[str] = None
    moving_obstacle_state: Optional[str] = None
    anchor_count: Optional[int] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.los_fraction <= 1.0):
            raise ValueError("los_fraction must be in [0, 1]")
        if not (0.0 <= self.nlos_fraction <= 1.0):
            raise ValueError("nlos_fraction must be in [0, 1]")
        if self.los_fraction + self.nlos_fraction > 1.0 + 1e-9:
            raise ValueError("los_fraction + nlos_fraction must not exceed 1")
        if self.width_m <= 0 or self.length_m <= 0 or self.height_m <= 0:
            raise ValueError("environment dimensions must be positive")

    @property
    def floor_area_m2(self) -> float:
        return self.width_m * self.length_m

    @property
    def volume_m3(self) -> float:
        return self.width_m * self.length_m * self.height_m

    @property
    def anchors_per_sqm(self) -> Optional[float]:
        if self.anchor_count is None:
            return None
        return self.anchor_count / self.floor_area_m2

    @property
    def anchors_per_cubic_m(self) -> Optional[float]:
        if self.anchor_count is None:
            return None
        return self.anchor_count / self.volume_m3


def anchor_density_3d(n_anchors: int, volume_m3: float) -> float:
    """rho_3D = N_a / V"""
    if volume_m3 <= 0:
        raise ValueError("volume_m3 must be positive")
    return n_anchors / volume_m3


def poisson_expected_anchors_in_range(density_3d: float, radius_m: float) -> float:
    """mu = rho_3D * (4/3) * pi * R^3, a Poisson-model planning approximation.

    This treats anchors as uniformly randomly placed in 3D, which real
    deployments rarely are. Use it for rough coverage planning only, never
    as a substitute for evaluating actual anchor geometry.
    """
    if radius_m < 0:
        raise ValueError("radius_m must not be negative")
    return density_3d * (4.0 / 3.0) * math.pi * radius_m**3


def poisson_coverage_probability(mu: float, min_anchors: int) -> float:
    """P(at least min_anchors anchors within range), under the Poisson planning model.

    Uses the Poisson survival function; still a planning approximation, not
    a measured or geometry-checked coverage probability.
    """
    if mu < 0:
        raise ValueError("mu must not be negative")
    if min_anchors <= 0:
        return 1.0
    # P(N >= k) = 1 - P(N <= k-1), computed directly to avoid a scipy dependency
    # for this one small sum.
    cumulative = 0.0
    term = math.exp(-mu)
    cumulative += term
    for i in range(1, min_anchors):
        term *= mu / i
        cumulative += term
    return 1.0 - cumulative
