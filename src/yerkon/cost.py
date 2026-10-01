"""What a deployment costs to build and what it costs to keep running.

Capital cost comes from the report's own bill of materials. Operating
cost comes from an inventory of named recurring items, each attached to a
countable thing in the deployment, because the usual shortcut of a fixed
percentage of capital produces a number with no mechanism behind it and
no way to check it. See ADR-0006.

This module knows nothing about radios, terrain or positions. It counts
things and prices them, so it can be read and argued with by somebody who
does not care how the link budget works. Every rate carries its own
provenance, and a costing reports the assumptions it rests on alongside
the total, because most of these rates are placeholders and a total that
hides that is worse than no total.
"""

from __future__ import annotations

from yerkon.numbers import added

from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import Provenance, Sourced
from yerkon.numbers import decimal_comma
from yerkon.settings import DEFAULTS, Settings


@dataclass(frozen=True)
class Product:
    """A line in the report's bill of materials."""

    name: str
    unit_price_tl: Sourced

    def __post_init__(self) -> None:
        if float(self.unit_price_tl.value) < 0.0:
            raise ValueError("a product does not pay you to buy it")


def _bom(key: str, name: str) -> Product:
    """A product priced from the itemised bill (`bom.py`, ADR-0105).

    Derived rather than read off a datasheet: the sum of every part at
    its seller's own price for that many boards.
    """
    from yerkon.bom import read

    bill = read()
    board = bill.boards[key]
    return Product(
        name=name,
        unit_price_tl=Sourced(
            round(bill.price(key), 2), "TL", Provenance.DERIVED,
            "bom.toml, every part at its seller's price ladder",
            note=(
                "{} units, priced part by part from the sellers."
                .format(bill.used_tier)
            ),
        ),
    )


#: The plain module's unit, without the frequency hopping certificate.
#: No row of the table uses it now; the simulator can (ADR-0094).
SX1280_ANCHOR = _bom("sx1280-anchor", "FHSS ve LBT belgesi olmayan yayın birimi")
#: The broadcast unit the town and the open country both use.
#:
#: They were two lines of the report because they carried two radio
#: modules. Certified as adaptive frequency hopping, both may radiate
#: 20 dBm, which the amplified module reaches (ADR-0099); with the same module they
#: are the same board (ADR-0079, ADR-0094).
AMPLIFIED_ANCHOR = _bom("amplified-anchor", "Şehir içi ve kırsal yayın birimi")
TUNNEL_ANCHOR = _bom("tunnel-anchor", "Kritik bölge yayın birimi")
PEDESTRIAN_RECEIVER = _bom("pedestrian", "Yaya alıcısı")
VEHICLE_RECEIVER = _bom("vehicle", "Kara aracı alıcısı")

PRODUCTS = {
    "anchor": SX1280_ANCHOR,
    "amplified": AMPLIFIED_ANCHOR,
    "tunnel": TUNNEL_ANCHOR,
    "pedestrian": PEDESTRIAN_RECEIVER,
    "vehicle": VEHICLE_RECEIVER,
}

def _board(key: str, remove=(), add=()):
    """A board of the bill with some parts taken off and others put on.

    For what the simulator can choose and no row of the table uses: the
    27 dBm module, a louder module on a receiver, and the antennas the
    rows carried before the hopping certificate (ADR-0091).
    """
    from dataclasses import replace

    from yerkon.bom import read

    bill = read()
    board = bill.boards[key]
    if not remove and not add:
        return board
    parts = list(board.parts)
    for gone in remove:
        parts.remove(next(p for p in parts if p.key == gone))
    parts += [bill.parts[extra] for extra in add]
    return replace(board, parts=tuple(parts))


def _priced(board, name: str, key: str, remove=(), add=()) -> Product:
    """A board as a line of the bill, at the tier the table uses."""
    from yerkon.bom import read

    tier = read().used_tier
    return Product(
        name=name,
        unit_price_tl=Sourced(
            round(board.at(tier), 2), "TL", Provenance.DERIVED,
            "bom.toml, {} with {} in place of {}".format(
                key, " and ".join(add) or "nothing", " and ".join(remove)),
            note="{} units, priced part by part from the sellers.".format(tier),
        ),
    )


#: The 27 dBm module's unit: the amplified board with the 27 dBm module
#: in place of the 20 dBm one. It used to be priced as the 20 dBm board,
#: which put 128 TL a unit on the wrong side.
E28_27S_ANCHOR = _priced(
    _board("amplified-anchor", ("e28-2g4m20s",), ("e28-2g4m27s",)),
    "Yayın birimi, E28-2G4M27S", "amplified-anchor",
    ("e28-2g4m20s",), ("e28-2g4m27s",))

#: Which line of the bill of materials a module is sold as.
#:
#: Keyed by part name rather than by the object, so this module still
#: needs to know nothing about radios. A corridor carrying three modules
#: is three different products, and pricing it as one would put a
#: thousand lira of difference per anchor in the wrong place.
ANCHOR_PRODUCT_BY_PART = {
    "EBYTE E28-2G4M12S": SX1280_ANCHOR,
    "EBYTE E28-2G4M20S": AMPLIFIED_ANCHOR,
    "EBYTE E28-2G4M27S": E28_27S_ANCHOR,
    "Qorvo DWM3000": TUNNEL_ANCHOR,
}

#: The board each module is built on, and what goes on it in place of
#: what the board carries as built.
_ANCHOR_BOARD = {
    "EBYTE E28-2G4M12S": ("sx1280-anchor", (), ()),
    "EBYTE E28-2G4M20S": ("amplified-anchor", (), ()),
    "EBYTE E28-2G4M27S": ("amplified-anchor", ("e28-2g4m20s",), ("e28-2g4m27s",)),
    "Qorvo DWM3000": ("tunnel-anchor", (), ()),
}

#: What an antenna puts on a board, by its part name. The 5 dBi rod sits
#: on the box's own connector; a mast or roof antenna needs a cable.
ANTENNA_PARTS = {
    "Taoglas GW.22.5151": ("gw-22-5151",),
    "TP-Link TL-ANT2412D": ("tl-ant2412d", "lmr200-pigtail"),
    "L-com HGV-2409U": ("hgv-2409u", "lmr200-pigtail"),
}

_ROD = ANTENNA_PARTS["Taoglas GW.22.5151"]
_SWAPPED: dict = {}


def _anchor_swaps(part: str, antenna: str) -> tuple:
    """The board a pole is built on, and the parts taken off and put on."""
    if part not in _ANCHOR_BOARD:
        raise ValueError(
            "no anchor product for {!r}. The bill of materials names: "
            "{}".format(part, ", ".join(sorted(ANCHOR_PRODUCT_BY_PART))))
    key, remove, add = _ANCHOR_BOARD[part]
    remove, add = list(remove), list(add)
    extra = ANTENNA_PARTS.get(antenna, _ROD)
    if extra != _ROD and key != "tunnel-anchor":
        remove.append("gw-22-5151")
        add.extend(extra)
    return key, tuple(remove), tuple(add)


def anchor_board(part: str, antenna: str = ""):
    """A pole's board as the bill builds it, with its antenna swapped in."""
    return _board(*_anchor_swaps(part, antenna))


def anchor_product(part: str, antenna: str = "") -> Product:
    """The bill-of-materials line for a module, by its part name.

    ``antenna`` is the pole antenna's part name. The boards in the bill
    carry the 5 dBi rod, so any other antenna the bill prices swaps it
    out; one it does not price, and the tunnel's module antenna, leave
    the board as it is.
    """
    key, remove, add = _anchor_swaps(part, antenna)
    product = ANCHOR_PRODUCT_BY_PART[part]
    if ANTENNA_PARTS.get(antenna, _ROD) == _ROD or key == "tunnel-anchor":
        return product
    cached = (part, antenna)
    if cached not in _SWAPPED:
        _SWAPPED[cached] = _priced(_board(key, remove, add),
                                   "{}, {}".format(product.name, antenna),
                                   key, remove, add)
    return _SWAPPED[cached]


#: The receiver boards, and the bill's keys for the 2,4 GHz module and
#: antenna each carries as built.
_RECEIVER_BOARD = {
    "vehicle": ("vehicle", "e28-2g4m20s", "gw-22-5151"),
    "pedestrian": ("pedestrian", "e28-2g4m20s", None),
}
_MODULE_KEY = {
    "EBYTE E28-2G4M12S": "e28-2g4m12s",
    "EBYTE E28-2G4M20S": "e28-2g4m20s",
    "EBYTE E28-2G4M27S": "e28-2g4m27s",
}


def _receiver_swaps(kind: str, parts, antenna: str) -> tuple:
    key, module, rod = _RECEIVER_BOARD[kind]
    remove, add = [], []
    carried = [_MODULE_KEY[p] for p in parts if p in _MODULE_KEY]
    if carried and carried[0] != module:
        remove.append(module)
        add.append(carried[0])
    wanted = ANTENNA_PARTS.get(antenna)
    if wanted and rod and wanted != _ROD:
        remove.append(rod)
        add.extend(wanted)
    return key, tuple(remove), tuple(add)


def receiver_board(kind: str, parts=(), antenna: str = ""):
    """A receiver's board with the modules and antenna it carries."""
    kind = kind if kind in _RECEIVER_BOARD else "vehicle"
    return _board(*_receiver_swaps(kind, parts, antenna))


def receiver_product(kind: str, parts=(), antenna: str = "",
                     base: Optional[Product] = None) -> Product:
    """A receiver's line of the bill, with the modules and antenna it
    carries.

    ``base`` is the board as built. A unit carrying another SX1280
    module, or another antenna the bill prices, swaps it in; anything
    else leaves the board as it is.
    """
    base = base or PRODUCTS.get(kind, VEHICLE_RECEIVER)
    if kind not in _RECEIVER_BOARD:
        return base
    key, remove, add = _receiver_swaps(kind, parts, antenna)
    if not remove:
        return base
    cached = (kind, remove, add)
    if cached not in _SWAPPED:
        _SWAPPED[cached] = _priced(_board(key, remove, add),
                                   "{}, {}".format(base.name, ", ".join(add)),
                                   key, remove, add)
    return _SWAPPED[cached]


@dataclass(frozen=True)
class AnchorSite:
    """One anchor, and what putting it where it is costs beyond the unit.

    Deliberately not a world object. Cost counts things; it does not need
    to know where anything stands, and keeping it that way means a
    costing can be checked without running a simulation.
    """

    product: Product
    structure: str
    site_cost_tl: Sourced
    #: How many of these sites a crew visits in a day. A visit costs this
    #: share of a crew day, per diem included.
    per_crew_day: float
    #: True when the structure already has mains power, so the anchor
    #: draws from it and pays a bill instead of carrying its own supply.
    has_power: bool = False
    #: True when the structure already carries a data connection.
    has_backhaul: bool = False
    #: What the structure's owner charges a year, where it is rented.
    rent_tl_per_year: float = 0.0
    #: A crew day here, where it differs from the operating one.
    crew_day_tl: Optional[float] = None

    def __post_init__(self) -> None:
        if self.per_crew_day <= 0.0:
            raise ValueError("a crew reaches at least part of a site a day")


@dataclass(frozen=True)
class Inventory:
    """Everything a deployment consists of, and the ground it serves."""

    anchors: tuple[AnchorSite, ...]
    #: Receivers bought, as (product, count). Whether these belong to the
    #: operator or to the vehicles is a question the report does not
    #: settle, so they are counted separately and never folded into the
    #: per-square-kilometre figures.
    receivers: tuple[tuple[Product, int], ...] = ()
    #: Ground on which a position is available, in km². See ADR-0012.
    service_area_km2: float = 0.0
    #: Length of road served, in km, for corridor deployments.
    route_km: float = 0.0
    #: Whether the maintenance crew leaves its base city to get here.
    crew_travels: bool = False

    def __post_init__(self) -> None:
        if not self.anchors:
            raise ValueError("an inventory with no anchors costs nothing")
        if self.service_area_km2 < 0.0 or self.route_km < 0.0:
            raise ValueError("an area is not negative")

    @property
    def off_grid_anchors(self) -> int:
        return sum(1 for anchor in self.anchors if not anchor.has_power)

    @property
    def unconnected_anchors(self) -> int:
        return sum(1 for anchor in self.anchors if not anchor.has_backhaul)


# --- The recurring items --------------------------------------------------


@dataclass(frozen=True)
class OperatingRates:
    """What each recurring item costs, per the thing it attaches to.

    Every field is a rate somebody could look up, argue with, or replace.
    That is the point of ADR-0006: a percentage of capital could be none
    of those things.

    None of them is written here. They come from the settings file, so
    replacing one is an edit to a file rather than a change to a program
    (ADR-0016).
    """

    electricity_tl_per_kwh: Sourced
    anchor_kwh_per_year: Sourced
    connectivity_tl_per_year: Sourced
    #: A standalone supply for an anchor on a structure with no mains.
    off_grid_supply_tl: Sourced
    #: How long a unit lasts before it is replaced.
    service_life_years: Sourced
    maintenance_visits_per_year: Sourced
    #: Off-grid sites need more attendance: batteries age and panels foul.
    extra_off_grid_visits_per_year: Sourced
    #: A day of the fitting and maintenance crew: truck, electrician, helper.
    crew_day_tl: Sourced
    #: Each anchor's yearly share of the central system, which is spread
    #: across a thousand anchors rather than added whole to every row.
    central_operation_tl_per_anchor_year: Sourced
    #: What a crew member is paid a day away from the base city (H Cetveli).
    per_diem_tl: Sourced
    #: The part of it a same-day trip earns (Harcırah Kanunu, Madde 39).
    per_diem_share: Sourced
    #: People in a maintenance crew.
    crew_size: Sourced
    #: The battery's part of the standalone supply, which wears out first.
    battery_tl: Sourced
    battery_life_years: Sourced
    #: The rest of the standalone supply: panel, controller, bracket, cable.
    off_grid_life_years: Sourced


def operating_rates(settings: Settings = DEFAULTS) -> OperatingRates:
    """The recurring rates, from a settings file."""
    return OperatingRates(
        **{
            name: settings.sourced("operating.{}".format(name))
            for name in OperatingRates.__dataclass_fields__
        }
    )


DEFAULT_RATES = operating_rates()


# --- A costing ------------------------------------------------------------


@dataclass(frozen=True)
class LineItem:
    """One named cost, and where its rate came from."""

    label: str
    tl: float
    basis: str
    provenance: Provenance
    note: str = ""

    @property
    def is_assumed(self) -> bool:
        return self.provenance is Provenance.ASSUMPTION


@dataclass(frozen=True)
class Costing:
    """What it costs to build, what it costs to run, and on what footing."""

    capital: tuple[LineItem, ...]
    operating: tuple[LineItem, ...]
    service_area_km2: float
    route_km: float
    receivers: tuple[LineItem, ...] = ()

    @property
    def capex_tl(self) -> float:
        return added(item.tl for item in self.capital)

    @property
    def opex_tl_per_year(self) -> float:
        return added(item.tl for item in self.operating)

    @property
    def receiver_tl(self) -> float:
        return added(item.tl for item in self.receivers)

    @property
    def capex_tl_per_km2(self) -> float:
        return self._per_km2(self.capex_tl)

    @property
    def opex_tl_per_km2_year(self) -> float:
        return self._per_km2(self.opex_tl_per_year)

    @property
    def capex_tl_per_route_km(self) -> float:
        if self.route_km <= 0.0:
            return float("nan")
        return self.capex_tl / self.route_km

    @property
    def opex_tl_per_route_km_year(self) -> float:
        if self.route_km <= 0.0:
            return float("nan")
        return self.opex_tl_per_year / self.route_km

    def _per_km2(self, total: float) -> float:
        if self.service_area_km2 <= 0.0:
            # Dividing by a service area of zero would produce infinity,
            # which reads as an answer. There is no answer.
            return float("nan")
        return total / self.service_area_km2

    @property
    def assumed_share(self) -> float:
        """How much of the total rests on figures nobody supplied.

        Printed with the total. A cost that is nine tenths assumption is
        a shape, not a price, and the reader should be told which.
        """
        total = self.capex_tl + self.opex_tl_per_year
        if total <= 0.0:
            return 0.0
        assumed = added(
            item.tl
            for item in self.capital + self.operating
            if item.is_assumed
        )
        return assumed / total

    def describe(self) -> str:
        lines = ["Capital:"]
        lines += [_line(item) for item in self.capital]
        lines.append("  {:<34}{:>14} TL".format(
            "total", decimal_comma(self.capex_tl, 2)))
        lines.append("")
        lines.append("Operating, per year:")
        lines += [_line(item) for item in self.operating]
        lines.append("  {:<34}{:>14} TL".format(
            "total", decimal_comma(self.opex_tl_per_year, 2)))
        if self.receivers:
            lines.append("")
            lines.append("Receivers, counted apart:")
            lines += [_line(item) for item in self.receivers]
        lines.append("")
        lines.append("Per square kilometre served ({} km²):".format(
            decimal_comma(self.service_area_km2, 2)))
        lines.append("  {:<34}{:>14} TL".format(
            "capital", decimal_comma(self.capex_tl_per_km2, 2)))
        lines.append("  {:<34}{:>14} TL/year".format(
            "operating", decimal_comma(self.opex_tl_per_km2_year, 2)))
        lines.append("")
        lines.append(
            "{}% of this rests on figures nobody supplied.".format(
                decimal_comma(100.0 * self.assumed_share, 0)
            )
        )
        return "\n".join(lines)


def _line(item: LineItem) -> str:
    mark = " (assumed)" if item.is_assumed else ""
    return "  {:<34}{:>14} TL   {}{}".format(
        item.label, decimal_comma(item.tl, 2), item.basis, mark
    )


def price(
    inventory: Inventory, rates: OperatingRates = DEFAULT_RATES
) -> Costing:
    """Everything the deployment costs, item by item."""
    anchors = len(inventory.anchors)
    off_grid = inventory.off_grid_anchors
    unconnected = inventory.unconnected_anchors

    units_tl = added(float(a.product.unit_price_tl.value) for a in inventory.anchors)
    sites_tl = added(float(a.site_cost_tl.value) for a in inventory.anchors)
    supplies_tl = off_grid * float(rates.off_grid_supply_tl.value)

    capital = (
        LineItem(
            "anchor units", units_tl,
            "{} units from the bill of materials".format(anchors),
            Provenance.DATASHEET,
        ),
        LineItem(
            "structures and installation", sites_tl,
            "{} sites".format(anchors),
            _weakest(a.site_cost_tl for a in inventory.anchors),
        ),
        LineItem(
            "standalone power", supplies_tl,
            "{} of {} sites have no mains".format(off_grid, anchors),
            rates.off_grid_supply_tl.provenance,
        ),
    )

    energy_tl = (
        (anchors - off_grid)
        * float(rates.anchor_kwh_per_year.value)
        * float(rates.electricity_tl_per_kwh.value)
    )
    rent_tl = added(a.rent_tl_per_year for a in inventory.anchors)
    rented = sum(1 for a in inventory.anchors if a.rent_tl_per_year > 0.0)
    connectivity_tl = unconnected * float(rates.connectivity_tl_per_year.value)
    # Each part over its own life in the tax depreciation list: the radio
    # unit, the battery, and the rest of the solar supply (ADR-0089).
    battery_tl = min(float(rates.battery_tl.value),
                     float(rates.off_grid_supply_tl.value))
    replacement_tl = (
        units_tl / max(float(rates.service_life_years.value), 1e-9)
        + off_grid * battery_tl
        / max(float(rates.battery_life_years.value), 1e-9)
        + off_grid * (float(rates.off_grid_supply_tl.value) - battery_tl)
        / max(float(rates.off_grid_life_years.value), 1e-9)
    )
    # Each site's visits are a share of a crew day: a crew reaches eight
    # columns in town but four poles kilometres apart (ADR-0101). The
    # per diem is paid by the day too, so it is shared the same way.
    visits = 0.0
    crew_days = 0.0
    maintenance_tl = 0.0
    for anchor in inventory.anchors:
        here = float(rates.maintenance_visits_per_year.value) + (
            0.0 if anchor.has_power
            else float(rates.extra_off_grid_visits_per_year.value))
        day_tl = (anchor.crew_day_tl if anchor.crew_day_tl is not None
                  else float(rates.crew_day_tl.value))
        visits += here
        crew_days += here / anchor.per_crew_day
        maintenance_tl += here * day_tl / anchor.per_crew_day
    per_diem_tl = (
        crew_days * float(rates.crew_size.value) * float(rates.per_diem_tl.value)
        * float(rates.per_diem_share.value)
        if inventory.crew_travels else 0.0
    )
    central_tl = anchors * float(rates.central_operation_tl_per_anchor_year.value)

    operating = (
        LineItem(
            "energy", energy_tl,
            "{} mains-fed anchors".format(anchors - off_grid),
            rates.anchor_kwh_per_year.provenance,
        ),
        LineItem(
            "connectivity", connectivity_tl,
            "{} anchors without existing backhaul".format(unconnected),
            rates.connectivity_tl_per_year.provenance,
        ),
        LineItem(
            "structure rent", rent_tl,
            "{} rented structures".format(rented),
            Provenance.ASSUMPTION if rented else Provenance.DATASHEET,
        ),
        LineItem(
            "replacement", replacement_tl,
            "units over {} years, batteries over {} (depreciation list)".format(
                decimal_comma(float(rates.service_life_years.value), 0),
                decimal_comma(float(rates.battery_life_years.value), 0),
            ),
            rates.service_life_years.provenance,
        ),
        LineItem(
            "maintenance", maintenance_tl,
            "{} visits a year".format(decimal_comma(visits, 1)),
            rates.crew_day_tl.provenance,
        ),
        LineItem(
            "per diem", per_diem_tl,
            "{} person-days away from the base city".format(
                decimal_comma(crew_days * float(rates.crew_size.value), 1))
            if inventory.crew_travels else "the crew stays in its city",
            rates.per_diem_tl.provenance,
        ),
        LineItem(
            "central operation", central_tl,
            "{} anchors at {} TL a year each".format(
                anchors,
                decimal_comma(
                    float(rates.central_operation_tl_per_anchor_year.value), 0
                ),
            ),
            rates.central_operation_tl_per_anchor_year.provenance,
        ),
    )

    receivers = tuple(
        LineItem(
            product.name,
            count * float(product.unit_price_tl.value),
            "{} units".format(count),
            product.unit_price_tl.provenance,
        )
        for product, count in inventory.receivers
    )

    return Costing(
        capital=capital,
        operating=operating,
        receivers=receivers,
        service_area_km2=inventory.service_area_km2,
        route_km=inventory.route_km,
    )


def _weakest(sources) -> Provenance:
    """The weakest provenance in a group, since that is what it rests on."""
    order = [
        Provenance.ASSUMPTION,
        Provenance.DERIVED,
        Provenance.STANDARD,
        Provenance.MEASUREMENT,
        Provenance.DATASHEET,
    ]
    found = [s.provenance for s in sources]
    if not found:
        return Provenance.ASSUMPTION
    return min(found, key=order.index)
