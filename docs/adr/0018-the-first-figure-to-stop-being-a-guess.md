# 0018. The first figure to stop being a guess

## Status
Accepted.

## Context
`clock.crystal.residual_ppm` was 0,5, chosen because half a part per
million at 2,4 GHz is a 1,2 kHz residual and that seemed unremarkable for
a receiver that has already had to lock to the signal. It was the least
supported number in the model and the one that decided whether
single-sided two-way ranging worked on the SX1280 at all.

`matlab/yerkon_clock_residual.m` measured it. Eight preamble symbols,
three hundred trials, crystal offsets of 2, 5, 10 and 20 ppm, over the
signal-to-noise range where links actually close.

## Decision
The default is 0,0793 ppm, with `MEASUREMENT` provenance and the run it
came from. That is the worst root-mean-square residual over the range,
not the best and not the mean, because a figure that holds only at the
strong end of a link fails at the far end.

## Consequences
Six times better than the guess, and the guess was conservative in the
right direction.

The measurement also says what limits it, which the guess could not. The
residual barely improves with signal: thirty decibels more buys a factor
of two, where a noise-limited estimator would buy thirty. Run with no
noise at all, the same estimator gives 0,0164 to 0,0643 ppm depending
only on where the peak falls between FFT bins — matching the measured
plateau to four decimal places. The floor is the parabolic peak
interpolator, not the channel.

That distinction matters more than the number. A systematic error does
not average down over repeated exchanges, so no amount of ranging
removes it, and a finer interpolator would lower it. The figure is a
property of an estimator rather than of a crystal.

One design decision changed. At the assumed residual the impulse radio's
single-sided clock term was ten centimetres against a ten centimetre
floor, so double-sided ranging earned its third frame. Measured, that
term is 1,6 cm and the floor swallows it. The tunnel deployment is
single-sided now: a third less air time, 0,72 m at the ninety-fifth
percentile instead of 1,00, and half again as many fixes. A test holds
the old value and checks that the old conclusion still follows from it,
so it is clear the answer changed because a number did and not because
the model did.

Thirty-two of thirty-three figures are still assumptions. This is what
sourcing one looks like, and the ordering in `defaults.toml` says which
to do next.

What the measurement does not cover: phase noise, multipath, and drift
during the exchange. It is a floor. The remaining risk is that a real
part sits well above it, and that needs a bench rather than a
simulation.
