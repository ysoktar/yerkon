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
- `regulatory.py`, the power a band allows, per region.
- `rf.py`, the link budget: one calculation that decides both whether a
  link closes and how precisely it can measure.
- `world.py`, terrain, a graded road alignment, and the structures an
  anchor can be mounted on.
- `site/`, real ground and real buildings, fetched once and cached.

Not built yet: ranging protocol, estimator, evaluation, cost, the table,
the viewer. `docs/HANDOFF.md` has the plan and the open questions.

## Running

```bash
pip install -e ".[dev]"
pytest
```

## Fetching a site

Real ground, once, into a cache. Everything else runs offline against it
(ADR-0008).

```bash
yerkon fetch --south 39.85 --west 32.70 --north 39.98 --east 33.05 \
             --into sites/ankara-o20 --spacing 30
```

Three sources are tried in turn and the first that answers wins:

1. a GeoTIFF you already have, if you pass `--geotiff`;
2. the **Copernicus 30 m** tiles in public object storage, which need no
   key, have no rate limit, and cover a whole degree square in one file.
   Tiles are cached under `sites/_tiles`, so a second site in the same
   square costs nothing;
3. a public query service, which is slower, coarser, and limited to a
   thousand calls a day. It is the fallback, not the plan.

Buildings come from OpenStreetMap alongside. If they cannot be fetched
the site records that nobody looked, rather than implying open ground.

## What the link budget already says

Using only the parts the report names, at the power Turkey allows, over
open ground with the receiver on a vehicle roof at 1,5 m:

| Link | Margin | Ranging sigma |
|---|---|---|
| 5 km, 25 m mast | 44,9 dB | 4,10 m |
| 10 km, 25 m mast | 32,8 dB | 16,41 m |
| 5 km, 35 m mast | 47,8 dB | 2,94 m |
| 10 km, 35 m mast | 35,8 dB | 11,72 m |
| 15 km, 35 m mast | 28,7 dB | 26,37 m |

Every one of those links closes, and that is the least interesting thing
about them. Closing is not the constraint; **precision** is. A link with
33 dB in hand still measures distance to sixteen metres, because the
ranging bound falls off with signal-to-noise ratio long after the packet
is still being decoded. Reading "the link closes at 15 km" as "the system
works at 15 km" is the mistake this table exists to prevent.

Height is what buys range. Solving for the distance at which ranging
sigma reaches 5 m, over open ground:

| Mounted on | Height | Usable range |
|---|---|---|
| Roadside sign | 3 m | 1,66 km |
| Sign gantry | 6 m | 2,51 km |
| Billboard | 10 m | 3,47 km |
| Lighting column | 12 m | 3,83 km |
| Purpose-built mast | 25 m | 5,52 km |
| Tower | 35 m | 6,53 km |

The 5 to 10 km requirement is therefore met from purpose-built masts and
not from existing roadside furniture. Signs and gantries are worth using
where they happen to sit, but a network built only from them needs
anchors every two to three kilometres.

Two further consequences, both testable claims in `tests/test_rf.py`:

The rural module's 27 dBm amplifier buys nothing in Turkey, because the
band caps radiated power by density and the cap binds at 12,1 dBm at this
bandwidth. Both anchor radios therefore radiate the same power and reach
the same distance. Under the American rules, which cap conducted power
instead, the same amplifier is worth about 18 dB.

A narrowband radio does not deliver centimetres at short range. The
waveform bound says 2 cm at 100 m; the part measures about 3 m. The model
reports the larger of the two.
