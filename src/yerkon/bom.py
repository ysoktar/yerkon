"""The bill of materials, part by part, at one, a hundred and a thousand.

The report prints two totals per product and no part prices. This reads
`bom.toml`, where every main part carries the distributor price it was
found at, and works out three things for each product: what is left of
the report's total once its named parts are taken out (the "other"
line: power conversion, protection, connectors, enclosure), what the
product costs with the cheaper parts in, and that cost at the three
tiers.

Nothing here knows about radios or deployments. It prices boards.
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

FILE = pathlib.Path(__file__).resolve().parent / "bom.toml"


@dataclass(frozen=True)
class Part:
    key: str
    name: str
    role_tr: str
    role_en: str
    usd: float
    seller: str
    url: str
    #: A distributor's published price at volume, where one was read:
    #: the tier it applies from, and where and when (ADR-0093).
    volume_usd: Optional[float] = None
    volume_tier: Optional[int] = None
    volume_seller: str = ""
    volume_url: str = ""
    volume_date: str = ""
    volume_note: str = ""

    def role(self, language: Optional[str] = None) -> str:
        return self.role_en if language == "en" else self.role_tr


@dataclass(frozen=True)
class Board:
    """One product: what the report priced, and what it costs now."""

    key: str
    name_tr: str
    name_en: str
    report_tr: str
    report_en: str
    report_one_tl: float
    report_hundred_tl: float
    was: tuple[Part, ...]
    parts: tuple[Part, ...]
    usd_try: float
    thousand_over_hundred: float

    def name(self, language: Optional[str] = None) -> str:
        return self.name_en if language == "en" else self.name_tr

    @property
    def hundred_over_one(self) -> float:
        """The report's own discount from one unit to a hundred."""
        return self.report_hundred_tl / self.report_one_tl

    @property
    def other_usd(self) -> float:
        """What the report's one unit total holds beyond its named parts."""
        named = sum(part.usd for part in self.was)
        return self.report_one_tl / self.usd_try - named

    @property
    def one_tl(self) -> float:
        return (self.other_usd + sum(p.usd for p in self.parts)) * self.usd_try

    @property
    def hundred_tl(self) -> float:
        return self.one_tl * self.hundred_over_one

    @property
    def thousand_tl(self) -> float:
        """A thousand units: each part at its published volume price
        where one was read, and the rest, the "other" line included,
        carried from one unit by the report's own discount (ADR-0093).

        A published volume price is often dearer than that discount
        would make it: the report's ratio was a guess about volume, and
        where a distributor's tier says otherwise the tier wins.
        """
        carried = self.hundred_over_one * self.thousand_over_hundred
        total = self.other_usd * carried + sum(
            part.volume_usd if part.volume_usd is not None
            else part.usd * carried
            for part in self.parts
        )
        return total * self.usd_try

    def at(self, tier: int) -> float:
        return {1: self.one_tl, 100: self.hundred_tl,
                1000: self.thousand_tl}[tier]

    @property
    def swapped(self) -> tuple[tuple[Part, Part], ...]:
        """Each part that changed, beside what it replaced."""
        kept = {p.key for p in self.was}
        new = [p for p in self.parts if p.key not in kept]
        gone = [p for p in self.was if p.key not in {q.key for q in self.parts}]
        return tuple(zip(gone, new))


@dataclass(frozen=True)
class Bill:
    usd_try: float
    usd_try_source: str
    thousand_over_hundred: float
    used_tier: int
    parts: dict
    boards: dict

    def price(self, key: str) -> float:
        """What the table charges for one of these, in TL."""
        return self.boards[key].at(self.used_tier)


def _volume(table: Optional[dict]) -> dict:
    if not table:
        return {}
    return {
        "volume_usd": float(table["usd"]), "volume_tier": int(table["tier"]),
        "volume_seller": table.get("seller", ""), "volume_url": table.get("url", ""),
        "volume_date": table.get("date", ""), "volume_note": table.get("note", ""),
    }


@lru_cache(maxsize=None)
def read(path: pathlib.Path = FILE) -> Bill:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    parts = {
        p["key"]: Part(
            key=p["key"], name=p["name"], role_tr=p["role"]["tr"],
            role_en=p["role"]["en"], usd=float(p["usd"]),
            seller=p["seller"], url=p["url"],
            **_volume(p.get("volume")),
        )
        for p in raw["part"]
    }
    usd_try = float(raw["usd_try"])
    ratio = float(raw["thousand_over_hundred"])
    boards = {}
    for b in raw["product"]:
        try:
            was = tuple(parts[k] for k in b["was"])
            now = tuple(parts[k] for k in b["parts"])
        except KeyError as missing:
            raise ValueError(
                "{} names a part the bill does not list: {}".format(
                    b["key"], missing)
            ) from None
        boards[b["key"]] = Board(
            key=b["key"], name_tr=b["name"]["tr"], name_en=b["name"]["en"],
            report_tr=b["report"]["tr"], report_en=b["report"]["en"],
            report_one_tl=float(b["report_one_tl"]),
            report_hundred_tl=float(b["report_hundred_tl"]),
            was=was, parts=now, usd_try=usd_try,
            thousand_over_hundred=ratio,
        )
    tier = int(raw["used_tier"])
    if tier not in (1, 100, 1000):
        raise ValueError("a tier is 1, 100 or 1000, not {}".format(tier))
    return Bill(usd_try=usd_try, usd_try_source=raw["usd_try_source"],
                thousand_over_hundred=ratio, used_tier=tier,
                parts=parts, boards=boards)
