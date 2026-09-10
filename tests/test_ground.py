"""Real Ankara ground, and the rule that nothing here stands on a plane."""

import math

import pytest

from yerkon.scenarios import (
    CHOICES,
    catalogue,
    HARD_RURAL_SITE,
    RURAL_SITE,
    SITES,
    TUNNEL_BORE,
    TUNNEL_SITE,
    URBAN_SITE,
    fetched,
    rural_ground,
    tunnel_ground,
    urban_ground,
)
from yerkon.settings import DEFAULTS
from yerkon.world import bore_terrain, flat_terrain


# --- What ships -----------------------------------------------------------


@pytest.mark.parametrize(
    "name", [URBAN_SITE, RURAL_SITE, HARD_RURAL_SITE, TUNNEL_SITE]
)
def test_the_ground_each_row_stands_on_ships_with_the_package(name):
    """ADR-0008, finally taken at its word.

    A cache directory is a self-contained artefact, so a clone reproduces
    every number in the table with no network. A megabyte of Copernicus
    grid is a small price for that.
    """
    site = fetched(name)
    assert site is not None, "{} was never fetched into {}".format(name, SITES)
    assert site.manifest.elevation_source
    assert site.manifest.fetched_at
    assert site.relief_m > 0.0


def test_the_fetched_ground_covers_the_scenario_that_stands_on_it():
    """A grid smaller than its scenario silently clamps at the edge.

    Which would put a row of anchors on the last known contour and look
    like terrain rather than like the artefact it is.
    """
    for name, extent_m in ((URBAN_SITE, 2900.0), (RURAL_SITE, 19_800.0)):
        site = fetched(name)
        assert site.width_m >= extent_m, name
        assert site.height_m >= extent_m, name


# --- Nowhere is flat ------------------------------------------------------


def _spread_of(terrain, extent_m, samples=9):
    step = extent_m / (samples - 1)
    heights = [
        terrain.height_at(i * step, j * step)
        for i in range(samples)
        for j in range(samples)
    ]
    return max(heights) - min(heights)


@pytest.mark.parametrize("name", sorted(CHOICES))
def test_no_scenario_stands_on_a_level_surface(name):
    """ADR-0021. A plane is the most favourable ground this model can draw.

    Every reflection off it arrives at exactly the specular angle the
    two-ray term assumes, nothing can obstruct anything, and every
    terminal sits at one height. It looks like the assumption-free choice
    and it is the opposite of one.
    """
    deployed = CHOICES[name]
    extent = max(
        max(a.ground_position_m[0] for a in deployed.scenario.deployment.anchors),
        1.0,
    )
    assert _spread_of(deployed.scenario.terrain, extent) > 1.0
    assert "flat" not in deployed.scenario.terrain.description


def test_the_modelled_fallback_is_not_flat_either():
    """The place a run lands when nobody has fetched anything.

    If the fallback were a plane, a machine with no network would be
    running a different and friendlier study than one with a cache, and
    nothing would say so.
    """
    for terrain, extent in (
        (urban_ground(DEFAULTS, 30.0), 3000.0),
        (rural_ground(DEFAULTS), 20_000.0),
        (tunnel_ground(DEFAULTS, 2000.0, site_name=""), 2000.0),
    ):
        assert "flat" not in terrain.description
        assert _spread_of(terrain, extent) > 1.0


def test_the_relief_the_fallback_uses_was_measured_not_guessed():
    """ADR-0016 and ADR-0021 together.

    The fallback exists so a run without a cache is still not a plane.
    That is only worth anything if its shape came from the real grids
    rather than from somebody's idea of a landscape.
    """
    for key in ("site.urban_relief_m", "site.rural_relief_m", "site.tunnel_grade"):
        entry = DEFAULTS.entry(key)
        assert not entry.is_assumed, key
        assert "Copernicus" in entry.sourced.source, key


# --- The bore -------------------------------------------------------------


def test_the_bore_goes_through_the_mountain_rather_than_over_it():
    """A tunnel cannot be built by draping a road over terrain.

    Its floor is a straight line between two portals, and the mountain
    is above it the whole way. Sampling the surface instead would give a
    road that climbs a hill nobody drives over.
    """
    site = fetched(TUNNEL_SITE)
    (entry_x, entry_y), (exit_x, _) = TUNNEL_BORE
    length = exit_x - entry_x
    bore = tunnel_ground(DEFAULTS, length)

    cover = [
        site.height_at(entry_x + f * length, entry_y) - bore.height_at(f * length, 0.0)
        for f in [i / 40.0 for i in range(2, 39)]
    ]
    assert min(cover) > 0.0, "the bore surfaces partway along; that is a cutting"
    assert max(cover) > 50.0, "no mountain above it; that is not a tunnel"


def test_the_bore_falls_at_a_gradient_a_road_tunnel_is_built_to():
    """Between half a percent and three, for drainage.

    A level floor is not a simplification of a tunnel. It is a tunnel no
    highway authority would accept, and it puts every anchor and every
    receiver at one height, which is the arrangement least able to say
    anything about the vertical.
    """
    bore = CHOICES["tunnel"].scenario.terrain
    fall = abs(bore.height_at(2000.0, 0.0) - bore.height_at(0.0, 0.0))
    assert 0.004 <= fall / 2000.0 <= 0.030


def test_the_bore_is_straight():
    bore = bore_terrain(1168.5, 1132.7, 2000.0)
    assert bore.height_at(1000.0, 0.0) == pytest.approx(1150.6)
    # And it is a plane, so the cross-section is level whatever y is.
    assert bore.height_at(500.0, -6.0) == bore.height_at(500.0, 6.0)


def test_a_bore_of_no_length_is_refused():
    with pytest.raises(ValueError, match="a bore has a length"):
        bore_terrain(100.0, 90.0, 0.0)


# --- The instrument that is left ------------------------------------------


def test_flat_terrain_survives_as_a_test_instrument_and_says_so():
    """It is still the right tool for isolating one variable.

    What it is not is a description of anywhere, and its docstring is
    where that has to be said, because nothing else in the codebase
    reaches it any more.
    """
    assert flat_terrain(elevation_m=900.0).height_at(1e6, -1e6) == 900.0
    assert "laboratory" in flat_terrain.__doc__


# --- What a round is sized by ---------------------------------------------


def test_no_rural_link_fails_for_distance():
    """ADR-0022. Every rural failure is ground in the way, not range.

    The two look identical in the availability column and have opposite
    remedies: more masts fix distance, and nothing about spacing fixes a
    ridge. If this ever stops holding, the rural row's whole cost
    argument changes and somebody should have to notice.
    """
    import numpy as np

    from yerkon.rf import Terminal, evaluate_link

    deployed = CHOICES["rural"]
    deployment = deployed.scenario.deployment
    terrain = deployed.scenario.terrain
    unit = deployment.receivers[0]

    closed = blocked = out_of_range = 0
    for at_s in np.linspace(0.0, unit.journey.duration_s - 1.0, 40):
        here = unit.journey.position_at(float(at_s))
        for _, anchor, radio in deployment.nearest_to(unit, here):
            receiver = Terminal(radio, deployment.antenna, here)
            over_ground = evaluate_link(
                anchor, receiver,
                obstruction=terrain.obstruction_between(
                    anchor.position_m, receiver.position_m
                ),
                region=deployment.region,
            )
            if over_ground.closes:
                closed += 1
            elif evaluate_link(
                anchor, receiver, obstruction=None, region=deployment.region
            ).closes:
                blocked += 1
            else:
                out_of_range += 1

    assert closed and blocked, "this sample shows neither outcome"
    assert out_of_range == 0, (
        "{} rural links failed for distance; the row's remedy is no longer "
        "line of sight".format(out_of_range)
    )


def test_the_rural_round_polls_more_anchors_than_a_fix_needs():
    """ADR-0022. Eight attempts over blocked ground yield four replies.

    Which is exactly what a cold fix needs and nothing spare, and it is
    why the rural row sat in the low eighties. A round is sized by how
    many anchors answer, not by how many a position needs — and those are
    the same number only over ground that hides nothing.
    """
    rural = CHOICES["rural"].scenario.deployment
    assert rural.max_anchors_per_round >= 12

    # The other two rows poll almost nothing that fails, so a longer
    # round would buy them nothing and cost update rate.
    for name in ("urban", "tunnel"):
        assert CHOICES[name].scenario.deployment.max_anchors_per_round == 8


@pytest.mark.slow
def test_a_longer_rural_round_buys_availability_on_every_seed():
    """The check the neighbour list failed, applied to what replaced it.

    A change measured on one seed is a change measured on nothing: the
    ordering trick this replaced gave +2,57 points on the first seed it
    was tried on and −1,24 on the third. This one is positive on all of
    them, and the test says so rather than trusting the run that
    happened to be shipped.
    """
    from dataclasses import replace

    from yerkon.evaluate import run_scenario

    base = CHOICES["rural"].scenario
    for seed in (202, 404):
        longer = replace(base, seed=seed)
        shorter = replace(
            longer,
            deployment=replace(longer.deployment, max_anchors_per_round=8),
        )
        assert (
            run_scenario(longer).availability
            > run_scenario(shorter).availability
        ), seed


# --- The figures reaching both ends of a link -----------------------------


def test_editing_a_radio_figure_reaches_the_receiver_and_not_only_the_anchor():
    """The link budget takes its noise figure from the *receiving* terminal.

    So a unit built from the shipped part made every edit to a radio
    figure invisible to link closure: the anchors moved and the thing
    deciding whether the packet arrived did not. `--defaults` and the
    viewer's own sliders both went through this, silently doing nothing.
    """
    from yerkon.settings import DEFAULTS

    noisier = DEFAULTS.with_values({"radio.sx1280.noise_figure_db": 14.0})
    deployment = CHOICES["urban"].scenario.deployment
    edited = catalogue(noisier)["urban"].scenario.deployment

    assert float(deployment.receivers[0].radios[0].noise_figure_db.value) == 6.0
    assert float(edited.receivers[0].radios[0].noise_figure_db.value) == 14.0
    assert float(edited.anchors[0].radio.noise_figure_db.value) == 14.0


@pytest.mark.parametrize("name", ["urban", "rural", "tunnel"])
def test_every_unit_carries_the_modules_this_run_built(name):
    """Not the module-level ones. Checked per row, because it was one
    scenario's units that were wired correctly and two that were not."""
    from yerkon.settings import DEFAULTS

    quieter = DEFAULTS.with_values({"radio.dwm3000.noise_figure_db": 3.0})
    for unit in catalogue(quieter)[name].scenario.deployment.receivers:
        impulse = [
            radio for radio in unit.radios if "DWM" in radio.part.upper()
        ]
        assert impulse, "{} carries no impulse module".format(unit.identifier)
        assert float(impulse[0].noise_figure_db.value) == 3.0


# --- What the reflecting patch is, and whether it points at you -----------


def test_a_slope_is_not_roughness():
    """ADR-0026. Roughness means deviation from the surface, and a hill
    is a surface.

    Measured about a window's mean height instead, a 12 % grade reads as
    2,8 m of scatter where the ground is smooth to 7 cm — a factor of
    forty, and enough to switch the coherent reflection off everywhere
    that is not level. The model then got roughly the right answer for
    entirely the wrong reason.
    """
    from yerkon.world import _plane_through

    tilted = tuple((i / 20.0, 100.0 + 40.0 * (i / 20.0)) for i in range(21))
    roughness, slope = _plane_through(tilted)

    assert roughness == pytest.approx(0.0, abs=1e-9), "a plane is not rough"
    assert slope == pytest.approx(40.0)

    # And real scatter is still measured, on top of any slope.
    lumpy = tuple(
        (f, h + (0.5 if index % 2 else -0.5))
        for index, (f, h) in enumerate(tilted)
    )
    # Not exact: an odd number of alternating samples leaves a whisker
    # of slope, which the fit correctly takes out along with the ramp.
    assert _plane_through(lumpy)[0] == pytest.approx(0.5, rel=0.01)


def test_a_tilted_patch_aims_the_reflection_away_rather_than_scattering_it():
    """Different physics, same symptom, and they must not be conflated.

    Rough ground scatters the ray in all directions. Tilted ground is a
    mirror that works perfectly and points somewhere else. Only the
    second depends on how far the ray still has to travel.
    """
    import math

    from yerkon.rf import aimed_fraction

    assert aimed_fraction(1000.0, 0.0, 2.45e9) == 1.0

    tilted = math.radians(2.0)
    # It matters where along the path the reflection lands: a mast
    # talking to a vehicle puts it near the vehicle, where the swung ray
    # has little room to drift off.
    near_the_middle = aimed_fraction(400.0, tilted, 2.45e9, 0.5)
    near_the_receiver = aimed_fraction(400.0, tilted, 2.45e9, 0.93)
    assert near_the_receiver > near_the_middle * 10.0


def test_the_bore_keeps_its_reflection_and_open_ground_does_not():
    """ADR-0026, and the reason the tunnel row behaves unlike the others.

    A bore really is a plane, so its reflection arrives and the two-ray
    cancellation is real there. Outdoors the reflecting patch is tilted a
    degree or two and the ray misses, which is why textbook two-ray nulls
    turn up over airfields and calm water rather than over countryside.
    """
    import math

    import numpy as np

    from yerkon.rf import aimed_fraction

    def aimed_over(name, samples=12):
        deployed = CHOICES[name]
        deployment = deployed.scenario.deployment
        terrain = deployed.scenario.terrain
        unit = deployment.receivers[0]
        got = []
        for at_s in np.linspace(0.0, unit.journey.duration_s - 1.0, samples):
            here = unit.journey.position_at(float(at_s))
            for _, anchor, _ in deployment.nearest_to(unit, here)[:3]:
                span = math.dist(anchor.position_m, here)
                if span < 20.0:
                    continue
                found = terrain.obstruction_between(anchor.position_m, here)
                got.append(aimed_fraction(
                    span, found.reflection_tilt_rad, 2.45e9,
                    found.reflection_at_fraction,
                ))
        return float(np.median(got))

    assert aimed_over("tunnel") > 0.5, "a bore is a mirror pointed at you"
    assert aimed_over("rural") < 0.1, "a hillside is a mirror pointed elsewhere"


# --- Ground that is not the same everywhere -------------------------------


def test_a_patch_is_rough_as_a_fact_about_that_place():
    """ADR-0026, and ADR-0019 before it.

    A receiver ranging to the same anchor from the same spot meets the
    same ground every time. Drawn as noise it would average out over a
    round; drawn from the position it does not, which is what makes it
    worth modelling at all.
    """
    from yerkon.world import patchwork

    ground = patchwork(typical_m=0.3, patch_m=200.0, spread=0.8, seed=5)
    assert ground(1234.0, -56.0) == ground(1234.0, -56.0)
    assert ground(1234.0, -56.0) != ground(9876.0, 543.0)

    # And it is the same ground in another process, which a salted
    # `hash()` would not have been once the work was spread (ADR-0025).
    from yerkon.parallel import spread as run_over

    here = ground(1234.0, -56.0)
    assert run_over(_ask_patch, [(ground, 1234.0, -56.0)] * 2) == (here, here)


def _ask_patch(task):
    ground, x, y = task
    return ground(x, y)


def test_a_patchwork_leaves_the_site_roughness_meaning_what_it_measured():
    """Only the variation is added, not a different average.

    The multipliers are centred on mean square rather than mean, because
    roughness enters the reflection through its square. A patchwork that
    quietly raised the average would be a different site, not the same
    site described better.
    """
    import statistics

    from yerkon.world import patchwork

    typical = 0.4
    ground = patchwork(typical_m=typical, patch_m=150.0, spread=0.9, seed=11)
    sampled = [ground(x * 7.0, x * 3.0) for x in range(4000)]
    root_mean_square = (sum(v * v for v in sampled) / len(sampled)) ** 0.5

    assert root_mean_square == pytest.approx(typical, rel=0.12)
    assert min(sampled) < typical / 2.0, "nothing varies"
    assert max(sampled) > typical * 1.5


def test_more_levels_split_the_same_variance_rather_than_adding_more():
    """A third scale describes the ground finer, not rougher."""
    import statistics

    from yerkon.world import patchwork

    def rms(levels):
        ground = patchwork(0.4, 300.0, 0.7, levels=levels, seed=3)
        sampled = [ground(x * 11.0, x * 5.0) for x in range(3000)]
        return (sum(v * v for v in sampled) / len(sampled)) ** 0.5

    assert rms(2) == pytest.approx(rms(3), rel=0.15)


@pytest.mark.parametrize("row", ["urban", "rural", "tunnel"])
def test_every_row_can_have_its_ground_and_its_noise_varied_apart(row):
    """Separate seeds, on purpose.

    Holding the ground and varying the noise asks what the measurement
    does on one landscape; the reverse asks what one deployment does on
    many. Mixed into a single seed, neither question could be asked.
    """
    assert DEFAULTS.entry("{}.ground_seed".format(row))
    assert DEFAULTS.entry("{}.ground_patch_m".format(row))
    assert DEFAULTS.entry("{}.ground_levels".format(row))
    assert DEFAULTS.number("{}.ground_seed".format(row)) != CHOICES[
        row].scenario.seed

    ground = CHOICES[row].scenario.terrain.patches
    assert ground is not None, "the row has no patchwork"
    assert ground.levels >= 2


def test_the_patchwork_changes_nothing_in_these_three_rows_and_says_why():
    """A finding, not an omission. ADR-0026.

    Outdoors the reflecting patch is tilted, so the ray is aimed away
    whatever the roughness. In the bore the floor is two centimetres of
    scatter against a criterion of metres at that grazing angle, so it is
    optically smooth and varying it does nothing. The model is right and
    these three scenarios do not exercise it — which is worth pinning, so
    that a scenario which *does* exercise it is noticed.
    """
    from yerkon.scenarios import catalogue

    for row in ("urban", "rural", "tunnel"):
        flat_ground = DEFAULTS.with_values(
            {"{}.ground_roughness_spread".format(row): 0.0})
        varied = CHOICES[row].scenario.terrain
        plain = catalogue(flat_ground)[row].scenario.terrain

        anchor = CHOICES[row].scenario.deployment.anchors[0].position_m
        unit = CHOICES[row].scenario.deployment.receivers[0]
        here = unit.journey.position_at(unit.journey.duration_s / 2.0)

        assert varied.obstruction_between(anchor, here).surface_roughness_m == (
            pytest.approx(
                plain.obstruction_between(anchor, here).surface_roughness_m,
                rel=0.5,
            )
        ), row
