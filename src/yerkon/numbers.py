"""How numbers are written in this project's output.

A comma for the decimal mark and a dot between thousands, as Turkish
writes them. Every figure that reaches a person passes through here
rather than through ``format`` directly; the pages mark the thousands of
their running text with ``grouped_html`` on the way out.
"""

from __future__ import annotations

import functools as _functools
import operator as _operator


def added(values, start=0):
    """The sum of these, added one after another from the left.

    Python 3.12 made the built-in ``sum`` of floats compensated, so the
    same figures add up a few units in the last place differently under
    3.11, under 3.13 and under the 3.14 the browser simulator runs on. A
    link that closes by a hair under one closes short under another, and
    the simulator on the site gave a VPE of 3,97 m where the table, run
    under 3.11, says 4,00. Plain addition is what 3.11 did, so the table
    stands as published and every interpreter now agrees with it.
    """
    return _functools.reduce(_operator.add, values, start)


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


import re as _re

#: A whole number of four or more digits standing on its own: not the tail
#: of a part number (E28-2G4M20S, C1525), a standard (P.1546, 2022/179) or
#: an address, and not followed by more of one.
_LONG = _re.compile(
    r"(?<![\w.,/:\-#=&?%+])(\d{4,})(?=(?:,\d+)?(?![\w/\-]|[.,]\d))")

#: What a figure is counted in. A four digit number from 1900 to 2099 is a
#: year unless one of these follows it.
_UNITS = _re.compile(
    r"\s*(?:m\b|km|m²|mm|cm|TL|lira|adet|birim|direk|bina|metre|MHz|GHz|kHz|"
    r"kWh|dB|ms|sn|s\b|saat|gün|kişi|units?|anchors?|buildings?|poles?|"
    r"metres?|days?|hours?|people|/km|x\b|×|USD|\$|€)", _re.IGNORECASE)

#: Names in front of which a number is an identifier, not a quantity.
_NAMES = _re.compile(
    r"(?:IEEE|ISO|IEC|EN|TS|ETSI|RG|Madde|Article|sayı|No|no|Kanun|Law|"
    r"Tablo|Table|ADR|ADR-|FY|Q\d|\d\d\.\d\d\.\d{4},?|No\.|isteği|request|"
    r"Kanun\S*\s*\(|Law\s*\(|"
    # A brand or a standard in capitals names what follows: YDL 803040.
    # CAPEX and OPEX are amounts, not brands: CAPEX 10.053 TL/km².
    r"\b(?!CAPEX\b|OPEX\b)[A-Z][A-Z0-9]{1,}(?:-[A-Z0-9]+)?)\s*$")


#: What after a number makes it a name: a law's articles, or a word
#: spelt like a product (LiPo, LoRa) rather than a unit.
_NAMED_AFTER = _re.compile(r"\s*(?:sayılı|Ek\b|Additional|[A-Z][a-z]+[A-Z])")


#: Two whole numbers joined by a dash, a range: 80000-110000 TL. The
#: single-number pattern leaves a number touching a dash alone, so a part
#: number (KF301-5) keeps its digits; a range is two quantities.
_RANGE = _re.compile(
    r"(?<![\w.,/:\-#=&?%+])(\d{4,})([-–])(\d{4,})"
    r"(?=(?:,\d+)?(?![\w/\-]|[.,]\d))")


def grouped(text: str, lone_years: bool = False) -> str:
    """Every quantity in running text with its thousands marked by a dot,
    as Turkish writes them: 1.400 TL, 162.442 TL/km, 6.489,6 MHz.

    Years, law and gazette numbers, standards and part numbers are left
    as they are written, because grouping them would change what they
    name.
    """
    def ranged(found):
        # Both ends are read against what follows the whole range, so a
        # year span (2012-2020 dönemi) stays and a price span is grouped.
        before = text[max(0, found.start() - 12):found.start()]
        after = text[found.end():found.end() + 12]
        return "{}{}{}".format(_mark(found.group(1), before, after),
                               found.group(2),
                               _mark(found.group(3), before, after))

    def _mark(digits, before, after):
        if _NAMES.search(before):
            return digits
        alone = not lone_years and not text.strip(" ≈≤≥<>~%/km²-,0123456789\n")
        # A year has no decimals: 2083,43 is an amount.
        if (not alone and len(digits) == 4 and 1900 <= int(digits) <= 2099
                and not _re.match(r",\d", after)
                and not _UNITS.match(after.lstrip(",0123456789"))):
            return digits
        if _NAMED_AFTER.match(after) and not _UNITS.match(after):
            return digits
        head = len(digits) % 3 or 3
        return ".".join([digits[:head]] + [digits[i:i + 3]
                                           for i in range(head, len(digits), 3)])

    text = _RANGE.sub(ranged, text)

    def one(found):
        digits = found.group(1)
        before = text[max(0, found.start() - 12):found.start()]
        if _NAMES.search(before):
            return digits
        after = text[found.end():found.end() + 12]
        # A number alone, as in a table cell, is a quantity, not a year.
        alone = not lone_years and not text.strip(" ≈≤≥<>~%/km²-,0123456789\n")
        if (not alone and len(digits) == 4 and 1900 <= int(digits) <= 2099
                and not _re.match(r",\d", after)
                and not _UNITS.match(after.lstrip(",0123456789"))):
            return digits
        if _NAMED_AFTER.match(after) and not _UNITS.match(after):
            return digits
        head = len(digits) % 3 or 3
        parts = [digits[:head]] + [digits[i:i + 3]
                                   for i in range(head, len(digits), 3)]
        return ".".join(parts)
    return _LONG.sub(one, text)


#: The parts of a page whose text is not prose: code, and the insides of
#: tags, where a number is an attribute and not something anybody reads.
_TAGS = _re.compile(r"(<(?:script|style|code|pre)\b.*?</(?:script|style|code|pre)>|<[^>]*>)",
                    _re.S | _re.I)


_DRAWINGS = _re.compile(r"(<svg\b.*?</svg>)", _re.S | _re.I)


def grouped_html(page: str) -> str:
    """``grouped`` over the text of an HTML page and nowhere else.

    Inside a drawing a number standing alone is an axis label, and on a
    timeline that is a year, so there a lone year stays a year."""
    def text_of(chunk: str, in_drawing: bool) -> str:
        pieces = _TAGS.split(chunk)
        return "".join(piece if i % 2 else grouped(piece, in_drawing)
                       for i, piece in enumerate(pieces))
    parts = _DRAWINGS.split(page)
    return "".join(text_of(part, i % 2 == 1) for i, part in enumerate(parts))
