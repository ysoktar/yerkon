"""Tunnel unit layouts side by side: staggered, paired, on the wall, on the
centre line and on the roof, each run exactly as the table runs the
tunnel row.

Local only; the site does not read this. Each layout is a settings file
(spacing, offset, bracket height) plus the pattern the units follow
along the bore. Run from the repository root:

    python tools/tunnel_layouts.py            # every layout
    python tools/tunnel_layouts.py --fast     # quicker, not publishable
"""

from __future__ import annotations

import argparse
import contextlib
import io
import pathlib
import re
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from yerkon import scenarios  # noqa: E402
from yerkon import cli  # noqa: E402

DEFAULTS = ROOT / "src" / "yerkon" / "defaults.toml"

#: name, pattern, spacing between stations (m), offset from the axis (m),
#: bracket height (m), what it is.
LAYOUTS = (
    ("staggered-40", "staggered", 40.0, 4.0, 1.2,
     "walls in turn, 40 m (published)"),
    ("staggered-40-wall", "staggered", 40.0, 5.5, 1.2,
     "walls in turn, 40 m, on the wall itself"),
    ("staggered-50-wall", "staggered", 50.0, 5.5, 1.2,
     "walls in turn, 50 m, on the wall itself"),
    ("paired-80", "paired", 80.0, 4.0, 1.2,
     "both walls at the same point, every 80 m"),
    ("paired-60", "paired", 60.0, 4.0, 1.2,
     "both walls at the same point, every 60 m"),
    ("centre-40", "staggered", 40.0, 0.0, 1.2,
     "on the centre line, 40 m"),
    ("roof-40", "staggered", 40.0, 0.0, 5.0,
     "on the roof, centre line, 40 m, 5 m up"),
)


def laid(pattern: str):
    """The function that places tunnel units, for one pattern."""
    from yerkon.world import Anchor

    def along(length_m, spacing_m, offset_m, mounting, terrain,
              radio=scenarios.SX1280, prefix="N"):
        out = []
        for station, x in enumerate(np.arange(0.0, length_m + 1.0, spacing_m)):
            sides = ((offset_m, -offset_m) if pattern == "paired"
                     else ((offset_m if station % 2 == 0 else -offset_m),))
            for side in sides:
                out.append(Anchor("{}{}".format(prefix, len(out)),
                                  (float(x), side), mounting, terrain,
                                  radio=radio))
        return tuple(out)
    return along


def settings_file(spacing: float, offset: float, height: float) -> pathlib.Path:
    text = DEFAULTS.read_text(encoding="utf-8")
    for key, value in (("tunnel.anchor_spacing_m", spacing),
                       ("tunnel.anchor_offset_m", offset),
                       ("mounting.tunnel_bracket.height_m", height)):
        text, found = re.subn(
            r'(\[values\."{}"\]\nvalue = )[0-9.]+'.format(re.escape(key)),
            r"\g<1>{}".format(value), text)
        assert found == 1, key
    handle = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                         encoding="utf-8")
    handle.write(text)
    handle.close()
    return pathlib.Path(handle.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args()
    original = scenarios._anchors_along
    print("| Yerleşim | Birim | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] "
          "| Kullanılabilirlik | CAPEX [TL/km] | OPEX [TL/km/yıl] |")
    print("|---|---|---|---|---|---|---|---|")
    for name, pattern, spacing, offset, height, said in LAYOUTS:
        scenarios._anchors_along = laid(pattern)
        path = settings_file(spacing, offset, height)
        argv = ["table", "--only", "tunnel", "--no-notes", "--defaults",
                str(path)] + (["--fast"] if args.fast else [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(argv)
        row = [line for line in out.getvalue().splitlines()
               if line.startswith("YERKON (Tünel)")][0]
        cells = re.split(r"\s{2,}", row.strip())
        units = int(len(np.arange(0.0, 2001.0, spacing))
                    * (2 if pattern == "paired" else 1))
        print("| {} ({}) | {} | {} |".format(
            name, said, units, " | ".join(cells[3:6] + cells[6:7]
                                          + cells[8:10])))
        path.unlink()
    scenarios._anchors_along = original


if __name__ == "__main__":
    main()
