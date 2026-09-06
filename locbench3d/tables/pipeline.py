"""End-to-end scenario pipeline: a ScenarioSpec in, a ScenarioResult out.

This is the integration point between the method catalog, anchor/path
generation, the Monte Carlo engine, and the metrics modules. It is
intentionally simple about two things the requirements say not to
over-engineer:

* Anchor layout: a small set of deterministic presets scaled to the
  scenario's environment box, not a layout optimizer.
* Range-error model: a Gaussian (or, for SX1280, the hardware-calibrated
  bootstrap model) driven directly by the scenario's configured
  uncertainty parameters, not a physical RF propagation simulation.

Methods without a native simulator (see ``methods.catalog``) are rejected
here with a clear error directing the caller to sourced/imported evidence
instead.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.core.geometry_bounds import CRLBResult, GeometryResult, evaluate_geometry, range_crlb
from locbench3d.hardware.sx1280_error_model import build_robinson_calibrated_model
from locbench3d.methods.catalog import get_method
from locbench3d.methods.tdoa import evaluate_tdoa_geometry, tdoa_crlb
from locbench3d.metrics.accuracy import AccuracyResult, compute_accuracy_metrics
from locbench3d.metrics.path_metrics import PathMetricsResult, compute_path_metrics
from locbench3d.metrics.reliability import ReliabilityResult, compute_reliability_metrics
from locbench3d.metrics.scalability import ScalabilityResult, evaluate_scalability
from locbench3d.paths.trajectories import Path3D, straight_line_path
from locbench3d.protocol.traffic import RangingMethod
from locbench3d.simulate.monte_carlo import FixResult, simulate_path_fixes
from locbench3d.experiment.schema import ScenarioSpec

_METHOD_TO_RANGING_MODEL = {
    "SX1280_RANGING": RangingMethod.SS_TWR,
    "UWB_SS_TWR": RangingMethod.SS_TWR,
    "UWB_DS_TWR": RangingMethod.DS_TWR,
    "TDOA": RangingMethod.TDOA,
    "TOA": RangingMethod.TOA,
    "TOF": RangingMethod.TOF,
    "GENERIC_RTT": RangingMethod.SS_TWR,
    "WIFI_RTT_FTM": RangingMethod.SS_TWR,
    "RSSI_TRILATERATION": RangingMethod.TOA,
    "ACOUSTIC_RANGING": RangingMethod.SS_TWR,
}

_DEFAULT_SIGMA_M = 0.15


@dataclass(frozen=True)
class ScenarioResult:
    spec: ScenarioSpec
    anchors: np.ndarray
    path: Path3D
    fixes: list[FixResult]
    accuracy: AccuracyResult
    reliability: ReliabilityResult
    scalability: ScalabilityResult
    path_metrics: PathMetricsResult
    geometry_valid_fraction: float
    representative_geometry: GeometryResult
    representative_crlb: CRLBResult
    error_model_evidence: EvidenceRecord
    n_path_samples: int


def default_anchor_layout(
    width_m: float, length_m: float, height_m: float, n: int, seed: int = 0
) -> np.ndarray:
    """A small set of deterministic 3D anchor presets, scaled to the box.

    Not a coverage-optimized layout; a planning tool, not an optimizer.
    """
    if n < 0:
        raise ValueError("n must not be negative")
    presets = [
        (0.0, 0.0, 0.0),
        (width_m, 0.0, 0.0),
        (width_m, length_m, 0.0),
        (0.0, length_m, 0.0),
        (width_m / 2, length_m / 2, height_m),
        (0.0, 0.0, height_m),
        (width_m, length_m, height_m),
        (width_m / 2, 0.0, height_m / 2),
    ]
    if n <= len(presets):
        pts = presets[:n]
    else:
        pts = list(presets)
        rng = np.random.default_rng(seed)
        extra = n - len(presets)
        pts += list(
            zip(
                rng.uniform(0.0, width_m, extra),
                rng.uniform(0.0, length_m, extra),
                rng.uniform(0.0, height_m, extra),
            )
        )
    return np.array(pts[:n], dtype=float)


def default_path(spec: ScenarioSpec) -> Path3D:
    p0 = (spec.width_m * 0.2, spec.length_m * 0.2, spec.height_m * 0.3)
    p1 = (spec.width_m * 0.8, spec.length_m * 0.8, spec.height_m * 0.6)
    return straight_line_path(f"{spec.scenario_id}-default-path", p0, p1, n_samples=5, duration_s=5.0)


def build_error_sampler(spec: ScenarioSpec, seed: int):
    """Return (sampler, evidence) for range-error generation.

    SX1280 hardware profiles use the Robinson-calibrated bootstrap model.
    Everything else uses a Gaussian model driven by the scenario's own
    ``timing_uncertainty_m`` / ``additional_measurement_uncertainty_m`` /
    NLOS parameters, explicitly labeled SIMULATED_MONTE_CARLO (a synthetic
    model, not a measurement).
    """
    if spec.hardware_profile == "Semtech SX1280":
        model = build_robinson_calibrated_model(seed=seed)
        return model.sample_errors_m, model.evidence

    base_sigma = spec.timing_uncertainty_m if spec.timing_uncertainty_m is not None else _DEFAULT_SIGMA_M
    extra = spec.additional_measurement_uncertainty_m or 0.0
    combined_sigma = float(np.hypot(base_sigma, extra))
    nlos_p = spec.nlos_probability or 0.0
    nlos_bias = spec.nlos_bias_m or 0.0
    rng = np.random.default_rng(seed)

    def sampler(n: int) -> np.ndarray:
        values = rng.normal(0.0, combined_sigma, n)
        if nlos_p > 0:
            is_nlos = rng.random(n) < nlos_p
            values = values + is_nlos * nlos_bias
        return values

    evidence = EvidenceRecord(
        evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
        source_name="Configured Gaussian/NLOS-bias range-error model",
        source_url="",
        source_scope=(
            f"Synthetic model: N(0, {combined_sigma:.4f} m) range noise, plus a "
            f"{nlos_bias:.3f} m bias applied to a randomly selected "
            f"{nlos_p:.0%} of attempts. Parameters come directly from this "
            "scenario's configuration, not from a measurement or a "
            "hardware-calibrated fit."
        ),
    )
    return sampler, evidence


def run_scenario(spec: ScenarioSpec, n_repeats: int = 20, seed: int = 0) -> ScenarioResult:
    method_def = get_method(spec.method)
    if not method_def.has_native_simulator:
        raise ValueError(
            f"Method {spec.method!r} has no native simulator "
            f"({method_def.evidence_note}); use sourced/imported evidence "
            "tables instead of run_scenario for this method."
        )
    ranging_method = _METHOD_TO_RANGING_MODEL[spec.method]

    anchor_count = spec.anchor_count if spec.anchor_count is not None else 5
    anchors = default_anchor_layout(spec.width_m, spec.length_m, spec.height_m, anchor_count, seed=seed)
    path = default_path(spec)

    sampler, evidence = build_error_sampler(spec, seed=seed)
    sigma_estimate = float(np.std(sampler(2000)))
    if sigma_estimate <= 0:
        sigma_estimate = _DEFAULT_SIGMA_M

    delivery_probability = 1.0 - (spec.packet_loss_probability or 0.0)

    fixes = simulate_path_fixes(
        scenario_id=spec.scenario_id,
        method=ranging_method,
        anchors=anchors,
        path=path,
        error_sampler=sampler,
        evidence=evidence,
        n_repeats=n_repeats,
        seed=seed,
        delivery_probability=delivery_probability,
        sigma_for_geometry_check_m=sigma_estimate,
    )

    accuracy = compute_accuracy_metrics(fixes)
    reliability = compute_reliability_metrics(
        fixes, accuracy_thresholds_m=[0.1, 0.25, 0.5, 1.0, 2.0]
    )
    path_metrics = compute_path_metrics(path, fixes)

    scheduling_model = spec.scheduling_model or "scheduled"
    scalability = evaluate_scalability(
        method=ranging_method,
        anchor_count=anchor_count,
        tag_count=spec.tag_count if spec.tag_count is not None else 1,
        requested_update_rate_hz=spec.update_rate_hz if spec.update_rate_hz is not None else 1.0,
        frame_duration_s=spec.frame_duration_s,
        guard_duration_s=spec.guard_duration_s,
        scheduling_model=scheduling_model,
        packet_loss_probability=spec.packet_loss_probability or 0.0,
    )

    geometry_results = []
    for pt in path.points():
        if ranging_method == RangingMethod.TDOA:
            geometry_results.append(
                evaluate_tdoa_geometry(pt, anchors, sigma_range_m=sigma_estimate)
            )
        else:
            geometry_results.append(evaluate_geometry(pt, anchors, sigma_range_m=sigma_estimate))
    geometry_valid_fraction = float(
        np.mean([g.geometry_valid for g in geometry_results])
    )
    representative_geometry = geometry_results[0]
    if ranging_method == RangingMethod.TDOA:
        representative_crlb = tdoa_crlb(path.points()[0], anchors, sigma_range_m=sigma_estimate)
    else:
        representative_crlb = range_crlb(path.points()[0], anchors, sigma_range_m=sigma_estimate)

    return ScenarioResult(
        spec=spec,
        anchors=anchors,
        path=path,
        fixes=fixes,
        accuracy=accuracy,
        reliability=reliability,
        scalability=scalability,
        path_metrics=path_metrics,
        geometry_valid_fraction=geometry_valid_fraction,
        representative_geometry=representative_geometry,
        representative_crlb=representative_crlb,
        error_model_evidence=evidence,
        n_path_samples=path.n_samples,
    )
