# ADR-0025: a closure is what kept this on one core

## Status

Accepted.

## Context

Everything slow in this project is the same shape: dozens of scenario
runs that do not depend on each other. The table is three. The error
dissection is sixteen a row, so forty-eight. A rural deployment search is
thirty-six. Each run is tens of seconds, and they were all queued onto
one core while the other three sat idle.

The obstacle was not the design of the work. It was one line in each
terrain constructor. `Terrain.elevation_m` held a closure —
`lambda x, y: elevation_m`, or a `def elevation` capturing a site — and a
closure cannot cross a process boundary. `Road` did the same through
`graded_alignment`, which returned a `surface` function closing over a
sampled profile. So a `Scenario` could not be pickled, and nothing
holding one could be handed to a worker.

That is a small implementation detail with a large consequence, and it
had never surfaced because nothing had tried.

There was a second thing, and the user found it rather than a test.
`yerkon solve` searched a short hardcoded list of figures per scenario,
so the page could retune the values but not choose which figures were in
the search at all. A search space somebody else wrote is a menu, not a
tool — and the command line had always taken `--vary`.

## Decision

**Replace the closures with small callables.** `Level`, `Rolling`,
`Sloping` and `Fetched` are frozen dataclasses with `__call__`;
`Alignment` is the road profile read back by distance along. They pickle,
so a `Scenario` pickles, so the work fans out. They also repr and compare,
which the closures did not.

**`yerkon.parallel.spread` runs the independent tasks.** Three rules
shape it, and each of them is a way of not silently changing an answer:

*Results come back in the order they went out.* A dissection matches runs
to error sources by position; a pool returning them as they completed
would attribute one source's runs to another and every figure would be
plausible and wrong.

*A worker seeds itself from the scenario.* `run_scenario` already reseeds
from `Scenario.seed`, so a run is a property of the arrangement and not
of the machine. Anything drawing from a shared generator would make every
published figure depend on how many cores happened to be free.

*It leaves the machine a core.* A search should not make the viewer it
was started from unusable, and one task is never worth the cost of
starting a pool.

Where the pool cannot start at all — a sandbox, a frozen build, a machine
out of handles — it runs the tasks here instead. Slow beats broken.

**The search space is built in the page.** Any figure in the settings
file can be added to a search, dropped from it, or retuned; the engine
already validated the key and refused one it had no entry for. The
short list per scenario became what it always should have been: a
suggested starting point, one click from being replaced.

**And the study writes itself out.** `yerkon deliver` renders four
Markdown files — the rows and the ground under them, the error budget,
every figure and what it rests on, the deployments that could have been
built instead — because what this project is *for* is the block on page
15 and the argument behind it, and until now all of that lived in a
terminal or a browser tab. The dissection is skippable, since it is by
far the slowest part and somebody refreshing the table should not wait
for it.

## Consequences

On four cores, using three:

| | before | after |
|---|---|---|
| `yerkon table` | ~4 min | 71 s |
| `yerkon budget --only tunnel` | 82 s | 43 s |
| the rural search (36 candidates) | ~25 min | ~9 min |

Every figure is identical to the serial run — checked, not assumed, and
now a test: the same scenario run in two processes and here must agree on
availability and on both percentiles.

The speed matters more than the clock says. A thirty-six candidate search
that takes half an hour is one somebody runs once and accepts; at nine
minutes it is one they run three times with different targets. The
`--vary` boxes in the page only became useful at the same time, and for
the same reason.

What did not change: the work is still every candidate simulated in full.
Nothing here is a faster model, and a surrogate fitted to a few runs would
still be a second model of the same thing (ADR-0023).
