# ADR-0020: an error figure nobody can act on is half a result

## Status

Accepted.

## Context

The table says a receiver in town is out by 1,24 m at the fiftieth
percentile, and in a bore by 1,81 m. Both are true and neither can be
acted on. The question anybody holding a budget actually asks is which
of those metres is the cheapest to remove, and the table does not answer
it. Worse, the intuition is wrong: the tunnel is the most accurate
deployment in the study by every hardware measure — an impulse radio, a
ten centimetre measurement floor, anchors a hundred and fifty metres
apart — and it comes out the *least* accurate of the three.

Two ways to answer it were available.

An **analytic error budget** propagates each term through a linearised
geometry and adds them in quadrature. It is instant and it is a second
model of the same thing. Where it disagreed with the simulation, nothing
would say which was wrong, and the disagreement would be largest exactly
where the answer matters most: a corridor's near-singular geometry, a
bias that does not average, a filter that has been running for minutes.

**Re-running the simulation with one error source silenced** is slow —
sixteen full runs per scenario, a couple of minutes each — and it cannot
disagree with the table, because it *is* the table's own engine with one
term switched off.

## Decision

Dissect by re-running. `yerkon.terms.Terms` names the seven sources;
`run_scenario` takes one and silences what it is told to; `yerkon.budget`
runs the combinations and reports them.

Three rules make the runs comparable.

**The receiver's belief does not change.** `measure` still reports the
whole modelled variance in every observation, whatever is silenced. Only
the error actually injected changes. A run that also narrowed the
filter's variance would tighten its gains, and the difference between two
such runs would be partly the estimator re-tuning itself rather than the
error under study.

**The floor is a term, not a clamp.** `sigma_terms_m` returns the
implementation floor as whatever must be added in quadrature to reach it,
which is zero wherever the physics is already above it. Summed, the three
terms reproduce `max(hypot(waveform, clock), floor)` exactly, so the
split changed no published number.

**Both readings are printed.** *Alone* is the error if a source were the
only one; *removing it* is what the whole falls to if that source goes
and the rest stay. They differ enormously and only the second is a
purchase decision: taking 0,50 m out of a 2,00 m total leaves 1,94 m. A
report that printed only the first column would sell improvements worth
six centimetres.

## Consequences

The dissection immediately overturned the reading the table invited.

In the **tunnel**, the anchor survey error is worth 1,84 m on its own and
everything else together is worth 0,17 m. The bore's geometry multiplies
one range's sigma by eighteen, because every anchor is within four metres
of the same line, and what it multiplies hardest is the one error that
never averages out. Buying a better radio for that deployment buys
nothing. Surveying its brackets properly takes it from 1,81 m to 0,17 m.

In the **town**, the ranking inverts: the module's measurement floor is
worth 1,13 m and the survey error 0,09 m. The geometry multiplier is
0,6 — *below one*. An area deployment with a filter running across it
comes out better than a single range, which is the quantitative form of
the thing the corridor framing had been hiding.

One figure the dissection produced was an artefact of the ground rather
than a finding, and it took ADR-0021 to see it. `excess_path` came out at
exactly 0,00 m in all four rows, which read as "obstructions cost
nothing" and in fact meant "two of these three scenarios stand on a
plane, and a plane cannot obstruct anything". On real Ankara ground it is
the third or fourth largest term in every row. A dissection is only as
honest as the world it re-runs.

The cost is honesty about runtime: `yerkon budget` is minutes, not
seconds, and it says so before it starts. The alternative was a number
that arrives instantly and cannot be checked against anything.
