"""Named deployment options, and the search that writes new ones."""

import math

import pytest

from yerkon.evidence import Provenance
from yerkon.options import Option, available, read, settings_for, write
from yerkon.scenarios import catalogue
from yerkon.settings import DEFAULTS
from yerkon.solve import (
    AlreadyMet,
    SEARCHABLE,
    Outcome,
    Search,
    Target,
    evaluate,
    mast_cost_tl,
    search,
)


# --- Deployment geometry is a figure, not a literal ------------------------


#: Every number that decides the shape of a deployment.
#:
#: Named as a list rather than discovered, so that adding a scenario
#: without giving it these fails here instead of silently hard-coding
#: itself back into `scenarios.py` (ADR-0023).
GEOMETRY = tuple(
    "{}.{}".format(row, knob)
    for row in ("urban", "rural")
    for knob in ("extent_m", "anchor_spacing_m", "anchor_stagger_m",
                 "anchors_per_round", "accept_sigma_m")
) + (
    "tunnel.length_m", "tunnel.anchor_spacing_m", "tunnel.anchor_offset_m",
    "tunnel.width_m", "tunnel.anchors_per_round", "tunnel.accept_sigma_m",
)


@pytest.mark.parametrize("key", GEOMETRY)
def test_every_number_that_shapes_a_deployment_is_in_the_file(key):
    """ADR-0023. One file changes every figure in the table.

    A spacing written into `scenarios.py` cannot be moved by the viewer,
    cannot be searched by `yerkon solve`, and cannot be saved as an
    option. It is exactly the kind of number this project has spent its
    whole life dragging out of code.
    """
    entry = DEFAULTS.entry(key)
    assert entry.sourced.provenance is Provenance.DESIGN, key
    assert entry.sourced.note.strip(), key
    assert entry.affects.strip(), key


def test_a_deployment_choice_is_not_counted_as_an_assumption():
    """They are different things and the report says so.

    An assumption is a placeholder waiting for somebody to measure it. A
    choice is the thing being decided — nobody can measure what anchor
    spacing "really is". Counting choices among the placeholders would
    dilute the figure that says how much of this study is still
    guesswork, which is the figure the whole costing rests on.
    """
    assert DEFAULTS.choices, "no choices are recorded"
    for entry in DEFAULTS.choices:
        assert not entry.is_assumed

    measurable = len(DEFAULTS.entries) - len(DEFAULTS.choices)
    assert DEFAULTS.assumed_share == pytest.approx(
        len(DEFAULTS.assumed) / measurable
    )


def test_moving_a_geometry_figure_moves_the_deployment():
    """The check that the wiring is real rather than declared."""
    denser = DEFAULTS.with_values({"rural.anchor_spacing_m": 2000.0,
                                   "rural.anchor_stagger_m": 1000.0})
    assert (
        len(catalogue(denser)["rural"].scenario.deployment.anchors)
        > len(catalogue(DEFAULTS)["rural"].scenario.deployment.anchors)
    )


# --- Options ---------------------------------------------------------------


def test_the_project_ships_more_than_one_deployment_to_choose_between():
    """A study with one arrangement is a study that never asked.

    The rural row alone has two defensible answers — more masts or taller
    ones — and which is right depends on costs nobody has supplied.
    Shipping both is the honest form of that.
    """
    names = available()
    assert {"rural-dense", "rural-tall"} <= set(names)


@pytest.mark.parametrize("name", sorted(available()))
def test_every_shipped_option_says_what_it_does_and_actually_does_it(name):
    option = read(name)
    assert option.title.strip()
    assert len(option.note.split()) >= 20, "an option needs a reason"
    assert option.values, "an option that changes nothing is not an option"

    moved = option.applied_to(DEFAULTS)
    for key, was, now in option.differences(DEFAULTS):
        assert moved.number(key) == pytest.approx(now)
        assert was != pytest.approx(now), key


def test_an_option_naming_a_figure_that_does_not_exist_is_refused(tmp_path):
    """Silently changing nothing is the worst outcome available.

    It would look like a deployment somebody chose and behave like the
    default, and no number anywhere would say which had been run.
    """
    with pytest.raises(KeyError, match="nothing may be assumed in the code"):
        write(Option("bad", "Bad", "x" * 40, {"not.a.figure": 1.0}),
              where=tmp_path)


def test_an_option_survives_being_written_and_read_back(tmp_path):
    option = Option(
        name="written", title="Written", origin="test",
        note="A saved option has to come back as the same option.",
        values={"rural.anchor_spacing_m": 2500.0},
    )
    write(option, where=tmp_path)
    assert read("written", where=tmp_path) == option


def test_asking_for_an_option_that_is_not_there_says_what_is(tmp_path):
    write(Option("here", "Here", "x" * 40, {"rural.extent_m": 10_000.0}),
          where=tmp_path)
    with pytest.raises(FileNotFoundError, match="here"):
        read("elsewhere", where=tmp_path)


def test_an_option_composes_with_a_settings_file_rather_than_replacing_it():
    """Somebody's real quotations and a denser grid have to survive together.

    An option is a short list of edits for exactly this reason. If it
    replaced the file, choosing a deployment would silently discard every
    measured figure in it.
    """
    measured = DEFAULTS.with_values(
        {"mounting.tall_mast.site_cost_tl": {"value": 61000.0,
                                             "source": "a quotation"}}
    )
    both = settings_for("rural-dense", measured)
    assert both.number("rural.anchor_spacing_m") == 3000.0
    assert not both.entry("mounting.tall_mast.site_cost_tl").is_assumed


# --- The search ------------------------------------------------------------


def test_a_taller_mast_costs_more_than_its_extra_length():
    """Steel and foundation grow about as the square of height.

    Unpriced, ten extra metres look like the cheapest availability in the
    study. Priced, more masts beat taller ones at equal money, and the
    whole rural recommendation turns on it.
    """
    base = DEFAULTS.number("mounting.tall_mast.height_m")
    cost = DEFAULTS.number("mounting.tall_mast.site_cost_tl")

    assert mast_cost_tl(base) == pytest.approx(cost)
    assert mast_cost_tl(2 * base) == pytest.approx(4 * cost)
    assert mast_cost_tl(base + 10.0) > cost * (base + 10.0) / base


def test_a_search_keeps_a_grid_and_a_mast_physical():
    """Figures that have to move together, move together.

    A grid staggers by half its spacing and a taller mast costs more
    steel. A search that moved one without the other would price a mast
    nobody sells, and would find bargains that do not exist.
    """
    from yerkon.solve import _follows

    complete = _follows({"rural.anchor_spacing_m": 2000.0,
                         "mounting.tall_mast.height_m": 40.0})
    assert complete["rural.anchor_stagger_m"] == 1000.0
    assert complete["mounting.tall_mast.site_cost_tl"] > DEFAULTS.number(
        "mounting.tall_mast.site_cost_tl"
    )


def an_outcome(availability=0.9, p50=2.0, p95=8.0, capex=100.0, values=None):
    return Outcome(
        values=values or {"rural.anchor_spacing_m": 4000.0},
        availability=availability, hpe_p50_m=p50, hpe_p95_m=p95,
        vpe_p95_m=100.0, fixes_per_second=1.3, anchors=33,
        capex_tl=capex, opex_tl_per_year=10.0,
    )


def test_a_target_is_a_bar_to_clear_on_every_count():
    target = Target(availability=0.9, hpe_p50_m=2.0)
    assert target.met_by(an_outcome())
    assert not target.met_by(an_outcome(availability=0.89))
    assert not target.met_by(an_outcome(p50=2.01))


def test_the_search_returns_the_cheapest_that_meets_not_the_best():
    """ADR-0015 again, for geometry rather than for structures.

    A search that maximised availability would always return the densest
    grid it was offered, because more anchors always help a little. What
    somebody with a budget needs is the least expensive arrangement that
    clears the bar.
    """
    found = Search(
        scenario="rural", target=Target(availability=0.85),
        tried=(
            an_outcome(availability=0.86, capex=100.0),
            an_outcome(availability=0.99, capex=900.0),
            an_outcome(availability=0.50, capex=10.0),
        ),
    )
    assert found.best.capex_tl == 100.0


def test_a_search_that_meets_nothing_returns_nothing():
    """Not the best of a bad set.

    A search that returned its least-bad failure would need its answer
    checked against the target by hand every time, which is how a figure
    that meets nothing ends up in a report.
    """
    found = Search(
        scenario="rural", target=Target(availability=0.99),
        tried=(an_outcome(availability=0.5), an_outcome(availability=0.6)),
    )
    assert found.best is None
    with pytest.raises(ValueError, match="nothing met"):
        found.as_option("hopeless")


def test_a_search_will_not_save_an_option_that_changes_nothing():
    """The settings in hand already being the answer is a result, not a file.

    An option whose whole content is a no-op would sit in the list
    looking like a decision.
    """
    found = Search(
        scenario="rural", target=Target(availability=0.5),
        tried=(an_outcome(values={
            "rural.anchor_spacing_m": DEFAULTS.number("rural.anchor_spacing_m")
        }),),
    )
    with pytest.raises(AlreadyMet, match="already meet"):
        found.as_option("pointless")


def test_a_search_over_a_figure_that_does_not_exist_fails_before_it_runs():
    """Forty simulations then a KeyError is the wrong order to find out."""
    with pytest.raises(KeyError, match="nothing may be assumed in the code"):
        search("rural", Target(), over={"not.a.figure": (1.0, 2.0)})


def test_every_searchable_figure_is_one_the_settings_file_holds():
    for scenario, knobs in SEARCHABLE.items():
        for key in knobs:
            DEFAULTS.entry(key)


@pytest.mark.slow
def test_a_search_finds_a_real_arrangement_and_writes_it_back(tmp_path):
    """End to end: search, meet, save, and run against what was saved.

    Deliberately on the tunnel, which is the quickest row, and against a
    target the default does not meet, so the search has to actually find
    something rather than shrug.
    """
    found = search(
        "tunnel",
        Target(availability=0.99, hpe_p50_m=1.0),
        over={"tunnel.anchor_spacing_m": (150.0, 120.0)},
    )
    assert found.best is not None
    assert found.best.values["tunnel.anchor_spacing_m"] == 120.0

    write(found.as_option("found", DEFAULTS), where=tmp_path)
    saved = read("found", where=tmp_path)
    assert saved.origin == "yerkon solve"

    tighter = saved.applied_to(DEFAULTS)
    assert (
        len(catalogue(tighter)["tunnel"].scenario.deployment.anchors)
        > len(catalogue(DEFAULTS)["tunnel"].scenario.deployment.anchors)
    )
