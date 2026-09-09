# 0006. OPEX comes from an inventory, not a percentage

## Status
Accepted.

## Context
The report leaves OPEX empty for every YERKON row. The common shortcut, a
fixed percentage of capital cost, would produce a number with no mechanism
behind it and no way to check it.

## Decision
Annual operating cost is the sum of named recurring items, each attached to
a countable thing in the deployment: energy per anchor, connectivity per
anchor or per gateway, hardware replacement from a stated service life,
scheduled maintenance visits per site, and central system operation
amortised across deployments.

Every rate is a named constant with its source recorded, in the same way
hardware prices are. Where no source exists, the constant says so and the
row is marked as an assumption.

## Consequences
OPEX responds to node count, so a design change that halves the anchors
halves most of the operating cost too. Rates the project cannot source are
visible as assumptions rather than hidden inside a percentage.
