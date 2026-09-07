"""Simulate the three YERKON deployment groups described in the TOBB ETU
competition presentation ("YERKON_1.pdf": a terrestrial GNSS-backup
positioning system proposed for T.C. Ulastirma ve Altyapi Bakanligi /
UDHAM's "Ulasan ve Erisen Turkiye 2053" competition), using locbench3d's
core simulation primitives directly (not the ``run_scenario`` pipeline's
default box-corner anchor layout, which gives poor vertical geometry for
wide/thin coverage areas - a real geometric effect, not a library bug:
near-coplanar, low-mounted anchors genuinely have weak VDOP).

Four result rows are produced, matching a "2 outdoor + 1 indoor/outdoor,
expandable to 4" comparison-table request:

  1. urban              - Grup 1 / Sehir Ici, SX1280/LoRa TWR, per-unit
                          ranging-offset CALIBRATED (deck's own recommended
                          practice; removes Robinson's ~2.83 m mean bias).
  2. urban_uncalibrated  - identical scenario, but WITHOUT that calibration
                          step, showing the honest cost of skipping it.
  3. rural              - Grup 2 / Kirsal, E28-2G4M27S (SX1280-based) TWR.
  4. tunnel             - Grup 3 / Kritik Bolgeler (tunnel), UWB/DWM3000 TWR.

Evidence provenance (see locbench3d/core/evidence.py):
  - SX1280 scenarios (urban, rural) use ``build_robinson_calibrated_model``,
    a bootstrap built from Stuart Robinson's published SX1280 ranging
    measurements (stuartsprojects.github.io) - the SAME source the YERKON
    deck itself cites for its "<1 m LOS" claim. Evidence type:
    HARDWARE_CALIBRATED_MODEL.
  - The tunnel scenario uses DWM3000 UWB, for which this project has no
    calibrated hardware profile. A configured Gaussian/NLOS-bias model is
    used instead, parameterized to the deck's own stated target (+/-10 cm
    class error). Evidence type: SIMULATED_MONTE_CARLO - explicitly NOT a
    hardware-calibrated claim.

Run directly:

    python examples/yerkon_comparison/simulate_yerkon.py

This prints the full result dict as JSON and also writes
``yerkon_results.json`` next to this script.
"""
import json
import os

import numpy as np

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.core.geometry_bounds import evaluate_geometry
from locbench3d.hardware.sx1280_error_model import build_robinson_calibrated_model
from locbench3d.metrics.accuracy import compute_accuracy_metrics
from locbench3d.metrics.cost import CostBreakdown, cost_per_area
from locbench3d.metrics.reliability import compute_reliability_metrics
from locbench3d.paths.trajectories import straight_line_path
from locbench3d.protocol.traffic import RangingMethod
from locbench3d.simulate.monte_carlo import simulate_path_fixes

SEED = 42
N_REPEATS = 300
ACCURACY_THRESHOLDS_M = [0.5, 1.0, 2.0]


def gaussian_nlos_sampler(sigma_m, nlos_probability, nlos_bias_m, seed):
    """Simple configured error model: Gaussian range noise plus an
    occasional NLOS bias. Used only where no calibrated hardware model
    exists (see module docstring)."""
    rng = np.random.default_rng(seed)

    def sampler(n):
        values = rng.normal(0.0, sigma_m, n)
        if nlos_probability > 0:
            is_nlos = rng.random(n) < nlos_probability
            values = values + is_nlos * nlos_bias_m
        return values

    return sampler


def debiased_bootstrap_sampler(raw_errors_m, seed):
    """Bootstrap sampler over real calibrated errors, with the sample mean
    removed - i.e. what per-unit ranging-offset calibration (which the
    YERKON deck's own architecture section recommends) would plausibly
    achieve. Still HARDWARE_CALIBRATED_MODEL evidence (built from the same
    real data), with one explicit extra assumption (mean-bias removal)."""
    raw_errors_m = np.asarray(raw_errors_m, dtype=float)
    debias = float(np.mean(raw_errors_m))
    rng = np.random.default_rng(seed)

    def sampler(n):
        return rng.choice(raw_errors_m, size=n, replace=True) - debias

    return sampler, debias


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS = {}

# Grup 1: Sehir Ici (Urban), 200 m x 200 m cell.
# Mix of pole-top (8 m), building-mount (20 m) and rooftop base-station
# (35 m) anchors, matching the deck's own mounting-point list.
SCENARIOS["urban"] = dict(
    anchors=np.array(
        [
            [0, 0, 8], [200, 0, 8], [0, 200, 8], [200, 200, 8],
            [100, 0, 20], [0, 100, 20],
            [100, 100, 35], [150, 150, 35],
        ],
        dtype=float,
    ),
    path=straight_line_path(
        "yerkon-urban", (50, 50, 1.5), (150, 150, 1.5), n_samples=6, duration_s=60.0
    ),
    hardware_profile="Semtech SX1280",
    nlos_probability=0.35,
    nlos_bias_m=1.5,
    packet_loss_probability=0.02,
    area_km2=0.2 * 0.2,
    unit_price_100_tl=1366.07,  # deck's bulk (100-unit) BOM price, sehir ici yayin birimi
)

# Grup 2: Kirsal (Rural), 20 km corridor x 2 km width.
# Cell-tower-height anchors (35-45 m) along the corridor, with some
# cross-corridor and height spread for 3D observability.
SCENARIOS["rural"] = dict(
    anchors=np.array(
        [[0, 0, 35], [5000, 2000, 45], [10000, 0, 38], [15000, 2000, 42], [20000, 0, 36]],
        dtype=float,
    ),
    path=straight_line_path(
        "yerkon-rural", (2000, 1000, 1.5), (18000, 1000, 1.5), n_samples=6, duration_s=600.0
    ),
    hardware_profile="Semtech SX1280",  # E28-2G4M27S is SX1280-based per the deck's own BOM
    nlos_probability=0.15,
    nlos_bias_m=2.0,
    packet_loss_probability=0.01,
    area_km2=20.0 * 2.0,
    unit_price_100_tl=1082.68,  # kirsal yayin birimi (E28-2G4M27S)
)

# Grup 3: Kritik Bolgeler (tunnel), 2 km x 20 m, UWB.
# Alternating low side-wall / high ceiling mounts along the tunnel length.
# 12 nodes over 2 km, matching the deck's own stated pilot-corridor
# density ("bir ulasim koridoruna 10-15 yayin dugumu kurulacak").
_tunnel_x = [0, 180, 360, 540, 720, 900, 1080, 1260, 1440, 1620, 1800, 1980]
_tunnel_y = [2, 18, 3, 17, 4, 16, 2, 18, 3, 17, 4, 16]
_tunnel_z = [1.0, 3.5, 4.5, 1.5, 3.0, 4.0, 1.2, 3.8, 4.2, 1.8, 2.8, 4.4]
SCENARIOS["tunnel"] = dict(
    anchors=np.array(list(zip(_tunnel_x, _tunnel_y, _tunnel_z)), dtype=float),
    path=straight_line_path(
        "yerkon-tunnel", (100, 10, 1.5), (1900, 10, 1.5), n_samples=6, duration_s=120.0
    ),
    hardware_profile=None,  # no calibrated DWM3000 profile; configured Gaussian instead
    timing_uncertainty_m=0.03,
    nlos_probability=0.10,
    nlos_bias_m=0.3,
    packet_loss_probability=0.03,
    area_km2=2.0 * 0.02,
    unit_price_100_tl=1634.44,  # kritik bolge yayin birimi (DWM3000)
)


def _simulate_one(scenario_id, method, anchors, path, sampler, evidence, delivery_probability):
    sigma_estimate = float(np.std(sampler(2000)))
    fixes = simulate_path_fixes(
        scenario_id=scenario_id,
        method=method,
        anchors=anchors,
        path=path,
        error_sampler=sampler,
        evidence=evidence,
        n_repeats=N_REPEATS,
        seed=SEED,
        delivery_probability=delivery_probability,
        sigma_for_geometry_check_m=sigma_estimate,
    )
    accuracy = compute_accuracy_metrics(fixes)
    reliability = compute_reliability_metrics(fixes, accuracy_thresholds_m=ACCURACY_THRESHOLDS_M)
    geom = evaluate_geometry(path.points()[0], anchors, sigma_range_m=sigma_estimate)
    return accuracy, reliability, geom


def _to_result_dict(cfg, evidence, accuracy, reliability, geom):
    capex_total = len(cfg["anchors"]) * cfg["unit_price_100_tl"]
    capex_per_km2 = cost_per_area(CostBreakdown(anchor_cost=capex_total), cfg["area_km2"])
    return {
        "evidence_type": evidence.evidence_type.value,
        "anchor_count": len(cfg["anchors"]),
        "attempted_fixes": reliability.attempted_fixes,
        "valid_fix_rate": reliability.valid_fix_rate,
        "hpe_p50_m": accuracy.horizontal_p50_m,
        "hpe_p95_m": accuracy.horizontal_p95_m,
        "hpe_max_m": accuracy.horizontal_max_m,
        "vpe_p50_m": accuracy.vertical_p50_m,
        "vpe_p95_m": accuracy.vertical_p95_m,
        "error_3d_p95_m": accuracy.error_3d_p95_m,
        "geometry_valid": geom.geometry_valid,
        "condition_number": geom.condition_number,
        "availability_1m": reliability.availability_by_threshold.get(1.0),
        "availability_2m": reliability.availability_by_threshold.get(2.0),
        "area_km2": cfg["area_km2"],
        "capex_total_tl": capex_total,
        "capex_per_km2_tl": capex_per_km2,
    }


def run_all():
    """Run all four YERKON result rows and return them as a dict."""
    results = {}

    # --- urban: calibrated (primary) and uncalibrated (raw) variants ---
    cfg = SCENARIOS["urban"]
    model = build_robinson_calibrated_model(seed=SEED)

    raw_sampler = model.sample_errors_m
    accuracy, reliability, geom = _simulate_one(
        "yerkon-urban-raw", RangingMethod.DS_TWR, cfg["anchors"], cfg["path"],
        raw_sampler, model.evidence, 1.0 - cfg["packet_loss_probability"],
    )
    results["urban_uncalibrated"] = _to_result_dict(cfg, model.evidence, accuracy, reliability, geom)
    results["urban_uncalibrated"]["hardware_profile"] = cfg["hardware_profile"]

    calibrated_sampler, debias_removed_m = debiased_bootstrap_sampler(model.errors_m, SEED)
    accuracy, reliability, geom = _simulate_one(
        "yerkon-urban-calibrated", RangingMethod.DS_TWR, cfg["anchors"], cfg["path"],
        calibrated_sampler, model.evidence, 1.0 - cfg["packet_loss_probability"],
    )
    results["urban"] = _to_result_dict(cfg, model.evidence, accuracy, reliability, geom)
    results["urban"]["hardware_profile"] = cfg["hardware_profile"]
    results["urban"]["debias_removed_m"] = debias_removed_m
    results["urban"]["note"] = "per-unit ranging-offset calibration applied (deck's own recommended practice)"

    # --- rural ---
    cfg = SCENARIOS["rural"]
    model = build_robinson_calibrated_model(seed=SEED)
    accuracy, reliability, geom = _simulate_one(
        "yerkon-rural", RangingMethod.DS_TWR, cfg["anchors"], cfg["path"],
        model.sample_errors_m, model.evidence, 1.0 - cfg["packet_loss_probability"],
    )
    results["rural"] = _to_result_dict(cfg, model.evidence, accuracy, reliability, geom)
    results["rural"]["hardware_profile"] = cfg["hardware_profile"]

    # --- tunnel ---
    cfg = SCENARIOS["tunnel"]
    sigma = cfg["timing_uncertainty_m"]
    evidence = EvidenceRecord(
        evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
        source_name="Configured Gaussian/NLOS-bias model for DWM3000 UWB (no calibrated profile)",
        source_scope=(
            f"Synthetic model: N(0, {sigma} m) range noise plus NLOS bias, "
            "parameterized to the YERKON deck's own stated target "
            "(+/-10 cm class error) for the DWM3000 UWB module. Not a "
            "hardware-calibrated measurement."
        ),
    )
    sampler = gaussian_nlos_sampler(sigma, cfg["nlos_probability"], cfg["nlos_bias_m"], SEED)
    accuracy, reliability, geom = _simulate_one(
        "yerkon-tunnel", RangingMethod.DS_TWR, cfg["anchors"], cfg["path"],
        sampler, evidence, 1.0 - cfg["packet_loss_probability"],
    )
    results["tunnel"] = _to_result_dict(cfg, evidence, accuracy, reliability, geom)
    results["tunnel"]["hardware_profile"] = "DWM3000 (configured, not calibrated)"

    return results


if __name__ == "__main__":
    results = run_all()
    text = json.dumps(results, indent=2, ensure_ascii=False)
    print(text)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yerkon_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nWrote {out_path}")
