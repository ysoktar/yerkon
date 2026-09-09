# 0015. Siting searches structures, not parameters

## Status
Accepted.

## Context
The last thing on the list, deferred until everything else was built. An
optimiser is only as good as what it optimises, and until the link
budget, the exchange, the estimator and the costing all existed and were
tested, any siting algorithm would have been minimising a number nobody
could defend.

The costing then said what to optimise. The radios are about one percent
of a mast-based deployment's capital. Searching over modules to save
money would be searching the wrong percent.

## Decision
The search is over *which structure to use at each point and how far
apart*, using only structures the corridor is said to carry, and building
only where none stands. Every candidate is a deployment somebody could
build: real anchors on real mountings, scored by the same link budget and
priced by the same bill of materials the table uses.

Two ways of mixing are searched, because they pull in opposite directions
and neither wins in general. Taking the **cheapest** structure standing
at each point gives the lowest price per anchor and, being short, needs
more of them. Taking the **tallest** costs more each and needs fewer. The
answer is whichever came out cheaper, and the runner-up is reported
beside it.

Spacings are searched from sparse to dense and the search stops at the
first that meets the requirement, because denser is dearer and never
covers less. The first written version searched dense to sparse and
returned an answer that worked and cost two and a half times too much.

The area sweep runs once, on the winner. It is the slowest thing in the
project and running it on every candidate would have made the search
minutes instead of seconds.

## Consequences
Over eight kilometres of rolling ground at a five metre tolerance, with
signs standing every 250 m: twenty-one existing roadside signs at 600 m
spacing meet the requirement for 274736 TL. Sixteen purpose-built
twenty-five metre masts meet the same requirement for 1529323 TL.

Five and a half times, and the signs win despite reaching 1,66 km against
a mast's 5,52. Height buys range and range is not what is scarce; what is
scarce is money, and a sign that already stands costs a thirty-fourth of
a mast that does not.

That is the mixed-mounting strategy, arrived at by search rather than by
assertion, and it inverts the intuition the range figures give.

The search will also refuse. A tolerance under the radio's own
measurement floor is not a siting problem and no arrangement of anchors
meets it, so nothing is returned rather than the best of a bad set.

What the search cannot do is invent a survey. What structures stand where
is configuration, and the defaults are an assumption about a typical
stretch of Turkish highway. A real deployment replaces them with what is
actually there, and the answer will move.
