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
