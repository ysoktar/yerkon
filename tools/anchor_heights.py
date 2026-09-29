"""Broadcast units at different heights, to make the vertical observable.

Local only; the site does not read this. Every unit of the town and the
open-country rows stands at one height (a lighting column, a
distribution pole), so a receiver on the road sees them all at nearly the
same elevation and the ranges say little about its height. These
layouts keep the placement and put the units at different heights,
starting from the ground, and then on different structures together.
Each is run exactly as the table runs its rows, with and without the
height aid.

    python tools/anchor_heights.py --fast            # every layout, both ways
    python tools/anchor_heights.py --only rural --layout ladder
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from yerkon import cli  # noqa: E402
from yerkon import placed  # noqa: E402
from height_sources import settings_file  # noqa: E402

#: The unit nearest the ground: a bracket low on the same pole, above
#: splash and reach.
GROUND_M = 1.0

#: name -> (what it is, heights on the row's own pole in turn, or the
#: mountings in turn). A height of None is the pole's own height.
LAYOUTS = {
    "published": ("every unit at the pole's own height", (None,), None),
    "ground": ("every other unit 1 m off the ground, the rest at the "
               "pole's own height", (GROUND_M, None), None),
    "ladder": ("four heights in turn on the same poles: 1 m, a third, "
               "two thirds and the pole's own height",
               (GROUND_M, 1 / 3, 2 / 3, None), None),
    "structures": ("different structures in turn: road sign (3 m), sign "
                   "gantry (6 m), the row's own pole, tall mast (25 m)",
                   None, ("roadside_sign", "sign_gantry", None, "tall_mast")),
}


def at_height(mounting, height_m):
    return dataclasses.replace(
        mounting, height_m=dataclasses.replace(mounting.height_m,
                                               value=float(height_m)))


def patch(layout: str) -> None:
    _, heights, structures = LAYOUTS[layout]
    original = placed.anchors

    def anchors(placement, mounting, terrain, radio, prefix="P"):
        stood = original(placement, mounting, terrain, radio, prefix)
        out = []
        for index, anchor in enumerate(stood):
            own = anchor.mounting
            pole_m = float(own.height_m.value)
            if structures is not None:
                key = structures[index % len(structures)]
                here = own if key is None else mounting[key]
            else:
                share = heights[index % len(heights)]
                if share is None:
                    here = own
                elif share < 1.0:
                    here = at_height(own, max(GROUND_M, share * pole_m))
                else:
                    here = at_height(own, share)
            out.append(dataclasses.replace(anchor, mounting=here))
        return tuple(out)

    placed.anchors = anchors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layout", choices=tuple(LAYOUTS))
    parser.add_argument("--only", action="append", choices=("urban", "rural"))
    parser.add_argument("--aid", choices=("on", "off"))
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args()

    layout = args.layout or "published"
    patch(layout)
    aids = (args.aid,) if args.aid else ("on", "off")
    for aid in aids:
        path = settings_file(2.43 if aid == "on" else 0.0)
        argv = ["table", "--no-notes", "--defaults", str(path)]
        for row in args.only or ("urban", "rural"):
            argv += ["--only", row]
        if args.fast:
            argv.append("--fast")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(argv)
        print("## {} ({}), height aid {}".format(
            layout, LAYOUTS[layout][0], aid))
        print(out.getvalue())
        path.unlink()


if __name__ == "__main__":
    main()
