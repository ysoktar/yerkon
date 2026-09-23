"""The site in front of the simulator.

Two things get checked here that nothing else can. Every phrase is in
both languages, the same promise the panel keeps (ADR-0035). And the
four rows on the results page come out of the published record rather
than out of a copy somebody typed, which is the whole reason the record
exists (ADR-0064).
"""

from __future__ import annotations

import dataclasses
import html
import pathlib
import re

import pytest

from yerkon.published import EVERY_ROW, Published, read, write
from yerkon.report import Row
from yerkon.viewer.pages import (
    COLUMNS,
    PAGES,
    SIMULATOR,
    Words,
    page_at,
    render,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC = ROOT / "src/yerkon/viewer/static"
TURKISH = re.compile(r"[çğıöşüÇĞİÖŞÜ]")


def every_phrase():
    """Every Words the site holds, with where it was found.

    The module's own names rather than the pages alone. The standfirst,
    the column heads and the line under the table are drawn on every
    page, and a walk through PAGES does not reach any of them: that
    walk said the site was whole while its English standfirst was in
    Turkish.
    """
    import yerkon.viewer.pages as module

    for name, value in sorted(vars(module).items()):
        if name.startswith("_"):
            continue
        for found in _phrases(value):
            yield name, found


def _phrases(thing):
    if isinstance(thing, Words):
        return [thing]
    if isinstance(thing, dict):
        out = []
        for one in thing.values():
            out += _phrases(one)
        return out
    if dataclasses.is_dataclass(thing) and not isinstance(thing, type):
        out = []
        for field in dataclasses.fields(thing):
            out += _phrases(getattr(thing, field.name))
        return out
    if isinstance(thing, (tuple, list)):
        out = []
        for one in thing:
            out += _phrases(one)
        return out
    return []


# --- both languages -------------------------------------------------------


def test_every_phrase_the_site_says_is_in_both_languages():
    for where, phrase in every_phrase():
        assert phrase.tr.strip(), "{}: empty Turkish".format(where)
        assert phrase.en.strip(), "{}: {}".format(where, phrase.tr)


def test_nothing_turkish_was_left_standing_in_the_english():
    """A phrase carrying ı, ş or ğ and copied across was never translated.

    A part number is the same in both and says so by holding no Turkish
    letter, so this catches the copied sentence without catching
    `E28-2G4M27S`.
    """
    for where, phrase in every_phrase():
        if TURKISH.search(phrase.tr):
            assert phrase.en != phrase.tr, "{}: {}".format(where, phrase.tr)


def test_the_way_back_from_the_simulator_is_in_both_languages():
    words = (STATIC / "words.js").read_text(encoding="utf-8")
    assert '"back.site"' in words
    line = words[words.index('"back.site"'):][:120]
    assert "tr:" in line and "en:" in line
    assert 'data-say="back.site"' in (
        STATIC / "simulator.html").read_text(encoding="utf-8")


def test_a_page_is_drawn_in_the_language_it_was_asked_for():
    home = page_at("/")
    assert home.lead.tr in render(home, "tr")
    assert home.lead.en in render(home, "en")
    assert home.lead.tr not in render(home, "en")


# --- moving around --------------------------------------------------------


def test_every_page_has_its_own_address():
    slugs = [page.slug for page in PAGES]
    assert len(slugs) == len(set(slugs))
    for slug in slugs:
        assert page_at("/" + slug) is not None


def test_every_page_carries_the_whole_navigation_and_the_way_in():
    """Arriving anywhere reaches everywhere, including the simulator."""
    for page in PAGES:
        drawn = render(page, "tr")
        for other in PAGES:
            assert 'href="/{}"'.format(other.slug) in drawn, other.slug
        assert 'href="{}"'.format(SIMULATOR) in drawn


def test_the_site_links_to_nothing_the_server_does_not_serve():
    """A dead link is a dead page and no Python failure."""
    routing = (ROOT / "src/yerkon/viewer/server.py").read_text(encoding="utf-8")
    wanted = set()
    for page in PAGES:
        drawn = render(page, "tr")
        wanted |= set(re.findall(r'(?:href|src)="([^"]+)"', drawn))
    for reference in sorted(wanted):
        if reference.startswith("http"):
            continue
        if reference.startswith("#"):
            continue
        address = reference.split("?")[0]
        if address == SIMULATOR:
            assert (STATIC / "simulator.html").exists()
        elif address.rsplit(".", 1)[-1] in ("css", "js", "png"):
            # On disk, and routed: a picture the server does not serve is
            # a broken image on a page that otherwise looks finished.
            assert (STATIC / address.lstrip("/")).exists(), reference
            assert '"{}"'.format(address) in routing, reference
        else:
            assert page_at(address) is not None, reference
    assert '"/site.css"' in routing


def test_the_simulator_is_served_where_the_pages_point_at_it():
    routing = (ROOT / "src/yerkon/viewer/server.py").read_text(encoding="utf-8")
    assert "SIMULATOR" in routing
    assert '"simulator.html"' in routing
    assert not (STATIC / "index.html").exists(), (
        "the simulator moved off /; a leftover index.html would be served "
        "at the site's own address"
    )


def test_the_running_simulator_does_not_sit_on_a_page_of_the_site():
    """Both were called "simulation" once, and both wanted /simulasyon.

    The server answers SIMULATOR before it looks a page up, so a page
    whose slug matched it could never be reached (ADR-0071).
    """
    from yerkon.viewer.pages import SIMULATOR

    taken = SIMULATOR.strip("/")
    clash = [page.slug for page in PAGES if page.slug == taken]
    assert not clash, (
        "{} is both the running simulator and the {} page; the page would "
        "never be served".format(SIMULATOR, clash[0])
    )


def test_the_link_into_the_simulator_and_the_page_about_it_read_apart():
    """One explains the simulation, the other runs it."""
    from yerkon.viewer.pages import SIMULATION, SIMULATOR_LABEL

    for language in ("tr", "en"):
        assert (SIMULATOR_LABEL.said(language)
                != SIMULATION.nav.said(language)), language


def test_asking_for_a_page_that_is_not_there_is_not_a_page():
    assert page_at("/yok") is None
    assert page_at("/api/scene") is None


# --- the numbers ----------------------------------------------------------


def a_record(**changes) -> Published:
    """A published record with numbers no real run would produce."""
    rows = []
    for at, key in enumerate(EVERY_ROW):
        rows.append(Row(
            system="YERKON ({})".format(key),
            technology="Karasal konumlandırma",
            environment="Dış",
            hpe_p50_m=90.0 + at,
            hpe_p95_m=91.0 + at,
            vpe_p95_m=92.0 + at,
            availability=0.9375,
            area_km2=93.0 + at,
            capex_tl_per_unit=94000.0 + at,
            opex_tl_per_unit_year=95000.0 + at,
            # The real record's tunnel row is priced by its length
            # (ADR-0073). A synthetic one where every row is an area
            # never walks the path the real one takes.
            costed_by="route" if key == "tunnel" else "area",
            reached_km2=96.0 + at,
            assumed_share=0.5,
        ))
    held = dict(
        run_on="2026-01-02", source="defaults.toml", shadow_draws=8,
        profile_spacing_m=10.0, rows=tuple(rows), keys=EVERY_ROW,
    )
    held.update(changes)
    return Published(**held)


def test_the_results_page_draws_the_published_run():
    drawn = render(page_at("/sonuclar"), "tr", a_record())
    for expected in ("90,00", "91,00", "93,00", "%93,75", "94000"):
        assert expected in drawn, expected
    assert "2026-01-02" in drawn


def test_the_home_page_leads_with_one_figure_per_row():
    """ADR-0068. There is no weighted row to lead with any more."""
    record = a_record()
    drawn = render(page_at("/"), "tr", record)
    for key in EVERY_ROW:
        shown = "{:.2f}".format(record.row(key).hpe_p95_m).replace(".", ",")
        assert shown in drawn, key


def test_no_page_carries_a_copy_of_the_published_table():
    """The site cannot drift from the run unless it holds its own copy.

    So it is drawn with no record at all and searched for every number
    the published run produced. A cell quoted in a sentence is the copy
    that goes stale on the run after next, and prose that explains a
    finding without restating a cell does not.
    """
    record = read()
    typed = {cell for row in record.rows for cell in row.cells()[3:]}
    for page in PAGES:
        drawn = render(page, "tr", None) + render(page, "en", None)
        for cell in sorted(typed):
            # On its own rather than inside a longer number: 0,02 and
            # 0,024 are different figures and only one of them is a cell.
            found = re.search(
                r"(?<![\d,%]){}(?![\d,])".format(re.escape(cell)), drawn
            )
            assert not found, "{} quotes the published {}".format(
                "/" + page.slug, cell
            )
    results = render(page_at("/sonuclar"), "tr", None)
    assert "yerkon table --publish" in results


def test_the_published_record_says_how_finely_it_was_read():
    """A coarse table and a published one look the same in a file."""
    drawn = render(page_at("/sonuclar"), "tr", a_record())
    assert "8" in drawn and "defaults.toml" in drawn


# --- the record itself ----------------------------------------------------


def test_a_record_survives_being_written_and_read(tmp_path):
    record = a_record()
    path = tmp_path / "published.toml"
    write(
        rows=record.rows, keys=record.keys, source=record.source,
        shadow_draws=record.shadow_draws,
        profile_spacing_m=record.profile_spacing_m, path=path,
    )
    back = read(path)
    assert back.keys == EVERY_ROW
    assert back.source == record.source
    for before, after in zip(record.rows, back.rows):
        assert before.cells() == after.cells()
        assert before.reached_km2 == after.reached_km2


def test_a_coarse_run_is_not_published(tmp_path):
    """ADR-0063. A fast answer flatters the deployment."""
    record = a_record()
    for draws, spacing in ((1, 10.0), (8, 0.0)):
        with pytest.raises(ValueError, match="coarse"):
            write(
                rows=record.rows, keys=record.keys, source="defaults.toml",
                shadow_draws=draws, profile_spacing_m=spacing,
                path=tmp_path / "published.toml",
            )
    assert not (tmp_path / "published.toml").exists()


def test_a_table_missing_a_row_is_not_published(tmp_path):
    record = a_record()
    with pytest.raises(ValueError, match="a row per deployment"):
        write(
            rows=record.rows[:2], keys=record.keys[:2], source="defaults.toml",
            shadow_draws=8, profile_spacing_m=10.0,
            path=tmp_path / "published.toml",
        )


def test_the_rows_are_written_in_the_order_the_table_prints_them(tmp_path):
    record = a_record()
    backwards = tuple(reversed(record.rows))
    path = write(
        rows=backwards, keys=tuple(reversed(EVERY_ROW)), source="x",
        shadow_draws=8, profile_spacing_m=10.0,
        path=tmp_path / "published.toml",
    )
    assert read(path).keys == EVERY_ROW


def test_the_record_is_the_table_the_readme_quotes():
    """Two copies, and the file is the one a run writes.

    The README is read by people who will never start the server, so it
    carries the table as text. This is what stops it from being last
    week's table.
    """
    record = read()
    body = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = [
        line for line in body.splitlines()
        if line.startswith("| YERKON")
    ]
    assert len(rows) == len(record.rows), rows
    for line, row in zip(rows, record.rows):
        quoted = [cell.strip() for cell in line.strip("|").split("|")]
        assert quoted == list(row.cells()), line


def test_the_shipped_record_is_a_whole_table_read_finely():
    record = read()
    assert record.keys == EVERY_ROW
    assert record.shadow_draws >= 2
    assert record.profile_spacing_m > 0.0
    assert record.run_on


def test_the_command_line_hands_the_record_the_keys_it_ran(tmp_path):
    """Nothing else covers this wiring.

    Publishing for real is a quarter of an hour, so what runs between
    the run and the record is tested here rather than end to end.
    """
    import argparse

    from yerkon.cli import _publish

    record = a_record()
    written = _publish(
        rows=record.rows,
        keys=["urban", "rural", "tunnel"],
        args=argparse.Namespace(
            defaults=None, option=None, preset=None,
            publish=str(tmp_path / "published.toml"),
        ),
        settings=None,
    )
    assert read(written).keys == EVERY_ROW
    assert read(written).source == "defaults.toml"


def test_publishing_says_which_figures_the_run_read(tmp_path):
    import argparse

    from yerkon.cli import _publish

    record = a_record()
    written = _publish(
        rows=record.rows,
        keys=["urban", "rural", "tunnel"],
        args=argparse.Namespace(
            defaults="my.toml", option="rural-dense", preset=None,
            publish=str(tmp_path / "published.toml"),
        ),
        settings=None,
    )
    assert read(written).source == "my.toml + rural-dense"


# --- the other systems in the table ---------------------------------------


def test_every_note_the_table_points_at_exists_and_is_in_both_languages():
    from yerkon.comparison import keys_of, read as read_comparison

    table = read_comparison()
    wanted = {table.availability_note}
    wanted |= set(table.yerkon.values())
    for row in table.rows:
        for cell in row.cells:
            wanted |= set(keys_of(cell))

    missing = sorted(wanted - set(table.notes))
    assert not missing, "cells point at notes that are not there: {}".format(
        ", ".join(missing)
    )
    spare = sorted(set(table.notes) - wanted)
    assert not spare, "notes nothing points at: {}".format(", ".join(spare))
    for key, note in table.notes.items():
        assert note.get("tr", "").strip(), key
        assert note.get("en", "").strip(), key
        assert note["tr"] != note["en"], key


def test_every_row_has_a_figure_for_every_column():
    from yerkon.comparison import read as read_comparison

    for row in read_comparison().rows:
        assert len(row.cells) == len(COLUMNS) - 3, row.system


def test_the_results_page_draws_the_other_systems_and_numbers_the_notes():
    from yerkon.comparison import read as read_comparison

    table = read_comparison()
    drawn = render(page_at("/sonuclar"), "tr", a_record())
    for row in table.rows:
        assert ">{}<".format(row.system) in drawn, row.system
    # Numbered in the order they appear, starting at the column head.
    assert 'id="note1"' in drawn and 'href="#note1"' in drawn
    assert 'id="note{}"'.format(len(table.notes)) in drawn
    assert table.said("gps-capex", "tr")[:40] in drawn


def test_our_own_rows_are_marked_apart_from_the_published_ones():
    """A reader has to see which three rows this project produced."""
    drawn = render(page_at("/sonuclar"), "tr", a_record())
    assert drawn.count('<tr class="ours">') == len(EVERY_ROW)


def test_the_other_systems_are_not_drawn_without_a_run_of_our_own():
    """The page compares; with nothing of ours to compare it says so."""
    drawn = render(page_at("/sonuclar"), "tr", None)
    assert "GPS" not in drawn
    assert "yerkon table --publish" in drawn


# --- what a cost is divided by ------------------------------------------


def test_a_corridor_is_priced_by_its_length():
    """A tunnel's area is a fiftieth of a km², and dividing by it made
    the cell large for arithmetic reasons (ADR-0073)."""
    record = read()
    tunnel = dict(zip(record.keys, record.rows))["tunnel"]
    assert tunnel.costed_by == "route"
    cells = list(tunnel.cells())
    assert cells[8].endswith(" /km"), cells[8]
    assert cells[9].endswith(" /km"), cells[9]
    for key in ("urban", "rural"):
        row = dict(zip(record.keys, record.rows))[key]
        assert row.costed_by == "area"
        assert "/km" not in list(row.cells())[8]


def test_the_row_priced_by_length_says_so_in_the_table():
    from yerkon.comparison import read as read_comparison

    drawn = render(page_at("/sonuclar"), "tr", read())
    note = read_comparison().notes[read_comparison().yerkon["by_route"]]
    assert note["tr"][:40] in drawn
    assert note["tr"] != note["en"]


def test_a_cost_drawing_leaves_out_what_is_not_on_its_axis():
    """Per kilometre and per square kilometre are not one scale."""
    from yerkon.viewer.pages import _marks

    record = read()
    priced = {mark.label for mark in _marks(record, "tr", 5)}
    assert not any("Tünel" in name for name in priced), priced
    # It is still in the drawings that do share an axis.
    errors = {mark.label for mark in _marks(record, "tr", 1)}
    assert any("Tünel" in name for name in errors)


# --- the drawings --------------------------------------------------------


def test_a_cell_is_read_as_the_bound_it_is():
    """A ceiling plotted as a point is the one way these could lie."""
    from yerkon.viewer.charts import figure_in

    assert figure_in("-") is None
    assert figure_in("") is None
    exact = figure_in("15,72")
    assert (exact.value, exact.kind, exact.bounded) == (15.72, "exact", False)
    ceiling = figure_in("≤ 8")
    assert (ceiling.value, ceiling.kind, ceiling.bounded) == (
        8.0, "at_most", True)
    assert ceiling.text == "≤ 8"
    floor = figure_in("≥ 0,035")
    assert (floor.value, floor.kind, floor.bounded) == (
        0.035, "at_least", True)
    about = figure_in("≈ 683,80")
    assert (about.value, about.kind, about.bounded) == (
        683.80, "about", False)


def test_a_region_name_is_not_mistaken_for_the_figure():
    """QZSS writes "R1 ≤ 1", and the 1 in R1 comes first in the text."""
    from yerkon.viewer.charts import figure_in

    found = figure_in("R1 ≤ 1 / R2 ≤ 2")
    assert (found.value, found.kind) == (1.0, "at_most")
    assert found.paired and found.text == "≤ 1"


def test_only_the_first_of_a_pair_is_printed_beside_a_mark():
    """The mark sits on one figure, so it may not be labelled with two."""
    from yerkon.viewer.charts import figure_in

    assert figure_in("≤ 10 / ≤ 5").text == "≤ 10"
    assert figure_in("≥ %99 / ≥ %90").text == "≥ 99"


def test_a_drawing_prints_the_table_s_own_numbers():
    """A reader moving between picture and table finds one number.

    Read off the record rather than typed here, so the day the table is
    published again this still holds.
    """
    record = read()
    drawn = render(page_at("/sonuclar"), "tr", record)
    # Inside the drawings only: the table itself and the note markers
    # around it are full of bare numbers.
    pictures = "".join(re.findall(r"<svg class=\"chart\".*?</svg>", drawn,
                                  re.S))
    assert pictures
    for row in record.rows:
        shown = list(row.cells())[4]
        assert ">{}<".format(shown) in pictures, shown
        assert ">{}<".format(shown.split(",")[0]) not in pictures, (
            "{} was rounded to its whole part".format(shown))
    # And one of the other systems', which comes from comparison.toml.
    assert ">15,72<" in pictures and ">0,017<" in pictures


def test_a_bound_is_drawn_with_an_open_end():
    from yerkon.viewer.charts import Mark, bars, figure_in

    ceiling = bars([Mark(label="X", figure=figure_in("≤ 8"))],
                   title="t", unit="m")
    exact = bars([Mark(label="X", figure=figure_in("8"))],
                 title="t", unit="m")
    assert "<path" in ceiling, "a ceiling needs the open end"
    assert "<path" not in exact, "a measurement must not get one"


def test_a_system_with_an_empty_cell_is_left_out_rather_than_guessed():
    from yerkon.viewer.charts import figure_in
    from yerkon.viewer.pages import _marks

    # NavIC publishes no HPE P95, and eLoran no area.
    names = {mark.label for mark in _marks(a_record(), "tr", 1)}
    assert "NavIC SPS" not in names
    assert "GPS" in names
    areas = {mark.label for mark in _marks(a_record(), "tr", 4)}
    assert "eLoran" not in areas
    assert "QZSS SLAS" in areas


def test_every_drawing_takes_its_colours_from_the_palette_tokens():
    """Hard coded hex would be one palette's colour on both.

    The accent and the recessive grey the charts use are their own
    tokens, not the text ones: on a dark surface those two sit closer
    together than a reader with full colour vision can separate.
    """
    from yerkon.viewer import charts

    source = pathlib.Path(charts.__file__).read_text(encoding="utf-8")
    hex_colour = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    found = hex_colour.findall(source)
    assert not found, "hard coded colours: {}".format(found)
    # Each token is defined once per palette: light, the dark media
    # query, and the dark override the button sets.
    css = (STATIC / "site.css").read_text(encoding="utf-8")
    for token in ("--chart-mark", "--chart-context"):
        assert css.count(token) == 3, token


def test_a_chart_is_drawn_again_at_a_phone_s_width():
    """Scrolled, the wide one opens on its labels with no data in view."""
    drawn = render(page_at("/sonuclar"), "tr", a_record())
    wide = drawn.count('class="only-wide"')
    assert wide == drawn.count('class="only-narrow"')
    assert wide == drawn.count('<figure class="chart">')
    assert wide >= 3


def test_a_drawing_escapes_what_it_is_given():
    from yerkon.viewer.charts import Mark, bars, figure_in

    drawn = bars([Mark(label="<script>x</script>", figure=figure_in("8"))],
                 title="<b>t</b>", unit="m")
    assert "<script>" not in drawn
    assert "&lt;script&gt;" in drawn


def test_an_apostrophe_reaches_the_page_as_an_apostrophe():
    """SVG text is content, not an attribute: &#x27; shows up as itself."""
    from yerkon.viewer.charts import Mark, bars, figure_in

    drawn = bars([Mark(label="%5'e", figure=figure_in("8"))],
                 title="t", unit="m")
    assert "%5'e" in drawn and "&#x27;" not in drawn


# --- the bibliography -----------------------------------------------------


def test_every_source_a_note_cites_is_in_the_bibliography():
    from yerkon.comparison import read as read_comparison
    from yerkon.sources import read as read_sources

    known = read_sources().by_key
    missing = sorted(
        "{} -> {}".format(key, cited)
        for key, note in read_comparison().notes.items()
        for cited in note.get("sources", ())
        if cited not in known
    )
    assert not missing, "notes cite entries that are not there: {}".format(
        ", ".join(missing)
    )


def test_every_note_under_the_table_rests_on_a_source():
    """A claim about somebody else's system has to say where it came from.

    A note that says what a column or a denominator means is exempt,
    and says so with `defines = true` rather than being named here: the
    list of exceptions grew once already (ADR-0073) and a list of names
    is the kind of thing that stops being read.
    """
    from yerkon.comparison import read as read_comparison

    table = read_comparison()
    bare = sorted(
        key for key, note in table.notes.items()
        if not note.get("sources") and not note.get("defines")
    )
    assert not bare, "notes with nothing behind them: {}".format(
        ", ".join(bare)
    )


def test_every_entry_of_the_bibliography_is_whole_and_in_both_languages():
    """The labels themselves, not what `said` hands back.

    `said` falls back to Turkish when the English is missing, so asking
    it would call a half written entry whole.
    """
    from yerkon.sources import read as read_sources

    bibliography = read_sources()
    seen = set()
    for group in bibliography.groups:
        assert group.entries, group.key
        assert group.name.get("tr", "").strip(), group.key
        assert group.name.get("en", "").strip(), group.key
        for entry in group.entries:
            assert entry.key not in seen, entry.key
            seen.add(entry.key)
            assert entry.url.startswith("https://"), entry.key
            assert entry.label.get("tr", "").strip(), entry.key
            assert entry.label.get("en", "").strip(), entry.key
    assert seen == set(bibliography.by_key), "an entry is in no group"


def test_an_entry_under_no_heading_is_an_error_rather_than_a_silent_drop(
    tmp_path,
):
    """A misspelled group would otherwise take the entry off the page."""
    from yerkon.sources import SOURCES, read as read_sources

    beside = tmp_path / "sources.toml"
    beside.write_text(
        SOURCES.read_text(encoding="utf-8").replace(
            'group = "news"', 'group = "nowhere"', 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no declared group"):
        read_sources(beside)


def test_the_sources_page_draws_every_entry():
    """Including the ones no note cites: the list is the report's."""
    from yerkon.sources import read as read_sources

    drawn = render(page_at("/kaynaklar"), "tr", a_record())
    bibliography = read_sources()
    for group in bibliography.groups:
        assert ">{}<".format(group.said("tr")) in drawn, group.key
        for entry in group.entries:
            assert 'href="{}"'.format(entry.url.replace("&", "&amp;")) \
                in drawn, entry.key


def test_a_note_under_the_table_links_to_what_it_rests_on():
    from yerkon.comparison import read as read_comparison
    from yerkon.sources import read as read_sources

    drawn = render(page_at("/sonuclar"), "tr", a_record())
    cited = read_comparison().notes["gps-capex"]["sources"]
    assert cited
    for key in cited:
        entry = read_sources().entry(key)
        assert entry.said("tr") in drawn, key


def test_a_link_in_a_phrase_is_drawn_once_escaped():
    """html.escape runs over the whole phrase before the link is made.

    Escaping the address a second time would turn & into &amp;amp; and
    send the reader to an address that is not the one written down.
    """
    from yerkon.viewer.pages import _marked

    drawn = _marked("bak [buraya](https://example.com/a?b=1&c=2)")
    assert '<a href="https://example.com/a?b=1&amp;c=2">buraya</a>' in drawn
    assert "&amp;amp;" not in drawn


def test_a_link_to_anything_but_http_stays_text():
    from yerkon.viewer.pages import _marked

    for address in ("javascript:alert(1)", "data:text/html,<b>x</b>",
                    "file:///etc/passwd"):
        drawn = _marked("[kötü]({})".format(address))
        assert "<a " not in drawn, address


def test_the_sources_are_shipped_with_the_package():
    named = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"sources.toml"' in named


# --- the site as files ----------------------------------------------------


def test_the_folder_carries_both_languages_and_every_page(tmp_path):
    from yerkon.viewer.pages import CARRIED, browser_simulator, write_pages

    written = write_pages(tmp_path, a_record())
    names = {str(path.relative_to(tmp_path)) for path in written}
    assert "index.html" in names and "en/index.html" in names
    assert "simulasyon.html" in names and "en/simulasyon.html" in names
    assert "site.css" in names and ".nojekyll" in names
    # The simulator itself, run by the visitor's browser (ADR-0080).
    assert {"calistir.html", "yerkon.zip", "sim-worker.js"} <= names
    assert len(written) == (2 * len(PAGES) + len(CARRIED) + 1
                            + len(browser_simulator()))


def test_a_page_in_the_folder_points_at_files_that_are_there(tmp_path):
    """Served, the links are addresses. Loose, they are file names, and
    a folder served under /yerkon/ has no root to point at."""
    written = write_pages_of(tmp_path)
    for path in written:
        if path.suffix != ".html":
            continue
        drawn = path.read_text(encoding="utf-8")
        for reference in re.findall(r'(?:href|src)="([^"]+)"', drawn):
            if reference.startswith("http") or reference.startswith("#"):
                continue
            # The simulator is asked for its language in the address.
            reference = reference.split("?")[0]
            # Answered by the engine in the browser rather than by a file.
            if reference.startswith("api/"):
                continue
            assert not reference.startswith("/"), "{}: {}".format(
                path.name, reference
            )
            assert (path.parent / reference).resolve().exists(), "{}: {}".format(
                path.name, reference
            )


def write_pages_of(into):
    from yerkon.viewer.pages import write_pages

    return write_pages(into, a_record())


def test_the_folder_in_the_repository_is_what_the_pages_draw_now(tmp_path):
    """`docs/` is generated and committed, so it can go stale in a way
    `published.toml` cannot: nothing runs to rebuild it.

    Redrawn here and compared. A page edited without `yerkon pages`
    being run fails, and so does a published run nobody redrew the site
    for.
    """
    from yerkon.viewer.pages import write_pages

    docs = ROOT / "docs"
    written = write_pages(tmp_path, read())
    stale = []
    for path in written:
        beside = docs / path.relative_to(tmp_path)
        if not beside.exists() or beside.read_bytes() != path.read_bytes():
            stale.append(str(path.relative_to(tmp_path)))
    assert not stale, (
        "these differ from what the pages draw now; run `yerkon pages`: "
        "{}".format(", ".join(stale))
    )
    # And nothing the pages no longer draw. A page that was renamed
    # leaves its file behind, and the address keeps serving it.
    drawn = {path.relative_to(tmp_path) for path in written}
    for folder in ("", "en"):
        for found in (docs / folder).glob("*.html"):
            assert found.relative_to(docs) in drawn, (
                "{} is not a page any more; run `yerkon pages`".format(found)
            )


def test_the_site_as_files_refuses_to_draw_a_table_that_is_not_there(tmp_path):
    from yerkon.cli import pages as write_them

    holder = tmp_path / "nothing.toml"
    import yerkon.published as published

    was, published.PUBLISHED = published.PUBLISHED, holder
    try:
        assert write_them(["--into", str(tmp_path / "out")]) == 2
    finally:
        published.PUBLISHED = was
    assert not (tmp_path / "out").exists()


# --- drawing --------------------------------------------------------------


def test_a_phrase_with_markup_in_it_cannot_reach_the_page_as_markup():
    page = page_at("/")
    dangerous = dataclasses.replace(
        page, lead=Words(tr="<script>x</script>", en="<script>x</script>")
    )
    drawn = render(dangerous, "tr")
    assert "<script>x</script>" not in drawn
    assert "&lt;script&gt;" in drawn


def test_emphasis_and_code_survive_escaping():
    page = page_at("/")
    marked = dataclasses.replace(
        page, lead=Words(tr="**kalın** ve `kod`", en="**bold** and `code`")
    )
    drawn = render(marked, "tr")
    assert "<strong>kalın</strong>" in drawn
    assert "<code>kod</code>" in drawn


def test_a_part_nobody_can_draw_is_an_error_rather_than_a_blank():
    from yerkon.viewer.pages import Part, _part

    with pytest.raises(ValueError, match="draw"):
        _part(Part(kind="nonsense"), "tr", None)


def test_what_the_town_s_structures_save_is_what_the_model_prices():
    """ADR-0077, ADR-0079. The one counterfactual the results page quotes.

    A unit on a lighting column against the same unit on a mast raised
    for it. The record has no run of a town on masts, so the page cannot
    read the comparison from it; it draws it from the prices the model
    uses instead, and nothing in it is typed. Moving the mast's price
    moves the page.
    """
    from yerkon.cost import SX1280_ANCHOR, DEFAULT_RATES
    from yerkon.numbers import decimal_comma
    from yerkon.viewer.costing import ratio_on_masts
    from yerkon.world import LIGHTING_COLUMN, TALL_MAST

    unit = float(SX1280_ANCHOR.unit_price_tl.value)
    on_column = unit + float(LIGHTING_COLUMN.site_cost_tl.value)
    on_mast = (unit + float(TALL_MAST.site_cost_tl.value)
               + float(DEFAULT_RATES.off_grid_supply_tl.value))
    assert ratio_on_masts() == round(on_mast / on_column)

    page = render(page_at("sonuclar"), "tr")
    for figure in (on_column, on_mast):
        assert decimal_comma(figure, 2) in page
    assert "{} kat".format(ratio_on_masts()) in page


def test_every_cost_cell_is_the_last_line_of_its_breakdown():
    """ADR-0079. The cost page and the table cannot disagree.

    The page prices each row from the same inventory over the same area
    the published run used. If a price moves and nobody republishes, the
    page and the table would say two things; this is what notices.
    """
    from yerkon.viewer.costing import costed

    record = read()
    for key in record.keys:
        row = record.row(key)
        deployed, costing = costed(key, row.area_km2)
        if deployed.serves_a_corridor:
            capex, opex = (costing.capex_tl_per_route_km,
                           costing.opex_tl_per_route_km_year)
        else:
            capex, opex = costing.capex_tl_per_km2, costing.opex_tl_per_km2_year
        assert capex == pytest.approx(row.capex_tl_per_unit, rel=1e-4), key
        assert opex == pytest.approx(row.opex_tl_per_unit_year, rel=1e-4), key


def test_the_cost_page_shows_every_part_and_every_assumption():
    from yerkon.bom import read as bill
    from yerkon.viewer.costing import ASSUMED

    page = render(page_at("maliyet"), "tr", read())
    for part in bill().parts.values():
        used = any(part in board.parts for board in bill().boards.values())
        if used:
            assert html.escape(part.name) in page, part.name
    for key, name in ASSUMED:
        assert name[0] in page, key


def test_the_table_never_calls_anything_pnt():
    """ADR-0066, carried to the other systems' rows.

    The YERKON rows stopped saying it in ADR-0066, but the technology
    cells of TerraPoiNT, Locata and eLoran still did, and so did the
    page. The word is not used on this site, for anybody.
    """
    import tomllib

    table = tomllib.loads(
        (ROOT / "src/yerkon/comparison.toml").read_text(encoding="utf-8"))
    for row in table["row"]:
        assert "PNT" not in row["technology"], row["system"]
    for key, note in table["note"].items():
        assert "PNT" not in note["tr"] and "PNT" not in note["en"], key
    for page in PAGES:
        for language in ("tr", "en"):
            drawn = re.sub(r'href="[^"]*"', "", render(page, language))
            assert "PNT" not in drawn, (page.slug, language)


# --- The simulator in the visitor's browser (ADR-0080) --------------------


def test_the_published_site_opens_the_simulator_rather_than_a_page_about_it():
    """"Simülasyonu çalıştır" runs it; it no longer sends people elsewhere."""
    from yerkon.viewer.pages import BROWSER_SIMULATOR, Where

    assert Where(language="tr", loose=True).simulator() == BROWSER_SIMULATOR
    assert Where(language="en", loose=True).simulator() == (
        "../" + BROWSER_SIMULATOR + "?dil=en")
    assert Where().simulator() == SIMULATOR


def test_the_browser_simulator_asks_nothing_of_the_domain_root(tmp_path):
    """The site lives under a path of its own on GitHub Pages.

    An absolute "/app.js" or "/words.js" is looked for at the root of the
    domain, where there is nothing, and the page would be blank.
    """
    from yerkon.viewer.pages import browser_simulator

    files = browser_simulator()
    page = files["calistir.html"].decode("utf-8")
    assert '<script src="local.js"></script>' in page
    assert page.index("local.js") < page.index('src="app.js"'), (
        "the replacement fetch has to be in place before the page asks")
    for absolute in ('src="/', 'href="/style', 'href="/app'):
        assert absolute not in page, absolute
    app = files["app.js"].decode("utf-8")
    assert 'from "/' not in app


def test_the_archive_the_browser_imports_answers_on_its_own(tmp_path):
    """The package as the browser gets it, imported from nowhere else.

    Unpacked into a folder and imported in a fresh interpreter with that
    folder first on the path, which is what the worker does. If a file
    the engine needs were left out of the archive, this is where it
    would show, rather than as an error in somebody's browser.
    """
    import io
    import json
    import subprocess
    import sys
    import zipfile

    from yerkon.viewer.pages import package_zip

    archive = package_zip()
    assert package_zip() == archive, "the archive changes between builds"
    names = zipfile.ZipFile(io.BytesIO(archive)).namelist()
    assert "yerkon/viewer/server.py" in names
    assert "yerkon/site/places/kizilay/elevation.npy" in names
    assert not any("_tiles" in n or "__pycache__" in n for n in names)

    zipfile.ZipFile(io.BytesIO(archive)).extractall(tmp_path)
    script = (
        "import sys, json; sys.path.insert(0, {!r});"
        "import yerkon; assert yerkon.__file__.startswith({!r}), yerkon.__file__;"
        "from yerkon.viewer.server import answer;"
        "print(answer('GET', '/api/scene'))"
    ).format(str(tmp_path), str(tmp_path))
    run = subprocess.run([sys.executable, "-c", script], capture_output=True,
                         text=True, cwd=tmp_path, timeout=300)
    assert run.returncode == 0, run.stderr[-2000:]
    status, kind, text = json.loads(run.stdout)
    assert status == 200 and "json" in kind
    assert json.loads(text)["anchors"]


def test_the_socketless_answer_is_the_server_s_answer():
    """Same handler, same bytes; only where they go is different."""
    import json

    from yerkon.viewer.server import answer

    status, kind, text = json.loads(answer("GET", "/api/nothing-here"))
    assert status == 404 and json.loads(text)["error"]
    status, kind, text = json.loads(
        answer("POST", "/api/mode", json.dumps({"mode": "tunnel"})))
    assert status == 200 and json.loads(text)["showing"] == "tunnel"
    answer("POST", "/api/mode", json.dumps({"mode": "urban"}))
