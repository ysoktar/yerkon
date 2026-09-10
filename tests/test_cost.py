"""What a deployment costs to build and to run. See ADR-0006."""

import math

import pytest

from yerkon.cost import (
    DEFAULT_RATES,
    PRODUCTS,
    RURAL_ANCHOR,
    URBAN_ANCHOR,
    VEHICLE_RECEIVER,
    AnchorSite,
    Inventory,
    OperatingRates,
    Product,
    price,
)
from yerkon.evidence import Provenance
from yerkon.world import LIGHTING_COLUMN, TALL_MAST


def site(mounting=TALL_MAST, product=RURAL_ANCHOR):
    return AnchorSite(
        product=product,
        structure=mounting.kind,
        site_cost_tl=mounting.site_cost_tl,
        has_power=mounting.has_power,
        has_backhaul=mounting.has_backhaul,
    )


def an_inventory(count=13, mounting=TALL_MAST, **kwargs):
    fields = dict(service_area_km2=57.2, route_km=24.0)
    fields.update(kwargs)
    return Inventory(anchors=tuple(site(mounting) for _ in range(count)), **fields)


# --- The bill of materials ------------------------------------------------


def test_the_prices_are_the_ones_the_report_published():
    assert float(URBAN_ANCHOR.unit_price_tl.value) == 1366.07
    assert float(RURAL_ANCHOR.unit_price_tl.value) == 1082.68
    assert float(VEHICLE_RECEIVER.unit_price_tl.value) == 4002.29


def test_every_product_the_report_names_is_reachable():
    assert set(PRODUCTS) == {
        "urban", "rural", "tunnel", "pedestrian", "vehicle"
    }


def test_a_price_comes_from_the_report_and_says_so():
    assert URBAN_ANCHOR.unit_price_tl.provenance is Provenance.DATASHEET
    assert "page 14" in URBAN_ANCHOR.unit_price_tl.source


def test_a_product_cannot_cost_less_than_nothing():
    from yerkon.evidence import Sourced

    with pytest.raises(ValueError, match="pay you to buy it"):
        Product(
            "free lunch",
            Sourced(-1.0, "TL", Provenance.ASSUMPTION, "nowhere", note="a test"),
        )


# --- Inventories ----------------------------------------------------------


def test_an_inventory_with_no_anchors_is_refused():
    with pytest.raises(ValueError, match="no anchors"):
        Inventory(anchors=())


def test_an_inventory_counts_what_the_structures_do_not_provide():
    mixed = Inventory(
        anchors=(site(TALL_MAST), site(LIGHTING_COLUMN), site(LIGHTING_COLUMN)),
        service_area_km2=10.0,
    )
    assert mixed.off_grid_anchors == 1, "only the mast has no mains"
    assert mixed.unconnected_anchors == 3, "none of them has backhaul"


# --- Capital --------------------------------------------------------------


def test_the_radios_are_a_rounding_error_beside_the_masts():
    """The finding the mixed-mounting strategy exists to act on.

    The bill of materials is the only sourced part of the capital cost
    and it is roughly one percent of it. What a deployment costs is
    decided by what the anchors are bolted to.
    """
    costing = price(an_inventory(mounting=TALL_MAST))
    units = next(item for item in costing.capital if item.label == "anchor units")
    assert units.tl / costing.capex_tl < 0.05


def test_existing_structures_cost_a_fraction_of_purpose_built_ones():
    masts = price(an_inventory(mounting=TALL_MAST)).capex_tl
    columns = price(an_inventory(mounting=LIGHTING_COLUMN)).capex_tl
    assert columns < masts / 10.0


def test_a_site_with_no_mains_has_to_carry_its_own_supply():
    off_grid = price(an_inventory(mounting=TALL_MAST))
    mains = price(an_inventory(mounting=LIGHTING_COLUMN))

    def supply(costing):
        return next(
            item.tl for item in costing.capital if item.label == "standalone power"
        )

    assert supply(off_grid) > 0.0
    assert supply(mains) == 0.0


# --- Operating ------------------------------------------------------------


def energy_of(costing):
    return next(item.tl for item in costing.operating if item.label == "energy")


def test_an_off_grid_anchor_pays_no_electricity_bill():
    """It has a panel instead, which was charged to capital."""
    assert energy_of(price(an_inventory(mounting=TALL_MAST))) == 0.0
    assert energy_of(price(an_inventory(mounting=LIGHTING_COLUMN))) > 0.0


def test_a_longer_service_life_costs_less_a_year():
    from dataclasses import replace

    def replacement(years):
        rates = replace(DEFAULT_RATES, service_life_years=_rate_of(years))
        costing = price(an_inventory(), rates)
        return next(
            item.tl for item in costing.operating if item.label == "replacement"
        )

    assert replacement(16.0) == pytest.approx(replacement(8.0) / 2.0)


def _rate_of(value, unit="years"):
    from yerkon.evidence import Sourced

    return Sourced(value, unit, Provenance.ASSUMPTION, "test", note="a test value")


def test_a_central_system_shared_wider_costs_each_deployment_less():
    """Which is why it is a rate and not a constant added to every row."""
    def central(sharing):
        from dataclasses import replace

        rates = replace(
            DEFAULT_RATES,
            anchors_sharing_central_operation=_rate_of(sharing, "anchors"),
        )
        costing = price(an_inventory(), rates)
        return next(
            item.tl for item in costing.operating
            if item.label == "central operation"
        )

    assert central(2000.0) == pytest.approx(central(1000.0) / 2.0)


def test_an_off_grid_site_is_visited_more_often():
    def maintenance(mounting):
        costing = price(an_inventory(mounting=mounting))
        return next(
            item.tl for item in costing.operating if item.label == "maintenance"
        )

    assert maintenance(TALL_MAST) > maintenance(LIGHTING_COLUMN)


def test_operating_cost_responds_to_node_count():
    """ADR-0006: a design change that halves the anchors halves most of it."""
    thirteen = price(an_inventory(count=13)).opex_tl_per_year
    twenty_six = price(an_inventory(count=26)).opex_tl_per_year
    assert twenty_six == pytest.approx(2.0 * thirteen, rel=0.01)


# --- Dividing by the ground it serves -------------------------------------


def test_no_service_area_gives_no_answer_rather_than_infinity():
    """Infinity reads as a number. There is no number here."""
    costing = price(an_inventory(service_area_km2=0.0))
    assert math.isnan(costing.capex_tl_per_km2)
    assert math.isnan(costing.opex_tl_per_km2_year)


def test_cost_per_square_kilometre_falls_as_the_served_area_grows():
    narrow = price(an_inventory(service_area_km2=15.2))
    wide = price(an_inventory(service_area_km2=75.2))
    assert wide.capex_tl_per_km2 < narrow.capex_tl_per_km2


def test_receivers_are_counted_apart_from_the_infrastructure():
    """Whether they belong to the operator is a question the report leaves open."""
    costing = price(
        Inventory(
            anchors=(site(),),
            receivers=((VEHICLE_RECEIVER, 100),),
            service_area_km2=10.0,
        )
    )
    assert costing.receiver_tl == pytest.approx(100 * 4002.29)
    assert costing.receiver_tl not in [item.tl for item in costing.capital]
    assert costing.capex_tl < costing.receiver_tl


# --- Saying what it rests on ----------------------------------------------


def test_a_costing_says_how_much_of_itself_nobody_supplied():
    costing = price(an_inventory())
    assert costing.assumed_share > 0.9


def test_the_structures_line_carries_the_weakest_provenance_under_it():
    costing = price(an_inventory())
    structures = next(
        item for item in costing.capital
        if item.label == "structures and installation"
    )
    assert structures.is_assumed


def test_the_description_warns_before_it_is_quoted():
    printed = price(an_inventory()).describe()
    assert "rests on figures nobody supplied" in printed
    assert "(assumed)" in printed
    assert "," in printed and "1242574,84" in printed.replace(" ", "")


def test_the_default_rates_are_all_marked_as_assumptions():
    """None of them was supplied, and none of them should look sourced."""
    for name in OperatingRates.__dataclass_fields__:
        rate = getattr(DEFAULT_RATES, name)
        assert rate.provenance is Provenance.ASSUMPTION, name


# --- Pricing a mixed corridor ---------------------------------------------


def test_each_module_is_priced_as_its_own_line_of_the_bill():
    from yerkon.cost import TUNNEL_ANCHOR, anchor_product
    from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280

    assert anchor_product(SX1280.part) is URBAN_ANCHOR
    assert anchor_product(E28_2G4M27S.part) is RURAL_ANCHOR
    assert anchor_product(DWM3000.part) is TUNNEL_ANCHOR


def test_a_module_the_report_does_not_name_is_refused_with_the_list():
    from yerkon.cost import anchor_product

    with pytest.raises(ValueError, match="bill of materials names"):
        anchor_product("Some Other Radio")


def test_a_corridor_of_three_modules_is_priced_as_three_products():
    """Pricing it as one puts hundreds of lira per anchor in the wrong place."""
    from yerkon.viewer.state import AnchorRun, from_scenario

    # A corridor carrying all three modules. Built here rather than asked
    # for as a mode: the modes are the table's three rows now, and any one
    # of them can hold runs of several modules, which is all a mixed
    # corridor ever was (ADR-0028).
    mixed = from_scenario("rural").merged({
        "width_m": 0.0,
        "runs": (
            AnchorRun("C", "sx1280", "column", 0.0, 3000.0, 400.0, 25.0),
            AnchorRun("M", "e28", "mast", 3500.0, 15_000.0, 2000.0, 400.0),
            AnchorRun("T", "dwm3000", "tunnel", 15_500.0, 17_500.0, 150.0, 4.0),
        ),
    })
    inventory = mixed.deployed().inventory(100.0)
    products = {site.product.name for site in inventory.anchors}
    assert len(products) == 3

    one_product = sum(
        float(URBAN_ANCHOR.unit_price_tl.value) for _ in inventory.anchors
    )
    truthful = sum(
        float(site.product.unit_price_tl.value) for site in inventory.anchors
    )
    assert truthful != pytest.approx(one_product)
