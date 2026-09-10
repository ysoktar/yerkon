"""Every figure nobody supplied, in one file rather than in the code."""

import pathlib

import pytest

from yerkon.evidence import Provenance
from yerkon.settings import DEFAULT_FILE, DEFAULTS, REQUIRED, load

COMPLETE = """
[values."a.thing"]
value = 1.5
unit = "m"
provenance = "ASSUMPTION"
source = "this project"
note = "a note"
affects = "something"
"""


def write(tmp_path, text, name="settings.toml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


# --- Loading --------------------------------------------------------------


def test_the_shipped_file_loads_and_holds_every_kind_of_figure():
    keys = set(DEFAULTS.entries)
    for prefix in ("mounting.", "operating.", "radio.", "clock.", "ranging.",
                   "site.", "estimator."):
        assert any(key.startswith(prefix) for key in keys), prefix


def test_a_missing_file_says_what_to_copy(tmp_path):
    with pytest.raises(FileNotFoundError, match="Copy"):
        load(str(tmp_path / "nowhere.toml"))


def test_a_file_that_is_not_toml_says_so(tmp_path):
    with pytest.raises(ValueError, match="not valid TOML"):
        load(write(tmp_path, "this is not = = toml"))


def test_a_file_with_no_values_says_what_it_is_for(tmp_path):
    with pytest.raises(ValueError, match="list of every"):
        load(write(tmp_path, "[something]\nelse = 1\n"))


@pytest.mark.parametrize("field", REQUIRED)
def test_an_incomplete_entry_is_refused_rather_than_filled_in(tmp_path, field):
    """A figure with no note or no `affects` is a figure nobody can replace."""
    lines = [line for line in COMPLETE.splitlines()
             if not line.startswith(field + " ")]
    with pytest.raises(ValueError, match=field):
        load(write(tmp_path, "\n".join(lines)))


def test_an_unknown_provenance_lists_the_ones_that_exist(tmp_path):
    text = COMPLETE.replace('"ASSUMPTION"', '"VIBES"')
    with pytest.raises(ValueError, match="DATASHEET"):
        load(write(tmp_path, text))


def test_a_figure_the_code_asks_for_and_the_file_lacks_is_an_error(tmp_path):
    """Never a default. A missing figure is a hole, not a zero."""
    settings = load(write(tmp_path, COMPLETE))
    with pytest.raises(KeyError, match="nothing may be assumed in the code"):
        settings.number("a.thing.that.is.not.there")


# --- Sourcing one ---------------------------------------------------------


def test_the_shipped_figures_are_all_still_assumptions():
    """If this ever fails, somebody sourced one, which is the point."""
    assert DEFAULTS.assumed_share > 0.0
    for entry in DEFAULTS.assumed:
        assert entry.sourced.provenance is Provenance.ASSUMPTION


def test_sourcing_a_figure_stops_it_counting_as_an_assumption(tmp_path):
    """Three edits in one place: the value, the source, the provenance."""
    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        '''[values."mounting.tall_mast.site_cost_tl"]
value = 85000.0
unit = "TL"
provenance = "ASSUMPTION"
source = "this project"''',
        '''[values."mounting.tall_mast.site_cost_tl"]
value = 5000.0
unit = "TL"
provenance = "MEASUREMENT"
source = "a quotation"''',
    )
    settings = load(write(tmp_path, text))

    assert settings.number("mounting.tall_mast.site_cost_tl") == 5000.0
    assert not settings.entry("mounting.tall_mast.site_cost_tl").is_assumed
    assert len(settings.assumed) == len(DEFAULTS.assumed) - 1
    assert settings.assumed_share < DEFAULTS.assumed_share


# --- What reads it --------------------------------------------------------


def test_the_mounting_catalogue_is_built_from_the_file(tmp_path):
    from yerkon.world import mountings

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        "value = 85000.0", "value = 1234.0"
    )
    rebuilt = mountings(load(write(tmp_path, text)))
    assert float(rebuilt["tall_mast"].site_cost_tl.value) == 1234.0


def test_the_operating_rates_are_built_from_the_file(tmp_path):
    from yerkon.cost import operating_rates

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        "value = 1800.0", "value = 99.0"
    )
    rebuilt = operating_rates(load(write(tmp_path, text)))
    assert float(rebuilt.maintenance_tl_per_visit.value) == 99.0


def test_the_radios_take_their_unpublished_figures_from_the_file(tmp_path):
    from yerkon.hardware import radios

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        '''[values."radio.sx1280.noise_figure_db"]
value = 6.0''',
        '''[values."radio.sx1280.noise_figure_db"]
value = 9.0''',
    )
    rebuilt = radios(load(write(tmp_path, text)))
    assert float(rebuilt["sx1280"].noise_figure_db.value) == 9.0


def test_the_clocks_take_theirs_from_the_file(tmp_path):
    from yerkon.ranging import clocks

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        '''[values."clock.crystal.residual_ppm"]
value = 0.5''',
        '''[values."clock.crystal.residual_ppm"]
value = 3.0''',
    )
    rebuilt = clocks(load(write(tmp_path, text)))
    assert float(rebuilt["crystal"].residual_ppm.value) == 3.0


def test_a_worse_noise_figure_shortens_every_link(tmp_path):
    """The file is not decoration: the physics moves when it moves."""
    from yerkon.hardware import radios
    from yerkon.rf import Terminal, usable_range_m
    from yerkon.hardware import W24P_U

    def reach(noise_db):
        text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
            '''[values."radio.sx1280.noise_figure_db"]
value = 6.0''',
            '''[values."radio.sx1280.noise_figure_db"]
value = {}'''.format(noise_db),
        )
        radio = radios(load(write(tmp_path, text, "n{}.toml".format(noise_db))))["sx1280"]
        anchor = Terminal(radio, W24P_U, (0.0, 0.0, 25.0))
        receiver = Terminal(radio, W24P_U, (0.0, 0.0, 1.5))
        return usable_range_m(anchor, receiver, radio, target_sigma_m=5.0)

    assert reach(12.0) < reach(6.0)


def test_the_scenarios_are_rebuilt_from_the_file(tmp_path):
    from yerkon.scenarios import catalogue

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        '''[values."mounting.lighting_column.height_m"]
value = 12.0''',
        '''[values."mounting.lighting_column.height_m"]
value = 20.0''',
    )
    rebuilt = catalogue(load(write(tmp_path, text)))
    column = rebuilt["urban"].scenario.deployment.anchors[0].mounting
    assert float(column.height_m.value) == 20.0
