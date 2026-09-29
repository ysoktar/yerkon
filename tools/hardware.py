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


# --- The module experiment (29 September 2026) --------------------------------
#
# JLCPCB's parts API, 29 September 2026, every ladder as listed. Semtech's
# own board is the SX1280 datasheet's reference design (Rev 1.1, table
# 14-1), part for part.

JLC = "JLCPCB, 29.09.2026"


def _jlc(key, name, code, ladder, note=""):
    return _part(key, name, ladder, "JLCPCB",
                 "https://jlcpcb.com/partdetail/{}".format(code), "29.09.2026", note)


E28_12S_JLC = _jlc("x-e28-12s", "EBYTE E28-2G4M12S", "C411310",
                   [(1, 6.9639), (10, 5.9844), (30, 5.3866), (100, 4.8863)])
E28_20S_JLC = _jlc("x-e28-20s", "EBYTE E28-2G4M20S", "C411311",
                   [(1, 5.9584), (10, 5.8122)])
E28_12SX_JLC = _jlc("x-e28-12sx", "EBYTE E28-2G4M12SX", "C17916848",
                    [(1, 6.9899), (10, 6.0071), (30, 5.4077), (100, 4.9042)])
E28_20SX_JLC = _jlc("x-e28-20sx", "EBYTE E28-2G4M20SX", "C42377415",
                    [(1, 6.038), (10, 5.8853)])
SX1280_CHIP = _jlc("x-sx1280", "Semtech SX1280IMLTRT", "C125969",
                   [(1, 3.2716), (10, 3.1092), (30, 3.0117), (100, 2.9143),
                    (500, 2.8688), (1000, 2.8477)])
SX1281_CHIP = _jlc("x-sx1281", "Semtech SX1281IMLTRT", "C2151551",
                   [(1, 3.4828), (10, 2.9792), (30, 2.5683), (100, 2.2661),
                    (500, 2.1264), (1000, 2.0647)], "out of stock on 29.09.2026")
#: Semtech's reference design, less the chip: (part, count).
REFERENCE_RF = (
    (_jlc("x-nx2016sa", "NDK NX2016SA 52 MHz", "C6249276",
          [(1, 1.1615), (200, 0.4646), (500, 0.4484), (1000, 0.4403)],
          "out of stock on 29.09.2026"), 1),
    (_jlc("x-mlz2012", "TDK MLZ2012M150WT000 15 uH", "C383402",
          [(1, 0.0738), (100, 0.0626), (300, 0.0571), (2000, 0.0512)]), 1),
    (_jlc("x-lqw3n0", "Murata LQW15AN3N0B80D", "C2041661",
          [(1, 0.2512), (50, 0.2021), (150, 0.1812), (500, 0.1549), (2500, 0.1432)]), 1),
    (_jlc("x-lqw2n5", "Murata LQW15AN2N5C00D", "C703121",
          [(1, 0.0684), (100, 0.0564), (300, 0.0502), (1000, 0.0459)]), 1),
    (_jlc("x-c0p8", "Murata GRM1555C1HR80BA01D", "C76988",
          [(1, 0.0129), (500, 0.0107), (1500, 0.0095)]), 1),
    (_jlc("x-c1p2", "Murata GRM1555C1H1R2BA01D", "C76954",
          [(1, 0.0081), (1000, 0.0065)], "out of stock on 29.09.2026"), 2),
    (_jlc("x-c100p", "Murata GRM1555C1H101JA01D", "C77177",
          [(1, 0.0108), (500, 0.0086), (1500, 0.0073)]), 1),
    (_jlc("x-c0p5", "Murata GRM1555C1HR50WA01D", "C88941",
          [(1, 0.0156), (500, 0.0125), (1500, 0.0108)], "out of stock on 29.09.2026"), 1),
    (_jlc("x-c10n", "Murata GRM155R71E103KA01D", "C77013",
          [(1, 0.0101), (500, 0.008), (1500, 0.0069)]), 2),
    (_jlc("x-c100n", "Murata GRM155R71C104KA88D", "C71629",
          [(1, 0.0051), (1000, 0.0047), (3000, 0.0044)]), 2),
    (_jlc("x-c470n", "Murata GRM155R61A474KE15D", "C77003",
          [(1, 0.0169), (500, 0.0138), (1500, 0.0122)]), 1),
    (_jlc("x-r0", "Vishay CRCW04020000Z0ED", "C190119",
          [(1, 0.0031), (1000, 0.0025), (3000, 0.0021)]), 1),
)
UFL = _jlc("x-ufl", "Hirose U.FL-R-SMT-1(10)", "C88373",
           [(1, 0.2218), (50, 0.1776), (150, 0.1588), (500, 0.135), (2500, 0.1246)])
#: For the pedestrian when the module has an IPEX socket and no antenna.
FLEX = _jlc("x-flex", "Molex 1461530050 2,4 GHz flex antenna", "C916292",
            [(1, 2.474), (10, 2.0939), (30, 1.8568), (100, 1.5367), (500, 1.4263),
             (1000, 1.3792)])


def _assembly(extended: int, joints: int):
    """JLCPCB's assembly for the parts a board gains: 3,07 $ an extended
    part type an order, 0,0016 $ a joint a board (the rate `smt` uses)."""
    at = lambda boards: round(joints * 0.0016 + extended * 3.07 / boards, 4)
    return _part("x-smt-{}-{}".format(extended, joints),
                 "JLCPCB dizgi, eklenen parçalar", [(1, at(1)), (100, at(100)),
                                                     (1000, at(1000))],
                 "JLCPCB", "https://jlcpcb.com/help/article/pcb-assembly-price",
                 "29.09.2026", "{} extended part types, {} joints".format(
                     extended, joints))


#: The module's own antenna. EBYTE gives no gain; 0 dBi as ADR-0100.
def _on_board():
    from yerkon.evidence import Provenance, Sourced
    from yerkon.hardware import Antenna

    return Antenna(
        part="on-board antenna",
        peak_gain_dbi=Sourced(0.0, "dBi", Provenance.ASSUMPTION,
                              "EBYTE, module datasheets",
                              note="EBYTE gives no gain for its PCB antenna; "
                                   "0 dBi, as ADR-0100"),
        efficiency=Sourced(1.0, "fraction", Provenance.ASSUMPTION,
                           "EBYTE, module datasheets",
                           note="folded into the 0 dBi"),
        centre_frequency_hz=2442e6, bandwidth_hz=100e6)


ON_BOARD = _on_board()

SX1280_RADIO = ("Semtech SX1280 (own board)", 12.5,
                "Semtech SX1280 datasheet: +12,5 dBm",
                -132.0, "Semtech SX1280 datasheet: -132 dBm, SF12 203 kHz, typical")
EXPERIMENT_RADIOS = {
    "12s": ("EBYTE E28-2G4M12S (x)", 12.5,
            "EBYTE E28-2G4M12S datasheet: 12 / 12,5 / 14 dBm, typical",
            -129.0, "EBYTE E28-2G4M12S datasheet: -128 / -129 / -130 dBm, typical"),
    "12sx": ("EBYTE E28-2G4M12SX (x)", 13.0,
             "EBYTE E28-2G4M12SX: 12-14 dBm, no typical given; the middle",
             -129.0, "EBYTE E28-2G4M12SX: -128 to -130 dBm, no typical; the middle"),
    "20s": ("EBYTE E28-2G4M20S (x)", 20.0,
            "EBYTE E28-2G4M20S datasheet: 19 / 20 / 21 dBm, typical",
            -131.0, "EBYTE E28-2G4M20S datasheet: -130 / -131 / -132 dBm, typical"),
    "20sx": ("EBYTE E28-2G4M20SX (x)", 20.0,
             "EBYTE E28-2G4M20SX page: 19 / 20 / 21 dBm, typical",
             -131.0, "EBYTE E28-2G4M20SX page: -130 / -131 / -132 dBm, typical"),
}
EXPERIMENT_PARTS = {"12s": E28_12S_JLC, "12sx": E28_12SX_JLC,
                    "20s": E28_20S_JLC, "20sx": E28_20SX_JLC}
#: Only an IPEX socket: no antenna of their own.
IPEX_ONLY = {"12sx", "20sx"}


def experiment_setups() -> list:
    """Every module on every unit, with the 5 dBi rod on pole and vehicle
    and without it (the module's own antenna)."""
    out = []
    module = ("e28-2g4m20s",)
    for name, radio in EXPERIMENT_RADIOS.items():
        part = EXPERIMENT_PARTS[name]
        walk = (FLEX,) if name in IPEX_ONLY else ()
        for antenna in ("rod", "board"):
            if antenna == "board" and name in IPEX_ONLY:
                continue
            out.append(Setup(
                "x-{}-{}".format(name, antenna),
                "{} on every unit, {}".format(
                    radio[0], "5 dBi rod" if antenna == "rod" else "own antenna"),
                pole="e28", pole_antenna=antenna, vehicle_antenna=antenna,
                radio=radio, remove=module, add=(part,),
                vehicle_remove=module, vehicle_add=(part,),
                pedestrian_remove=module, pedestrian_add=(part,) + walk,
                strip=() if antenna == "rod" else ("gw-22-5151", "ipex-sma")))
    for chip, radio_part in (("sx1280", SX1280_CHIP), ("sx1281", SX1281_CHIP)):
        radio = SX1280_RADIO if chip == "sx1280" else (
            ("Semtech SX1281 (own board)",) + SX1280_RADIO[1:])
        for antenna in ("rod", "board"):
            ufl = (UFL,) if antenna == "rod" else ()
            # Joints: VQFN24 25, crystal 4, 13 two-pad parts, U.FL 3, less
            # the module's 16. Extended types: 13, and U.FL, less the module.
            joints = 25 + 4 + 13 * 2 + (3 if antenna == "rod" else 0) - 16
            extended = 13 + (1 if antenna == "rod" else 0) - 1
            rf = (radio_part,) + tuple((p, n) for p, n in REFERENCE_RF) + (
                (_assembly(extended, joints), 1),)
            out.append(Setup(
                "x-{}-{}".format(chip, antenna),
                "{} on every unit, {}".format(
                    radio[0], "5 dBi rod" if antenna == "rod" else "trace antenna"),
                pole="e28", pole_antenna=antenna, vehicle_antenna=antenna,
                radio=radio, remove=module, add=rf + ufl,
                vehicle_remove=module, vehicle_add=rf + ufl,
                pedestrian_remove=module, pedestrian_add=rf,
                strip=() if antenna == "rod" else ("gw-22-5151", "ipex-sma"),
                cannot=("Semtech: the SX1281 has no ranging engine"
                        if chip == "sx1281" else "")))
    return out


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
    #: A module the model does not name, as (part, output dBm, where the
    #: output is from, typical sensitivity dBm, where that is from). Every
    #: unit of the setup carries it. The model's SX1280 closes a link from
    #: a 6 dB noise figure and Semtech's -132 dBm; a module its maker
    #: rates less sensitive gets the difference added to the noise figure.
    radio: tuple = ()
    #: Parts put on every board of the setup, as (part, count), and keys
    #: taken off every board, from the main parts or the rest.
    extra: tuple = ()
    strip: tuple = ()
    #: Shown instead of results, for a setup that cannot range.
    cannot: str = ""


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
    ) + tuple(experiment_setups())}


def board(bill, key: str, remove=(), add=()):
    """A board from the bill with parts taken off and put on.

    Parts put on are either a key in the bill or a part defined here.
    """
    base = bill.boards[key]
    parts = list(base.parts)
    others = list(base.others)
    for gone in remove:
        match = [p for p in parts if p.key == gone]
        if match:
            parts.remove(match[0])
            continue
        match = [o for o in others if o[0].key == gone]
        if not match:
            raise KeyError("{} has no {}".format(key, gone))
        others.remove(match[0])
    for extra in add:
        if isinstance(extra, tuple):
            others.append(extra)
        else:
            parts.append(bill.parts[extra] if isinstance(extra, str) else extra)
    return dataclasses.replace(base, parts=tuple(parts), others=tuple(others))


def prices(setup: Setup, bill=None) -> dict:
    """The pole, vehicle and pedestrian boards at 1, 100 and 1000, in TL."""
    bill = bill or bom.read()
    boards = {
        "pole": board(bill, setup.board, setup.remove + setup.strip,
                      setup.add + setup.extra),
        "vehicle": board(bill, "vehicle", setup.vehicle_remove + setup.strip,
                         setup.vehicle_add + setup.extra),
        "pedestrian": board(bill, "pedestrian", setup.pedestrian_remove,
                            setup.pedestrian_add + setup.extra),
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
        if setup.radio:
            part, output, output_source, sensitivity, sensitivity_source = setup.radio
            base = found["e28"]
            found[setup.key] = dataclasses.replace(
                base, part=part,
                max_output_dbm=Sourced(output, "dBm", Provenance.DATASHEET,
                                       output_source),
                sensitivity_dbm=Sourced(sensitivity, "dBm", Provenance.DATASHEET,
                                        sensitivity_source),
                noise_figure_db=Sourced(
                    float(base.noise_figure_db.value) + (sensitivity + 132.0),
                    "dB", Provenance.DERIVED,
                    "the model's noise figure plus the datasheet's "
                    "sensitivity short of Semtech's -132 dBm"))
        return found

    scenarios.radios = radios
    antennas = {"rod": hardware.GW_22_5151, "mast": hardware.TL_ANT2412D,
                "roof": hardware.HGV_2409U, "printed": hardware.W24P_U,
                "uwb": hardware.DWM3000_ANTENNA, "board": ON_BOARD}
    scenarios.ROW_REGIONS[row] = setup.rule
    scenarios.ROW_ANTENNAS[row] = (antennas[setup.pole_antenna],
                                   {"vehicle": antennas[setup.vehicle_antenna],
                                    "pedestrian": antennas[setup.pedestrian_antenna]})
    own = setup.key if setup.radio else None
    scenarios.ROW_RADIOS[row] = (own or setup.pole, {
        "vehicle": (own or setup.vehicle, "dwm3000"),
        "pedestrian": (own or setup.pedestrian, "dwm3000"),
    })

    product = cost.Product(
        name=setup.title,
        unit_price_tl=Sourced(priced["pole"][bill.used_tier], "TL",
                              Provenance.DERIVED,
                              "bom.toml with this setup's parts"))
    module_part = radios()[own or setup.pole].part
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
