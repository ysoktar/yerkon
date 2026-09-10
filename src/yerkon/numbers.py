"""How numbers are written in this project's output.

The report uses a comma for the decimal mark and no thousands separator,
so every figure that reaches a person passes through here rather than
through ``format`` directly.
"""

from __future__ import annotations


def readable(value: float) -> str:
    """A figure at whatever precision it actually needs, and no more.

    The defaults span three hundred microseconds to two hundred and forty
    thousand lira. A fixed two places renders the first as zero, which is
    worse than ugly: a figure that reads as unset when it is set will be
    "corrected" by somebody.

    A whole number keeps no decimals, because sixteen bytes is sixteen
    bytes. Everything else keeps three significant figures with the
    trailing zeros trimmed off.
    """
    number = float(value)
    if number == 0.0:
        return "0"
    if number == int(number) and abs(number) < 1e15:
        return decimal_comma(number, 0)

    import math

    magnitude = abs(number)
    places = max(2 - int(math.floor(math.log10(magnitude))), 1)
    text = decimal_comma(number, places)
    if "," in text:
        text = text.rstrip("0").rstrip(",")
    return text


def decimal_comma(value: float, places: int = 2) -> str:
    """A number as the report writes it: comma decimal mark, no grouping.

    ``places`` of zero gives a whole number with no mark at all, which is
    what a count or a metre of mast height wants.
    """
    if places < 0:
        raise ValueError("places is a count of digits")
    text = "{:.{places}f}".format(float(value), places=places)
    return text.replace(".", ",")
