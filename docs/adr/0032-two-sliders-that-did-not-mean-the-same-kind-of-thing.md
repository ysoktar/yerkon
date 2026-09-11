# ADR-0032: two sliders that did not mean the same kind of thing

## Status

Accepted.

## Context

The site has two dimensions and the page has a slider for each. **En**
(width) and **Boy** (length) sit one above the other, look identical, and
did entirely different things.

Width shapes the anchors directly: over an area a run lays a grid from
the road out to `width_m`, so widening the site adds rows of masts and
you watch it happen.

Length did nothing to them. An anchor run carries its own `from_m` and
`to_m`, and those are what place it, so dragging **Boy** from twenty
kilometres to eight left thirty-six masts standing exactly where they
were across a site less than half as long. It changed the route, and —
after the mesh started following the route — the ground. Not the
deployment.

That asymmetry is an accident of order. Width came later, wired to the
anchors; length was already there, and the run's own ends were never
reconciled with it.

## Decision

Shortening the site brings its anchor runs inside it, and does so through
the confirmation panel (ADR-0009), which is the rule this project already
has for a change that forces another change. Pull **Boy** to 8 km and the
panel says:

    İstediğin değişiklik    Sahanın boyu    20000 → 8000
    Bunlar da değişiyor     Grubun bitişi   20000 → 8000

Nothing moves until yes.

Only the length slider clips. Typing an end into a run is a person being
explicit about that run, and clipping it under them would be answering a
question they did not ask — so a run may still be given an end past the
site, deliberately, by hand.

## Consequences

The two sliders now mean the same kind of thing, and the one that moves
anchors says so before it moves them.

The report's own rows are untouched: `scenarios.catalogue()` places
anchors directly rather than through a run, and in all three prepared
tabs the run already spanned exactly the corridor, so no figure in the
table moves.

The alternative considered was clipping silently, the way width already
grows the grid silently. Rejected because the two are not alike: widening
adds anchors the person can see appear, while shortening discards
placements they may have spent an afternoon on — including anchors
dragged by hand. A change that can destroy work goes through the panel.
