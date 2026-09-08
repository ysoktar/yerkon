"""How well the anchor positions are actually known, and what that costs.

Every position solution in this project so far assumed the anchors sit
exactly where the layout says. No deployment knows that. Someone has to
survey each mounting point, and the residual error from that survey enters
the solution directly.

It is worth separating from ranging error because it behaves differently.
Ranging error is redrawn on every measurement, so averaging over a track
reduces it. A survey error is fixed for the life of the installation. The
filter cannot average it away, more anchors do not dilute it, and a longer
observation does not help. It sets a floor.

The floor matters most where the ranging is best. Urban ranging error is
around 2.4 m, so 8 cm of survey error changes nothing. Tunnel ranging
error is 0.36 m, and the tunnel is also the hardest place to survey,
because there is no sky and the position has to be carried in from a
portal by traverse.

The three specs below are this project's assumptions, chosen from what
each survey method can normally deliver. They are not quoted from a survey
report for this project, because none exists.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from yerkon.evidence import EvidenceRecord, EvidenceType


@dataclass(frozen=True)
class SurveySpec:
    """Residual position error left by one survey method, in metres."""

    method: str
    horizontal_sigma_m: float
    vertical_sigma_m: float
    evidence: EvidenceRecord
    #: Growth of the error with distance along a traverse, in metres per
    #: square root of a kilometre. A traverse accumulates error as a random
    #: walk, so a point 50 km along a tunnel is known far less well than one
    #: near the portal. ``None`` where the survey fixes each point
    #: independently, which is what any satellite method does.
    traverse_growth_m_per_sqrt_km: Optional[float] = None

    def sigma_at(self, distance_along_m: float) -> tuple[float, float]:
        """Horizontal and vertical sigma at a point on the traverse."""
        h, v = self.horizontal_sigma_m, self.vertical_sigma_m
        if self.traverse_growth_m_per_sqrt_km:
            grown = self.traverse_growth_m_per_sqrt_km * math.sqrt(
                max(distance_along_m, 0.0) / 1000.0
            )
            h = math.hypot(h, grown)
            v = math.hypot(v, grown)
        return h, v


_RTK_SCOPE = (
    "Residual error of a real-time kinematic satellite survey, after the "
    "baseline resolves. Each mounting point is fixed independently against "
    "a reference station, so the errors do not accumulate along the route."
)

URBAN_SURVEY = SurveySpec(
    method="RTK satellite survey in an urban canyon",
    horizontal_sigma_m=0.08,
    vertical_sigma_m=0.12,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="Assumed RTK survey residual, obstructed sky",
        source_scope=_RTK_SCOPE,
        caveats=(
            "8 cm horizontal and 12 cm vertical are this project's numbers. "
            "Open-sky RTK does better than this. A street between tall "
            "buildings does worse, because the same reflections that "
            "obstruct the ranging links also degrade the survey. The "
            "vertical figure is the larger one because satellite geometry "
            "is always weaker in height than in plan."
        ),
    ),
)

RURAL_SURVEY = SurveySpec(
    method="RTK satellite survey, open sky",
    horizontal_sigma_m=0.03,
    vertical_sigma_m=0.05,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="Assumed RTK survey residual, clear sky",
        source_scope=_RTK_SCOPE,
        caveats=(
            "3 cm horizontal and 5 cm vertical are this project's numbers, "
            "taken as what RTK normally delivers on an open highway verge. "
            "They are small next to the rural ranging error, so the rural "
            "row barely moves when they are applied."
        ),
    ),
)

TUNNEL_SURVEY = SurveySpec(
    method="Total station traverse from the portal",
    horizontal_sigma_m=0.005,
    vertical_sigma_m=0.005,
    traverse_growth_m_per_sqrt_km=0.015,
    evidence=EvidenceRecord(
        evidence_type=EvidenceType.ENGINEERING_ASSUMPTION,
        source_name="Assumed total station traverse residual in a tunnel",
        source_scope=(
            "A tunnel has no sky, so no satellite method reaches the "
            "mounting points. The position is carried in from a surveyed "
            "portal by a chain of instrument setups. Each setup adds a "
            "small independent error, so the total grows as the square root "
            "of the distance from the portal rather than staying constant."
        ),
        caveats=(
            "5 mm at the portal and 15 mm growth per square root kilometre "
            "are this project's numbers. At 50 km that reaches about 11 cm. "
            "A real tunnel survey controls this with gyro-theodolite "
            "azimuth checks and by traversing from both portals, which is "
            "why the assumed growth is modest. It is still the largest "
            "single term in the tunnel row's error budget, because the "
            "ranging error there is only 0.36 m."
        ),
    ),
)

SURVEY_BY_ENVIRONMENT = {
    "urban": URBAN_SURVEY,
    "rural": RURAL_SURVEY,
    "tunnel": TUNNEL_SURVEY,
}


def surveyed_positions(
    true_positions: np.ndarray,
    spec: SurveySpec,
    seed: int,
    traverse_axis: Optional[int] = None,
) -> np.ndarray:
    """Where the survey says the anchors are, given where they really are.

    Draw once per deployment and reuse. Redrawing per fix would turn a
    fixed installation error into noise that averages away, which is the
    opposite of how it behaves.

    ``traverse_axis`` names the coordinate that measures distance from the
    portal, for a survey whose error grows along a route. Leave it ``None``
    for a survey that fixes each point independently.
    """
    rng = np.random.default_rng(seed)
    offsets = np.zeros_like(true_positions, dtype=float)
    if traverse_axis is None:
        h, v = spec.horizontal_sigma_m, spec.vertical_sigma_m
        offsets[:, 0] = rng.normal(0.0, h, len(true_positions))
        offsets[:, 1] = rng.normal(0.0, h, len(true_positions))
        offsets[:, 2] = rng.normal(0.0, v, len(true_positions))
        return true_positions + offsets

    along = true_positions[:, traverse_axis]
    origin = float(np.min(along))
    for i, position_along in enumerate(along):
        h, v = spec.sigma_at(float(position_along) - origin)
        offsets[i, 0] = rng.normal(0.0, h)
        offsets[i, 1] = rng.normal(0.0, h)
        offsets[i, 2] = rng.normal(0.0, v)
    return true_positions + offsets


def rms_offset_m(true_positions: np.ndarray, surveyed: np.ndarray) -> float:
    """Root-mean-square 3D distance between true and surveyed positions."""
    delta = surveyed - true_positions
    return float(np.sqrt(np.mean(np.sum(delta**2, axis=1))))
