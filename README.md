# YERKON simulation

Estimates what a terrestrial positioning network built from the YERKON
hardware delivers, and what it costs to build and run. The output is the
YERKON block of the comparison table on page 15 of the report.

This is a rebuild. The previous version is in the git history and its
numbers should not be used; the reasons are in `docs/adr/`, and the short
version is that its filter could see the answer and its link range was a
constant rather than a result.

## Where to start

- `CONTEXT.md` is the glossary. Read it before the code.
- `docs/adr/` records the decisions and what each one replaced.
- `src/yerkon/rf.py` is the module the study turns on.

## State

Built and tested:

- `evidence.py`, which makes a datasheet figure and a guess look different.
- `hardware.py`, the parts the report's bill of materials names, with
  their published figures.
- `rf.py`, the link budget: one calculation that decides both whether a
  link closes and how precisely it can measure.

Not built yet: world, ranging protocol, estimator, evaluation, cost, the
table, the viewer. `docs/HANDOFF.md` has the plan and the open questions.

## Running

```bash
pip install -e ".[dev]"
pytest
```

## What the link budget already says

Using only the parts the report names, at the power the band allows:

| Link | Margin | Ranging sigma |
|---|---|---|
| 5 km, 35 m mast | 57 dB | 1,01 m |
| 10 km, 35 m mast | 51 dB | 2,01 m |
| 15 km, 45 m mast | 48 dB | 3,02 m |

The 5 to 10 km requirement is met with the stock antenna and tens of
decibels to spare. What limits the long links is Fresnel clearance rather
than power: at 15 km the path needs about 16 m of clearance over the
highest ground, so mast height and terrain decide the range, not the radio.

Two consequences follow, and both are testable claims in `tests/test_rf.py`:

The rural module's 27 dBm amplifier buys nothing, because the band caps
radiated power at 12,1 dBm at this bandwidth. Both anchor radios therefore
radiate the same power and reach the same distance.

A narrowband radio does not deliver centimetres at short range. The
waveform bound says 2 cm at 100 m; the part measures about 3 m. The model
reports the larger of the two.
