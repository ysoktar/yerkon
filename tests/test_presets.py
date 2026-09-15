"""Named arrangements: saving a tab, loading it back, and running one.

The thing that must not happen here is an arrangement that means one
thing on screen and another after a round trip through a file. It
happened once — a tab saved with twelve anchors came back with nine —
and both halves of that are pinned below.
"""

import json

import pytest

from yerkon.presets import (
    CLEARED,
    SHIPPED,
    Preset,
    PresetStore,
    UnknownPreset,
    empty_state,
    offered,
    shipped,
)
from yerkon.viewer.state import ViewState, from_scenario


# --- What a name may be ---------------------------------------------------


@pytest.mark.parametrize("name", ["konya", "D100", "bolu-dagi", "a_b", "Ğüéş"])
def test_a_name_somebody_would_actually_type_is_allowed(name):
    assert Preset(name=name, mode="rural").name == name


@pytest.mark.parametrize("name", ["", "../etc", "a/b", ".hidden", "-lead",
                                  "x" * 65, "boş ad"])
def test_a_name_that_would_escape_the_folder_is_refused(name):
    """It becomes a file on somebody's disk, so it is checked like a site
    name is and for the same reason."""
    with pytest.raises(ValueError, match="düzenleme adı|arrangement name"):
        Preset(name=name, mode="rural")


# --- The hash, which is why a preset may drive a published row -----------


def test_the_hash_follows_the_contents_and_not_the_file():
    """`--preset` makes a printed row rest on a file somebody saved, so
    the row says which file *and which version of it* (ADR-0043). A hash
    that moved when the file was reformatted would be no use for that,
    and one that stayed put when a number changed would be worse."""
    state = {"corridor_m": 3000.0, "runs": [{"identifier": "A"}]}
    one = Preset(name="a", mode="rural", state=state)

    same_other_order = Preset(name="a", mode="rural",
                              state=dict(reversed(list(state.items()))))
    assert one.digest == same_other_order.digest

    edited = Preset(name="a", mode="rural",
                    state={**state, "corridor_m": 3001.0})
    assert one.digest != edited.digest


def test_reformatting_the_file_is_not_a_different_arrangement(tmp_path):
    store = PresetStore(tmp_path)
    store.write(Preset(name="a", mode="rural", state={"corridor_m": 3000.0}))
    was = store.read("a").digest

    path = tmp_path / "a.json"
    path.write_text(json.dumps(json.loads(path.read_text()), indent=8,
                               sort_keys=True) + "\n\n", encoding="utf-8")
    assert store.read("a").digest == was


def test_what_a_row_says_about_the_arrangement_that_drove_it(tmp_path):
    store = PresetStore(tmp_path)
    store.write(Preset(name="konya", mode="rural", state={"seed": 3}))
    said = store.read("konya").describe()
    assert "konya" in said and "rural" in said
    assert store.read("konya").digest in said
    assert str(tmp_path) in said, "which file, not just which name"


# --- The folder -----------------------------------------------------------


def test_saving_and_reading_one_back(tmp_path):
    store = PresetStore(tmp_path)
    written = store.write(Preset(name="mine", mode="urban",
                                 state={"corridor_m": 1234.0}))
    assert written.exists()
    assert store.names() == ("mine",)
    assert store.read("mine").state["corridor_m"] == 1234.0


def test_nothing_is_written_until_something_is_saved(tmp_path):
    """Somebody who never saves one never grows a folder they did not
    ask for."""
    store = PresetStore(tmp_path / "never")
    assert store.names() == ()
    assert not (tmp_path / "never").exists()


def test_asking_for_one_that_is_not_there_lists_the_ones_that_are(tmp_path):
    store = PresetStore(tmp_path)
    store.write(Preset(name="here", mode="rural"))
    with pytest.raises(UnknownPreset, match="here"):
        store.read("elsewhere")


def test_a_file_edited_into_nonsense_does_not_hide_the_others(tmp_path):
    """Listing the rest beats refusing to list anything."""
    store = PresetStore(tmp_path)
    store.write(Preset(name="good", mode="rural", state={"seed": 1}))
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")

    names = [p.name for p in offered("rural", store, from_scenario)]
    assert "good" in names
    assert "broken" not in names
    assert list(SHIPPED) == names[:2], "the shipped two come first"


def test_saving_over_a_name_replaces_it_rather_than_merging(tmp_path):
    """"Save as" over the name you just loaded is how somebody iterates,
    and half of one arrangement over half of another is not a thing
    anybody wants."""
    store = PresetStore(tmp_path)
    store.write(Preset(name="x", mode="rural", state={"seed": 1, "gone": 2}))
    store.write(Preset(name="x", mode="rural", state={"seed": 9}))
    assert store.read("x").state == {"seed": 9}


# --- What the two shipped ones are ---------------------------------------


@pytest.mark.parametrize("mode", ["urban", "rural", "tunnel"])
def test_the_empty_one_is_this_rows_own_ground_with_nothing_on_it(mode):
    """A blank sheet rather than a blank slate.

    The urban row stands on Kızılay and the tunnel row goes through a
    mountain; somebody loading the empty urban arrangement is building an
    urban arrangement, on urban ground. An earlier version left the
    extent alone, so "empty" inherited the shape of whatever it replaced
    and was a different thing each time it was loaded.
    """
    blank = empty_state(mode, from_scenario)
    full = from_scenario(mode)

    for key, nothing in CLEARED.items():
        assert blank[key] == nothing, key
    assert blank["site"] == full.site
    assert blank["corridor_m"] == full.corridor_m
    assert blank["width_m"] == full.width_m
    assert blank["scenario"] == mode


@pytest.mark.parametrize("mode", ["urban", "rural", "tunnel"])
def test_the_default_one_is_the_row_as_it_ships(mode):
    assert shipped(mode, "default", from_scenario).state == \
        from_scenario(mode).as_json()


def test_the_shipped_two_are_not_files(tmp_path):
    """They are how somebody gets back to a known starting point, so
    they exist whether or not anybody has a presets folder."""
    names = [p.name for p in offered("urban", PresetStore(tmp_path),
                                     from_scenario)]
    assert names == list(SHIPPED)
    assert not any(tmp_path.iterdir())


# --- The round trip, which is the whole point ----------------------------


def test_an_arrangement_comes_back_as_the_arrangement_it_was_saved_as(tmp_path):
    """The bug this is here for: a tab saved with twelve anchors loaded
    with nine.

    Loading brings a site inside the ground that was measured for it
    (ADR-0037) and must not do more than that. Clipping each run to the
    site as well would make one saved arrangement mean two different
    things depending on whether it came from a file — this project has
    already decided a run's own typed end is the person being explicit
    about that run.
    """
    server, session = _a_running_viewer(tmp_path)

    state = session.read()
    # A run reaching past the end of the site, which is what the page
    # used to build and what a person may still type on purpose.
    stretched = state.merged({"runs": [
        {**run.as_json(), "to_m": state.corridor_m + 400.0}
        for run in state.runs
    ]})
    session.write(stretched)
    before = len(stretched.anchors(stretched.terrain()))

    server._save_preset("round")
    server._load_preset("default")          # go somewhere else first
    server._load_preset("round")

    back = session.read()
    assert len(back.anchors(back.terrain())) == before


def test_loading_carries_the_tab_and_not_the_row_it_was_saved_from():
    """An arrangement built on the rural row is often exactly what
    somebody wants to look at on the urban one. Which row it *runs* as is
    decided by the tab it is loaded into."""
    rural = Preset(name="r", mode="rural", state=from_scenario("rural").as_json())
    carried = {key: value for key, value in rural.state.items()
               if key not in ("scenario", "language")}
    urban = from_scenario("urban").merged(carried)
    assert urban.scenario == "urban"


def test_an_arrangement_holds_the_things_that_are_easy_to_lose():
    """Anchors moved by hand, anchors deleted, and figures edited away
    from the shipped file — an afternoon's work that lives nowhere else."""
    state = from_scenario("urban").merged({
        "moved": {"C0": (12.0, 34.0)},
        "removed": ("C1",),
        "overrides": {"mounting.tall_mast.height_m": 30.0},
    })
    saved = Preset(name="afternoon", mode="urban", state=state.as_json())
    back = ViewState().merged(saved.state)

    assert back.moved == {"C0": (12.0, 34.0)}
    assert back.removed == ("C1",)
    assert back.overrides["mounting.tall_mast.height_m"] == 30.0


def _a_running_viewer(directory):
    """The real handler with a real session, minus the socket.

    Through the server rather than around it: the question is what the
    viewer does when somebody presses Load, and a test that re-implements
    the loading is a test of the re-implementation.
    """
    import yerkon.viewer.server as server_module

    server_module.PRESETS[0] = PresetStore(directory)
    session = server_module.Session()

    class Bare(server_module.Handler):
        def __init__(self):
            self.session = session

    return Bare(), session


def test_loading_still_brings_a_site_inside_the_ground_measured_for_it(tmp_path):
    """The one thing loading *is* allowed to change (ADR-0037).

    A saved arrangement can name a site larger than the grid fetched for
    it — by hand, or from a fetch that was redone smaller since. Standing
    anchors out there puts them on the boundary row extruded into a
    plane, which is the most favourable ground this project can draw.
    """
    server, session = _a_running_viewer(tmp_path)
    server._load_preset("default")
    measured = session.read().corridor_m

    session.write(session.read().merged({"corridor_m": measured * 3}))
    server._save_preset("toobig")
    server._load_preset("toobig")
    assert session.read().corridor_m == pytest.approx(measured)


# --- Driving a published row ---------------------------------------------


def test_a_preset_replaces_the_row_it_was_saved_from(tmp_path):
    """Matched by the row's key rather than by its title.

    A row's `name` is a sentence in whichever language the run is in —
    "Kırsal" or "Rural" — so matching on it would work in Turkish and
    quietly stop working in English.
    """
    from types import SimpleNamespace

    from yerkon.cli import _with_presets
    from yerkon.scenarios import catalogue

    store = PresetStore(tmp_path)
    store.write(Preset(name="mine", mode="rural",
                       state=from_scenario("rural").as_json()))

    available = catalogue()
    keys = list(available)
    rows = tuple(available[key] for key in keys)
    swapped, used = _with_presets(
        keys, rows,
        SimpleNamespace(preset=["mine"], presets=str(tmp_path)))

    assert [p.name for p in used] == ["mine"]
    where = keys.index("rural")
    assert swapped[where] is not rows[where], "the rural row was replaced"
    for other in range(len(keys)):
        if other != where:
            assert swapped[other] is rows[other], "and nothing else was"


def test_a_preset_for_a_row_this_table_is_not_running_says_so(tmp_path):
    """Rather than silently landing on whichever row came first."""
    from types import SimpleNamespace

    from yerkon.cli import _with_presets
    from yerkon.scenarios import catalogue

    store = PresetStore(tmp_path)
    store.write(Preset(name="mine", mode="tunnel",
                       state=from_scenario("tunnel").as_json()))

    with pytest.raises(ValueError, match="tunnel"):
        _with_presets(["urban"], (catalogue()["urban"],),
                      SimpleNamespace(preset=["mine"], presets=str(tmp_path)))


def test_no_preset_leaves_the_table_exactly_as_it_was(tmp_path):
    from types import SimpleNamespace

    from yerkon.cli import _with_presets
    from yerkon.scenarios import catalogue

    rows = tuple(catalogue().values())
    swapped, used = _with_presets(
        list(catalogue()), rows,
        SimpleNamespace(preset=None, presets=str(tmp_path)))
    assert swapped == rows and used == ()


def test_the_notes_name_the_arrangement_and_which_version_of_it(tmp_path):
    """A row that rests on a file somebody saved has to say which file
    and which version, or two runs print the same provenance for two
    different tables (ADR-0001)."""
    from yerkon.report import footnotes

    store = PresetStore(tmp_path)
    store.write(Preset(name="konya", mode="rural", state={"seed": 7}))
    preset = store.read("konya")

    said = footnotes((), (), (preset,))
    assert "konya" in said
    assert preset.digest in said
    assert "scenarios.py" in said, "and that this is not a shipped scenario"

    # Without one, the table says nothing about arrangements at all.
    assert "konya" not in footnotes((), ())


def test_an_empty_arrangement_reports_no_number_rather_than_a_wrong_one():
    """Zero looked safer than absent and was not.

    The panel divides the round by itself to get fixes a second, so a
    round of zero printed "1000000000,00 /s" — a number that looks like a
    finding and is a division by nothing — and the covered areas came out
    NaN. There is no round when nothing takes a turn, and nothing covers
    any ground when there is nothing to cover it.
    """
    from yerkon.viewer.scene import scene, sweep

    blank = empty_state("urban", from_scenario)
    state = ViewState().merged({k: v for k, v in blank.items()
                                if k != "scenario"})

    assert scene(state)["round_s"] is None
    swept = sweep(state)
    assert swept["served_km2"] is None
    assert swept["reached_km2"] is None
    assert swept["counts"] == []

    # And the row as it ships still reports real ones, so this did not
    # turn every number into a dash.
    full = from_scenario("urban")
    assert scene(full)["round_s"] > 0.0
