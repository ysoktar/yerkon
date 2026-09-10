# ADR-0023: a deployment is a file, not a decision baked into code

## Status

Accepted.

## Context

ADR-0016 moved every figure nobody supplied into `defaults.toml`, and
the viewer made all of them editable while it runs. That was the right
rule applied to half the numbers.

The other half stayed in `scenarios.py` as literals: how far apart the
anchors stand, how much ground a row covers, how many anchors a round
polls, how noisy a range may be before it is thrown away, how wide the
bore is. Every one of them decides a column of the published table.

The cost of that showed up as soon as the study got interesting. Fixing
the rural row meant trying spacings, mast heights and round sizes — and
every one of those experiments was a scratch script that edited a
literal, ran, printed, and threw the arrangement away. The findings
survived in an ADR; the arrangements did not survive at all. Nobody
could re-run them, the viewer could not show them, and the two
defensible answers for the rural row could not both exist, because
`scenarios.py` can only hold one number at a time.

There was also a smaller problem waiting. Putting these in the settings
file alongside the placeholders would have made "99 % of this costing
rests on figures nobody supplied" quietly wrong, because anchor spacing
is not a figure waiting for a measurement. Nobody can measure what
spacing *really is*. It is the thing being decided.

## Decision

**Three parts.**

**A `DESIGN` provenance.** Deployment geometry goes in the same file as
everything else — one place changes every number in the table, and the
viewer already edits anything in that file — but marked as a choice
rather than as a placeholder. `Settings.assumed_share` counts only the
figures that could in principle be measured, so the number that says how
much of this study is guesswork keeps meaning what it says.

**Named options.** An option is a short list of edits to the settings
and the reason somebody made them, in a file of its own. It carries no
machinery: a new one costs a file, not a code change. It *composes* with
`--defaults` rather than replacing it, so somebody's real quotations and
a denser grid survive together — an option that replaced the file would
silently discard every measured figure in it.

Four ship, because the study kept running into them:

| option | what it is |
|---|---|
| `rural-dense` | 49 masts at 3 km, 30 m tall. The cheapest way past 90 % |
| `rural-tall` | The same 33 masts, 10 m taller. Loses at equal money, wins per site |
| `urban-dense` | Anchors on every lighting column rather than every other |
| `rural-hard-ground` | The Gölbaşı hills: what this design costs where it was not meant to go |

The first two are there together on purpose. Which is right depends on
whether money or site access is the scarce thing, and this project does
not have the figures to say.

**A solver.** `yerkon solve` searches arrangements against a target and
saves the winner as a new option. Two rules shape it:

*It runs the real simulation.* Each candidate is a full scenario against
fetched ground, which is why it is slow and why its answers can be
trusted against the table — they come from the same engine. A surrogate
fitted to a few runs would be a second model of the same thing,
disagreeing with the first exactly where the ground is difficult.

*Cheapest that meets, not best.* A search that maximised availability
would always return the densest grid it was offered, because more
anchors always help a little. What somebody with a budget needs is the
least expensive arrangement that clears the bar — the same rule
ADR-0015 settled for structures, applied to geometry.

It also refuses two things rather than producing a misleading file. If
nothing meets the target it returns nothing, not the best of a bad set,
because a search that returns its least-bad failure needs its answer
checked by hand every time. And if the settings already meet the target
it says so instead of saving an option that changes nothing, which would
sit in the list looking like a decision.

## Consequences

Sixteen figures moved out of `scenarios.py` into the settings file, and
`scenarios.py` stopped holding any number that decides a column.
Everything downstream came along for free: they are editable live in the
viewer, they can be sourced, they appear in `yerkon defaults`, and they
can be searched.

The solver immediately earned its place. Asked for a tunnel under a
metre at the fiftieth percentile, it found that 120 m bracket spacing —
seventeen anchors instead of fourteen, 23 000 TL more — takes that row
from 1,81 m to **0,48 m**. Nearly four times the accuracy for a fifth
more capital, in the row whose per-square-kilometre cost is already the
largest in the table by three orders of magnitude. Nobody had tried it,
because trying it used to mean editing a literal.

What this does not do is make the search cheap. Thirty-six rural
arrangements is thirty-six full simulations and the better part of half
an hour. That is the price of the first rule, and the alternative was a
faster answer that could not be checked against anything.
