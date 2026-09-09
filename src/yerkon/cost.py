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

from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.evidence import Provenance, Sourced
from yerkon.numbers import decimal_comma


@dataclass(frozen=True)
class Product:
    """A line in the report's bill of materials."""

    name: str
    unit_price_tl: Sourced

    def __post_init__(self) -> None:
        if float(self.unit_price_tl.value) < 0.0:
            raise ValueError("a product does not pay you to buy it")


def _bom(name: str, price_tl: float) -> Product:
    return Product(
        name=name,
        unit_price_tl=Sourced(
            price_tl, "TL", Provenance.DATASHEET,
            "YERKON report, bill of materials, page 14",
            note="Hundred-unit tier, priced 6 September 2026.",
        ),
    )


URBAN_ANCHOR = _bom("Şehir içi yayın birimi", 1366.07)
RURAL_ANCHOR = _bom("Kırsal yayın birimi", 1082.68)
TUNNEL_ANCHOR = _bom("Kritik bölge yayın birimi", 1634.44)
PEDESTRIAN_RECEIVER = _bom("Yaya alıcısı", 3117.74)
VEHICLE_RECEIVER = _bom("Kara aracı alıcısı", 4002.29)

PRODUCTS = {
    "urban": URBAN_ANCHOR,
    "rural": RURAL_ANCHOR,
    "tunnel": TUNNEL_ANCHOR,
    "pedestrian": PEDESTRIAN_RECEIVER,
    "vehicle": VEHICLE_RECEIVER,
}


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
    #: True when the structure already has mains power, so the anchor
    #: draws from it and pays a bill instead of carrying its own supply.
    has_power: bool = False
    #: True when the structure already carries a data connection.
    has_backhaul: bool = False


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


def _rate(value: float, unit: str, what: str) -> Sourced:
    return Sourced(
        value, unit, Provenance.ASSUMPTION, "this project",
        note=(
            "No figure for {} was supplied. It is configuration: set it in "
            "the scenario. Until it is sourced, any total containing it is "
            "an order of magnitude, not a price.".format(what)
        ),
    )


@dataclass(frozen=True)
class OperatingRates:
    """What each recurring item costs, per the thing it attaches to.

    Every field is a rate somebody could look up, argue with, or replace.
    That is the point of ADR-0006: a percentage of capital could be none
    of those things.
    """

    electricity_tl_per_kwh: Sourced = _rate(3.20, "TL/kWh", "the tariff an anchor draws on")
    anchor_kwh_per_year: Sourced = _rate(35.0, "kWh/year", "an anchor's annual consumption")
    connectivity_tl_per_year: Sourced = _rate(600.0, "TL/year", "a cellular data plan per anchor")
    #: A standalone supply for an anchor on a structure with no mains.
    off_grid_supply_tl: Sourced = _rate(9500.0, "TL", "a solar panel, battery and regulator")
    #: How long a unit lasts before it is replaced.
    service_life_years: Sourced = _rate(8.0, "years", "the service life of an outdoor unit")
    maintenance_visits_per_year: Sourced = _rate(0.5, "visits/year", "scheduled attendance at an anchor")
    #: Off-grid sites need more attendance: batteries age and panels foul.
    extra_off_grid_visits_per_year: Sourced = _rate(0.5, "visits/year", "the extra attendance an off-grid site needs")
    maintenance_tl_per_visit: Sourced = _rate(1800.0, "TL/visit", "a crew, a vehicle and traffic management")
    central_operation_tl_per_year: Sourced = _rate(240_000.0, "TL/year", "running the central system")
    #: Anchors the central system is shared across. A national network
    #: amortises it far wider than one corridor does, which is why this
    #: is a rate rather than a constant added to every deployment.
    anchors_sharing_central_operation: Sourced = _rate(1000.0, "anchors", "the network the central system serves")


DEFAULT_RATES = OperatingRates()


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
        return sum(item.tl for item in self.capital)

    @property
    def opex_tl_per_year(self) -> float:
        return sum(item.tl for item in self.operating)

    @property
    def receiver_tl(self) -> float:
        return sum(item.tl for item in self.receivers)

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
        assumed = sum(
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

    units_tl = sum(float(a.product.unit_price_tl.value) for a in inventory.anchors)
    sites_tl = sum(float(a.site_cost_tl.value) for a in inventory.anchors)
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
    connectivity_tl = unconnected * float(rates.connectivity_tl_per_year.value)
    replacement_tl = (units_tl + supplies_tl) / max(
        float(rates.service_life_years.value), 1e-9
    )
    visits = anchors * float(rates.maintenance_visits_per_year.value) + (
        off_grid * float(rates.extra_off_grid_visits_per_year.value)
    )
    maintenance_tl = visits * float(rates.maintenance_tl_per_visit.value)
    central_tl = (
        anchors
        * float(rates.central_operation_tl_per_year.value)
        / max(float(rates.anchors_sharing_central_operation.value), 1e-9)
    )

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
            "replacement", replacement_tl,
            "over {} years of service life".format(
                decimal_comma(float(rates.service_life_years.value), 0)
            ),
            rates.service_life_years.provenance,
        ),
        LineItem(
            "maintenance", maintenance_tl,
            "{} visits a year".format(decimal_comma(visits, 1)),
            rates.maintenance_tl_per_visit.provenance,
        ),
        LineItem(
            "central operation", central_tl,
            "{} anchors' share of a system serving {}".format(
                anchors,
                decimal_comma(
                    float(rates.anchors_sharing_central_operation.value), 0
                ),
            ),
            rates.central_operation_tl_per_year.provenance,
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
