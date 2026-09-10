# 0016. Assumptions live in a file, and nowhere else

## Status
Accepted. Extends ADR-0006.

## Context
The report supplied a bill of materials and nothing else. Everything else
this project needs — what a mast costs to build, what a maintenance visit
costs, what noise figure the SX1280 has, what a frequency-offset estimate
leaves behind — is a placeholder somebody wrote.

Each carried its own provenance and its own note, which was enough to
stop a placeholder passing as a measurement but not enough to make one
findable. They were scattered across five modules. A costing that reports
itself as ninety-nine percent assumption is only useful if the person
reading it can then go and find the ninety-nine percent, and they could
not.

Worse, nothing stopped another one being added. The discipline was a
habit, and habits are not enforceable.

## Decision
Every figure nobody supplied lives in `src/yerkon/assumptions.toml`. Each
entry carries its value, unit, provenance, source, a note saying what it
stands for, what it affects, and where it was measured, what doubling it
does.

Nothing else in `src/` may construct one. A test walks the syntax tree of
every module and fails the build if it finds a `Sourced` value marked
ASSUMPTION written in code. It looks for the construction rather than the
word, because comparing against ASSUMPTION is exactly what a costing must
do to report how much of itself rests on one.

The catalogues are built from the file rather than written down:
`world.mountings`, `hardware.radios`, `ranging.clocks`,
`cost.operating_rates`, `scenarios.catalogue`. The module-level constants
are what those builders return for the shipped file, so nothing that
already worked changed.

Replacing a figure is three edits in one place: the value, the source,
and provenance from ASSUMPTION to whatever it now is. Everything
downstream stops counting it at that moment.

`yerkon assumptions` lists what is left. `--assumptions FILE` on every
other verb runs the whole study against a different file.

## Consequences
The share a result reports as resting on guesses is now computed from the
file rather than asserted, and it falls as figures are sourced. Sourcing
the mast cost alone takes the siting answer from ninety-four percent
assumed to sixty-nine.

The file is the work list, and it is ordered by consequence rather than
by module. Thirty-three figures, and the sensitivity line on each says
which ones are worth an afternoon.

It also made the model answer a question it could not before. Set the
mast cost to 8500 TL and existing signs still win; set it to 5000 and
masts take over at seventeen anchors for 264906 TL. The break-even the
costing predicted at 6588 TL is now something a person can walk up to
from either side by editing one line.

The physics moves too, which is the part that matters most. A noise
figure is not a cost, and getting it wrong shortens every link in the
study. It is on the same list as the price of a maintenance visit
because it has the same standing: somebody guessed it.

All of them are editable while the viewer runs. Every figure appears in
the panel with what it affects written under it, and changing one rebuilds
everything from it: the mounting catalogue, the radios, the clocks, the
rates, the scenarios. A figure that moves the link budget — a mounting
height, a noise figure, a clock residual — cascades through the same
confirmation panel as any other setting; one that only moves a price
applies at once.

A number typed into a viewer is still a guess, so an edit keeps its
ASSUMPTION provenance unless a source is given with it. That distinction
is the whole difference between exploring and reporting, and it means the
counter in the panel tells the truth about how much of what is on screen
rests on nothing.

An afternoon of that is worth keeping, so the viewer writes the edited
file back out. It is the same shape the loader reads, so it goes straight
back in through --assumptions.

What this does not do is remove the assumptions. It makes them a
finite, ordered, enforceable list instead of a property of the code.
