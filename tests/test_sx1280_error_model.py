"""Hardware-calibrated SX1280 range-error model built from Robinson's data.

The model must not invent a range-dependent or configuration-dependent
relationship that six unrepeated data points cannot support, and it must
not silently claim to be a measurement.
"""
import numpy as np
import pytest

from locbench3d.core.evidence import EvidenceType
from locbench3d.hardware.sx1280_error_model import (
    RobinsonCalibratedErrorModel,
    build_robinson_calibrated_model,
)


def test_model_evidence_type_is_hardware_calibrated_not_measured():
    model = build_robinson_calibrated_model(seed=1)
    assert model.evidence.evidence_type == EvidenceType.HARDWARE_CALIBRATED_MODEL


def test_model_sample_errors_come_from_the_published_set():
    model = build_robinson_calibrated_model(seed=1)
    samples = model.sample_errors_m(n=1000)
    published = {4.4, 7.6, 3.0, -2.0, 1.0, 3.0}
    assert set(np.round(samples, 6)).issubset(published)


def test_model_does_not_claim_range_dependence():
    """With 6 unrepeated points the model must say explicitly that it does
    not condition on range, rather than silently interpolating a trend."""
    model = build_robinson_calibrated_model(seed=1)
    assert "range" in model.scope_note.lower()
    assert "does not condition" in model.scope_note.lower() or (
        "not conditioned" in model.scope_note.lower()
    )


def test_model_is_deterministic_given_seed():
    a = build_robinson_calibrated_model(seed=42).sample_errors_m(n=20)
    b = build_robinson_calibrated_model(seed=42).sample_errors_m(n=20)
    np.testing.assert_array_equal(a, b)


def test_sample_count_matches_request():
    model = build_robinson_calibrated_model(seed=7)
    assert len(model.sample_errors_m(n=37)) == 37
