"""One edit, one confirmation, every consequence shown. See ADR-0009.

Settings in this project are not independent: the region sets legal
power, which sets how far a link still ranges within tolerance, which
sets how far apart anchors can stand. This module makes that chain
visible before anything changes rather than after.

The consequences are not listed here. They are computed by
``design.derive``, which calls the same link budget the simulation runs
on, so the panel cannot drift away from what the model actually does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from yerkon.design import Design, Outcome, derive
from yerkon.numbers import decimal_comma
from yerkon.rf import DEFAULT_SEARCH_LIMIT_M


@dataclass(frozen=True)
class Change:
    """One value that would move, written the way a person reads it."""

    label: str
    before: str
    after: str
    #: Why this one follows. Empty for the change that was asked for.
    because: str = ""

    @property
    def is_consequence(self) -> bool:
        return bool(self.because)


#: Why each derived value moves. Stated once, here, because a panel that
#: shows a number changing without saying what changed it is the thing
#: this module exists to avoid.
WHY = {
    "eirp_dbm": "the region's ceiling and the antenna's gain decide legal power",
    "anchor_height_m": "the mounting structure sets how high the anchor stands",
    "usable_range_m": "range is whatever the link budget allows at the target precision",
    "closure_range_m": "the same budget decides where the link stops decoding",
}


@dataclass(frozen=True)
class Proposal:
    """An edit and everything it would drag with it, not yet applied."""

    current: Design
    proposed: Design
    asked: tuple[Change, ...]
    follows: tuple[Change, ...]

    @property
    def changes_anything(self) -> bool:
        return bool(self.asked or self.follows)

    def accept(self) -> Design:
        """The design as edited. Call only after a person said yes."""
        return self.proposed

    def describe(self) -> str:
        """The panel. One string, rendered by every front end (ADR-0001)."""
        if not self.changes_anything:
            return "Nothing would change."

        lines = ["You asked to change:"]
        width = max(len(c.label) for c in self.asked) if self.asked else 0
        lines += [
            "  {label:<{width}}  {before} -> {after}".format(
                label=c.label, width=width, before=c.before, after=c.after
            )
            for c in self.asked
        ]

        if self.follows:
            lines.append("")
            lines.append("Which also changes:")
            label_width = max(len(c.label) for c in self.follows)
            before_width = max(len(c.before) for c in self.follows)
            for change in self.follows:
                lines.append("  {label:<{lw}}  {before:>{bw}} -> {after}".format(
                    label=change.label, lw=label_width,
                    before=change.before, bw=before_width,
                    after=change.after,
                ))
                lines.append("    because {}".format(change.because))
        else:
            lines.append("")
            lines.append("Nothing else follows from that.")

        return "\n".join(lines)


def propose(current: Design, **edits) -> Proposal:
    """What would change, and what would change with it. Applies nothing."""
    proposed = current.with_(**edits)

    asked = [
        Change(
            label=SETTING_LABELS.get(name, name),
            before=_setting(getattr(current, name)),
            after=_setting(getattr(proposed, name)),
        )
        for name in edits
        if _setting(getattr(current, name)) != _setting(getattr(proposed, name))
    ]

    before, after = derive(current), derive(proposed)
    follows = [
        Change(
            label=OUTCOME_LABELS[name],
            before=shown_before,
            after=shown_after,
            because=WHY[name],
        )
        for name in Outcome.__dataclass_fields__
        for shown_before, shown_after in [
            (show_outcome(name, getattr(before, name)), show_outcome(name, getattr(after, name)))
        ]
        if shown_before != shown_after
    ]

    return Proposal(current, proposed, tuple(asked), tuple(follows))


def confirm(
    current: Design, ask: Callable[[str], bool], **edits
) -> tuple[Design, bool]:
    """Propose an edit, show it, and apply it only on a yes.

    ``ask`` receives the whole panel and answers once for all of it. The
    command line hands it a prompt; the application hands it a dialog.
    Returns the design to use and whether the edit went through, so a
    refusal leaves the caller with exactly what it started with rather
    than a half-applied state.
    """
    proposal = propose(current, **edits)
    if not proposal.changes_anything:
        return current, False
    if ask(proposal.describe()):
        return proposal.accept(), True
    return current, False


SETTING_LABELS = {
    "region": "region",
    "anchor_radio": "anchor radio",
    "antenna": "antenna",
    "mounting": "mounting",
    "receiver_height_m": "receiver height",
    "surface_roughness_m": "ground roughness",
    "target_ranging_sigma_m": "ranging tolerance",
}

OUTCOME_LABELS = {
    "eirp_dbm": "legal radiated power",
    "anchor_height_m": "anchor height",
    "usable_range_m": "usable range",
    "closure_range_m": "range where the link still decodes",
}


def _setting(value) -> str:
    """A setting as a person reads it, whatever type it is."""
    for attribute in ("region", "part", "kind"):
        named = getattr(value, attribute, None)
        if isinstance(named, str):
            return named
    if isinstance(value, float):
        return "{} m".format(decimal_comma(value, 2))
    return str(value)


def show_outcome(name: str, value: float) -> str:
    """One derived value, written the way the panel writes it.

    Public because the front ends print outcomes outside a proposal too,
    and two renderings of the same number that disagree is worse than one
    exported function.
    """
    if name == "eirp_dbm":
        return "{} dBm".format(decimal_comma(value, 1))
    if name == "anchor_height_m":
        return "{} m".format(decimal_comma(value, 1))
    if value <= 0.0:
        # Not a short range. The tolerance is below the radio's own
        # measurement floor, so no distance meets it, including zero.
        return "no distance meets it"
    if value >= DEFAULT_SEARCH_LIMIT_M:
        # The searches stop here. Printing the limit as though the link
        # stopped there would be an invention.
        return "beyond {} km".format(decimal_comma(DEFAULT_SEARCH_LIMIT_M / 1000.0, 0))
    return "{} km".format(decimal_comma(value / 1000.0, 2))
