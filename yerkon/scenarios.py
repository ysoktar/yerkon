"""The four YERKON deployment cases that fill the comparison table.

Each case states its coverage area, its anchor layout, the radio it uses,
and where every one of those numbers came from. Anchor layouts are built
here rather than taken from a generic preset, because the geometry is the
result: a preset that scatters anchors around a box would answer a
question nobody asked about a system mounted on poles, road signs and
tunnel walls.

Every coverage area is at least 1 km², so the CAPEX column compares like
with like. That constraint is what sets the anchor counts: a 1 km² urban
cell needs a grid, and a tunnel only reaches 1 km² of plan area after tens
of kilometres of running length.

See docs/SCENARIOS.md for the full parameter tables and docs/METHOD.md for
how each table column is computed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from yerkon.evidence import EvidenceRecord, assumption, from_deck
from yerkon.link_budget import (
    RURAL_LINK_RANGE,
    TUNNEL_LINK_RANGE,
    URBAN_LINK_RANGE,
    minimum_spacing_for_fix,
)
from yerkon.geometry import (
    dop_from_jacobian,
    evaluate_geometry,
    range_jacobian,
    true_ranges,
)
from yerkon.metrics import (
    AccuracyResult,
    CostBreakdown,
    ReliabilityResult,
    compute_accuracy_metrics,
    compute_reliability_metrics,
    cost_per_area,
)
from yerkon.path import Path3D, straight_line_path, zigzag_path
from yerkon.ranging_error import (
    ROBINSON_VALID_RANGE_M,
    RangingErrorModel,
    add_nlos,
    build_dwm3000_model,
    build_sx1280_model,
)
from yerkon.simulate import (
    RangingMethod,
    anchors_in_range,
    select_anchors,
    simulate_path_fixes,
)

SEED = 42
N_REPEATS = 300
N_PATH_SAMPLES = 24
ACCURACY_THRESHOLDS_M = [0.5, 1.0, 2.0, 5.0]

#: How many anchors a receiver ranges to per fix, nearest first. Two-way
#: ranging spends airtime per anchor, and the report describes the receiver
#: as talking to "enough" broadcast units rather than to every audible one.
#: Eight leaves redundancy over the four a 3D fix needs, and keeps the
#: links short enough that most of them fall inside the range envelope the
#: SX1280 error measurements cover.
MAX_ANCHORS_PER_FIX = 8

# Bulk (100-unit) component prices from the YERKON presentation's own BOM
# table, in TL. Component cost only: no installation, certification,
# groundwork, power or labour. Real CAPEX is higher, and by an amount this
# project cannot estimate from the presentation.
UNIT_PRICE_TL = {
    "urban": 1366.07,
    "rural": 1082.68,
    "critical": 1634.44,
}

_PRICE_EVIDENCE = from_deck(
    "YERKON presentation, bulk component price table (100-unit tier)",
    "Component bill-of-materials prices only. Excludes installation, "
    "certification, groundwork, power supply, backhaul and labour, which "
    "the presentation itself lists separately or not at all.",
)


@dataclass(frozen=True)
class AnchorGroup:
    """Anchors sharing one mounting type, and what they cost."""

    label: str
    positions: np.ndarray
    unit_price_tl: float
    evidence: EvidenceRecord

    @property
    def count(self) -> int:
        return int(len(self.positions))

    @property
    def total_cost_tl(self) -> float:
        return self.count * self.unit_price_tl


@dataclass(frozen=True)
class Scenario:
    """One deployment case: where the anchors are, what radio they use, and
    over what area the resulting accuracy is claimed."""

    key: str
    display_name: str
    technology: str
    environment: str
    groups: tuple[AnchorGroup, ...]
    path: Path3D
    error_model: RangingErrorModel
    area_km2: float
    max_link_range_m: float
    packet_loss_probability: float
    corridor_length_km: Optional[float] = None
    parameter_evidence: tuple[EvidenceRecord, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def evidence_records(self) -> tuple[EvidenceRecord, ...]:
        """Every declared source behind this scenario: the error model, the
        anchor layouts, and the standalone parameter assumptions."""
        return (
            (self.error_model.evidence,)
            + tuple(g.evidence for g in self.groups)
            + self.parameter_evidence
        )

    @property
    def anchors(self) -> np.ndarray:
        return np.vstack([g.positions for g in self.groups])

    @property
    def anchor_count(self) -> int:
        return int(len(self.anchors))

    @property
    def capex_total_tl(self) -> float:
        return sum(g.total_cost_tl for g in self.groups)


def _jitter(rng: np.random.Generator, n: int, amplitude_m: float) -> np.ndarray:
    """Small seeded variation in mounting height.

    Real installations are never on a perfect lattice, and a perfect
    lattice can produce degenerate geometry that no real deployment would
    have. The amplitude is deliberately smaller than the spacing between
    mount classes, so it varies the layout without blurring them together.
    """
    return rng.uniform(-amplitude_m, amplitude_m, n)


# ---------------------------------------------------------------------------
# Anchor layouts
# ---------------------------------------------------------------------------

#: Urban mounting heights, from the presentation's own list of mounting
#: points: street furniture, building facades, and rooftops.
URBAN_MOUNT_HEIGHTS_M = (8.0, 20.0, 35.0)


def urban_grid_layout(
    side_m: float = 1000.0, spacing_m: float = 250.0, seed: int = SEED
) -> AnchorGroup:
    """A grid of city broadcast units over a square cell.

    Spacing is set from the assumed urban link range: at 250 m spacing and
    a 400 m range, a receiver anywhere in the cell reaches the surrounding
    3x3 block of anchors, which is enough for a redundant 3D fix. Mount
    heights cycle through the three classes so that neighbouring anchors
    differ in height; a grid at one uniform height is coplanar and cannot
    resolve the vertical axis at all.
    """
    rng = np.random.default_rng(seed)
    coords = np.arange(0.0, side_m + 1e-9, spacing_m)
    positions = []
    for i, x in enumerate(coords):
        for j, y in enumerate(coords):
            height = URBAN_MOUNT_HEIGHTS_M[(i + 2 * j) % len(URBAN_MOUNT_HEIGHTS_M)]
            positions.append((x, y, height))
    positions = np.array(positions, dtype=float)
    positions[:, 2] += _jitter(rng, len(positions), 0.75)
    return AnchorGroup(
        label="Şehir içi yayın birimi (direk / cephe / çatı montajı)",
        positions=positions,
        unit_price_tl=UNIT_PRICE_TL["urban"],
        evidence=assumption(
            "Urban grid layout, {:.0f} m spacing over a {:.0f} m cell".format(
                spacing_m, side_m
            ),
            "Grid spacing and the three mounting heights are this project's "
            "choice, sized to the assumed urban link range. The presentation "
            "names the mounting classes but gives no spacing or cell size.",
        ),
    )


def roadside_layout(
    length_m: float = 42000.0,
    sign_spacing_m: float = 500.0,
    road_half_width_m: float = 12.0,
    sign_height_m: float = 6.0,
    seed: int = SEED,
) -> AnchorGroup:
    """Units on facing road-sign gantries down both sides of the road.

    Signs come in facing pairs across the carriageway, which is what makes
    this layout worth building: a pair 24 m apart seen from a receiver on
    the road subtends a steep enough elevation angle to constrain height,
    while a line of distant masts does not.
    """
    rng = np.random.default_rng(seed + 1)
    x = np.arange(0.0, length_m + 1e-9, sign_spacing_m)
    positions = []
    for xi in x:
        positions.append((xi, +road_half_width_m, sign_height_m))
        positions.append((xi, -road_half_width_m, sign_height_m))
    positions = np.array(positions, dtype=float)
    positions[:, 2] += _jitter(rng, len(positions), 0.5)
    return AnchorGroup(
        label="Yol levhası üstü yayın birimi (karşılıklı, iki yol kenarı)",
        positions=positions,
        unit_price_tl=UNIT_PRICE_TL["rural"],
        evidence=assumption(
            "Facing roadside sign mounts every {:.0f} m at {:.1f} m height".format(
                sign_spacing_m, sign_height_m
            ),
            "Sign spacing, the 6 m mounting height and the 12 m road half "
            "width are this project's assumptions, chosen to match typical "
            "Turkish divided-highway signage. The presentation states that "
            "existing roadside infrastructure is used but gives no spacing.",
        ),
    )


def mast_layout(
    length_m: float = 42000.0,
    spacing_m: float = 2500.0,
    offset_m: float = 30.0,
    seed: int = SEED,
) -> AnchorGroup:
    """Sparse tall masts along the same corridor.

    These are the anchors that see over the terrain and carry the link
    budget between sign clusters. They are also the only ones high enough
    to give a receiver a steep elevation angle from several hundred metres
    away, which is where the roadside pairs stop helping.
    """
    rng = np.random.default_rng(seed + 2)
    x = np.arange(0.0, length_m + 1e-9, spacing_m)
    heights = rng.uniform(35.0, 45.0, len(x))
    sides = np.where(np.arange(len(x)) % 2 == 0, 1.0, -1.0)
    positions = np.column_stack([x, sides * offset_m, heights])
    return AnchorGroup(
        label="Kırsal kule/direk yayın birimi (35-45 m)",
        positions=positions,
        unit_price_tl=UNIT_PRICE_TL["rural"],
        evidence=assumption(
            "Masts every {:.0f} m at 35-45 m height".format(spacing_m),
            "Mast spacing and heights are this project's assumptions for "
            "existing roadside mast infrastructure. The presentation "
            "mentions mast mounting without stating a spacing.",
        ),
    )


def tunnel_layout(
    length_m: float = 50000.0,
    spacing_m: float = 60.0,
    width_m: float = 20.0,
    seed: int = SEED,
) -> AnchorGroup:
    """Wall and ceiling mounts running the length of a tunnel network.

    Mounts alternate between the two walls and between wall and ceiling
    height on a four-step cycle. A two-step cycle would put every anchor on
    one of two parallel lines, and two parallel lines in 3D are always
    coplanar, which makes the vertical axis unsolvable no matter how many
    anchors are added.
    """
    rng = np.random.default_rng(seed + 3)
    x = np.arange(0.0, length_m, spacing_m)
    cycle = (
        (0.1 * width_m, 1.2),
        (0.9 * width_m, 4.3),
        (0.15 * width_m, 4.4),
        (0.85 * width_m, 1.3),
    )
    positions = np.array(
        [(xi, *cycle[i % len(cycle)]) for i, xi in enumerate(x)], dtype=float
    )
    positions[:, 2] += _jitter(rng, len(positions), 0.25)
    return AnchorGroup(
        label="Tünel duvar/tavan yayın birimi (UWB)",
        positions=positions,
        unit_price_tl=UNIT_PRICE_TL["critical"],
        evidence=from_deck(
            "Tunnel node spacing of {:.0f} m".format(spacing_m),
            "Spacing follows the presentation's own pilot figure of 10-15 "
            "broadcast nodes per 2 km corridor. Wall and ceiling mounting "
            "heights and the alternating pattern are this project's "
            "assumptions.",
        ),
    )


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

URBAN_LINK_RANGE_M = URBAN_LINK_RANGE.range_m
RURAL_LINK_RANGE_M = RURAL_LINK_RANGE.range_m
TUNNEL_LINK_RANGE_M = TUNNEL_LINK_RANGE.range_m

#: Tunnel node spacing follows from the DWM3000's real range rather than
#: from the report's pilot figure. The report proposes 10-15 nodes per 2 km
#: corridor, which is roughly 150 m apart; at a 150 m link range that
#: leaves a receiver hearing one or two nodes, and a 3D fix needs four.
#: minimum_spacing_for_fix gives 75 m as the ceiling, and 60 m is used to
#: keep a fifth node in range as margin.
TUNNEL_MAX_SPACING_FOR_FIX_M = minimum_spacing_for_fix(TUNNEL_LINK_RANGE_M)
TUNNEL_NODE_SPACING_M = 60.0

_NLOS_EVIDENCE = assumption(
    "NLOS probabilities and bias magnitudes per environment",
    "Fraction of links carrying an obstruction bias, and how large that "
    "bias is, are set per environment by this project. Neither the "
    "report nor the ranging measurements distinguish line-of-sight "
    "from obstructed links.",
)


def urban_scenario(calibrated: bool = True, seed: int = SEED) -> Scenario:
    """1 km x 1 km city cell served by SX1280 units on a 150 m grid.

    Grid spacing is the main design knob here, and it buys vertical
    accuracy rather than horizontal: going from 250 m to 150 m spacing
    doubles the unit count and roughly halves VDOP, while HDOP barely
    moves. docs/SCENARIOS.md tabulates the trade.
    """
    side_m = 1000.0
    model = add_nlos(
        build_sx1280_model(seed=seed, calibrated=calibrated),
        seed=seed + 10,
        nlos_probability=0.35,
        nlos_bias_m=1.5,
    )
    suffix = "Kalibreli" if calibrated else "Ham"
    return Scenario(
        key="urban_calibrated" if calibrated else "urban_uncalibrated",
        display_name="YERKON (Şehir İçi - {})".format(suffix),
        technology="Karasal PNT (SX1280/LoRa TWR)",
        environment="Dış",
        groups=(urban_grid_layout(side_m=side_m, spacing_m=150.0, seed=seed),),
        path=straight_line_path(
            "urban-diagonal",
            (60.0, 90.0, 1.5),
            (940.0, 910.0, 1.5),
            n_samples=N_PATH_SAMPLES,
            duration_s=600.0,
        ),
        error_model=model,
        area_km2=(side_m / 1000.0) ** 2,
        max_link_range_m=URBAN_LINK_RANGE_M,
        packet_loss_probability=0.02,
        parameter_evidence=(URBAN_LINK_RANGE.evidence, _PRICE_EVIDENCE, _NLOS_EVIDENCE),
        notes=(
            "35% of links carry a 1.5 m NLOS bias, representing urban canyon "
            "reflection off buildings.",
        ),
    )


def rural_scenario(seed: int = SEED) -> Scenario:
    """42 km highway corridor with facing roadside signs plus sparse masts.

    Coverage is the carriageway between the two sign lines, not a wide
    swath either side of it, and the corridor is long enough that this
    still comes to just over 1 km². That choice is the whole result of the
    rural case: standing between two facing sign mounts gives a receiver
    VDOP near 2, while moving 50 m off to one side pushes it past 25,
    because every anchor then sits on the same side at the same height.
    Quoting an accuracy figure over a wide swath would average those two
    regimes into a number that describes neither. docs/SCENARIOS.md
    tabulates the fall-off.
    """
    length_m = 42000.0
    half_width_m = 12.0
    model = add_nlos(
        build_sx1280_model(seed=seed, calibrated=True),
        seed=seed + 11,
        nlos_probability=0.15,
        nlos_bias_m=2.0,
    )
    return Scenario(
        key="rural",
        display_name="YERKON (Kırsal)",
        technology="Karasal PNT (E28-SX1280 TWR)",
        environment="Dış",
        groups=(
            roadside_layout(length_m=length_m, sign_spacing_m=500.0, seed=seed),
            mast_layout(length_m=length_m, spacing_m=2500.0, seed=seed),
        ),
        path=zigzag_path(
            "rural-corridor-sweep",
            x_start=500.0,
            x_end=41500.0,
            y_amplitude=0.9 * half_width_m,
            z_m=1.5,
            n_samples=N_PATH_SAMPLES,
            duration_s=1800.0,
            n_crossings=7,
        ),
        error_model=model,
        area_km2=(length_m / 1000.0) * (2 * half_width_m / 1000.0),
        max_link_range_m=RURAL_LINK_RANGE_M,
        packet_loss_probability=0.01,
        corridor_length_km=length_m / 1000.0,
        parameter_evidence=(RURAL_LINK_RANGE.evidence, _PRICE_EVIDENCE, _NLOS_EVIDENCE),
        notes=(
            "Coverage is the {:.0f} m wide carriageway between the facing "
            "sign lines, over a {:.0f} km corridor. The test path weaves "
            "across the carriageway rather than tracking the centreline.".format(
                2 * half_width_m, length_m / 1000.0
            ),
            "Vertical accuracy degrades sharply outside the sign lines: VDOP "
            "is near 2 on the carriageway and above 25 at 50 m off-road.",
            "15% of links carry a 2.0 m NLOS bias, representing terrain and "
            "vegetation obstruction.",
        ),
    )


def critical_zone_scenario(seed: int = SEED) -> Scenario:
    """50 km tunnel network, the running length that reaches 1 km² of plan area."""
    length_m = 50000.0
    width_m = 20.0
    model = build_dwm3000_model(
        seed=seed, sigma_m=0.03, nlos_probability=0.10, nlos_bias_m=0.30
    )
    return Scenario(
        key="critical",
        display_name="YERKON (Kritik Bölge/Tünel)",
        technology="Karasal PNT (UWB/DWM3000 TWR)",
        environment="İç + dış",
        groups=(tunnel_layout(
                length_m=length_m,
                spacing_m=TUNNEL_NODE_SPACING_M,
                width_m=width_m,
                seed=seed,
            ),),
        path=straight_line_path(
            "tunnel-run",
            (320.0, 0.45 * width_m, 1.5),
            (49680.0, 0.55 * width_m, 1.5),
            n_samples=N_PATH_SAMPLES,
            duration_s=1800.0,
        ),
        error_model=model,
        area_km2=(length_m / 1000.0) * (width_m / 1000.0),
        max_link_range_m=TUNNEL_LINK_RANGE_M,
        packet_loss_probability=0.03,
        corridor_length_km=length_m / 1000.0,
        parameter_evidence=(TUNNEL_LINK_RANGE.evidence, _PRICE_EVIDENCE, _NLOS_EVIDENCE),
        notes=(
            "A tunnel only reaches 1 km² of plan area after 50 km of running "
            "length at 20 m width, so cost per km² is dominated by that "
            "geometry. Cost per km of tunnel is the more useful figure and "
            "is reported alongside it.",
        ),
    )


def all_scenarios(seed: int = SEED) -> list[Scenario]:
    """The four table rows, in the order they appear in the output."""
    return [
        urban_scenario(calibrated=True, seed=seed),
        urban_scenario(calibrated=False, seed=seed),
        rural_scenario(seed=seed),
        critical_zone_scenario(seed=seed),
    ]


# ---------------------------------------------------------------------------
# Running a scenario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeometryProfile:
    """Geometry quality along the path, summarised.

    VDOP is reported separately from HDOP because the two behave very
    differently in every one of these layouts, and a single combined number
    would hide the entire vertical story.
    """

    median_anchors_reachable: float
    median_anchors_used: float
    min_anchors_used: int
    median_hdop: Optional[float]
    median_vdop: Optional[float]
    worst_vdop: Optional[float]
    median_condition_number: Optional[float]
    samples_below_minimum_anchors: int
    median_link_range_m: float
    max_link_range_m: float
    links_beyond_calibrated_envelope: Optional[float]


def profile_geometry(scenario: Scenario, minimum_anchors: int = 4) -> GeometryProfile:
    """Measure what geometry the layout actually offers along the path."""
    anchors = scenario.anchors
    sigma = scenario.error_model.sigma_m()
    reachable: list[int] = []
    counts: list[int] = []
    hdops: list[float] = []
    vdops: list[float] = []
    conds: list[float] = []
    ranges: list[float] = []

    for point in scenario.path.points():
        reachable.append(
            int(anchors_in_range(point, anchors, scenario.max_link_range_m).sum())
        )
        visible = select_anchors(
            point, anchors, scenario.max_link_range_m, MAX_ANCHORS_PER_FIX
        )
        counts.append(int(len(visible)))
        if len(visible) == 0:
            continue
        ranges.extend(true_ranges(point, visible).tolist())
        if len(visible) < minimum_anchors:
            continue
        geom = evaluate_geometry(
            point, visible, sigma_range_m=sigma, minimum_anchors=minimum_anchors
        )
        if geom.condition_number is not None:
            conds.append(geom.condition_number)
        try:
            dop = dop_from_jacobian(range_jacobian(point, visible))
        except ValueError:
            continue
        hdops.append(dop.hdop)
        vdops.append(dop.vdop)

    envelope_max = ROBINSON_VALID_RANGE_M[1]
    beyond = None
    if ranges and scenario.error_model.population_errors_m is not None:
        beyond = float(np.mean(np.array(ranges) > envelope_max))

    return GeometryProfile(
        median_anchors_reachable=float(np.median(reachable)) if reachable else 0.0,
        median_anchors_used=float(np.median(counts)) if counts else 0.0,
        min_anchors_used=int(np.min(counts)) if counts else 0,
        median_hdop=float(np.median(hdops)) if hdops else None,
        median_vdop=float(np.median(vdops)) if vdops else None,
        worst_vdop=float(np.max(vdops)) if vdops else None,
        median_condition_number=float(np.median(conds)) if conds else None,
        samples_below_minimum_anchors=sum(1 for c in counts if c < minimum_anchors),
        median_link_range_m=float(np.median(ranges)) if ranges else 0.0,
        max_link_range_m=float(np.max(ranges)) if ranges else 0.0,
        links_beyond_calibrated_envelope=beyond,
    )


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    accuracy: AccuracyResult
    reliability: ReliabilityResult
    geometry: GeometryProfile
    capex_per_km2_tl: float
    capex_per_km_tl: Optional[float]

    @property
    def key(self) -> str:
        return self.scenario.key


def run_scenario(
    scenario: Scenario, n_repeats: int = N_REPEATS, seed: int = SEED
) -> ScenarioResult:
    """Simulate one scenario end to end and collect every reported metric."""
    sigma = scenario.error_model.sigma_m()
    fixes = simulate_path_fixes(
        scenario_id=scenario.key,
        anchors=scenario.anchors,
        path=scenario.path,
        error_sampler=scenario.error_model.sample,
        evidence=scenario.error_model.evidence,
        method=RangingMethod.DS_TWR,
        n_repeats=n_repeats,
        seed=seed,
        delivery_probability=1.0 - scenario.packet_loss_probability,
        max_range_m=scenario.max_link_range_m,
        max_anchors_per_fix=MAX_ANCHORS_PER_FIX,
        sigma_for_geometry_check_m=sigma,
    )
    capex = CostBreakdown(anchor_cost=scenario.capex_total_tl)
    return ScenarioResult(
        scenario=scenario,
        accuracy=compute_accuracy_metrics(fixes),
        reliability=compute_reliability_metrics(
            fixes, accuracy_thresholds_m=ACCURACY_THRESHOLDS_M
        ),
        geometry=profile_geometry(scenario),
        capex_per_km2_tl=cost_per_area(capex, scenario.area_km2),
        capex_per_km_tl=(
            scenario.capex_total_tl / scenario.corridor_length_km
            if scenario.corridor_length_km
            else None
        ),
    )


def run_all(n_repeats: int = N_REPEATS, seed: int = SEED) -> list[ScenarioResult]:
    return [run_scenario(s, n_repeats=n_repeats, seed=seed) for s in all_scenarios(seed)]
