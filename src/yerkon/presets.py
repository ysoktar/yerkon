"""Named arrangements: everything about one tab, saved and loaded back.

A tab is a whole study — the ground it stands on, how long and wide the
site is, every anchor run and every receiver, the anchors moved by hand
and the ones deleted, and every figure edited away from the shipped file.
Losing that to a slider is the thing tabs were introduced to stop
(ADR-0028), and keeping three of them alive in memory only pushes the
problem to the next time the process ends.

So an arrangement has a name. There is a *default* one for each row and
an *empty* one for each row, and anything a person builds from either can
be saved under a name of their own. Loading one replaces that tab and
nothing else: the rows are separate studies and always were.

**A preset can drive the published table.** `yerkon table --preset` runs
a saved arrangement instead of the shipped scenario, which makes a
printed row depend on a file somebody saved — so the row has to say
which file and *which version of it*. That is what `digest` is for: a
preset called `konya` edited between two runs would otherwise print two
different tables with identical provenance, which is exactly the kind of
untraceable number this project exists to avoid (ADR-0001, ADR-0043).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

from yerkon.language import say

#: Arrangements that need no file: one to start from and one to start
#: from nothing. Keys rather than sentences, like the modes themselves —
#: the label each gets is a question for `language.py`.
SHIPPED = ("default", "empty")

#: What a name may be. The same shape a site name may be, and for the
#: same reason: it becomes a file on somebody's disk.
A_NAME = re.compile(r"^[A-Za-z0-9À-ɏ][A-Za-z0-9À-ɏ_-]{0,63}$")

SUFFIX = ".json"


class UnknownPreset(LookupError):
    """Asked for by a name nothing answers to."""


@dataclass(frozen=True)
class Preset:
    """One tab, by name.

    `state` is a `ViewState.as_json()` dictionary, held as plain data
    rather than as a `ViewState`: this module is read by the CLI, which
    has no business importing the viewer to print a table.
    """

    name: str
    mode: str
    state: dict = field(default_factory=dict)
    #: Where it came from, for a person reading the footnotes: "shipped"
    #: or the path it was read from.
    source: str = "shipped"

    def __post_init__(self) -> None:
        if not A_NAME.match(self.name or ""):
            raise ValueError(say("preset.bad_name", None, name=self.name))

    @property
    def digest(self) -> str:
        """A short hash of what is actually in it.

        Over the canonical JSON rather than the file's bytes, so that
        reformatting, key order or a trailing newline do not read as a
        different arrangement — and so that a preset built in memory and
        one read from disk digest the same.
        """
        canonical = json.dumps(self.state, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    def describe(self) -> str:
        """What a footnote says about a row this drove."""
        return say("preset.from", None, name=self.name, mode=self.mode,
                   digest=self.digest, source=self.source)

    def as_json(self) -> dict:
        return {"name": self.name, "mode": self.mode, "state": self.state}

    @classmethod
    def from_json(cls, payload: dict, source: str = "") -> "Preset":
        missing = [key for key in ("name", "mode") if key not in payload]
        if missing:
            raise ValueError(say("preset.incomplete", None,
                                 missing=", ".join(missing), source=source))
        return cls(
            name=str(payload["name"]),
            mode=str(payload["mode"]),
            state=dict(payload.get("state") or {}),
            source=source or "shipped",
        )


class PresetStore:
    """A directory of saved arrangements.

    The working directory by default, beside `defaults.toml` and for the
    same reason: it is the thing a person keeps with the study, commits,
    and passes to somebody else. Reinstalling yerkon does not touch it,
    which a folder inside the package would not manage (ADR-0039 is the
    lesson — a bare name went to the shell's own directory, the command
    reported success, and the site appeared nowhere).

    Nothing is written until something is saved, so a person who never
    saves one never grows a folder they did not ask for.
    """

    def __init__(self, directory="presets") -> None:
        self.directory = pathlib.Path(directory)

    def names(self) -> tuple[str, ...]:
        """Saved names, in order. Shipped ones are not files and are not
        listed here; `Presets.for_mode` puts the two together."""
        if not self.directory.is_dir():
            return ()
        return tuple(sorted(
            path.stem for path in self.directory.glob("*" + SUFFIX)
            if A_NAME.match(path.stem)
        ))

    def path_for(self, name: str) -> pathlib.Path:
        if not A_NAME.match(name or ""):
            raise ValueError(say("preset.bad_name", None, name=name))
        return self.directory / (name + SUFFIX)

    def read(self, name: str) -> Preset:
        path = self.path_for(name)
        if not path.exists():
            raise UnknownPreset(say(
                "preset.unknown", None, name=name,
                known=", ".join(self.names()) or "—",
                directory=str(self.directory)))
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(say("preset.unreadable", None,
                                 path=str(path), error=error)) from error
        return Preset.from_json(payload, source=str(path))

    def write(self, preset: Preset) -> pathlib.Path:
        """Save it, and hand back where it went.

        Written whole rather than merged into whatever was there: a
        preset is one arrangement, and saving half of one over another
        half is not a thing anybody wants.
        """
        path = self.path_for(preset.name)
        self.directory.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(preset.as_json(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    def remove(self, name: str) -> None:
        path = self.path_for(name)
        if not path.exists():
            raise UnknownPreset(say(
                "preset.unknown", None, name=name,
                known=", ".join(self.names()) or "—",
                directory=str(self.directory)))
        path.unlink()


#: What "empty" empties. Everything else — the ground, how long and wide
#: the site is, the region, the scheme — is the row's own and stays.
CLEARED = {"runs": [], "units": [], "moved": {}, "removed": [], "overrides": {}}


def empty_state(mode: str, from_scenario) -> dict:
    """This row's own ground, with nothing standing on it.

    A blank sheet rather than a blank slate. The urban row stands on
    Kızılay and the tunnel row goes through a mountain, and somebody
    loading the empty urban arrangement wants to build an urban
    arrangement — on urban ground, not on a default twenty-four
    kilometres of modelled hills.

    Derived from the row rather than from whatever the tab happens to be
    showing, so that "empty" is the same thing every time it is loaded.
    An earlier version left the extent alone, which meant the empty
    arrangement inherited the shape of whatever it replaced.
    """
    return {**from_scenario(mode).as_json(), **CLEARED, "scenario": mode}


def shipped(mode: str, which: str, from_scenario) -> Preset:
    """One of the two arrangements that need no file.

    `from_scenario` is passed in rather than imported: this module is
    read by the CLI to print a table, and the table has no business
    pulling in a viewer to do it. The viewer hands over its own builder.
    """
    if which not in SHIPPED:
        raise ValueError(say("preset.unknown", None, name=which,
                             known=", ".join(SHIPPED), directory="—"))
    state = (empty_state(mode, from_scenario) if which == "empty"
             else from_scenario(mode).as_json())
    return Preset(name=which, mode=mode, state=state, source="shipped")


def offered(mode: str, store: "PresetStore", from_scenario) -> tuple:
    """Every arrangement this tab can be loaded from, in order.

    The two shipped ones first, then whatever is saved. Saved ones are
    not filtered by mode: an arrangement built on the rural row is often
    exactly what somebody wants to look at on the urban one, and the
    thing that decides which row it runs as is the tab it is loaded into
    rather than the tab it was saved from.
    """
    out = [shipped(mode, which, from_scenario) for which in SHIPPED]
    for name in store.names():
        try:
            out.append(store.read(name))
        except (ValueError, UnknownPreset):
            # A file somebody hand-edited into nonsense. Listing the rest
            # beats refusing to list anything.
            continue
    return tuple(out)
