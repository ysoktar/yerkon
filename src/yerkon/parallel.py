"""Running independent simulations at the same time.

Every slow thing in this project is the same shape: dozens of scenario
runs that do not depend on each other. The table is three, the error
dissection is sixteen per row, a deployment search is one per candidate.
Each is seconds to a minute, and they were all queued onto one core.

They can be spread because a `Scenario` now pickles — the terrain and
the road alignment are callables rather than closures, which is what a
process boundary requires (ADR-0025).

Two rules.

**A worker seeds itself from the scenario it is given.** `run_scenario`
already reseeds from `Scenario.seed`, so a run produces the same samples
wherever it happens. Anything that drew from a shared generator would
give different answers on different machines, which would make every
published figure a property of the hardware.

**Order comes back as it went out.** Results are matched to their inputs
by position rather than by whoever finishes first, so a dissection cannot
attribute one source's runs to another.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Iterable, Optional, Sequence, TypeVar

Task = TypeVar("Task")
Outcome = TypeVar("Outcome")

#: Below this many tasks, the pool costs more than it saves.
#:
#: Starting processes and shipping a fetched site to each is a second or
#: two. One scenario run is tens of seconds, so the crossover is low, but
#: it is not zero and a single run should never pay it.
WORTH_SPREADING = 2


def workers(asked: Optional[int] = None) -> int:
    """How many processes to use.

    One less than the machine has, so the terminal and the viewer stay
    responsive while a search runs. At least one.
    """
    if asked is not None:
        return max(int(asked), 1)
    return max((os.cpu_count() or 2) - 1, 1)


def spread(
    work: Callable[[Task], Outcome],
    over: Sequence[Task],
    processes: Optional[int] = None,
    watching: Optional[Callable[[Outcome], None]] = None,
) -> tuple:
    """Run ``work`` on every task, in parallel where that is worth it.

    ``watching`` is called once per finished task, in the order the tasks
    were given rather than the order they completed, so progress reads as
    a list being worked through rather than as a scramble.

    Falls back to running them here when there is one task, when one
    process was asked for, or when the pool cannot start — a machine that
    forbids subprocesses should be slow, not broken.
    """
    tasks = list(over)
    if not tasks:
        return ()

    how_many = workers(processes)
    if len(tasks) < WORTH_SPREADING or how_many == 1:
        return tuple(_one_at_a_time(work, tasks, watching))

    try:
        with ProcessPoolExecutor(max_workers=min(how_many, len(tasks))) as pool:
            done = []
            # `map` yields in the order given, so a caller watching the
            # stream sees task one before task two however they finished.
            for outcome in pool.map(work, tasks):
                done.append(outcome)
                if watching is not None:
                    watching(outcome)
            return tuple(done)
    except (OSError, RuntimeError, ImportError):
        # No subprocesses available: a sandbox, a frozen build, a machine
        # out of file handles. Slow beats broken.
        return tuple(_one_at_a_time(work, tasks, watching))


def _one_at_a_time(
    work: Callable[[Task], Outcome],
    tasks: Iterable[Task],
    watching: Optional[Callable[[Outcome], None]],
) -> list:
    done = []
    for task in tasks:
        outcome = work(task)
        done.append(outcome)
        if watching is not None:
            watching(outcome)
    return done
