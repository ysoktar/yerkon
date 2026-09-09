# 0005. The weighted row combines samples, not percentiles

## Status
Accepted.

## Context
Report footnote 32 already says the weighted row averages the P50 and P95
values of the three scenarios, and that this is not the same as combining
the samples. It is not the same, and the averaged figure has no
distributional meaning.

## Decision
The weighted row draws from the three scenarios' raw per-fix error samples
in proportion to the weights, then computes percentiles from that combined
sample.

Weights are configuration, defaulting to the report's 50% urban, 35% rural,
15% tunnel.

## Consequences
The weighted row's P95 can sit outside the range of the three input P95
values, which is correct: a mixture's tail is driven by its worst
component.

Footnote 32 will need rewriting when this table is published.
