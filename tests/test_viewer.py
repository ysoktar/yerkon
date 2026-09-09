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


def test_flat_ground_is_asked_for_by_setting_the_relief_to_zero():
    assert "flat" in a_state(relief_m=0.0).terrain().description
    assert "rolling" in a_state(relief_m=40.0).terrain().description


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


def test_the_page_asks_for_every_file_the_server_serves():
    """A missing script is a 404 and a dead page, not a Python failure."""
    import pathlib
    import re

    static = pathlib.Path(__file__).resolve().parent.parent / (
        "src/yerkon/viewer/static"
    )
    page = (static / "index.html").read_text(encoding="utf-8")
    for reference in re.findall(r'(?:src|href)="/([^"]+)"', page):
        assert (static / reference).exists(), reference

    application = (static / "app.js").read_text(encoding="utf-8")
    for imported in re.findall(r'from "/([^"]+)"', application):
        assert (static / imported).exists(), imported
