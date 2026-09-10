"""Search deployment options for one that meets a target, and save it.

Every figure that shapes a deployment is in the settings file
(ADR-0023), so searching the design space is searching a few numbers in
that file. This tries combinations of them, runs the real simulation on
each, keeps the ones that meet the target, and returns the cheapest —
then `yerkon solve --save` writes it out as a named option that anything
else can be run against.

Two rules the search is built around.

**It runs the simulation.** Each candidate is a full scenario against
real ground, which is why this is slow and why its answers can be
trusted against the table: they come from the same engine. A surrogate
model fitted to a few runs would be faster and would be a second model
of the same thing, disagreeing with the first exactly where the ground
is difficult.

**Cheapest that meets, not best.** A search that maximised availability
would always return the densest grid it was offered, because more
anchors always help a little. What a person with a budget needs is the
least expensive arrangement that clears the bar, which is what
`yerkon site` already does for structures and what this does for
geometry (ADR-0015).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from yerkon.cost import DEFAULT_RATES, OperatingRates, operating_rates, price
from yerkon.evaluate import Samples, run_scenario
from yerkon.options import Option
from yerkon.scenarios import catalogue
from yerkon.settings import DEFAULTS, Settings


class AlreadyMet(ValueError):
    """The search found that the settings in hand are already the answer."""


@dataclass(frozen=True)
class Target:
    """What a deployment has to achieve to count as meeting the bar.

    All of these are floors and ceilings rather than things to maximise.
    A search with no target is a search that returns whatever it was
    given most of.
    """

    #: Share of attempted fixes that must produce a position.
    availability: float = 0.0
    #: Horizontal error at the fiftieth percentile, in metres, at most.
    hpe_p50_m: float = math.inf
    #: Horizontal error at the ninety-fifth percentile, in metres, at most.
    hpe_p95_m: float = math.inf
    #: Fixes a unit must get per second, at least.
    fixes_per_second: float = 0.0

    def met_by(self, outcome: "Outcome") -> bool:
        return (
            outcome.availability >= self.availability
            and outcome.hpe_p50_m <= self.hpe_p50_m
            and outcome.hpe_p95_m <= self.hpe_p95_m
            and outcome.fixes_per_second >= self.fixes_per_second
        )

    def describe(self) -> str:
        parts = []
        if self.availability > 0.0:
            parts.append("availability ≥ {:.1%}".format(self.availability))
        if math.isfinite(self.hpe_p50_m):
            parts.append("HPE P50 ≤ {:.2f} m".format(self.hpe_p50_m))
        if math.isfinite(self.hpe_p95_m):
            parts.append("HPE P95 ≤ {:.2f} m".format(self.hpe_p95_m))
        if self.fixes_per_second > 0.0:
            parts.append("{:.2f} fixes a second".format(self.fixes_per_second))
        return ", ".join(parts) or "nothing in particular"


@dataclass(frozen=True)
class Outcome:
    """What one candidate arrangement produced."""

    values: dict
    availability: float
    hpe_p50_m: float
    hpe_p95_m: float
    vpe_p95_m: float
    fixes_per_second: float
    anchors: int
    capex_tl: float
    opex_tl_per_year: float

    @property
    def capital_per_point(self) -> float:
        """Lira per point of availability, for comparing candidates."""
        return self.capex_tl / max(self.availability * 100.0, 1e-9)


#: What a search may move, and what is worth trying, by scenario.
#:
#: Deliberately short. A grid over five knobs is a hundred full
#: simulations and an afternoon; a grid over two or three is minutes and
#: answers the question somebody actually asked. Anything not here can
#: still be searched by naming it on the command line.
SEARCHABLE = {
    "rural": {
        "rural.anchor_spacing_m": (4000.0, 3000.0, 2500.0, 2000.0),
        "mounting.tall_mast.height_m": (25.0, 30.0, 35.0),
        "rural.anchors_per_round": (8.0, 12.0, 16.0),
    },
    "urban": {
        "urban.anchor_spacing_m": (500.0, 400.0, 300.0),
        "urban.anchors_per_round": (8.0, 12.0),
    },
    "tunnel": {
        "tunnel.anchor_spacing_m": (150.0, 120.0, 100.0),
        "tunnel.anchors_per_round": (8.0, 12.0),
    },
}

#: Figures that have to move with another to stay physical.
#:
#: A grid staggers by half its spacing; a taller mast costs more steel.
#: A search that moved one without the other would be pricing a mast
#: nobody sells or laying out a grid nobody builds, and it would find
#: bargains that do not exist.
def _follows(values: dict) -> dict:
    out = dict(values)
    for spacing_key, stagger_key in (
        ("rural.anchor_spacing_m", "rural.anchor_stagger_m"),
        ("urban.anchor_spacing_m", "urban.anchor_stagger_m"),
    ):
        if spacing_key in out:
            out[stagger_key] = out[spacing_key] / 2.0
    if "mounting.tall_mast.height_m" in out:
        out["mounting.tall_mast.site_cost_tl"] = mast_cost_tl(
            out["mounting.tall_mast.height_m"]
        )
    return out


def mast_cost_tl(
    height_m: float, settings: Settings = DEFAULTS
) -> float:
    """What a mast of a given height costs to put up.

    Steel and foundation grow faster than height — the usual rule of
    thumb is roughly its square, because a taller mast carries more
    moment as well as more length. It matters: unpriced, ten extra metres
    look like the cheapest availability in the study, and priced, more
    masts beat taller ones at equal money.

    Anchored on the one mast figure in the settings file, so replacing
    that figure with a real quotation moves the whole curve.
    """
    base_height = settings.number("mounting.tall_mast.height_m")
    base_cost = settings.number("mounting.tall_mast.site_cost_tl")
    if height_m <= 0.0 or base_height <= 0.0:
        raise ValueError("a mast has a height")
    return base_cost * (height_m / base_height) ** 2


def evaluate(
    scenario_name: str,
    values: dict,
    settings: Settings = DEFAULTS,
    rates: Optional[OperatingRates] = None,
) -> Outcome:
    """Run one candidate arrangement, and price it."""
    complete = _follows(values)
    tuned = settings.with_values(complete)
    deployed = catalogue(tuned)[scenario_name]

    samples = run_scenario(deployed.scenario)
    p50, _ = samples.percentile(50)
    p95, v95 = samples.percentile(95)
    round_s = deployed.scenario.deployment.round_duration_s()

    area = deployed.served_km2()
    costing = price(
        deployed.inventory(area if area else 1.0),
        rates or operating_rates(tuned),
    )
    return Outcome(
        values=complete,
        availability=samples.availability,
        hpe_p50_m=p50,
        hpe_p95_m=p95,
        vpe_p95_m=v95,
        fixes_per_second=1.0 / round_s if round_s > 0.0 else 0.0,
        anchors=len(deployed.scenario.deployment.anchors),
        capex_tl=costing.capex_tl,
        opex_tl_per_year=costing.opex_tl_per_year,
    )


@dataclass(frozen=True)
class Search:
    """Every candidate tried, and which of them met the target."""

    scenario: str
    target: Target
    tried: tuple[Outcome, ...] = field(default_factory=tuple)

    @property
    def met(self) -> tuple[Outcome, ...]:
        return tuple(o for o in self.tried if self.target.met_by(o))

    @property
    def best(self) -> Optional[Outcome]:
        """The cheapest arrangement that meets the target, or nothing.

        Nothing rather than the best of a bad set. A search that returns
        its least-bad failure is a search whose answer has to be checked
        against the target by hand every time, which is how a number that
        does not meet anything ends up in a report.
        """
        met = self.met
        return min(met, key=lambda o: o.capex_tl) if met else None

    def as_option(self, name: str, settings: Settings = DEFAULTS) -> Option:
        """The winner, written up so it can be chosen by name from now on."""
        best = self.best
        if best is None:
            raise ValueError(
                "nothing met {}; there is no option to save".format(
                    self.target.describe()
                )
            )
        moved = {
            key: value
            for key, value in best.values.items()
            if abs(value - settings.number(key)) > 1e-9
        }
        if not moved:
            # The settings already meet the target. Saving an option that
            # changes nothing would put a file in the list whose whole
            # content is a claim, and choosing it later would look like a
            # decision when it is a no-op.
            raise AlreadyMet(
                "the settings already meet {}; the cheapest arrangement "
                "that meets it is the one you have, so there is nothing "
                "to save".format(self.target.describe())
            )
        return Option(
            name=name,
            title="{}: {} — {}".format(
                self.scenario, self.target.describe(),
                "{} anchors, {:,.0f} TL".format(best.anchors, best.capex_tl)
                .replace(",", " "),
            ),
            origin="yerkon solve",
            note=(
                "Found by searching {} arrangements of the {} row against "
                "the real ground it stands on, and keeping the cheapest "
                "that met {}.\n\n"
                "It delivers {:.1%} availability, {:.2f} m at the fiftieth "
                "percentile and {:.2f} m at the ninety-fifth, at {:.2f} "
                "fixes a second, from {} anchors.\n\n"
                "Every candidate was a full simulation rather than a "
                "fitted model, so these figures come from the same engine "
                "the table does (ADR-0023)."
            ).format(
                len(self.tried), self.scenario, self.target.describe(),
                best.availability, best.hpe_p50_m, best.hpe_p95_m,
                best.fixes_per_second, best.anchors,
            ),
            values=moved,
        )


def search(
    scenario_name: str,
    target: Target,
    over: Optional[dict] = None,
    settings: Settings = DEFAULTS,
    watching: Optional[Callable[[Outcome], None]] = None,
) -> Search:
    """Try every combination of the given figures, and report what met.

    ``over`` maps a settings key to the values worth trying. It defaults
    to a short list per scenario, because a grid over five knobs is a
    hundred full simulations and the question is usually about two.
    """
    knobs = over or SEARCHABLE.get(scenario_name)
    if not knobs:
        raise ValueError(
            "nothing to search for {}. Name the figures to vary.".format(
                scenario_name
            )
        )
    for key in knobs:
        settings.entry(key)      # fail now, not forty simulations in

    keys = sorted(knobs)
    tried = []
    for combination in itertools.product(*(knobs[key] for key in keys)):
        outcome = evaluate(
            scenario_name, dict(zip(keys, combination)), settings
        )
        tried.append(outcome)
        if watching is not None:
            watching(outcome)
    return Search(scenario=scenario_name, target=target, tried=tuple(tried))
