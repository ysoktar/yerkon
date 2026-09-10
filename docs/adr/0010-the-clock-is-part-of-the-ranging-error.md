# 0010. The clock is part of the ranging error, and the exchange decides how much

## Status
Accepted.

## Context
The link budget gives a bound on how precisely a waveform can time an
arrival. It says nothing about the exchange that carries the timing, and
on the hardware this report names the exchange is where most of the error
comes from.

A frame at SF10 lasts about sixteen milliseconds. In single-sided two-way
ranging, the near radio measures a round trip on its own clock and
subtracts a reply delay measured on the far radio's, so the difference
between the two clocks multiplies that whole delay. At ten parts per
million that is eighty nanoseconds, or twenty-four metres — eight times
the only ranging error anyone has actually measured on the part.

That the published measurements do not show twenty-four metres of error
is itself evidence. It says the correction every coherent receiver
already performs in order to demodulate is also doing the ranging work.

## Decision
A range measurement's error is the waveform bound and the clock term
added in quadrature, with the part's measured floor applied underneath.
The clock term comes from three things: the exchange scheme, the reply
delay implied by the frame, and how much of the clock offset survives the
receiver's frequency-offset estimate.

Single-sided ranging multiplies the reply delay. Double-sided ranging
cancels that to first order and multiplies the flight time instead, which
is hundreds of times shorter but grows with distance.

Airtime is counted in the radio's own symbols, over the same preamble the
processing gain is taken over, so a radio cannot be given a cheap frame
and a generous gain at once.

## Consequences
Which scheme to use was a per-radio answer while the residual offset was
assumed, and became one answer once it was measured.

Assumed at half a part per million, the SX1280's single-sided clock term
was one metre against a waveform bound of metres, so single-sided cost
nothing there; the impulse radio's was ten centimetres against a ten
centimetre floor, so double-sided earned its extra frame.

Measured, the residual is 0,0793 ppm (ADR-0018). The impulse radio's
single-sided term falls to 1,6 cm, which its floor swallows whole, and
the extra frame buys nothing on either radio. Both are single-sided now.
On the tunnel row that is a third less air time, 0,72 m at the
ninety-fifth percentile instead of 1,00, and half again as many fixes.

A frequency-offset estimate is not optional on the slow radio. The model
can be asked what happens without one, and the answer is that ranging
stops working.

Airtime is now a quantity the study can spend. A round against six
anchors on the SX1280 takes a quarter of a second, during which a vehicle
at a hundred kilometres an hour travels nearly seven metres — more than
twice the ranging error beside it. The estimator therefore cannot treat a
round as simultaneous, and this is decided here rather than discovered
later.

Half a part per million of residual offset is the least supported number
in the model and the first one worth measuring.
