"""Named deployment options: a few shipped, and any number saved later.

Every number that shapes a deployment lives in the settings file
(ADR-0023), which means an option is just a short list of edits to it.
That is the whole design: an option carries no machinery, only the
handful of figures it moves and the reason it moves them, so a new one
costs a file rather than a code change.

Three come with the project because the study kept running into them —
the rural row's two ways of buying availability, and a denser town — and
`yerkon solve` writes more of the same shape.
"""

from __future__ import annotations

import pathlib
import tomllib
from dataclasses import dataclass, field
from typing import Optional

from yerkon.language import chosen
from yerkon.numbers import readable
from yerkon.settings import DEFAULTS, Settings

#: Where the shipped options live, and where saved ones are written.
OPTIONS = pathlib.Path(__file__).resolve().parent / "options"

SUFFIX = ".toml"


@dataclass(frozen=True)
class Option:
    """A named set of edits to the settings, and why somebody made them."""

    name: str
    title: str
    note: str
    #: Figures this option moves, keyed as `defaults.toml` keys them.
    values: dict = field(default_factory=dict)
    #: Where it came from: shipped with the project, or written by a search.
    origin: str = "shipped"
    #: The English beside the Turkish above.
    #:
    #: Beside one another rather than in two files, for the same reason
    #: the settings file carries both: two files drift, and an option
    #: whose Turkish and English claim different things about the same
    #: figures is worse than one with no English at all (ADR-0035).
    #:
    #: Last rather than beside their Turkish, because this class is built
    #: positionally in a dozen places and putting a new field in the
    #: middle of one silently shifts every argument after it — which is
    #: how an option with no values at all passed a test that existed to
    #: refuse exactly that.
    title_en: str = ""
    note_en: str = ""

    def said(self, language: Optional[str] = None) -> tuple[str, str]:
        """Its title and note, in one language.

        Falls back to the Turkish where an option has no English — a
        saved option written before this, or one somebody wrote by hand —
        because refusing to show it would hide a deployment somebody
        saved rather than prompt them to translate it.
        """
        if chosen(language) == "en":
            return (self.title_en or self.title, self.note_en or self.note)
        return (self.title, self.note)

    def applied_to(self, settings: Settings = DEFAULTS) -> Settings:
        """The settings this option describes.

        Refuses a key the settings file has no entry for, because a
        typo that silently did nothing would be an option that claims to
        change something and does not.
        """
        return settings.with_values(self.values)

    def differences(self, settings: Settings = DEFAULTS) -> tuple[tuple, ...]:
        """What this option moves, as (key, from, to).

        A figure may be a name rather than a number — which ground a row
        stands on is as much a deployment choice as its spacing
        (ADR-0027) — so both sides come back as they are stored.
        """
        out = []
        for key, value in sorted(self.values.items()):
            was = settings.sourced(key)
            out.append((
                key,
                was.value if was.is_text else float(was.value),
                str(value) if was.is_text else float(value),
            ))
        return tuple(out)

    def as_toml(self) -> str:
        lines = [
            "# Bir YERKON yerleşim seçeneği. / A YERKON deployment option.",
            "#",
            "# `--option {}` ile defaults.toml üzerine uygulanır; yalnızca"
            .format(self.name),
            "# farklı olan değerler listelenir.",
            "#",
            "# Applied over defaults.toml with `--option {}`. Only the"
            .format(self.name),
            "# figures that differ are listed; everything else stays as it is.",
            "",
            "name = {!r}".format(self.name),
            "title = {!r}".format(self.title),
        ]
        if self.title_en:
            lines.append("title_en = {!r}".format(self.title_en))
        lines.append("origin = {!r}".format(self.origin))
        lines.append('note = """{}"""'.format(self.note))
        if self.note_en:
            lines.append('note_en = """{}"""'.format(self.note_en))
        lines += ["", "[values]"]
        for key, value in sorted(self.values.items()):
            lines.append("{!r} = {!r}".format(
                key, value if isinstance(value, str) else float(value)))
        return "\n".join(lines) + "\n"

    def describe(
        self, settings: Settings = DEFAULTS, language: Optional[str] = None
    ) -> str:
        """One block a person can read before choosing it."""
        title, _ = self.said(language)
        lines = ["{}  —  {}".format(self.name, title)]
        for key, was, now in self.differences(settings):
            lines.append("    {:<38} {} -> {}".format(
                key, _shown(was), _shown(now)
            ))
        return "\n".join(lines)


def _shown(value) -> str:
    """A figure as a person reads it, name or number."""
    return value if isinstance(value, str) else readable(value)


def available(where: Optional[pathlib.Path] = None) -> tuple[str, ...]:
    """Every option on hand, shipped or saved, by name."""
    directory = where or OPTIONS
    if not directory.exists():
        return ()
    return tuple(sorted(
        path.stem for path in directory.glob("*" + SUFFIX)
    ))


def read(name: str, where: Optional[pathlib.Path] = None) -> Option:
    """One option by name, saying what is on hand if it is not there."""
    directory = where or OPTIONS
    path = directory / (name + SUFFIX)
    if not path.exists():
        raise FileNotFoundError(
            "no option called {}. There is: {}".format(
                name, ", ".join(available(directory)) or "nothing"
            )
        )
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    missing = {"name", "title", "note", "values"} - set(payload)
    if missing:
        raise ValueError(
            "{} is not a complete option: it has no {}".format(
                path, ", ".join(sorted(missing))
            )
        )
    return Option(
        name=str(payload["name"]),
        title=str(payload["title"]),
        note=str(payload["note"]),
        title_en=str(payload.get("title_en", "")),
        note_en=str(payload.get("note_en", "")),
        values={
            str(k): v if isinstance(v, str) else float(v)
            for k, v in payload["values"].items()
        },
        origin=str(payload.get("origin", "shipped")),
    )


def write(option: Option, where: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Save an option so it can be chosen by name from then on.

    Checks it against the settings first. An option naming a figure that
    does not exist would be a saved file that quietly changes nothing,
    and a search that produced one would look like it had found
    something.
    """
    option.applied_to(DEFAULTS)

    directory = where or OPTIONS
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (option.name + SUFFIX)
    path.write_text(option.as_toml(), encoding="utf-8")
    return path


def settings_for(
    name: Optional[str],
    settings: Optional[Settings] = None,
    where: Optional[pathlib.Path] = None,
) -> Settings:
    """The settings a run should use, given an option name or none."""
    base = settings or DEFAULTS
    if not name:
        return base
    return read(name, where).applied_to(base)
