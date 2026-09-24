"""The YERKON rows, and what they are allowed to claim."""


import numpy as np
import pytest

from yerkon.cost import Costing, LineItem
from yerkon.evaluate import Samples
from yerkon.evidence import Provenance
from yerkon.report import (
    COLUMNS,
    Result,
    Row,
    as_markdown,
    as_text,
    build,
    footnotes,
    run,
)
from yerkon.scenarios import ALL, RURAL, TUNNEL, URBAN


def a_row(**overrides):
    fields = dict(
        system="YERKON (test)",
        technology="Karasal konumlandırma",
        environment="Dış",
        hpe_p50_m=2.5,
        hpe_p95_m=8.0,
        vpe_p95_m=30.0,
        availability=0.9817,
        area_km2=57.2,
        capex_tl_per_unit=21723.34,
        opex_tl_per_unit_year=900.64,
    )
    fields.update(overrides)
    return Row(**fields)


# --- The shape of the table -----------------------------------------------


def test_the_table_has_the_ten_columns_the_report_has():
    assert len(COLUMNS) == 10
    assert COLUMNS[0] == "Sistem"
    assert COLUMNS[-1] == "OPEX [TL/km²/yıl]"


def test_a_row_fills_every_column():
    assert len(a_row().cells()) == len(COLUMNS)


def test_the_opex_column_is_filled_rather_than_left_empty():
    """The report leaves it blank for all four YERKON rows.

    Filling it is the point of ADR-0006 and one of the two things this
    project was asked for.
    """
    opex = a_row().cells()[-1]
    assert opex not in {"", "-", "nan"}


def test_numbers_use_a_comma_and_no_thousands_separator():
    cells = a_row(capex_tl_per_unit=1242574.84, hpe_p50_m=2.5).cells()
    assert "2,50" in cells
    assert "1242575" in cells
    assert not any("." in cell for cell in cells[3:])


def test_availability_is_written_as_the_report_writes_it():
    assert a_row(availability=0.9817).cells()[6] == "%98,17"


def test_the_markdown_and_the_text_carry_the_same_numbers():
    rows = (a_row(), a_row(system="YERKON (other)"))
    markdown, text = as_markdown(rows), as_text(rows)
    for cell in rows[0].cells():
        assert cell in markdown
        assert cell in text


# --- Rows made from samples -------------------------------------------------


def made_up_result(deployed, horizontal, vertical, attempted=None, capex=1e5):
    horizontal = np.asarray(horizontal, dtype=float)
    vertical = np.asarray(vertical, dtype=float)
    samples = Samples(
        name=deployed.scenario.name,
        horizontal_error_m=horizontal,
        vertical_error_m=vertical,
        attempted=horizontal.size if attempted is None else attempted,
    )
    costing = Costing(
        capital=(LineItem("units", capex, "test", Provenance.DATASHEET),),
        operating=(LineItem("running", capex / 20.0, "test", Provenance.ASSUMPTION),),
        service_area_km2=10.0,
        route_km=10.0,
    )
    return Result(deployed, samples, costing, 10.0, 40.0)


def test_the_tunnel_serves_a_bore_and_not_a_plane():
    """Sweeping a grid around a tunnel would measure ground the model
    does not represent and the deployment cannot serve."""
    assert TUNNEL.served_km2() == pytest.approx(2.0 * 12.0 / 1000.0)
    assert URBAN.served_km2() is None
    assert RURAL.served_km2() is None


def test_the_three_scenarios_use_the_modules_the_bill_assigns():
    """The town and the open country share a board now (ADR-0079).

    The report gave the open country the amplified E28-2G4M27S. Under
    the Turkish density limit its amplifier cannot speak at the ranging
    bandwidth, so the rural row carries the plain module and reads the
    same to the digit.
    """
    from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280

    def radios(deployed):
        return {a.radio for a in deployed.scenario.deployment.anchors}

    assert radios(URBAN) == {SX1280}
    assert radios(RURAL) == {SX1280}
    assert E28_2G4M27S not in radios(RURAL)
    assert radios(TUNNEL) == {DWM3000}


def test_every_unit_carries_both_modules_as_the_bill_of_materials_says():
    """Both receivers list an SX1280 and a DWM3000. That is what lets one
    unit work on the road and in a bore without changing."""
    from yerkon.hardware import DWM3000, SX1280

    for deployed in ALL:
        for unit in deployed.scenario.deployment.receivers:
            assert SX1280 in unit.radios
            assert DWM3000 in unit.radios


def test_every_scenario_carries_more_than_one_unit():
    """A deployment serves traffic, not one vehicle, and the air they
    share is what decides how often each is fixed."""
    for deployed in ALL:
        assert len(deployed.scenario.deployment.receivers) >= 2


def test_a_scenario_prices_the_units_it_actually_carries():
    inventory = URBAN.inventory(5.0)
    names = {product.name for product, _ in inventory.receivers}
    assert names == {"Kara aracı alıcısı", "Yaya alıcısı"}


def test_no_scenario_carries_a_journey_share_any_more():
    """ADR-0068. It existed for the weighted row and went with it."""
    assert not hasattr(ALL[0], "weight")


@pytest.mark.slow
def test_the_tunnel_measures_a_range_far_better_than_the_town_does():
    """An impulse radio against a spread one. If this inverts, something broke.

    This is a claim about ranging and only about ranging. It used to be
    written as a claim about position — that the tunnel row must beat the
    urban row by three times — and the area rewrite falsified it: the
    tunnel now ranges twenty-nine times better and positions no better at
    all. That was not a regression, and a test that called it one would
    have argued for undoing the fix.
    """
    tunnel = run(TUNNEL)
    urban = run(URBAN)
    assert tunnel.samples.median_range_sigma_m < (
        urban.samples.median_range_sigma_m / 10.0
    )


@pytest.mark.slow
def test_a_bore_turns_its_ranging_advantage_into_no_advantage_at_all():
    """ADR-0020. The geometry, not the radio, is what the tunnel row is about.

    Every anchor in a bore stands within a few metres of one line, so the
    arrangement multiplies a range error instead of averaging it down,
    and a town full of anchors on a grid does the opposite. Twenty-nine
    times better ranging therefore arrives as no better a position, and
    the number that says so is the ratio of position error to range
    error: far above one in the bore, below one in the town.
    """
    tunnel, urban = run(TUNNEL), run(URBAN)

    def amplification(result):
        return result.row().hpe_p50_m / result.samples.median_range_sigma_m

    assert amplification(tunnel) > 5.0
    assert amplification(urban) < 1.0


@pytest.mark.slow
def test_the_tunnel_still_supports_the_height_the_open_road_cannot():
    """Anchors that surround a receiver make the vertical observable.

    Anchors beside it do not, whatever shape the site is (ADR-0011), and
    this is the one comparison between the rows that the area rewrite
    left standing.
    """
    assert run(TUNNEL).row().vpe_p95_m < run(URBAN).row().vpe_p95_m


def test_the_whole_block_is_one_row_per_deployment(monkeypatch):
    """ADR-0068. There is no weighted row any more.

    A claim about the table's shape, so the simulations are stood in
    for: every draw of every row comes back as a made-up result, and
    `build` still does the part this is about, which is folding the
    draws back into one row per deployment. Run for real it was the
    publishing run, eight draws of three rows at full resolution, and
    the slowest test in the suite at nearly ten minutes.
    """
    import yerkon.report as report

    monkeypatch.setattr(report, "spread", lambda work, jobs: tuple(
        made_up_result(deployed, [1.0, 2.0], [3.0, 4.0])
        for deployed, *_ in jobs))
    _, rows = build()
    assert len(rows) == 3
    assert [row.system for row in rows] == [
        "YERKON ({})".format(d.scenario.name) for d in ALL
    ]


@pytest.mark.slow
def test_the_notes_say_what_the_table_rests_on():
    results, rows = build((TUNNEL,))
    notes = footnotes(results, rows)
    assert "rests on rates nobody supplied" in notes
    assert "waveguide" in notes
    assert "not a service availability figure" in notes
    # The weights line carried the ADR-0005 citation and went with the
    # weighted row (ADR-0068). What the notes still have to say is where
    # the height constraint went.
    assert "ADR-0011" in notes


@pytest.mark.slow
def test_the_notes_never_print_a_service_area_without_the_reached_area():
    """ADR-0012. The gap between them is the finding.

    Read coarsely: the two areas and the gap between them come from a
    sweep, and the sweep does not need eight draws or full-resolution
    profiles to show that one is several times the other.
    """
    from yerkon.settings import hurried

    results, rows = build(settings=hurried(), only=("rural",))
    notes = footnotes(results, rows)
    assert "is not coverage" in notes
    assert "times more ground" in notes


@pytest.mark.slow
def test_running_the_block_twice_gives_the_same_table():
    first = as_markdown(build((TUNNEL,))[1])
    again = as_markdown(build((TUNNEL,))[1])
    assert first == again


# --- The sweep and the journey converge at different rates (ADR-0055) -----


def test_the_sweep_is_run_fewer_times_than_the_journey():
    """Measured rather than assumed. An area is an average over
    thousands of cells and settles at once — over Kızılay three draws
    give 6,19, 6,32 and 6,28 km². A ninety-fifth percentile is a tail
    and settles slowly: the rural row's went 279,6 m on one draw, 32,0
    over five, and sits at 24 to 26 m only from eight onwards. Sweeping
    eight times would double what the table costs to answer a question
    that was already answered.
    """
    from yerkon.report import AREA_DRAWS, draws_of
    from yerkon.scenarios import CHOICES

    urban = CHOICES["urban"]
    assert AREA_DRAWS < urban.shadow_draws
    assert len(draws_of(urban)[:AREA_DRAWS]) == AREA_DRAWS


def test_a_row_with_no_shadows_to_draw_is_still_a_row():
    """A deployment can name eight draws over ground that has no
    shadowing on it — a hand-built one, or a settings file with the
    spread set to zero. Then there is one arrangement and every draw is
    that one, rather than an index past the end of a list."""
    from dataclasses import replace

    from yerkon.report import draws_of, run
    from yerkon.scenarios import CHOICES

    urban = CHOICES["urban"]
    bare = replace(urban, scenario=replace(
        urban.scenario, terrain=replace(urban.scenario.terrain,
                                        shadowing=None)))
    assert bare.shadow_draws > 1 and len(draws_of(bare)) == 1
    first = run(bare, draw=0, with_area=False).samples.percentile(50)[0]
    for draw in (3, 7, 99):
        assert run(bare, draw=draw,
                   with_area=False).samples.percentile(50)[0] == first
