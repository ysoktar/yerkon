"""Hardware-calibrated SX1280 ranging error model.

Built from Stuart Robinson's six published short-range observations
(``locbench3d.hardware.sx1280_published``). This is deliberately a simple
nonparametric (bootstrap resampling) model rather than a fitted Gaussian or
a range-dependent regression: six unrepeated points at six different
ranges cannot support either a distribution-shape claim or a range-
dependence claim, and inventing one would violate the project's own rule
against inferring dependencies the data does not support.

Evidence type is ``HARDWARE_CALIBRATED_MODEL``: a simulation driven by
measured (here, published-measured) range-error data, not a raw
measurement and not an unconditioned analytic model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from locbench3d.core.evidence import EvidenceRecord, EvidenceType
from locbench3d.hardware.sx1280_published import ROBINSON_RANGING_OBSERVATIONS

_SCOPE_NOTE = (
    "Resampling model built from Stuart Robinson's six published short-range "
    "SX1280 ranging observations (0-250 m, one hardware/environment "
    "configuration). The model draws errors with replacement from those six "
    "values; it does not condition on range, bandwidth, spreading factor, "
    "center frequency, LOS/NLOS state, temperature, oscillator, orientation "
    "or hardware, because six unrepeated points cannot support fitting any "
    "of those dependencies. Treat this as a rough, small-sample stand-in "
    "for a real conditional error model, not a validated one. It must not "
    "be used to claim SX1280 accuracy at ranges outside 0-250 m."
)


@dataclass(frozen=True)
class RobinsonCalibratedErrorModel:
    errors_m: tuple[float, ...]
    seed: int
    scope_note: str
    evidence: EvidenceRecord
    _rng: np.random.Generator = field(repr=False, compare=False)

    def sample_errors_m(self, n: int) -> np.ndarray:
        if n < 0:
            raise ValueError("n must be non-negative")
        values = np.asarray(self.errors_m)
        return self._rng.choice(values, size=n, replace=True)


def build_robinson_calibrated_model(seed: int = 0) -> RobinsonCalibratedErrorModel:
    errors = tuple(obs.error_m for obs in ROBINSON_RANGING_OBSERVATIONS)
    evidence = EvidenceRecord(
        evidence_type=EvidenceType.HARDWARE_CALIBRATED_MODEL,
        source_name="Bootstrap resample of Stuart Robinson SX1280 short-range errors",
        source_url=(
            "https://stuartsprojects.github.io/2019/04/26/"
            "Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html"
        ),
        source_scope=_SCOPE_NOTE,
    )
    return RobinsonCalibratedErrorModel(
        errors_m=errors,
        seed=seed,
        scope_note=_SCOPE_NOTE,
        evidence=evidence,
        _rng=np.random.default_rng(seed),
    )
