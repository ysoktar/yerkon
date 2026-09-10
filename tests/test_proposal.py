"""One edit, one confirmation, every consequence shown. See ADR-0009."""

import pytest

from yerkon.design import Design
from yerkon.numbers import decimal_comma
from yerkon.proposal import confirm, propose
from yerkon.regulatory import UNITED_STATES
from yerkon.world import ROADSIDE_SIGN, TALL_MAST


# --- How numbers are written ----------------------------------------------


@pytest.mark.parametrize(
    "value, places, expected",
    [
        (5520.6, 0, "5521"),
        (5.52, 2, "5,52"),
        (12.108, 1, "12,1"),
        (1234567.0, 0, "1234567"),
        (0.5, 2, "0,50"),
    ],
)
def test_numbers_use_a_comma_and_no_thousands_separator(value, places, expected):
    assert decimal_comma(value, places) == expected


# --- What a proposal contains ---------------------------------------------


def test_an_edit_that_changes_nothing_proposes_nothing():
    proposal = propose(Design(), mounting=TALL_MAST)
    assert not proposal.changes_anything
    assert proposal.describe() == "Nothing would change."


def test_the_asked_for_change_is_separated_from_what_follows():
    proposal = propose(Design(), mounting=ROADSIDE_SIGN)

    assert [c.label for c in proposal.asked] == ["mounting"]
    assert all(not c.is_consequence for c in proposal.asked)
    assert all(c.is_consequence for c in proposal.follows)
    assert "usable range" in [c.label for c in proposal.follows]


def test_every_consequence_says_why_it_follows():
    """A number moving with no reason given is the thing to avoid."""
    proposal = propose(Design(), region=UNITED_STATES)
    assert proposal.follows
    for change in proposal.follows:
        assert change.because, change.label


def test_the_panel_shows_old_and_new_for_everything_that_moves():
    panel = propose(Design(), mounting=ROADSIDE_SIGN).describe()

    assert "tall mast -> roadside sign" in panel
    assert "25,0 m -> 3,0 m" in panel
    assert "5,52 km -> 1,66 km" in panel
    assert "because" in panel


def test_a_change_with_no_consequences_says_so_rather_than_going_quiet():
    """Silence would read as a panel that failed to compute them."""
    panel = propose(Design(), receiver_height_m=1.6).describe()
    assert "Nothing else follows" in panel or "Which also changes" in panel


def test_a_tolerance_nothing_meets_reads_as_such_not_as_zero_kilometres():
    panel = propose(Design(), target_ranging_sigma_m=1.0).describe()
    assert "no distance meets it" in panel
    assert "0,00 km" not in panel


def test_a_search_that_ran_out_of_room_is_not_reported_as_a_range():
    """No legal configuration reaches the limit now, so the renderer is
    checked directly rather than through one that used to."""
    from yerkon.proposal import show_outcome
    from yerkon.rf import DEFAULT_SEARCH_LIMIT_M

    assert show_outcome("closure_range_m", DEFAULT_SEARCH_LIMIT_M) == "beyond 60 km"
    assert show_outcome("closure_range_m", DEFAULT_SEARCH_LIMIT_M + 1.0) == (
        "beyond 60 km"
    )
    assert "km" in show_outcome("closure_range_m", 11_707.0)


# --- Confirming ------------------------------------------------------------


def test_one_edit_asks_once_however_many_values_move():
    asked = []

    def ask(panel):
        asked.append(panel)
        return True

    design, applied = confirm(
        Design(), ask, mounting=ROADSIDE_SIGN, region=UNITED_STATES
    )

    assert len(asked) == 1, "a batch is one question, not one per consequence"
    assert applied
    assert design.mounting is ROADSIDE_SIGN
    assert design.region is UNITED_STATES


def test_the_whole_panel_is_what_gets_asked():
    """The person answering sees the consequences, not just the edit."""
    seen = []
    confirm(Design(), lambda panel: seen.append(panel) or True,
            mounting=ROADSIDE_SIGN)
    assert "usable range" in seen[0]


def test_refusing_leaves_nothing_half_applied():
    original = Design()
    design, applied = confirm(
        original, lambda panel: False, mounting=ROADSIDE_SIGN, region=UNITED_STATES
    )
    assert not applied
    assert design == original


def test_an_edit_that_changes_nothing_does_not_ask():
    asked = []
    design, applied = confirm(
        Design(), lambda panel: asked.append(panel) or True, mounting=TALL_MAST
    )
    assert asked == []
    assert not applied


# --- Figures at the precision they need ------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.0003, "0,0003"),
        (0.1, "0,1"),
        (0.5, "0,5"),
        (3.2, "3,2"),
        (16.0, "16"),
        (85000.0, "85000"),
        (240000.0, "240000"),
        (0.0, "0"),
    ],
)
def test_a_figure_is_written_at_the_precision_it_needs(value, expected):
    """Three hundred microseconds rendered at two places is zero, and a
    figure that reads as unset when it is set will be corrected by
    somebody."""
    from yerkon.numbers import readable

    assert readable(value) == expected


def test_no_default_reads_as_zero_unless_it_is_zero():
    from yerkon.numbers import readable
    from yerkon.settings import DEFAULTS

    for key, entry in DEFAULTS.entries.items():
        value = float(entry.sourced.value)
        if value != 0.0:
            assert readable(value) != "0", key
