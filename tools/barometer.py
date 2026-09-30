"""The receiver's height from air pressure, against the units' own
pressure readings, with the errors a real pair of sensors would have.

Local only; the site does not read this. Every broadcast unit carries a
pressure sensor and sends its reading with its ranging reply; the unit's
height is surveyed. The receiver carries the same sensor. The difference
between the two readings is a height difference: at Ankara's height,
about 11 Pa a metre.

What goes wrong, and where each figure comes from:

- Sensor noise, relative accuracy between units, the drift of a year and
  the change of offset with temperature: the sensor's data sheet
  (`SENSORS`).
- The air's own pressure slope across the ground: the geostrophic wind
  relation, |grad p| = rho f V. At 40 degrees north, 10 m/s of wind is
  about 1 Pa a kilometre, 30 m/s about 3. With one unit as reference the
  receiver is wrong by this slope times its distance to that unit; with
  a plane fitted through every unit it heard, the slope drops out.
- Converting pressure to height needs the air's temperature; the one it
  uses is off by as much as the sensors' temperature is (`--delta-t`,
  which has no source: a unit on a pole in the sun and a receiver in a
  cabin differ by an amount nobody has published for this). With
  ``--strategy slope`` the receiver also fits the fall of pressure with
  height from the units it heard, weighed against the temperature's
  figure: where the units stand at different heights the fit wins.
- The receiver's own offset. Either calibrated at the factory and then
  drifting for up to a year (`--calibration factory`), or learned on the
  road against the elevation model the receiver already carries, one
  500 m patch at a time (`--calibration dem`).

Not in it: a vehicle's cabin pressure changing with speed and ventilation
(no published figure was found; at the model's constant speeds it would
be a constant, which the road calibration takes out), wind gusts on a
pedestrian, and weather changing during a round (a round is 0,4 s).

    python tools/barometer.py --fast --sensor spl07-003 --strategy plane
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import io
import math
import pathlib
import sys
import zlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from yerkon import cli  # noqa: E402
from yerkon import estimator  # noqa: E402
from yerkon import evaluate  # noqa: E402
from yerkon import report  # noqa: E402
from height_sources import settings_file  # noqa: E402


@dataclasses.dataclass(frozen=True)
class Sensor:
    name: str
    noise_pa: float           # RMS, the mode named in `source`
    relative_pa: float        # between two readings of one sensor
    drift_pa_year: float      # after a one-point calibration
    tco_pa_k: float           # offset change per kelvin
    source: str


SENSORS = {
    "icp-10111": Sensor("TDK ICP-10111", 0.4, 1.0, 100.0, 0.5,
                        "DS-000186 rev 1.2, table 3: relative ±1 Pa, "
                        "long-term drift ±1 hPa/y, TCO ±0,5 Pa/°C; "
                        "ULN noise 0,4 Pa"),
    "icp-20100": Sensor("TDK ICP-20100", 0.5, 1.0, 10.0, 0.4,
                        "data sheet table 3: relative ±1 Pa, long-term "
                        "drift ±10 Pa/y, TCO ±0,4 Pa/°C; noise taken as "
                        "0,5 Pa"),
    "spl07-003": Sensor("Goertek SPL07-003", 0.5, 3.0, 10.0, 0.5,
                        "data sheet v1.0: relative ±3 Pa, long-term "
                        "±0,1 hPa/12 months, TCO ±0,5 Pa/°C, standard "
                        "mode noise 0,5 Pa"),
    "bmp581": Sensor("Bosch BMP581", 0.21, 1.5, 10.0, 0.5,
                     "BST-BMP581-DS004-13: long-term drift ±10 Pa/y, "
                     "short-term ±1,5 Pa/24 h (taken as the relative "
                     "figure), TCO ±0,5 Pa/K, high-resolution noise "
                     "0,21 Pa"),
}

#: Air density at 900 m in the standard atmosphere, and gravity: Pa per m.
RHO_G = 1.1249 * 9.80665
AIR_K = 282.3

#: The elevation model the road calibration leans on (ADR-0088).
DEM_SIGMA_M = 2.43
DEM_PATCH_M = 500.0


#: The elevation model's own draw, kept before the patch replaces it.
DEM_DRAWN = evaluate._MapError.drawn


class Context:
    """What the patched loop learns as it runs."""

    unit = None
    answered: list = []
    at_s = 0.0
    variance = None


def _crc(text: str) -> int:
    return zlib.crc32(text.encode("utf-8"))


class Barometric:
    """One receiver's pressure height, shaped as the evaluation expects
    of a map: ``at(along)`` is what the height it reports is out by,
    relative to the road surface there plus the antenna."""

    def __init__(self, receiver, scenario, index, args):
        self.receiver = receiver
        self.road = receiver.journey.road
        self.args = args
        sensor = SENSORS[args.sensor]
        self.sensor = sensor
        stream = np.random.default_rng([int(scenario.seed), 91, int(index)])
        self.stream = stream
        # The receiver's offset, Pa: a year's drift after the factory and
        # the offset's move with the cabin's temperature.
        self.bias_pa = (stream.normal(0.0, sensor.drift_pa_year)
                        + sensor.tco_pa_k * stream.normal(0.0, args.delta_t))
        weather = np.random.default_rng([int(scenario.seed), 92])
        angle = weather.uniform(0.0, 2.0 * math.pi)
        self.slope_pa_m = (args.gradient / 1000.0) * np.array(
            [math.cos(angle), math.sin(angle)])
        self.dem = DEM_DRAWN(
            self.road.length_m, DEM_SIGMA_M, DEM_PATCH_M, scenario.seed,
            index)
        self.seed = int(scenario.seed)
        # The air temperature the conversion uses, off for the whole run.
        self.air_error_k = stream.normal(0.0, args.delta_t)
        self.offsets = {}
        # The road calibration: an estimate of the offset in metres.
        start = (sensor.drift_pa_year ** 2
                 + (sensor.tco_pa_k * args.delta_t) ** 2) / RHO_G ** 2
        self.bias_hat_m = 0.0
        self.bias_var_m2 = start
        self.patch = None
        self.patch_sum = 0.0
        self.patch_count = 0

    def unit_offset_pa(self, identifier):
        if identifier not in self.offsets:
            stream = np.random.default_rng([self.seed, 93, _crc(identifier)])
            self.offsets[identifier] = (
                stream.normal(0.0, self.sensor.relative_pa)
                + self.sensor.tco_pa_k * stream.normal(0.0,
                                                       self.args.delta_t))
        return self.offsets[identifier]

    def pressure(self, x, y, h):
        return float(self.slope_pa_m @ np.array([x, y])) - RHO_G * h

    def reading_height(self, truth):
        """The receiver's height from this round's units, and the
        variance the filter is told."""
        sensor, args = self.sensor, self.args
        units = {}
        for identifier, position in Context.answered:
            units[identifier] = position
        if not units:
            return None
        x, y, h = truth
        read_r = (self.pressure(x, y, h) + self.bias_pa
                  + self.stream.normal(0.0, sensor.noise_pa))
        rows = []
        for identifier, (ux, uy, uh) in units.items():
            read = (self.pressure(ux, uy, uh)
                    + self.unit_offset_pa(identifier)
                    + self.stream.normal(0.0, sensor.noise_pa))
            rows.append((ux, uy, uh, read))
        rows = np.array(rows)
        # The air temperature the conversion uses is off by delta-t.
        rho_g = RHO_G * AIR_K / (AIR_K + self.air_error_k)
        # What each unit's reading says the pressure is at its own
        # position, brought to height zero with the converting density.
        level = rows[:, 3] + rho_g * rows[:, 2]
        # With units at different heights the readings themselves say how
        # fast pressure falls with height here. The fit weighs that
        # against the fall the air temperature gives, each by how well it
        # is known, so flat ground leans on the temperature and a hillside
        # on the units.
        if args.strategy == "slope" and len(rows) >= 4:
            unit_pa = math.sqrt(sensor.noise_pa ** 2 + sensor.relative_pa ** 2
                                + (sensor.tco_pa_k * args.delta_t) ** 2)
            prior_sigma = max(RHO_G * args.delta_t / AIR_K, 1e-3)
            design = np.vstack([
                np.column_stack([np.ones(len(rows)), rows[:, 0], rows[:, 1],
                                 rows[:, 2]]) / unit_pa,
                np.array([[0.0, 0.0, 0.0, 1.0 / prior_sigma]])])
            target = np.concatenate([rows[:, 3] / unit_pa,
                                     [-rho_g / prior_sigma]])
            fit, *_ = np.linalg.lstsq(design, target, rcond=None)
            covariance = np.linalg.pinv(design.T @ design)
            rest = fit[0] + fit[1] * x + fit[2] * y
            height = (read_r - rest) / fit[3] - self.bias_hat_m
            point = np.array([1.0, x, y, h])
            spread_pa2 = float(point @ covariance @ point)
            variance = (self.bias_var_m2
                        + (sensor.noise_pa ** 2 + spread_pa2) / RHO_G ** 2)
            return height, variance
        if args.strategy in ("plane", "slope") and len(rows) >= 3:
            design = np.column_stack([np.ones(len(rows)), rows[:, 0],
                                      rows[:, 1]])
            fit, *_ = np.linalg.lstsq(design, level, rcond=None)
            here = fit[0] + fit[1] * x + fit[2] * y
            spread = 1.0 / len(rows)
            slope_var = 0.0
        else:
            nearest = int(np.argmin(np.hypot(rows[:, 0] - x,
                                              rows[:, 1] - y)))
            here = level[nearest]
            spread = 1.0
            distance = math.hypot(rows[nearest, 0] - x, rows[nearest, 1] - y)
            slope_var = (args.gradient / 1000.0 * distance / RHO_G) ** 2
        height = (here - read_r) / rho_g - self.bias_hat_m
        reach = abs(h - float(np.mean(rows[:, 2])))
        variance = (
            self.bias_var_m2
            + (sensor.noise_pa ** 2 * (1.0 + spread)) / RHO_G ** 2
            + spread * (sensor.relative_pa ** 2
                        + (sensor.tco_pa_k * args.delta_t) ** 2) / RHO_G ** 2
            + slope_var
            + (reach * args.delta_t / AIR_K) ** 2)
        return height, variance

    def calibrate(self, height_m, along_estimate):
        """Against the elevation model, one patch of road at a time."""
        if self.args.calibration != "dem":
            return
        road_here = (self.road.surface_height_at(along_estimate)
                     + self.receiver.journey.antenna_height_m
                     + self.dem.at(along_estimate))
        travelled = self.receiver.journey.speed_m_s * Context.at_s
        patch = int(travelled // DEM_PATCH_M)
        if self.patch is not None and patch != self.patch \
                and self.patch_count:
            measured = self.patch_sum / self.patch_count
            gain = self.bias_var_m2 / (self.bias_var_m2 + DEM_SIGMA_M ** 2)
            self.bias_hat_m += gain * measured
            self.bias_var_m2 *= (1.0 - gain)
            self.patch_sum, self.patch_count = 0.0, 0
        self.patch = patch
        self.patch_sum += height_m - road_here
        self.patch_count += 1

    def at(self, along_m):
        truth = self.receiver.journey.position_at(Context.at_s)
        found = self.reading_height(truth)
        base = (self.road.surface_height_at(along_m)
                + self.receiver.journey.antenna_height_m)
        if found is None:
            # No unit answered: nothing to compare with; the filter
            # keeps its own height.
            Context.variance = 1e6
            return 0.0
        height, variance = found
        self.calibrate(height, along_m)
        Context.variance = variance
        return height - base


def patch(args) -> None:
    original_run = evaluate.run_scenario
    original_measure = evaluate.measure
    original_nearest = evaluate.Deployment.nearest_to
    original_absorb = estimator.TrackingFilter.absorb_height

    def nearest_to(self, receiver, at_m):
        Context.unit = receiver.identifier
        Context.answered = []
        return original_nearest(self, receiver, at_m)

    def measure(anchor, receiver, at_s, *rest, **named):
        found = original_measure(anchor, receiver, at_s, *rest, **named)
        if found is not None:
            Context.answered.append((named.get("anchor_id"),
                                     tuple(anchor.position_m)))
            Context.at_s = at_s
        return found

    def absorb_height(self, at_s, height_m, variance_m2):
        if Context.variance is not None:
            variance_m2 = Context.variance
            Context.variance = None
        return original_absorb(self, at_s, height_m, variance_m2)

    def run_scenario(scenario, *rest, **named):
        receivers = scenario.deployment.receivers

        def drawn(length_m, sigma_m, step_m, seed, index):
            return Barometric(receivers[index], scenario, index, args)

        evaluate._MapError.drawn = staticmethod(drawn)
        return original_run(dataclasses.replace(
            scenario, height_aid_sigma_m=DEM_SIGMA_M), *rest, **named)

    evaluate.Deployment.nearest_to = nearest_to
    evaluate.measure = measure
    estimator.TrackingFilter.absorb_height = absorb_height
    evaluate.run_scenario = run_scenario
    report.run_scenario = run_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sensor", choices=tuple(SENSORS),
                        default="spl07-003")
    parser.add_argument("--strategy", choices=("plane", "nearest", "slope"),
                        default="plane")
    parser.add_argument("--calibration", choices=("dem", "factory"),
                        default="dem")
    parser.add_argument("--gradient", type=float, default=3.0,
                        help="the air's pressure slope, Pa per km")
    parser.add_argument("--delta-t", type=float, default=10.0,
                        help="temperature error, kelvin, one sigma")
    parser.add_argument("--only", action="append",
                        choices=("urban", "rural", "tunnel"))
    parser.add_argument("--fast", action="store_true")
    args = parser.parse_args()

    patch(args)
    path = settings_file(DEM_SIGMA_M)
    argv = ["table", "--no-notes", "--defaults", str(path)]
    for row in args.only or ("urban", "rural"):
        argv += ["--only", row]
    if args.fast:
        argv.append("--fast")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cli.main(argv)
    print("## {} {} {} gradient {} Pa/km delta-t {} K".format(
        args.sensor, args.strategy, args.calibration, args.gradient,
        args.delta_t))
    print(out.getvalue())
    path.unlink()


if __name__ == "__main__":
    main()
