# 0003. The estimator sees only observations

## Status
Accepted. Fixes a defect in the previous codebase.

## Context
The previous filter took the receiver's true height and true lateral
position, added noise, and fed them back as "map" measurements. It also
propagated on accelerations read from the truth trajectory. Its
"radio-only" comparison still received lateral map aid and still used those
accelerations.

Both make the reported accuracy meaningless: the filter was told the answer
and the ablation did not remove the aid it claimed to remove.

## Decision
The estimator takes one argument: a sequence of Observations. An
Observation carries a measured value, the surveyed position of whatever
produced it, a timestamp and a variance. Truth is not reachable from inside
the estimator package, and a test asserts that the package does not import
the world package.

Map aiding, where used, comes from a Map object with its own error, built
independently of the receiver's trajectory. A map can be wrong, and a
map-matching failure is a modelled event rather than an impossibility.

Ablations switch off the production of observations, not their use.
Switching off odometry means no odometry observations exist.

## Consequences
Vertical accuracy is now a statement about the radio geometry, which is
what the comparison table asks for. It is worse than the previous
codebase reported, and it is honest.
