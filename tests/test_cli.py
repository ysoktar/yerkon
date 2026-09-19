"""The command line, which is one of two front ends over the same engine."""

import pytest

from yerkon.cli import design, describe_outcome, main
from yerkon.design import Design


def test_design_with_no_edits_reports_what_the_settings_imply(capsys):
    assert design([]) == 0
    printed = capsys.readouterr().out
    assert "usable range" in printed
    assert "5,52 km" in printed


def test_an_edit_shows_the_panel_before_applying_anything(capsys):
    assert design(["--mounting", "sign", "--yes"]) == 0
    printed = capsys.readouterr().out
    assert "You asked to change:" in printed
    assert "Which also changes:" in printed
    assert printed.index("You asked to change:") < printed.index("Applying")


def test_a_refused_edit_changes_nothing(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert design(["--mounting", "sign"]) == 0
    assert "Nothing changed." in capsys.readouterr().out


def test_an_accepted_edit_reports_the_settings_it_leaves_behind(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert design(["--mounting", "sign"]) == 0
    printed = capsys.readouterr().out
    assert "roadside sign" in printed.split("Settings:")[-1]


def test_an_unknown_name_is_refused_with_the_alternatives(capsys):
    assert design(["--mounting", "lamppost"]) == 2
    assert "Choose one of" in capsys.readouterr().err


def test_an_impossible_tolerance_is_refused_rather_than_crashing(capsys):
    assert design(["--tolerance", "0"]) == 2
    assert "tolerance of zero" in capsys.readouterr().err


def test_the_help_lists_both_verbs(capsys):
    assert main([]) == 0
    printed = capsys.readouterr().out
    assert "yerkon fetch" in printed
    assert "yerkon design" in printed


def test_an_unknown_verb_is_an_error(capsys):
    assert main(["simulate"]) == 2
    assert "Unknown command" in capsys.readouterr().err


def test_the_outcome_description_uses_the_panel_wording():
    """Two renderings of the same number that disagree is worse than one."""
    printed = describe_outcome(Design())
    assert "legal radiated power" in printed
    assert "12,1 dBm" in printed


# --- The table verb --------------------------------------------------------


def test_the_help_lists_the_table_verb(capsys):
    from yerkon.cli import main

    main([])
    assert "yerkon table" in capsys.readouterr().out


@pytest.mark.slow
def test_the_table_verb_prints_the_columns_the_report_has(capsys):
    from yerkon.cli import table

    assert table(["--only", "tunnel"]) == 0
    printed = capsys.readouterr().out
    assert "Sistem" in printed
    assert "OPEX [TL/km²/yıl]" in printed
    assert "Notes:" in printed


@pytest.mark.slow
def test_the_table_verb_can_leave_the_notes_out(capsys):
    from yerkon.cli import table

    assert table(["--only", "tunnel", "--no-notes", "--markdown"]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("| Sistem")
    assert "Notes:" not in printed


# --- Reading it coarsely, for trying things (ADR-0063) ------------------


@pytest.mark.slow
def test_fast_runs_the_same_study_read_coarsely_and_says_so(capsys):
    """The whole point of the flag is that it is not publishable, so the
    line saying that is checked rather than the speed, which a busy
    machine would make flaky."""
    from yerkon.cli import table

    assert table(["--only", "tunnel", "--fast"]) == 0
    printed = capsys.readouterr().out
    assert "Sistem" in printed
    assert "read coarsely for speed" in printed
    assert "not the published ones" in printed
    # Which way it is wrong, not only that it is.
    assert "flatters the deployment" in printed


@pytest.mark.slow
def test_a_run_that_is_not_fast_says_nothing_about_being_coarse(capsys):
    """Otherwise the warning is furniture and stops being read."""
    from yerkon.cli import table

    assert table(["--only", "tunnel"]) == 0
    assert "read coarsely for speed" not in capsys.readouterr().out


@pytest.mark.slow
def test_turning_the_notes_off_does_not_turn_the_warning_off(capsys):
    """It is about the table above rather than about what the table
    rests on, so `--no-notes` does not take it with them."""
    from yerkon.cli import table

    assert table(["--only", "tunnel", "--fast", "--no-notes"]) == 0
    said = capsys.readouterr()
    assert "Notes:" not in said.out
    assert "read coarsely for speed" in said.err


def test_fast_reaches_the_figures_the_run_uses():
    """Through the one funnel every verb takes its settings from, so a
    verb added later gets the flag by taking that funnel."""
    import argparse

    from yerkon.cli import _settings_from
    from yerkon.settings import is_hurried

    plain = argparse.Namespace(defaults=None, option=None, fast=False)
    assert _settings_from(plain) is None

    quick = argparse.Namespace(defaults=None, option=None, fast=True)
    assert is_hurried(_settings_from(quick))


def test_fast_wins_over_a_file_that_set_the_same_figures(tmp_path):
    """Asking for speed and being given a quarter of an hour anyway is
    the one thing this flag must not do, so it is applied last."""
    import argparse

    from yerkon.cli import _settings_from
    from yerkon.settings import DEFAULTS, is_hurried

    slow = tmp_path / "slow.toml"
    slow.write_text(DEFAULTS.with_values({
        "site.shadow_draws": 8.0, "site.profile_spacing_m": 10.0,
    }).to_toml(), encoding="utf-8")

    asked = argparse.Namespace(defaults=str(slow), option=None, fast=False)
    assert not is_hurried(_settings_from(asked))

    asked.fast = True
    assert is_hurried(_settings_from(asked))


# --- The defaults verb --------------------------------------------------


def test_the_defaults_verb_lists_every_figure_nobody_supplied(capsys):
    from yerkon.cli import defaults

    assert defaults([]) == 0
    printed = capsys.readouterr().out
    assert "still assumptions" in printed
    assert "mounting.tall_mast.site_cost_tl" in printed
    assert "affects:" in printed


def test_the_defaults_verb_says_how_to_replace_one(capsys):
    from yerkon.cli import defaults

    defaults([])
    printed = capsys.readouterr().out
    assert "change provenance from ASSUMPTION" in printed
    assert "--defaults" in printed


def test_the_defaults_verb_can_list_what_has_been_sourced(capsys, tmp_path):
    import pathlib

    from yerkon.cli import defaults
    from yerkon.settings import DEFAULT_FILE

    text = pathlib.Path(DEFAULT_FILE).read_text(encoding="utf-8").replace(
        '''[values."mounting.tall_mast.site_cost_tl"]
value = 85000.0
unit = "TL"
provenance = "ASSUMPTION"
source = "bu proje"''',
        '''[values."mounting.tall_mast.site_cost_tl"]
value = 5000.0
unit = "TL"
provenance = "MEASUREMENT"
source = "a quotation"''',
    )
    path = tmp_path / "sourced.toml"
    path.write_text(text, encoding="utf-8")

    assert defaults(["--file", str(path), "--sourced"]) == 0
    printed = capsys.readouterr().out
    assert "mounting.tall_mast.site_cost_tl" in printed


def test_a_missing_defaults_file_is_refused_with_a_message(capsys):
    from yerkon.cli import defaults

    assert defaults(["--file", "/nowhere/at/all.toml"]) == 2
    assert "Copy" in capsys.readouterr().err


def test_the_help_lists_the_defaults_verb(capsys):
    from yerkon.cli import main

    main([])
    assert "yerkon defaults" in capsys.readouterr().out
