"""Turning a measurement back into a default.

The MATLAB scripts under `matlab/` measure figures the report did not
supply. This reads what they write and says what to put in
`defaults.toml`, so that the loop from "somebody guessed this" to
"somebody measured it" closes without anybody transcribing a number by
hand.

It reads CSV with the standard library and nothing else, because the
point is that a measurement should be easy to bring back.
"""

from __future__ import annotations

import csv
import math
import pathlib
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.numbers import readable


@dataclass(frozen=True)
class Measured:
    """One figure, measured, ready to replace the default it stands in for."""

    key: str
    value: float
    unit: str
    source: str
    note: str
    #: What the default was, so the change can be seen rather than found.
    was: Optional[float] = None

    def as_toml(self) -> str:
        lines = [
            '[values."{}"]'.format(self.key),
            "value = {!r}".format(float(self.value)),
            'unit = "{}"'.format(self.unit),
            'provenance = "MEASUREMENT"',
            'source = "{}"'.format(self.source.replace('"', "'")),
            'note = "{}"'.format(self.note.replace('"', "'")),
        ]
        return "\n".join(lines)


def clock_residual(path: str) -> Measured:
    """Read `clock_residual.csv` and take the figure to use.

    The worst residual over the signal-to-noise range where links
    actually close, not the best and not the mean. A default that holds
    only at the strong end of the link is a default that fails where it
    matters, which is the far end.
    """
    rows = _rows(path, {"offset_ppm", "snr_db", "residual_ppm_rms"})

    # Below +10 dB after correlation there is no peak to find and the
    # estimator does not work. That is also below where the link closes,
    # so those rows describe a link nobody has (ADR-0017).
    usable = [row for row in rows if float(row["snr_db"]) >= 10.0]
    if not usable:
        raise ValueError(
            "{} has no rows at or above +10 dB post-correlation, which is "
            "where the link closes. Re-run with that range.".format(path)
        )

    worst = max(float(row["residual_ppm_rms"]) for row in usable)
    offsets = sorted({float(row["offset_ppm"]) for row in usable})

    return Measured(
        key="clock.crystal.residual_ppm",
        value=worst,
        unit="ppm",
        source="matlab/yerkon_clock_residual.m, {}".format(
            pathlib.Path(path).name
        ),
        note=(
            "Worst root-mean-square residual over {} to {} dB after "
            "correlation, for crystal offsets of {} ppm. Additive noise "
            "only: no phase noise, no multipath and no drift during the "
            "exchange, so a real part will be worse than this."
        ).format(
            readable(min(float(r["snr_db"]) for r in usable)),
            readable(max(float(r["snr_db"]) for r in usable)),
            " and ".join(readable(o) for o in offsets),
        ),
    )


def _rows(path: str, required: set) -> list:
    where = pathlib.Path(path)
    if not where.exists():
        raise FileNotFoundError(
            "no measurement at {}. Run the MATLAB script and bring back "
            "what it writes.".format(where)
        )
    with open(where, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError("{} has a header and no rows".format(where))
    missing = required - set(rows[0])
    if missing:
        raise ValueError(
            "{} is missing the columns {}. It has {}.".format(
                where, ", ".join(sorted(missing)), ", ".join(sorted(rows[0]))
            )
        )
    return rows


#: Which reader handles which file the MATLAB writes.
#:
#: One, for now. The other figure on the list — the 2,94 m
#: implementation floor — cannot be measured by simulating the waveform,
#: and the reason is worth writing down rather than discovering twice.
#:
#: One chip at 1625 kHz is 615 ns, which is 184 m of flight. Interpolating
#: a correlation peak gets to perhaps a tenth of that, so a chirp
#: simulation says the part rangesto about 18 m. The part measurably
#: ranges to 2,94 m. Its timing therefore does not come from the symbol
#: correlation at all; it comes from a vendor mechanism running far finer
#: than a chip, which Semtech does not document.
#:
#: A script producing 18 m would contradict a measurement for a reason
#: already understood, which is worse than no script. Measuring that
#: figure needs the part on a bench, not a simulation.
READERS = {
    "clock_residual": clock_residual,
}


def read(path: str) -> Measured:
    """Whichever measurement this file holds, by its name."""
    stem = pathlib.Path(path).stem
    for name, reader in READERS.items():
        if stem.startswith(name):
            return reader(path)
    raise ValueError(
        "{} is not a measurement this knows how to read. Expected one of: "
        "{}.".format(path, ", ".join(sorted(READERS)))
    )
