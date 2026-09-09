# 0004. Roads have grade

## Status
Accepted.

## Context
The previous codebase placed every road receiver at a constant 1,5 m
elevation and then constrained the filter's height to a map surface with
that same elevation. Vertical error measured the map's assumed accuracy and
nothing else.

## Decision
A Site carries a terrain elevation field. Roads follow it with a grade, and
a receiver's true height is the terrain elevation plus the vehicle's
antenna mounting offset. Bridges and tunnel portals change that elevation
sharply.

No scenario fixes the receiver's height, and the estimator's vertical
coordinate is always free.

## Consequences
Vertical dilution of precision now has something to act on. Reported
vertical error will be large for the road scenarios, because a network of
anchors at similar heights genuinely cannot resolve height well. That is
the finding, not a fault.
