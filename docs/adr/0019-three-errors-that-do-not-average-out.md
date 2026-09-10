# 0019. Three errors that do not average out

## Status
Accepted.

## Context
Every error in the model was noise. A range came back as the true
distance plus a draw from a normal distribution, and a filter given
enough of those converges on the truth. Real positioning systems do not
behave that way, and the reason is that their worst errors are not noise.

## Decision
Three additions, all of them biases or outages rather than noise.

**Excess path length.** When something stands in the way, the signal goes
over it, and a range measurement times that longer path. A knife edge `h`
metres above the line of sight adds `h²/2 · (1/d₁ + 1/d₂)`, which is
centimetres for a gentle rise on a long link and ten metres for a ridge
across a short one. It is computed from the clearance the link budget
already knows and it is always positive.

**Anchor survey error.** The estimator is given each anchor's surveyed
position and treats it as exact, so whatever is wrong with the survey
goes into every fix that anchor contributes to. Drawn once per anchor at
the start of a run and held, because a survey error is a property of an
installation rather than of a measurement.

**Packet loss.** Everything the link budget does not model: interference
from the rest of a shared band, collisions with traffic this study does
not simulate, fades the two-ray average smooths over. An exchange lost
this way produces nothing, exactly like one that never closed. 2,4 GHz is
the same band as wireless networking, which is why the town figure is
three times the open-road one and the tunnel's is zero.

None of them changes the variance the observation carries. A receiver
does not know it is being lied to, and a variance inflated to cover a
bias would model one that did.

## Consequences
The tunnel row went from 0,24 m to 1,76 m at the median, on a fifteen
centimetre survey error alone. Its sub-metre figure had been resting on
perfectly known anchors, and the geometry that leaves the vertical
unobservable amplifies a survey error by about ten as well.

That amplification is linear and does not saturate: 0,05 m of survey
error gives 0,68 m, 0,15 gives 1,76, 0,30 gives 3,14. **You cannot
position better than you surveyed the anchors**, and on a corridor you
cannot position within ten times as well.

The road rows barely moved, and that is the same finding from the other
side. A spread radio ranges to about three metres, and a tenth of a metre
of survey error disappears underneath it. The floor is there in every
deployment and it only binds where everything else is better than it.

So a survey specification belongs beside the hardware specification, and
it belongs there most in exactly the deployment that looked least likely
to need it.
