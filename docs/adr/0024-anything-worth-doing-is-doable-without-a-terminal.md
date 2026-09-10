# ADR-0024: anything worth doing is doable without a terminal

## Status

Accepted.

## Context

The project grew a verb at a time. `table` runs the report, `budget`
takes each row's error apart, `solve` searches deployments, `options`
lists the named ones, `defaults` lists the figures. Every one of them
was reachable only from a shell.

The viewer, meanwhile, could do the one thing that is fast: draw the
scene and recompute a few numbers as sliders move. Everything that takes
minutes stayed on the command line, which meant the person most likely
to be exploring the design — moving a mast, dragging an anchor, trying a
spacing — had to leave the picture, remember what they had changed, type
it again as flags, and read the answer somewhere else.

That is also how a figure gets lost. The viewer's edits live in its own
session; a `yerkon table` in another window knows nothing about them.

There was a second problem in the same place. The camera could only
orbit a fixed point. Over a twenty kilometre rural region that is not a
limitation, it is a wall: there is no way to look at a corner. Worse,
`refreshScene` re-centred the camera on every response, so even the
target could not be moved by hand — any change would have been undone by
the next edit. Zoom stepped a fixed twelve percent per wheel event,
which a trackpad turns into a lurch and a mouse into imprecision, and it
zoomed towards the middle rather than towards the cursor, so getting
close to one anchor meant zooming in and then hunting for it.

## Decision

**Long work runs on a thread and reports as it goes.** A dissection is
twelve minutes; a browser gives up long before that, and twelve minutes
of silence is indistinguishable from broken. `yerkon.viewer.jobs` starts
the work, collects the lines it prints, and hands back an identifier the
page polls once a second. A failure becomes a message on the page rather
than a traceback in a terminal nobody is looking at.

**Everything runs against the settings the page is showing.** Not
against the shipped defaults. Somebody who has spent an afternoon moving
figures can ask what their arrangement costs, where its error comes
from, and what it would take to reach a target, without writing any of it
to a file first. `yerkon.viewer.tasks` is the seam: it arranges, and the
same modules the table is built from do the work (ADR-0001).

**Options apply as overrides.** Choosing one lands its edits in the same
place a person's hand edits live, so it composes with their work instead
of replacing it, and it undoes the same way.

**The camera moves.** Right-drag, middle-drag or a held modifier slides
the ground under the cursor; the point grabbed stays under the pointer,
which is the only pan that feels like a map rather than like a nudge.
Wheel zoom scales with how far the wheel actually turned and moves
towards the cursor. WASD and the arrows walk the way the camera faces
rather than along the world's axes, because "forward" means what is on
the screen. `F` frames everything, which is the one gesture a person
needs after getting lost — and getting lost is the price of being able
to go anywhere. Every gesture is captured on the canvas, so a drag that
crosses into the panel keeps working until the button comes up.

Framing now happens once, on the first load and on a mode change, and
never again.

## Consequences

The command line and the page do the same things, and a test names the
verbs so that adding one to a terminal and not to the page fails.

Two tests were also weakened without anybody noticing, and this found
both. The route test matched only quoted paths, so a whole feature's
`ask(\`/api/job?id=${...}\`)` would have gone unchecked — exactly the dead
route it exists to catch. And nothing checked the other direction at
all: that every button, box and menu the page draws is actually reached
by the script. A control that looks live and does nothing is worse than
no control.

The smoke test of the finished endpoints turned up a real reporting bug
too. Asked for one scenario, the table printed a "weighted average" row
identical to it — a weighted average of one thing is that thing, and
printing it twice under a name that promises a combination is worse than
not printing it. `build` now adds that row only when it has more than one
deployment to combine.

What this does not do is make the work fast. A dissection over three
scenarios is still twelve minutes, because every figure in it comes from
running the real simulation rather than from a fitted model (ADR-0020).
The page can now watch that happen, which is the honest improvement
available.
