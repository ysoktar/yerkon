"""The report block as files somebody can hand over.

Everything this project produces has lived in a terminal or a browser
tab. What the work is *for* is the YERKON block on page 15 of the
report — four rows, ten columns — and the argument behind it: what the
rows stand on, where their error comes from, what could be bought
instead, and how much of the costing is still resting on figures nobody
supplied.

So this writes that argument out as Markdown. Several files rather than
one, because they answer different questions and get read by different
people: a table is for whoever fills in page 15, a provenance list is
for whoever has to defend it, an error budget is for whoever holds the
money.

Nothing here computes anything. Every figure comes from the same modules
the table does, run once and rendered several ways (ADR-0001).
"""

from __future__ import annotations

import datetime
import pathlib
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from yerkon.budget import dissect_all
from yerkon.numbers import decimal_comma, readable
from yerkon.options import available, read as read_option
from yerkon.report import Result, Row, as_markdown, build, footnotes
from yerkon.scenarios import ALL, Deployed
from yerkon.settings import DEFAULTS, Settings
from yerkon.terms import LABELS, REMEDIES

Say = Callable[[str], None]


@dataclass(frozen=True)
class Written:
    """One file, and one line saying what is in it."""

    path: pathlib.Path
    about: str


def _shown(sourced) -> str:
    """A figure as a person reads it.

    Not every figure is a quantity: which ground a row stands on is a
    name, and it belongs in this table beside the spacings (ADR-0027).
    """
    if sourced.is_text:
        return "`{}`".format(sourced.value) if sourced.value else "—"
    return readable(float(sourced.value))


def _as_read(value) -> str:
    """A figure from an option's diff, name or number."""
    return value if isinstance(value, str) else readable(value)


def _quiet(line: str) -> None:
    return


def _header(title: str, settings: Settings) -> str:
    """The same three lines on every file: what, from what, and when.

    A table nobody can date is a table nobody can check against the
    figures it was run on.
    """
    return (
        "# {}\n\n"
        "*YERKON — karasal PNT yedeği. {} tarihinde, {} sayıdan üretildi; "
        "bunların %{}'i hâlâ kimsenin sağlamadığı bir değere dayanıyor.*\n"
    ).format(
        title,
        datetime.date.today().isoformat(),
        len(settings.entries),
        decimal_comma(100.0 * settings.assumed_share, 0),
    )


# --- The four rows --------------------------------------------------------


def table_md(
    results: Sequence[Result], rows: Sequence[Row], settings: Settings
) -> str:
    """Page 15's block, and the notes that keep it honest."""
    out = [
        _header("Karşılaştırma tablosu — YERKON satırları", settings),
        "\nRaporun 15. sayfasındaki tablonun YERKON bloğu. Onuncu sütun — "
        "OPEX — raporda dört satır için de boştu; buradaki değer, sermaye "
        "giderinin bir yüzdesi değil, adı konmuş yinelenen kalemlerden "
        "toplanmıştır (ADR-0006).\n",
        as_markdown(rows),
        "\n## Satırların dayandığı zemin\n",
    ]
    for result in results:
        terrain = result.deployed.scenario.terrain
        out.append(
            "- **{}** — {}. {} direk, {}.".format(
                result.deployed.scenario.name,
                terrain.description,
                len(result.deployed.scenario.deployment.anchors),
                result.deployed.technology,
            )
        )
    out.append("\n## Notlar\n\n```\n" + footnotes(results, rows) + "\n```\n")
    return "\n".join(out)


# --- Where the error comes from -------------------------------------------


def budget_md(dissections: Sequence, settings: Settings) -> str:
    """What each error source was worth, and what removing it would take."""
    out = [
        _header("Hata bütçesi — her kaynağın payı", settings),
        "\nHer satır, aynı senaryonun tek bir hata kaynağı susturularak "
        "yeniden koşturulmasıdır; yeni bir model değil (ADR-0020).\n\n"
        "**Tek başına**, o kaynak tek olsaydı kalacak hatadır. "
        "**Kalkarsa**, o kaynak gidip diğerleri kalınca toplamın ineceği "
        "yerdir — hatalar kareli toplandığı için her zaman daha küçüktür, "
        "ve satın alma kararı olan odur.\n",
    ]
    for one in dissections:
        out.append(
            "\n## {}\n\nHPE P50 {} m · P95 {} m · bir menzilin σ'sı {} m · "
            "geometri çarpanı ×{}\n".format(
                one.name,
                decimal_comma(one.whole_p50_m, 2),
                decimal_comma(one.whole_p95_m, 2),
                decimal_comma(one.range_sigma_m, 2),
                decimal_comma(one.geometry_gain, 1),
            )
        )
        out.append(
            "| Hata kaynağı | Tek başına [m] | Kalkarsa [m] | Kazanç [m] | Çare |\n"
            "|---|---|---|---|---|"
        )
        for contribution in one.ranked():
            out.append("| {} | {} | {} | {} | {} |".format(
                LABELS[contribution.source],
                decimal_comma(contribution.alone_p50_m, 2),
                decimal_comma(contribution.without_p50_m, 2),
                decimal_comma(contribution.saves_m(one.whole_p50_m), 2),
                REMEDIES[contribution.source],
            ))
        out.append("| Model artığı | {} | | | hiçbir kaynak açık değilken kalan |"
                   .format(decimal_comma(one.residue_p50_m, 2)))

        dominant = one.dominant()
        out.append(
            "\n{}\n".format(
                "Önce harcanacak yer: **{}**. Kalkarsa HPE P50 {} m'den "
                "{} m'ye iner.".format(
                    LABELS[dominant.source].lower(),
                    decimal_comma(one.whole_p50_m, 2),
                    decimal_comma(dominant.without_p50_m, 2),
                )
                if dominant else
                "Tek bir baskın kaynak yok: en büyük ikisi birbirine yakın, "
                "yani burada sıralama değil bir tercih vardır."
            )
        )
    return "\n".join(out)


# --- What the numbers rest on ---------------------------------------------


def figures_md(settings: Settings) -> str:
    """Every figure, what it affects, and how much weight it can carry."""
    out = [
        _header("Sayılar ve dayanakları", settings),
        "\nRapor yalnızca malzeme listesini verdi. Aşağıdaki her sayı ya "
        "ölçülmüş, ya bir belgeden alınmış, ya da bu proje tarafından "
        "seçilmiştir — ve hangisi olduğu yazılıdır (ADR-0016).\n\n"
        "**Tasarım kararları** ayrı tutulur: direk aralığı gibi bir sayı "
        "kimsenin ölçebileceği bir şey değil, karara bağlanan şeydir "
        "(ADR-0023). Onları varsayımların arasında saymak, çalışmanın ne "
        "kadarının tahmine dayandığını söyleyen oranı sulandırırdı.\n",
    ]
    for title, entries in (
        ("Hâlâ kimsenin sağlamadığı sayılar", settings.assumed),
        ("Kaynağı olan sayılar", settings.sourced_entries),
        ("Tasarım kararları", settings.choices),
    ):
        out.append("\n## {} ({})\n".format(title, len(entries)))
        out.append("| Sayı | Değer | Dayanak | Neyi etkiliyor |\n|---|---|---|---|")
        for entry in entries:
            out.append("| `{}` | {} {} | {} | {} |".format(
                entry.key, _shown(entry.sourced),
                entry.sourced.unit,
                entry.sourced.provenance.value.title(),
                entry.affects,
            ))
    return "\n".join(out)


# --- What could be bought instead -----------------------------------------


def options_md(settings: Settings) -> str:
    """The deployments this project ships besides the one in the table."""
    out = [
        _header("Seçenekler — başka neler kurulabilirdi", settings),
        "\nHer seçenek, ayar dosyasında birkaç sayıyı değiştiren kısa bir "
        "listedir; yeni bir tanesi kod değil, dosya maliyetindedir "
        "(ADR-0023). `yerkon table --option AD` ile koşulur.\n",
    ]
    names = available()
    if not names:
        out.append("\nHazır seçenek yok.\n")
        return "\n".join(out)

    for name in names:
        option = read_option(name)
        out.append("\n## `{}` — {}\n".format(option.name, option.title))
        out.append("| Sayı | Şu an | Bu seçenekte |\n|---|---|---|")
        for key, was, now in option.differences(settings):
            out.append("| `{}` | {} | {} |".format(
                key, _as_read(was), _as_read(now)))
        out.append("\n{}\n".format(option.note))
    return "\n".join(out)


# --- Writing them out -----------------------------------------------------


def deliver(
    into: str | pathlib.Path,
    deployments: Sequence[Deployed] = ALL,
    settings: Optional[Settings] = None,
    with_budget: bool = True,
    say: Say = _quiet,
) -> tuple[Written, ...]:
    """Run the study once and write it out as Markdown.

    The dissection is optional because it is by far the slowest part —
    sixteen simulations a row against three — and somebody who wants the
    table refreshed should not have to wait for the error budget too.
    """
    settings = settings or DEFAULTS
    directory = pathlib.Path(into)
    directory.mkdir(parents=True, exist_ok=True)

    say("Running the table.")
    results, rows = build(deployments, settings=settings)

    written = [
        _write(directory / "tablo.md", table_md(results, rows, settings),
               "the four rows, the ground they stand on, and the notes"),
        _write(directory / "sayilar.md", figures_md(settings),
               "every figure, what it affects, and what it rests on"),
        _write(directory / "secenekler.md", options_md(settings),
               "the deployments shipped besides the one in the table"),
    ]

    if with_budget:
        say("Taking the error apart. This is the slow part.")
        written.append(_write(
            directory / "hata-butcesi.md",
            budget_md(dissect_all(deployments), settings),
            "what each error source was worth, and what removing it takes",
        ))

    written.append(_write(
        directory / "README.md", _index(written), "what is in each file"))
    for one in written:
        say("Wrote {}".format(one.path))
    return tuple(written)


def _index(written: Sequence[Written]) -> str:
    lines = [
        "# YERKON — rapor teslimi\n",
        "\nBu klasör `yerkon deliver` tarafından yazıldı. Her sayı, "
        "tablonun kullandığı motorun aynısından gelir (ADR-0001).\n",
    ]
    for one in written:
        lines.append("- [`{}`]({}) — {}".format(
            one.path.name, one.path.name, one.about))
    return "\n".join(lines) + "\n"


def _write(path: pathlib.Path, body: str, about: str) -> Written:
    path.write_text(body.rstrip() + "\n", encoding="utf-8")
    return Written(path=path, about=about)
