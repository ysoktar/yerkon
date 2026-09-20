"""The comparison table's other systems, as their own sources publish them.

The table this project exists to fill has fourteen rows in it. Three are
this project's and come from `published.toml`, which a run writes. The
rest are GPS, Galileo, GLONASS, BeiDou, QZSS, NavIC, TerraPoiNT, Locata,
Pozyx and eLoran, and they are published figures: nothing here is
computed and nothing here is a measurement of ours.

What this module does is keep those rows out of the page that draws
them, beside the notes that say what was done to each one. A cell like
"≈ 683,80" is a historical investment divided by the earth's surface,
and the note beside it says so; a cell that is empty is empty because
the source publishes nothing that fits the column, and the note says
that too (ADR-0069).
"""

from __future__ import annotations

import pathlib
import re
import tomllib
from dataclasses import dataclass
from typing import Optional

#: Where the other systems' rows are kept, beside the published record.
COMPARISON = pathlib.Path(__file__).parent / "comparison.toml"

#: A note marker inside a cell: the key, not a number. The page numbers
#: them in the order they appear, so adding one renumbers nothing here.
MARKER = re.compile(r"\^([a-z0-9-]+)")


@dataclass(frozen=True)
class Row:
    """One system, as its sources publish it."""

    system: str
    technology: str
    environment: str
    #: The seven figures, in the order the table prints them, each one
    #: possibly carrying note markers.
    cells: tuple[str, ...]


@dataclass(frozen=True)
class Table:
    rows: tuple[Row, ...]
    #: Note key to its text in both languages.
    notes: dict
    #: The note on the availability column itself.
    availability_note: str
    #: Which notes attach to the rows that come from the run.
    yerkon: dict

    def said(self, key: str, language: str) -> str:
        note = self.notes[key]
        return note.get(language) or note["tr"]


def read(path: Optional[pathlib.Path] = None) -> Table:
    """The other systems' rows and their notes."""
    path = pathlib.Path(path) if path else COMPARISON
    held = tomllib.loads(path.read_text(encoding="utf-8"))
    rows = tuple(
        Row(
            system=one["system"],
            technology=one["technology"],
            environment=one["environment"],
            cells=tuple(one["cells"]),
        )
        for one in held["row"]
    )
    return Table(
        rows=rows,
        notes=held["note"],
        availability_note=held["availability_note"],
        yerkon=held["yerkon"],
    )


def keys_of(cell: str) -> tuple[str, ...]:
    """The note keys a cell carries."""
    return tuple(MARKER.findall(cell))


def without_markers(cell: str) -> str:
    """The cell as a person reads it, with the markers taken out."""
    return MARKER.sub("", cell)
