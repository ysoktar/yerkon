# ADR-0035: two languages, beside each other

## Status

Accepted.

## Context

The report this answers is Turkish, and the people who will check it work
in Turkish. The code, the decisions and the tests are English, because
that is what they were written in and rewriting fifteen thousand lines of
comments would be a large, risky change that nobody would read.

The page sat between the two. Its chrome was Turkish; the seventy-two
figures said what they rest on and what they affect in English; the
ground described itself in English; the ready-made options argued for
themselves in English. So the one surface built for the people who need
it most was the one that could not decide.

Translating it was the first answer, and the wrong one: it deletes the
English rather than adding the Turkish, and it makes the page unreadable
to anyone reading the code beside it.

## Decision

Two languages, and neither is a translation of the other in the sense
that one is the original. A chooser sits beside the search box — two
buttons rather than a menu, because a two-item menu costs a click to find
out what is in it — and switching asks the engine again rather than
translating what the page already has.

Text somebody **wrote** lives beside the value it describes:
`note`/`note_en`, `affects`/`affects_en`, `source`/`source_en`,
`sensitivity`/`sensitivity_en` in `defaults.toml`, and
`title`/`title_en`, `note`/`note_en` in each option. Both beside one
value, not in two files, because two files drift and the failure is not
a bad translation — it is two different claims about the same number.

Text the project **builds** lives in `language.py`, as a pair of format
strings under one name. Text the page builds lives in `words.js`, the
same way. A name missing a language raises rather than falling back:
a fallback is a page nine tenths translated and nobody noticing the
tenth.

Nothing decides anything. The values, the geometry and every result are
identical in both, and a test builds the whole table twice to say so.

Numbers are written the same way in both: a comma decimal mark and no
thousands separator, which is what the report uses. The English is a way
into the same study rather than a second study, and a figure with two
written forms is a figure somebody can quote two ways.

A recorded fact is not translated. `Copernicus DEM 30 m ×2` is what was
fetched, stored in the manifest on disk; it used to read `(2 tiles)`,
which meant the cached sites were English whatever the page was set to.

## Consequences

The panel, the figures, the ground, the options and the solver's output
all read in whichever language is chosen, and the engine is the only
thing that holds any of those words.

Two things came out of the build worth keeping:

`say(key, ...values)` was positional at first, on the reasoning that the
two languages do not want their pieces in the same order. They do not —
"72 değerin 35 tanesi varsayım" counts the total first, "35 of 72 figures
are assumptions" counts the assumptions first — and with `{}` in both,
one language silently gets the other's numbers. It did, on the very first
sentence that had two. Fields are named now, and each language orders
them as it likes.

Adding `title_en`/`note_en` in the middle of the `Option` dataclass
shifted every positional argument after them, which made an option with
no values at all pass the test that exists to refuse exactly that. New
fields go on the end.

## What is not done

`report.py`, `deliver.py` and the command line still speak Turkish only.
The table's row names, its column headings and the Markdown deliverables
are the report's own words, and putting them in both is the same work
again on a different surface. The page says so where it shows them: what
the engine hands the viewer is in the chosen language, and what `yerkon
table` prints is not.
