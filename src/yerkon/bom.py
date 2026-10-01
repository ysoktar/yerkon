"""The bill of materials, part by part, at one, a hundred and a thousand.

`bom.toml` gives every part its seller's own price ladder: the least
quantity each price starts at. A product at a tier is the sum of its
parts, each at the price the pieces that many boards need buy. Where a
seller published no tier for that quantity, no discount is assumed and
the last known tier holds (ADR-0105).

Nothing here knows about radios or deployments. It prices boards.
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

FILE = pathlib.Path(__file__).resolve().parent / "bom.toml"

#: The tiers the pages show and the table can be priced at.
TIERS = (1, 100, 1000)


@dataclass(frozen=True)
class Part:
    key: str
    name: str
    role_tr: str
    role_en: str
    seller: str
    url: str
    #: (least quantity, USD a piece from it), in rising quantity.
    ladder: tuple[tuple[int, float], ...]
    date: str = ""
    note: str = ""
    volume_url: str = ""
    #: The name in English, where the name is words rather than a part
    #: number ("Pasifler ve gösterge"); empty when one name serves both.
    name_en: str = ""

    def role(self, language: Optional[str] = None) -> str:
        return self.role_en if language == "en" else self.role_tr

    def called(self, language: Optional[str] = None) -> str:
        """The name to show in `language`."""
        return self.name_en if language == "en" and self.name_en else self.name

    def at(self, pieces: int) -> float:
        """USD a piece when `pieces` are bought.

        The last tier at or below `pieces`. Fewer than the seller's least
        order still pays the first tier: that is what one board costs.
        """
        price = self.ladder[0][1]
        for least, usd in self.ladder:
            if least <= pieces:
                price = usd
        return price


@dataclass(frozen=True)
class Board:
    """One product and what it costs at each tier."""

    key: str
    name_tr: str
    name_en: str
    #: The main parts, one of each.
    parts: tuple[Part, ...]
    usd_try: float
    #: The rest of the board, with how many of each.
    others: tuple[tuple[Part, int], ...] = ()

    def name(self, language: Optional[str] = None) -> str:
        return self.name_en if language == "en" else self.name_tr

    @property
    def lines(self) -> tuple[tuple[Part, int], ...]:
        """Every part on the board with its count."""
        return tuple((part, 1) for part in self.parts) + self.others

    def usd(self, boards: int) -> float:
        """One board's parts in USD when `boards` are made."""
        return sum(n * part.at(n * boards) for part, n in self.lines)

    def at(self, tier: int) -> float:
        """One board in TL when `tier` of them are made."""
        return self.usd(tier) * self.usd_try

    @property
    def one_tl(self) -> float:
        return self.at(1)

    @property
    def hundred_tl(self) -> float:
        return self.at(100)

    @property
    def thousand_tl(self) -> float:
        return self.at(1000)


@dataclass(frozen=True)
class Bill:
    usd_try: float
    usd_try_source: str
    used_tier: int
    parts: dict
    boards: dict

    def price(self, key: str) -> float:
        """What the table charges for one of these, in TL."""
        return self.boards[key].at(self.used_tier)


def _counted(parts: dict, entry: str, board: str) -> tuple:
    """A "key" or "key:count" entry of a board's other line."""
    key, _, count = entry.partition(":")
    if key not in parts:
        raise ValueError("{} names a part the bill does not list: {}".format(
            board, key))
    return parts[key], int(count or 1)


def _ladder(key: str, rows) -> tuple:
    ladder = tuple((int(q), float(u)) for q, u in rows)
    if not ladder or [q for q, _ in ladder] != sorted({q for q, _ in ladder}):
        raise ValueError("{}: a ladder climbs in quantity, once each".format(key))
    return ladder


@lru_cache(maxsize=None)
def read(path: pathlib.Path = FILE) -> Bill:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    parts = {
        p["key"]: Part(
            key=p["key"], name=p["name"], role_tr=p["role"]["tr"],
            role_en=p["role"]["en"], seller=p["seller"], url=p["url"],
            ladder=_ladder(p["key"], p["ladder"]), date=p.get("date", ""),
            note=p.get("note", ""), volume_url=p.get("volume_url", ""),
            name_en=p.get("name_en", ""),
        )
        for p in raw["part"]
    }
    usd_try = float(raw["usd_try"])
    boards = {}
    for b in raw["product"]:
        boards[b["key"]] = Board(
            key=b["key"], name_tr=b["name"]["tr"], name_en=b["name"]["en"],
            parts=tuple(_counted(parts, k, b["key"])[0] for k in b["parts"]),
            usd_try=usd_try,
            others=tuple(_counted(parts, entry, b["key"])
                         for entry in b.get("other", ())),
        )
    tier = int(raw["used_tier"])
    if tier not in TIERS:
        raise ValueError("a tier is 1, 100 or 1000, not {}".format(tier))
    return Bill(usd_try=usd_try, usd_try_source=raw["usd_try_source"],
                used_tier=tier, parts=parts, boards=boards)
