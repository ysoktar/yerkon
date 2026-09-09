# 0012. Service area is where a position is available, not where a packet arrives

## Status
Accepted. Refines the definition of **service area** in `CONTEXT.md`.

## Context
The comparison table divides cost by service area, so what counts as
served decides the cost per square kilometre. The GNSS rows it sits
beside mean, by service area, ground where a receiver can determine its
position.

`CONTEXT.md` defined the YERKON service area as the union of the areas
the anchors reach. On a corridor deployment those two readings are not
close. Measured over a real sweep with anchors every four kilometres on
twenty-five metre masts, one anchor reaches 392,5 km² and four reach
15,2 km². Reporting the first would understate cost per square kilometre
by a factor of twenty-six.

The gap is not an artefact. A position needs four ranges. An anchor's
usable range from a mast is about five and a half kilometres, so a
receiver four kilometres from one anchor is typically in reach of three,
which is one short.

## Decision
Service area is the ground on which enough anchors are reachable, at
usable ranging precision, to produce a position. It is measured by
sweeping a grid over the real terrain and asking the link budget at each
cell, which is what makes it the area range actually covers rather than a
corridor drawn around the road.

The reached area is computed alongside and reported next to it. The two
are never printed without each other, because the difference between them
is the finding.

## Consequences
Anchor spacing stops being a range question and becomes a geometry
question. Four kilometres is inside the radio's reach and outside what a
position needs; measured across a sweep, halving the spacing to fifteen
hundred metres takes the served area from 15,2 to 75,2 km² and the median
horizontal error from 5,22 to 2,64 m.

Cost per square kilometre now falls as anchors are added over part of the
range, because each anchor adds more served area than it costs until the
overlap is complete. A model using the reached area would have shown cost
per square kilometre rising monotonically and hidden that.

`CONTEXT.md` is amended to match. The earlier reading is recorded here
rather than deleted, because a service area quoted from it would be
wrong by more than an order of magnitude and somebody may still meet one.
