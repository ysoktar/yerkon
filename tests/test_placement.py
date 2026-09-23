"""Placing anchors on places that are already high (ADR-0081)."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from yerkon import placement as P
from yerkon.cost import DEFAULT_RATES
from yerkon.settings import hurried
from yerkon.world import flat_terrain, mountings, Anchor

TERRAIN = flat_terrain()
COLUMN = mountings()["lighting_column"]


def _candidate(x, y, cost, origin="road"):
    return P.Candidate(Anchor("X", (x, y), COLUMN, TERRAIN), origin, cost)


def _problem(candidates, cells, reach, grid=()):
    cells = np.asarray(cells, dtype=float)
    return P.Problem(tuple(candidates), cells, np.asarray(reach, dtype=bool),
                     tuple(grid), P.quarters(candidates, cells))


# --- What counts as served ------------------------------------------------


def test_four_anchors_in_one_quarter_do_not_serve_a_cell():
    """Four ranges that all run the same way leave the other axis unmeasured.

    The first version counted anchors only, and the simulation put its
    ninety-fifth percentile far above the grid's.
    """
    east = [_candidate(100.0 + 10 * k, 5.0 * k, 1.0) for k in range(4)]
    p = _problem(east, [(0.0, 0.0)], [[True]] * 4)
    assert p.share(range(4)) == 0.0


def test_four_anchors_in_three_quarters_serve_it():
    around = [_candidate(100.0, 0.0, 1.0), _candidate(0.0, 100.0, 1.0),
              _candidate(-100.0, 0.0, 1.0), _candidate(110.0, 5.0, 1.0)]
    p = _problem(around, [(0.0, 0.0)], [[True]] * 4)
    assert p.share(range(4)) == 1.0
    assert p.share(range(3)) == 0.0


# --- The choice -----------------------------------------------------------


def _ring(cost_of, n=8):
    """Anchors on a circle round one cell, each costing what it is told."""
    out = []
    for k in range(n):
        angle = 2 * np.pi * k / n
        out.append(_candidate(100 * np.cos(angle), 100 * np.sin(angle),
                              cost_of(k)))
    return out


def test_the_cheapest_cover_takes_the_cheaper_of_two_equal_places():
    """Two rings reach the same cell; one costs a tenth of the other."""
    dear = _ring(lambda k: 10.0)
    cheap = _ring(lambda k: 1.0)
    p = _problem(dear + cheap, [(0.0, 0.0)], [[True]] * 16,
                 grid=range(8))
    chosen = P.cheapest_cover(p, p.share(p.grid))
    assert p.share(chosen) >= p.share(p.grid)
    assert p.cost(chosen) == pytest.approx(4.0)
    assert all(i >= 8 for i in chosen)


def test_the_search_finds_the_exhaustive_optimum_on_a_small_problem():
    """Two cells, nine candidates, every one of the 512 subsets tried.

    Greedy on its own takes the dear anchor that reaches both cells
    first, because it closes the most per lira at that moment. Drop and
    interchange have to find the cheaper set.
    """
    from itertools import combinations

    cells = [(0.0, 0.0), (1000.0, 0.0)]
    left = [_candidate(-100, 0, 1.0), _candidate(0, 100, 1.0),
            _candidate(0, -100, 1.0)]
    right = [_candidate(1100, 0, 1.0), _candidate(1000, 100, 1.0),
             _candidate(1000, -100, 1.0)]
    dear = [_candidate(500, 0, 1.5)]
    cheap = [_candidate(100, 0, 0.5), _candidate(900, 0, 0.5)]
    everything = left + right + dear + cheap
    reach = ([[True, False]] * 3 + [[False, True]] * 3 + [[True, True]]
             + [[True, False], [False, True]])
    p = _problem(everything, cells, reach)

    best = min(
        p.cost(subset)
        for size in range(len(everything) + 1)
        for subset in combinations(range(len(everything)), size)
        if p.share(subset) == 1.0
    )
    chosen = P.cheapest_cover(p, 1.0)
    assert p.share(chosen) == 1.0
    assert p.cost(chosen) == pytest.approx(best)


def test_drop_and_interchange_turn_a_wasteful_start_into_the_cheapest():
    """Eight dear anchors round a cell, where four cheap ones would do.

    Drop removes the four the cell does not need; interchange swaps the
    rest for the cheap ring. Called directly, because on small problems
    greedy often lands on the optimum and would hide a broken step.
    """
    dear = _ring(lambda k: 10.0)
    cheap = _ring(lambda k: 1.0)
    p = _problem(dear + cheap, [(0.0, 0.0)], [[True]] * 16)
    costs = np.array([c.lifecycle_tl for c in p.candidates])
    improved = P._cheapen(p, list(range(8)), 1.0, costs)
    assert p.share(improved) == 1.0
    assert p.cost(improved) == pytest.approx(4.0)


def test_the_best_within_a_budget_never_spends_more_than_it():
    p = _problem(_ring(lambda k: 1.0 + k), [(0.0, 0.0)], [[True]] * 8,
                 grid=range(4))
    budget = p.cost(p.grid)
    chosen = P.best_within(p, budget)
    assert p.cost(chosen) <= budget + 1e-9
    assert p.share(chosen) >= p.share(p.grid)


# --- Cost -----------------------------------------------------------------


def test_the_lifecycle_cost_comes_from_the_cost_model():
    """A lira of yearly rent is a service life of lira over the life.

    Priced through `cost.price` so a rate edit reaches the search the way
    it reaches the table.
    """
    roof = mountings()["rooftop"]
    part = "Semtech SX1280 (EBYTE E28-2G4M12S)"
    base = P.lifecycle_tl(roof, part, DEFAULT_RATES)
    dearer = replace(roof, rent_tl_per_year=replace(
        roof.rent_tl_per_year, value=float(roof.rent_tl_per_year.value) + 100))
    life = float(DEFAULT_RATES.service_life_years.value)
    assert P.lifecycle_tl(dearer, part, DEFAULT_RATES) - base == \
        pytest.approx(100 * life)


# --- Candidates -----------------------------------------------------------


def test_a_roof_at_the_default_height_is_not_a_candidate():
    """A roof whose height nobody measured is not already high.

    Over Polatlı every building but twelve carries the fetch's default.
    """
    from yerkon.scenarios import catalogue
    from yerkon.site.fetch import DEFAULT_BUILDING_HEIGHT_M

    deployed = catalogue(hurried())["urban"]
    buildings = SimpleNamespace(
        is_empty=False,
        centre_x_m=np.array([500.0, 1000.0]),
        centre_y_m=np.array([500.0, 1000.0]),
        height_m=np.array([30.0, DEFAULT_BUILDING_HEIGHT_M + 20.0]),
        tallest_at=lambda x, y: 0.0,
    )
    site = SimpleNamespace(
        furniture=None, buildings=buildings, roads_m=(),
        elevation_grid_m=np.zeros((4, 4)), grid_spacing_m=1000.0,
        height_at=lambda x, y: 0.0,
    )
    found, _ = P.candidates(deployed, site, "urban")
    roofs = [c for c in found if c.origin == "rooftop"]
    assert len(roofs) == 2

    site.buildings = SimpleNamespace(
        **{**vars(buildings),
           "height_m": np.array([30.0, DEFAULT_BUILDING_HEIGHT_M])})
    found, _ = P.candidates(deployed, site, "urban")
    assert len([c for c in found if c.origin == "rooftop"]) == 1


def test_a_street_structure_inside_a_building_is_not_a_candidate():
    """Inside a footprint the ground is the roof (ADR-0038).

    A column there would be handed the building's height for nothing.
    """
    from yerkon.scenarios import catalogue

    deployed = catalogue(hurried())["urban"]
    block = (1000.0, 1000.0, 100.0)  # centre x, centre y, radius

    def tallest_at(x, y):
        return 20.0 if np.hypot(x - block[0], y - block[1]) <= block[2] else 0.0

    site = SimpleNamespace(
        furniture=None, roads_m=([(800.0, 1000.0), (1200.0, 1000.0)],),
        buildings=SimpleNamespace(
            is_empty=False, centre_x_m=np.array([]), centre_y_m=np.array([]),
            height_m=np.array([]), tallest_at=tallest_at),
        elevation_grid_m=np.zeros((4, 4)), grid_spacing_m=1000.0,
        height_at=lambda x, y: 0.0,
    )
    found, _ = P.candidates(deployed, site, "urban")
    road = [c.anchor.ground_position_m for c in found if c.origin == "road"]
    assert road
    assert all(tallest_at(x, y) == 0.0 for x, y in road)


def test_the_grid_is_always_among_the_candidates():
    """So the search can never do worse than the layout it replaces."""
    from yerkon.scenarios import catalogue, fetched

    settings = hurried()
    deployed = catalogue(settings)["urban"]
    found, grid = P.candidates(deployed, fetched("kizilay"), "urban",
                               settings)
    assert len(grid) == len(deployed.scenario.deployment.anchors)
    assert [found[i].anchor.ground_position_m for i in grid] == [
        a.ground_position_m for a in deployed.scenario.deployment.anchors]
    kinds = {c.origin for c in found}
    assert {"furniture", "rooftop", "hilltop", "road"} <= kinds


def test_the_reach_matrix_uses_the_link_budget_not_a_disc():
    """Over Kızılay a column reaches some cells and not others at one range.

    A disc would give every cell at the same distance the same answer.
    Buildings do not.
    """
    from yerkon.scenarios import catalogue, fetched

    settings = hurried()
    deployed = catalogue(settings)["urban"]
    site = fetched("kizilay")
    found, grid = P.candidates(deployed, site, "urban", settings)
    # The grid anchor nearest the middle, so the ring stays on the site.
    anchor = min((found[i].anchor for i in grid), key=lambda a: np.hypot(
        a.ground_position_m[0] - 1400, a.ground_position_m[1] - 1400))
    ax, ay = anchor.ground_position_m
    ring = np.array([(ax + 400 * np.cos(a), ay + 400 * np.sin(a))
                     for a in np.linspace(0, 2 * np.pi, 24, endpoint=False)])
    rows = P._reach_rows(((anchor,), deployed.scenario.deployment,
                          deployed.scenario.terrain, ring, 1500.0))
    assert 0 < rows.sum() < len(ring)


# --- Handing the answer over ----------------------------------------------


def test_a_placed_run_puts_every_anchor_where_the_search_said():
    from yerkon.viewer.state import from_scenario
    from yerkon.viewer.tasks import placed_run

    state = from_scenario("urban")
    catalogue = mountings(state.settings())
    chosen_places = [
        P.Candidate(Anchor("a", (400.0, 700.0), catalogue["rooftop"],
                           TERRAIN), "rooftop", 1.0),
        P.Candidate(Anchor("b", (900.0, 1200.0), catalogue["roadside_sign"],
                           TERRAIN), "furniture", 1.0),
    ]
    answer = SimpleNamespace(
        problem=SimpleNamespace(candidates=chosen_places), chosen=(0, 1))
    changes = placed_run(state, answer)
    placed = state.merged(changes)
    anchors = placed.placed(placed.terrain())
    at = sorted((a.ground_position_m, a.mounting.kind) for _, a in anchors)
    assert at == [((400.0, 700.0), "rooftop"),
                  ((900.0, 1200.0), "roadside sign")]


def test_a_roof_is_not_offered_for_a_whole_run():
    """A lattice of roofs would put brackets on bare ground."""
    from yerkon.viewer.scene import scene
    from yerkon.viewer.state import from_scenario

    offered = [key for key, _ in scene(from_scenario("urban"))["choices"]
               ["mountings"]]
    assert "roof" not in offered
    assert "column" in offered
