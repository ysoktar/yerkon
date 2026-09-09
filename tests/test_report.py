"""The four YERKON rows, and what they are allowed to claim."""

import math

import numpy as np
import pytest

from yerkon.cost import Costing, LineItem, price
from yerkon.evaluate import Samples
from yerkon.evidence import Provenance
from yerkon.report import (
    COLUMNS,
    WEIGHTED_ROW,
    Result,
    Row,
    as_markdown,
    as_text,
    build,
    footnotes,
    run,
    weighted,
)
from yerkon.scenarios import ALL, RURAL, TUNNEL, URBAN


def a_row(**overrides):
    fields = dict(
        system="YERKON (test)",
        technology="Karasal PNT",
        environment="Dış",
        hpe_p50_m=2.5,
        hpe_p95_m=8.0,
        vpe_p95_m=30.0,
        availability=0.9817,
        area_km2=57.2,
        capex_tl_per_km2=21723.34,
        opex_tl_per_km2_year=900.64,
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
    cells = a_row(capex_tl_per_km2=1242574.84, hpe_p50_m=2.5).cells()
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


# --- The weighted row ------------------------------------------------------


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


def test_the_weighted_row_is_not_an_average_of_the_percentiles():
    """ADR-0005. Averaging three P95 values does not produce a P95."""
    steady = made_up_result(URBAN, np.ones(1000), np.ones(1000))
    tailed = made_up_result(
        RURAL,
        np.concatenate([np.ones(900), np.full(100, 60.0)]),
        np.ones(1000),
    )

    average = 0.5 * (
        steady.samples.percentile(95)[0] + tailed.samples.percentile(95)[0]
    )
    row = weighted([steady, tailed])

    assert row.hpe_p95_m != pytest.approx(average, rel=0.05)


def test_the_weighted_row_is_named_as_the_report_names_it():
    assert weighted([made_up_result(URBAN, np.ones(50), np.ones(50))]).system == (
        WEIGHTED_ROW
    )


def test_a_weighted_row_needs_something_to_weigh():
    with pytest.raises(ValueError, match="needs rows to weigh"):
        weighted([])


def test_cost_per_square_kilometre_is_blended_and_not_summed():
    """Adding the areas would describe a network nobody proposed."""
    one = made_up_result(URBAN, np.ones(100), np.ones(100), capex=1e5)
    two = made_up_result(RURAL, np.ones(100), np.ones(100), capex=3e5)
    row = weighted([one, two])
    assert row.capex_tl_per_km2 < max(
        one.costing.capex_tl_per_km2, two.costing.capex_tl_per_km2
    )
    assert row.capex_tl_per_km2 > min(
        one.costing.capex_tl_per_km2, two.costing.capex_tl_per_km2
    )


# --- Running the real scenarios -------------------------------------------


def test_the_tunnel_serves_a_bore_and_not_a_plane():
    """Sweeping a grid around a tunnel would measure ground the model
    does not represent and the deployment cannot serve."""
    assert TUNNEL.served_km2() == pytest.approx(2.0 * 12.0 / 1000.0)
    assert URBAN.served_km2() is None
    assert RURAL.served_km2() is None


def test_the_three_scenarios_use_the_three_modules_the_report_assigns():
    from yerkon.hardware import DWM3000, E28_2G4M27S, SX1280

    assert URBAN.scenario.deployment.anchor_radio is SX1280
    assert RURAL.scenario.deployment.anchor_radio is E28_2G4M27S
    assert TUNNEL.scenario.deployment.anchor_radio is DWM3000


def test_every_scenario_carries_a_weight_and_they_are_not_all_equal():
    weights = [d.weight for d in ALL]
    assert all(w > 0.0 for w in weights)
    assert len(set(weights)) > 1


@pytest.mark.slow
def test_the_tunnel_row_beats_the_road_rows_on_accuracy():
    """An impulse radio at a hundred and fifty metres against a spread
    one at kilometres. If this ever inverts, something is wrong."""
    tunnel = run(TUNNEL).row()
    urban = run(URBAN).row()
    assert tunnel.hpe_p95_m < urban.hpe_p95_m / 3.0
    assert tunnel.vpe_p95_m < urban.vpe_p95_m


@pytest.mark.slow
def test_the_whole_block_is_four_rows():
    _, rows = build()
    assert len(rows) == 4
    assert rows[-1].system == WEIGHTED_ROW


@pytest.mark.slow
def test_the_notes_say_what_the_table_rests_on():
    results, rows = build((TUNNEL,))
    notes = footnotes(results, rows)
    assert "rests on rates nobody supplied" in notes
    assert "waveguide" in notes
    assert "not a service availability figure" in notes
    assert "ADR-0005" in notes


@pytest.mark.slow
def test_the_notes_never_print_a_service_area_without_the_reached_area():
    """ADR-0012. The gap between them is the finding."""
    results, rows = build((RURAL,))
    notes = footnotes(results, rows)
    assert "is not coverage" in notes
    assert "times more ground" in notes


@pytest.mark.slow
def test_running_the_block_twice_gives_the_same_table():
    first = as_markdown(build((TUNNEL,))[1])
    again = as_markdown(build((TUNNEL,))[1])
    assert first == again
