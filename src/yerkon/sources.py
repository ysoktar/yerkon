"""Where every figure that is not ours came from.

The report carries a bibliography and its entries are hyperlinks. These
are those addresses, read out of the deck rather than found again later,
so a link on the site goes where the report's own link goes.

`comparison.toml` cites these by key, which is what keeps a note under
the table and an entry on the sources page naming the same thing. A key
nothing cites is still listed: the bibliography is the report's, not a
list of what this site happened to use (ADR-0070).
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass
from typing import Optional

#: Where the bibliography lives, beside the rows it supports.
SOURCES = pathlib.Path(__file__).parent / "sources.toml"


@dataclass(frozen=True)
class Source:
    """One entry of the bibliography."""

    key: str
    group: str
    label: dict
    url: str

    def said(self, language: str) -> str:
        return self.label.get(language) or self.label["tr"]


@dataclass(frozen=True)
class Group:
    """A heading in the bibliography, with the entries under it."""

    key: str
    name: dict
    entries: tuple[Source, ...]

    def said(self, language: str) -> str:
        return self.name.get(language) or self.name["tr"]


@dataclass(frozen=True)
class Bibliography:
    groups: tuple[Group, ...]

    @property
    def by_key(self) -> dict:
        return {
            entry.key: entry
            for group in self.groups
            for entry in group.entries
        }

    def entry(self, key: str) -> Source:
        return self.by_key[key]


def read(path: Optional[pathlib.Path] = None) -> Bibliography:
    """The bibliography, grouped as the report groups it."""
    path = pathlib.Path(path) if path else SOURCES
    held = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = [
        Source(key=one["key"], group=one["group"], label=one["label"],
               url=one["url"])
        for one in held["source"]
    ]
    groups = tuple(
        Group(
            key=group["key"],
            name=group["name"],
            entries=tuple(e for e in entries if e.group == group["key"]),
        )
        for group in held["group"]
    )
    # An entry whose group is misspelled belongs to no heading, so it
    # would be dropped from the page without anything being said.
    declared = {group.key for group in groups}
    homeless = sorted(e.key for e in entries if e.group not in declared)
    if homeless:
        raise ValueError(
            "{}: these entries are in no declared group: {}".format(
                path, ", ".join(homeless)
            )
        )
    return Bibliography(groups=groups)
