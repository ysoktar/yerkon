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

from yerkon.published import EVERY_ROW, Published, as_toml, read, write
from yerkon.report import Row
from yerkon.viewer.pages import (
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
        wanted |= set(re.findall(r'href="([^"]+)"', render(page, "tr")))
    for reference in sorted(wanted):
        if reference.startswith("http"):
            continue
        address = reference.split("?")[0]
        if address == SIMULATOR:
            assert (STATIC / "simulator.html").exists()
        elif address.endswith(".css") or address.endswith(".js"):
            assert (STATIC / address.lstrip("/")).exists(), reference
        else:
            assert page_at(address) is not None, reference
    assert '"/site.css"' in routing


def test_the_simulator_is_served_where_the_pages_point_at_it():
    routing = (ROOT / "src/yerkon/viewer/server.py").read_text(encoding="utf-8")
    assert "SIMULATOR" in routing
    assert '"simulator.html"' in routing
    assert not (STATIC / "index.html").exists(), (
        "the simulator moved to /simulasyon; a leftover index.html would be "
        "served at the site's own address"
    )


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
            technology="Karasal PNT",
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


def test_the_home_page_leads_with_the_weighted_row():
    record = a_record()
    drawn = render(page_at("/"), "tr", record)
    weighted = record.row("weighted")
    assert "{:.2f}".format(weighted.hpe_p50_m).replace(".", ",") in drawn


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
    with pytest.raises(ValueError, match="four rows"):
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


def test_the_command_line_names_the_weighted_row_the_record_wants(tmp_path):
    """`build` appends a fourth row that has no scenario key of its own.

    Nothing else covers this: publishing for real is a quarter of an
    hour, so the wiring between the run and the record is tested here
    rather than end to end.
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


# --- the site as files ----------------------------------------------------


def test_the_folder_carries_both_languages_and_the_simulator_page(tmp_path):
    from yerkon.viewer.pages import LOOSE_PAGES, write_pages

    written = write_pages(tmp_path, a_record())
    names = {str(path.relative_to(tmp_path)) for path in written}
    assert "index.html" in names and "en/index.html" in names
    assert "simulasyon.html" in names and "en/simulasyon.html" in names
    assert "site.css" in names and ".nojekyll" in names
    assert len(written) == 2 * len(LOOSE_PAGES) + 3


def test_a_page_in_the_folder_points_at_files_that_are_there(tmp_path):
    """Served, the links are addresses. Loose, they are file names, and
    a folder served under /yerkon/ has no root to point at."""
    written = write_pages_of(tmp_path)
    for path in written:
        if path.suffix != ".html":
            continue
        drawn = path.read_text(encoding="utf-8")
        for reference in re.findall(r'(?:href|src)="([^"]+)"', drawn):
            if reference.startswith("http"):
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
