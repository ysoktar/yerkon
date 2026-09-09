"""How numbers are written in this project's output.

The report uses a comma for the decimal mark and no thousands separator,
so every figure that reaches a person passes through here rather than
through ``format`` directly.
"""

from __future__ import annotations


def decimal_comma(value: float, places: int = 2) -> str:
    """A number as the report writes it: comma decimal mark, no grouping.

    ``places`` of zero gives a whole number with no mark at all, which is
    what a count or a metre of mast height wants.
    """
    if places < 0:
        raise ValueError("places is a count of digits")
    text = "{:.{places}f}".format(float(value), places=places)
    return text.replace(".", ",")
