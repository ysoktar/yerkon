"""What a deployment costs to build and to run. See ADR-0006."""

import math

import pytest

from yerkon.cost import (
    DEFAULT_RATES,
    PRODUCTS,
    AMPLIFIED_ANCHOR,
    SX1280_ANCHOR,
    VEHICLE_RECEIVER,
    AnchorSite,
    Inventory,
    OperatingRates,
    Product,
    price,
)
from yerkon.evidence import Provenance
from yerkon.world import LIGHTING_COLUMN, SIGNALLED_COLUMN, TALL_MAST


def site(mounting=TALL_MAST, product=SX1280_ANCHOR):
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


def test_the_bill_starts_from_the_report_s_own_totals():
    """ADR-0079. With the report's parts in, the report's number comes out.

    The report prints a total per product and no part prices. The bill
    takes the named parts out at their distributor prices and calls what
    is left "other"; put the same parts back and the total is the
    report's to the lira, at one unit and at a hundred.
    """
    from yerkon.bom import read

    for board in read().boards.values():
        back = (board.other_usd + sum(p.usd for p in board.was)) * board.usd_try
        assert back == pytest.approx(board.report_one_tl)
        assert back * board.hundred_over_one == pytest.approx(
            board.report_hundred_tl)


def test_what_is_left_of_each_anchor_is_the_same_board():
    """The check that says the breakdown agrees with the report.

    Taking each anchor's named parts out of the report's total leaves
    power conversion, protection, connectors and an enclosure, which are
    the same whatever radio sits on the board. If the three remainders
    disagreed by much, a part price here would be wrong. They agree to
    within a dollar.
    """
    from yerkon.bom import read

    left = [read().boards[k].other_usd
            for k in ("sx1280-anchor", "amplified-anchor", "tunnel-anchor")]
    assert max(left) - min(left) < 1.0
    assert all(13.0 < usd < 22.0 for usd in left)


def test_no_part_is_swapped_for_a_dearer_one():
    from yerkon.bom import read

    for board in read().boards.values():
        for gone, came in board.swapped:
            assert came.usd < gone.usd, (board.key, gone.name, came.name)
        assert board.one_tl <= board.report_one_tl


def test_the_table_prices_hardware_for_the_network_it_runs():
    """A thousand units, because the operating model runs a thousand.

    The central system is shared across a thousand anchors in the
    operating rates. Pricing the hardware at a hundred while running it
    as one of a thousand put two network sizes in one row.
    """
    from yerkon.bom import read

    assert read().used_tier == int(
        float(DEFAULT_RATES.anchors_sharing_central_operation.value))
    board = read().boards["sx1280-anchor"]
    assert float(SX1280_ANCHOR.unit_price_tl.value) == pytest.approx(
        board.thousand_tl, abs=0.01)


def test_every_product_the_report_names_is_reachable():
    assert set(PRODUCTS) == {
        "anchor", "amplified", "tunnel", "pedestrian", "vehicle"
    }


def test_a_price_comes_from_the_bill_and_says_so():
    assert SX1280_ANCHOR.unit_price_tl.provenance is Provenance.DERIVED
    assert "bom.toml" in SX1280_ANCHOR.unit_price_tl.source


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


def test_a_junction_cabinet_saves_the_data_plan_and_nothing_else():
    """What reusing the city's own network is worth, and what it is not.

    A signalised junction already carries a line to the traffic
    management centre, so an anchor beside one buys no plan of its own.
    It is the same column at the same height for the same fitting cost,
    so the capital does not move. Only the connectivity line does, and
    only by the share of anchors that stand at a junction.
    """
    import dataclasses

    # Priced as if a line cost something. No unit buys one now
    # (ADR-0079), which would make this test pass on nothing.
    rates = dataclasses.replace(
        DEFAULT_RATES,
        connectivity_tl_per_year=dataclasses.replace(
            DEFAULT_RATES.connectivity_tl_per_year, value=1188.0),
    )
    plain = price(an_inventory(count=4, mounting=LIGHTING_COLUMN), rates)
    mixed = Inventory(
        anchors=(
            site(SIGNALLED_COLUMN), site(LIGHTING_COLUMN),
            site(LIGHTING_COLUMN), site(LIGHTING_COLUMN),
        ),
        service_area_km2=57.2, route_km=24.0,
    )
    connected = price(mixed, rates)

    assert connected.capex_tl == pytest.approx(plain.capex_tl)
    assert mixed.off_grid_anchors == 0, "every column has mains"
    assert mixed.unconnected_anchors == 3, "one of the four is at a junction"

    def line(costing, label):
        return next(i for i in costing.operating if i.label == label).tl

    rate = float(rates.connectivity_tl_per_year.value)
    assert line(plain, "connectivity") - line(connected, "connectivity") == (
        pytest.approx(rate)
    )
    for label in ("energy", "replacement", "maintenance", "central operation"):
        assert line(connected, label) == pytest.approx(line(plain, label))


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
    assert costing.receiver_tl == pytest.approx(
        100 * float(VEHICLE_RECEIVER.unit_price_tl.value))
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
    from yerkon.numbers import decimal_comma

    costing = price(an_inventory())
    printed = costing.describe()
    assert "rests on figures nobody supplied" in printed
    assert "(assumed)" in printed
    total = decimal_comma(costing.capex_tl, 2)
    assert "," in total and total in printed.replace(" ", "")


def test_a_rate_looks_sourced_only_when_it_names_its_source():
    """Most of them were supplied by nobody, and those must say so.

    ADR-0079 gave three of them something to rest on: a published tariff
    for the data plan, a datasheet sum for the energy, and two operating
    choices. Each of those names where it came from; everything else is
    still an assumption.
    """
    for name in OperatingRates.__dataclass_fields__:
        rate = getattr(DEFAULT_RATES, name)
        if rate.provenance is Provenance.ASSUMPTION:
            continue
        assert rate.provenance in (
            Provenance.DATASHEET, Provenance.DERIVED, Provenance.DESIGN), name
        if rate.provenance is not Provenance.DESIGN:
            assert not rate.source.startswith("bu proje"), name


# --- Pricing a mixed corridor ---------------------------------------------


def test_each_module_is_priced_as_its_own_line_of_the_bill():
    from yerkon.cost import TUNNEL_ANCHOR, anchor_product
    from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280

    assert anchor_product(SX1280.part) is SX1280_ANCHOR
    assert anchor_product(E28_2G4M27S.part) is AMPLIFIED_ANCHOR
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
        float(SX1280_ANCHOR.unit_price_tl.value) for _ in inventory.anchors
    )
    truthful = sum(
        float(site.product.unit_price_tl.value) for site in inventory.anchors
    )
    assert truthful != pytest.approx(one_product)


def test_no_unit_carries_a_sim_card():
    """ADR-0079. Nothing in the report asks for one.

    The first cost model gave every unit without a line a cellular plan
    of its own. The report only says the centre keeps the units' keys
    and records current; the tie runs through the tunnel's spine and
    the junction cabinets, and the receivers that range against a unit
    are what notice when it stops answering. No row pays for data.
    """
    from yerkon.scenarios import CHOICES

    assert float(DEFAULT_RATES.connectivity_tl_per_year.value) == 0.0
    for name, deployed in CHOICES.items():
        line = next(i for i in price(deployed.inventory(10.0)).operating
                    if i.label == "connectivity")
        assert line.tl == 0.0, name


def test_the_amplifier_buys_nothing_under_the_turkish_rule():
    """Why the open country lost its amplifier (ADR-0079).

    At the ranging bandwidth the density limit caps radiated power at
    about 12 dBm, which the plain module already reaches. Under the
    American rule the amplifier still speaks, which is why the part
    stays in the catalogue.
    """
    from yerkon.hardware import E28_2G4M27S, SX1280, W24P_U
    from yerkon.regulatory import TURKEY, UNITED_STATES

    gain = W24P_U.gain_dbi(0.0)
    bandwidth = float(SX1280.ranging_bandwidth_hz.value)

    def legal(rule, radio):
        return rule.permitted_eirp_dbm(
            bandwidth, gain, float(radio.max_output_dbm.value))

    assert legal(TURKEY, E28_2G4M27S) == pytest.approx(legal(TURKEY, SX1280))
    assert legal(UNITED_STATES, E28_2G4M27S) > legal(UNITED_STATES, SX1280)
