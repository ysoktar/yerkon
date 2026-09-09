# Handoff

What is built, what is next, and what is still undecided. Written so that
another session, or another model, can pick this up without reading the
whole history.

Read `CONTEXT.md` first for the vocabulary and `docs/adr/` for the
decisions. Neither is optional: most of the mistakes this project has
already made were mistakes of vocabulary, and each ADR records one of
them.

## The single deliverable

The YERKON block of the comparison table on page 15 of the report: four
rows (urban, rural, tunnel, weighted), ten columns. Every number traceable
to a datasheet, a published measurement, or a stated assumption.

The report leaves the OPEX column empty for all four rows. Filling it is
in scope; the rates are modular configuration and will be researched
later (ADR-0006).

## Standing constraints

- **Range.** At least 5 km, target 5 to 10 km, evaluated out to 15 km,
  using only the modules the report's bill of materials names, with their
  stock antenna. No better antenna is assumed.
- **Roads have grade.** Nothing fixes a receiver to a constant height
  (ADR-0004).
- **The estimator is fusion, without a height constraint.**
- **Service area is the real area the anchors reach**, not the corridor
  strip.
- **Mounting is mixed**: existing roadside furniture (signs, gantries,
  billboards) alongside purpose-built masts.
- **Numbers use a comma decimal mark and no thousands separator.**
- **Changing one thing that forces another needs confirmation**, shown as
  a panel listing every value that would change, answered with a single
  y/n for the whole batch. Both the CLI and the app render the same panel
  (ADR-0009). Built.

## Built

| Module | What it owns |
|---|---|
| `evidence.py` | `Sourced` and `Provenance`, so a datasheet figure and a guess do not look alike |
| `hardware.py` | the modules the report names, with their published figures |
| `regulatory.py` | what each region's rules allow: Turkey, Europe, the United States, licensed |
| `rf.py` | the link budget |
| `world.py` | terrain, graded road alignments, mounting structures |
| `site/` | real ground and buildings, fetched once into a cache |
| `design.py` | the settings a person chooses, and what they imply |
| `proposal.py` | the confirmation panel: one edit, one y/n, every consequence shown |
| `numbers.py` | comma decimal mark, no thousands separator |
| `cli.py` | the `fetch` and `design` verbs |

`tests/test_architecture.py` inspects imports so the estimator cannot
reach the truth. It is a test, not a convention, on purpose.

### The one module the study turns on

`rf.py` decides two different things from one calculation: whether a link
closes, and how precisely it can measure. Keeping them together is what
makes range an outcome rather than a constant (ADR-0002), and separating
them is the change most likely to quietly break this project.

The distinction that ADR-0007 exists to protect: **reaching is not
ranging.** A link at 15 km still has 29 dB in hand and still measures
distance to twenty-six metres. Anything that reports link closure as
though it were coverage is wrong.

## Next, in dependency order

1. **`ranging`** — real two-way ranging: timestamp exchanges, clock
   offset and drift, reply turnaround, and the scheduling that decides
   how many anchors a receiver can range against per second. Produces
   `Observation`s and nothing else.
2. **`estimator`** — fusion without a height constraint. May import
   `ranging`'s observation type. May not import `world`; the architecture
   test enforces this.
3. **`evaluate`** — journeys, per-fix error samples, percentiles.
   Deterministic: every run reseeds, because a previous version of this
   project silently carried one scenario's random state into the next and
   invalidated every swept comparison in its docs.
4. **`cost`** — CAPEX from the bill of materials, OPEX from the inventory
   in ADR-0006.
5. **`report`** — the four rows. The weighted row combines the raw
   samples, never the percentiles (ADR-0005).
6. **The 3D viewer** — live, and everything configurable.

Deferred by explicit instruction until the above is done: the algorithm
that sites anchors for a target accuracy at least cost.

## Open questions

- **OPEX rates.** Energy, connectivity, service life, maintenance visit
  frequency, central operation. Each needs a source or an explicit
  assumption marker.
- **The multipath channel and the implementation floor** want calibrating
  against MATLAB once `ranging` exists. The floor is currently one
  published measurement per radio.

## What this project has already got wrong

Kept because each one is a mistake worth not repeating.

- Free-space path loss for near-ground links understated loss by 13 to
  34 dB and produced a "10 km with 50 dB to spare" claim. Two-ray ground
  reflection replaced it (ADR-0007).
- "Use the widest bandwidth" was wrong. Position error is U-shaped in
  bandwidth, because a wide channel resolves multipath into separate
  peaks and a peak detector picks the strongest, which in a blocked
  channel is a reflection.
- A stateful RNG shared across scenarios contaminated every swept
  comparison in the old repository's documentation.
- Cramér-Rao alone claimed 2 cm from a narrowband radio at 100 m against
  about 3 m measured. The model now reports the larger of the bound and
  the measured floor.
- LAMBDA80-24S is the SX1280 module, not an antenna. The antenna is the
  Inventek W24P-U.
- Earth bulge is the midpoint sag `d₁d₂/(2kR)`, not the tangent-plane
  form, which overstated the clearance needed at 15 km by four times.
- "I cannot download elevation data here" was wrong, concluded from three
  hosts. Copernicus tiles come straight from public object storage.
