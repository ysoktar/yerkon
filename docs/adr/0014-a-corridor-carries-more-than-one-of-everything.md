# 0014. A corridor carries more than one of everything

## Status
Accepted. Replaces the single-radio deployment.

## Context
The model gave a deployment one anchor module and one receiver, and the
report describes neither.

The bill of materials names three anchor modules and assigns them to
three places: a spread module for towns, the same silicon behind an
amplifier for open country, an impulse radio for tunnels. A real corridor
runs out of a town, across open country and through a bore, so it carries
all three at once and no single row of the table measures that
arrangement.

Both receivers in the same bill carry two radios each. "Yaya alıcısı:
SX1280, DWM3000, ESP32-S3..." and "Kara aracı alıcısı: SX1280, DWM3000,
STM32...". That is not redundancy, it is what lets one unit range against
town anchors on the road and tunnel anchors inside a bore without
anything about the unit changing.

And a deployment serves traffic, not one vehicle.

## Decision
The radio belongs to the anchor. A deployment holds anchors of whatever
kinds it was built with, and units that carry whatever modules they were
built with. A unit ranges against every anchor it shares a waveform with
and silently ignores the rest, which is what the hardware does.

Units share the air. A round is as long as every unit's exchanges laid
end to end, so a second unit does not halve the work, it doubles the
wait.

The viewer edits anchors as *runs* — a stretch of corridor carrying one
module on one mounting at one spacing — because that is how a network is
specified and built. Several runs may overlap.

## Consequences
The capacity constraint became visible and it is severe. In town, sixteen
anchors and two units make a round of 1018 ms, so each unit is fixed once
a second. Adding units does not add fixes: measured over a journey, two
units attempt the same number of rounds in total that one did. The air
was already fully spent.

That cost accuracy immediately. Urban HPE at the median went from 3,35 m
with one unit to 5,06 m with two, because each filter now coasts twice as
long between updates. This is not a regression; it is the first honest
figure, and the earlier one described a network with one customer.

A shared setting no longer moves everything. Changing the region raises
the ceiling for the spread runs and moves nothing for the impulse one,
because an ultra-wideband rating is already an emission limit rather than
a conducted power. The confirmation panel shows the runs that change and
stays quiet about the one that does not.

Swapping the urban module for the rural one changes nothing at all under
the Turkish rule, so the panel does not appear. That was already known
from the link budget; it is now visible where somebody would try it.

## Addendum, 2026-09-10: only the tunnel is a corridor

The three scenarios were all built as corridors — a line of anchors down
one axis and a receiver driving east along it — because the first one
written was a highway and the other two were copied from it. That was
wrong for two of them, and the error was not small.

A town is an area. A stretch of open country is an area. Their anchors
stand on a rough grid of streets or on masts spread over ground, and a
vehicle in either one turns. Modelling them as lines gave every anchor a
receiver could hear nearly the same bearing, which is the geometry that
makes a corridor's cross-track direction barely observable, and the
horizontal error inherited that amplification for no reason but the
shape of the file.

Urban is now a town three kilometres on a side, forty-six anchors on
lighting columns at a five hundred metre grid with alternate rows
staggered. Rural is twenty kilometres on a side, thirty-three masts at a
four kilometre grid. Both are driven on a circuit that runs round the
edge and across the middle, so the cross-track geometry changes as the
unit turns. The tunnel is unchanged, because a bore really is a line.

What it moved: urban HPE at the fiftieth percentile from 5,31 m to
1,24 m, rural from 4,22 m to 2,14 m, and the rural service area from
58 km² to 372,50 km², which took its capital cost per square kilometre
from 21424 TL to 8468 TL. A factor of four in accuracy and a factor of
two and a half in cost, none of it from a change to the physics.

Two consequences follow. A receiver over an area can hear far more
anchors than it has time to range against, so `Deployment` grew
`max_anchors_per_round`: it ranges against the nearest eight and ignores
the rest, which is what real systems do and what keeps a round from
taking two seconds. And `Deployed.serves_a_corridor` now decides whether
cost per route kilometre is printed at all — for an area those route
kilometres are the length of a test journey, not a dimension of the
service, and reporting one as the other is what invited this in the
first place.
