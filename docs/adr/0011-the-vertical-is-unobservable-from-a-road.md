# 0011. The vertical is unobservable from a road, and that is the answer

## Status
Accepted.

## Context
Anchors go on structures beside a road. The catalogue spans three metres
for a sign to twenty-five for a purpose-built mast, so a deployment can
mix heights across a range of twenty-two metres. The links they serve are
kilometres long.

Twenty-two metres of height against four thousand metres of baseline is
not a spread. Every range is very nearly horizontal, so the vertical
component of a range measurement is a second-order term, and the geometry
that would separate a receiver at one and a half metres from its mirror
image above the anchors barely exists.

The arithmetic shows this twice. A least-squares solve oscillates between
the two sides of the anchor plane instead of settling, and where it does
settle the vertical variance runs to hundreds of square metres.

Measured over four hundred solves with anchors at one height and again
with heights mixed from three to twenty-five metres, the vertical error
is about the same: a median around twenty-five metres either way. Mixing
mounting heights does not buy an observable vertical.

## Decision
No height constraint, as specified. The vertical stays a free parameter
and its error is reported at whatever size the geometry produces.

The least-squares solve is damped, and the damping is raised whenever a
step makes the fit worse. That is a statement about the arithmetic, not
about where the receiver is: it makes the solve settle on one side of the
plane instead of oscillating, and it does not shrink the vertical error.

An unobservable vertical is not an outage. A fix is refused when a
*horizontal* axis is undetermined — anchors in a line, say — because such
a position means nothing. A fix with a large vertical error still means
something and is counted as a fix.

## Consequences
The VPE column will read tens of metres for every road scenario, against
an HPE of a few. That is a true statement about a terrestrial network of
roadside anchors, and it is the reason real systems reach for a
barometer, a road-surface model, or an anchor somewhere genuinely high.

None of those is in the report's bill of materials, so none is modelled.
If one is added later, this ADR is what it argues against.

Reporting a small VPE would require telling the estimator the height it
was meant to find. The previous codebase did something of that kind and
its accuracy figures were statements about nothing.
