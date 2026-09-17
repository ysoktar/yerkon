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


def test_relief_is_a_trade_rather_than_a_help():
    """Flat ground is not the best case, and relief is not simply better.

    Perfectly level ground returns a clean cancelling ray, so every link
    over it is mediocre and every link over it works. Relief scatters
    that ray and lifts the mast above the reflecting surface, which makes
    the links that survive markedly better — and it drops the receiver
    into dips, where the link does not survive at all.

    Measured across a corridor rather than at one distance, because the
    answer depends on where the receiver is standing and an earlier
    version of this test rested on a lucky one.
    """
    import statistics

    from yerkon.hardware import E28_2G4M27S, SX1280, W24P_U
    from yerkon.rf import Terminal, evaluate_link, ranging_sigma_m

    def sweep(terrain):
        alive = []
        attempted = 0
        for distance_m in range(3000, 10_001, 250):
            attempted += 1
            anchor = Anchor("m", (0.0, 0.0), TALL_MAST, terrain)
            receiver_z = terrain.height_at(float(distance_m), 0.0) + 2.0
            tx = Terminal(E28_2G4M27S, W24P_U, anchor.position_m)
            rx = Terminal(SX1280, W24P_U, (float(distance_m), 0.0, receiver_z))
            obstruction = terrain.obstruction_between(
                tx.position_m, rx.position_m, 200
            )
            budget = evaluate_link(tx, rx, obstruction=obstruction)
            if budget.closes:
                alive.append(ranging_sigma_m(budget, E28_2G4M27S))
        return len(alive) / attempted, (
            statistics.median(alive) if alive else math.inf
        )

    flat_share, flat_sigma = sweep(flat_terrain())
    gentle_share, gentle_sigma = sweep(rolling_terrain(10.0, 2000.0, seed=3))
    rugged_share, rugged_sigma = sweep(rolling_terrain(80.0, 2000.0, seed=11))

    # Level ground blocks nothing but its own curve, and that is not
    # nothing: at ten kilometres a 2 m antenna's first Fresnel zone is
    # into the bulge, and the Recommendation's method charges six
    # decibels for it where a single knife edge over the worst point
    # read half a decibel (ADR-0053). One link of twenty-nine, and it is
    # the farthest.
    assert flat_share >= 28 / 29, flat_share
    assert flat_share < 1.0, (
        "a plane is still a curved plane: if this passes, the curvature "
        "has stopped being counted"
    )
    assert gentle_sigma < flat_sigma, "the links that survive relief are better"
    assert rugged_share < gentle_share / 2.0, "rugged ground closes almost nothing"
    assert rugged_sigma > flat_sigma, "and what it leaves is worse"


def test_gentle_relief_helps_by_aiming_the_cancelling_ray_away():
    """And not by scattering it. ADR-0026.

    A tilted patch is a mirror that works perfectly and points somewhere
    else, so a few metres of undulation can be worth ten decibels — which
    is why the strongest two-ray nulls in the world are over airfields
    and calm water rather than over countryside.

    This used to be asserted the other way round: that gentle relief cost
    some links entirely. It does not, at this scale, and the old model
    only appeared to agree because it counted a slope as roughness and
    got the same weak reflection for the wrong reason.
    """
    from yerkon.hardware import E28_2G4M27S, SX1280, W24P_U
    from yerkon.rf import Terminal, aimed_fraction, evaluate_link

    distance_m = 6000.0

    def loss_over(terrain):
        anchor = Anchor("m", (0.0, 0.0), TALL_MAST, terrain)
        tx = Terminal(E28_2G4M27S, W24P_U, anchor.position_m)
        rx = Terminal(SX1280, W24P_U, (
            distance_m, 0.0, terrain.height_at(distance_m, 0.0) + 2.0))
        obstruction = terrain.obstruction_between(
            tx.position_m, rx.position_m, 200)
        budget = evaluate_link(tx, rx, obstruction=obstruction)
        return budget.path_loss_db, obstruction

    flat_db, flat_ground = loss_over(flat_terrain())
    gentle_db, gentle_ground = loss_over(rolling_terrain(10.0, 2000.0, seed=3))

    assert flat_ground.reflection_tilt_rad == 0.0, "a plane does not tilt"
    assert aimed_fraction(distance_m, flat_ground.reflection_tilt_rad, 2.45e9) == 1.0

    assert abs(gentle_ground.reflection_tilt_rad) > 0.0
    assert aimed_fraction(
        distance_m, gentle_ground.reflection_tilt_rad, 2.45e9) < 0.01

    # The claim is about the reflection, so it is measured on the
    # reflection: with nothing in the way, gentle ground costs ten
    # decibels less than a plane, because the tilted patch aims the
    # cancelling ray past the receiver instead of into it.
    from dataclasses import replace

    def without_anything_in_the_way(terrain, obstruction):
        anchor = Anchor("m", (0.0, 0.0), TALL_MAST, terrain)
        return evaluate_link(
            Terminal(E28_2G4M27S, W24P_U, anchor.position_m),
            Terminal(SX1280, W24P_U, (
                distance_m, 0.0, terrain.height_at(distance_m, 0.0) + 2.0)),
            obstruction=replace(obstruction, profile=(),
                                peak_terrain_m=-1e6),
        ).path_loss_db

    flat_reflection = without_anything_in_the_way(flat_terrain(), flat_ground)
    gentle_reflection = without_anything_in_the_way(
        rolling_terrain(10.0, 2000.0, seed=3), gentle_ground)
    assert gentle_reflection < flat_reflection - 3.0, (
        "the aiming should be worth several decibels: flat {:.1f}, gentle "
        "{:.1f}".format(flat_reflection, gentle_reflection)
    )
    # And it is the aiming that does it, not the roughness: the patch is
    # smooth enough that scattering alone would leave the ray intact.
    assert gentle_ground.surface_roughness_m < 5.0

    # What the hills give back, they also take: those same hills stand in
    # the path. Counted one edge at a time this link came out ahead
    # overall; counted over the whole profile the way ITU-R P.526 counts
    # it, the diffraction costs more than the aiming saves at six
    # kilometres (ADR-0053). Both halves are real and the net is a trade,
    # which is what the test above this one is named for.
    assert gentle_db > flat_db, (
        "flat {:.1f}, gentle {:.1f}".format(flat_db, gentle_db))
    assert gentle_db - gentle_reflection > flat_db - flat_reflection, (
        "the hills that aim the reflection away are the hills in the way"
    )


# --- What the ground model does not carry (ADR-0055) ----------------------


def test_a_shadow_is_a_fact_about_a_place_rather_than_a_draw():
    """The same rule as the ground's own roughness and the survey error
    before it (ADR-0019): a receiver ranging to the same anchor from the
    same spot meets the same shadow every time. Drawn as noise it would
    average away over a round and the whole effect would vanish."""
    from yerkon.world import Shadowing

    field = Shadowing(sigma_db=6.0, correlation_m=50.0)
    once = field.between((0.0, 0.0), (317.0, 211.0))
    assert once == field.between((0.0, 0.0), (317.0, 211.0))
    assert once != 0.0


def test_the_spread_is_the_figure_it_was_given():
    """Interpolating between four independent corners narrows the spread
    unless it is renormalised — and narrows it by a different amount in
    the middle of a cell than at its corner, which would make the width
    a function of where you stood."""
    import statistics

    from yerkon.world import Shadowing

    field = Shadowing(sigma_db=6.0, correlation_m=50.0)
    corners = [field.between((0.0, 0.0), (x * 50.0, y * 50.0))
               for x in range(50) for y in range(50)]
    middles = [field.between((0.0, 0.0), (x * 50.0 + 25.0, y * 50.0 + 25.0))
               for x in range(50) for y in range(50)]
    assert statistics.pstdev(corners) == pytest.approx(6.0, abs=0.4)
    assert statistics.pstdev(middles) == pytest.approx(6.0, abs=0.4)
    assert abs(statistics.mean(corners)) < 0.6


def test_a_shadow_lasts_as_far_as_it_is_told_to():
    """A step is not an independent draw, or it would average away over
    a round. Gudmundson's measurements put it at tens of metres."""
    from yerkon.world import Shadowing

    import statistics

    field = Shadowing(sigma_db=6.0, correlation_m=50.0)
    walk = [field.between((0.0, 0.0), (x * 5.0, 0.0)) for x in range(3000)]

    def alike(step):
        """How much two points that far apart agree, from -1 to 1."""
        first, second = walk[:-step], walk[step:]
        return statistics.correlation(first, second)

    # Measured over a walk rather than asserted on one pair: two
    # independent draws agree by chance often enough that a single
    # comparison tests nothing.
    assert alike(1) > 0.9, "five metres is the same shadow"
    assert 0.6 < alike(5) < 0.9, "twenty-five is halfway to another"
    assert 0.15 < alike(10) < 0.45, (
        "fifty — the figure it was given — is most of the way there")
    assert abs(alike(20)) < 0.15, "a hundred is another shadow"
    assert abs(alike(200)) < 0.15, "and so is a kilometre"


def test_two_anchors_at_one_spot_are_shadowed_separately():
    """The case that costs a fix: standing still, some anchors are
    behind something and others are not. One field over the site would
    shadow them together and never produce it."""
    from yerkon.world import Shadowing

    field = Shadowing(sigma_db=6.0, correlation_m=50.0)
    where = (700.0, 300.0)
    assert (field.between((0.0, 0.0), where)
            != field.between((4000.0, 0.0), where))


def test_another_arrangement_of_shadows_is_another_answer():
    from yerkon.world import Shadowing

    where = (700.0, 300.0)
    first = Shadowing(sigma_db=6.0, correlation_m=50.0, seed=1)
    second = Shadowing(sigma_db=6.0, correlation_m=50.0, seed=2)
    assert first.between((0.0, 0.0), where) != second.between((0.0, 0.0), where)


def test_no_spread_is_no_shadow():
    from yerkon.world import Shadowing

    assert Shadowing(sigma_db=0.0).between((0.0, 0.0), (500.0, 0.0)) == 0.0
    with pytest.raises(ValueError, match="magnitude"):
        Shadowing(sigma_db=-1.0)
    with pytest.raises(ValueError, match="a shadow has a size"):
        Shadowing(sigma_db=6.0, correlation_m=0.0)


def test_the_ground_hands_the_shadow_to_the_link_budget():
    """Through the obstruction, beside the clutter it sits next to: the
    terrain knows both ends of the path and the budget assembles the
    decibels."""
    from dataclasses import replace

    from yerkon.rf import Terminal, evaluate_link
    from yerkon.hardware import E28_2G4M27S, W24P_U
    from yerkon.world import Shadowing, rolling_terrain

    plain = rolling_terrain(40.0, 3000.0)
    shadowed = replace(plain, shadowing=Shadowing(sigma_db=6.0))
    here, there = (0.0, 0.0, 25.0), (900.0, 0.0, 2.0)

    assert plain.obstruction_between(here, there).shadow_db == 0.0
    said = shadowed.obstruction_between(here, there).shadow_db
    assert said != 0.0

    tx, rx = Terminal(E28_2G4M27S, W24P_U, here), Terminal(E28_2G4M27S, W24P_U, there)
    with_it = evaluate_link(tx, rx, obstruction=shadowed.obstruction_between(here, there))
    without = evaluate_link(tx, rx, obstruction=plain.obstruction_between(here, there))
    assert with_it.path_loss_db == pytest.approx(without.path_loss_db + said)
