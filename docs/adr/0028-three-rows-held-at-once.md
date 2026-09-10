# ADR-0028: three rows held at once, not one swapped in and out

## Status

Accepted.

## Context

The viewer's four modes lived behind a dropdown, and switching rebuilt
the arrangement from scratch. An afternoon spent on the rural row — a
mast raised, anchors dragged, a spacing narrowed — was gone the moment
somebody looked at the tunnel.

That made the one thing the page is for impossible. The table has three
rows; comparing them means preparing all three, and nothing could be
prepared because nothing survived a glance elsewhere.

There was a second, quieter version of the same problem. A run from the
page rebuilt its scenarios from `catalogue(settings)` — the shipped
arrangement with the page's figures applied. So a table run reported the
catalogue's deployment, not the one on screen. Drag an anchor, run the
table, and the number that came back described something else.

## Decision

Three tabs, one per row, all held at once. `Session` keeps a `ViewState`
per row and which one is showing; switching changes only the last.
Resetting resets the row showing and leaves the others alone.

A run takes **the rows as prepared**: `deployments_of` builds from each
tab's own `ViewState`, not from the catalogue. What you set up is what
you run.

Running covers either the row showing — one row of output — or all
three, which produces the three plus the weighted row they make. That is
the shape of the block on page 15, so the page and the report now
produce the same thing by construction rather than by coincidence.

The mixed corridor that used to be a fourth mode is gone as a preset.
Nothing is lost in kind: any tab still carries as many anchor runs of as
many modules as it likes, which is all a mixed corridor ever was. The
tests that covered it build one directly.

## Consequences

Preparing and comparing is possible for the first time.

Two things fell out of the change that were bugs on their own. The rural
tab opened on the Gölbaşı hills while the rural row of the table stands
on the Polatlı plain, so the picture and the published figure described
different places. And the tunnel tab ran on a roadside sign rather than a
tunnel bracket, because the page's mounting list was written by hand and
had never gained the bracket — while `design.MOUNTING_CHOICES` had never
gained it either, so asking for one raised. Two catalogues that disagreed
with each other and with the model.

The page no longer holds any of those lists. The engine serves the
mountings, the radios and the rows, so a mounting that exists can be
chosen and one that does not cannot be offered.
