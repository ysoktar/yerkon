# ADR-0027: a figure can be a name, and an option that changes nothing is a lie

## Status

Accepted.

## Context

`rural-hard-ground` shipped as one of four named deployment options. Its
note said it stood the rural row on Gölbaşı's 907 m of relief instead of
Polatlı's 486 m, and that availability fell from about 90 % to about 45 %.

Checking the shipped options against their own notes after the ground
corrections, it produced **exactly the default's numbers** — 89,50 %
availability, 2,69 m at the fiftieth percentile, to every digit.

It set `site.rural_relief_m`, which is the *fallback* relief used when no
ground has been fetched. Polatlı is fetched and ships with the package,
so the fallback is never consulted and the option changed nothing at all.

Nothing raised. `options.write` already refuses an option naming a figure
the settings file does not hold — that check exists precisely to stop a
saved file that quietly does nothing. This one named a figure that
exists and simply is not read in the configuration that ships.

The reason it could not do better is that the thing it needed to change
was not a figure. Which site a row stands on lived in `scenarios.py` as
`RURAL_SITE = "polatli"`, and `defaults.toml` held numbers only. So the
option reached for the nearest number instead.

That also left the viewer's new fetch panel half-connected: somebody
could fetch İzmir from the page, look at it, and have no way to put a
report row on it.

## Decision

**A `Sourced` value may be a name as well as a number.**
`Settings.number` refuses a name with a message saying to ask for its
text; `Settings.text` returns it. An edit is coerced by the kind the
entry already is, because a page sends everything as text and without
that a spacing would be stored as the string `"3000"` and compare
unequal to `3000` everywhere.

`urban.site`, `rural.site` and `tunnel.site` are now DESIGN figures like
the spacings beside them. They carry directory names under
`src/yerkon/site/ankara/`, empty meaning modelled terrain. Anything
`yerkon fetch` writes — including from the viewer — can go in one.

`rural-hard-ground` sets `rural.site = "golbasi"` and now does what it
says. In the figures panel a name renders as a picker of the sites
actually fetched rather than a free text box, because typing a directory
that is not there is the one mistake this can make.

## Consequences

The fetch panel is connected end to end: fetch a place from the page,
then point a report row at it, and the table, the dissection and the
solver all run against it.

Three tests now pin the failure that got here: that the site is a figure,
that the option reaches other ground, and that asking a name for a number
says so rather than guessing.

The wider lesson is about the check that did not fire. `options.write`
verifies that every key an option names exists. That is not the same
question as whether the key is *read* in the configuration it will be
applied to, and this project has now been caught twice by that gap —
once here and once when sixteen deployment figures were sent to the
viewer with no group heading to draw them under, so they were present,
correct and invisible. Existence is cheap to check. Being consulted is
not, and the only thing that catches it is running the thing and
comparing against what it claimed.

Which is what found this: not a test, but re-reading four notes against
four fresh runs.
