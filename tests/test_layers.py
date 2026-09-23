"""What the coverage sweep knows, beyond how many anchors reach.

The sweep runs a full link budget for every anchor at every cell — that
is what makes it the slowest thing here — and used to keep one bit of
each. These are the other three readings it was already computing and
throwing away (ADR-0044).
"""

import json
import math

import numpy as np
import pytest

from yerkon.evaluate import CoverageGrid, coverage_grid
from yerkon.layout import DILUTION_CEILING, FEWEST_FOR_A_FIX
from yerkon.viewer.scene import _bands, sweep
from yerkon.viewer.state import from_scenario


@pytest.fixture(scope="module")
def swept():
    """One real sweep, shared. It costs seconds, and every test below
    asks a different question of the same answer."""
    state = from_scenario("rural")
    terrain = state.terrain()
    return coverage_grid(
        state.deployment(terrain), terrain,
        target_sigma_m=state.tolerance_m,
        resolution_m=state.sweep_m * 2,        # coarser: this is a test
        margin_m=3000.0,
    )


# --- The count is still the count ----------------------------------------


def test_the_reading_that_was_always_there_is_unchanged(swept):
    """The loop was restructured to keep what it was discarding, and the
    first thing that must survive that is the number the published area
    column is made of."""
    assert swept.counts.dtype == np.dtype(int)
    assert swept.counts.min() >= 0
    by_hand = float(np.count_nonzero(swept.counts >= 4)) * swept.cell_km2
    assert swept.area_reached_by(4) == pytest.approx(by_hand)
    # Reached is a superset of served, always, and this is the ADR-0012
    # distinction the count exists to make.
    assert swept.area_reached_by(1) >= swept.area_reached_by(4)


# --- What the other three say --------------------------------------------


def test_every_layer_covers_the_same_ground_as_the_count(swept):
    for layer in (swept.margin_db, swept.sigma_m, swept.dilution):
        assert layer.shape == swept.counts.shape


def test_nothing_reaches_means_no_number_rather_than_a_small_one(swept):
    """NaN and not zero. Zero decibels of margin is an answer — a link
    that closes with nothing to spare — and "no anchor reaches here" is a
    different fact that must not be painted in the same colour."""
    nothing = swept.counts == 0
    if not nothing.any():
        pytest.skip("this deployment reaches every cell swept")
    assert np.isnan(swept.sigma_m[nothing]).all()
    assert np.isnan(swept.dilution[nothing]).all()


def test_there_is_no_dilution_until_there_is_a_fix(swept):
    """Two ranges put a receiver on one of two points, so there is no
    geometry to report and reporting one anyway would be a number
    somebody could read as a result (ADR-0040)."""
    assert FEWEST_FOR_A_FIX == 3
    too_few = swept.counts < FEWEST_FOR_A_FIX
    assert np.isnan(swept.dilution[too_few]).all()


def test_a_dilution_that_is_reported_is_a_real_one(swept):
    """The ceiling is how the layout module says "no fix here"; this grid
    says it with NaN. Converted once rather than asking every reader to
    know both spellings."""
    said = swept.dilution[np.isfinite(swept.dilution)]
    assert said.size, "some ground has a fix"
    assert said.min() >= 0.7, "below the four-square ideal would be wrong"
    assert said.max() < DILUTION_CEILING


def test_the_error_is_the_ranging_sigma_times_the_geometry(swept):
    """The same two quantities the published HPE column is made of, and
    the standard reading of what geometry does to a range error."""
    both = np.isfinite(swept.sigma_m) & np.isfinite(swept.dilution)
    assert both.any()
    assert swept.error_m[both] == pytest.approx(
        swept.sigma_m[both] * swept.dilution[both])
    assert np.isnan(swept.error_m[~both]).all()


def test_the_margin_reported_is_one_a_link_actually_had(swept):
    """Margin is only defined for a link that closes, and `rf` refuses to
    invent one for a link that does not — so anything finite here came
    from a budget that closed and is therefore not negative."""
    said = swept.margin_db[np.isfinite(swept.margin_db)]
    assert said.size
    assert said.min() >= 0.0


def test_a_grid_that_was_never_given_the_extra_layers_still_works():
    """They are optional on the dataclass, because `coverage_grid` is not
    the only thing that has ever built one."""
    bare = CoverageGrid(counts=np.array([[0, 4]]), xs=np.array([0.0, 1.0]),
                        ys=np.array([0.0]), resolution_m=1.0)
    assert bare.error_m is None
    assert bare.area_reached_by(4) == pytest.approx(bare.cell_km2)


# --- What reaches the page -----------------------------------------------


def test_the_payload_is_json_and_says_null_where_there_is_no_number():
    """NaN is not JSON. `json.dumps` writes a bare `NaN`, which
    `JSON.parse` refuses — so one unreachable cell would have been a page
    that stopped updating."""
    payload = sweep(from_scenario("urban"))
    text = json.dumps(payload)
    assert "NaN" not in text
    assert json.loads(text) == payload

    for name in ("anchors", "margin_db", "dilution", "error_m"):
        assert name in payload["layers"], name
        assert len(payload["layers"][name]) == len(payload["ys"])


def test_a_layer_that_reads_better_as_it_grows_gets_one_more_threshold():
    """Four bands either way. A rising layer needs a floor below which
    nothing is painted; a falling one does not, because "nothing here"
    arrives as a null."""
    bands = _bands(from_scenario("urban"))
    assert len(bands["anchors"]) == 4
    assert len(bands["margin_db"]) == 4
    assert len(bands["dilution"]) == 3
    assert len(bands["error_m"]) == 3
    for name, edges in bands.items():
        assert list(edges) == sorted(edges), name


def test_the_error_bands_are_multiples_of_this_rows_own_tolerance():
    """Because the question this project asks is whether ground meets the
    bar, not how it scores against an abstract scale (ADR-0015). Move the
    bar and the picture moves with it."""
    from dataclasses import replace

    state = from_scenario("urban")
    loose = _bands(replace(state, tolerance_m=10.0))["error_m"]
    tight = _bands(replace(state, tolerance_m=2.0))["error_m"]
    assert loose == [10.0, 20.0, 40.0]
    assert tight == [2.0, 4.0, 8.0]


def test_an_arrangement_with_nothing_in_it_still_says_where_the_bands_are():
    """The picker and its legend are drawn before any anchor is placed,
    and a legend with no numbers in it is a legend that has to be
    explained (ADR-0043)."""
    from yerkon.presets import empty_state
    from yerkon.viewer.state import ViewState

    blank = empty_state("urban", from_scenario)
    state = ViewState().merged({k: v for k, v in blank.items()
                                if k != "scenario"})
    payload = sweep(state)
    assert payload["layers"] == {}
    assert payload["bands"]["error_m"] == [state.tolerance_m,
                                           state.tolerance_m * 2,
                                           state.tolerance_m * 4]


# --- The finding this makes visible --------------------------------------


def test_anchors_in_a_line_colour_the_ground_beside_them_badly():
    """ADR-0011 as a picture rather than as a finding.

    A corridor puts anchors along a road. Off to the side the geometry
    opens up; on the line itself it collapses, and the error layer is
    where somebody sees that without running anything.
    """
    from dataclasses import replace

    state = from_scenario("rural")
    # One run, all anchors on one side, which is the arrangement ADR-0011
    # is about: masts raised along a corridor, 4 km apart. Written out
    # rather than taken from the rural row, which stands on the
    # distribution network's poles now (ADR-0079) and is not a corridor.
    in_a_line = replace(
        state, width_m=0.0,
        runs=tuple(replace(run, mounting="mast", spacing_m=4000.0,
                           offset_m=0.0, stagger_m=0.0)
                   for run in state.runs),
    )
    terrain = in_a_line.terrain()
    grid = coverage_grid(
        in_a_line.deployment(terrain), terrain,
        target_sigma_m=in_a_line.tolerance_m,
        resolution_m=in_a_line.sweep_m * 2, margin_m=2000.0,
    )
    said = grid.dilution[np.isfinite(grid.dilution)]
    if not said.size:
        pytest.skip("nothing on this line has three anchors in reach")
    # Somewhere along that line the geometry is poor. Loosely: the point
    # is that the layer distinguishes, not that it hits a figure.
    assert said.max() > 2.0, said.max()
    assert math.isfinite(float(said.max()))
