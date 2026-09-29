"""Compare radio hardware setups on the table's rows, every column.

    python tools/hardware.py                      every setup, city and country
    python tools/hardware.py --setup o4 --setup e28-20s --row urban
    python tools/hardware.py --search cheaper     place the poles for each setup
    python tools/hardware.py --tl-ant2412d-usd 97.32
    python tools/hardware.py --set urban.anchors_per_round=6 --row urban

Each setup names the pole's module and antenna, the vehicle's and the
pedestrian's modules and antennas, and the spectrum rule, and prices the
pole board from `bom.toml` with the parts it swaps. Everything else is
the row as the table runs it: the same site, poles, routes, settings and
random draws, at full resolution.

This is a local tool and stays out of the package on purpose: the site
and the simulator that runs in a visitor's browser are built from
`src/yerkon`, and nothing here reaches them.

Every exchange closes both ways, as the model runs it (ADR-0110), and
each run prices the pole with its own setup's board.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from yerkon import bom  # noqa: E402


# --- Parts the bill of materials no longer carries ---------------------------

def _part(key, name, ladder, seller, url, date, note=""):
    return bom.Part(key=key, name=name, role_tr=name, role_en=name,
                    seller=seller, url=url, ladder=tuple(ladder), date=date,
                    note=note)


#: The 27 dBm module. Its current manual and product page name the chip
#: SX1281, which has no ranging engine; the 2019 manual says SX1280.
E28_2G4M27S = _part(
    "e28-2g4m27s", "EBYTE E28-2G4M27S", [(1, 8.7416), (100, 8.4593)],
    "LCSC", "https://www.lcsc.com/product-detail/C411312.html",
    "before 28.09.2026", "LCSC's table ends at 100+")

#: The O4 pole antenna (ADR-0091). Discontinued. 50,66 USD was the Amazon
#: price on the parts list before 28 September; on 28 September ServerBlink
#: had it at 97,32 USD in stock, and Walmart listed 14,99 USD it could not
#: sell. `--tl-ant2412d-usd` moves it.
TL_ANT2412D_USD = 50.66


def tl_ant2412d(usd: float):
    return _part(
        "tl-ant2412d", "TP-Link TL-ANT2412D", [(1, usd)], "Amazon",
        "https://www.amazon.com/TP-Link-Outdoor-Omni-directional-Antenna-TL-ANT2412D/dp/B003CFATO2",
        "before 28.09.2026", "discontinued; no volume price published")


#: The O4 vehicle roof antenna. Microcom, 28 September 2026, ships in six
#: to eight weeks; DigiKey sells it at 154,71 USD for one, 130,21 at 25.
HGV_2409U = _part(
    "hgv-2409u", "L-com HGV-2409U", [(1, 58.95)], "Microcom",
    "https://www.microcom.us/hgv2409u.html", "28.09.2026",
    "no volume price published")

#: 0,3 m of LMR-200 from the board to a mast or roof antenna.
LMR200 = _part(
    "lmr200-pigtail", "LMR-200 anten kablosu", [(1, 9.50)], "Amazon",
    "https://www.amazon.com/LMR200-Double-Shielded-LMR-200-Pigtail/dp/B0DQ61NXP9",
    "before 28.09.2026", "no volume price published")


# --- Setups -------------------------------------------------------------------

@dataclass(frozen=True)
class Setup:
    """One way of equipping the town's and the open country's rows."""

    key: str
    title: str
    #: Keys in `hardware.radios()`, plus "e28-27s".
    pole: str
    vehicle: str = "e28"
    pedestrian: str = "e28"
    #: "rod" is the 5 dBi Taoglas GW.22.5151 the table uses; "mast" and
    #: "roof" are the O4 antennas; the pedestrian keeps its printed one.
    pole_antenna: str = "rod"
    vehicle_antenna: str = "rod"
    #: "printed" is the pedestrian's chip antenna; "uwb" is the DWM3000's
    #: own, which the tunnel row uses at every end.
    pedestrian_antenna: str = "printed"
    #: A key in `regulatory.REGIONS`.
    rule: str = "TR-FHSS"
    #: The pole board: a board in `bom.toml`, and the parts swapped on it.
    board: str = "amplified-anchor"
    remove: tuple = ()
    add: tuple = ()
    vehicle_remove: tuple = ()
    vehicle_add: tuple = ()
    pedestrian_remove: tuple = ()
    pedestrian_add: tuple = ()
    #: Settings this setup changes, as (key, value) pairs; --set wins.
    values: tuple = ()


def setups(tl_usd: float = TL_ANT2412D_USD) -> dict:
    mast = tl_ant2412d(tl_usd)
    return {s.key: s for s in (
        Setup("e28-20s", "E28-2G4M20S on every unit (published)", pole="e28"),
        Setup("e28-12s", "E28-2G4M12S on the pole, hopping certificate",
              pole="sx1280", board="sx1280-anchor"),
        Setup("e28-27s", "E28-2G4M27S on the pole, hopping certificate",
              pole="e28-27s", remove=("e28-2g4m20s",), add=(E28_2G4M27S,)),
        Setup("e28-12s-uncertified", "E28-2G4M12S on the pole, no certificate",
              pole="sx1280", board="sx1280-anchor", rule="TR"),
        Setup("o4", "O4: E28-2G4M12S, 12 dBi mast and 8 dBi roof antennas, no certificate",
              pole="sx1280", vehicle="sx1280", pole_antenna="mast",
              vehicle_antenna="roof", rule="TR", board="sx1280-anchor",
              remove=("gw-22-5151",), add=(mast, LMR200),
              vehicle_remove=("e28-2g4m20s", "gw-22-5151"),
              vehicle_add=("e28-2g4m12s", HGV_2409U, LMR200),
              pedestrian="sx1280", pedestrian_remove=("e28-2g4m20s",),
              pedestrian_add=("e28-2g4m12s",)),
        # The tunnel row: UWB as published, and the 2,4 GHz module in its
        # place. Run with --row tunnel.
        Setup("tunnel-dwm3000", "Tunnel: DWM3000 (published)", pole="dwm3000",
              pole_antenna="uwb", vehicle_antenna="uwb", pedestrian_antenna="uwb",
              rule="TR", board="tunnel-anchor"),
        # The tunnel's 2 m gate is set for UWB's decimetre ranging and
        # turns every LoRa range away; the 20S gets the city's 15 m gate.
        Setup("tunnel-e28-20s", "Tunnel: E28-2G4M20S on every unit, hopping certificate, 15 m gate",
              pole="e28", board="amplified-anchor",
              values=(("tunnel.accept_sigma_m", 15.0),)),
    )}


def board(bill, key: str, remove=(), add=()):
    """A board from the bill with parts taken off and put on.

    Parts put on are either a key in the bill or a part defined here.
    """
    base = bill.boards[key]
    parts = list(base.parts)
    for gone in remove:
        match = [p for p in parts if p.key == gone]
        if not match:
            raise KeyError("{} has no {}".format(key, gone))
        parts.remove(match[0])
    for extra in add:
        parts.append(bill.parts[extra] if isinstance(extra, str) else extra)
    return dataclasses.replace(base, parts=tuple(parts))


def prices(setup: Setup, bill=None) -> dict:
    """The pole, vehicle and pedestrian boards at 1, 100 and 1000, in TL."""
    bill = bill or bom.read()
    boards = {
        "pole": board(bill, setup.board, setup.remove, setup.add),
        "vehicle": board(bill, "vehicle", setup.vehicle_remove, setup.vehicle_add),
        "pedestrian": board(bill, "pedestrian", setup.pedestrian_remove,
                            setup.pedestrian_add),
    }
    return {name: {tier: round(b.at(tier), 2) for tier in bom.TIERS}
            for name, b in boards.items()}


# --- One run ----------------------------------------------------------------

def run_one(setup: Setup, row: str, aim: str,
            values: dict = None, fix_rate: float = 1.0) -> dict:
    """One row with one setup, in this process. Patches the model's module
    tables, so each run gets a process of its own (see `main`)."""
    import time

    from yerkon import cost, evaluate, hardware, ranging, scenarios
    from yerkon.evidence import Provenance, Sourced
    from yerkon.report import build
    from yerkon.settings import DEFAULTS

    bill = bom.read()
    priced = prices(setup, bill)
    values = {**dict(setup.values), **(values or {})}
    settings = DEFAULTS.with_values(values) if values else DEFAULTS

    original = scenarios.radios

    def radios(settings=DEFAULTS):
        found = original(settings)
        found["e28-27s"] = hardware._sx1280_family(
            "EBYTE E28-2G4M27S", 27.0,
            "EBYTE E28-2G4M27S product page, rated output power", settings)
        return found

    scenarios.radios = radios
    antennas = {"rod": hardware.GW_22_5151, "mast": hardware.TL_ANT2412D,
                "roof": hardware.HGV_2409U, "printed": hardware.W24P_U,
                "uwb": hardware.DWM3000_ANTENNA}
    scenarios.ROW_REGIONS[row] = setup.rule
    scenarios.ROW_ANTENNAS[row] = (antennas[setup.pole_antenna],
                                   {"vehicle": antennas[setup.vehicle_antenna],
                                    "pedestrian": antennas[setup.pedestrian_antenna]})
    scenarios.ROW_RADIOS[row] = (setup.pole, {
        "vehicle": (setup.vehicle, "dwm3000"),
        "pedestrian": (setup.pedestrian, "dwm3000"),
    })

    product = cost.Product(
        name=setup.title,
        unit_price_tl=Sourced(priced["pole"][bill.used_tier], "TL",
                              Provenance.DERIVED,
                              "bom.toml with this setup's parts"))
    module_part = radios()[setup.pole].part
    cost.ANCHOR_PRODUCT_BY_PART[module_part] = product


    start = time.time()
    extra = {}
    if aim:
        from yerkon.cost import operating_rates
        from yerkon.placement import deployed_with, mix, search

        grid = scenarios.catalogue(
            settings.with_values({row + ".layout": "grid"}))[row]
        answer = search(grid, scenarios.fetched(settings.text(row + ".site")),
                        row, aim, settings)
        deployed = deployed_with(grid, answer.problem, answer.chosen)
        extra = {"placed": {str(k): v for k, v in
                            mix(answer.problem, answer.chosen).items()}}
        rates = operating_rates(settings)
    else:
        deployed = scenarios.catalogue(settings)[row]
        rates = None
    deployed = dataclasses.replace(deployed, product=product)
    _, rows = build((deployed,), rates=rates)
    record = dataclasses.asdict(rows[0])
    from yerkon.ranging import exchange_duration_s

    dep = deployed.scenario.deployment
    exchange_s = exchange_duration_s(dep.anchors[0].radio, dep.scheme)
    per_second = dep.duty_cycle / exchange_s
    per_fix = dep.max_anchors_per_round
    record.update(
        exchange_ms=1000 * exchange_s, per_fix=per_fix, fix_rate=fix_rate,
        # The model's own assumption: every receiver of the row on one
        # medium, one exchange at a time.
        one_channel=per_second / (per_fix * fix_rate),
        # The ceiling: every pole answering at once.
        # Per route km where the row is costed by its length.
        busy_per_km2=len(dep.anchors) / (
            rows[0].area_km2 if rows[0].costed_by == "area" else deployed.route_km)
        * per_second / (per_fix * fix_rate),
        values=values or {})
    record.update(setup=setup.key, row=row, aim=aim,
                  anchors=len(deployed.scenario.deployment.anchors),
                  prices=priced, seconds=round(time.time() - start), **extra)
    return record


# --- Output -------------------------------------------------------------------

def c(x, n=2):
    return ("{:." + str(n) + "f}").format(x).replace(".", ",")


def table(records, chosen) -> str:
    out = []
    for row, title in (("urban", "City (Kızılay)"), ("rural", "Country (Polatlı)"),
                       ("tunnel", "Tunnel (per route km; area in km² of the bore)")):
        mine = [r for r in records if r["row"] == row]
        if not mine:
            continue
        out += ["## " + title, "",
                "| Setup | Poles | Poles a fix | Pole unit, 1000 | HPE P50 | HPE P95 | VPE P95 | "
                "Availability | Area km² | CAPEX TL/km² | OPEX TL/km²/yr | "
                "Receivers, one channel | Receivers/km², every pole busy |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in mine:
            out.append("| {} | {} | {} | {} | {} | {} | {} | %{} | {} | {} | {} | {} | {} |".format(
                r["setup"] + (" ({})".format(", ".join(
                    "{}={}".format(k, v) for k, v in r["values"].items())) if r.get("values") else ""),
                r["anchors"], r["per_fix"], c(r["prices"]["pole"]["1000"]),
                c(r["hpe_p50_m"]), c(r["hpe_p95_m"]), c(r["vpe_p95_m"]),
                c(100 * r["availability"]), c(r["area_km2"]),
                c(r["capex_tl_per_unit"], 0), c(r["opex_tl_per_unit_year"], 0),
                c(r["one_channel"], 1), c(r["busy_per_km2"], 2)))
        out.append("")
    out += ["## Boards (TL)", "",
            "| Setup | Pole 1 / 100 / 1000 | Vehicle 1 / 100 / 1000 | Pedestrian 1 / 100 / 1000 |",
            "|---|---|---|---|"]
    seen = {}
    for r in records:
        seen.setdefault(r["setup"], r["prices"])
    for key in chosen:
        if key in seen:
            p = seen[key]
            out.append("| {} | {} | {} | {} |".format(key, *(
                " / ".join(c(p[b][t]) for t in ("1", "100", "1000"))
                for b in ("pole", "vehicle", "pedestrian"))))
    return "\n".join(out)


def _values(pairs) -> dict:
    """KEY=VALUE pairs as settings values, numbers where they parse."""
    out = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        try:
            out[key] = float(value)
        except ValueError:
            out[key] = value
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare radio hardware setups on the city and country rows.")
    parser.add_argument("--setup", action="append",
                        help="a setup to run; repeat for several (default: all)")
    parser.add_argument("--row", action="append", choices=("urban", "rural", "tunnel"),
                        help="a row to run; repeat for both (default: both)")
    parser.add_argument("--search", choices=("cheaper", "better"),
                        help="search each setup's own poles before running it")
    parser.add_argument("--tl-ant2412d-usd", type=float, default=TL_ANT2412D_USD,
                        help="the O4 pole antenna's price (default %(default)s)")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="change a settings value for every run, e.g. "
                             "urban.anchors_per_round=6; repeat for several")
    parser.add_argument("--fix-rate", type=float, default=1.0,
                        help="fixes a second each receiver needs, for capacity (default 1)")
    parser.add_argument("--list", action="store_true", help="list the setups and stop")
    parser.add_argument("--out", help="also write the tables to this Markdown file")
    parser.add_argument("--one", nargs=2, metavar=("SETUP", "ROW"), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    known = setups(args.tl_ant2412d_usd)
    if args.list:
        for key, s in known.items():
            print("{:<22}{}".format(key, s.title))
        return 0
    if args.one:
        record = run_one(known[args.one[0]], args.one[1],
                         args.search or "",
                         values=_values(args.set), fix_rate=args.fix_rate)
        print(json.dumps(record, ensure_ascii=False))
        return 0

    chosen = args.setup or list(known)
    unknown = [s for s in chosen if s not in known]
    if unknown:
        print("unknown setup: {}".format(", ".join(unknown)), file=sys.stderr)
        return 2
    records = []
    for key in chosen:
        for row in args.row or ("urban", "rural"):
            # A tunnel setup is for the tunnel row and no other.
            if key.startswith("tunnel-") != (row == "tunnel"):
                continue
            print("running {} on {}".format(key, row), file=sys.stderr)
            command = [sys.executable, os.path.abspath(__file__), "--one", key, row,
                       "--tl-ant2412d-usd", str(args.tl_ant2412d_usd)]
            if args.search:
                command += ["--search", args.search]
            for pair in args.set:
                command += ["--set", pair]
            command += ["--fix-rate", str(args.fix_rate)]
            done = subprocess.run(command, capture_output=True, text=True)
            if done.returncode != 0:
                print(done.stderr[-2000:], file=sys.stderr)
                return 1
            records.append(json.loads(done.stdout.strip().splitlines()[-1]))
    text = table(records, chosen)
    print(text)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(text + "\n")
        with open(os.path.splitext(args.out)[0] + ".json", "w") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
