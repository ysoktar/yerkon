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
