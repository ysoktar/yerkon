"""Anchor arrangements the placement search chose, kept as data (ADR-0096).

The search (`yerkon.placement`, ADR-0081) tries every candidate against
the real link budget, which takes minutes. A table row cannot run it on
every build, and the simulator's tab cannot either, so the answer is
written down once — where each anchor stands and what it stands on —
and both read it back. `yerkon place --save` writes it again.

A placement belongs to the ground it was searched on. Asked for over
other ground, it is not there, and the row falls back to its lattice
rather than putting a Kızılay arrangement on Polatlı.
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass
from typing import Optional

#: Where the arrangements are kept, one file per row.
PLACEMENTS = pathlib.Path(__file__).resolve().parent / "placements"

#: The simulator's mounting names and the settings file's, both ways.
MOUNTING_KEYS = {
    "column": "lighting_column",
    "sign": "roadside_sign",
    "gantry": "sign_gantry",
    "billboard": "billboard",
    "mast": "tall_mast",
    "pole": "distribution_pole",
    "roof": "rooftop",
    "tunnel": "tunnel_bracket",
}

#: What `at_a_signalised_junction` calls a column there (ADR-0077).
JUNCTION_KIND = "lighting column at a signalised junction"


@dataclass(frozen=True)
class Placement:
    """One row's arrangement, as the search left it."""

    row: str
    #: "better" or "cheaper", the question the search was asked.
    aim: str
    #: The fetched ground it was searched on.
    site: str
    #: How it was made, so it can be made again.
    made: str
    #: (x, y, mounting, junction) per anchor, in the site's metres and
    #: the simulator's mounting names.
    spots: tuple
    #: How many anchors came from each kind of place.
    mix: dict


def path_of(row: str) -> pathlib.Path:
    return PLACEMENTS / "{}.toml".format(row)


def read(row: str) -> Optional[Placement]:
    """The row's arrangement, or nothing where none was saved."""
    path = path_of(row)
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Placement(
        row=data["row"], aim=data["aim"], site=data["site"],
        made=data["made"],
        spots=tuple((float(x), float(y), str(key), bool(junction))
                    for x, y, key, junction in data["spots"]),
        mix=dict(data.get("mix", {})),
    )


def write(placement: Placement) -> pathlib.Path:
    """Save an arrangement where the row will read it."""
    PLACEMENTS.mkdir(exist_ok=True)
    lines = [
        "# Yerleşim aramasının seçtiği direkler (ADR-0081, ADR-0096).",
        "# The anchors the placement search chose (ADR-0081, ADR-0096).",
        "# {}".format(placement.made),
        "",
        'row = "{}"'.format(placement.row),
        'aim = "{}"'.format(placement.aim),
        'site = "{}"'.format(placement.site),
        'made = "{}"'.format(placement.made),
        "",
        "# x (m), y (m), mounting, at a signalised junction",
        "spots = [",
    ]
    lines += ['  [{:.1f}, {:.1f}, "{}", {}],'.format(
        x, y, key, "true" if junction else "false")
        for x, y, key, junction in placement.spots]
    lines += ["]", "", "[mix]"]
    lines += ['{} = {}'.format(origin, count)
              for origin, count in sorted(placement.mix.items())]
    lines += [""]
    path = path_of(placement.row)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def key_of(mounting) -> tuple[str, bool]:
    """A mounting's simulator name, and whether it stands at a junction."""
    junction = mounting.kind == JUNCTION_KIND
    kind = "lighting column" if junction else mounting.kind
    for key, name in MOUNTING_KEYS.items():
        if name.replace("_", " ") == kind:
            return key, junction
    raise ValueError("no mounting is called {!r}".format(mounting.kind))


def spots_of(anchors) -> tuple:
    """Anchors as the (x, y, mounting, junction) a placement keeps."""
    out = []
    for anchor in anchors:
        key, junction = key_of(anchor.mounting)
        x, y = anchor.ground_position_m[:2]
        out.append((round(float(x), 1), round(float(y), 1), key, junction))
    return tuple(out)


def anchors(placement: Placement, mounting: dict, terrain, radio,
            prefix: str = "P") -> tuple:
    """The arrangement stood up on this ground, with these mountings.

    ``mounting`` is the settings file's catalogue (`world.mountings`).
    Named ``P0``, ``P1``... in the file's order, which is the order the
    simulator's `placed` run names them in, so a tab and its row are the
    same anchors down to the name.
    """
    from yerkon.world import Anchor, at_a_signalised_junction

    junction = at_a_signalised_junction(mounting["lighting_column"],
                                        JUNCTION_KIND)
    return tuple(
        Anchor("{}{}".format(prefix, index), (x, y),
               junction if at_junction else mounting[MOUNTING_KEYS[key]],
               terrain, radio=radio)
        for index, (x, y, key, at_junction) in enumerate(placement.spots)
    )
