# 0002. Range is an outcome, not a constant

## Status
Accepted. Replaces the fixed link ranges of the previous codebase.

## Context
The previous codebase decided reachability from three hardcoded numbers:
400 m urban, 3000 m rural, 150 m tunnel. It separately computed a
signal-to-noise ratio to scale measurement error. The two disagreed. A
change to antenna gain moved the measurement error and left reachability
untouched, so no antenna or terrain change could ever alter the node count
or the cost.

The report specifies stock antennas by part number and the deployment needs
5 to 10 km links, evaluated to 15 km. Whether those links close is the
single most consequential question in the study, because it sets the node
count, which sets the capital cost.

## Decision
One function decides both. Given two radios, their antennas and mounting
geometry, the terrain between them and the channel, it returns a Link
Budget: received power, noise, signal-to-noise ratio, and the resulting
time-of-arrival variance.

A link closes when its signal-to-noise ratio clears the demodulation
threshold for the radio's configuration. The same budget sets the variance
of any measurement the link carries and the probability that a packet is
lost. There is no maximum range constant.

## Consequences
Antenna gain, mounting height, terrain obstruction, transmit power and
ranging bandwidth all move node count, accuracy and cost together, which is
the behaviour the study needs.

Long links must now be justified rather than assumed. A 10 km link at
2,4 GHz needs Fresnel clearance the terrain may not give, and the budget
will say so.
