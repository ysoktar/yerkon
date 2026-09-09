"""Placing anchors for a target accuracy at the lowest cost."""

import math

import numpy as np
import pytest

from yerkon.evaluate import Journey, Receiver
from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280
from yerkon.siting import (
    TYPICAL_ROADSIDE,
    Availability,
    Requirement,
    cheapest,
)
from yerkon.world import (
    LIGHTING_COLUMN,
    ROADSIDE_SIGN,
    Road,
    TALL_MAST,
    graded_alignment,
    rolling_terrain,
)

pytestmark = pytest.mark.slow

TERRAIN = rolling_terrain(amplitude_m=40.0, wavelength_m=3000.0, micro_roughness_m=0.2)
CORRIDOR_M = 8000.0


def a_unit():
    centreline = [(float(x), 0.0) for x in np.arange(0.0, CORRIDOR_M + 1.0, 500.0)]
    road = Road(
        centreline_m=centreline, terrain=TERRAIN,
        surface_m=graded_alignment(centreline, TERRAIN),
    )
    return (
        Receiver(
            "araç",
            Journey(road=road, speed_m_s=27.8, duration_s=200.0),
            radios=(SX1280, DWM3000),
        ),
    )


def search(**kwargs):
    fields = dict(
        terrain=TERRAIN, corridor_m=CORRIDOR_M, receivers=a_unit(),
        radio=E28_2G4M27S, measure_area=False,
    )
    fields.update(kwargs)
    return cheapest(**fields)


# --- What has to be met ---------------------------------------------------


def test_a_position_needs_four_ranges():
    with pytest.raises(ValueError, match="fewer than four"):
        Requirement(anchors_required=3)


def test_coverage_is_a_share_of_the_corridor():
    with pytest.raises(ValueError, match="share of the corridor"):
        Requirement(corridor_covered=1.5)


# --- What already stands there --------------------------------------------


def test_a_structure_that_stands_nowhere_can_be_built_anywhere():
    """A mast has no positions of its own and can go wherever it is wanted."""
    nowhere = Availability(TALL_MAST, every_m=math.inf)
    assert nowhere.positions(10_000.0) == []


def test_a_structure_only_stands_where_it_stands():
    columns = Availability(LIGHTING_COLUMN, every_m=60.0, from_m=0.0, to_m=600.0)
    positions = columns.positions(10_000.0)
    assert positions[0] == 0.0
    assert max(positions) <= 600.0


# --- The search -----------------------------------------------------------


def test_existing_roadside_furniture_beats_building_masts():
    """The finding the whole mixed-mounting strategy rests on.

    A sign is three metres and reaches under two kilometres, against a
    mast's twenty-five and five and a half. It also already exists, and
    costs a thirty-fourth as much to use, which turns out to matter far
    more.
    """
    winner, everything = search()
    assert winner is not None

    masts = [
        c for c in everything
        if c.meets and all(a.mounting is TALL_MAST for a in c.anchors)
    ]
    assert masts, "a mast deployment should be searched for comparison"
    assert winner.costing.capex_tl < masts[0].costing.capex_tl / 3.0


def test_the_cheapest_that_meets_it_is_found_rather_than_the_first_that_works():
    """Denser is dearer and never covers less, so the search runs sparse
    to dense. Running it the other way finds an answer that works and
    costs several times too much."""
    winner, everything = search()
    meeting = [c for c in everything if c.meets]
    assert winner.costing.capex_tl == min(c.costing.capex_tl for c in meeting)


def test_every_candidate_is_a_deployment_somebody_could_build():
    winner, everything = search()
    for candidate in everything:
        assert candidate.anchors
        assert candidate.costing.capex_tl > 0.0
        assert 0.0 <= candidate.corridor_covered <= 1.0


def test_both_ways_of_mixing_are_tried():
    """Cheapest per site and tallest per site pull in opposite directions
    and neither wins in general, so the answer is whichever came out
    cheaper rather than whichever was assumed."""
    _, everything = search()
    labels = " ".join(c.label for c in everything)
    assert "mixed (cheapest)" in labels
    assert "mixed (tallest)" in labels


def test_a_tighter_tolerance_costs_more():
    loose, _ = search(requirement=Requirement(target_sigma_m=8.0))
    tight, _ = search(requirement=Requirement(target_sigma_m=4.0))
    assert loose is not None and tight is not None
    assert tight.costing.capex_tl >= loose.costing.capex_tl


def test_a_tolerance_under_the_radios_own_floor_cannot_be_bought():
    """No amount of money moves it. The SX1280 family measures to about
    three metres however strong the signal, so a two and a half metre
    tolerance is not a siting problem at all."""
    floor_m = float(E28_2G4M27S.implementation_floor_m.value)
    winner, _ = search(
        requirement=Requirement(target_sigma_m=floor_m * 0.85)
    )
    assert winner is None


def test_asking_for_more_of_the_corridor_costs_more():
    some, _ = search(requirement=Requirement(corridor_covered=0.6))
    most, _ = search(requirement=Requirement(corridor_covered=0.98))
    assert some is not None and most is not None
    assert most.costing.capex_tl >= some.costing.capex_tl


def test_a_target_no_structure_can_meet_returns_nothing_rather_than_a_guess():
    """A refusal is an answer. Silently returning the best of a bad set
    would read as a deployment that works."""
    impossible = Requirement(target_sigma_m=0.05)  # far under any floor
    winner, everything = search(requirement=impossible)
    assert winner is None
    assert everything, "the candidates it tried are still reported"
    assert not any(c.meets for c in everything)


def test_a_corridor_with_no_furniture_has_to_build():
    """Where nothing stands, the answer is masts, and it costs what masts
    cost. That is the comparison the roadside answer is measured against."""
    empty = (Availability(TALL_MAST, every_m=math.inf),)
    winner, _ = search(available=empty)
    assert winner is not None
    assert all(anchor.mounting is TALL_MAST for anchor in winner.anchors)


def test_the_winner_is_measured_on_the_real_swept_area():
    """The sweep is the slowest thing in the project, so it runs once, on
    the deployment that won."""
    winner, _ = search(measure_area=True)
    assert winner is not None
    assert winner.served_km2 > 0.0
    assert winner.costing.capex_tl_per_km2 > 0.0


def test_every_anchor_is_priced_as_the_module_inside_it():
    from yerkon.cost import RURAL_ANCHOR, anchor_product

    winner, _ = search(radio=E28_2G4M27S)
    units = next(
        item for item in winner.costing.capital if item.label == "anchor units"
    )
    assert units.tl == pytest.approx(
        len(winner.anchors) * float(RURAL_ANCHOR.unit_price_tl.value)
    )
    assert anchor_product(E28_2G4M27S.part) is RURAL_ANCHOR
