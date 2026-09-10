"""Every number nobody supplied, loaded from a file rather than written here.

`assumptions.toml` beside this module is the whole list. Nothing in the
rest of `src/` may construct an assumption of its own, and a test in
`tests/test_architecture.py` refuses the build if anything tries.

The point is not tidiness. A placeholder buried in a function is a
placeholder nobody will ever find, and this project's costings rest
between seventy-nine and ninety-nine percent on placeholders. Putting
them in one file makes sourcing one an edit rather than a change to a
program, and makes the share still resting on guesses a number the tool
can compute instead of a claim somebody has to remember to update.

Filling one in is three edits in one place: the ``value``, the
``source``, and ``provenance`` from ASSUMPTION to whatever it now is.
Everything downstream stops counting it the moment that happens.
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import Provenance, Sourced

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "assumptions.toml"

REQUIRED = ("value", "unit", "provenance", "source", "note", "affects")


@dataclass(frozen=True)
class Entry:
    """One figure, and everything a person needs to replace it."""

    key: str
    sourced: Sourced
    #: What moves when this number does.
    affects: str
    #: What doubling it does, where that was measured.
    sensitivity: str = ""

    @property
    def is_assumed(self) -> bool:
        return self.sourced.provenance is Provenance.ASSUMPTION


@dataclass(frozen=True)
class Settings:
    """The file, loaded. Read-only, and never guesses on a caller's behalf."""

    entries: dict
    path: str

    def entry(self, key: str) -> Entry:
        try:
            return self.entries[key]
        except KeyError:
            raise KeyError(
                "{} has no value for {!r}. Every figure the code needs must "
                "be in that file; nothing may be assumed in the code."
                .format(self.path, key)
            ) from None

    def sourced(self, key: str) -> Sourced:
        return self.entry(key).sourced

    def number(self, key: str) -> float:
        return float(self.sourced(key).value)

    @property
    def assumed(self) -> tuple[Entry, ...]:
        """The entries still resting on nothing, in key order."""
        return tuple(
            entry for _, entry in sorted(self.entries.items())
            if entry.is_assumed
        )

    @property
    def sourced_entries(self) -> tuple[Entry, ...]:
        return tuple(
            entry for _, entry in sorted(self.entries.items())
            if not entry.is_assumed
        )

    @property
    def assumed_share(self) -> float:
        """How much of the list is still a placeholder, as a fraction."""
        if not self.entries:
            return 0.0
        return len(self.assumed) / len(self.entries)


def load(path: Optional[str] = None) -> Settings:
    """Read a settings file. Refuses an incomplete entry rather than filling it in."""
    where = pathlib.Path(path) if path else DEFAULT_FILE
    if not where.exists():
        raise FileNotFoundError(
            "no settings file at {}. Copy {} and edit it."
            .format(where, DEFAULT_FILE)
        )

    try:
        document = tomllib.loads(where.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError("{} is not valid TOML: {}".format(where, error)) from None

    raw = document.get("values")
    if not isinstance(raw, dict) or not raw:
        raise ValueError(
            "{} has no [values.\"...\"] entries. It is the list of every "
            "figure the model needs.".format(where)
        )

    entries = {}
    for key, fields in sorted(raw.items()):
        missing = [name for name in REQUIRED if name not in fields]
        if missing:
            raise ValueError(
                "{}: {!r} is missing {}. Every entry says what it is, where "
                "it came from and what it affects, so that replacing it is "
                "possible without reading the code."
                .format(where, key, ", ".join(missing))
            )
        try:
            provenance = Provenance(fields["provenance"])
        except ValueError:
            raise ValueError(
                "{}: {!r} has provenance {!r}. Use one of: {}."
                .format(
                    where, key, fields["provenance"],
                    ", ".join(p.value for p in Provenance),
                )
            ) from None

        entries[key] = Entry(
            key=key,
            sourced=Sourced(
                float(fields["value"]),
                str(fields["unit"]),
                provenance,
                str(fields["source"]),
                note=str(fields["note"]),
            ),
            affects=str(fields["affects"]),
            sensitivity=str(fields.get("sensitivity", "")),
        )

    return Settings(entries=entries, path=str(where))


#: The shipped file, loaded once. Every module's defaults come from here.
#:
#: A run that wants different figures loads its own and passes it to the
#: catalogue builders, rather than mutating this.
DEFAULTS = load()
