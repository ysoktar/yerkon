import pytest

from yerkon.evidence import Provenance, Sourced


def test_a_value_carries_its_source_into_arithmetic():
    gain = Sourced(3.2, "dBi", Provenance.DATASHEET, "Inventek W24P-U")
    assert float(gain) == 3.2
    assert gain.provenance is Provenance.DATASHEET


def test_a_number_without_a_source_is_refused():
    with pytest.raises(ValueError, match="source"):
        Sourced(1.0, "m", Provenance.DATASHEET, "  ")


def test_an_assumption_must_say_what_it_rests_on():
    """A guess that looks like a fact is the thing this module prevents."""
    with pytest.raises(ValueError, match="note"):
        Sourced(0.5, "m", Provenance.ASSUMPTION, "this project")

    allowed = Sourced(
        0.5, "m", Provenance.ASSUMPTION, "this project",
        note="No survey exists for the pilot site.",
    )
    assert allowed.value == 0.5
