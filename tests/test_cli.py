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


# --- The assumptions verb --------------------------------------------------


def test_the_assumptions_verb_lists_every_figure_nobody_supplied(capsys):
    from yerkon.cli import assumptions

    assert assumptions([]) == 0
    printed = capsys.readouterr().out
    assert "still assumptions" in printed
    assert "mounting.tall_mast.site_cost_tl" in printed
    assert "affects:" in printed


def test_the_assumptions_verb_says_how_to_replace_one(capsys):
    from yerkon.cli import assumptions

    assumptions([])
    printed = capsys.readouterr().out
    assert "change provenance from ASSUMPTION" in printed
    assert "--assumptions" in printed


def test_the_assumptions_verb_can_list_what_has_been_sourced(capsys, tmp_path):
    import pathlib

    from yerkon.cli import assumptions
    from yerkon.settings import DEFAULT_FILE

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
    path = tmp_path / "sourced.toml"
    path.write_text(text, encoding="utf-8")

    assert assumptions(["--file", str(path), "--sourced"]) == 0
    printed = capsys.readouterr().out
    assert "mounting.tall_mast.site_cost_tl" in printed


def test_a_missing_assumptions_file_is_refused_with_a_message(capsys):
    from yerkon.cli import assumptions

    assert assumptions(["--file", "/nowhere/at/all.toml"]) == 2
    assert "Copy" in capsys.readouterr().err


def test_the_help_lists_the_assumptions_verb(capsys):
    from yerkon.cli import main

    main([])
    assert "yerkon assumptions" in capsys.readouterr().out
