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


def a_mixed_corridor():
    """A corridor carrying all three modules, and three units on it.

    This was a preset until the modes became three tabs, one per row of
    the table (ADR-0028). Nothing was lost in kind — any tab can still
    hold several anchor runs of different modules, which is what made it
    a mixed corridor — so the tests that check that capability build it
    here instead of asking for a mode that no longer exists.
    """
    from yerkon.viewer.state import AnchorRun, UnitPlan, ViewState

    return ViewState(
        scenario="rural", corridor_m=20_000.0, width_m=0.0,
        relief_m=250.0, hill_spacing_m=6000.0, roughness_m=0.2,
        tolerance_m=5.0, sweep_m=400.0, journey_s=600.0,
        runs=(
            AnchorRun("C", "sx1280", "column", 0.0, 3000.0, 400.0, 25.0),
            AnchorRun("M", "e28", "mast", 3500.0, 15_000.0, 2000.0, 400.0),
            AnchorRun("T", "dwm3000", "tunnel", 15_500.0, 17_500.0, 150.0, 4.0),
        ),
        units=(
            UnitPlan("araç", "vehicle", 100.0, 0.0, 1.5),
            UnitPlan("kamyon", "vehicle", 80.0, 5000.0, 2.8),
            UnitPlan("yaya", "pedestrian", 5.0, 16_000.0, 1.6),
        ),
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
    state = a_mixed_corridor()
    deployment = state.deployment(state.terrain())
    assert len({anchor.radio.part for anchor in deployment.anchors}) == 3
    assert len(state.runs) == 3


def test_a_corridor_can_carry_more_than_one_unit_of_different_kinds():
    state = a_mixed_corridor()
    units = state.deployment(state.terrain()).receivers
    assert len(units) == 3
    assert {unit.product for unit in units} == {"vehicle", "pedestrian"}


def test_each_mode_the_report_names_can_be_loaded():
    for mode in MODES:
        state = from_scenario(mode)
        assert state.runs and state.units
        assert state.deployment(state.terrain()).anchors


def test_a_unit_carrying_one_module_hears_fewer_anchors_than_one_carrying_both():
    state = a_mixed_corridor()
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
    state = a_mixed_corridor().merged(
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
    state = a_mixed_corridor()
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
    state = a_mixed_corridor()
    found = cascades(state, {"region": "US"})
    moved = {group["run"] for group in found["groups"]}
    assert moved == {"C", "M"}
    assert "T" not in moved


def test_shortening_the_site_proposes_the_runs_it_would_shorten():
    """The two site sliders did not mean the same kind of thing.

    Width shapes the anchors directly — a grid runs from the road out to
    it — and length did not, because a run carries its own start and end.
    So one slider moved the deployment and the other moved nothing, with
    nothing on screen saying why.
    """
    state = a_state(corridor_m=20_000.0, width_m=0.0)
    found = cascades(state, {"corridor_m": 8000.0})

    assert found, "shortening the site moved anchors and said nothing"
    group = found["groups"][0]
    assert group["run"] == state.runs[0].identifier
    assert [c["key"] for c in group["asked"]] == ["corridor_m"]
    moved = {c["key"]: (c["before"], c["after"]) for c in group["follows"]}
    assert moved["to_m"] == (24_000.0, 8000.0)


def test_lengthening_the_site_moves_no_anchors_and_asks_nothing():
    """Nothing is standing outside it, so nothing has to come in."""
    state = a_state(corridor_m=8000.0, width_m=0.0)
    assert cascades(state, {"corridor_m": 30_000.0}) is None


def test_a_run_keeps_the_end_somebody_typed_into_it():
    """Clipping that would be answering a question nobody asked.

    Only the length slider brings runs inside the site. Editing a run's
    own end is a person being explicit about that run.
    """
    state = a_state(corridor_m=8000.0, width_m=0.0)
    longer = state.merged({"runs": runs_of(state, to_m=30_000.0)})
    assert longer.runs[0].to_m == 30_000.0
    assert cascades(state, {"runs": runs_of(state, to_m=30_000.0)}) is None
    assert longer.within_site().runs[0].to_m == 8000.0


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
    state = a_mixed_corridor()
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
    drawn = scene(a_mixed_corridor())
    reaches = {anchor["run"]: anchor["reach_m"] for anchor in drawn["anchors"]}
    assert len(reaches) == 3
    assert len(set(reaches.values())) == 3


def test_the_scene_carries_each_unit_and_the_route_it_takes():
    drawn = scene(a_mixed_corridor())
    assert len(drawn["units"]) == 3
    for unit in drawn["units"]:
        assert unit["trail"] and unit["hears"] >= 0
        assert unit["radios"]


def test_the_scene_is_json_and_nothing_but_json():
    """It crosses a socket on every drag."""
    json.dumps(scene(a_state()))


def test_the_ground_mesh_covers_everything_the_sweep_will_cover():
    """Or coverage cells are painted beside the terrain rather than on it."""
    state = a_mixed_corridor()
    drawn = scene(state)
    swept = sweep(state)
    assert min(drawn["terrain"]["xs"]) <= min(swept["xs"])
    assert max(drawn["terrain"]["xs"]) >= max(swept["xs"])
    assert min(drawn["terrain"]["ys"]) <= min(swept["ys"])
    assert max(drawn["terrain"]["ys"]) >= max(swept["ys"])


def test_the_ground_mesh_holds_the_route_as_well_as_the_anchors():
    """Or the site's length moves nothing a person can see.

    An anchor run keeps its own start and end, so lengthening the
    corridor stretched the road and left the mesh exactly where it was:
    the ground stayed the shape it had been and the road drove off the
    edge of it into nothing.
    """
    from yerkon.viewer.state import AnchorRun

    # An anchor run over the first few kilometres of a longer site, which
    # is the arrangement the mesh got wrong: the ground was drawn around
    # the masts and the journey went somewhere else entirely.
    short = a_state(
        corridor_m=6000.0, width_m=0.0,
        runs=(AnchorRun("M", "e28", "mast", 0.0, 3000.0, 1000.0, 100.0),),
    )
    long = short.merged({"corridor_m": 20_000.0})

    drawn = scene(long)
    east = max(point["x"] for point in drawn["road"])
    assert max(drawn["terrain"]["xs"]) >= east, "the road runs off the ground"
    assert max(drawn["terrain"]["xs"]) > max(scene(short)["terrain"]["xs"]), (
        "the site got longer and the ground it is drawn on did not"
    )


def test_a_mesh_cell_is_about_as_wide_as_it_is_deep():
    """A hundred by forty spread one budget over any site's proportions.

    Twenty kilometres by twenty was sampled every 460 m along and every
    1100 m across, so the ground came out in stripes and a hill read as a
    ridge — the mesh could only resolve it in one direction.
    """
    from yerkon.viewer.scene import mesh_shape

    for along, across in ((20_000.0, 20_000.0), (32_000.0, 8000.0),
                          (3000.0, 3000.0), (24_000.0, 800.0)):
        columns, rows = mesh_shape(along, across)
        wide = along / (columns - 1)
        deep = across / (rows - 1)
        assert 0.2 < wide / deep < 5.0, (along, across, wide, deep)


def test_the_ground_can_be_asked_for_over_one_window_of_the_site():
    """Zoomed in, the site's own mesh is two flat facets under a 30 m model.

    The detail is measured and was merely never asked for.
    """
    from yerkon.viewer.scene import ground

    state = a_state()
    whole = scene(state)["terrain"]
    span = max(whole["xs"]) - min(whole["xs"])

    middle = (min(whole["xs"]) + max(whole["xs"])) / 2
    across = (min(whole["ys"]) + max(whole["ys"])) / 2
    close = ground(
        state, middle - span / 40, middle + span / 40,
        across - span / 40, across + span / 40,
    )
    finer = close["xs"][1] - close["xs"][0]
    coarser = whole["xs"][1] - whole["xs"][0]
    assert finer < coarser / 5, (finer, coarser)
    json.dumps(close)


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
    state = a_mixed_corridor()
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


def test_a_session_holds_all_three_rows_at_once():
    """ADR-0028. Switching rows must not throw away what a row holds.

    A dropdown that rebuilt the arrangement on every switch meant an
    afternoon on the rural row was gone the moment somebody looked at the
    tunnel, so nothing could be prepared and compared.
    """
    from yerkon.viewer.state import MODES

    session = Session()
    assert set(session.states) == set(MODES)

    session.write(session.read("urban").merged({"corridor_m": 9000.0}), "urban")
    session.show("tunnel")
    assert session.read().scenario == "tunnel"
    assert session.read("urban").corridor_m == 9000.0, "the tab was discarded"

    session.show("urban")
    assert session.read().corridor_m == 9000.0


def test_a_run_covers_the_rows_as_prepared_and_says_so_when_asked_for_one():
    session = Session()
    assert [name for name, _ in session.prepared()] == list(
        __import__("yerkon.viewer.state", fromlist=["MODES"]).MODES)
    assert [name for name, _ in session.prepared(["rural"])] == ["rural"]
    with pytest.raises(ValueError, match="no row called"):
        session.prepared(["atlantis"])


def test_resetting_one_row_leaves_the_others_alone():
    session = Session()
    session.write(session.read("rural").merged({"seed": 77}), "rural")
    session.write(session.read("urban").merged({"seed": 88}), "urban")
    session.show("rural")
    session.reset()
    assert session.read("rural").seed != 77
    assert session.read("urban").seed == 88


def test_showing_a_row_that_does_not_exist_says_which_do():
    with pytest.raises(ValueError, match="no row called"):
        Session().show("mixed")


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


def test_only_the_bore_is_a_line():
    """The report's town and open country are areas. ADR-0014's addendum.

    A mode list where every mode was a corridor is what put a factor of
    four into the urban row for no physical reason.
    """
    from yerkon.viewer.state import MODES, from_scenario

    shapes = {name: from_scenario(name).width_m > 0.0 for name in MODES}
    assert shapes == {"urban": True, "rural": True, "tunnel": False}


def test_there_are_three_rows_and_each_opens_on_its_own_ground():
    """ADR-0028. Three tabs, and each one matching the row it prepares.

    The rural tab opened on the Gölbaşı hills while the rural row of the
    table stood on the Polatlı plain, so the picture and the published
    figure described different places.
    """
    from yerkon.settings import DEFAULTS
    from yerkon.viewer.state import MODES, from_scenario

    assert len(MODES) == 3
    for name in MODES:
        assert from_scenario(name).site == DEFAULTS.text(
            "{}.site".format(name)
        ), name


def test_the_reach_drawn_is_the_reach_the_ground_gives():
    """A ring the run does not agree with is worse than no ring.

    A fetched grid brings its own surface roughness and ignores the
    slider, so a reach ring computed from the slider would describe a
    deployment on ground nobody is standing on — and nothing on screen
    would say which of the two was real.
    """
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

    # A ranged setting draws two controls that share one state field: the
    # slider `x` and the exact number `x-num`, which the page reaches by
    # building the name rather than by spelling it.
    assert '"-num"' in application, (
        "the number beside each slider is no longer reached by convention;"
        " this test's allowance for it is now hiding dead controls"
    )
    unused = {
        name for name in interactive
        if name.removesuffix("-num") not in application
    }
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


def test_a_run_uses_the_arrangement_the_tab_holds():
    """Not the shipped catalogue, and not only the figures. ADR-0028.

    A tab holds an arrangement somebody built — anchors dragged, a mast
    raised, a spacing narrowed — and a run that quietly rebuilt it from
    the catalogue would report a deployment nobody was looking at.
    """
    from yerkon.viewer.state import from_scenario
    from yerkon.viewer.tasks import deployments_of

    prepared = from_scenario("urban")
    denser = prepared.merged({
        "runs": tuple(
            {**run.as_json(), "spacing_m": 250.0} for run in prepared.runs
        )
    })
    standard = deployments_of([("urban", prepared)])[0]
    edited = deployments_of([("urban", denser)])[0]
    assert (
        len(edited.scenario.deployment.anchors)
        > len(standard.scenario.deployment.anchors)
    )


def test_a_run_with_no_rows_says_so():
    from yerkon.viewer.tasks import deployments_of

    with pytest.raises(ValueError, match="no rows to run"):
        deployments_of([])





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
    assert target_from({}).describe() == "belirli bir şey değil"


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


# --- Two languages ---------------------------------------------------------


def test_the_page_says_nothing_it_has_not_got_in_both_languages():
    """A phrase with one language is a page nine tenths translated, which
    is the failure nobody notices (ADR-0035)."""
    import pathlib
    import re

    words = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/words.js"
    ).read_text(encoding="utf-8")

    phrases = re.findall(r'^  "([\w.]+)": \{(.*?)\},\n', words, re.S | re.M)
    assert len(phrases) > 100, "this stopped matching the catalogue"
    for key, body in phrases:
        assert "tr:" in body, key
        assert "en:" in body, key


def test_a_phrase_names_its_fields_rather_than_counting_them():
    """Positional substitution gave one language the other's numbers.

    "72 değerin 35 tanesi varsayım" counts the total first and "35 of 72
    figures are assumptions" counts the assumptions first, and with {} in
    both, one of them is wrong. It was.
    """
    import pathlib

    words = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/words.js"
    ).read_text(encoding="utf-8")
    # The phrases themselves, not the prose explaining why.
    phrases = "".join(
        line for line in words.split("export function say")[0].splitlines()
        if line.lstrip().startswith('"')
    )
    assert "{}" not in phrases, (
        "a phrase still counts its fields instead of naming them"
    )


def test_the_markup_holds_no_words_of_its_own():
    """Every phrase is a name the page looks up, so switching language
    reaches all of them."""
    import pathlib
    import re

    page = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/index.html"
    ).read_text(encoding="utf-8")
    body = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    body = body[body.index("<aside"):]
    left = [" ".join(run.split()) for run in re.split(r"<[^>]+>", body)]
    turkish = [
        run for run in left
        if run and re.search(r"[çğıöşüÇĞİÖŞÜ]", run)
    ]
    assert not turkish, "still written into the markup: {}".format(turkish)


def test_every_row_of_the_table_is_named_in_both():
    from yerkon.viewer.state import MODES, mode_labels

    turkish = mode_labels("tr")
    english = mode_labels("en")
    for name in MODES:
        assert turkish[name] and english[name], name
        assert turkish[name] != english[name], name


def test_switching_language_moves_every_row_at_once():
    """A language belongs to the person reading rather than to a row."""
    session = Session()
    session.speak("en")
    for name in MODES:
        assert session.read(name).language == "en"
    assert "the rural row" in session.read("rural").settings().entry(
        "rural.site").affects


def test_resetting_a_row_keeps_the_language_on_screen():
    session = Session()
    session.speak("en")
    assert session.reset("rural").language == "en"


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
    assert "orbit.target = onGround(" in application
    for gesture in ("event.button === 2", "event.shiftKey", "NUDGE"):
        assert gesture in application, gesture


def test_the_point_the_camera_turns_around_rides_on_the_ground():
    """A pivot that keeps the height it was framed at gets buried.

    Ankara's rural grid moves four hundred and fifty metres and the
    relief is drawn five times over, so sliding across it left the point
    being turned around two kilometres under the hill in view space.
    Turning about that swings the whole site past the screen rather than
    rotating the thing being looked at, which is the single reason the
    camera felt wrong after any pan.
    """
    application = read_app_js()
    assert "function onGround" in application
    body = application[application.index("function onGround"):]
    body = body[: body.index("\n}")]
    assert "groundAt(" in body and "draw.VERTICAL" in body

    # Every gesture that slides the pivot has to use it, or the one that
    # does not is the one that buries the camera again.
    for gesture in ("panning", "wheel", "NUDGE"):
        assert gesture in application, gesture
    assert application.count("orbit.target = onGround(") == 4, (
        "a gesture moves the pivot without putting it back on the ground"
    )


def test_the_scene_is_painted_once_a_frame_and_not_once_an_event():
    """A trackpad reports far faster than this scene can be drawn.

    Painting on every pointer event meant the queue grew for as long as a
    drag lasted and the picture ran behind the hand. The arithmetic was
    right the whole time and moving still felt broken.
    """
    application = read_app_js()
    scheduler = application[application.index("function render()"):]
    scheduler = scheduler[: scheduler.index("function paintScene")]
    assert "requestAnimationFrame" in scheduler
    assert "framePending" in scheduler


def test_the_camera_is_framed_once_and_then_left_alone():
    """Re-centring on every refresh is what made panning pointless.

    Any slide a person made was undone by their next edit, which reads as
    a broken camera rather than as a deliberate reset.
    """
    application = read_app_js()
    framing = application[application.index("terrainData = latest.terrain;"):]
    framing = framing[: framing.index("scheduleSweep")]
    assert "frameEverything()" in framing
    guard = framing.index("if (!framed)")
    assert guard < framing.index("frameEverything()"), (
        "the camera is framed outside the guard, so an edit re-centres it"
    )


def test_framing_aims_at_the_ground_rather_than_at_sea_level():
    """ADR-0029. Ankara is 700 to 1900 m up and the relief is drawn five
    times over, so a camera aimed at z = 0 looks at a point nearly six
    thousand units below everything there is.

    That is a blank screen, and it was one, on every mode standing on
    fetched ground. Modelled terrain averages zero and hid it completely
    until the scenarios moved onto real Ankara.
    """
    application = read_app_js()
    body = application[application.index("function frameEverything"):]
    body = body[: body.index("\n}")]
    assert "ground_z" in body, "the framing ignores how high the ground is"
    assert "draw.VERTICAL" in body, (
        "the framing ignores the vertical exaggeration it is drawn with"
    )


def test_a_slide_reads_the_cursor_against_the_camera_it_started_with():
    """Otherwise the slide is a loop through the terrain, and it rings.

    The pivot rides on the ground, so its height moves the eye, the eye
    moves where the cursor's ray lands, and that moves the pivot. Over
    real relief the gain is above one: the scene lurched forward and back
    on alternate frames for as long as the drag lasted. Measured as a
    frame-to-frame difference that alternated 9,8 / 5,7 / 9,6 / 5,7 while
    a steady turn stayed level.
    """
    application = read_app_js()
    grab = application[application.index("if (slide) {"):]
    grab = grab[: grab.index("} else {")]
    assert "from: view()" in grab, (
        "the slide does not keep the camera it started with"
    )

    move = application[application.index("if (panning) {"):]
    move = move[: move.index("if (spinning)")]
    assert "panning.from.onPlane" in move, (
        "the slide reads the cursor against the live camera, which is the"
        " loop that oscillated"
    )
    assert "groundUnder(...pixel(event))" not in move


def test_the_ground_is_sampled_between_its_samples():
    """A nearest-sample lookup is a staircase seven hundred metres wide.

    That was tolerable while it only placed coverage cells and became a
    bug the moment the camera's pivot started riding on it.
    """
    application = read_app_js()
    body = application[application.index("function sampleAt"):]
    body = body[: body.index("\nfunction within")]
    assert "Math.round" not in body, "still taking the nearest sample"
    assert "Math.floor" in body


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


def test_every_step_of_the_panel_says_what_it_currently_holds():
    """A collapsed step is only worth collapsing if it still reports.

    The panel was one column of every control the engine has, in the
    order the engine grew them. Somebody scrolls that looking for the one
    thing they came for, and cannot see what the other five sections are
    set to without opening all five.
    """
    import pathlib
    import re

    static = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static"
    )
    page = (static / "index.html").read_text(encoding="utf-8")
    application = read_app_js()

    steps = re.findall(r'<details class="step" id="(step-[a-z]+)"', page)
    assert len(steps) >= 5, "the panel is no longer built as steps"

    lines = set(re.findall(r'<span class="now" id="(sum-[a-z]+)"', page))
    assert len(lines) == len(steps), "a step has no line of its own"
    for line in lines:
        assert '"{}"'.format(line) in application, (
            "{} is drawn and nothing ever writes to it".format(line)
        )


def test_the_search_matches_however_the_word_is_spelled():
    """Somebody hunting the noise figure types "gurultu" as often as
    "gürültü", and a search that answers one of them is a search people
    stop using."""
    application = read_app_js()
    assert "function folded" in application or "const folded" in application
    fold = application[application.index("const FOLD"):]
    fold = fold[: fold.index("function wireFind")]
    for letter in ("ı", "ş", "ğ", "ü", "ö", "ç"):
        assert letter in fold, letter


def test_a_hidden_row_is_actually_hidden():
    """A class that sets `display` outranks the browser's [hidden].

    A searched-away figure row is a grid, so it stayed on screen with the
    attribute set on it and the search looked broken while doing exactly
    what it was told.
    """
    import pathlib

    style = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/style.css"
    ).read_text(encoding="utf-8")
    assert "[hidden] { display: none !important; }" in style


def test_every_key_the_settings_file_uses_has_a_name_in_the_panel():
    """`clock.crystal.residual_ppm` is what goes in the file and what
    somebody editing the file needs; it is not a name. Seventy-two of
    them read as a dump of variables rather than as the set of things
    this study rests on."""
    from yerkon.settings import DEFAULTS

    application = read_app_js()
    terms = application[application.index("const TERMS = {"):]
    terms = terms[: terms.index("\n};")]

    missing = sorted({
        part
        for key in DEFAULTS.entries
        for part in key.split(".")[1:]
        if "{}:".format(part) not in terms
        # A part name that is a product is already a name.
        and part not in ("sx1280", "dwm3000", "tcxo")
    })
    assert not missing, "no Turkish name for: {}".format(", ".join(missing))


def test_no_slider_stops_short_of_a_value_a_mode_actually_sets():
    """A slider that clamps shows one number while the state holds another.

    The rural mode ran a forty minute journey and the slider stopped at
    fifteen, so it read 900 and cut the journey to a quarter the moment
    anybody touched it — a setting silently changed by looking at it.
    """
    import pathlib
    import re

    from yerkon.viewer.state import MODES, from_scenario

    page = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src/yerkon/viewer/static/index.html"
    ).read_text(encoding="utf-8")
    ranges = {
        found.group(1): (float(found.group(2)), float(found.group(3)))
        for found in re.finditer(
            r'id="([a-z_]+)"[^>]*min="([-\d.]+)"[^>]*max="([-\d.]+)"', page)
    }
    assert ranges, "no sliders found; this stopped matching the page"

    for mode in MODES:
        state = from_scenario(mode)
        for name, (low, high) in ranges.items():
            value = getattr(state, name, None)
            if not isinstance(value, (int, float)):
                continue
            assert low <= value <= high, (
                "{} sets {} to {}, outside the slider's [{}, {}]".format(
                    mode, name, value, low, high)
            )


def test_a_finished_task_is_eventually_forgotten_but_a_running_one_never_is():
    """A page left open for a day runs a lot of these, each holding its log.

    Dropping the oldest keeps that bounded. Dropping a *running* one would
    make a twelve minute dissection vanish from under the page watching
    it, which is worse than any amount of memory.
    """
    import time

    from yerkon.viewer.jobs import Jobs

    registry = Jobs()
    started = [
        registry.start("quick", lambda say: {}).identifier
        for _ in range(Jobs.REMEMBERED + 8)
    ]
    for _ in range(200):
        if registry.read(started[-1]) and registry.read(started[-1]).done:
            break
        time.sleep(0.01)

    kept = [one for one in started if registry.read(one) is not None]
    assert len(kept) <= Jobs.REMEMBERED
    assert started[-1] in kept, "the newest task was dropped"

    running = registry.start("slow", lambda say: (time.sleep(3), {})[-1])
    for _ in range(Jobs.REMEMBERED + 8):
        registry.start("quick", lambda say: {})
    assert registry.read(running.identifier) is not None


def test_every_figure_in_the_file_has_a_heading_to_be_drawn_under():
    """The panel renders per group, so one without a heading is invisible.

    Sixteen deployment figures spent a release documented as "editable in
    the viewer" and never appeared in it: the server sent them and the
    page had nowhere to put them. Nothing failed, because a figure that
    is not drawn does not raise.
    """
    from yerkon.settings import DEFAULTS
    from yerkon.viewer.scene import GROUPS, figures

    headings = {key for key, _ in GROUPS}
    present = {key.split(".")[0] for key in DEFAULTS.entries}
    assert present <= headings, "no heading for {}".format(
        ", ".join(sorted(present - headings))
    )

    listed = figures(a_state())
    drawn = sum(
        1 for figure in listed["figures"] if figure["group"] in headings
    )
    assert drawn == listed["total"]


def test_asking_for_a_row_that_does_not_exist_refuses_rather_than_defaulting():
    """A silent fallback is how a typo becomes the wrong deployment.

    `from_scenario` used to return a plain ViewState for any name it did
    not know, so asking for a mode that had been removed gave a single
    rural corridor and every figure that followed described it — a costing
    test found three anchor products where there was one, which is the
    only reason anybody noticed.
    """
    from yerkon.viewer.state import from_scenario

    with pytest.raises(ValueError, match="no row called"):
        from_scenario("mixed")
    with pytest.raises(ValueError, match="no row called"):
        from_scenario("")
