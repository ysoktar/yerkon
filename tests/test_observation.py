"""What the estimator is allowed to see, and what it is not."""

import pytest

from yerkon.observation import RangeObservation


def a_range(**overrides):
    fields = dict(
        at_s=0.0,
        anchor_position_m=(0.0, 0.0, 25.0),
        measured_range_m=5000.0,
        variance_m2=25.0,
    )
    fields.update(overrides)
    return RangeObservation(**fields)


def test_an_observation_reports_sigma_from_the_variance_it_carries():
    assert a_range(variance_m2=9.0).sigma_m == pytest.approx(3.0)


def test_a_measurement_with_no_uncertainty_is_refused():
    """A zero variance weights one measurement infinitely in a solve."""
    with pytest.raises(ValueError, match="weighted infinitely"):
        a_range(variance_m2=0.0)


def test_a_negative_range_is_refused():
    with pytest.raises(ValueError, match="cannot be negative"):
        a_range(measured_range_m=-1.0)


def test_an_observation_carries_no_truth():
    """ADR-0003, checked on the type rather than on a comment.

    Anything the estimator could use to shortcut its way to the answer
    would have to be a field here, so the fields are the whole of what it
    can see.
    """
    allowed = {
        "at_s",
        "anchor_position_m",
        "measured_range_m",
        "variance_m2",
        "anchor_id",
    }
    assert set(RangeObservation.__dataclass_fields__) == allowed


def test_an_observation_cannot_be_edited_after_the_fact():
    with pytest.raises(Exception):
        a_range().measured_range_m = 1.0
