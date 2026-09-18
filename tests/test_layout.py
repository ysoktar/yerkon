"""Where the anchors go, and why one method is not the same as another."""

import math

import numpy as np
import pytest

from yerkon.layout import (
    DILUTION_CEILING,
    FEWEST_FOR_A_FIX,
    METHODS,
    Ground,
    Plan,
    Spot,
    dilution_at,
    place,
)

AREA = Ground(length_m=3000.0, width_m=3000.0, reach_m=900.0)
LINE = Ground(length_m=2000.0, width_m=0.0, reach_m=400.0)


# --- The seam -------------------------------------------------------------


@pytest.mark.parametrize("method", METHODS)
def test_every_method_is_reached_through_one_function(method):
    """The whole interface is `place(plan, ground)`.

    Adding a method is a function and a name; no caller changes, and the
    viewer's chooser is a string it got from the engine.
    """
    spots = place(Plan(method=method, spacing_m=800.0, most=30), AREA)
    assert isinstance(spots, tuple)
    assert all(isinstance(spot, Spot) for spot in spots)


@pytest.mark.parametrize("method", METHODS)
def test_no_method_places_an_anchor_off_the_site(method):
    """Past the edge is ground nobody measured (ADR-0037)."""
    for spot in place(Plan(method=method, spacing_m=800.0, most=30), AREA):
        assert -1e-6 <= spot.x_m <= AREA.length_m + 1e-6, spot
        assert -1e-6 <= spot.y_m <= AREA.width_m + 1e-6, spot


def test_a_method_nobody_has_lists_the_ones_that_exist():
    with pytest.raises(ValueError, match="grid"):
        place(Plan(method="vibes"), AREA)


def test_placing_nothing_is_a_method_rather_than_an_empty_result():
    """The arrangement somebody builds by hand starts from here."""
    assert place(Plan(method="manual"), AREA) == ()


# --- What the lattices are for --------------------------------------------


def test_the_hexagonal_lattice_covers_the_same_ground_with_fewer_anchors():
    """Kershner, 1939: a triangular lattice is the fewest equal discs that
    cover a plane, which is why cellular planning is drawn on one.

    Each lattice is compared at *its own* covering limit rather than at
    the same spacing, because the limits differ: the furthest point of a
    cell from its corners is the circumradius, which is `s/sqrt(2)` for a
    square and `s/sqrt(3)` for a triangle. So a square lattice covers up
    to `s = r*sqrt(2)` and a triangular one up to `s = r*sqrt(3)`, and
    comparing them at one spacing measures nothing.

    Coverage is read away from the edges. Both lattices lose their last
    row to the site's boundary and that is an artefact of the site rather
    than of the lattice.
    """
    reach = 900.0
    ground = Ground(length_m=12000.0, width_m=12000.0, reach_m=reach)
    inside = _cells(ground, across=60)
    keep = (
        (inside[:, 0] > reach) & (inside[:, 0] < ground.length_m - reach)
        & (inside[:, 1] > reach) & (inside[:, 1] < ground.width_m - reach)
    )
    interior = inside[keep]

    def covering(method, spacing):
        spots = place(Plan(method=method, spacing_m=spacing), ground)
        seen = np.zeros(len(interior), dtype=bool)
        for spot in spots:
            seen |= ((interior[:, 0] - spot.x_m) ** 2
                     + (interior[:, 1] - spot.y_m) ** 2) <= reach ** 2
        return len(spots), seen.mean()

    square_count, square_share = covering("grid", reach * math.sqrt(2.0))
    hex_count, hex_share = covering("hex", reach * math.sqrt(3.0))

    assert square_share > 0.99, square_share
    assert hex_share > 0.99, hex_share
    # The published ratio is 2/sqrt(3), about 15 %. Checked loosely,
    # because a finite site cannot hit an asymptotic density exactly.
    assert hex_count < square_count * 0.95, (hex_count, square_count)


def test_a_corridor_puts_anchors_on_alternating_sides():
    """A line of anchors all to one side of a road leaves the cross-track
    direction barely observable, which is what ADR-0011 is about."""
    spots = place(Plan(method="corridor", spacing_m=200.0, offset_m=6.0), LINE)
    sides = {round(spot.y_m, 3) for spot in spots}
    assert sides == {6.0, -6.0}


def test_an_area_method_falls_back_to_the_corridor_on_a_line():
    """A site with no width is a corridor, and a grid over it is a line."""
    assert place(Plan(method="grid", spacing_m=200.0, offset_m=6.0), LINE) == (
        place(Plan(method="corridor", spacing_m=200.0, offset_m=6.0), LINE)
    )


# --- Dilution, which is why this module exists ----------------------------


def test_anchors_in_a_line_leave_the_direction_across_it_unobservable():
    """ADR-0011, as a number rather than as a finding.

    Three anchors along a road and a receiver on that road: the geometry
    matrix is singular across the line, so the dilution is at the ceiling.
    Step off the line and it recovers.
    """
    road = [(0.0, 0.0), (500.0, 0.0), (1000.0, 0.0)]
    assert dilution_at((450.0, 1.0), road, 3000.0) == DILUTION_CEILING
    assert dilution_at((450.0, 5.0), road, 3000.0) > 8.0
    assert dilution_at((450.0, 200.0), road, 3000.0) < 2.0


def test_four_anchors_round_a_point_is_the_textbook_one():
    """A square with the receiver at its centre is dilution exactly one:
    the ranging error arrives as position error unamplified."""
    square = [(0.0, 0.0), (1000.0, 0.0), (0.0, 1000.0), (1000.0, 1000.0)]
    assert dilution_at((500.0, 500.0), square, 3000.0) == pytest.approx(1.0, abs=1e-6)


def test_too_few_anchors_is_the_ceiling_rather_than_a_number():
    """Two ranges put a receiver on one of two points. There is no
    dilution to report, and reporting one anyway would be a number
    somebody could read as a result."""
    assert FEWEST_FOR_A_FIX == 3
    assert dilution_at((500.0, 500.0), [(0.0, 0.0), (1000.0, 0.0)],
                       3000.0) == DILUTION_CEILING
    assert dilution_at((500.0, 500.0), [], 3000.0) == DILUTION_CEILING


def test_an_anchor_out_of_reach_does_not_count_towards_a_fix():
    """Geometry without signal is not geometry."""
    far = [(0.0, 0.0), (1000.0, 0.0), (500.0, 866.0)]
    assert dilution_at((500.0, 300.0), far, 3000.0) < 2.0
    assert dilution_at((500.0, 300.0), far, 100.0) == DILUTION_CEILING


# --- What the searches are for --------------------------------------------


def test_choosing_for_geometry_beats_choosing_for_coverage_at_the_same_count():
    """The finding this module is built to make measurable.

    Coverage is the right score for a network that wants signal
    everywhere and the wrong one here: it will happily put every anchor
    in a row. Both searches run over the same candidates with the same
    reach; the only difference is what they count.
    """
    ground = Ground(length_m=4000.0, width_m=4000.0, reach_m=1200.0)
    by_coverage = place(Plan(method="greedy-coverage", most=12), ground)
    by_geometry = place(Plan(method="greedy-dop", most=len(by_coverage)), ground)
    assert len(by_geometry) == len(by_coverage)

    cells = _cells(ground)
    from yerkon.layout import dilution_field

    worse = dilution_field(cells, [(s.x_m, s.y_m) for s in by_coverage], 1200.0)
    better = dilution_field(cells, [(s.x_m, s.y_m) for s in by_geometry], 1200.0)
    assert better.mean() < worse.mean()


def test_the_geometry_search_stops_at_the_bar_rather_than_at_the_budget():
    """Cheapest that meets, not best (ADR-0015, ADR-0023).

    One more anchor always improves a continuous score a little, so a
    search without a bar to clear returns whatever budget it was given.
    """
    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=900.0)
    generous = place(Plan(method="greedy-dop", most=200, target_dop=2.0), ground)
    assert len(generous) < 200

    stricter = place(Plan(method="greedy-dop", most=200, target_dop=1.3), ground)
    assert len(stricter) >= len(generous)


def test_k_cover_puts_enough_anchors_over_every_cell_to_fix_at_all():
    """Set cover for k rather than for one, because a position needs
    three ranges before it has a unique answer."""
    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=1100.0)
    spots = place(Plan(method="k-cover", cover_k=3, most=80), ground)
    cells = _cells(ground)
    counts = np.zeros(len(cells), dtype=int)
    for spot in spots:
        counts += (((cells[:, 0] - spot.x_m) ** 2
                    + (cells[:, 1] - spot.y_m) ** 2) <= 1100.0 ** 2).astype(int)
    assert (counts >= 3).mean() > 0.95


def test_a_search_places_on_a_structure_that_already_stands_where_there_is_one():
    """An anchor bolted to a lighting column costs the column nothing
    (ADR-0015), so where a fetch brought road furniture the candidates
    are the furniture rather than a lattice."""
    furniture = tuple(
        Spot(float(x), float(y), "column")
        for x in range(0, 3001, 500) for y in range(0, 3001, 500)
    )
    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=900.0,
                    furniture=furniture)
    spots = place(Plan(method="greedy-dop", most=12, mounting="mast"), ground)
    assert spots
    standing = {(spot.x_m, spot.y_m) for spot in furniture}
    for spot in spots:
        assert (spot.x_m, spot.y_m) in standing
        assert spot.mounting == "column", "the structure has to travel with it"


def _cells(ground: Ground, across: int = 30) -> np.ndarray:
    xs = np.linspace(0.0, ground.length_m, across)
    ys = np.linspace(0.0, max(ground.width_m, 1.0), across)
    grid_x, grid_y = np.meshgrid(xs, ys)
    return np.column_stack([grid_x.ravel(), grid_y.ravel()])


# --- Two numbers that were one, and the bug that made (ADR-0047) ---------


def test_dilution_and_being_served_are_two_different_thresholds():
    """Three is a property of the arithmetic; four is what a deployment
    needs.

    `dilution_at` inverts a two-by-two matrix — x and y, with no clock
    column (ADR-0010) and no observable vertical (ADR-0011) — so three
    ranges is where it starts meaning anything. But the estimator solves
    three unknowns, `coverage()` and `siting.Requirement` both refuse
    fewer than four ranges in those words, and the published area column
    is `area_reached_by(4)`.

    The searches used the first for the second, so one would declare
    itself finished at a count its own estimator cannot fix from.
    """
    import inspect

    from yerkon.evaluate import coverage
    from yerkon.layout import ENOUGH_TO_BE_SERVED

    assert FEWEST_FOR_A_FIX == 3
    assert ENOUGH_TO_BE_SERVED > FEWEST_FOR_A_FIX

    # Tied to what the rest of the project demands rather than written
    # down twice. `coverage` refuses fewer than four in those words, and
    # a test that read the constant it is testing would move with a bug
    # in it instead of catching one.
    assert inspect.signature(coverage).parameters[
        "anchors_required"].default == ENOUGH_TO_BE_SERVED
    with pytest.raises(ValueError, match="fewer than four"):
        coverage(None, None, anchors_required=ENOUGH_TO_BE_SERVED - 1)


def test_a_search_keeps_going_until_four_anchors_reach_not_three():
    """The bug, as a number. With three as the bar, a search over a
    square site stopped at four anchors in the corners — where no point
    saw all four — and the service area collapsed."""
    # Reach larger than the site, which is the condition the bug bites
    # under and the one Kızılay is in: 3 825 m of reach on 2 970 m of
    # ground, so a single anchor is audible everywhere and the dilution
    # bar is met almost at once. Somewhere that needs many anchors
    # anyway would place enough of them by accident and prove nothing —
    # the first version of this test did exactly that and passed with
    # the bug put back on purpose.
    #
    # Four is written out rather than read from the constant under test,
    # for the same reason.
    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=3800.0)
    spots = place(Plan(method="greedy-dop", most=60, target_dop=2.0), ground)
    cells = _cells(ground, across=25)

    counts = np.zeros(len(cells), dtype=int)
    for spot in spots:
        counts += (((cells[:, 0] - spot.x_m) ** 2
                    + (cells[:, 1] - spot.y_m) ** 2) <= 3800.0 ** 2).astype(int)
    served = (counts >= 4).mean()
    assert served > 0.8, (
        "a search that stops before four anchors reach most of the site "
        "leaves ground the area column cannot count: {:.0%}".format(served)
    )


def test_k_cover_defaults_to_the_number_the_area_column_counts():
    """It covered to three, and the column counts four, so an urban
    k-cover deployment reported nought square kilometres served."""
    assert Plan().cover_k == 4

    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=1100.0)
    spots = place(Plan(method="k-cover", most=120), ground)
    cells = _cells(ground)
    counts = np.zeros(len(cells), dtype=int)
    for spot in spots:
        counts += (((cells[:, 0] - spot.x_m) ** 2
                    + (cells[:, 1] - spot.y_m) ** 2) <= 1100.0 ** 2).astype(int)
    assert (counts >= 4).mean() > 0.95


def test_the_geometry_search_still_stops_at_its_bar_rather_than_the_budget():
    """Raising the sufficiency threshold must not turn "cheapest that
    meets" into "spend the budget" (ADR-0015, ADR-0023)."""
    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=900.0)
    generous = place(Plan(method="greedy-dop", most=200, target_dop=2.0), ground)
    assert len(generous) < 200


def test_the_number_of_anchors_a_run_covers_to_is_the_engine_s_own():
    """It was written down a third time, in the viewer, and that copy
    won: a run carries its own `cover_k` into `place`, so `Plan`'s
    default never applied. Three places, two answers (ADR-0047)."""
    from yerkon.layout import ENOUGH_TO_BE_SERVED
    from yerkon.viewer.state import AnchorRun

    run = AnchorRun("A", "e28", "mast", 0.0, 1000.0, 500.0, 25.0)
    assert run.cover_k == Plan().cover_k == ENOUGH_TO_BE_SERVED == 4


# --- What a search was asked for, and where it stopped (ADR-0056) ---------


def test_a_lattice_is_not_asked_whether_it_met_anything():
    """A spacing is not a target. Reporting a grid as having met its bar
    would invent a claim the method never made."""
    from yerkon.layout import bar_of

    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=900.0)
    for method in ("grid", "hex", "corridor", "perimeter", "manual"):
        plan = Plan(method=method, spacing_m=700.0)
        assert bar_of(plan, ground, place(plan, ground)) is None, method


@pytest.mark.parametrize("method,bar", [
    ("greedy-dop", "dilution"),
    ("k-cover", "anchors_in_reach"),
    ("greedy-coverage", "covered_share"),
])
def test_every_search_says_what_it_was_asked_for(method, bar):
    from yerkon.layout import bar_of

    ground = Ground(length_m=3000.0, width_m=3000.0, reach_m=1200.0)
    plan = Plan(method=method, most=40, target_dop=2.0, cover_k=4)
    said = bar_of(plan, ground, place(plan, ground))
    assert said is not None and said.name == bar
    assert said.wanted > 0.0


def test_a_search_that_cleared_its_bar_says_so():
    """The whole point. Over ground a search can serve, the answer is a
    result; the three tests below are the three ways it is not."""
    from yerkon.layout import bar_of

    ground = Ground(length_m=2000.0, width_m=2000.0, reach_m=2000.0)
    plan = Plan(method="k-cover", cover_k=1, most=40)
    spots = place(plan, ground)
    said = bar_of(plan, ground, spots)
    assert said.met and said.short == 0
    assert said.got >= said.wanted


def test_a_search_that_ran_out_of_budget_says_which():
    """A budget that ran out may clear the bar with a larger one, and a
    search out of candidates will not. They are the same silence from
    outside, and the next thing a person reaches for differs."""
    from yerkon.layout import bar_of

    ground = Ground(length_m=6000.0, width_m=6000.0, reach_m=500.0)
    plan = Plan(method="k-cover", cover_k=4, most=6)
    said = bar_of(plan, ground, place(plan, ground))
    assert not said.met
    assert said.spent_the_budget
    assert said.short > 0


def test_a_search_out_of_candidates_says_that_instead():
    """Every candidate taken and the bar still missed: a larger budget
    buys nothing, and the card must not suggest it would."""
    from yerkon.layout import bar_of

    # Four structures in one corner, and a site far wider than the
    # reach: everything that could be placed has been.
    corner = tuple(Spot(x, y) for x in (50.0, 150.0) for y in (50.0, 150.0))
    ground = Ground(length_m=8000.0, width_m=8000.0, reach_m=400.0,
                    furniture=corner)
    plan = Plan(method="greedy-coverage", most=99)
    spots = place(plan, ground)
    said = bar_of(plan, ground, spots)
    assert len(spots) <= len(corner)
    assert not said.met and not said.spent_the_budget
    assert said.short > 0


def test_poor_geometry_and_no_geometry_are_different_answers():
    """`greedy-dop` misses its bar two ways: somewhere cannot be fixed
    at all, or everywhere can and the geometry is merely poor. The first
    is a coverage problem and the second is a placement one, so the card
    says which."""
    from yerkon.layout import bar_of

    thin = Ground(length_m=9000.0, width_m=9000.0, reach_m=600.0)
    plan = Plan(method="greedy-dop", most=8, target_dop=2.0)
    missing = bar_of(plan, thin, place(plan, thin))
    assert not missing.met and missing.short > 0

    # Everything in reach of everything, and a target no arrangement of
    # four can beat.
    tight = Ground(length_m=800.0, width_m=800.0, reach_m=4000.0)
    fussy = Plan(method="greedy-dop", most=5, target_dop=0.2)
    poor = bar_of(fussy, tight, place(fussy, tight))
    assert not poor.met and poor.short == 0
    assert poor.got > poor.wanted


def test_the_bar_is_asked_of_what_is_standing():
    """Deleting anchors by hand can take an arrangement back under its
    bar, and then the card has to stop saying it cleared one."""
    from yerkon.layout import bar_of

    ground = Ground(length_m=1500.0, width_m=1500.0, reach_m=3000.0)
    plan = Plan(method="k-cover", cover_k=4, most=40)
    spots = place(plan, ground)
    assert len(spots) == 4 and bar_of(plan, ground, spots).met

    fewer = bar_of(plan, ground, spots[:3])
    assert not fewer.met
    assert fewer.got == 3.0 and fewer.short > 0
    assert bar_of(plan, ground, ()).got == 0.0


def test_the_bar_counts_the_way_the_search_counts():
    """`_seen_and_dilution` drops an anchor sitting exactly on a cell
    centre, because the unit vector to it is undefined and the dilution
    arithmetic needs one. For "how many anchors are in reach" it is
    plainly one of them.

    Measured with the geometry count, a k-cover arrangement the search
    had just declared complete came back one anchor short at every
    candidate that happened to land on a cell centre, and the card
    called a finished search unfinished.
    """
    from yerkon.layout import bar_of

    ground = Ground(length_m=1500.0, width_m=1500.0, reach_m=3000.0)
    for wanted in (1, 2, 3, 4):
        plan = Plan(method="k-cover", cover_k=wanted, most=40)
        spots = place(plan, ground)
        said = bar_of(plan, ground, spots)
        assert said.met, (wanted, said)
        assert said.got >= wanted
