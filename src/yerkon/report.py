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

import math
import textwrap
from dataclasses import dataclass, replace
from typing import Optional, Sequence

from yerkon.cost import (
    DEFAULT_RATES,
    Costing,
    OperatingRates,
    operating_rates,
    price,
)
from yerkon.budget import Dissection
from yerkon.evaluate import Samples, combine, coverage, pooled, run_scenario
from yerkon.parallel import spread
from yerkon.numbers import decimal_comma
from yerkon.scenarios import ALL, Deployed, catalogue, reweighted
from yerkon.settings import Settings

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


#: How many arrangements of shadows the coverage sweep is run over.
#:
#: Fewer than the journey, because the two converge at completely
#: different rates and it is measured rather than assumed. An area is an
#: average over thousands of cells and settles at once: over Kızılay,
#: three draws give 6,19, 6,32 and 6,28 km². A ninety-fifth percentile
#: is a tail and settles slowly: the rural row's went 279,6 m on one
#: draw, 32,0 over five, and only from eight onwards does it sit still
#: at 24 to 26 m. Running the sweep the same number of times would
#: double what the table costs to answer a question that was already
#: answered (ADR-0055).
AREA_DRAWS = 3


def draws_of(deployed: Deployed) -> tuple:
    """This row once per arrangement of shadows it is run over.

    Each draw is the same deployment over the same ground with the vans
    and hedges and building corners the model does not carry arranged
    one way rather than another (ADR-0055). The seeds run upward from
    the one the settings name, so the first draw is the arrangement a
    single run would have used.
    """
    ground = deployed.scenario.terrain
    shadowing = getattr(ground, "shadowing", None)
    how_many = max(int(deployed.shadow_draws), 1)
    if shadowing is None or shadowing.sigma_db <= 0.0 or how_many == 1:
        return (deployed.scenario,)
    return tuple(
        replace(deployed.scenario, terrain=replace(
            ground, shadowing=replace(shadowing, seed=shadowing.seed + step)))
        for step in range(how_many)
    )


def run(
    deployed: Deployed, rates: Optional[OperatingRates] = None,
    draw: int = 0, with_area: bool = True,
) -> Result:
    """Simulate one arrangement of this scenario and price it.

    One draw, because that is what a simulation is: this is the unit the
    report pools rather than the pooling itself (ADR-0055). ``draw``
    picks which arrangement of shadows, and ``with_area`` skips the
    coverage sweep for the draws whose area is not wanted — an area is
    an average over thousands of cells and settles at once, where a
    ninety-fifth percentile is a tail and does not.
    """
    rates = DEFAULT_RATES if rates is None else rates
    # Against what there is rather than what was asked for: a row can
    # name eight draws over ground with no shadows to draw, and then
    # there is one arrangement and every draw is it.
    scenarios = draws_of(deployed)
    scenario = scenarios[min(max(draw, 0), len(scenarios) - 1)]
    samples = run_scenario(scenario)

    confined_km2 = deployed.served_km2()
    if confined_km2 is not None:
        area_km2, reached_km2 = confined_km2, None
    elif with_area:
        swept = coverage(
            scenario.deployment,
            scenario.terrain,
            resolution_m=deployed.coverage_resolution_m,
            margin_m=deployed.coverage_margin_m,
        )
        area_km2, reached_km2 = swept.fixable_km2, swept.reached_km2
    else:
        # This draw is here for its samples. The area is somebody else's
        # answer and is folded in from the draws that computed one.
        area_km2, reached_km2 = math.nan, math.nan

    costing = price(deployed.inventory(
        area_km2 if math.isfinite(area_km2) else 1.0), rates)
    return Result(deployed, samples, costing, area_km2, reached_km2)


def folded(draws: Sequence[Result], rates: OperatingRates) -> Result:
    """Several draws of one row, as the row.

    The samples pool, because a percentile is a statement about a
    population and this project already refuses to average percentiles
    once (ADR-0005). The areas average, because an area is an answer per
    draw rather than a sample. The cost is priced once at the end,
    against the area the row actually reports.
    """
    if not draws:
        raise ValueError("a row needs a draw")
    first = draws[0]
    if len(draws) == 1:
        return first

    areas = [r.area_km2 for r in draws if math.isfinite(r.area_km2)]
    reached = [r.reached_km2 for r in draws
               if r.reached_km2 is not None and math.isfinite(r.reached_km2)]
    area_km2 = sum(areas) / len(areas) if areas else first.area_km2
    return Result(
        first.deployed,
        pooled([r.samples for r in draws], first.deployed.scenario.name),
        price(first.deployed.inventory(area_km2), rates),
        area_km2,
        sum(reached) / len(reached) if reached else None,
    )


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
    deployments: Optional[Sequence[Deployed]] = None,
    rates: Optional[OperatingRates] = None,
    weights: Optional[dict] = None,
    settings: Optional[Settings] = None,
    only: Optional[Sequence[str]] = None,
) -> tuple[tuple[Result, ...], tuple[Row, ...]]:
    """Every row of the block, and the results behind them.

    ``weights`` is the journey mix the last row is computed under, keyed
    by scenario name. Nobody supplied one, so it is configuration and the
    notes print whatever was used.

    ``settings`` is a file of the figures nobody supplied. Pass one and
    the scenarios, the mounting costs, the unpublished radio figures and
    the operating rates are all rebuilt from it, so a table run against
    real numbers is real all the way down (ADR-0016).
    """
    if settings is not None:
        catalogued = catalogue(settings)
        deployments = deployments or tuple(catalogued.values())
        if only:
            deployments = tuple(catalogued[name] for name in only)
        rates = rates or operating_rates(settings)
    else:
        deployments = deployments or ALL
        rates = rates or DEFAULT_RATES

    deployments = reweighted(tuple(deployments), weights)
    # Each row is a journey and a coverage sweep and depends on no other,
    # so the rows are run at the same time (ADR-0025).
    # Every row, every arrangement of shadows, all at once: the draws of
    # one row depend on each other no more than the rows do, and there
    # are four cores rather than three (ADR-0025, ADR-0055).
    drawn = [len(draws_of(deployed)) for deployed in deployments]
    jobs = [
        (deployed, rates, draw, draw < AREA_DRAWS)
        for deployed, how_many in zip(deployments, drawn)
        for draw in range(how_many)
    ]
    every = spread(_run_one, jobs)
    results = []
    at = 0
    for how_many in drawn:
        results.append(folded(list(every[at:at + how_many]), rates))
        at += how_many
    results = tuple(results)
    rows = tuple(r.row() for r in results)
    if len(results) > 1:
        # A weighted average of one scenario is that scenario, and
        # printing it twice under a name that promises a combination is
        # worse than not printing it. The block has four rows when it
        # describes three deployments (ADR-0005).
        rows += (weighted(results),)
    return results, rows


def _run_one(task) -> Result:
    """One draw of one row. Top-level so a worker process can import it."""
    deployed, rates, draw, with_area = task
    return run(deployed, rates, draw=draw, with_area=with_area)


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


def _anchor_mix(deployment) -> str:
    """What the deployment is actually made of, counted by mounting.

    A corridor carries more than one kind, so naming a single mounting
    would describe a deployment nobody built.
    """
    counted: dict = {}
    for anchor in deployment.anchors:
        counted[anchor.mounting.kind] = counted.get(anchor.mounting.kind, 0) + 1
    return ", ".join(
        "{} on {}".format(count, kind) for kind, count in sorted(counted.items())
    )


def coarsely_read(results: Sequence[Result]) -> str:
    """What a run gave up for speed, or nothing where it gave up nothing.

    Read off what actually ran rather than off what was asked for, so a
    settings file that happens to carry these figures says the same
    thing as `--fast` does.
    """
    if not results:
        return ""
    first = results[0]
    given_up = []
    if int(getattr(first.deployed, "shadow_draws", 1)) <= 1:
        given_up.append(
            "the shadows are drawn once rather than pooled over eight, and "
            "one draw put the open-country row's ninety-fifth percentile "
            "anywhere between 14,6 and 279,6 m (ADR-0055)"
        )
    spacing = getattr(first.deployed.scenario.terrain, "profile_spacing_m", 0.0)
    if not spacing:
        given_up.append(
            "the ground profile is read at a fixed 64 samples rather than "
            "every 10 m, which on a 6,9 km link is a reading every 108 m "
            "and reads diffraction 6,32 dB low (ADR-0062)"
        )
    if not given_up:
        return ""
    # Which way it is wrong, not only that it is. Both coarse readings
    # understate loss, so a fast run flatters the system: over the
    # shipped rows it read the open-country percentile 18,59 m against
    # the published 22,72 and its availability %52,00 against %41,83.
    # A row that looks bad read fast really is bad (ADR-0063).
    return (
        "These numbers were read coarsely for speed and are not the "
        "published ones: " + "; ".join(given_up) + ". Both read loss low, "
        "so a fast answer flatters the deployment rather than erring the "
        "safe way. Run it without --fast to publish anything."
    )


def footnotes(results: Sequence[Result], rows: Sequence[Row],
              arrangements: Sequence = ()) -> str:
    """What the table rests on, printed with it rather than beside it.

    `arrangements` are the saved presets that drove rows, where any did
    (`yerkon table --preset`). Named here because the moment a printed
    row can come from a file somebody saved, "which file, and which
    version of it" is part of what the row rests on — a preset edited
    between two runs would otherwise print two different tables with
    identical provenance (ADR-0001, ADR-0043).
    """
    lines = ["Notes:"]
    hurried = coarsely_read(results)
    if hurried:
        lines.append("  {}".format(hurried))
    for arrangement in arrangements:
        lines.append("  {}".format(arrangement.describe()))
    if arrangements:
        lines.append(
            "    A saved arrangement is not a shipped scenario. These rows "
            "rest on somebody's stored file rather than on `scenarios.py`, "
            "and the twelve characters after each name are a hash of its "
            "contents: two runs that print the same hash ran the same "
            "arrangement."
        )
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
            lines.append(
                "    Its route kilometres are a test journey through the "
                "area, not a dimension of the service, so cost is quoted "
                "per square kilometre and not per kilometre of road."
            )
        else:
            lines.append(
                "  {}: the deployment serves a bore {} m wide over {} km, "
                "so its area is the carriageway itself and nothing else. "
                "Per square kilometre it therefore looks enormous beside "
                "the open-road rows, which is arithmetic and not a "
                "judgement: a tunnel serves a line. Compare it on cost per "
                "route kilometre instead. The floor is {}; propagation "
                "carries no waveguide term, which understates what a real "
                "tunnel delivers.".format(
                    result.deployed.scenario.name,
                    decimal_comma(result.deployed.confined_width_m or 0.0, 0),
                    decimal_comma(result.deployed.route_km, 1),
                    result.deployed.scenario.terrain.description,
                )
            )
        built = "    {}: {} TL to build, {} TL a year to run".format(
            _anchor_mix(result.deployed.scenario.deployment),
            decimal_comma(result.costing.capex_tl, 0),
            decimal_comma(result.costing.opex_tl_per_year, 0),
        )
        if result.deployed.serves_a_corridor:
            # Only a bore has route kilometres worth quoting. Over an
            # area they are the length of a test journey rather than a
            # dimension of the service.
            built += ", {} TL per route kilometre".format(
                decimal_comma(result.costing.capex_tl_per_route_km, 0)
            )
        lines.append(built + ".")
        lines.append(
            "    {} of that rests on rates nobody supplied.".format(
                "%{}".format(decimal_comma(100.0 * row.assumed_share, 0))
            )
        )
        deployment = result.deployed.scenario.deployment
        if result.samples.attempted_links:
            lost = result.samples.lost_links / result.samples.attempted_links
            if lost > 0.01:
                lines.append(
                    "    {} of exchanges were lost and every round still "
                    "produced a position, because a round attempts {} "
                    "ranges and a position needs four. Density absorbs "
                    "loss.".format(
                        "%" + decimal_comma(100.0 * lost, 1),
                        min(
                            deployment.max_anchors_per_round,
                            len(deployment.anchors),
                        ),
                    )
                    if row.availability > 0.999 else
                    "    {} of exchanges were lost, which is what the "
                    "availability column is mostly counting.".format(
                        "%" + decimal_comma(100.0 * lost, 1)
                    )
                )
        lines.append(
            "    {} units share the air: a round takes {} ms, so each is "
            "fixed {} times a second and a second unit halves that rather "
            "than adding to it.".format(
                len(deployment.receivers),
                decimal_comma(deployment.round_duration_s() * 1000.0, 0),
                decimal_comma(1.0 / max(deployment.round_duration_s(), 1e-9), 2),
            )
        )
        modules = sorted({a.radio.part for a in deployment.anchors})
        if len(modules) > 1:
            lines.append(
                "    Anchor modules: {}. Each is priced as its own line of "
                "the bill of materials, and a unit ranges only against the "
                "ones it shares a waveform with.".format(", ".join(modules))
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


# --- Where the error came from --------------------------------------------

BREAKDOWN_COLUMNS = ("Hata kaynağı", "Tek başına", "Kalkarsa", "Kazanç", "Çare")


def _signed(metres: float) -> str:
    """Metres saved, without printing a negative zero.

    A source worth less than the run's own seed noise comes out slightly
    negative, and "-0,00" reads as a finding rather than as the rounding
    it is.
    """
    return decimal_comma(0.0 if abs(metres) < 0.005 else metres, 2)


def _wrapped(text: str, width: int = 78, indent: str = "") -> str:
    """Fill each paragraph to a terminal width, keeping the breaks between them."""
    return "\n".join(
        textwrap.fill(paragraph, width=width, initial_indent=indent,
                      subsequent_indent=indent)
        for paragraph in text.split("\n")
    )


def as_breakdown(dissections: Sequence[Dissection]) -> str:
    """Each scenario's error taken apart, aligned for a terminal.

    Three numbers per source and then the thing to buy. "Tek başına" is
    the error if that source were the only one; "kalkarsa" is what the
    whole error falls to if it goes away and the rest stay; "kazanç" is
    the difference between that and the published figure, which is the
    metres the money would actually buy.
    """
    return "\n\n".join(
        [_breakdown_of(dissection) for dissection in dissections]
        + [_wrapped(BREAKDOWN_NOTE)]
    )


def _breakdown_of(dissection: Dissection) -> str:
    grid = [BREAKDOWN_COLUMNS]
    for contribution in dissection.ranked():
        grid.append((
            contribution.label,
            decimal_comma(contribution.alone_p50_m, 2),
            decimal_comma(contribution.without_p50_m, 2),
            _signed(contribution.saves_m(dissection.whole_p50_m)),
            contribution.remedy,
        ))
    grid.append((
        "Model artığı", decimal_comma(dissection.residue_p50_m, 2), "", "",
        "hiçbir kaynak açık değilken kalan",
    ))

    widths = [
        max(len(line[column]) for line in grid)
        for column in range(len(BREAKDOWN_COLUMNS))
    ]
    lines = [
        "{} — HPE P50 {} m, P95 {} m; bir menzilin σ'sı {} m, "
        "geometri çarpanı ×{}".format(
            dissection.name,
            decimal_comma(dissection.whole_p50_m, 2),
            decimal_comma(dissection.whole_p95_m, 2),
            decimal_comma(dissection.range_sigma_m, 2),
            decimal_comma(dissection.geometry_gain, 1),
        ),
        "",
    ]
    last = len(BREAKDOWN_COLUMNS) - 1
    for index, line in enumerate(grid):
        lines.append(("  " + "  ".join(
            cell if column == last
            else cell.ljust(widths[column]) if column == 0
            else cell.rjust(widths[column])
            for column, cell in enumerate(line)
        )).rstrip())
        if index == 0:
            lines.append("  " + "  ".join("-" * width for width in widths))

    lines.append("")
    lines.append(_wrapped(
        "Kareler toplamı {} m; yayımlanan {} m. Aradaki fark, kaynakların "
        "birbirinden tam bağımsız olmadığıdır.".format(
            decimal_comma(dissection.quadrature_p50_m, 2),
            decimal_comma(dissection.whole_p50_m, 2),
        ),
        indent="  ",
    ))

    dominant = dissection.dominant()
    if dominant is None:
        lines.append(_wrapped(
            "Tek bir baskın kaynak yok: en büyük ikisi birbirine yakın, "
            "yani burada sıralama değil bir tercih vardır.",
            indent="  ",
        ))
    else:
        lines.append(_wrapped(
            "Önce harcanacak yer: {}. Kalkarsa HPE P50 {} m'den {} m'ye "
            "iner; bunun için gereken {}.".format(
                dominant.label.lower(),
                decimal_comma(dissection.whole_p50_m, 2),
                decimal_comma(dominant.without_p50_m, 2),
                dominant.remedy,
            ),
            indent="  ",
        ))

    for contribution in dissection.contributions:
        if contribution.fixes_lost <= 0:
            continue
        lines.append(_wrapped(
            "{} ayrıca {} çözüme mal oluyor: bu kaynak konumu "
            "kötüleştirmekten çok konumun hiç üretilmemesine neden "
            "oluyor.".format(contribution.label, contribution.fixes_lost),
            indent="  ",
        ))
    return "\n".join(lines)


BREAKDOWN_NOTE = (
    "Her satır, aynı senaryonun tek bir hata kaynağı susturularak yeniden "
    "koşturulmasıdır; yeni bir model değil (ADR-0020). Alıcının kendi "
    "ölçümüne biçtiği varyans her koşuda aynı bırakılır, yoksa süzgeç "
    "ağırlıklarını da değiştirir ve iki koşu karşılaştırılamaz olurdu.\n"
    "\"Tek başına\" ile \"kalkarsa\" arasındaki uçurum kareli toplamdan "
    "gelir: 2,00 m'lik bir toplamdan 0,50 m'yi çıkarmak geriye 1,94 m "
    "bırakır. Yalnız ilk sütuna bakan biri, alınmaya değmeyecek bir "
    "iyileştirmeyi değerli sanır."
)
