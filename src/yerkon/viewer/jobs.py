"""Work the page asks for that takes minutes rather than milliseconds.

A scene redraw is a tenth of a second and a slider expects that. The
table is four minutes, the error dissection is twelve, and a deployment
search is longer still — all of them because every figure they produce
comes from running the real simulation rather than from a fitted model
(ADR-0020, ADR-0023).

So they run on a thread and the page asks how they are getting on. The
alternative was a request that hangs for twelve minutes behind a browser
timeout, or a second faster model that would disagree with the first.

Nothing here computes anything. It starts things, collects what they
print, and hands back whatever they returned.
"""

from __future__ import annotations

import threading
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Job:
    """One piece of long work: what it is, how far it has got, what it gave."""

    identifier: str
    kind: str
    #: Lines the work has reported as it went, oldest first.
    progress: list = field(default_factory=list)
    #: How many steps it expects, where it knows. Zero means it cannot say.
    total: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
    done: bool = False

    def as_json(self) -> dict:
        return {
            "id": self.identifier,
            "kind": self.kind,
            "progress": list(self.progress),
            "total": self.total,
            "done": self.done,
            "result": self.result,
            "error": self.error,
        }


class Jobs:
    """Every long task this session has started, by identifier.

    One lock over the whole registry. The work itself holds nothing: it
    appends a line, releases, and carries on, so a page polling every
    second never waits on a simulation.
    """

    #: How many finished tasks to keep before dropping the oldest.
    #:
    #: A page left open for a day runs a lot of these, and each holds
    #: every line it printed. Keeping the last few is enough: the page
    #: polls one at a time and stops caring the moment it has rendered
    #: the result.
    REMEMBERED = 16

    def __init__(self) -> None:
        self._jobs: dict = {}
        self._lock = threading.Lock()

    def start(
        self,
        kind: str,
        work: Callable[[Callable[[str], None]], dict],
        total: int = 0,
    ) -> Job:
        """Run ``work`` on a thread, giving it a way to report progress."""
        job = Job(identifier=uuid.uuid4().hex[:12], kind=kind, total=total)
        with self._lock:
            self._jobs[job.identifier] = job
            self._forget_the_oldest()

        def say(line: str) -> None:
            with self._lock:
                job.progress.append(str(line))

        def run() -> None:
            try:
                outcome = work(say)
            except Exception as trouble:            # noqa: BLE001
                # Whatever went wrong belongs on the page rather than in a
                # terminal the person may not be looking at. The traceback
                # goes to the terminal, where a developer will want it.
                traceback.print_exc()
                with self._lock:
                    job.error = str(trouble) or trouble.__class__.__name__
                    job.done = True
                return
            with self._lock:
                job.result = outcome
                job.done = True

        threading.Thread(target=run, daemon=True, name=kind).start()
        return job

    def read(self, identifier: str) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(identifier)
            if job is None:
                return None
            # A copy, so a poll cannot read a half-appended list while the
            # work is still writing to it.
            return Job(
                identifier=job.identifier, kind=job.kind,
                progress=list(job.progress), total=job.total,
                result=job.result, error=job.error, done=job.done,
            )

    def forget(self, identifier: str) -> None:
        with self._lock:
            self._jobs.pop(identifier, None)

    def _forget_the_oldest(self) -> None:
        """Drop finished tasks past the limit. Never a running one.

        Dictionaries keep their insertion order, so the oldest finished
        task is the first one that is done. A task still running is never
        dropped however old it is: a twelve minute dissection would
        otherwise vanish from under the page watching it.
        """
        while len(self._jobs) > self.REMEMBERED:
            stale = next(
                (key for key, job in self._jobs.items() if job.done), None
            )
            if stale is None:
                return
            self._jobs.pop(stale)
