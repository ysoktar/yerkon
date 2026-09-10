# ADR-0022: size a round by how many anchors answer, not by how many a fix needs

## Status

Accepted.

## Context

On real Ankara ground the rural row produced a position 82,3 % of the
time. That is the weakest number in the table, and the obvious readings
of it were all wrong.

The first question was what the failures actually are. Availability
counts a link that did not close the same as a link that was never in
range, and the two have opposite remedies: more masts fix distance, and
nothing about spacing fixes a ridge. Measuring it separated them
completely:

| | share of rural links |
|---|---|
| closed | 53,9 % |
| killed by ground | 46,1 % |
| too far even over clear ground | **0,0 %** |

Not one rural link fails for distance. Every single failure would close
if the terrain were taken away. The masts are not too far apart; they
cannot see each other.

## What was tried

**Height.** A taller mast sees over more ridges, and it works: 25 m to
35 m at unchanged spacing took availability from 82,3 % to 87,8 %,
without a single extra mast. That reads like a bargain until height is
priced. Steel and foundation grow faster than height — roughly as its
square — so at equal money the comparison inverts:

| spacing | height | masts | availability | mast capital |
|---|---|---|---|---|
| 4000 m | 25 m | 33 | 82,3 % | 2 805 000 TL |
| 4000 m | 35 m | 33 | 87,8 % | 5 497 800 TL |
| **3000 m** | **30 m** | **49** | **90,5 %** | **5 997 600 TL** |
| 3000 m | 35 m | 49 | 90,7 % | 8 163 400 TL |

For about six million lira you can buy 87,8 % with tall masts or 90,5 %
with more of them. Spacing wins at equal budget. Either way it is roughly
twice the capital for seven points.

**A neighbour list.** If the nearest anchor is behind a ridge while one
twice as far is in plain sight, a round ordered by distance spends itself
on links that cannot close. A diagnostic supported this: the nearest
eight leave a unit short of four usable ranges 25 % of the time where the
whole field would leave it short 20 %. So the receiver was made to call
back whoever answered last round, keeping two slots free to discover new
ones — which real receivers do, and which costs no mast, no power and no
airtime.

On the first seed it gave +2,57 points. **Across three seeds it gave
+2,57, +0,01 and −1,24.** It was noise, and it was very nearly shipped on
the strength of one run. The five point diagnostic was real but it does
not reach availability, because availability is not gated on getting four
anchors: the tracking filter survives a round on a single range, so most
of a cold-start deficit never shows up in the column.

**Being less fussy.** Raising the ranging tolerance from 30 m to 60 m
changed nothing at all — not one figure to two decimal places. No rural
link that closes is ever noisier than 30 m, so the acceptance gate was
never binding. A dead lever, worth knowing is dead.

## Decision

Poll twelve anchors a round in the rural row rather than eight.

| anchors per round | availability | HPE P50 | round |
|---|---|---|---|
| 8 | 82,3 % | 2,31 m | 509 ms |
| **12** | **89,6 %** | **2,71 m** | **763 ms** |
| 16 | 89,9 % | 2,97 m | 1018 ms |

Across three seeds: +7,29, +5,32, +3,85 points. Positive every time,
which is what the neighbour list was not.

Eight was chosen when the scenarios became areas, on the reasoning that a
position needs four and a little margin looked generous. That reasoning
holds over open ground and fails over real relief. Half the anchors
polled never answer, so eight attempts yield about four replies —
*exactly* what a cold fix needs, with nothing spare, which is why the
column sat in the low eighties. Twelve attempts yield about six. Sixteen
buys another 0,8 points and costs more in update rate than it returns.

`max_anchors_per_round` already belonged to the deployment rather than to
the project, so this is one number on the rural scenario. Urban and
tunnel keep eight: in a town at a 500 m grid and in a bore at 150 m
spacing, almost everything polled answers, and a longer round would buy
nothing and cost update rate.

## Consequences

The rural row goes from 82,26 % to 89,55 % availability for no capital at
all. What it costs is update rate — 1,96 fixes a second per unit down to
1,31 — and about 0,4 m of horizontal error, because the ranges in one
round now span 763 ms and the vehicle moves 21 m in that time. For a
system whose purpose is to be there when GNSS is not, availability is
worth more than the third of a fix per second it costs.

The generalisation is the part worth carrying: **a round is sized by how
many anchors reply, not by how many a position needs.** Those are the
same number only over ground that hides nothing, which is nowhere
(ADR-0021).

Two negative results are recorded above rather than deleted. The
neighbour list is the more useful of them: it is a plausible, cheap,
realistic-sounding mechanism that does not work here, and the next person
to think of it should find out in a paragraph rather than in an
afternoon.

Getting past about 90 % needs money — roughly twice the mast capital, per
the table above — or a journey that follows a road instead of a rectangle
over open country. The second is not yet possible: OpenStreetMap is
unreachable from the machine that fetched this ground, so no site in the
package carries road geometry, and every rural journey drives over
whatever is there. A real alignment would raise this figure again, and
until one is fetched the rural row is conservative for a reason that is
written down rather than assumed.
