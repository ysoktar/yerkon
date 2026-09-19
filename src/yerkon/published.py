"""The four rows as a file, so everything that shows them shows the same ones.

`yerkon table` prints the table, the README quotes it and the site draws
it. Two of those are copies, and a copy made by hand drifts: the numbers
moved four times while the propagation model was being corrected, and
each move meant retyping the same forty cells somewhere else.

So a run writes down what it produced and everything else reads that one
file. Nothing here computes anything. What it does refuse is a record
that would be read as published and is not: a coarse run (ADR-0063) and
a table missing rows both come back as errors rather than as a file.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import tomllib
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.report import Row

#: Where the published table lives. Inside the package beside
#: `defaults.toml`, because the site serves it from wherever the package
#: was installed and a path relative to a checkout would not be there.
PUBLISHED = pathlib.Path(__file__).parent / "published.toml"

#: Keys of the rows a published table holds, in the order it holds them.
EVERY_ROW = ("urban", "rural", "tunnel", "weighted")

#: Columns of one row, in the order the report prints them. The three
#: names are not translated: they are what goes into the Turkish report.
NUMBERS = (
    "hpe_p50_m",
    "hpe_p95_m",
    "vpe_p95_m",
    "availability",
    "area_km2",
    "capex_tl_per_km2",
    "opex_tl_per_km2_year",
)


@dataclass(frozen=True)
class Published:
    """One run of the table, with enough of its run to judge it by."""

    #: The day the run finished, as the machine that ran it had it.
    run_on: str
    #: What the run read its figures from, by name.
    source: str
    #: The two figures that decide how finely a run reads (ADR-0063).
    #: Written down because a coarse table looks exactly like a published
    #: one once the numbers are in a file.
    shadow_draws: int
    profile_spacing_m: float
    rows: tuple[Row, ...]
    keys: tuple[str, ...]

    def row(self, key: str) -> Row:
        return self.rows[self.keys.index(key)]


def read(path: Optional[pathlib.Path] = None) -> Published:
    """The published table, as the numbers rather than as text."""
    path = pathlib.Path(path) if path else PUBLISHED
    held = tomllib.loads(path.read_text(encoding="utf-8"))
    rows, keys = [], []
    for one in held.get("row", ()):
        keys.append(one["key"])
        rows.append(Row(
            system=one["system"],
            technology=one["technology"],
            environment=one["environment"],
            reached_km2=one.get("reached_km2"),
            assumed_share=float(one.get("assumed_share", 0.0)),
            **{name: float(one[name]) for name in NUMBERS},
        ))
    return Published(
        run_on=held["run_on"],
        source=held["source"],
        shadow_draws=int(held["shadow_draws"]),
        profile_spacing_m=float(held["profile_spacing_m"]),
        rows=tuple(rows),
        keys=tuple(keys),
    )


def as_toml(published: Published) -> str:
    """The file's text. Written by hand because it is six lines of it."""
    out = [
        "# The published YERKON block of the comparison table.",
        "#",
        "# Written by `yerkon table --publish`, read by the site and by",
        "# the tests that keep the README from drifting away from it.",
        "# Edit the model and run it again rather than editing this.",
        "",
        "run_on = {}".format(_text(published.run_on)),
        "source = {}".format(_text(published.source)),
        "shadow_draws = {}".format(published.shadow_draws),
        "profile_spacing_m = {}".format(_number(published.profile_spacing_m)),
    ]
    for key, row in zip(published.keys, published.rows):
        out += [
            "",
            "[[row]]",
            "key = {}".format(_text(key)),
            "system = {}".format(_text(row.system)),
            "technology = {}".format(_text(row.technology)),
            "environment = {}".format(_text(row.environment)),
        ]
        for name in NUMBERS:
            out.append("{} = {}".format(name, _number(getattr(row, name))))
        if row.reached_km2 is not None:
            out.append("reached_km2 = {}".format(_number(row.reached_km2)))
        out.append("assumed_share = {}".format(_number(row.assumed_share)))
    return "\n".join(out) + "\n"


def write(
    rows: Sequence[Row],
    keys: Sequence[str],
    source: str,
    shadow_draws: float,
    profile_spacing_m: float,
    path: Optional[pathlib.Path] = None,
    today: Optional[datetime.date] = None,
) -> pathlib.Path:
    """Write a run down as the published table.

    Refuses a table that is not the whole table and refuses a coarse
    read, because the file carries no mark saying which run it came from
    once somebody is reading the site rather than the terminal.
    """
    missing = [key for key in EVERY_ROW if key not in keys]
    if missing:
        raise ValueError(
            "the published table has four rows and this run has {}; "
            "missing: {}".format(len(keys), ", ".join(missing))
        )
    if int(shadow_draws) < 2 or float(profile_spacing_m) <= 0.0:
        raise ValueError(
            "this run read coarsely (shadow draws {}, profile spacing {} m) "
            "and a coarse read is not published; run it without --fast"
            .format(int(shadow_draws), _number(float(profile_spacing_m)))
        )
    order = [keys.index(key) for key in EVERY_ROW]
    published = Published(
        run_on=(today or datetime.date.today()).isoformat(),
        source=source,
        shadow_draws=int(shadow_draws),
        profile_spacing_m=float(profile_spacing_m),
        rows=tuple(rows[at] for at in order),
        keys=EVERY_ROW,
    )
    path = pathlib.Path(path) if path else PUBLISHED
    path.write_text(as_toml(published), encoding="utf-8")
    return path


def _text(value: str) -> str:
    # A TOML basic string and a JSON string escape the same way, and the
    # row names carry apostrophes and non-ASCII letters.
    return json.dumps(value, ensure_ascii=False)


def _number(value: float) -> str:
    # Written to the decimal places the table prints rather than to
    # seventeen, so the file reads like the table it holds. A full stop
    # here: this is TOML, and the comma belongs to what a person reads.
    text = "{:.4f}".format(float(value)).rstrip("0").rstrip(".")
    return text or "0"
