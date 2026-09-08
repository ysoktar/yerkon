"""Ranging error models for the two radios YERKON specifies.

Two models, with deliberately different standing:

``build_sx1280_model`` resamples six real published measurements. It is the
only place in this project where a number traces back to hardware someone
actually switched on. It is also six points from one hobbyist test at one
configuration over 0-250 m, which is far less than a characterised error
model, and the scope note says so.

``build_dwm3000_model`` is a configured Gaussian. No calibrated DWM3000
data was available, so the model is parameterised to the accuracy target
the YERKON presentation states for the part. A target is not a
measurement, and the evidence type (SIMULATED_MONTE_CARLO) keeps that
visible in every output row.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from yerkon.evidence import EvidenceRecord, EvidenceType

ROBINSON_URL = (
    "https://stuartsprojects.github.io/2019/04/26/"
    "Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html"
)

#: Stuart Robinson's six published short-range SX1280 observations, as
#: (true range [m], indicated range [m]). The YERKON presentation cites the
#: same source for its sub-metre line-of-sight claim.
ROBINSON_OBSERVATIONS: tuple[tuple[float, float], ...] = (
    (0.0, 4.4),
    (50.0, 57.6),
    (100.0, 103.0),
    (150.0, 148.0),
    (200.0, 201.0),
    (250.0, 253.0),
)

#: Range envelope the six observations actually cover. Ranging errors used
#: beyond this are extrapolation, and the scenario results report what
#: fraction of their links fall outside it.
ROBINSON_VALID_RANGE_M = (0.0, 250.0)

_SX1280_SCOPE = (
    "Bootstrap resample of Stuart Robinson's six published short-range "
    "SX1280 ranging observations (0-250 m, one hardware and environment "
    "configuration, published on a personal engineering blog). Errors are "
    "drawn with replacement from those six values. The model does not "
    "condition on range, bandwidth, spreading factor, line-of-sight state, "
    "temperature or antenna orientation, because six unrepeated points "
    "cannot support fitting any of those. It is a small-sample stand-in "
    "for a characterised error model, not a validated one."
)

_DWM3000_SCOPE_TEMPLATE = (
    "Configured Gaussian range error, N(0, {sigma} m), plus an NLOS bias "
    "applied to a fraction of links. Parameterised to the +/-10 cm class "
    "accuracy the YERKON presentation states for the DWM3000 module. No "
    "calibrated DWM3000 measurements were available to this project, so "
    "this is a design target expressed as a distribution, not a measured "
    "error model."
)


@dataclass(frozen=True)
class RangingErrorModel:
    """A sampler of range errors in metres, with its provenance attached."""

    name: str
    evidence: EvidenceRecord
    sample: Callable[[int], np.ndarray] = field(repr=False)
    population_errors_m: Optional[tuple[float, ...]] = None
    mean_bias_m: float = 0.0
    #: True when the model's own errors already contain multipath, as a
    #: waveform simulation through a channel does. Layering a separate NLOS
    #: bias on top of such a model counts the same physics twice.
    includes_multipath: bool = False
    #: How to rebuild this model with a different random seed.
    #:
    #: ``sample`` closes over a generator, so it carries state: calling it
    #: twice gives different draws. That is correct for one run and wrong
    #: for comparing two, because the second scenario in a process would
    #: silently draw from a different point in the stream. Any code that
    #: runs more than one scenario has to reseed first, and needs a way to
    #: do it that does not know how the model was built.
    respawn: Optional[Callable[[int], "RangingErrorModel"]] = field(
        default=None, repr=False
    )
    #: Link distances the model's evidence actually covers, in metres.
    #: ``None`` means the model makes no distance-dependent claim, so there
    #: is nothing to extrapolate beyond. Reporting a link as outside the
    #: envelope only means something when the model has one.
    valid_range_m: Optional[tuple[float, float]] = None

    def reseed(self, seed: int) -> "RangingErrorModel":
        """An identical model whose sampler starts from ``seed``.

        Returns self where the model does not know how to rebuild itself,
        which keeps this safe to call on any model but means the caller
        should set ``respawn`` on models it intends to compare.
        """
        if self.respawn is None:
            return self
        return self.respawn(seed)

    def sigma_m(self, n: int = 4000) -> float:
        """Standard deviation of the sampled error, estimated by sampling.

        Used to give the geometry check a noise scale; not a published
        specification.
        """
        return float(np.std(self.sample(n)))


def robinson_errors_m() -> tuple[float, ...]:
    """The six published errors (indicated minus true range)."""
    return tuple(indicated - truth for truth, indicated in ROBINSON_OBSERVATIONS)


def build_sx1280_model(seed: int = 0, calibrated: bool = True) -> RangingErrorModel:
    """Bootstrap model over Robinson's measured SX1280 errors.

    With ``calibrated=True`` the mean of the six errors is subtracted
    first. That models the per-unit ranging offset calibration the YERKON
    presentation calls for in its own architecture section: a constant
    offset is exactly what a per-unit calibration removes. With
    ``calibrated=False`` the raw published errors are used, showing what
    the same deployment produces if that step is skipped.
    """
    errors = np.array(robinson_errors_m(), dtype=float)
    bias = float(np.mean(errors))
    population = errors - bias if calibrated else errors
    rng = np.random.default_rng(seed)

    if calibrated:
        caveat = (
            "Mean bias of {:.2f} m removed, modelling the per-unit ranging "
            "offset calibration the YERKON architecture specifies. The "
            "residual spread is unchanged and still comes from six points."
        ).format(bias)
    else:
        caveat = (
            "Raw published errors, including their {:.2f} m mean bias. "
            "Represents a deployment that skips per-unit offset calibration."
        ).format(bias)

    return RangingErrorModel(
        name="Semtech SX1280 (Robinson bootstrap, {})".format(
            "calibrated" if calibrated else "uncalibrated"
        ),
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.HARDWARE_CALIBRATED_MODEL,
            source_name="Bootstrap resample of Stuart Robinson SX1280 short-range errors",
            source_url=ROBINSON_URL,
            source_scope=_SX1280_SCOPE,
            caveats=caveat,
        ),
        sample=lambda n: rng.choice(population, size=n, replace=True),
        population_errors_m=tuple(float(v) for v in population),
        mean_bias_m=0.0 if calibrated else bias,
        valid_range_m=ROBINSON_VALID_RANGE_M,
        respawn=lambda s: build_sx1280_model(seed=s, calibrated=calibrated),
    )


def build_dwm3000_model(
    seed: int = 0,
    sigma_m: float = 0.03,
    nlos_probability: float = 0.10,
    nlos_bias_m: float = 0.30,
) -> RangingErrorModel:
    """Configured Gaussian plus NLOS bias for the DWM3000 UWB module."""
    if sigma_m <= 0:
        raise ValueError("sigma_m must be positive")
    if not 0.0 <= nlos_probability <= 1.0:
        raise ValueError("nlos_probability must be in [0, 1]")
    rng = np.random.default_rng(seed)

    def sample(n: int) -> np.ndarray:
        values = rng.normal(0.0, sigma_m, n)
        if nlos_probability > 0.0:
            values = values + (rng.random(n) < nlos_probability) * nlos_bias_m
        return values

    return RangingErrorModel(
        name="Qorvo DWM3000 (configured, not calibrated)",
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
            source_name="Configured Gaussian/NLOS model for DWM3000 UWB",
            source_scope=_DWM3000_SCOPE_TEMPLATE.format(sigma=sigma_m),
            caveats=(
                "NLOS probability {:.0%} and bias {:.2f} m are this project's "
                "assumptions, not measurements."
            ).format(nlos_probability, nlos_bias_m),
        ),
        sample=sample,
        respawn=lambda s: build_dwm3000_model(
            seed=s,
            sigma_m=sigma_m,
            nlos_probability=nlos_probability,
            nlos_bias_m=nlos_bias_m,
        ),
    )


def add_nlos(
    model: RangingErrorModel,
    seed: int,
    nlos_probability: float,
    nlos_bias_m: float,
) -> RangingErrorModel:
    """Layer an NLOS bias on top of an existing error model.

    Robinson's measurements come from one environment, so they carry
    whatever multipath that environment had and nothing more. Urban canyon
    and rural roadside links block differently, and this adds that
    difference as an explicit, separately labelled assumption rather than
    pretending the six points already cover it.
    """
    if not 0.0 <= nlos_probability <= 1.0:
        raise ValueError("nlos_probability must be in [0, 1]")
    rng = np.random.default_rng(seed)
    base = model.sample

    def sample(n: int) -> np.ndarray:
        values = base(n)
        if nlos_probability > 0.0:
            values = values + (rng.random(n) < nlos_probability) * nlos_bias_m
        return values

    caveat = model.evidence.caveats
    extra = (
        "NLOS bias of {:.2f} m applied to {:.0%} of links is an engineering "
        "assumption layered on top of the measured error distribution."
    ).format(nlos_bias_m, nlos_probability)
    return RangingErrorModel(
        name=model.name + " + NLOS",
        evidence=EvidenceRecord(
            evidence_type=model.evidence.evidence_type,
            source_name=model.evidence.source_name,
            source_url=model.evidence.source_url,
            source_scope=model.evidence.source_scope,
            caveats=(caveat + " " + extra).strip(),
        ),
        sample=sample,
        population_errors_m=model.population_errors_m,
        mean_bias_m=model.mean_bias_m,
        valid_range_m=model.valid_range_m,
        respawn=lambda s: add_nlos(
            model.reseed(s), s, nlos_probability, nlos_bias_m
        ),
    )
