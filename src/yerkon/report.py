"""The four YERKON rows of the comparison table on page 15 of the report.

Ten columns: system, technology, environment, HPE at the fiftieth and
ninety-fifth percentiles, VPE at the ninety-fifth, availability, service
area, capital cost per square kilometre and operating cost per square
kilometre per year.

The report leaves that last column empty for all four rows. This project
fills it from an inventory of named recurring items (ADR-0006).

The fourth row is a weighted average, and it is not a separate
simulation. It combines the three scenarios' raw per-fix error samples
under fixed weights and recomputes its percentiles from the combination,
because averaging three ninety-fifth percentiles does not produce a
ninety-fifth percentile of anything (ADR-0005).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.cost import DEFAULT_RATES, Costing, Inventory, OperatingRates, price
from yerkon.evaluate import Samples, combine, coverage, run_scenario
from yerkon.numbers import decimal_comma
from yerkon.scenarios import ALL, Deployed

COLUMNS = (
    "Sistem",
    "Teknoloji",
    "Ortam",
    "HPE P50 [m]",
    "HPE P95 [m]",
    "VPE P95 [m]",
    "Kullanılabilirlik",
    "Alan [km²]",
    "CAPEX [TL/km²]",
    "OPEX [TL/km²/yıl]",
)

WEIGHTED_ROW = "YERKON Ağırlıklı Ortalama"


@dataclass(frozen=True)
class Row:
    """One line of the table, as numbers rather than as text."""

    system: str
    technology: str
    environment: str
    hpe_p50_m: float
    hpe_p95_m: float
    vpe_p95_m: float
    availability: float
    area_km2: float
    capex_tl_per_km2: float
    opex_tl_per_km2_year: float
    #: Ground a packet reaches, which is not the service area. Carried so
    #: the two are never printed apart (ADR-0012).
    reached_km2: Optional[float] = None
    #: Share of the cost figures resting on rates nobody supplied.
    assumed_share: float = 0.0

    def cells(self) -> tuple[str, ...]:
        return (
            self.system,
            self.technology,
            self.environment,
            decimal_comma(self.hpe_p50_m, 2),
            decimal_comma(self.hpe_p95_m, 2),
            decimal_comma(self.vpe_p95_m, 2),
            "%{}".format(decimal_comma(100.0 * self.availability, 2)),
            decimal_comma(self.area_km2, 2),
            decimal_comma(self.capex_tl_per_km2, 0),
            decimal_comma(self.opex_tl_per_km2_year, 0),
        )


@dataclass(frozen=True)
class Result:
    """Everything one scenario produced, kept together for auditing."""

    deployed: Deployed
    samples: Samples
    costing: Costing
    area_km2: float
    reached_km2: Optional[float]

    def row(self) -> Row:
        hpe_p50, _ = self.samples.percentile(50)
        hpe_p95, vpe_p95 = self.samples.percentile(95)
        return Row(
            system="YERKON ({})".format(self.deployed.scenario.name),
            technology=self.deployed.technology,
            environment=self.deployed.environment,
            hpe_p50_m=hpe_p50,
            hpe_p95_m=hpe_p95,
            vpe_p95_m=vpe_p95,
            availability=self.samples.availability,
            area_km2=self.area_km2,
            capex_tl_per_km2=self.costing.capex_tl_per_km2,
            opex_tl_per_km2_year=self.costing.opex_tl_per_km2_year,
            reached_km2=self.reached_km2,
            assumed_share=self.costing.assumed_share,
        )


def run(
    deployed: Deployed, rates: OperatingRates = DEFAULT_RATES
) -> Result:
    """Simulate one scenario and price what it took to build it."""
    samples = run_scenario(deployed.scenario)

    confined_km2 = deployed.served_km2()
    if confined_km2 is not None:
        area_km2, reached_km2 = confined_km2, None
    else:
        swept = coverage(
            deployed.scenario.deployment,
            deployed.scenario.terrain,
            resolution_m=deployed.coverage_resolution_m,
            margin_m=deployed.coverage_margin_m,
        )
        area_km2, reached_km2 = swept.fixable_km2, swept.reached_km2

    costing = price(deployed.inventory(area_km2), rates)
    return Result(deployed, samples, costing, area_km2, reached_km2)


def weighted(results: Sequence[Result]) -> Row:
    """The fourth row. Samples combined, not percentiles. ADR-0005."""
    if not results:
        raise ValueError("a weighted row needs rows to weigh")

    samples = combine(
        [(r.samples, r.deployed.weight) for r in results], WEIGHTED_ROW
    )
    hpe_p50, _ = samples.percentile(50)
    hpe_p95, vpe_p95 = samples.percentile(95)

    total_weight = sum(r.deployed.weight for r in results)

    def blended(value_of) -> float:
        return sum(
            r.deployed.weight * value_of(r) for r in results
        ) / total_weight

    return Row(
        system=WEIGHTED_ROW,
        technology="Karasal PNT",
        environment="İç + dış",
        hpe_p50_m=hpe_p50,
        hpe_p95_m=hpe_p95,
        vpe_p95_m=vpe_p95,
        availability=samples.availability,
        # Cost per square kilometre is already a ratio, so the blend is of
        # the ratios under the same weights the errors used. Adding the
        # areas would describe a network nobody proposed.
        area_km2=blended(lambda r: r.area_km2),
        capex_tl_per_km2=blended(lambda r: r.costing.capex_tl_per_km2),
        opex_tl_per_km2_year=blended(lambda r: r.costing.opex_tl_per_km2_year),
        assumed_share=blended(lambda r: r.costing.assumed_share),
    )


def build(
    deployments: Sequence[Deployed] = ALL,
    rates: OperatingRates = DEFAULT_RATES,
) -> tuple[tuple[Result, ...], tuple[Row, ...]]:
    """Every row of the block, and the results behind them."""
    results = tuple(run(d, rates) for d in deployments)
    rows = tuple(r.row() for r in results) + (weighted(results),)
    return results, rows


def as_markdown(rows: Sequence[Row]) -> str:
    """The table, in a form that can be pasted somewhere and read."""
    lines = [
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "|".join(["---"] * len(COLUMNS)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.cells()) + " |")
    return "\n".join(lines)


def as_text(rows: Sequence[Row]) -> str:
    """The table, aligned for a terminal."""
    grid = [COLUMNS] + [row.cells() for row in rows]
    widths = [max(len(line[i]) for line in grid) for i in range(len(COLUMNS))]
    out = []
    for index, line in enumerate(grid):
        out.append("  ".join(
            cell.ljust(widths[column]) if column < 3
            else cell.rjust(widths[column])
            for column, cell in enumerate(line)
        ))
        if index == 0:
            out.append("  ".join("-" * width for width in widths))
    return "\n".join(out)


def footnotes(results: Sequence[Result], rows: Sequence[Row]) -> str:
    """What the table rests on, printed with it rather than beside it."""
    lines = ["Notes:"]
    for result in results:
        row = result.row()
        if row.reached_km2 is not None:
            lines.append(
                "  {}: {} km² is where enough anchors are reachable for a "
                "position. A packet reaches {} km², which is {} times more "
                "ground and is not coverage (ADR-0012).".format(
                    result.deployed.scenario.name,
                    decimal_comma(row.area_km2, 2),
                    decimal_comma(row.reached_km2, 2),
                    decimal_comma(row.reached_km2 / max(row.area_km2, 1e-9), 1),
                )
            )
        else:
            lines.append(
                "  {}: the deployment serves a bore {} m wide over {} km, "
                "so its area is the carriageway itself and nothing else. "
                "Per square kilometre it therefore looks enormous beside "
                "the open-road rows, which is arithmetic and not a "
                "judgement: a tunnel serves a line. Compare it on cost per "
                "route kilometre instead. Propagation is modelled as level "
                "ground with no waveguide term, which understates what a "
                "real tunnel delivers.".format(
                    result.deployed.scenario.name,
                    decimal_comma(result.deployed.confined_width_m or 0.0, 0),
                    decimal_comma(result.deployed.route_km, 1),
                )
            )
        lines.append(
            "    {} anchors on {}: {} TL to build, {} TL a year to run, "
            "{} TL per route kilometre.".format(
                len(result.deployed.scenario.deployment.anchors),
                result.deployed.mounting.kind,
                decimal_comma(result.costing.capex_tl, 0),
                decimal_comma(result.costing.opex_tl_per_year, 0),
                decimal_comma(result.costing.capex_tl_per_route_km, 0),
            )
        )
        lines.append(
            "    {} of that rests on rates nobody supplied.".format(
                "%{}".format(decimal_comma(100.0 * row.assumed_share, 0))
            )
        )

    lines.append(
        "  Weights for the last row: {}. It combines the three scenarios' "
        "raw per-fix samples, not their percentiles (ADR-0005).".format(
            ", ".join(
                "{} {}".format(
                    r.deployed.scenario.name,
                    decimal_comma(r.deployed.weight, 2),
                )
                for r in results
            )
        )
    )
    lines.append(
        "  Availability counts modelled failures only: a link that did not "
        "close, a round with too few ranges, a solve that did not settle. "
        "It is not a service availability figure."
    )
    lines.append(
        "  No height constraint anywhere. VPE is what roadside geometry "
        "actually supports (ADR-0011)."
    )
    return "\n".join(lines)
