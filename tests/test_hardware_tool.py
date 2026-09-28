"""The local hardware comparison tool prices its boards from the bill.

Only the prices are checked here; a run takes minutes.
"""
import importlib.util
import pathlib
import sys

import pytest

from yerkon import bom

TOOL = pathlib.Path(__file__).resolve().parent.parent / "tools" / "hardware.py"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("hardware_tool", TOOL)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses look their module up by name while the class is built.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_published_setup_costs_what_the_bill_says(tool):
    bill = bom.read()
    priced = tool.prices(tool.setups()["e28-20s"], bill)
    for tier in bom.TIERS:
        assert priced["pole"][tier] == round(bill.boards["amplified-anchor"].at(tier), 2)
        assert priced["vehicle"][tier] == round(bill.boards["vehicle"].at(tier), 2)


def test_o4_swaps_the_rod_for_the_mast_antenna_and_its_cable(tool):
    bill = bom.read()
    o4 = tool.prices(tool.setups(50.66)["o4"], bill)["pole"][1000]
    plain = bill.boards["sx1280-anchor"].at(1000)
    rod = bill.parts["gw-22-5151"].at(1000)
    assert o4 == pytest.approx(plain + (50.66 + 9.50 - rod) * bill.usd_try, abs=0.01)


def test_the_mast_antenna_price_moves_only_o4(tool):
    cheap, dear = tool.setups(50.66), tool.setups(97.32)
    assert tool.prices(cheap["e28-20s"]) == tool.prices(dear["e28-20s"])
    assert tool.prices(dear["o4"])["pole"][1000] > tool.prices(cheap["o4"])["pole"][1000]


def test_the_tool_stays_out_of_the_package():
    # The site and the browser simulator are built from src/yerkon.
    assert "src" not in TOOL.parts


def test_capacity_is_the_air_time_shared_out():
    import sys

    sys.path.insert(0, str(TOOL.parent))
    import units

    from yerkon.ranging import exchange_duration_s
    from yerkon.scenarios import catalogue
    from yerkon.settings import DEFAULTS

    rows = {row[0]: row for row in units.capacity(1.0)}
    dep = catalogue(DEFAULTS)["urban"].scenario.deployment
    per_second = dep.duty_cycle / exchange_duration_s(dep.anchors[0].radio, dep.scheme)
    one_channel = rows["urban"][7]
    assert one_channel == pytest.approx(per_second / dep.max_anchors_per_round)
    # Every pole busy carries more than one channel, never less.
    assert rows["urban"][9] * rows["urban"][5] >= one_channel
