"""Where the receiver's road height comes from, three ways, each run
exactly as the table runs its rows.

Local only; the site does not read this.

- ``dem``: the published model. The filter reads the road's height from a
  digital elevation model (Copernicus DEM), wrong by 2,43 m (one sigma)
  in patches (ADR-0088).
- ``none``: no height aid; the height is left to the ranges.
- ``units``: every broadcast unit's card carries, from its installation
  survey, the height of the road beneath it. The receiver interpolates
  those heights along its road, between the units within ``--reach`` of
  it. The filter is told this source's own error: the survey error and
  the interpolation's root mean square along that road.

Run from the repository root:

    python tools/height_sources.py units            # all three rows
    python tools/height_sources.py units --only rural
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import io
import math
import pathlib
import re
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from yerkon import cli  # noqa: E402
from yerkon import evaluate  # noqa: E402
from yerkon import report  # noqa: E402

DEFAULTS = ROOT / "src" / "yerkon" / "defaults.toml"

#: Units further than this from the road are not its units: the height
#: they carry is the height of another road.
REACH_M = 30.0

#: The survey of the road height under a unit, one sigma. The same figure
#: the model already gives a unit's surveyed position.
SURVEY_SIGMA_M = 0.15


def stored_heights(road, anchors, reach_m, seed, index):
    """(along, surveyed road height) for the units beside this road."""
    stream = np.random.default_rng([int(seed), 89, int(index)])
    out = []
    for anchor in anchors:
        x, y = anchor.ground_position_m
        along = road.nearest_along(x, y)
        px, py, _ = road.point_at(along)
        if math.hypot(px - x, py - y) > reach_m:
            continue
        out.append((along, road.surface_height_at(along)
                    + stream.normal(0.0, SURVEY_SIGMA_M)))
    out.sort()
    return out


class UnitHeights:
    """The unit-based height's error along one road, in the shape the
    evaluation expects of a map's error: ``at(along)`` is what the
    receiver's height is out by there."""

    def __init__(self, road, stored):
        self.road = road
        self.alongs = np.array([a for a, _ in stored])
        self.heights = np.array([h for _, h in stored])

    def estimate(self, along_m: float) -> float:
        if len(self.alongs) == 0:
            return float("nan")
        return float(np.interp(along_m, self.alongs, self.heights))

    def at(self, along_m: float) -> float:
        return self.estimate(along_m) - self.road.surface_height_at(along_m)

    def rms_m(self, step_m: float = 10.0) -> float:
        points = np.arange(0.0, self.road.length_m, step_m)
        errors = [self.at(a) for a in points]
        return float(np.sqrt(np.mean(np.square(errors))))


def patch_units(reach_m: float) -> None:
    """Swap the map's error for the unit-based one, per receiver."""
    original = evaluate.run_scenario

    def run_scenario(scenario, *args, **kwargs):
        receivers = scenario.deployment.receivers
        per_unit = []
        for index, unit in enumerate(receivers):
            road = unit.journey.road
            stored = stored_heights(road, scenario.deployment.anchors,
                                    reach_m, scenario.seed, index)
            per_unit.append(UnitHeights(road, stored))
        usable = [u for u in per_unit if len(u.alongs) >= 2]
        if len(usable) < len(per_unit):
            raise SystemExit("a receiver's road has fewer than two units "
                             "within {} m".format(reach_m))
        sigma = max(math.sqrt(u.rms_m() ** 2 + SURVEY_SIGMA_M ** 2)
                    for u in per_unit)
        print("# {}: {} units per road on average, filter told {:.2f} m, "
              "worst road rms {:.2f} m".format(
                  scenario.name,
                  sum(len(u.alongs) for u in per_unit) / len(per_unit),
                  sigma, max(u.rms_m() for u in per_unit)),
              file=sys.stderr)
        by_index = dict(enumerate(per_unit))

        def drawn(length_m, sigma_m, step_m, seed, index):
            return by_index[index]

        evaluate._MapError.drawn = staticmethod(drawn)
        return original(dataclasses.replace(scenario,
                                            height_aid_sigma_m=sigma),
                        *args, **kwargs)

    evaluate.run_scenario = run_scenario
    # The table calls it through its own import.
    report.run_scenario = run_scenario


def settings_file(height_aid_sigma_m: float) -> pathlib.Path:
    text = DEFAULTS.read_text(encoding="utf-8")
    text, found = re.subn(
        r'(\[values\."estimator\.height_aid_sigma_m"\]\nvalue = )[0-9.]+',
        r"\g<1>{}".format(height_aid_sigma_m), text)
    assert found == 1
    handle = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False,
                                         encoding="utf-8")
    handle.write(text)
    handle.close()
    return pathlib.Path(handle.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", choices=("dem", "none", "units"))
    parser.add_argument("--only", action="append",
                        choices=("urban", "rural", "tunnel"))
    parser.add_argument("--reach", type=float, default=REACH_M)
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args()

    if args.source == "units":
        patch_units(args.reach)
    # "none" switches the aid off; "units" only needs it on, the figure
    # itself is replaced per road above.
    path = settings_file(0.0 if args.source == "none" else 2.43)
    argv = ["table", "--no-notes", "--defaults", str(path)]
    for row in args.only or ():
        argv += ["--only", row]
    if args.fast:
        argv.append("--fast")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cli.main(argv)
    print(out.getvalue())
    path.unlink()


if __name__ == "__main__":
    main()
