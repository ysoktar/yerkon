"""The study written out as files somebody can hand over."""

import pytest

from yerkon.deliver import budget_md, deliver, figures_md, options_md, table_md
from yerkon.report import build
from yerkon.scenarios import CHOICES
from yerkon.settings import DEFAULTS


def test_every_file_says_what_it_was_made_from_and_when():
    """A table nobody can date is a table nobody can check.

    The figures move — a measurement lands, a rate is quoted — and a
    delivered file that does not say which set it came from cannot be
    reconciled with the repository a month later.
    """
    body = figures_md(DEFAULTS)
    assert "# " in body.split("\n")[0]
    assert str(len(DEFAULTS.entries)) in body
    from datetime import date

    assert date.today().isoformat() in body


def test_the_figures_file_keeps_choices_apart_from_assumptions():
    """ADR-0023. They are different things and the delivery says so.

    A reader who counts anchor spacing among the placeholders concludes
    the study is more guesswork than it is, and stops trusting the number
    that says how much of it genuinely is.
    """
    body = figures_md(DEFAULTS)
    assert "Tasarım kararları ({})".format(len(DEFAULTS.choices)) in body
    assert "Hâlâ kimsenin sağlamadığı sayılar ({})".format(
        len(DEFAULTS.assumed)) in body
    for entry in DEFAULTS.choices:
        assert "`{}`".format(entry.key) in body


def test_the_options_file_lists_what_could_have_been_built_instead():
    body = options_md(DEFAULTS)
    for name in ("rural-dense", "rural-tall"):
        assert "`{}`".format(name) in body
    # And what each one moves, not only that it exists.
    assert "rural.anchor_spacing_m" in body


@pytest.mark.slow
def test_the_table_file_carries_the_rows_and_the_ground_under_them():
    """A row without its terrain is a row that cannot be reproduced.

    Two of the three stand on fetched Ankara and one on a bore through a
    real mountain; a delivery that omitted that would be four numbers
    with no way back to what produced them.
    """
    results, rows = build(tuple(CHOICES.values()))
    body = table_md(results, rows, DEFAULTS)

    for row in rows:
        assert row.system in body
    assert "Copernicus" in body
    assert "bore through" in body
    assert "ADR-0006" in body, "the OPEX column has to say where it came from"


@pytest.mark.slow
def test_writing_it_all_out_produces_files_that_can_be_read_back(tmp_path):
    written = deliver(
        tmp_path, (CHOICES["tunnel"],), DEFAULTS, with_budget=False
    )
    names = {one.path.name for one in written}
    assert {"tablo.md", "sayilar.md", "secenekler.md", "README.md"} == names

    for one in written:
        assert one.path.exists()
        assert one.about.strip(), one.path.name
        body = one.path.read_text(encoding="utf-8")
        assert body.startswith("# "), one.path.name
        assert body.endswith("\n")

    # The index names every other file, so a folder is navigable.
    index = (tmp_path / "README.md").read_text(encoding="utf-8")
    for one in written:
        if one.path.name != "README.md":
            assert one.path.name in index


@pytest.mark.slow
def test_the_error_budget_can_be_skipped_because_it_is_the_slow_part(tmp_path):
    """Somebody refreshing the table should not wait for the dissection."""
    quick = deliver(tmp_path, (CHOICES["tunnel"],), DEFAULTS, with_budget=False)
    assert "hata-butcesi.md" not in {one.path.name for one in quick}


@pytest.mark.slow
def test_the_error_budget_names_a_remedy_for_every_source(tmp_path):
    """A contribution nobody can act on is what ADR-0020 exists to fix."""
    from yerkon.budget import dissect_all
    from yerkon.terms import REMEDIES

    body = budget_md(dissect_all((CHOICES["tunnel"],), ("survey", "floor")),
                     DEFAULTS)
    assert REMEDIES["survey"] in body
    assert "Tek başına" in body and "Kalkarsa" in body
