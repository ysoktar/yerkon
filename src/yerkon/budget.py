"""Which error source made the position wrong, and by how much.

The table says a receiver in town is out by 1,24 m at the fiftieth
percentile. That figure cannot be acted on. Money buys removal of one
error source at a time, and the sources behind that metre are not
interchangeable: surveying the columns better is a week of GNSS work,
lowering the waveform noise is more anchors or more power, and the
implementation floor cannot be lowered at all without a different part.

So this runs each scenario several times, silencing one source at a time,
and reports what each was worth. Two readings of every source, because
they answer different questions:

**Alone** is the error a receiver would have if that source were the only
one. It is what the source is worth on its own, and it is the reading to
compare against the others.

**Removing it** is what the whole error would fall to if that source went
away and every other stayed. It is smaller than the alone figure for
anything that is not dominant, because errors add in quadrature: taking
0,5 m out of a 2,0 m total leaves 1,94 m, and a table that only reported
the alone figure would make that 0,5 m look like a purchase worth making.

Nothing here is a new model. Every run is the same simulation the table
is built from, with the same seeds and the same arrangement, so a
dissection that did not add up would be evidence about the model rather
than about the report. See ADR-0020.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.evaluate import Samples, combine, run_scenario
from yerkon.scenarios import ALL, Deployed
from yerkon.terms import ALL as EVERYTHING, LABELS, NAMES, REMEDIES, Terms

#: What the combined row is called, in the language the table uses.
WEIGHTED = "Ağırlıklı Ortalama"


@dataclass(frozen=True)
class Contribution:
    """What one error source was worth, by both readings."""

    source: str

    #: Horizontal error at the fiftieth percentile with only this live.
    alone_p50_m: float
    alone_p95_m: float
    alone_vertical_p95_m: float

    #: Horizontal error at the fiftieth percentile with this one silenced.
    without_p50_m: float
    without_p95_m: float

    #: Fixes this source cost: the whole run's, less this one's.
    #:
    #: Only packet loss usually shows here. It is the one source that
    #: does not make a position worse so much as stop it happening.
    fixes_lost: int

    @property
    def label(self) -> str:
        return LABELS[self.source]

    @property
    def remedy(self) -> str:
        return REMEDIES[self.source]

    def saves_m(self, whole_p50_m: float) -> float:
        """Metres the fiftieth percentile would fall by if this went away.

        Negative is possible and is not a bug: silencing a source
        reshuffles which links are accepted and redraws the noise, and
        for a source worth far less than the total that reshuffle can be
        larger than the source. A negative here means the source is below
        the run's own noise, which is itself the finding.
        """
        return whole_p50_m - self.without_p50_m


@dataclass(frozen=True)
class Dissection:
    """One scenario's error, taken apart."""

    name: str
    #: The published figures: everything live. These are the table's own.
    whole_p50_m: float
    whole_p95_m: float
    whole_vertical_p95_m: float
    #: Every source silenced. What is left is the model's own residue.
    residue_p50_m: float
    #: Median sigma the receiver believed one range had, in metres.
    range_sigma_m: float
    contributions: tuple[Contribution, ...]

    @property
    def quadrature_p50_m(self) -> float:
        """The alone figures combined as independent errors.

        Printed beside the whole so the gap between them is visible. The
        sources are not perfectly independent — they pass through one
        estimator and one geometry — so this does not have to match, and
        how far it misses is the honest measure of how much the split
        simplifies.
        """
        return math.sqrt(
            sum(c.alone_p50_m ** 2 for c in self.contributions)
            + self.residue_p50_m ** 2
        )

    @property
    def geometry_gain(self) -> float:
        """How much the arrangement multiplies one range's error.

        The whole horizontal error over the sigma of a single range. Above
        one, the anchors are placed such that range errors come out
        amplified — a corridor does this badly, because every anchor is
        on nearly the same line. Below one, the filter is averaging
        several rounds faster than the geometry spoils them.

        It is not a dilution of precision in the textbook sense: this
        one is measured through a moving filter rather than computed from
        a single snapshot's matrix, and it carries the biases as well as
        the noise. It is the number that says whether more anchors or
        better anchors is the cheaper metre.
        """
        if self.range_sigma_m <= 0.0:
            return math.nan
        return self.whole_p50_m / self.range_sigma_m

    def ranked(self) -> tuple[Contribution, ...]:
        """Sources worst-first, by what they are worth alone."""
        return tuple(
            sorted(self.contributions, key=lambda c: c.alone_p50_m, reverse=True)
        )

    def dominant(self) -> Optional[Contribution]:
        """The source to spend on first, or nothing if none stands out.

        Nothing, when the largest is within a quarter of the next: two
        sources that close together are one decision, not a ranking, and
        naming a winner between them would read as a finding when it is
        seed noise.
        """
        ranked = self.ranked()
        if len(ranked) < 2 or ranked[0].alone_p50_m <= 0.0:
            return None
        if ranked[1].alone_p50_m > 0.75 * ranked[0].alone_p50_m:
            return None
        return ranked[0]


def dissect(deployed: Deployed, sources: Sequence[str] = NAMES) -> Dissection:
    """Run one scenario once per source, and once with each source alone.

    Fifteen runs for seven sources. Each is the full simulation, so this
    is slow by construction: the alternative is an analytic error budget,
    which would be a second model of the same thing and would agree with
    the first only by luck.
    """
    return _from_runs(
        deployed.scenario.name, _runs_of(deployed, sources), sources
    )


def dissect_all(
    deployments: Sequence[Deployed] = ALL,
    sources: Sequence[str] = NAMES,
) -> tuple[Dissection, ...]:
    """Every scenario taken apart, and the weighted row along with them.

    The weighted row is dissected the same way the table's weighted row
    is built: by combining the raw per-fix samples of each run under the
    weights, never by averaging the three scenarios' percentiles, which
    would not be a percentile of anything (ADR-0005).
    """
    per_scenario = [(d, _runs_of(d, sources)) for d in deployments]
    each = tuple(
        _from_runs(deployed.scenario.name, runs, sources)
        for deployed, runs in per_scenario
    )
    if len(per_scenario) < 2:
        return each

    return each + (
        _from_runs(
            WEIGHTED,
            {
                name: combine(
                    [(runs[name], deployed.weight) for deployed, runs in per_scenario],
                    WEIGHTED,
                )
                for name, _ in _every_run(sources)
            },
            sources,
        ),
    )


def _runs_of(deployed: Deployed, sources: Sequence[str]) -> dict:
    """Every configuration this dissection needs, run and kept by name."""
    return {
        name: run_scenario(deployed.scenario, terms)
        for name, terms in _every_run(sources)
    }


def _every_run(sources: Sequence[str]) -> tuple[tuple[str, Terms], ...]:
    """Every configuration a dissection needs, named."""
    runs = [("whole", EVERYTHING), ("none", Terms.none())]
    for source in sources:
        runs.append(("only:{}".format(source), Terms.only(source)))
        runs.append(("without:{}".format(source), EVERYTHING.without(source)))
    return tuple(runs)


def _from_runs(name: str, runs: dict, sources: Sequence[str]) -> Dissection:
    """Turn one scenario's set of runs into the figures a reader wants."""
    whole = runs["whole"]
    whole_p50, _ = whole.percentile(50)
    whole_p95, whole_vertical = whole.percentile(95)
    residue_p50, _ = runs["none"].percentile(50)

    contributions = []
    for source in sources:
        alone = runs["only:{}".format(source)]
        without = runs["without:{}".format(source)]
        alone_p50, _ = alone.percentile(50)
        alone_p95, alone_vertical = alone.percentile(95)
        without_p50, _ = without.percentile(50)
        without_p95, _ = without.percentile(95)
        contributions.append(
            Contribution(
                source=source,
                alone_p50_m=alone_p50,
                alone_p95_m=alone_p95,
                alone_vertical_p95_m=alone_vertical,
                without_p50_m=without_p50,
                without_p95_m=without_p95,
                fixes_lost=without.produced - whole.produced,
            )
        )

    return Dissection(
        name=name,
        whole_p50_m=whole_p50,
        whole_p95_m=whole_p95,
        whole_vertical_p95_m=whole_vertical,
        residue_p50_m=residue_p50,
        range_sigma_m=whole.median_range_sigma_m,
        contributions=tuple(contributions),
    )
