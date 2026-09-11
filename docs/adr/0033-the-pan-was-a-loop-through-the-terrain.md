# ADR-0033: the pan was a loop through the terrain

## Status

Accepted.

## Context

Dragging the scene flickered. Not always — turning was smooth, sliding
was not.

Measured rather than guessed at: capture the canvas on consecutive frames
of a steady drag and difference them. A steady gesture changes every pixel
a little, so the difference should be level. Turning gave 9,4 / 9,5 / 9,6
/ 9,7, rising gently. Sliding gave 9,8 / 5,7 / 9,6 / 5,7 / 9,2 / 4,4 — a
clean two-step cycle, which is the scene going forward and snapping back
on alternate frames.

ADR-0029's fix put the camera's pivot on the ground under it, which is
what makes turning feel like walking round something rather than swinging
the site past the screen. That closed a loop nobody looked at:

- the pivot's height comes from the ground under it;
- the eye sits at a fixed offset from the pivot, so the pivot's height
  moves the eye;
- the slide asks where the cursor's ray meets the ground **from the eye**;
- and the slide moves the pivot.

Over real relief the gain of that loop is above one, so it rings.

Interpolating the ground height was tried first, on the theory that the
nearest-sample lookup — a staircase seven hundred metres wide — had
locally infinite gain at every step. It did not fix it: 8,8 / 4,5 / 8,8 /
4,4. The instability is the loop itself, not the quantisation.

## Decision

A slide reads every later cursor position against the camera as it stood
when the ground was grabbed. There is then no path from the pivot back
into the slide, and the loop is gone: 6,7 / 6,7 / 6,5 / 6,3 / 6,4, level
like a turn.

It is also what a rigid drag means. The promise the gesture makes is that
the point you took hold of stays under the cursor, and the mapping from
pixels to ground that makes that true is the one that was on screen when
you took hold of it.

The interpolation stays, because a staircase is the wrong shape for a
ground height whatever else is true of it: it stepped the pivot, the
dragged anchor and the coverage cells alike.

## Consequences

Sliding is smooth, and the pivot still rides on the ground.

What it costs: while a long slide crosses relief, the eye rises and falls
with the ground, so the grabbed point drifts from the cursor by about the
relief crossed. That is the same magnitude as the alternative — freezing
the pivot's height for the gesture and re-seating it on release — spread
smoothly over the drag instead of snapping at the end of it.

The method is the part worth keeping. "It flickers" is not a bug report
anybody can act on, and reading the code for it would have found the
pivot change and called it correct, which it is. Differencing consecutive
frames turned it into a number that alternated, and an alternating number
names its own cause: a feedback loop, not a redraw fault, not a sort
order, not a fetch.
