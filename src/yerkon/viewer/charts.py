"""Pictures of the table, drawn as SVG the page carries itself.

A thirteen row table with seven measures is a reference, not a picture.
A reader who wants to know where YERKON sits has to hold thirteen
numbers in their head, and nobody does. These draw the same numbers so
the shape of the answer arrives before the reading does (ADR-0074).

Nothing here computes a figure. Every mark is a cell of the published
record or of `comparison.toml`, parsed and placed; if a cell is empty
the mark is absent rather than guessed.

Three rules the drawings follow, from the visualisation guidance:

* **Emphasis, not twelve colours.** This project's three rows carry the
  accent; the other ten are one recessive grey. Thirteen categorical
  hues would be unreadable and would bury the rows the page is about.
* **A bound is drawn as a bound.** `≤ 8` is not the number 8. Those
  marks carry an open end and the caption says so, because plotting a
  ceiling as a point is the one way these pictures could lie.
* **Both palettes are chosen, not flipped.** The colours come from CSS
  custom properties the stylesheet sets for each palette; the accent
  and the recessive grey were checked apart in each, since the pair the
  site uses for text is too close to tell apart on a dark surface.

SVG rather than a plotting library: the site is a folder of files that
has to open with no network and no script (ADR-0065).
"""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from typing import Optional, Sequence

from yerkon.numbers import decimal_comma

#: A number in a cell, with the decimal comma this project writes.
#:
#: Not preceded by a letter, because QZSS names its regions R1 and R2
#: and a plain search finds the 1 in "R1 ≤ 1" before the figure.
NUMBER = re.compile(r"(?<![A-Za-z])-?\d+(?:,\d+)?")

#: What the sign in front of a number does to it.
BOUNDS = (("≤", "at_most"), ("≥", "at_least"), (">", "over"),
          ("<", "under"), ("≈", "about"))


@dataclass(frozen=True)
class Figure:
    """One cell, as far as a drawing can read it."""

    value: float
    #: exact, at_most, at_least, over, under or about.
    kind: str
    #: The cell held two figures and this is the first of them.
    paired: bool = False
    #: Just this figure, written as the cell writes it. A cell holding
    #: "≤ 10 / ≤ 5" carries an average and a worst case; a mark sits on
    #: one of them, so printing the whole pair beside it would label
    #: the mark with a number it is not at.
    text: str = ""

    @property
    def bounded(self) -> bool:
        return self.kind in ("at_most", "at_least", "over", "under")


def figure_in(cell: str) -> Optional[Figure]:
    """The first figure a cell holds, or nothing.

    A cell is text on purpose: most of them are bounds, pairs or
    absences (ADR-0069). This reads the first figure and remembers
    which of those it was, so a drawing can show a ceiling as a ceiling
    instead of quietly promoting it to a measurement.
    """
    cell = cell.strip()
    if not cell or cell == "-":
        return None
    found = NUMBER.search(cell)
    if found is None:
        return None
    value = float(found.group(0).replace(",", "."))
    head = cell[: found.start()]
    kind, shown = "exact", found.group(0)
    for sign, named in BOUNDS:
        if sign in head:
            kind, shown = named, sign + " " + found.group(0)
            break
    return Figure(value=value, kind=kind, paired="/" in cell, text=shown)


@dataclass(frozen=True)
class Mark:
    """One system's figure for one measure."""

    label: str
    figure: Figure
    #: Drawn in the accent rather than the recessive grey.
    ours: bool = False
    #: The cell as the table prints it. Shown beside the mark rather
    #: than a rounding of the parsed value, so a reader moving between
    #: the picture and the table never finds two different numbers.
    shown: str = ""
    #: What a phone calls it, where the full name will not fit.
    short: str = ""

    def named(self, narrow: bool) -> str:
        return (self.short or self.label) if narrow else self.label


def _tick_decades(low: float, high: float) -> list[float]:
    """Powers of ten across a span, with its ends kept inside."""
    first = math.floor(math.log10(low))
    last = math.ceil(math.log10(high))
    return [10.0 ** power for power in range(int(first), int(last) + 1)]


def _labelled(ticks: Sequence[float], place, stop: float,
              apart: float = 44.0) -> set:
    """Which decades get a label when they will not all fit.

    Eleven decades across a phone leave twenty seven pixels a decade
    and a label wants forty, so they run into one another. This walks
    them in order and keeps one only where it clears the last kept by
    `apart` and clears the right edge; the gridlines still mark the
    rest.
    """
    kept, last = set(), None
    for tick in ticks:
        at = place(tick)
        if at > stop:
            continue
        if last is not None and at - last < apart:
            continue
        kept.add(tick)
        last = at
    return kept


def _said(value: float) -> str:
    """A figure the way this project writes one: comma, no grouping.

    Shortened with a suffix past a thousand, because a tick reading
    510064472 is wider than the space between two ticks.
    """
    if value >= 1_000_000:
        return decimal_comma(value / 1_000_000, 0 if value >= 1e7 else 1) \
            + " M"
    if value >= 1000:
        return decimal_comma(value / 1000, 0 if value >= 1e4 else 1) + " k"
    if value >= 10:
        return decimal_comma(value, 0)
    if value >= 1:
        return decimal_comma(value, 1).rstrip("0").rstrip(",")
    places = 2 if value >= 0.01 else 3
    return decimal_comma(value, places).rstrip("0").rstrip(",")


def _text(x: float, y: float, words: str, *, size: float = 12,
          anchor: str = "start", fill: str = "var(--quiet)",
          weight: str = "400") -> str:
    return (
        '<text x="{:.1f}" y="{:.1f}" font-size="{:g}" text-anchor="{}" '
        'fill="{}" font-weight="{}">{}</text>'
    # Text content, not an attribute: & < > need escaping and quotes do
    # not. Escaping an apostrophe here puts &#x27; inside an SVG text
    # node, where it is the reader's problem rather than the parser's.
    ).format(x, y, size, anchor, fill, weight,
             html.escape(words, quote=False))


def _frame(width: float, height: float, body: str, title: str) -> str:
    """One chart, wrapped so a narrow window scrolls it like a table."""
    return (
        '<div class="scroll"><svg class="chart" role="img" '
        'viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}">'
        "<title>{t}</title>{body}</svg></div>"
    ).format(w=width, h=height, t=html.escape(title, quote=False),
              body=body)


def bars(marks: Sequence[Mark], *, title: str, unit: str,
         logarithmic: bool = True, width: float = 860.0,
         label_width: float = 150.0, narrow: bool = False) -> str:
    """One row a system, largest first, with this project's rows lit.

    Logarithmic, because these measures run over decades: a tunnel
    serves 0,02 km² and GPS serves five hundred million, and on a
    straight axis every terrestrial row would be a stub too short to
    see. Which is also why the mark is a dot rather than a bar. A bar
    says its length is the value; on a logarithmic axis that is false
    and there is no zero for it to grow from, so a bar chart here would
    make GPS look four times NavIC instead of two hundred thousand
    times. A dot claims only its position, which is what the axis is
    for.
    """
    drawn = [mark for mark in marks if mark.figure is not None]
    if not drawn:
        return ""
    drawn = sorted(drawn, key=lambda mark: mark.figure.value, reverse=True)
    values = [mark.figure.value for mark in drawn]
    row_height, gap, top, bottom = 26.0, 8.0, 34.0, 34.0
    plot_left = label_width
    plot_width = width - plot_left - (58.0 if narrow else 92.0)
    height = top + len(drawn) * (row_height + gap) + bottom

    if logarithmic:
        low = min(values) / 1.6
        high = max(values) * 1.6
        span = math.log10(high) - math.log10(low)

        def across(value: float) -> float:
            return plot_left + plot_width * (
                (math.log10(value) - math.log10(low)) / span
            )
        ticks = _tick_decades(low, high)
    else:
        high = max(values) * 1.12
        low = 0.0

        def across(value: float) -> float:
            return plot_left + plot_width * (value / high)
        ticks = [high * step / 4 for step in range(5)]

    out = [_text(0, 18, title, size=13, fill="var(--ink)", weight="600")]
    # Gridlines first and hairline, so the data sits on top of them.
    for tick in ticks:
        if tick < low or tick > high:
            continue
        at = across(tick)
        out.append(
            '<line x1="{0:.1f}" y1="{1:g}" x2="{0:.1f}" y2="{2:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                at, top - 6, height - bottom + 6)
        )
        out.append(_text(at, height - bottom + 22, _said(tick), size=11,
                         anchor="middle"))
    out.append(_text(width, height - bottom + 22, unit, size=11,
                     anchor="end"))

    for index, mark in enumerate(drawn):
        y = top + index * (row_height + gap) + 11
        at = across(mark.figure.value)
        colour = "var(--chart-mark)" if mark.ours else "var(--chart-context)"
        lit = "var(--ink)" if mark.ours else "var(--quiet)"
        weight = "600" if mark.ours else "400"
        out.append(_text(plot_left - 10, y + 4, mark.named(narrow),
                         size=10 if narrow else 11,
                         anchor="end", fill=lit, weight=weight))
        # A hairline from the axis to the dot: a guide for the eye
        # across a wide row, drawn at the gridline's weight so it is
        # never read as a bar's length.
        out.append(
            '<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                plot_left, y, at - 7, y)
        )
        out.append(
            '<circle cx="{:.1f}" cy="{:.1f}" r="{}" fill="{}" '
            'stroke="var(--paper)" stroke-width="2"/>'.format(
                at, y, 6 if mark.ours else 5, colour)
        )
        # A ceiling gets an open end, so it never reads as a measurement.
        if mark.figure.bounded:
            back = mark.figure.kind in ("at_most", "under")
            out.append(
                '<path d="M{:.1f} {:.1f} l{} 6 l{} 6" fill="none" '
                'stroke="{}" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round"/>'.format(
                    at + (-11 if back else 11), y - 6,
                    -6 if back else 6, 6 if back else -6, colour)
            )
        shown = mark.shown or mark.figure.text or _said(mark.figure.value)
        out.append(_text(at + (22 if mark.figure.bounded else 14), y + 4,
                         shown, size=10 if narrow else 11, fill=lit,
                         weight=weight))
    return _frame(width, height, "".join(out), title)


def scatter(points: Sequence[tuple[Mark, Figure]], *, title: str,
            across_title: str, up_title: str, width: float = 860.0,
            height: float = 500.0, narrow: bool = False) -> str:
    """Two measures against each other, both logarithmic, ours lit.

    The one drawing that shows the trade the table is about: a system
    is precise because it covers a room, or wide because it covers a
    continent, and the interesting question is what a road gets.
    """
    drawn = [(mark, other) for mark, other in points
             if mark.figure is not None and other is not None]
    if not drawn:
        return ""
    xs = [other.value for _, other in drawn]
    ys = [mark.figure.value for mark, _ in drawn]
    size = 10 if narrow else 11
    left, right, top, bottom = (
        (38.0, 12.0, 40.0, 50.0) if narrow else (62.0, 20.0, 42.0, 54.0))
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_low, x_high = min(xs) / 6.0, max(xs) * 14.0
    y_low, y_high = min(ys) / 3.0, max(ys) * 3.0

    def across(value: float) -> float:
        return left + plot_w * (
            (math.log10(value) - math.log10(x_low))
            / (math.log10(x_high) - math.log10(x_low))
        )

    def up(value: float) -> float:
        return top + plot_h * (
            1 - (math.log10(value) - math.log10(y_low))
            / (math.log10(y_high) - math.log10(y_low))
        )

    out = [_text(0, 18, title, size=13, fill="var(--ink)", weight="600")]
    inside = [t for t in _tick_decades(x_low, x_high)
              if x_low <= t <= x_high]
    across_labels = _labelled(inside, across, left + plot_w - 22.0,
                              44.0 if narrow else 54.0)
    for tick in _tick_decades(x_low, x_high):
        if tick < x_low or tick > x_high:
            continue
        at = across(tick)
        out.append(
            '<line x1="{0:.1f}" y1="{1:g}" x2="{0:.1f}" y2="{2:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                at, top, top + plot_h)
        )
        if tick in across_labels:
            out.append(_text(at, top + plot_h + 18, _said(tick), size=size,
                             anchor="middle"))
    for tick in _tick_decades(y_low, y_high):
        if tick < y_low or tick > y_high:
            continue
        at = up(tick)
        out.append(
            '<line x1="{0:g}" y1="{1:.1f}" x2="{2:.1f}" y2="{1:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                left, at, left + plot_w)
        )
        out.append(_text(left - 8, at + 4, _said(tick), size=size,
                         anchor="end"))
    out.append(_text(left + plot_w, top + plot_h + 38, across_title,
                     size=size, anchor="end"))
    out.append(_text(0, top - 12 if not narrow else top - 8, up_title,
                     size=size, anchor="start"))

    # Where each label goes, decided before anything is drawn. Two
    # labels collide only when they overlap in both directions: the
    # first pass here pushed a label at the left edge down because one
    # at the right edge shared its height, and left the four satellite
    # rows stacked on top of each other.
    def span_of(mark: Mark, x: float) -> tuple[float, float, bool]:
        # Roughly, at 11px: six units a character, plus the dot and gap.
        room = (size * 0.56) * len(mark.named(narrow)) + 18
        flip = x + room > left + plot_w
        return (x - room, x) if flip else (x, x + room), flip

    laid = []
    for mark, other in sorted(drawn, key=lambda pair: pair[0].figure.value):
        x, y = across(other.value), up(mark.figure.value)
        (x0, x1), flip = span_of(mark, x)
        laid.append({"mark": mark, "x": x, "y": y, "label_y": y + 4,
                     "x0": x0, "x1": x1, "flip": flip})
    for _ in range(40):
        moved = False
        for one in laid:
            for two in laid:
                if one is two:
                    continue
                if one["x1"] <= two["x0"] or two["x1"] <= one["x0"]:
                    continue
                gap = one["label_y"] - two["label_y"]
                if 0 <= gap < size + 2:
                    one["label_y"] = two["label_y"] + size + 2
                    moved = True
        if not moved:
            break

    for spot in laid:
        mark, x, y = spot["mark"], spot["x"], spot["y"]
        label_y, flip = spot["label_y"], spot["flip"]
        colour = "var(--chart-mark)" if mark.ours else "var(--chart-context)"
        out.append(
            '<circle cx="{:.1f}" cy="{:.1f}" r="{}" fill="{}" '
            'stroke="var(--paper)" stroke-width="2"/>'.format(
                x, y, 6 if mark.ours else 5, colour)
        )
        # A leader only where the label had to move off its dot.
        if abs(label_y - (y + 4)) > 2:
            out.append(
                '<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
                'stroke="{}" stroke-width="1" stroke-opacity="0.45"/>'.format(
                    x + (-9 if flip else 9), y + 3,
                    x + (-9 if flip else 9), label_y - 4, colour)
            )
        out.append(_text(
            x + (-11 if flip else 11), label_y, mark.named(narrow),
            size=size, anchor="end" if flip else "start",
            fill="var(--ink)" if mark.ours else "var(--quiet)",
            weight="600" if mark.ours else "400",
        ))
    return _frame(width, height, "".join(out), title)


def budget(shares: Sequence[tuple[str, float]], *, title: str,
           width: float = 860.0) -> str:
    """What each error source is worth, as a share of the whole.

    One hue, darker where the share is larger: this is magnitude, not
    identity, and a categorical palette would invite the reader to
    think the sources are kinds rather than sizes.
    """
    kept = [(name, share) for name, share in shares if share > 0]
    if not kept:
        return ""
    kept = sorted(kept, key=lambda pair: pair[1], reverse=True)
    total = sum(share for _, share in kept)
    row_height, gap, top = 24.0, 7.0, 34.0
    label_width, bar_width = 172.0, width - 172.0 - 66.0
    height = top + len(kept) * (row_height + gap) + 10
    biggest = kept[0][1]
    out = [_text(0, 18, title, size=13, fill="var(--ink)", weight="600")]
    for index, (name, share) in enumerate(kept):
        y = top + index * (row_height + gap)
        length = max(bar_width * (share / biggest), 2.0)
        # Light to dark with the share, so the eye reads size as size.
        weight = 0.34 + 0.66 * (share / biggest)
        out.append(_text(label_width - 10, y + 14, name, size=11,
                         anchor="end", fill="var(--ink)"))
        out.append(
            '<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="15" rx="4" '
            'fill="var(--chart-mark)" fill-opacity="{:.2f}"/>'.format(
                label_width, y + 3, length, weight)
        )
        out.append(_text(label_width + length + 10, y + 14,
                         "%{:g}".format(round(100 * share / total, 1)),
                         size=11, fill="var(--quiet)"))
    return _frame(width, height, "".join(out), title)


def spread(rows: Sequence[tuple[str, Figure, Figure, Optional[Figure]]], *,
           title: str, unit: str, width: float = 860.0,
           label_width: float = 150.0, narrow: bool = False) -> str:
    """Each row's error from its median to its ninety fifth, and the
    vertical one beside it.

    A range rather than two separate marks, because the pair is one
    fact: half the fixes land inside the left dot and all but one in
    twenty inside the right. The vertical mark is hollow so it never
    reads as a third point on the same line; it is a different axis of
    the same fix and on these rows it is much the worse one.
    """
    drawn = [row for row in rows if row[1] is not None and row[2] is not None]
    if not drawn:
        return ""
    values = [figure.value for _, low, high, tall in drawn
              for figure in (low, high, tall) if figure is not None]
    row_height, gap, top, bottom = 34.0, 12.0, 38.0, 46.0
    plot_left = label_width
    plot_width = width - plot_left - (58.0 if narrow else 92.0)
    height = top + len(drawn) * (row_height + gap) + bottom
    low_end, high_end = min(values) / 1.5, max(values) * 1.5
    span = math.log10(high_end) - math.log10(low_end)

    def across(value: float) -> float:
        return plot_left + plot_width * (
            (math.log10(value) - math.log10(low_end)) / span)

    out = [_text(0, 18, title, size=13, fill="var(--ink)", weight="600")]
    for tick in _tick_decades(low_end, high_end):
        if tick < low_end or tick > high_end:
            continue
        at = across(tick)
        out.append(
            '<line x1="{0:.1f}" y1="{1:g}" x2="{0:.1f}" y2="{2:.1f}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                at, top - 6, height - bottom + 6)
        )
        out.append(_text(at, height - bottom + 22, _said(tick), size=11,
                         anchor="middle"))
    out.append(_text(width, height - bottom + 22, unit, size=11, anchor="end"))

    for index, (name, low, high, tall) in enumerate(drawn):
        y = top + index * (row_height + gap) + 12
        out.append(_text(plot_left - 10, y + 4, name,
                         size=10 if narrow else 11, anchor="end",
                         fill="var(--ink)", weight="600"))
        out.append(
            '<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
            'stroke="var(--chart-mark)" stroke-width="3" '
            'stroke-linecap="round"/>'.format(
                across(low.value), y, across(high.value), y)
        )
        for figure, filled in ((low, False), (high, True)):
            out.append(
                '<circle cx="{:.1f}" cy="{:.1f}" r="5" fill="{}" '
                'stroke="var(--chart-mark)" stroke-width="2"/>'.format(
                    across(figure.value), y,
                    "var(--chart-mark)" if filled else "var(--paper)")
            )
        out.append(_text(across(high.value) + 13, y + 4,
                         high.text or _said(high.value), size=11,
                         fill="var(--ink)", weight="600"))
        if tall is not None:
            at = across(tall.value)
            out.append(
                '<path d="M{:.1f} {:.1f} l6 6 l-6 6 l-6 -6 Z" fill="none" '
                'stroke="var(--chart-context)" stroke-width="2" '
                'stroke-linejoin="round"/>'.format(at, y - 6)
            )
            out.append(_text(at + 13, y + 20, tall.text or _said(tall.value),
                             size=11, fill="var(--quiet)"))
    return _frame(width, height, "".join(out), title)


def timeline(events: Sequence[tuple[float, str, str]], *, title: str,
             width: float = 860.0) -> str:
    """When each thing happened, on one line.

    Four events over nine years: a chart of counts would say nothing,
    but where they sit against each other is the point — they are not
    a historical curiosity, they are recent and they are speeding up.
    """
    if not events:
        return ""
    ordered = sorted(events)
    first, last = ordered[0][0], ordered[-1][0]
    left, right = 28.0, 28.0
    # The line sits low: every event is labelled above it in two tiers,
    # and the years go under it, so nothing shares a row with anything.
    line_y, plot_w = 104.0, width - left - right
    height = 142.0
    low = math.floor(first) - 0.6
    high = math.ceil(last) + 0.6

    def across(year: float) -> float:
        return left + plot_w * ((year - low) / (high - low))

    out = [_text(0, 18, title, size=13, fill="var(--ink)", weight="600"),
           '<line x1="{:.1f}" y1="{:g}" x2="{:.1f}" y2="{:g}" '
           'stroke="var(--line)" stroke-width="2"/>'.format(
               left, line_y, left + plot_w, line_y)]
    for year in range(int(math.ceil(low)), int(math.floor(high)) + 1):
        at = across(year)
        out.append(
            '<line x1="{0:.1f}" y1="{1:g}" x2="{0:.1f}" y2="{2:g}" '
            'stroke="var(--line)" stroke-width="1"/>'.format(
                at, line_y, line_y + 5)
        )
        if year % 2 == 1 or year == int(math.floor(high)):
            out.append(_text(at, line_y + 20, str(year), size=11,
                             anchor="middle"))
    for index, (year, where, what) in enumerate(ordered):
        at = across(year)
        # Near the right edge a label would run off, so it hangs left.
        edge = at > left + plot_w * 0.78
        anchor = "end" if edge else "start"
        x = at + (-11 if edge else 11)
        base = line_y - (66 if index % 2 == 0 else 26)
        out.append(
            '<line x1="{0:.1f}" y1="{1:g}" x2="{0:.1f}" y2="{2:.1f}" '
            'stroke="var(--chart-mark)" stroke-width="1" '
            'stroke-opacity="0.45"/>'.format(at, line_y - 7, base + 4)
        )
        out.append(
            '<circle cx="{:.1f}" cy="{:g}" r="6" fill="var(--chart-mark)" '
            'stroke="var(--paper)" stroke-width="2"/>'.format(at, line_y)
        )
        out.append(_text(x, base, where, size=11, anchor=anchor,
                         fill="var(--ink)", weight="600"))
        out.append(_text(x, base + 15, what, size=11, anchor=anchor))
    return _frame(width, height, "".join(out), title)
