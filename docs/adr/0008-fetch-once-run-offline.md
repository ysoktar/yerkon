# 0008. Site data is fetched once into a cache, then read offline

## Status
Accepted.

## Context
The project needs real ground and real buildings, from three sources that
behave differently. A GeoTIFF is a file someone downloads. An elevation
service answers coordinate queries over the network. OpenStreetMap answers
feature queries over a different network service with its own rate limits.

Calling any of them from inside a simulation run would make results depend
on a remote service being up, on its rate limiter, and on whatever it
returns that day. A Monte Carlo run makes tens of thousands of ground
queries, which no public service would tolerate and no reviewer could
reproduce.

Separately, this development environment blocks all three, so nothing that
calls them at run time can be tested here at all.

## Decision
Fetching and reading are different operations at different times.

`yerkon fetch` is the only thing that touches the network. It pulls
elevation and features for a bounding box and writes them to a cache
directory as plain files. Where several sources are reachable it uses them
together: elevation from a raster or a service, features from
OpenStreetMap, merged into one site.

Everything else reads the cache and never opens a socket. A run against a
populated cache is deterministic, offline, and reproducible by anyone with
the same cache.

A cache carries a manifest recording where each piece came from, when, and
at what resolution, so a number in the table can be traced to a source the
way a datasheet figure can.

## Consequences
The simulation cannot silently depend on a service being up.

Site data becomes an artefact that can be committed, shared and reviewed,
which is what makes a range figure checkable rather than merely stated.

The cost is a step: someone has to run the fetch before the first run for
a new area. Synthetic terrain needs no fetch, so the default path stays
one command.

The fetch has to degrade rather than fail. A site with elevation and no
buildings is worth having; the manifest records what is missing so the
model does not quietly treat absent buildings as open ground.
