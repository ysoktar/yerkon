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

import dataclasses
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
from yerkon.fusion import FusionSettings, TrackResult, run_filter
from yerkon.path import (
    Path3D,
    Track,
    driving_track,
    straight_line_path,
    zigzag_path,
)
from yerkon.receiver import ReceiverProfile, vehicle_receiver
from yerkon.ranging_error import (
    ROBINSON_URL,
    robinson_errors_m,
    RangingErrorModel,
    add_nlos,
    build_dwm3000_model,
    build_sx1280_model,
)
from yerkon.link_snr import LinkBudget, PATH_LOSS_EXPONENTS
from yerkon.survey import (
    SURVEY_BY_ENVIRONMENT,
    SurveySpec,
    rms_offset_m,
    surveyed_positions,
)
from yerkon.matlab_import import build_model_from_cases, load_trials
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

#: Filtered passes per scenario. Each pass yields hundreds of correlated
#: epochs, so fewer passes are needed than for independent single-epoch
#: draws, but several are still required: the per-anchor offsets and the
#: odometry scale error are drawn once per pass and dominate the result.
N_TRACK_RUNS = 16

#: Seconds discarded at the start of each pass while the filter converges
#: from its first single-epoch fix. A receiver that has been running for a
#: minute is not still in that transient, and convergence time is reported
#: separately rather than folded into the accuracy percentiles.
FILTER_WARMUP_S = 12.0

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
    track: Track
    receiver: ReceiverProfile
    error_model: RangingErrorModel
    area_km2: float
    max_link_range_m: float
    packet_loss_probability: float
    corridor_length_km: Optional[float] = None
    parameter_evidence: tuple[EvidenceRecord, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    #: How well this deployment knows where its own anchors are. The solver
    #: works from the surveyed positions while the ranges come from the true
    #: ones, so the residual survey error enters every fix as a fixed
    #: offset. Leave it ``None`` to assume a perfect survey.
    survey: Optional[SurveySpec] = None
    #: Coordinate index that measures distance from the survey origin, for a
    #: traverse whose error grows along a route. Only the tunnel needs it.
    survey_traverse_axis: Optional[int] = None

    @property
    def evidence_records(self) -> tuple[EvidenceRecord, ...]:
        """Every declared source behind this scenario: the error model, the
        anchor layouts, and the standalone parameter assumptions."""
        return (
            (self.error_model.evidence,)
            + tuple(g.evidence for g in self.groups)
            + self.parameter_evidence
            + self.receiver.evidence_records
        )

    @property
    def anchors(self) -> np.ndarray:
        """Where the anchors really are."""
        return np.vstack([g.positions for g in self.groups])

    @property
    def surveyed_anchors(self) -> np.ndarray:
        """Where the survey says they are, which is what the solver gets.

        Drawn once per scenario from a fixed seed, because an installation
        is surveyed once. Redrawing it per fix would let the filter average
        the error away, and a survey error is exactly the kind that does
        not average away.
        """
        if self.survey is None:
            return self.anchors
        return surveyed_positions(
            self.anchors,
            self.survey,
            seed=SEED + 4001,
            traverse_axis=self.survey_traverse_axis,
        )

    @property
    def survey_rms_offset_m(self) -> float:
        """How far the surveyed positions sit from the true ones, RMS."""
        if self.survey is None:
            return 0.0
        return rms_offset_m(self.anchors, self.surveyed_anchors)

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
    nlos_fraction = URBAN_NLOS_FRACTION
    model, from_simulation = sx1280_error_model(
        "urban", URBAN_LINK_RANGE_M, nlos_fraction, seed=seed, calibrated=calibrated
    )
    if not from_simulation:
        model = add_nlos(
            model, seed=seed + 10, nlos_probability=nlos_fraction, nlos_bias_m=1.5
        )
    suffix = "Kalibreli" if calibrated else "Ham"
    return Scenario(
        key="urban_calibrated" if calibrated else "urban_uncalibrated",
        display_name="YERKON (Şehir İçi - {})".format(suffix),
        technology="Karasal PNT (SX1280/LoRa TWR)",
        environment="Dış",
        groups=(urban_grid_layout(side_m=side_m, spacing_m=URBAN_GRID_SPACING_M, seed=seed),),
        path=straight_line_path(
            "urban-diagonal",
            (60.0, 90.0, 1.5),
            (940.0, 910.0, 1.5),
            n_samples=N_PATH_SAMPLES,
            duration_s=600.0,
        ),
        track=driving_track(
            "urban-drive",
            # Placed so the turning circle sits inside the cell: at 50 km/h
            # and 2.5 deg/s the radius is about 320 m, so the route stays
            # roughly 180 m clear of every edge.
            start=(609.0, 200.0, 1.5),
            heading_deg=20.0,
            speed_m_s=13.9,          # 50 km/h
            duration_s=180.0,
            dt_s=0.1,
            lane_change_amplitude_m=1.2,
            turn_rate_deg_s=2.5,
        ),
        receiver=vehicle_receiver(),
        error_model=model,
        area_km2=(side_m / 1000.0) ** 2,
        max_link_range_m=URBAN_LINK_RANGE_M,
        packet_loss_probability=0.02,
        survey=SURVEY_BY_ENVIRONMENT["urban"],
        parameter_evidence=(URBAN_LINK_RANGE.evidence, _PRICE_EVIDENCE, _NLOS_EVIDENCE),
        notes=(
            "35% of links are modelled as hard NLOS: the simulated channel "
            "attenuates the direct path, so the peak detector can lock to a "
            "reflection. At 406 kHz that produces a bounded error; at "
            "1625 kHz it becomes bimodal, which is why the wider bandwidth "
            "is not used here.",
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
    nlos_fraction = RURAL_NLOS_FRACTION
    model, from_simulation = sx1280_error_model(
        "rural", RURAL_LINK_RANGE_M, nlos_fraction, seed=seed, calibrated=True
    )
    if not from_simulation:
        model = add_nlos(
            model, seed=seed + 11, nlos_probability=nlos_fraction, nlos_bias_m=2.0
        )
    return Scenario(
        key="rural",
        display_name="YERKON (Kırsal)",
        technology="Karasal PNT (E28-SX1280 TWR)",
        environment="Dış",
        groups=(
            roadside_layout(
                length_m=length_m, sign_spacing_m=RURAL_SIGN_SPACING_M, seed=seed
            ),
            mast_layout(length_m=length_m, spacing_m=2500.0, seed=seed),
        ),
        track=driving_track(
            "rural-drive",
            start=(2000.0, 0.0, 1.5),
            heading_deg=0.0,
            speed_m_s=30.6,          # 110 km/h
            duration_s=180.0,
            dt_s=0.1,
            lane_change_amplitude_m=3.0,
        ),
        receiver=vehicle_receiver(),
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
        survey=SURVEY_BY_ENVIRONMENT["rural"],
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
            "15% of links are modelled as hard NLOS, representing terrain "
            "and vegetation blocking the direct path. The corridor is open "
            "enough that the wider 812 kHz ranging bandwidth wins here, "
            "where in the city 406 kHz does.",
        ),
    )


#: The SX1280 ranging bandwidth each environment is simulated at, in Hz.
#:
#: The part offers four and the report names none. Widening it is free in
#: link-budget terms - ``regulatory`` shows the band's density cap raises
#: the legal transmit power by exactly what the wider bandwidth adds to
#: thermal noise, so the range is unchanged - and in a clear channel the
#: ranging error halves with every doubling.
#:
#: It does not follow that the widest is best, and measuring it says
#: otherwise. Wide bandwidth resolves multipath into separate correlation
#: peaks instead of merging them into one broad blur. A peak detector then
#: picks the strongest, which in a blocked channel is a reflection at a
#: genuinely longer delay, so the error stops being a bounded average and
#: becomes bimodal: at 1625 kHz the median urban NLOS error is 0.00 m but
#: 28% of errors exceed 10 m.
#:
#: The usual escape is leading-edge detection, and this part cannot use
#: it. Back-searching lands about half a correlation lobe early, which is
#: 0.3 m for UWB at 499 MHz and about 90 m for the SX1280 at 1.6 MHz.
#: Measured: leading edge at 1625 kHz gives a -96 m offset and a wider
#: spread than peak detection even after that offset is calibrated out.
#:
#: So the best bandwidth is the one that balances timing resolution
#: against multipath picking, and it depends on how obstructed the
#: environment is. Measured on the scenarios themselves, in HPE P50:
#:
#:     urban (35% blocked)   203 kHz 3.52  406 kHz 1.93  812 kHz 3.44  1625 kHz 6.00
#:     rural (15% blocked)   203 kHz 21.4  406 kHz 13.8  812 kHz 8.68  1625 kHz 14.1
#:
#: Both are U-shaped with the optimum in the middle, and it moves wider as
#: the environment opens up. 406 kHz is also what Semtech's ranging mode
#: and Robinson's published measurements use, so the urban answer is that
#: the part's existing default is already right.
RANGING_BANDWIDTH_HZ = {
    "urban": 406e3,
    "rural": 812e3,
}

#: Fraction of links whose direct path is blocked, per environment.
#:
#: These weight the simulation's LOS and NLOS cases into the mix a
#: deployment sees. Read them as hard obstruction - the simulated NLOS
#: channel attenuates the direct path and drops the Rician K factor
#: negative, so the peak detector can lock to a reflection outright. That
#: is a stronger claim than the 1.5 m bias an earlier version layered on
#: the same fraction of links, and the resulting spread is much wider.
URBAN_NLOS_FRACTION = 0.35
RURAL_NLOS_FRACTION = 0.15

#: Urban grid spacing, in metres.
#:
#: 175 m, not the 150 m an earlier version used, because 150 m is on the
#: wrong side of a trade that has no downside. A fix uses at most
#: MAX_ANCHORS_PER_FIX anchors, so once the receiver hears more than eight
#: the extra ones are never used - packing the grid tighter then only
#: shrinks the baseline the nearest eight span, which is worse geometry
#: bought with more hardware. Measured over the spacing sweep, in HPE P50
#: against CAPEX per km2:
#:
#:     125 m  81 nodes  110652 TL  2.14 m
#:     150 m  49 nodes   66937 TL  1.93 m
#:     175 m  36 nodes   49179 TL  1.60 m   <- both cheaper and better
#:     225 m  25 nodes   34152 TL  1.93 m   <- same accuracy, half the cost
#:
#: 175 m beats 150 m on both axes at once, so nothing is being traded away
#: here. 225 m halves the cost again at the accuracy 150 m gave, but it
#: leaves only four anchors reachable at the worst point on the path,
#: which is the bare minimum for a 3D fix and no margin for a lost packet.
#: 175 m keeps five.
URBAN_GRID_SPACING_M = 175.0

#: Spacing between facing roadside sign mounts on the rural corridor, in
#: metres.
#:
#: 750 m rather than the 500 m an earlier version used, for the same
#: reason the urban grid opened up: a fix uses at most
#: MAX_ANCHORS_PER_FIX anchors, so past that point closer spacing only
#: shortens the baseline they span. Measured, at 812 kHz:
#:
#:      500 m  187 nodes  200854 TL  P50 8.43  P95 35.80
#:      750 m  131 nodes  140705 TL  P50 7.81  P95 26.49
#:     1000 m  103 nodes  110631 TL  P50 9.33  P95 57.65
#:     1500 m   75 nodes   80557 TL  P50 13.76 P95 63.30
#:
#: 750 m is 30% cheaper than 500 m and better on both the median and the
#: tail, so nothing is traded away. Past 750 m the tail runs away: 1000 m
#: doubles P95 to save a further 21%, which is the wrong trade for a row
#: whose weakest number is already its tail.
RURAL_SIGN_SPACING_M = 750.0

SX1280_CARRIER_HZ = 2450e6
UWB_CARRIER_HZ = 6489.6e6


def _waveform_model(
    case_names: tuple[str, ...],
    name: str,
    exponent_key: str,
    max_range_m: float,
    carrier_hz: float,
    bandwidth_hz: float,
    seed: int,
    calibrated: bool = True,
    nlos_fraction: Optional[float] = None,
) -> Optional[RangingErrorModel]:
    """Build an error model from the MATLAB run, or None if it is absent.

    The link budget is passed in so the trials are restricted to the
    distance and SNR pairs this deployment actually produces. Skipping that
    step pools every simulated SNR at every distance and comes out several
    times too wide; see ``matlab_import.realistic_trials``.
    """
    try:
        available = load_trials()
    except (FileNotFoundError, ValueError):
        return None
    selected = [c for c in available.values() if c.case in case_names]
    if len(selected) != len(case_names):
        return None
    budget = LinkBudget(
        bandwidth_hz=bandwidth_hz,
        frequency_hz=carrier_hz,
        exponent=PATH_LOSS_EXPONENTS[exponent_key],
    )
    weights = None
    if nlos_fraction is not None:
        weights = {"LOS": 1.0 - nlos_fraction, "NLOS": nlos_fraction}
    return build_model_from_cases(
        selected,
        name=name,
        seed=seed,
        calibrated=calibrated,
        budget=budget,
        max_range_m=max_range_m,
        condition_weights=weights,
    )


def sx1280_error_model(
    environment: str,
    max_range_m: float,
    nlos_fraction: float,
    seed: int = SEED,
    calibrated: bool = True,
    bandwidth_hz: Optional[float] = None,
) -> tuple[RangingErrorModel, bool]:
    """The SX1280 error model, preferring the waveform simulation.

    Returns the model and whether it came from the simulation. The
    fallback is the bootstrap over Robinson's six published measurements,
    which is the only hardware number in the project but covers one
    unstated bandwidth over 0-250 m. Where the MATLAB export is present the
    simulation supersedes it, because it knows its own bandwidth.
    """
    if bandwidth_hz is None:
        bandwidth_hz = RANGING_BANDWIDTH_HZ[environment]
    tag = "{:.0f}k".format(bandwidth_hz / 1e3)
    prefix = "sx1280_1600k" if bandwidth_hz == 1625e3 else "sx1280_" + tag
    model = _waveform_model(
        (prefix + "_los", prefix + "_nlos"),
        name="Semtech SX1280 at {:.0f} kHz (MATLAB waveform simulation, {})".format(
            bandwidth_hz / 1e3, "calibrated" if calibrated else "uncalibrated"
        ),
        exponent_key=environment,
        max_range_m=max_range_m,
        carrier_hz=SX1280_CARRIER_HZ,
        bandwidth_hz=bandwidth_hz,
        seed=seed,
        calibrated=calibrated,
        nlos_fraction=nlos_fraction,
    )
    if model is not None:
        if not calibrated:
            model = _with_hardware_offset(model)
        return model, True
    return build_sx1280_model(seed=seed, calibrated=calibrated), False


def _with_hardware_offset(model: RangingErrorModel) -> RangingErrorModel:
    """Add the constant offset only hardware has, to a simulated model.

    The uncalibrated row exists to show what skipping per-unit ranging
    calibration costs. The waveform simulation cannot show it: its own
    constant offset is 0.01 m, because it models the waveform and the
    channel but not the antenna phase centre or the chip's group delay,
    which is where a real per-unit offset comes from. Robinson's six
    measurements are the only place in this project where one was
    observed, at +2.83 m.

    So the two halves come from where each is actually known: the spread
    from the simulation, which knows its own bandwidth, and the constant
    offset from the hardware, which is the only thing that ever measured
    one. Leaving the row on the simulation alone would have made it
    identical to the calibrated row and quietly said per-unit calibration
    buys nothing.
    """
    offset = float(np.mean(robinson_errors_m()))
    base = model.sample
    return RangingErrorModel(
        name=model.name + " + measured per-unit offset",
        evidence=EvidenceRecord(
            evidence_type=model.evidence.evidence_type,
            source_name=model.evidence.source_name,
            source_url=ROBINSON_URL,
            source_scope=model.evidence.source_scope,
            caveats=(
                model.evidence.caveats
                + " The {:+.2f} m constant offset is Robinson's measured "
                "SX1280 offset, not a simulated one: the simulation has no "
                "antenna or chip group delay to produce one."
            ).format(offset),
        ),
        sample=lambda n: base(n) + offset,
        respawn=lambda s: _with_hardware_offset(model.reseed(s)),
        population_errors_m=(
            tuple(v + offset for v in model.population_errors_m)
            if model.population_errors_m
            else None
        ),
        mean_bias_m=offset,
        includes_multipath=model.includes_multipath,
        valid_range_m=model.valid_range_m,
    )


def tunnel_error_model(seed: int = SEED) -> RangingErrorModel:
    """The UWB error model, preferring the waveform simulation over the target.

    The fallback is a Gaussian parameterised to the accuracy the report
    targets for the DWM3000. A target is a statement of intent, and the
    MATLAB run supersedes it: that derives the error from the waveform, a
    multipath channel and the SNR, and says the target is not reached.
    Where the export is absent the fallback still runs, so a fresh clone
    works without MATLAB.
    """
    try:
        cases = load_trials()
    except (FileNotFoundError, ValueError):
        return build_dwm3000_model(
            seed=seed, sigma_m=0.03, nlos_probability=0.10, nlos_bias_m=0.30
        )
    tunnel_cases = [c for c in cases.values() if c.case == "uwb_tunnel"]
    if not tunnel_cases:
        return build_dwm3000_model(
            seed=seed, sigma_m=0.03, nlos_probability=0.10, nlos_bias_m=0.30
        )
    return build_model_from_cases(
        tunnel_cases,
        name="Qorvo DWM3000 (MATLAB waveform simulation, tunnel channel)",
        seed=seed,
        calibrated=True,
        budget=LinkBudget(
            bandwidth_hz=499.2e6,
            frequency_hz=UWB_CARRIER_HZ,
            exponent=PATH_LOSS_EXPONENTS["tunnel"],
        ),
        max_range_m=TUNNEL_LINK_RANGE_M,
    )


def critical_zone_scenario(seed: int = SEED) -> Scenario:
    """50 km tunnel network, the running length that reaches 1 km² of plan area."""
    length_m = 50000.0
    width_m = 20.0
    model = tunnel_error_model(seed=seed)
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
        track=driving_track(
            "tunnel-drive",
            start=(400.0, 9.0, 1.5),
            heading_deg=0.0,
            speed_m_s=22.2,          # 80 km/h
            duration_s=180.0,
            dt_s=0.1,
            lane_change_amplitude_m=1.5,
        ),
        receiver=vehicle_receiver(),
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
        survey=SURVEY_BY_ENVIRONMENT["tunnel"],
        # The tunnel runs along x, so distance from the portal is x.
        survey_traverse_axis=0,
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

    # Each model states the link distances its evidence covers. Comparing a
    # tunnel link against the SX1280 data's envelope would report a number
    # about the wrong radio.
    envelope = scenario.error_model.valid_range_m
    beyond = None
    if ranges and envelope is not None:
        beyond = float(np.mean(np.array(ranges) > envelope[1]))

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
class FusedResult:
    """What the receiver actually delivers, after the filter.

    The single-epoch numbers describe the radio on its own. These describe
    the system the report proposes: ranges fused with the IMU, wheel
    odometry and the map constraint, held across gaps.
    """

    hpe_p50_m: float
    hpe_p95_m: float
    vpe_p50_m: float
    vpe_p95_m: float
    error_3d_p95_m: float
    epochs: int
    runs: int
    median_convergence_s: Optional[float]
    gated_range_fraction: float
    settings: FusionSettings

    def to_dict(self) -> dict:
        return {
            "hpe_p50_m": self.hpe_p50_m,
            "hpe_p95_m": self.hpe_p95_m,
            "vpe_p50_m": self.vpe_p50_m,
            "vpe_p95_m": self.vpe_p95_m,
            "error_3d_p95_m": self.error_3d_p95_m,
            "epochs": self.epochs,
            "runs": self.runs,
            "median_convergence_s": self.median_convergence_s,
            "gated_range_fraction": self.gated_range_fraction,
            "bias_variance_fraction": self.settings.bias_variance_fraction,
            "used_odometry": self.settings.use_odometry,
            "used_heading": self.settings.use_heading,
            "used_map_height": self.settings.use_map_height,
        }


def run_fused(
    scenario: Scenario,
    settings: FusionSettings = FusionSettings(),
    n_runs: int = N_TRACK_RUNS,
    seed: int = SEED,
) -> FusedResult:
    """Run the receiver's filter along the scenario track, several times.

    Each pass draws its own per-anchor offsets and odometry scale error,
    which are what the result actually turns on: they persist for the whole
    pass, so a single pass would report one draw of them rather than their
    spread.
    """
    scenario = dataclasses.replace(
        scenario, error_model=scenario.error_model.reseed(seed)
    )
    sigma = scenario.error_model.sigma_m()
    nlos_probability, nlos_bias_m = _nlos_terms(scenario)

    horizontal: list[np.ndarray] = []
    vertical: list[np.ndarray] = []
    three_d: list[np.ndarray] = []
    convergences: list[float] = []
    gated: list[float] = []
    warmup_steps = int(FILTER_WARMUP_S / scenario.track.dt_s)
    # Surveyed once, then reused for every pass. An installation is
    # surveyed once, so redrawing it per pass would let the spread over
    # passes hide the error instead of showing it.
    surveyed = scenario.surveyed_anchors

    for run in range(n_runs):
        result = run_filter(
            track=scenario.track,
            anchors=scenario.anchors,
            solver_anchors=surveyed,
            receiver=scenario.receiver,
            sigma_range_m=sigma,
            common_bias_m=scenario.error_model.mean_bias_m,
            max_range_m=scenario.max_link_range_m,
            max_anchors_per_fix=MAX_ANCHORS_PER_FIX,
            packet_loss_probability=scenario.packet_loss_probability,
            nlos_probability=nlos_probability,
            nlos_bias_m=nlos_bias_m,
            seed=seed + 1000 * run,
            settings=settings,
        )
        if result.error_3d_m.size <= warmup_steps:
            continue
        horizontal.append(result.error_horizontal_m[warmup_steps:])
        vertical.append(result.error_vertical_m[warmup_steps:])
        three_d.append(result.error_3d_m[warmup_steps:])
        gated.append(result.gated_range_fraction)
        if result.converged_after_s is not None:
            convergences.append(result.converged_after_s)

    if not three_d:
        raise RuntimeError("no filtered pass produced a usable track")

    h = np.concatenate(horizontal)
    v = np.concatenate(vertical)
    e = np.concatenate(three_d)
    return FusedResult(
        hpe_p50_m=float(np.percentile(h, 50)),
        hpe_p95_m=float(np.percentile(h, 95)),
        vpe_p50_m=float(np.percentile(v, 50)),
        vpe_p95_m=float(np.percentile(v, 95)),
        error_3d_p95_m=float(np.percentile(e, 95)),
        epochs=int(e.size),
        runs=len(three_d),
        median_convergence_s=float(np.median(convergences)) if convergences else None,
        gated_range_fraction=float(np.mean(gated)) if gated else 0.0,
        settings=settings,
    )


def _nlos_terms(scenario: Scenario) -> tuple[float, float]:
    """The NLOS probability and bias to layer on during a filtered pass.

    Zero where the error model already carries multipath. The waveform
    simulation puts the signal through a channel, so its errors already
    contain the reflections; adding an NLOS bias on top would count the
    same physics twice.
    """
    if scenario.error_model.includes_multipath:
        return 0.0, 0.0
    return _NLOS_BY_SCENARIO.get(scenario.key, (0.0, 0.0))


_NLOS_BY_SCENARIO = {
    "urban_calibrated": (0.35, 1.5),
    "urban_uncalibrated": (0.35, 1.5),
    "rural": (0.15, 2.0),
    "critical": (0.10, 0.3),
}


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    accuracy: AccuracyResult
    reliability: ReliabilityResult
    geometry: GeometryProfile
    fused: FusedResult
    fused_radio_only: FusedResult
    capex_per_km2_tl: float
    capex_per_km_tl: Optional[float]

    @property
    def key(self) -> str:
        return self.scenario.key


def run_scenario(
    scenario: Scenario,
    n_repeats: int = N_REPEATS,
    seed: int = SEED,
    n_track_runs: int = N_TRACK_RUNS,
) -> ScenarioResult:
    """Simulate one scenario end to end and collect every reported metric."""
    # Reseed first. The error model's sampler carries generator state, so
    # running a second scenario in the same process would otherwise start
    # from wherever the first one stopped, and two runs of the same
    # scenario would disagree. Every comparison in docs/ depends on this.
    scenario = dataclasses.replace(
        scenario, error_model=scenario.error_model.reseed(seed)
    )
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
        solver_anchors=scenario.surveyed_anchors,
    )
    capex = CostBreakdown(anchor_cost=scenario.capex_total_tl)
    return ScenarioResult(
        scenario=scenario,
        accuracy=compute_accuracy_metrics(fixes),
        reliability=compute_reliability_metrics(
            fixes, accuracy_thresholds_m=ACCURACY_THRESHOLDS_M
        ),
        geometry=profile_geometry(scenario),
        fused=run_fused(scenario, seed=seed, n_runs=n_track_runs),
        # The same filter with every aiding source switched off, so the
        # gain from each one is measurable rather than asserted.
        fused_radio_only=run_fused(
            scenario,
            settings=FusionSettings(
                use_odometry=False, use_heading=False, use_map_height=False
            ),
            seed=seed,
            n_runs=n_track_runs,
        ),
        capex_per_km2_tl=cost_per_area(capex, scenario.area_km2),
        capex_per_km_tl=(
            scenario.capex_total_tl / scenario.corridor_length_km
            if scenario.corridor_length_km
            else None
        ),
    )


def run_all(
    n_repeats: int = N_REPEATS,
    seed: int = SEED,
    n_track_runs: int = N_TRACK_RUNS,
) -> list[ScenarioResult]:
    return [
        run_scenario(s, n_repeats=n_repeats, seed=seed, n_track_runs=n_track_runs)
        for s in all_scenarios(seed)
    ]
