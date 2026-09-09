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
- `observation.py`, the one type the estimator may see. It imports
  nothing, which is what makes ADR-0003 enforceable rather than hoped for.
- `estimator.py`, ranges into positions: a damped least-squares first fix
  and a constant-velocity filter that takes each range at its own instant.
- `evaluate.py`, where the parts meet: journeys along a graded road,
  per-fix error samples, availability, and swept service area.
- `cost.py`, CAPEX from the bill of materials and OPEX from an inventory
  of named recurring items, each carrying its own provenance.
- `scenarios.py`, the three deployments the table describes, as
  configuration rather than as code.
- `report.py`, the four rows and what they rest on.
- `ranging.py`, the two-way exchange: clocks, schemes, air time.
- `design.py` and `proposal.py`, the settings a person chooses and the
  panel that shows every consequence of an edit before applying it.

Not built yet: the table,
the viewer. `docs/HANDOFF.md` has the plan and the open questions.

## Running

```bash
pip install -e ".[dev]"
pytest
```

## The table

```bash
yerkon table
```

| Sistem | Teknoloji | Ortam | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] | Kullanılabilirlik | Alan [km²] | CAPEX [TL/km²] | OPEX [TL/km²/yıl] |
|---|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir içi) | Karasal PNT (SX1280/LoRa TWR) | Dış | 3,35 | 10,40 | 30,70 | %97,83 | 5,34 | 13082 | 6061 |
| YERKON (Kırsal) | Karasal PNT (E28-SX1280 TWR) | Dış | 2,69 | 10,33 | 113,21 | %99,22 | 58,00 | 21424 | 888 |
| YERKON (Tünel) | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 0,19 | 0,66 | 6,63 | %96,02 | 0,02 | 4453423 | 849511 |
| YERKON Ağırlıklı Ortalama | Karasal PNT | İç + dış | 2,72 | 10,21 | 86,76 | %98,42 | 25,87 | 460453 | 88337 |

The OPEX column is the one the report leaves empty for all four rows. It
comes from an inventory of named recurring items rather than a percentage
of capital (ADR-0006), and like every cost figure here it rests mostly on
rates nobody supplied — the command prints that share alongside.

Three things the table will not do without saying so:

**The tunnel's cost per km² is not comparable to the other rows.** A bore
12 m wide over 2 km is 0,024 km², so dividing by it produces a large
number by arithmetic rather than by judgement. On cost per route
kilometre the tunnel is 53441 TL and the rural corridor 51774 TL, which
is the comparison that means something.

**The service area is where a position is available**, not where a packet
arrives. For the rural corridor those are 58,00 and 445,44 km², a factor
of 7,7, and the notes print both every time (ADR-0012).

**VPE is what roadside geometry supports**, with no height constraint
anywhere. Tens of metres on the open road, six in the tunnel where the
anchors surround the receiver rather than lining up beside it (ADR-0011).

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

## Changing a setting

Settings are not independent, so an edit shows what it drags with it and
asks once (ADR-0009):

```console
$ yerkon design --mounting sign
You asked to change:
  mounting  tall mast -> roadside sign

Which also changes:
  anchor height                         25,0 m -> 3,0 m
    because the mounting structure sets how high the anchor stands
  usable range                         5,52 km -> 1,66 km
    because range is whatever the link budget allows at the target precision
  range where the link still decodes  38,93 km -> 15,54 km
    because the same budget decides where the link stops decoding

Apply all of that? [y/N]
```

The consequences are computed by the same link budget the simulation runs
on, not by a list of rules kept alongside it, and a test enforces that.

## What a deployment actually delivers

A 24 km corridor over rolling ground, anchors staggered either side on
25 m masts, a vehicle at 100 km/h, no height constraint:

| Anchor spacing | Anchors | HPE p50 | HPE p95 | Availability | Reached | Served |
|---|---|---|---|---|---|---|
| 1500 m | 17 | 2,64 m | 9,58 m | 1,000 | 445,2 km² | 75,2 km² |
| 2000 m | 13 | 3,11 m | 10,46 m | 0,984 | 447,2 km² | 57,2 km² |
| 3000 m | 9 | 4,69 m | 17,05 m | 0,981 | 409,0 km² | 15,2 km² |
| 4000 m | 7 | 5,22 m | 22,82 m | 0,972 | 392,5 km² | 15,2 km² |

Reached is ground where a packet arrives. Served is ground where four
anchors are in reach at once, which is what a position needs. They differ
by a factor of twenty-six at 4 km spacing, and quoting the first as
coverage would understate cost per km² by the same factor (ADR-0012).

So spacing is a geometry question, not a range question. Four kilometres
is well inside a mast's 5,5 km usable range and still leaves a receiver
one anchor short of a fix for most of the corridor.

## What it costs, and what that rests on

Thirteen anchors over 24 km, on a service area of 57,2 km²:

| | 13 masts (25 m) | 13 lighting columns (12 m) |
|---|---|---|
| Anchor units | 14074,84 TL | 14074,84 TL |
| Structures and installation | 1105000,00 TL | 39000,00 TL |
| Standalone power | 123500,00 TL | 0,00 TL |
| **Capital** | **1242574,84 TL** | **53074,84 TL** |
| Operating, per year | 51516,85 TL | 25834,84 TL |
| Radios as a share of capital | 1,1 % | 26,5 % |

The bill of materials — the only sourced part of any of this — is about
one percent of the cost of a mast-based network. What a deployment costs
is decided by what the anchors are bolted to and whether mains power
reaches them, not by which radio is inside.

That is why the deployment mixes structures, and why every costing prints
the share of itself that rests on figures nobody supplied. For the table
above that share is 99 %: the site costs and every operating rate are
order-of-magnitude placeholders carrying `ASSUMPTION` provenance and a
note saying so (ADR-0006). They are configuration, and the numbers move
when they are sourced.

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

## What the exchange adds on top

A range is not read off a link budget. Two radios trade frames, and at
SF10 a frame lasts 15,8 ms. In single-sided ranging the difference
between the two clocks multiplies that whole reply delay:

| Clock offset | Single-sided error | Double-sided error |
|---|---|---|
| 10 ppm, uncorrected | 24,1 m | 0,3 mm |
| 0,5 ppm, after frequency correction | 1,20 m | 0,02 mm |

Twenty-four metres is eight times the largest error ever measured on the
part, so the published measurements are themselves evidence that the
frequency-offset estimate every receiver already makes is doing the
ranging work too. Without it, ranging on this radio does not function.

With it, the scheme to choose is a per-radio answer. On the SX1280 at
kilometres the waveform bound is metres and the clock term is one metre,
so single-sided ranging costs nothing and saves a third of the air time.
On the impulse radio at 100 m the floor is 10 cm and the single-sided
clock term is also 10 cm, so double-sided earns its extra frame.

Air time is now a quantity the study can spend, and it buys less than it
looks:

| | SX1280 at SF10 | DWM3000 |
|---|---|---|
| Ranging frame | 15,75 ms | 1,06 ms |
| Double-sided exchange | 47,86 ms | 3,77 ms |
| Ranges per second | 20,9 | 265,1 |

A round against six anchors on the SX1280 therefore takes 239 ms, during
which a vehicle at 100 km/h travels 6,7 m — more than twice the 2,94 m
ranging error beside it. The ranges in one round are not simultaneous and
cannot be solved as though they were. That is a conclusion about the
estimator, reached before the estimator was written, and it is why the
receiver uses a filter rather than a snapshot trilateration.

## What the estimator gets

A receiver driving past six anchors at 100 km/h, ranged round after round
over 17 s, with no height constraint:

| | Snapshot per round | Filter |
|---|---|---|
| HPE p50 | 5,20 m | 1,46 m |
| HPE p95 | 6,42 m | 2,55 m |
| VPE p50 | 51,90 m | 23,41 m |

The snapshot is worse because it blames eight metres of vehicle motion on
the ranges. The filter knows the measurements happened 48 ms apart and
does not.

The vertical is bad for a different reason, and no amount of filtering
fixes it. Twenty-two metres of mounting-height spread against four
kilometres of baseline is no spread at all, so every range is very nearly
horizontal and the height barely enters the arithmetic. Mixing signs at
3 m with masts at 25 m makes no measurable difference. VPE in the tens of
metres is the true answer for a network of roadside anchors, and ADR-0011
records why it is reported rather than constrained away.
