"""Ground, structures and roads."""

import math

import pytest

from yerkon.world import (
    BILLBOARD,
    EXISTING_STRUCTURES,
    MAX_HIGHWAY_GRADE,
    ROADSIDE_SIGN,
    TALL_MAST,
    Anchor,
    Road,
    flat_terrain,
    graded_alignment,
    rolling_terrain,
)


def test_an_anchor_sits_on_the_ground_plus_its_structure():
    terrain = flat_terrain(elevation_m=120.0)
    anchor = Anchor("a", (0.0, 0.0), BILLBOARD, terrain)
    assert anchor.position_m[2] == pytest.approx(130.0)


def test_the_structures_that_already_exist_are_all_short():
    """The heart of the siting problem.

    Everything already standing beside a road is under 12 m, and a 10 km
    link needs the two ends to average about 12 m. That is why the
    deployment has to mix in built masts, and why this is pinned.
    """
    for structure in EXISTING_STRUCTURES:
        assert float(structure.height_m.value) <= 12.0
    assert float(TALL_MAST.height_m.value) > 12.0


def test_a_sign_has_no_power_and_a_gantry_does():
    """Drives the operating cost: a structure with mains is cheaper to run."""
    assert not ROADSIDE_SIGN.has_power
    assert BILLBOARD.has_power


def test_a_road_follows_the_ground_when_no_alignment_is_given():
    terrain = rolling_terrain(amplitude_m=30.0, wavelength_m=2000.0, seed=3)
    road = Road(centreline_m=[(0.0, 0.0), (5000.0, 0.0)], terrain=terrain)
    for distance in (0.0, 1234.0, 5000.0):
        x, y, z = road.point_at(distance)
        assert z == pytest.approx(terrain.height_at(x, y))


def test_no_road_in_this_codebase_is_flat():
    """ADR-0004. The previous version pinned every receiver at 1,5 m."""
    terrain = rolling_terrain(amplitude_m=30.0, wavelength_m=2000.0, seed=3)
    line = [(0.0, 0.0), (8000.0, 0.0)]
    road = Road(centreline_m=line, terrain=terrain,
                surface_m=graded_alignment(line, terrain))
    heights = [road.point_at(d)[2] for d in range(0, 8000, 100)]
    assert max(heights) - min(heights) > 10.0


def test_a_graded_alignment_never_exceeds_the_design_grade():
    """A road is cut and filled, not draped over the bare ground.

    Sampling raw terrain gives grades above 10%, which no motorway has.
    """
    terrain = rolling_terrain(amplitude_m=40.0, wavelength_m=3000.0, seed=7)
    line = [(0.0, 0.0), (20000.0, 0.0)]

    raw = Road(centreline_m=line, terrain=terrain)
    graded = Road(centreline_m=line, terrain=terrain,
                  surface_m=graded_alignment(line, terrain))

    raw_worst = max(abs(raw.grade_at(d)) for d in range(0, 19900, 50))
    graded_worst = max(abs(graded.grade_at(d)) for d in range(0, 19900, 50))

    assert raw_worst > MAX_HIGHWAY_GRADE
    assert graded_worst <= MAX_HIGHWAY_GRADE + 1e-9


def test_a_cut_alignment_never_rises_above_the_ground():
    """This one cuts and does not fill, and the docstring says so."""
    terrain = rolling_terrain(amplitude_m=40.0, wavelength_m=3000.0, seed=7)
    line = [(0.0, 0.0), (20000.0, 0.0)]
    road = Road(centreline_m=line, terrain=terrain,
                surface_m=graded_alignment(line, terrain))
    for distance in range(0, 20000, 250):
        x, y = road._ground_point(float(distance))
        assert road.surface_height_at(float(distance)) <= terrain.height_at(x, y) + 1e-6


def test_an_offset_moves_across_the_road_not_along_it():
    terrain = flat_terrain()
    road = Road(centreline_m=[(0.0, 0.0), (1000.0, 0.0)], terrain=terrain)
    centre = road.point_at(500.0)
    edge = road.point_at(500.0, offset_m=12.0)
    assert edge[0] == pytest.approx(centre[0])
    assert abs(edge[1] - centre[1]) == pytest.approx(12.0)


# --- Obstruction ----------------------------------------------------------


def test_flat_ground_between_two_masts_obstructs_nothing():
    terrain = flat_terrain()
    a = Anchor("a", (0.0, 0.0), TALL_MAST, terrain).position_m
    b = Anchor("b", (5000.0, 0.0), TALL_MAST, terrain).position_m
    obstruction = terrain.obstruction_between(a, b)
    assert obstruction.peak_terrain_m == pytest.approx(0.0)


def test_the_worst_point_is_measured_against_the_zone_width_there():
    """A hill beside the transmitter blocks less than a rise at the middle.

    Both features below leave a gap of the same order, and the raw gap is
    smaller at the near hill. But the Fresnel zone is about 2 m wide there
    and 17 m wide at the midpoint, so it is the midpoint rise that
    threatens the link. Picking by raw gap reports the wrong obstacle and
    would call a clear path blocked.
    """
    def elevation(x, y):
        if x < 300.0:
            return 100.0          # tall, but right under the transmitter
        if 4500.0 < x < 5500.0:
            return 40.0           # lower, but where the zone is widest
        return 0.0

    from yerkon.world import Terrain

    terrain = Terrain(elevation_m=elevation, description="test")
    a = (0.0, 0.0, 160.0)
    b = (10000.0, 0.0, 60.0)
    obstruction = terrain.obstruction_between(a, b, samples=200)
    assert 0.4 < obstruction.peak_at_fraction < 0.6
    assert obstruction.peak_terrain_m == pytest.approx(40.0)


def test_clutter_accumulates_with_distance():
    terrain = flat_terrain(clutter_loss_db_per_km=2.0)
    near = terrain.obstruction_between((0.0, 0.0, 20.0), (1000.0, 0.0, 2.0))
    far = terrain.obstruction_between((0.0, 0.0, 20.0), (5000.0, 0.0, 2.0))
    # Slant range, so a little over the ground distance.
    assert near.clutter_loss_db == pytest.approx(2.0, abs=0.01)
    assert far.clutter_loss_db == pytest.approx(10.0, abs=0.01)


def test_terrain_cannot_add_signal():
    with pytest.raises(ValueError):
        flat_terrain(clutter_loss_db_per_km=-1.0)
