# ADR-0026: a slope is not roughness, and a tilted mirror is not a rough one

## Status

Accepted.

## Context

The request was to let the reflecting ground vary from place to place
instead of being one number for a whole site, controllable per scenario,
at two or three scales, with its own seed. Building it turned up two
errors underneath it, and the second is the one that mattered.

**A slope was being counted as roughness.** `_reflection_surface`
measured the scatter of the ground about the *mean height* of the
reflecting patch. A hillside is a surface, not scatter: over a patch on a
12 % grade that method reported 2,8 m of roughness where the ground was
smooth to 7 cm. A factor of forty, and enough to drive the Ament factor
to zero everywhere that was not level.

So the coherent reflection was switched off across every outdoor link,
and the patchwork was invisible underneath it — a variation of 0,1 m
against a spurious 5,6 m.

**And detrending alone would have been worse than the bug.** With the
slope removed, a tilted patch became a perfect mirror, and the model
would have restored a clean two-ray null on ground that physically
cannot produce one. Measured across the Ankara scenarios, the reflecting
patch is tilted a degree or two on 84–96 % of links.

A tilted mirror does not scatter a ray. It aims it somewhere else. That
is different physics with the same symptom, and conflating them is how
the original error survived so long: it produced roughly the right
answer.

## Decision

**Roughness is measured about the patch's own plane.** A line is fitted
across the reflecting window and what is left over is the roughness. The
`Site` class already detrended for exactly this reason; this is the same
thing, done where the reflection is.

**Tilt is a separate term, `aimed_fraction`.** A surface tilted by τ
swings the reflected ray by 2τ; if that displaces it far against the
first Fresnel radius, it arrives too far off to cancel anything. Rolled
off smoothly, because a zone edge is not a wall.

Getting this right needed one more correction. The first version put the
reflection at the midpoint, and it is not there: a 25 m mast talking to a
receiver at 1,5 m puts it 93 % of the way along, a few hundred metres
from the receiver rather than kilometres, so the swung ray has far less
room to drift. Assuming the midpoint overstated the miss sevenfold on
exactly the geometry this study is made of.

**And the patchwork itself.** `Patchwork` makes roughness a function of
position at two or three scales, per scenario, with its own seed kept
apart from the measurement seed. Two properties matter:

*It is a fact about the place, not a draw.* A receiver ranging to the
same anchor from the same spot meets the same ground every time. Drawn as
noise it would average out over a round; drawn from the position it does
not — like the survey error and the excess path before it (ADR-0019).
The hash is a stable mix rather than Python's, which is salted per
process and would have given different ground in different workers the
moment the work was spread (ADR-0025).

*It leaves the site's roughness meaning what it measured.* The
multipliers are centred on mean square rather than mean, because
roughness enters through its square. Adding levels splits the same
variance finer rather than making the ground rougher.

## Consequences

**The table barely moved.** Urban 1,64 → 1,62 m, rural 2,71 → 2,69,
tunnel 1,81 → 1,77, weighted 2,02 → 1,93. Three corrections to the ground
physics and the published figures are within seed noise of where they
were, because the old model reached the same place by the wrong route:
it killed the coherent reflection by calling a slope rough, and the new
one kills it by correctly calling a slope tilted.

That is the best available evidence that both models were describing the
same world, and only one of them can say why.

**What did change is which row keeps its reflection.** The bore is a
genuine plane, so its coherent fraction rose from 0,17 to 0,73 and the
two-ray cancellation there is now real. Outdoors it stays near zero. This
is why textbook two-ray nulls turn up over airfields and calm water and
not over countryside, and the model now says so for the right reason.

**The patchwork changes nothing in these three scenarios, and that is a
finding rather than an omission.** Outdoors the ray is aimed away
whatever the roughness. In the bore the floor is 2 cm of scatter against
a criterion of metres at that grazing angle — optically smooth, so
varying it does nothing. It would matter on ground that is level *and*
rough: a runway with snow on it, a ploughed plain, a frozen lake. A test
pins that null result together with its reason, so that a scenario which
does exercise it is noticed rather than passing silently.

**The page can fetch anywhere now.** The one thing in this project that
touches the network was also the one thing the viewer could not do, so
using anywhere but the four Ankara sites meant dropping to a terminal.
For a viewer that is meant to be the main way in, that was a hole.
