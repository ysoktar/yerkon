# 0009. A change and everything it forces are confirmed together

## Status
Accepted.

## Context
Most of the settings in this project are not independent. Changing the
region changes the legal radiated power, which changes how far a link
still ranges within tolerance, which changes how far apart anchors can
stand, which changes how many there are and what they cost. Changing the
mounting structure or the target accuracy sets off the same chain.

A tool that silently recomputed the rest would leave someone reading a
cost figure without knowing which of their settings produced it. A tool
that confirmed each consequence separately would ask four questions for
one edit, and the person answering the second would not yet know what the
fourth was going to be.

## Decision
One edit produces one confirmation. The panel lists every value that
would change — the one asked for and every one that follows from it —
each with its old value, its new value, and, for the derived ones, why it
follows. The answer is a single y/n, and nothing is applied until it is y.

Derived values are computed by the same functions the simulation uses.
There is no separate table of rules saying what forces what: the
consequences are read off the physics, which is what makes them true
rather than merely declared. See ADR-0002.

The panel is one function producing one description, and both the command
line and the application render it. See ADR-0001.

## Consequences
An edit whose consequences are unacceptable is rejected before anything
changes, so there is no half-applied state to undo.

The panel grows as the model does. When the estimator lands, the chain
extends from ranging precision through geometry to position error, and
the same confirmation shows the new links without any change to how it is
answered.

A batch answer cannot accept some consequences and refuse others. That is
deliberate: the consequences are not optional, they are what the settings
mean. Refusing one means choosing different settings, not overriding the
physics.
