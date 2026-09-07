"""Read the MATLAB ranging simulation's output and turn it into error models.

``matlab/yerkon_ranging_sim.m`` derives ranging error from the waveform,
the multipath channel and the signal-to-noise ratio, rather than assuming
a distribution. This module reads what it produced and builds a
:class:`~yerkon.ranging_error.RangingErrorModel` from it, so the scenarios
can run on a derived error distribution instead of an assumed one.

The evidence type is ``WAVEFORM_SIMULATION``, deliberately its own class.
It is stronger than a design target expressed as a Gaussian, because the
bandwidth dependence and the line-of-sight asymmetry fall out of physics
rather than being chosen. It is weaker than a hardware measurement,
because the multipath channel parameters are this project's and no antenna
was ever switched on.

The pipeline runs without any of this. Import is opt-in, and where no CSV
is present the scenarios use their published-data and design-target models
as before.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from yerkon.evidence import EvidenceRecord, EvidenceType
from yerkon.ranging_error import RangingErrorModel

#: Where the MATLAB script writes, relative to the repository root.
DEFAULT_EXPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "matlab", "export"
)
TRIAL_FILENAME = "yerkon_ranging_errors.csv"
SUMMARY_FILENAME = "yerkon_ranging_summary.csv"
IMU_DRIFT_FILENAME = "yerkon_imu_drift.csv"

REQUIRED_TRIAL_COLUMNS = (
    "case", "radio", "condition", "bandwidth_hz", "snr_db",
    "true_range_m", "trial", "range_error_m",
)


@dataclass(frozen=True)
class WaveformCase:
    """Every trial the MATLAB run produced for one case."""

    case: str
    radio: str
    condition: str
    bandwidth_hz: float
    errors_m: np.ndarray

    @property
    def mean_bias_m(self) -> float:
        return float(np.mean(self.errors_m))

    @property
    def sigma_m(self) -> float:
        """Spread after the constant offset is removed.

        The constant part is what per-unit ranging calibration takes out,
        so it is reported separately rather than folded into the spread.
        """
        return float(np.std(self.errors_m))

    @property
    def p95_abs_error_m(self) -> float:
        return float(np.percentile(np.abs(self.errors_m), 95))


def load_trials(path: Optional[str] = None) -> dict[str, WaveformCase]:
    """Read the per-trial CSV, grouped by case.

    Raises if the file is missing or its columns are not the ones the
    MATLAB script writes, rather than guessing at a different layout.
    """
    path = path or os.path.join(DEFAULT_EXPORT_DIR, TRIAL_FILENAME)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "No MATLAB ranging output at {}. Run matlab/yerkon_ranging_sim.m "
            "and copy its export/ files here first.".format(path)
        )

    grouped: dict[str, list[float]] = {}
    meta: dict[str, tuple[str, str, float]] = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_TRIAL_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "{} is missing columns {}; expected the layout written by "
                "matlab/yerkon_ranging_sim.m".format(path, missing)
            )
        for row in reader:
            case = row["case"]
            grouped.setdefault(case, []).append(float(row["range_error_m"]))
            meta.setdefault(
                case,
                (row["radio"], row["condition"], float(row["bandwidth_hz"])),
            )

    if not grouped:
        raise ValueError("{} contains no trials".format(path))

    cases = {}
    for case, errors in grouped.items():
        radio, condition, bandwidth = meta[case]
        cases[case] = WaveformCase(
            case=case,
            radio=radio,
            condition=condition,
            bandwidth_hz=bandwidth,
            errors_m=np.array(errors, dtype=float),
        )
    return cases


def build_model_from_cases(
    cases: Sequence[WaveformCase],
    name: str,
    seed: int = 0,
    calibrated: bool = True,
) -> RangingErrorModel:
    """Bootstrap an error model over the simulated trials.

    Resampling the trials keeps whatever shape the simulation produced,
    including the heavy tail a narrowband receiver gets when it locks to a
    reflection. Fitting a Gaussian would throw that away, and the tail is
    the interesting part.
    """
    if not cases:
        raise ValueError("build_model_from_cases needs at least one case")

    pooled = np.concatenate([c.errors_m for c in cases])
    bias = float(np.mean(pooled))
    population = pooled - bias if calibrated else pooled
    rng = np.random.default_rng(seed)

    conditions = sorted({c.condition for c in cases})
    bandwidths = sorted({c.bandwidth_hz for c in cases})
    radios = sorted({c.radio for c in cases})

    scope = (
        "Bootstrap over {} waveform-level ranging trials simulated in MATLAB "
        "for {} at {} MHz bandwidth, conditions {}. Error comes from the "
        "transmitted waveform, a cluster-based multipath channel and the "
        "signal-to-noise ratio, through a leading-edge or peak time-of-"
        "arrival estimator. Nothing here was measured on hardware: the "
        "channel parameters follow the shape of the IEEE 802.15.4a models "
        "but are this project's, and the estimator is a reference "
        "implementation rather than any vendor's."
    ).format(
        pooled.size,
        "/".join(radios),
        "/".join("{:.3f}".format(b / 1e6) for b in bandwidths),
        "/".join(conditions),
    )

    caveat = (
        "Constant offset of {:.2f} m removed; per-unit ranging calibration "
        "is what takes that out in a deployment."
    ).format(bias) if calibrated else (
        "Raw simulated error including its {:.2f} m constant offset."
    ).format(bias)

    return RangingErrorModel(
        name=name,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.WAVEFORM_SIMULATION,
            source_name="MATLAB waveform-level ranging simulation",
            source_scope=scope,
            caveats=caveat,
        ),
        sample=lambda n: rng.choice(population, size=n, replace=True),
        population_errors_m=tuple(float(v) for v in population),
        mean_bias_m=0.0 if calibrated else bias,
    )


def summarise(cases: dict[str, WaveformCase]) -> list[dict]:
    """One row per case, for reporting what the MATLAB run found."""
    rows = []
    for case in sorted(cases.values(), key=lambda c: (c.radio, c.bandwidth_hz, c.condition)):
        rows.append(
            {
                "case": case.case,
                "radio": case.radio,
                "condition": case.condition,
                "bandwidth_mhz": case.bandwidth_hz / 1e6,
                "trials": int(case.errors_m.size),
                "mean_bias_m": case.mean_bias_m,
                "sigma_m": case.sigma_m,
                "p95_abs_error_m": case.p95_abs_error_m,
            }
        )
    return rows


@dataclass(frozen=True)
class ImuDrift:
    """How far a receiver drifts on inertial data alone, per outage length.

    This is the quantity the filter needs and the one the Python model was
    guessing at. It comes from MATLAB's ``imuSensor``, which carries the
    stochastic terms a real MEMS unit has, including bias instability as a
    random walk rather than the constant offset assumed here.
    """

    outage_s: np.ndarray
    drift_p50_m: np.ndarray
    drift_p95_m: np.ndarray

    def drift_at(self, seconds: float, percentile: str = "p50") -> float:
        """Interpolate the drift for an outage of a given length."""
        curve = self.drift_p50_m if percentile == "p50" else self.drift_p95_m
        return float(np.interp(seconds, self.outage_s, curve))

    def implied_accel_noise_m_s2(self, seconds: float = 1.0) -> float:
        """Acceleration noise that reproduces the measured drift.

        Free-inertial position error from white acceleration noise grows as
        roughly ``sigma * t^2 / 2``, so inverting at one outage length gives
        the figure the Python filter should be using instead of a guess.
        """
        drift = self.drift_at(seconds)
        return float(2.0 * drift / (seconds**2))


def load_imu_drift(path: Optional[str] = None) -> ImuDrift:
    """Read the drift curve written by matlab/yerkon_imu_char.m."""
    path = path or os.path.join(DEFAULT_EXPORT_DIR, IMU_DRIFT_FILENAME)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "No MATLAB IMU characterisation at {}. Run "
            "matlab/yerkon_imu_char.m and copy its export/ files here "
            "first.".format(path)
        )

    required = ("outage_s", "position_drift_p50_m", "position_drift_p95_m")
    outages, p50, p95 = [], [], []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "{} is missing columns {}; expected the layout written by "
                "matlab/yerkon_imu_char.m".format(path, missing)
            )
        for row in reader:
            outages.append(float(row["outage_s"]))
            p50.append(float(row["position_drift_p50_m"]))
            p95.append(float(row["position_drift_p95_m"]))

    if not outages:
        raise ValueError("{} contains no rows".format(path))

    order = np.argsort(outages)
    return ImuDrift(
        outage_s=np.array(outages)[order],
        drift_p50_m=np.array(p50)[order],
        drift_p95_m=np.array(p95)[order],
    )
