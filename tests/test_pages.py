"""The site in front of the simulator.

Two things get checked here that nothing else can. Every phrase is in
both languages, the same promise the panel keeps (ADR-0035). And the
four rows on the results page come out of the published record rather
than out of a copy somebody typed, which is the whole reason the record
exists (ADR-0064).
"""

from __future__ import annotations

import dataclasses
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
            capex_tl_per_km2=94000.0 + at,
            opex_tl_per_km2_year=95000.0 + at,
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

    The one exception is the availability warning, which defines the
    column rather than quoting a figure from anybody.
    """
    from yerkon.comparison import read as read_comparison

    table = read_comparison()
    bare = sorted(
        key for key, note in table.notes.items()
        if not note.get("sources") and key != table.availability_note
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
    from yerkon.viewer.pages import CARRIED, write_pages

    written = write_pages(tmp_path, a_record())
    names = {str(path.relative_to(tmp_path)) for path in written}
    assert "index.html" in names and "en/index.html" in names
    # The page that says where the simulation runs, since a folder of
    # files cannot run it.
    assert "simulasyon.html" in names and "en/simulasyon.html" in names
    assert "site.css" in names and ".nojekyll" in names
    assert len(written) == 2 * len(PAGES) + len(CARRIED) + 1


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
