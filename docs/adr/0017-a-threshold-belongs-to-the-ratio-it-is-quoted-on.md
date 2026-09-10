# 0017. A demodulation threshold belongs to the ratio it is quoted on

## Status
Accepted. Corrects this project's own link budget.

## Context
Writing a MATLAB script to measure the residual clock offset meant
simulating the receiver, and simulating the receiver meant choosing a
signal-to-noise ratio to simulate it at. The link budget said links close
down to −20 dB *after* the 30,1 dB despreading gain, so the script needed
to work at −20 dB post-correlation.

Nothing works at −20 dB post-correlation. The correlation peak is a
hundredth of the noise floor; there is no peak to find. That was the
first sign.

The second was arithmetic. At the model's claimed closure range of
38,9 km the received power was −156,0 dBm, against a part whose
best-case published sensitivity is −132 dBm. No arrangement of antennas
lets a radio hear twenty-four decibels below itself.

The cause was one line. A LoRa datasheet's "−20 dB" is quoted on the
ratio *in the occupied bandwidth*: working below the noise floor is what
despreading buys, and the figure already assumes it. The model added the
despreading gain and then compared against that same figure, granting
every link thirty decibels twice.

## Decision
A radio says which ratio its threshold is quoted on, and closure is
tested against that one. `threshold_is_in_band` is `True` for the SX1280
family, whose LoRa figure already assumes despreading, and `False` for
the impulse radio, whose working point is quoted after preamble
accumulation because there is no spreading to assume.

The processing gain still exists and still matters. It belongs in the
Cramér-Rao bound, where the relevant quantity is energy per symbol over
noise density, and not in the closure test.

## Consequences
The SX1280's closure range falls from 38,9 km to 11,7 km. Received power
at the edge is −124,8 dBm, above the part rather than below it.

The usable range does not move at all: 5,52 km from a 25 m mast, before
and after. The bound that sets it always used the post-correlation ratio
and was always right. What was wrong was only the claim about how far a
link keeps working after it has stopped being useful — which is to say,
the overstated half of ADR-0007's distinction.

So the four table rows barely move. Every link inside a deployment was
already well within 11,7 km, and the corrected model changes the answer
by a tenth of a metre here and there. The thing that was badly wrong was
the thing nobody was using.

Two claims retract. "Reaching is not ranging" was a factor of seven and
is a factor of two. And no legal configuration outruns the sixty
kilometre search any more, where the loudest used to.

One finding was rebuilt rather than retracted. The claim that gentle
relief beats flat ground rested on a single distance that happened to
suit it. Swept across a corridor, relief is a trade: level ground closes
at every distance with a median error of 5,63 m, ten metres of relief
closes at 72 % of them with a median of 3,08 m, and eighty metres closes
at 17 %. Relief improves the links that survive and kills the ones in
dips.

The simulation now agrees with the budget, which is the check that
matters: the frequency-offset estimator works from +10 dB
post-correlation upward, and +10 dB post-correlation is exactly where the
corrected threshold puts the edge of the link.
