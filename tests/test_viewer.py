"""The viewer's engine half: state, scene, and what needs confirming."""

import json

import pytest

from yerkon.viewer.scene import design_of, reach_of, scene, simulate, sweep
from yerkon.viewer.server import Session, cascades
from yerkon.viewer.state import (
    CASCADING,
    MODES,
    AnchorRun,
    UnitPlan,
    ViewState,
    from_scenario,
)


def a_state(**changes):
    return ViewState(**changes) if changes else ViewState()


def runs_of(state, **patch):
    """The state's runs as plain dictionaries, with the first one edited."""
    runs = [run.as_json() for run in state.runs]
    runs[0].update(patch)
    return runs


# --- State ----------------------------------------------------------------


def test_a_state_builds_the_same_objects_the_table_is_built_from():
    deployed = a_state().deployed()
    assert deployed.scenario.deployment.anchors
    assert deployed.route_km == pytest.approx(24.0)


def test_closer_spacing_puts_more_anchors_along_the_same_corridor():
    def count(spacing_m):
        state = a_state()
        state = state.merged({"runs": runs_of(state, spacing_m=spacing_m)})
        return len(state.deployed().scenario.deployment.anchors)

    assert count(1000.0) > count(4000.0)


def test_a_corridor_can_carry_more_than_one_kind_of_anchor():
    """Which is the arrangement the report describes and none of its
    three rows measures on its own."""
    state = from_scenario("mixed")
    deployment = state.deployment(state.terrain())
    assert len({anchor.radio.part for anchor in deployment.anchors}) == 3
    assert len(state.runs) == 3


def test_a_corridor_can_carry_more_than_one_unit_of_different_kinds():
    state = from_scenario("mixed")
    units = state.deployment(state.terrain()).receivers
    assert len(units) == 3
    assert {unit.product for unit in units} == {"vehicle", "pedestrian"}


def test_each_mode_the_report_names_can_be_loaded():
    for mode in MODES:
        state = from_scenario(mode)
        assert state.runs and state.units
        assert state.deployment(state.terrain()).anchors


def test_a_unit_carrying_one_module_hears_fewer_anchors_than_one_carrying_both():
    state = from_scenario("mixed")
    state = state.merged({
        "units": [
            {**state.units[0].as_json(), "identifier": "tek",
             "radios": ["sx1280"]},
            {**state.units[0].as_json(), "identifier": "çift",
             "radios": ["sx1280", "dwm3000"]},
        ],
    })
    deployment = state.deployment(state.terrain())
    one, both = deployment.receivers
    assert len(deployment.anchors_heard_by(one)) < len(
        deployment.anchors_heard_by(both)
    )


def test_a_setting_the_viewer_does_not_have_is_refused():
    """Better than silently dropping half an edit."""
    with pytest.raises(ValueError, match="not a setting: colour"):
        a_state().merged({"colour": "blue"})


def test_the_viewer_will_not_draw_a_flat_surface():
    """ADR-0021. Nowhere is flat, so the page does not offer flat.

    The relief slider used to reach zero and return a perfectly level
    plane. That is not a simplification of anywhere: it is the most
    favourable ground this project can draw, because every reflection
    arrives at the specular angle the two-ray model assumes. Asking for
    it now gets rolling ground with a metre of relief, and the slider
    itself does not go below five.
    """
    for relief_m in (0.0, -10.0, 40.0):
        assert "flat" not in a_state(relief_m=relief_m).terrain().description


def test_naming_a_fetched_site_puts_the_deployment_on_real_ground():
    """The whole point of ADR-0008 arriving in the viewer.

    A fetched grid brings its own relief, its own roughness and its own
    obstructions, so none of the three modelled sliders applies to it.
    """
    from yerkon.viewer.state import fetched_sites

    available = fetched_sites()
    assert available, "the package ships fetched Ankara ground"

    real = a_state(site=available[0]).terrain()
    assert "rolling" not in real.description
    assert real.micro_roughness_m > 0.0


def test_a_site_that_was_never_fetched_says_so_rather_than_inventing_ground():
    with pytest.raises(ValueError, match="no site fetched"):
        a_state(site="atlantis").terrain()


def test_a_bore_slopes_and_does_not_follow_the_mountain_over_it():
    """A tunnel goes through a hill, so its floor cannot be draped terrain.

    It is a straight line between two portals, and it falls, because
    every road tunnel is built to a drainage gradient.
    """
    bore = from_scenario("tunnel").terrain()
    assert bore.height_at(0.0, 0.0) != bore.height_at(2000.0, 0.0)
    # Straight: the midpoint sits exactly between the portals.
    ends = (bore.height_at(0.0, 0.0), bore.height_at(2000.0, 0.0))
    assert bore.height_at(1000.0, 0.0) == pytest.approx(sum(ends) / 2.0)
    # And within what a road tunnel is built to.
    grade = abs(ends[1] - ends[0]) / 2000.0
    assert 0.004 <= grade <= 0.030


def test_a_moved_anchor_stays_where_it_was_put():
    state = a_state(moved={"M2": (1234.0, -99.0)})
    anchors = state.anchors(state.terrain())
    placed = next(a for a in anchors if a.identifier == "M2")
    assert placed.ground_position_m == (1234.0, -99.0)


def test_a_removed_anchor_is_gone():
    state = a_state(removed=("M0", "M1"))
    identifiers = [a.identifier for a in state.anchors(state.terrain())]
    assert "M0" not in identifiers and "M1" not in identifiers


def test_removing_every_anchor_is_refused_rather_than_crashing_later():
    state = a_state(removed=tuple("M{}".format(i) for i in range(40)))
    with pytest.raises(ValueError, match="every anchor has been removed"):
        state.anchors(state.terrain())


def test_a_state_survives_a_round_trip_through_json():
    """It travels to the browser and back on every edit."""
    state = from_scenario("mixed").merged(
        {"moved": {"M1": (10.0, 20.0)}, "removed": ("M3",)}
    )
    again = ViewState().merged(json.loads(json.dumps(state.as_json())))
    assert again.moved == {"M1": (10.0, 20.0)}
    assert again.removed == ("M3",)
    assert [run.radio for run in again.runs] == [run.radio for run in state.runs]
    assert [unit.radios for unit in again.units] == [
        unit.radios for unit in state.units
    ]


# --- What has to be confirmed ---------------------------------------------


def test_changing_a_runs_mounting_has_to_be_confirmed():
    """It moves that run's anchor height, and everything follows."""
    state = a_state()
    found = cascades(state, {"runs": runs_of(state, mounting="sign")})
    assert found is not None
    group = found["groups"][0]
    assert group["run"] == state.runs[0].identifier
    labels = [c["label"] for c in group["follows"]]
    assert "usable range" in labels
    assert all(c["because"] for c in group["follows"])


def test_a_change_to_one_run_says_which_run_it_is():
    """A corridor carries several, and a panel that did not say which
    would be describing an unnamed part of the deployment."""
    state = from_scenario("mixed")
    runs = [run.as_json() for run in state.runs]
    runs[1]["mounting"] = "sign"
    found = cascades(state, {"runs": runs})
    assert [group["run"] for group in found["groups"]] == [state.runs[1].identifier]


def test_a_shared_setting_is_proposed_against_every_run_it_moves():
    """The region moves the spread runs and does not move the impulse one.

    An ultra-wideband rating is already an emission limit rather than a
    conducted power, so a jurisdiction that raises the conducted ceiling
    raises nothing for it. The panel shows the two runs that change and
    stays quiet about the one that does not, which is the true answer
    rather than a tidier one.
    """
    state = from_scenario("mixed")
    found = cascades(state, {"region": "US"})
    moved = {group["run"] for group in found["groups"]}
    assert moved == {"C", "M"}
    assert "T" not in moved


def test_changing_the_region_has_to_be_confirmed():
    found = cascades(a_state(region="TR"), {"region": "US"})
    assert found is not None
    assert any(
        c["key"] == "eirp_dbm" for c in found["groups"][0]["follows"]
    )


def test_moving_the_terrain_does_not_have_to_be_confirmed():
    """It changes the world, not the radio. The panel has nothing to say."""
    state = a_state()
    assert cascades(state, {"relief_m": 0.0}) is None
    assert cascades(state, {"runs": runs_of(state, spacing_m=1000.0)}) is None
    assert cascades(state, {"moved": {"M1": (0.0, 0.0)}}) is None


def test_moving_an_anchor_or_adding_a_unit_does_not_have_to_be_confirmed():
    state = from_scenario("mixed")
    units = [unit.as_json() for unit in state.units]
    units.append({**units[0], "identifier": "yeni"})
    assert cascades(state, {"units": units}) is None


def test_a_change_that_changes_nothing_is_not_confirmed():
    state = a_state()
    assert cascades(state, {"runs": runs_of(state)}) is None


def test_every_change_carries_a_key_the_page_can_translate_by():
    """So the engine stays in one language and the page in another."""
    state = a_state()
    found = cascades(state, {"runs": runs_of(state, mounting="sign")})
    group = found["groups"][0]
    for change in group["asked"] + group["follows"]:
        assert change["key"]


def test_the_cascading_settings_are_all_real_design_fields():
    from yerkon.design import Design
    from yerkon.viewer.state import CASCADING_RUN

    for name, field in CASCADING.items():
        assert name in ViewState.__dataclass_fields__, name
        assert field in Design.__dataclass_fields__, field
    for name, field in CASCADING_RUN.items():
        assert name in AnchorRun.__dataclass_fields__, name
        assert field in Design.__dataclass_fields__, field


# --- What the page is given -----------------------------------------------


def test_the_scene_carries_ground_road_anchors_and_units():
    drawn = scene(a_state())
    assert drawn["terrain"]["heights"]
    assert len(drawn["terrain"]["heights"]) == len(drawn["terrain"]["ys"])
    assert len(drawn["terrain"]["heights"][0]) == len(drawn["terrain"]["xs"])
    assert drawn["road"] and drawn["anchors"] and drawn["units"]
    assert all(run["reach_m"] > 0.0 for run in drawn["runs"])


def test_each_anchor_says_which_run_it_belongs_to_and_how_far_it_reaches():
    """A UWB bracket and a mast on one corridor cover nothing like the
    same ground, so one reach for the whole scene would be a lie."""
    drawn = scene(from_scenario("mixed"))
    reaches = {anchor["run"]: anchor["reach_m"] for anchor in drawn["anchors"]}
    assert len(reaches) == 3
    assert len(set(reaches.values())) == 3


def test_the_scene_carries_each_unit_and_the_route_it_takes():
    drawn = scene(from_scenario("mixed"))
    assert len(drawn["units"]) == 3
    for unit in drawn["units"]:
        assert unit["trail"] and unit["hears"] >= 0
        assert unit["radios"]


def test_the_scene_is_json_and_nothing_but_json():
    """It crosses a socket on every drag."""
    json.dumps(scene(a_state()))


def test_the_ground_mesh_covers_everything_the_sweep_will_cover():
    """Or coverage cells are painted beside the terrain rather than on it."""
    state = from_scenario("mixed")
    drawn = scene(state)
    swept = sweep(state)
    assert min(drawn["terrain"]["xs"]) <= min(swept["xs"])
    assert max(drawn["terrain"]["xs"]) >= max(swept["xs"])
    assert min(drawn["terrain"]["ys"]) <= min(swept["ys"])
    assert max(drawn["terrain"]["ys"]) >= max(swept["ys"])


def test_the_sweep_reports_both_areas_and_they_differ():
    """ADR-0012, on screen as well as in the table."""
    swept = sweep(a_state(sweep_m=1000.0))
    assert swept["reached_km2"] > swept["served_km2"]


def test_a_taller_mounting_reaches_further():
    state = a_state()
    tall = state.merged({"runs": runs_of(state, mounting="mast")})
    short = state.merged({"runs": runs_of(state, mounting="sign")})
    assert reach_of(tall, tall.runs[0]) > reach_of(short, short.runs[0])


def test_the_scene_reports_where_the_link_stops_decoding_beside_where_it_ranges():
    for run in scene(a_state())["runs"]:
        assert run["closure_m"] > run["reach_m"]


def test_the_scene_reports_how_long_a_round_takes():
    """Which is what a person needs to see when they add a second unit."""
    one = scene(a_state())["round_s"]
    state = from_scenario("mixed")
    assert scene(state)["round_s"] > one


@pytest.mark.slow
def test_simulating_from_the_viewer_gives_what_the_table_gives():
    result = simulate(a_state(journey_s=60.0, sweep_m=1000.0))
    assert result["units"] >= 1
    assert result["hpe_p50_m"] > 0.0
    assert 0.0 < result["availability"] <= 1.0
    assert result["capex_tl"] > 0.0
    assert result["opex_tl_per_year"] > 0.0
    assert 0.0 < result["assumed_share"] <= 1.0


# --- The session ----------------------------------------------------------


def test_a_session_holds_one_state_and_hands_it_back():
    session = Session()
    assert session.read().corridor_m == 24_000.0
    session.write(session.read().merged({"corridor_m": 9000.0}))
    assert session.read().corridor_m == 9000.0


# --- The browser half -----------------------------------------------------


def test_the_page_scripts_parse():
    """A syntax error in the page is a blank window and no Python failure.

    One went unnoticed until a browser was opened by hand: a bracket in
    the wrong order left the whole application dead while every Python
    test passed.
    """
    import pathlib
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed; the browser checks this instead")

    static = pathlib.Path(__file__).resolve().parent.parent / (
        "src/yerkon/viewer/static"
    )
    for script in sorted(static.glob("*.js")):
        finished = subprocess.run(
            [node, "--check", str(script)], capture_output=True, text=True
        )
        assert finished.returncode == 0, "{}: {}".format(
            script.name, finished.stderr
        )


def test_the_page_asks_for_nothing_the_server_does_not_serve():
    """A missing file or a wrong route is a dead page and no Python failure."""
    import pathlib
    import re

    viewer = pathlib.Path(__file__).resolve().parent.parent / "src/yerkon/viewer"
    static = viewer / "static"
    routing = (viewer / "server.py").read_text(encoding="utf-8")

    page = (static / "index.html").read_text(encoding="utf-8")
    application = (static / "app.js").read_text(encoding="utf-8")

    wanted = set(re.findall(r'(?:src|href)="(/[^"]*)"', page))
    wanted |= set(re.findall(r'from "(/[^"]+)"', application))
    wanted |= set(re.findall(r'(?:ask|fetch)\(\s*"(/[^"]+)"', application))
    # Template literals too. `ask(`/api/job?id=${...}`)` slipped past the
    # quoted forms for a whole feature, which is exactly the dead route
    # this test exists to catch.
    wanted |= set(re.findall(r'(?:ask|fetch)\(\s*`(/[^`$]+)', application))

    for reference in sorted(wanted):
        reference = reference.split("?")[0]
        if reference in ("/", ""):
            continue
        if reference.startswith("/api/"):
            assert '"{}"'.format(reference) in routing, reference
        else:
            assert (static / reference.lstrip("/")).exists(), reference


# --- Editing the figures while it runs ------------------------------------


def test_every_figure_nobody_supplied_is_offered_for_editing():
    from yerkon.settings import DEFAULTS
    from yerkon.viewer.scene import figures

    listed = figures(a_state())
    assert len(listed["figures"]) == len(DEFAULTS.entries)
    assert listed["assumed"] == len(DEFAULTS.assumed)
    assert listed["groups"]


def test_each_figure_carries_what_a_person_needs_to_change_it():
    from yerkon.viewer.scene import figures

    for figure in figures(a_state())["figures"]:
        assert figure["unit"] and figure["note"] and figure["affects"]
        assert "value" in figure and "assumed" in figure


def test_editing_a_figure_rebuilds_what_it_feeds():
    """The mounting catalogue, the radios, the clocks, the scenarios."""
    state = a_state().merged(
        {"overrides": {"mounting.tall_mast.site_cost_tl": 5000.0}}
    )
    anchors = state.anchors(state.terrain())
    assert float(anchors[0].mounting.site_cost_tl.value) == 5000.0


def test_editing_a_figure_that_moves_the_link_budget_has_to_be_confirmed():
    """A mounting height and a noise figure both change how far it reaches."""
    for key, value in (
        ("mounting.tall_mast.height_m", 40.0),
        ("radio.sx1280.noise_figure_db", 12.0),
    ):
        found = cascades(a_state(), {"overrides": {key: value}})
        assert found is not None, key
        labels = [c["label"] for c in found["groups"][0]["follows"]]
        assert "usable range" in labels, key


def test_editing_a_price_does_not_have_to_be_confirmed():
    """It moves what the deployment costs and nothing about the physics."""
    assert cascades(
        a_state(), {"overrides": {"mounting.tall_mast.site_cost_tl": 5000.0}}
    ) is None


def test_a_figure_edited_by_hand_is_still_an_assumption():
    """A number typed into a viewer is a different guess, not a measurement."""
    state = a_state().merged(
        {"overrides": {"mounting.tall_mast.site_cost_tl": 5000.0}}
    )
    settings = state.settings()
    assert settings.number("mounting.tall_mast.site_cost_tl") == 5000.0
    assert settings.entry("mounting.tall_mast.site_cost_tl").is_assumed


def test_a_figure_given_a_source_stops_being_an_assumption():
    state = a_state().merged({
        "overrides": {
            "mounting.tall_mast.site_cost_tl": {
                "value": 5000.0, "source": "a quotation",
            }
        }
    })
    settings = state.settings()
    assert not settings.entry("mounting.tall_mast.site_cost_tl").is_assumed
    assert len(settings.assumed) == len(a_state().settings().assumed) - 1


def test_an_edited_figure_moves_the_answer():
    """Not decoration: a worse noise figure shortens every link on screen."""
    from yerkon.viewer.scene import reach_of

    plain = a_state()
    noisy = plain.merged({"overrides": {"radio.e28.noise_figure_db": 12.0}}) \
        if "radio.e28.noise_figure_db" in plain.settings().entries else \
        plain.merged({"overrides": {"radio.sx1280.noise_figure_db": 12.0}})
    assert reach_of(noisy, noisy.runs[0]) < reach_of(plain, plain.runs[0])


def test_a_figure_the_file_does_not_hold_is_refused():
    state = a_state().merged({"overrides": {"not.a.figure": 1.0}})
    with pytest.raises(KeyError, match="nothing may be assumed in the code"):
        state.settings()


def test_the_edits_can_be_written_back_as_a_file(tmp_path):
    """A viewer that loses an afternoon's work is a toy."""
    from yerkon.settings import load

    state = a_state().merged({
        "overrides": {
            "mounting.tall_mast.site_cost_tl": {
                "value": 5000.0, "source": "a quotation",
            },
            "operating.maintenance_tl_per_visit": 2200.0,
        }
    })
    path = tmp_path / "written.toml"
    path.write_text(state.settings().to_toml(), encoding="utf-8")

    back = load(str(path))
    assert back.number("mounting.tall_mast.site_cost_tl") == 5000.0
    assert back.number("operating.maintenance_tl_per_visit") == 2200.0
    assert not back.entry("mounting.tall_mast.site_cost_tl").is_assumed


# --- A site is a line or an area, and the viewer shows both ---------------


def an_area(width_m=3000.0):
    from yerkon.viewer.state import AnchorRun, ViewState

    return ViewState(
        scenario="urban",
        corridor_m=3000.0,
        width_m=width_m,
        relief_m=0.0,
        runs=(
            AnchorRun("C", "sx1280", "column", 0.0, 3000.0, 500.0, 0.0,
                      stagger_m=250.0),
        ),
    )


def test_width_turns_a_line_of_anchors_into_a_grid():
    """ADR-0014's addendum. One knob decides the shape of the whole site.

    Seven positions along by seven across is forty-nine anchors; the same
    run with no width is the seven along it started as.
    """
    area = an_area()
    corridor = area.merged({"width_m": 0.0})
    terrain = area.terrain()

    assert len(corridor.anchors(terrain)) == 7
    assert len(area.anchors(terrain)) == 49


def test_an_area_is_driven_round_and_across_rather_than_straight():
    """A journey that only runs east never changes its cross-track geometry.

    Which would make an area behave like the corridor it is not, so the
    route has to turn.
    """
    area = an_area()
    terrain = area.terrain()

    straight = area.merged({"width_m": 0.0}).road(terrain)
    circuit = area.road(terrain)

    assert straight.length_m == pytest.approx(area.corridor_m, rel=0.05)
    assert circuit.length_m > 3.0 * area.corridor_m
    assert len({round(y) for _, y in circuit.centreline_m}) > 1


def test_a_staggered_row_is_offset_and_an_unstaggered_one_is_not():
    """A perfect grid puts every anchor a receiver sees on one of two lines.

    Which is a worse arrangement than anything anybody builds, so
    alternate rows shift along.
    """
    terrain = an_area().terrain()
    staggered = {a.position_m[0] for a in an_area().anchors(terrain)}
    square = {
        a.position_m[0]
        for a in an_area().merged({
            "runs": tuple(
                {**run.as_json(), "stagger_m": 0.0} for run in an_area().runs
            )
        }).anchors(terrain)
    }
    assert len(staggered) == 2 * len(square)


def test_only_the_bore_and_the_mixed_corridor_are_lines():
    """The report's town and open country are areas. ADR-0014's addendum.

    A mode list where every mode was a corridor is what put a factor of
    four into the urban row for no physical reason.
    """
    from yerkon.viewer.state import MODES, from_scenario

    shapes = {name: from_scenario(name).width_m > 0.0 for name in MODES}
    assert shapes == {
        "urban": True, "rural": True, "tunnel": False, "mixed": False
    }


def test_the_reach_drawn_is_the_reach_the_ground_gives():
    """A ring the run does not agree with is worse than no ring.

    A fetched grid brings its own surface roughness and ignores the
    slider, so a reach ring computed from the slider would describe a
    deployment on ground nobody is standing on — and nothing on screen
    would say which of the two was real.
    """
    from yerkon.viewer.scene import design_of

    real = a_state(site="kizilay", roughness_m=0.05)
    assert design_of(real).surface_roughness_m == pytest.approx(
        real.terrain().micro_roughness_m
    )
    assert design_of(real).surface_roughness_m != pytest.approx(0.05)

    modelled = a_state(roughness_m=0.05)
    assert design_of(modelled).surface_roughness_m == pytest.approx(0.05)


# --- Everything the command line can do, from the page --------------------


def test_every_control_the_page_offers_is_wired_to_something():
    """A control that looks live and does nothing is worse than no control.

    The other direction from the route test: not "does every route the
    script asks for exist" but "does anything actually reach every button,
    box and menu the page draws". Only interactive elements — a div the
    stylesheet positions is not a promise to the person looking at it.
    """
    import pathlib
    import re

    static = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static"
    )
    page = (static / "index.html").read_text(encoding="utf-8")
    application = (static / "app.js").read_text(encoding="utf-8")

    interactive = set(re.findall(
        r'<(?:button|input|select|textarea)\b[^>]*\bid="([a-z0-9_-]+)"', page
    ))
    assert len(interactive) > 10, "this stopped matching the page's controls"

    unused = {name for name in interactive if name not in application}
    assert not unused, "the page draws {} and nothing reaches them".format(
        ", ".join(sorted(unused))
    )


def test_the_page_can_reach_every_verb_the_command_line_has():
    """ADR-0024. Anything worth doing is doable without a terminal.

    Named as the list of verbs rather than discovered, so that adding one
    to the command line and not to the page fails here.
    """
    import pathlib

    viewer = pathlib.Path(__file__).resolve().parent.parent / "src/yerkon/viewer"
    routing = (viewer / "server.py").read_text(encoding="utf-8")
    for verb in ("table", "budget", "solve"):
        assert '"{}"'.format(verb) in routing, verb
    assert "/api/options" in routing
    assert "/api/option" in routing


def test_a_task_the_server_does_not_have_says_what_it_does_have():
    from yerkon.viewer.tasks import budget, table

    assert callable(table(a_state()))
    assert callable(budget(a_state()))


def test_a_task_runs_against_the_settings_the_page_is_showing():
    """Not against the shipped defaults.

    Somebody who has spent an afternoon moving figures has to be able to
    ask what their arrangement costs, without writing it to a file first.
    """
    from yerkon.viewer.tasks import deployments_of

    denser = a_state().merged({
        "overrides": {"urban.anchor_spacing_m": 250.0,
                      "urban.anchor_stagger_m": 125.0}
    })
    standard = deployments_of(a_state(), ["urban"])[0]
    edited = deployments_of(denser, ["urban"])[0]
    assert (
        len(edited.scenario.deployment.anchors)
        > len(standard.scenario.deployment.anchors)
    )


def test_asking_for_a_scenario_that_does_not_exist_says_so():
    from yerkon.viewer.tasks import deployments_of

    with pytest.raises(ValueError, match="no scenario called"):
        deployments_of(a_state(), ["atlantis"])


def test_a_blank_target_field_is_not_a_bar_of_zero():
    """An empty box means "I do not care", not "must be at least nothing".

    Read the other way, every search would be filtered by conditions
    nobody set, and the ones that matter would be diluted by them.
    """
    import math

    from yerkon.viewer.tasks import target_from

    wide = target_from({"availability": 0.9, "hpe_p50_m": ""})
    assert wide.availability == 0.9
    assert math.isinf(wide.hpe_p50_m)
    assert target_from({}).describe() == "nothing in particular"


def test_applying_an_option_keeps_the_edits_already_made():
    """An option is a short list of edits, so it composes with the rest.

    A person who has already corrected the mast cost and then picks a
    denser grid must not silently lose the correction.
    """
    from yerkon.options import read

    edited = a_state().merged({
        "overrides": {"mounting.tall_mast.site_cost_tl":
                      {"value": 61000.0, "source": "a quotation"}}
    })
    option = read("rural-dense")
    overrides = dict(edited.overrides)
    for key, value in option.values.items():
        overrides[key] = {"value": value, "source": "option"}
    both = edited.merged({"overrides": overrides})

    assert both.settings().number("rural.anchor_spacing_m") == 3000.0
    assert not both.settings().entry(
        "mounting.tall_mast.site_cost_tl").is_assumed


# --- Long work, watched rather than waited on ----------------------------


def test_a_long_task_reports_as_it_goes_rather_than_only_at_the_end():
    """ADR-0024. Twelve minutes of silence is indistinguishable from broken."""
    import time

    from yerkon.viewer.jobs import Jobs

    registry = Jobs()

    def work(say):
        say("first")
        say("second")
        return {"done": True}

    job = registry.start("test", work, total=2)
    for _ in range(100):
        if registry.read(job.identifier).done:
            break
        time.sleep(0.02)

    finished = registry.read(job.identifier)
    assert finished.progress == ["first", "second"]
    assert finished.result == {"done": True}
    assert finished.error is None


def test_a_task_that_fails_says_why_on_the_page(capsys):
    """A traceback in a terminal nobody is looking at is not an error message."""
    import time

    from yerkon.viewer.jobs import Jobs

    registry = Jobs()

    def work(say):
        raise ValueError("the ground was never fetched")

    job = registry.start("test", work)
    for _ in range(100):
        if registry.read(job.identifier).done:
            break
        time.sleep(0.02)

    finished = registry.read(job.identifier)
    assert finished.error == "the ground was never fetched"
    assert finished.result is None


def test_polling_a_task_cannot_see_a_half_written_line():
    """The reader gets a copy, so a list being appended to is never shared."""
    from yerkon.viewer.jobs import Jobs

    registry = Jobs()
    job = registry.start("test", lambda say: (say("one"), {})[-1])
    first = registry.read(job.identifier)
    first.progress.append("not really")
    assert "not really" not in registry.read(job.identifier).progress


def test_asking_after_a_task_that_was_never_started_says_so():
    from yerkon.viewer.jobs import Jobs

    assert Jobs().read("nothing") is None


# --- Moving around the scene ---------------------------------------------


def read_app_js():
    import pathlib

    return (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/app.js"
    ).read_text(encoding="utf-8")


def test_the_camera_can_be_moved_and_not_only_turned():
    """A viewer that only orbits is unusable over twenty kilometres.

    There is no way to look at a corner of a site if the point you turn
    around never moves, and until this was added there was not one.
    """
    application = read_app_js()
    assert "panning" in application
    assert "orbit.target = [" in application
    for gesture in ("event.button === 2", "event.shiftKey", "NUDGE"):
        assert gesture in application, gesture


def test_the_camera_is_framed_once_and_then_left_alone():
    """Re-centring on every refresh is what made panning pointless.

    Any slide a person made was undone by their next edit, which reads as
    a broken camera rather than as a deliberate reset.
    """
    application = read_app_js()
    framing = application[application.index("terrainData = latest.terrain;"):]
    framing = framing[: framing.index("scheduleSweep")]
    target = framing.index("orbit.target = [state.corridor_m")
    guard = framing.index("if (!framed)")
    assert guard < target, "the camera target is set outside the framing guard"


def test_zoom_follows_the_wheel_rather_than_stepping():
    """A fixed step per event makes a trackpad unusable and a mouse coarse.

    Trackpads send many small deltas and mice send few large ones; a
    twelve percent jump per event served neither.
    """
    application = read_app_js()
    assert "event.deltaY / 100" in application
    assert "Math.exp(" in application
    assert "Math.sign(event.deltaY)" not in application


def test_dragging_an_anchor_follows_the_ground_rather_than_one_plane():
    """Over rolling ground the two differ by more than a mast is tall.

    A drag against the plane through the origin drops an anchor visibly
    away from the cursor, which looks like a broken hit test.
    """
    application = read_app_js()
    assert "function groundUnder" in application
    settled = application[application.index("function groundUnder"):]
    settled = settled[: settled.index("function frameOn")]
    assert settled.count("onPlane") == 2, (
        "groundUnder should sample the level plane and then the real height"
    )
