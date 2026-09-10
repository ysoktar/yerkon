"""What the page can ask the engine to do, beyond drawing a scene.

The command line grew a verb at a time — a table, an error dissection, a
deployment search, a list of named options — and each one was only
reachable from a terminal. This is the same work, started from the page
and reported back as it goes (`yerkon.viewer.jobs`).

Everything here runs against **the settings the page is currently
showing**, not against the shipped defaults. That is the point: somebody
who has spent an afternoon moving figures should be able to ask what
their arrangement costs, where its error comes from, and what it would
take to reach a target — without writing any of it to a file first.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

import pathlib

from yerkon.budget import dissect_all
from yerkon.deliver import deliver as write_study
from yerkon.numbers import decimal_comma
from yerkon.options import available, read, write
from yerkon.parallel import workers
from yerkon.report import build
from yerkon.scenarios import SITES
from yerkon.settings import Settings
from yerkon.solve import SEARCHABLE, AlreadyMet, Target, search
from yerkon.terms import LABELS, NAMES, REMEDIES
from yerkon.viewer.state import ViewState

Say = Callable[[str], None]


def deployments_of(rows) -> tuple:
    """The rows as they were prepared, each from its own tab.

    Not from the shipped catalogue. A tab holds an arrangement somebody
    built — anchors dragged, a mast raised, a figure corrected — and a
    run that quietly used the catalogue instead would report a
    deployment nobody was looking at (ADR-0028).
    """
    if not rows:
        raise ValueError("no rows to run")
    return tuple(state.deployed() for _, state in rows)


def settings_of(rows) -> Settings:
    """The figures a run reports against: the first row's.

    The rows share one figure list in practice — the panel edits apply to
    whichever tab is showing and a person moves between them — so this
    takes the first rather than pretending to merge three.
    """
    return rows[0][1].settings()


# --- The table ------------------------------------------------------------


def table(rows) -> Callable:
    """The rows as prepared, plus the weighted row when all three run."""

    def work(say: Say) -> dict:
        chosen = deployments_of(rows)
        say("Running {} row{} on {} processes.".format(
            len(chosen), "" if len(chosen) == 1 else "s", workers()))
        results, table_rows = build(chosen, settings=settings_of(rows))
        say("Done.")
        return {
            "columns": [
                "Sistem", "HPE P50", "HPE P95", "VPE P95",
                "Kullanılabilirlik", "Alan km²", "CAPEX/km²", "OPEX/km²/yıl",
            ],
            "rows": [
                {
                    "system": row.system,
                    "cells": [
                        decimal_comma(row.hpe_p50_m, 2),
                        decimal_comma(row.hpe_p95_m, 2),
                        decimal_comma(row.vpe_p95_m, 2),
                        "%" + decimal_comma(100.0 * row.availability, 2),
                        decimal_comma(row.area_km2, 2),
                        decimal_comma(row.capex_tl_per_km2, 0),
                        decimal_comma(row.opex_tl_per_km2_year, 0),
                    ],
                }
                for row in table_rows
            ],
        }

    return work


# --- Where the error came from --------------------------------------------


def budget(rows, sources: Optional[list] = None) -> Callable:
    """Each row's error taken apart, one source at a time (ADR-0020)."""

    def work(say: Say) -> dict:
        chosen = deployments_of(rows)
        wanted = tuple(sources) if sources else NAMES
        say("Running {} simulations: {} scenario{} against {} sources, "
            "on {} processes.".format(
                len(chosen) * (2 * len(wanted) + 2), len(chosen),
                "" if len(chosen) == 1 else "s", len(wanted), workers()))

        dissections = dissect_all(chosen, wanted)
        say("Done.")
        return {
            "scenarios": [
                {
                    "name": one.name,
                    "whole_p50_m": decimal_comma(one.whole_p50_m, 2),
                    "whole_p95_m": decimal_comma(one.whole_p95_m, 2),
                    "range_sigma_m": decimal_comma(one.range_sigma_m, 2),
                    "geometry_gain": decimal_comma(one.geometry_gain, 1),
                    "residue_m": decimal_comma(one.residue_p50_m, 2),
                    "quadrature_m": decimal_comma(one.quadrature_p50_m, 2),
                    "dominant": (
                        one.dominant().source if one.dominant() else None
                    ),
                    "sources": [
                        {
                            "source": c.source,
                            "label": LABELS[c.source],
                            "remedy": REMEDIES[c.source],
                            "alone_m": decimal_comma(c.alone_p50_m, 2),
                            "without_m": decimal_comma(c.without_p50_m, 2),
                            "saves_m": decimal_comma(
                                c.saves_m(one.whole_p50_m), 2),
                            # For the bar the page draws. Shares of the
                            # largest, because these do not add to a whole:
                            # errors combine in quadrature and one of them
                            # is a coupling term (ADR-0020).
                            "share": (
                                c.alone_p50_m / one.ranked()[0].alone_p50_m
                                if one.ranked()[0].alone_p50_m > 0 else 0.0
                            ),
                        }
                        for c in one.ranked()
                    ],
                }
                for one in dissections
            ],
        }

    return work


# --- Searching for a deployment -------------------------------------------


def solve(
    state: ViewState,
    scenario: str,
    target: Target,
    over: Optional[dict] = None,
    save_as: Optional[str] = None,
) -> Callable:
    """Search arrangements for the cheapest that meets a target (ADR-0023)."""

    def work(say: Say) -> dict:
        settings = state.settings()
        knobs = over or SEARCHABLE.get(scenario)
        if not knobs:
            raise ValueError(
                "nothing to search for {}. Name the figures to vary.".format(
                    scenario)
            )
        candidates = 1
        for values in knobs.values():
            candidates *= len(values)
        say("Searching {} arrangements of {} for {}, on {} processes.".format(
            candidates, scenario, target.describe(), workers()))

        seen = [0]

        def note(outcome) -> None:
            seen[0] += 1
            say("[{}/{}] {} anchors · {} availability · HPE50 {} m · {} TL{}"
                .format(
                    seen[0], candidates, outcome.anchors,
                    "%" + decimal_comma(100.0 * outcome.availability, 1),
                    decimal_comma(outcome.hpe_p50_m, 2),
                    decimal_comma(outcome.capex_tl, 0),
                    "  ← meets" if target.met_by(outcome) else "",
                ))

        found = search(scenario, target, over, settings, watching=note)
        best = found.best
        if best is None:
            say("Nothing met it.")
            return {
                "met": False,
                "tried": len(found.tried),
                "closest": decimal_comma(
                    100.0 * max(o.availability for o in found.tried), 2),
            }

        say("{} of {} met it.".format(len(found.met), len(found.tried)))
        outcome = {
            "met": True,
            "tried": len(found.tried),
            "meeting": len(found.met),
            "anchors": best.anchors,
            "availability": "%" + decimal_comma(100.0 * best.availability, 2),
            "hpe_p50_m": decimal_comma(best.hpe_p50_m, 2),
            "hpe_p95_m": decimal_comma(best.hpe_p95_m, 2),
            "capex_tl": decimal_comma(best.capex_tl, 0),
            "fixes_per_second": decimal_comma(best.fixes_per_second, 2),
            "values": {
                key: value for key, value in sorted(best.values.items())
            },
            "moves": [
                {
                    "key": key,
                    "from": decimal_comma(settings.number(key), 2),
                    "to": decimal_comma(value, 2),
                }
                for key, value in sorted(best.values.items())
                if abs(value - settings.number(key)) > 1e-9
            ],
        }

        if save_as:
            try:
                path = write(found.as_option(save_as, settings))
                outcome["saved"] = save_as
                say("Saved as {}.".format(path.name))
            except AlreadyMet as nothing_to_do:
                outcome["already_met"] = str(nothing_to_do)
                say(str(nothing_to_do))
        return outcome

    return work


def target_from(payload: dict) -> Target:
    """A target from what the page sent, treating a blank field as no bar."""

    def bar(name: str, default: float) -> float:
        given = payload.get(name)
        if given in (None, ""):
            return default
        return float(given)

    return Target(
        availability=bar("availability", 0.0),
        hpe_p50_m=bar("hpe_p50_m", math.inf),
        hpe_p95_m=bar("hpe_p95_m", math.inf),
        fixes_per_second=bar("fixes_per_second", 0.0),
    )


# --- Writing the study out ------------------------------------------------


def deliver(rows, into: str, with_budget: bool = True) -> Callable:
    """Write the study out as Markdown, from the rows as prepared."""

    def work(say: Say) -> dict:
        chosen = deployments_of(rows)
        written = write_study(
            into or "docs/teslim", chosen, settings_of(rows),
            with_budget=with_budget, say=say,
        )
        return {
            "into": str(pathlib.Path(into or "docs/teslim").resolve()),
            "files": [
                {"name": one.path.name, "about": one.about} for one in written
            ],
        }

    return work


# --- Bringing in new ground -----------------------------------------------


def fetch(state: ViewState, payload: dict) -> Callable:
    """Fetch real ground for anywhere, from the page.

    The only thing in this project that touches the network, and it was
    the one thing the page could not do — so using anywhere but the four
    Ankara sites meant dropping to a terminal, which for a viewer that is
    meant to be the main way in is a hole (ADR-0008, ADR-0024).

    Writes into the package's own site folder, so what it fetches shows
    up in the ground selector immediately and is committed with
    everything else.
    """

    def work(say: Say) -> dict:
        from yerkon.site.cache import SiteCache
        from yerkon.site.fetch import (
            CopernicusElevation,
            OpenStreetMapBuildings,
            ServiceElevation,
            build_site,
        )
        from yerkon.site.model import BoundingBox

        name = str(payload.get("name", "")).strip()
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "a site needs a name of letters, digits, dashes or "
                "underscores; got {!r}".format(name)
            )

        bounds = BoundingBox(
            south=float(payload["south"]), west=float(payload["west"]),
            north=float(payload["north"]), east=float(payload["east"]),
        )
        spacing = float(payload.get("spacing_m") or 30.0)
        want_buildings = bool(payload.get("buildings", True))

        say("Fetching {:.4f},{:.4f} to {:.4f},{:.4f} at {:.0f} m.".format(
            bounds.south, bounds.west, bounds.north, bounds.east, spacing))
        say("The only thing here that uses the network. It can take a while.")

        site = build_site(
            bounds,
            spacing_m=spacing,
            elevation_sources=(
                CopernicusElevation(cache_directory=str(SITES / "_tiles")),
                ServiceElevation(),
            ),
            buildings_source=(
                OpenStreetMapBuildings() if want_buildings else None
            ),
        )
        SiteCache(SITES / name).save(site)

        say("{:.0f} x {:.0f} m, relief {:.0f} m, roughness {:.2f} m".format(
            site.width_m, site.height_m, site.relief_m, site.roughness_m()))
        for note in site.manifest.notes:
            say(note)

        return {
            "name": name,
            "describe": site.manifest.describe(),
            "width_m": round(site.width_m),
            "height_m": round(site.height_m),
            "relief_m": round(site.relief_m, 1),
            "roughness_m": round(site.roughness_m(), 2),
            "buildings": site.manifest.building_count,
            "notes": list(site.manifest.notes),
        }

    return work


# --- Named options --------------------------------------------------------


def _shown(value) -> str:
    """A figure as the page reads it. Not every one is a quantity.

    Which ground a row stands on is a name (ADR-0027), and asking
    `decimal_comma` for one took the whole options panel down with a 400
    — so the page showed no options at all rather than one bad row.
    """
    if isinstance(value, str):
        return value or "—"
    return decimal_comma(value, 2)


def listed(settings: Settings) -> dict:
    """Every option on hand, and what each would move from where it is now."""
    out = []
    for name in available():
        option = read(name)
        out.append({
            "name": option.name,
            "title": option.title,
            "note": option.note,
            "origin": option.origin,
            "moves": [
                {
                    "key": key,
                    "from": _shown(was),
                    "to": _shown(now),
                }
                for key, was, now in option.differences(settings)
            ],
        })
    return {"options": out, "searchable": {
        name: {key: list(values) for key, values in knobs.items()}
        for name, knobs in SEARCHABLE.items()
    }}
