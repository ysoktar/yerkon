# ADR-0034: a panel in the order somebody works

## Status

Accepted.

## Context

Everything this project can do is in the page (ADR-0024), and the page
showed it as one column in the order the engine grew: site shape, anchor
groups, receivers, terrain, regulation, ready-made options, run, solver,
sweep, seventy-two settings, result. About three thousand pixels.

Nobody reads three thousand pixels. They scroll it hunting for the one
control they came for, and they cannot see what any of the other sections
are currently set to without opening all of them. The answer — the four
figures the whole study exists to produce — was at the bottom, past the
seventy-two settings, so changing a control and seeing what it did meant
scrolling twice.

Think about somebody with a fresh stretch of road. What do they do, in
order? Find the ground. Say what shape the site is. Put something on it.
Say what it has to achieve. Ask what that rests on. Run it. That order
appeared nowhere in the panel, and the first step — fetching a place —
was fourth down and folded inside a `<details>`.

The seventy-two settings had their own problem. They were labelled with
their own keys: `clock.crystal.residual_ppm`. That is what belongs in
`defaults.toml` and what somebody editing the file needs, and it is not a
name — a list of seventy-two reads as a dump of variables rather than as
the set of things this study is resting on. And thirty-five of them are
still guesses, which is the single most useful thing the list can say; it
said it in a `title` attribute, which is to say it said it to nobody.

## Decision

Six steps, in that order, each a `<details>` whose summary carries its own
state:

    1 YER       kizilay · ölçülmüş zemin
    2 SAHA      3,0 km × 3,0 km alan
    3 YERLEŞİM  49 direk · 1 grup · 2 alıcı
    4 HEDEF     ±5,0 m · TR · tek yönlü
    5 DAYANAK   72 değerin 35 tanesi varsayım
    6 ÇALIŞTIR  üç satır ve ağırlıklı ortalama

One open at a time, brought into view when it opens. Closing loses
nothing, because the line says what the step holds, and that is what
holds the panel to a screen.

The result is pinned to the bottom of the panel and never scrolls away.

Every ranged setting draws a slider and an exact number. A slider whose
step is 500 cannot be given 4000, and a number alone says nothing about
the range it lives in; the number may also go past the slider's ends,
because clamping it would be a control changing a setting by being
looked at.

A search box over every setting, including all seventy-two figures.
Turkish folded to the letters a keyboard reaches without thinking, so
"gurultu" finds gürültü katsayısı. A step is open exactly when it holds a
hit, and everything in it that does not is hidden.

Each figure is named in the language the rest of the page is written in,
with its key a hover away, and carries a coloured mark for where its value
came from. "Yalnız varsayımları göster" reduces the list to the
thirty-five that are still guesses.

## Consequences

The whole study now reads in six lines without scrolling, and the answer
is always on screen beside the controls that move it.

A figure added to `defaults.toml` with no Turkish name falls through as
its own key rather than disappearing — and a test names the ones without
one, so the list does not quietly drift back into being a dump of
variables.

Still inconsistent, and worth saying: the line under each figure saying
what it affects comes from the engine and is in English. Those strings
are built with numbers in them on the Python side; translating them is a
job for the engine, not for the page, and it is not done.
