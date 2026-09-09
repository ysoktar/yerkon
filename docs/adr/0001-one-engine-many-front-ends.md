# 0001. One engine, many front ends

## Status
Accepted.

## Context
The previous codebase grew four ways of running the same physics: a batch
table generator, a set of ad-hoc sweep scripts, a MATLAB waveform study and
a pile of comparison snippets kept in a scratch directory. The numbers in
the documentation came from whichever one ran last, and two of them
disagreed without anything failing.

## Decision
One engine produces every number. It is deterministic given a seed and a
scenario, and it emits a stream of typed events rather than only a summary.

Everything else consumes that stream:

- the table generator reduces it to percentiles and costs,
- the 3D viewer replays it,
- experiments sweep scenario parameters and reduce many streams,
- regression tests assert on it.

A front end may not compute physics. If a viewer needs to show why a link
failed, the engine puts the reason in the event.

## Consequences
The viewer cannot drift from the table, because both read the same run.
Adding a front end costs nothing in physics. The cost is that the event
stream is now an interface: adding a field is cheap, changing the meaning
of one is not.
