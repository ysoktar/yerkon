"""Every unit's range, the receivers' parts and prices, and how many
receivers a square kilometre carries.

    python tools/units.py                    all three, as Markdown
    python tools/units.py --out FILE.md      and into a file
    python tools/units.py --fix-rate 2       capacity at two fixes a second

Local only, like `hardware.py`: the site and the browser simulator are
built from `src/yerkon` and nothing here reaches them.

**Ranges.** Every pole and receiver pairing of every setup in
`hardware.py`, both ways: a range counts only where the pole reaches the
receiver and the receiver's reply reaches the pole. Over flat open ground
with no buildings and no shadow, so these are the most a pairing gives;
the rows are run on the real ground and buildings and reach less. The
tunnel is measured along its own bore with its guided loss.

- *Closes*: the packet still gets through.
- *Passes the gate*: the range is still precise enough for the row's
  filter to take it (`accept_sigma_m`: 15 m in town, 30 m in the country,
  2 m in the tunnel).
- *Precise*: one sigma at most 5 m (1 m in the tunnel).

**Capacity.** A position takes one exchange with each anchor of a round
(12 in town and country, 8 in the tunnel), and one exchange holds the
channel for its air time. Two figures, because the model and the world
differ here:

- *One channel*: the model's own assumption. Every receiver of a row
  shares one medium, one exchange at a time, however far apart they are.
- *Every pole busy*: the ceiling. Each pole answers one exchange at a time
  but all poles work at once, as they could on different hopping channels
  or far enough apart. Receivers per km² = poles per km² × exchanges a
  pole can answer a second ÷ (anchors a round × fixes a second).

The truth for a real network lies between the two and depends on how the
exchanges are scheduled, which the model does not simulate.
"""

from __future__ import annotations

import argparse
import dataclasses
import math
import os
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
sys.path.insert(0, HERE)

import hardware as tool  # noqa: E402
from yerkon import bom  # noqa: E402

GATE = {"urban": 15.0, "rural": 30.0, "tunnel": 2.0}
PRECISE = {"urban": 5.0, "rural": 5.0, "tunnel": 1.0}
POLE_M = {"urban": 12.0, "rural": 10.0}
UNITS = {
    "urban": (("araç", "vehicle", 1.5), ("yaya", "pedestrian", 1.6)),
    "rural": (("araç", "vehicle", 1.5), ("kamyon", "vehicle", 2.8)),
}


def c(x, n=2):
    return ("{:." + str(n) + "f}").format(x).replace(".", ",")


def km(m):
    return "0" if m <= 0 else c(m / 1000.0, 2)


# --- Ranges -------------------------------------------------------------------

def _models():
    from yerkon import hardware
    from yerkon.settings import DEFAULTS

    radios = hardware.radios(DEFAULTS)
    radios["e28-27s"] = hardware._sx1280_family(
        "EBYTE E28-2G4M27S", 27.0,
        "EBYTE E28-2G4M27S product page, rated output power", DEFAULTS)
    antennas = {"rod": hardware.GW_22_5151, "mast": hardware.TL_ANT2412D,
                "roof": hardware.HGV_2409U, "printed": hardware.W24P_U}
    return radios, antennas


def both_ways(pole, unit, radio, region, target):
    """Closure and precision range with both directions required."""
    from yerkon.rf import closure_range_m, usable_range_m

    closes = min(closure_range_m(pole, unit, region=region),
                 closure_range_m(unit, pole, region=region))
    if target is None:
        return closes
    return min(usable_range_m(pole, unit, radio, target, region=region),
               usable_range_m(unit, pole, radio, target, region=region))


def open_ground_ranges():
    from yerkon.regulatory import REGIONS
    from yerkon.rf import Terminal

    radios, antennas = _models()
    lines = []
    for setup in tool.setups().values():
        region = REGIONS[setup.rule]
        for row in ("urban", "rural"):
            pole_radio = radios[setup.pole]
            pole = Terminal(pole_radio, antennas[setup.pole_antenna],
                            (0.0, 0.0, POLE_M[row]))
            for name, kind, height in UNITS[row]:
                if kind == "vehicle":
                    radio, antenna = radios[setup.vehicle], antennas[setup.vehicle_antenna]
                else:
                    radio, antenna = radios[setup.pedestrian], antennas["printed"]
                unit = Terminal(radio, antenna, (0.0, 0.0, height))
                lines.append((setup.key, row, name, height, POLE_M[row],
                              both_ways(pole, unit, pole_radio, region, None),
                              both_ways(pole, unit, pole_radio, region, GATE[row]),
                              both_ways(pole, unit, pole_radio, region, PRECISE[row])))
    return lines


def tunnel_ranges():
    """Along the bore from the first pole, with the tunnel's guided loss."""
    from yerkon.hardware import DWM3000_ANTENNA
    from yerkon.rf import Terminal, evaluate_link, ranging_sigma_m
    from yerkon.scenarios import catalogue
    from yerkon.settings import DEFAULTS

    deployed = catalogue(DEFAULTS)["tunnel"]
    dep, ground = deployed.scenario.deployment, deployed.scenario.terrain
    anchor = dep.anchors[0]
    pole = Terminal(anchor.radio, DWM3000_ANTENNA, anchor.position_m)
    x0 = anchor.position_m[0]
    end = max(a.position_m[0] for a in dep.anchors)

    def link(unit_radio, height, distance, reverse):
        x = x0 + distance
        here = (x, 0.0, ground.height_at(x, 0.0) + height)
        unit = Terminal(unit_radio, DWM3000_ANTENNA, here)
        a, b = (unit, pole) if reverse else (pole, unit)
        obstruction = dataclasses.replace(
            ground.obstruction_between(a.position_m, b.position_m), shadow_db=0.0)
        return evaluate_link(a, b, obstruction=obstruction, region=dep.region)

    def reach(unit_radio, height, target):
        def ok(distance):
            for reverse in (False, True):
                budget = link(unit_radio, height, distance, reverse)
                if not budget.closes:
                    return False
                if target is not None and ranging_sigma_m(budget, anchor.radio) > target:
                    return False
            return True

        low, high = 1.0, end - x0
        if not ok(low):
            return 0.0
        if ok(high):
            return high
        for _ in range(40):
            mid = 0.5 * (low + high)
            low, high = (mid, high) if ok(mid) else (low, mid)
        return low

    return [(name, height, anchor.position_m[2] - ground.height_at(
                 anchor.position_m[0], anchor.position_m[1]),
             reach(anchor.radio, height, None),
             reach(anchor.radio, height, GATE["tunnel"]),
             reach(anchor.radio, height, PRECISE["tunnel"]),
             end - x0)
            for name, height in (("araç", 1.5), ("yaya", 1.6))]


# --- Capacity -----------------------------------------------------------------

def capacity(fix_rate: float):
    """Receivers a row carries at `fix_rate` fixes a second, both ways."""
    from yerkon.ranging import exchange_duration_s
    from yerkon.scenarios import catalogue
    from yerkon.settings import DEFAULTS

    published = tomllib.load(open(os.path.join(
        HERE, "..", "src", "yerkon", "published.toml"), "rb"))
    served = {r["key"]: r for r in published["row"]}
    rows = catalogue(DEFAULTS)
    out = []
    for row in ("urban", "rural", "tunnel"):
        dep = rows[row].scenario.deployment
        exchange_s = exchange_duration_s(dep.anchors[0].radio, dep.scheme)
        per_second = dep.duty_cycle / exchange_s
        per_fix = dep.max_anchors_per_round
        one_channel = per_second / (per_fix * fix_rate)
        poles = len(dep.anchors)
        if row == "tunnel":
            size = rows[row].route_km
            unit = "km"
        else:
            size = served[row]["area_km2"]
            unit = "km²"
        busy = poles / size * per_second / (per_fix * fix_rate)
        out.append((row, exchange_s, per_second, per_fix, poles, size, unit,
                    one_channel, one_channel / size, busy))
    return out


# --- Receivers ----------------------------------------------------------------

def receiver_lines(bill):
    """Every part on each receiver, at 1, 100 and 1000, in TL."""
    out = {}
    for key in ("pedestrian", "vehicle"):
        board = bill.boards[key]
        rows = []
        for part, n in board.lines:
            rows.append((part.name, part.role_tr, n, part.seller,
                         [n * part.at(n * t) * bill.usd_try for t in bom.TIERS]))
        out[key] = (board, rows)
    return out


# --- Report -------------------------------------------------------------------

NAMES = {"urban": "Şehir içi", "rural": "Kırsal", "tunnel": "Tünel"}


def report(fix_rate: float) -> str:
    out = ["# Birimlerin menzili, alıcılar ve kapasite", ""]

    out += ["## Menziller: açık ve düz zeminde, iki yön birlikte", "",
            "Bina, tepe ve gölge yok; satırlar gerçek zeminde koşulduğu için "
            "oradaki menzil daha kısa. Bağlantı: paket geçiyor. Filtre: ölçüm "
            "satırın sınırında (şehir 15 m, kırsal 30 m). Hassas: bir sigma en çok 5 m.",
            "",
            "| Kurulum | Satır | Alıcı (yükseklik) | Direk | Bağlantı km | Filtre km | Hassas km |",
            "|---|---|---|---|---|---|---|"]
    for key, row, name, height, pole_m, closes, gate, precise in open_ground_ranges():
        out.append("| {} | {} | {} ({} m) | {} m | {} | {} | {} |".format(
            key, NAMES[row], name, c(height, 1), c(pole_m, 0), km(closes),
            km(gate), km(precise)))

    out += ["", "## Tünel: kendi borusu boyunca, yönlendirilmiş kayıpla", "",
            "DWM3000, kanal 5, iki uçta modülün kendi anteni. Filtre: bir sigma "
            "en çok 2 m. Hassas: en çok 1 m. Tünel borusunun uzunluğu üst sınır.",
            "",
            "| Alıcı (yükseklik) | Direk | Bağlantı m | Filtre m | Hassas m | Boru m |",
            "|---|---|---|---|---|---|"]
    for name, height, pole_m, closes, gate, precise, bore in tunnel_ranges():
        out.append("| {} ({} m) | {} m | {} | {} | {} | {} |".format(
            name, c(height, 1), c(pole_m, 1), c(closes, 0), c(gate, 0),
            c(precise, 0), c(bore, 0)))

    out += ["", "## Kapasite: saniyede {} konumda en çok alıcı".format(c(fix_rate, 1)), "",
            "Bir konum, turdaki her direkle bir ölçüm alışverişi ister. Tek kanal: "
            "modelin varsayımı, satırdaki bütün alıcılar tek ortamı sırayla "
            "paylaşıyor. Her direk meşgul: tavan, bütün direkler aynı anda "
            "çalışıyor (farklı atlama kanallarında ya da birbirinden uzakta). "
            "Gerçek ağ ikisinin arasında; zamanlama modelde yok.",
            "",
            "| Satır | Alışveriş ms | Direk başına saniyede alışveriş | Turdaki direk | Direk | Alan | "
            "Tek kanal: alıcı | Tek kanal: alıcı / alan | Her direk meşgul: alıcı / alan |",
            "|---|---|---|---|---|---|---|---|---|"]
    for row, ex, per_s, per_fix, poles, size, unit, one, one_per, busy in capacity(fix_rate):
        out.append("| {} | {} | {} | {} | {} | {} {} | {} | {} / {} | {} / {} |".format(
            NAMES[row], c(ex * 1000, 1), c(per_s, 1), per_fix, poles, c(size, 2), unit,
            c(one, 1), c(one_per, 2), unit, c(busy, 1), unit))

    bill = bom.read()
    out += ["", "## Alıcılar: parçalar ve fiyatlar (TL)", ""]
    for key, (board, rows) in receiver_lines(bill).items():
        out += ["### " + board.name(), "",
                "| Parça | Görevi | Adet | Satıcı | 1 | 100 | 1000 |",
                "|---|---|---|---|---|---|---|"]
        for name, role, n, seller, tl in rows:
            out.append("| {} | {} | {} | {} | {} | {} | {} |".format(
                name, role, n, seller, *(c(x) for x in tl)))
        out.append("| **Toplam** | | | | **{}** | **{}** | **{}** |".format(
            *(c(board.at(t)) for t in bom.TIERS)))
        out.append("")
    out += ["### Başka kurulumlarda alıcılar", "",
            "| Kurulum | Araç alıcısı 1 / 100 / 1000 | Yaya alıcısı 1 / 100 / 1000 |",
            "|---|---|---|"]
    for setup in tool.setups().values():
        p = tool.prices(setup, bill)
        out.append("| {} | {} | {} |".format(setup.key, *(
            " / ".join(c(p[b][t]) for t in bom.TIERS) for b in ("vehicle", "pedestrian"))))
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix-rate", type=float, default=1.0,
                        help="fixes a second each receiver needs (default 1)")
    parser.add_argument("--out", help="also write the report to this Markdown file")
    args = parser.parse_args(argv)
    text = report(args.fix_rate)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
