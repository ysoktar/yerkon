"""The viewer's engine half: state, scene, and what needs confirming."""

import json

import pytest

from yerkon.viewer.scene import design_of, scene, simulate, sweep
from yerkon.viewer.server import Session, cascades
from yerkon.viewer.state import CASCADING, ViewState


def a_state(**changes):
    return ViewState(**changes) if changes else ViewState()


# --- State ----------------------------------------------------------------


def test_a_state_builds_the_same_objects_the_table_is_built_from():
    deployed = a_state().deployed()
    assert deployed.scenario.deployment.anchors
    assert deployed.route_km == pytest.approx(24.0)


def test_closer_spacing_puts_more_anchors_along_the_same_corridor():
    few = len(a_state(spacing_m=4000.0).deployed().scenario.deployment.anchors)
    many = len(a_state(spacing_m=1000.0).deployed().scenario.deployment.anchors)
    assert many > few


def test_a_setting_the_viewer_does_not_have_is_refused():
    """Better than silently dropping half an edit."""
    with pytest.raises(ValueError, match="not a setting: colour"):
        a_state().merged({"colour": "blue"})


def test_flat_ground_is_asked_for_by_setting_the_relief_to_zero():
    assert "flat" in a_state(relief_m=0.0).terrain().description
    assert "rolling" in a_state(relief_m=40.0).terrain().description


def test_a_moved_anchor_stays_where_it_was_put():
    state = a_state(moved={"N2": (1234.0, -99.0)})
    anchors = state.anchors(state.terrain())
    placed = next(a for a in anchors if a.identifier == "N2")
    assert placed.ground_position_m == (1234.0, -99.0)


def test_a_removed_anchor_is_gone():
    state = a_state(removed=("N0", "N1"))
    identifiers = [a.identifier for a in state.anchors(state.terrain())]
    assert "N0" not in identifiers and "N1" not in identifiers


def test_removing_every_anchor_is_refused_rather_than_crashing_later():
    state = a_state(removed=tuple("N{}".format(i) for i in range(40)))
    with pytest.raises(ValueError, match="every anchor has been removed"):
        state.anchors(state.terrain())


def test_a_state_survives_a_round_trip_through_json():
    """It travels to the browser and back on every edit."""
    state = a_state(moved={"N1": (10.0, 20.0)}, removed=("N3",))
    again = ViewState().merged(json.loads(json.dumps(state.as_json())))
    assert again.moved == {"N1": (10.0, 20.0)}
    assert again.removed == ("N3",)
    assert again.spacing_m == state.spacing_m


# --- What has to be confirmed ---------------------------------------------


def test_changing_the_mounting_has_to_be_confirmed():
    """It moves the anchor height, and everything follows from that."""
    found = cascades(a_state(), {"mounting": "sign"})
    assert found is not None
    labels = [c["label"] for c in found["follows"]]
    assert "usable range" in labels
    assert all(c["because"] for c in found["follows"])


def test_changing_the_region_has_to_be_confirmed():
    found = cascades(a_state(region="TR"), {"region": "US"})
    assert found is not None
    assert any(c["key"] == "eirp_dbm" for c in found["follows"])


def test_moving_the_terrain_does_not_have_to_be_confirmed():
    """It changes the world, not the radio. The panel has nothing to say."""
    assert cascades(a_state(), {"relief_m": 0.0}) is None
    assert cascades(a_state(), {"spacing_m": 1000.0}) is None
    assert cascades(a_state(), {"moved": {"N1": (0.0, 0.0)}}) is None


def test_a_change_that_changes_nothing_is_not_confirmed():
    assert cascades(a_state(mounting="mast"), {"mounting": "mast"}) is None


def test_every_change_carries_a_key_the_page_can_translate_by():
    """So the engine stays in one language and the page in another."""
    found = cascades(a_state(), {"mounting": "sign"})
    for change in found["asked"] + found["follows"]:
        assert change["key"]


def test_the_cascading_settings_are_all_real_design_fields():
    from yerkon.design import Design

    for name, field in CASCADING.items():
        assert name in ViewState.__dataclass_fields__, name
        assert field in Design.__dataclass_fields__, field


# --- What the page is given -----------------------------------------------


def test_the_scene_carries_ground_road_and_anchors():
    drawn = scene(a_state())
    assert drawn["terrain"]["heights"]
    assert len(drawn["terrain"]["heights"]) == len(drawn["terrain"]["ys"])
    assert len(drawn["terrain"]["heights"][0]) == len(drawn["terrain"]["xs"])
    assert drawn["road"] and drawn["anchors"]
    assert drawn["reach_m"] > 0.0


def test_the_scene_is_json_and_nothing_but_json():
    """It crosses a socket on every drag."""
    json.dumps(scene(a_state()))


def test_the_ground_mesh_covers_everything_the_sweep_will_cover():
    """Or coverage cells are painted beside the terrain rather than on it."""
    state = a_state(spacing_m=2000.0)
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
    assert scene(a_state(mounting="mast"))["reach_m"] > (
        scene(a_state(mounting="sign"))["reach_m"]
    )


def test_the_scene_reports_where_the_link_stops_decoding_beside_where_it_ranges():
    drawn = scene(a_state())
    assert drawn["closure_m"] > drawn["reach_m"]


@pytest.mark.slow
def test_simulating_from_the_viewer_gives_what_the_table_gives():
    result = simulate(a_state(journey_s=60.0, sweep_m=1000.0))
    assert result["hpe_p50_m"] > 0.0
    assert 0.0 < result["availability"] <= 1.0
    assert result["capex_tl"] > 0.0
    assert result["opex_tl_per_year"] > 0.0
    assert 0.0 < result["assumed_share"] <= 1.0


# --- The session ----------------------------------------------------------


def test_a_session_holds_one_state_and_hands_it_back():
    session = Session()
    assert session.read().spacing_m == 2000.0
    session.write(session.read().merged({"spacing_m": 900.0}))
    assert session.read().spacing_m == 900.0
