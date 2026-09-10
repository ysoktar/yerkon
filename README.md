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
- `site/`, real ground and real buildings, fetched once and cached —
  including four fetched Ankara areas committed inside the package, so a
  clone reproduces the table with no network.
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
- `terms.py` and `budget.py`, the seven named error sources and the
  dissection that re-runs each scenario with one of them silenced, so the
  table's accuracy figures come with the reason they are what they are.
- `siting.py`, the search for the cheapest deployment that meets a target.
- `settings.py` and `defaults.toml`, every figure nobody supplied *and*
  every number that shapes a deployment, in one file that nothing else
  may add to.
- `options.py` and `options/`, named deployment options — a short list of
  edits to that file and the reason somebody made them.
- `solve.py`, the search for the cheapest arrangement that meets a
  target, which saves its winner as a new option.
- `viewer/`, a local web app over the same engine: the site in three
  dimensions, every setting live, and the confirmation panel in front of
  any change that forces another.
- `ranging.py`, the two-way exchange: clocks, schemes, air time.
- `design.py` and `proposal.py`, the settings a person chooses and the
  panel that shows every consequence of an edit before applying it.

`docs/HANDOFF.md` has the open questions and what is still a placeholder.

## Running

```bash
pip install -e ".[dev]"
pytest
```

## The viewer

```bash
yerkon view
```

Opens a local web app. The site in three dimensions, with the ground, the
route, each anchor and the ring it ranges within tolerance; the swept
coverage painted on the ground in two colours, one for ground a packet
reaches and one for ground where four anchors are in reach at once.

Four modes: the report's urban, rural and tunnel rows, and a **mixed
corridor** that runs out of a town, across open country and through a
bore, carrying all three anchor modules at once. None of the report's
three rows measures that arrangement; this one does.

**Zemin** picks the ground: fetched Ankara — Kızılay, Polatlı,
Kızılcahamam, Gölbaşı — or modelled hills. There is no flat option, on
the selector or on the relief slider, because nowhere is flat and a level
plane is the most favourable surface this model can draw rather than the
neutral one (ADR-0021). Choosing a fetched site greys out the three
modelled-terrain sliders, since a real grid brings its own relief,
roughness and obstructions.

**En** — the site's width — is the knob that decides the shape of
everything. At zero the site is a corridor: anchors line the road either
side and units drive straight. Above zero it is an area: anchors spread
over a staggered grid and units drive a circuit round the edge and across
the middle. The geometry a receiver gets from the two is not comparable,
which is why both are shown rather than one assumed. Urban and rural open
as areas; the tunnel and the mixed corridor open as lines.

Anchors are edited as *runs* — a group carrying one module on one
mounting at one spacing — and a site may hold as many as it needs, each
drawn in its own colour with its own reach ring. Units are edited the
same way: as many as you like, each with its own speed, start, antenna
height and set of modules, drawn on the route it takes.

Everything is live. Drag an anchor, shift-click to remove it, add or drop
a run or a unit, move any slider, and the scene and the numbers follow.

Changes that force other changes — region, module, mounting, tolerance,
roughness — raise the confirmation panel first, listing every value that
would move with its old and new figure and why it follows, answered once
for the whole batch (ADR-0009). The panel is grouped by anchor run and
says which it means, because a shared setting does not move every run the
same way: switching to the American rules raises the ceiling for the
spread runs and moves nothing for the impulse one. Dragging an anchor,
adding a unit or changing the terrain forces nothing, so it applies
immediately.

The page holds no physics. Every number on it was computed by the modules
that build the table, so the picture and the report cannot disagree. It
draws its own three dimensions rather than loading a library from a
content delivery network, so it works with the machine offline
(ADR-0013).

## The defaults

The report gave a bill of materials and nothing else. Every other figure
this project needs is a default somebody chose, and all of them live in
one file. It is called defaults rather than assumptions because that is
what it stays: a figure does not leave the file when somebody sources it,
it just stops being an assumption.

```bash
yerkon defaults --full
```

```
Still assumed in src/yerkon/defaults.toml
35 of 36 figures are still assumptions (%97).

mounting.tall_mast.site_cost_tl                  85000,00 TL
                                          affects: CAPEX of every anchor on a
                                          mast; 88,9 % of the rural row's capital
                                          sensitivity: masts beat signs only
                                          below 6588 TL, so 13 times cheaper
```

Nothing in `src/` may construct an assumption of its own — a test walks
the syntax tree of every module and fails the build if one tries, so the
file is the whole list (ADR-0016). Costs, mounting heights, the two
unpublished radio figures, the clocks, the urban clutter figure and the
filter's manoeuvre allowance are all on it.

Replacing one is three edits in one place: the value, the source, and
`provenance` from `ASSUMPTION` to what it now is. Then:

```bash
yerkon table --defaults my-figures.toml
yerkon site  --defaults my-figures.toml
yerkon view  --defaults my-figures.toml
```

Everything is rebuilt from it — scenarios, mounting catalogue, radios,
clocks, rates — and the share each result reports as resting on guesses
falls. Sourcing the mast cost alone takes the siting answer from %94
assumed to %69.

**Or edit them in the viewer.** All 33 appear in `yerkon view`, grouped,
each with what it affects written under it. Change one and everything
rebuilds live: raise the mast height from 25 m to 40 m and the panel
asks first, then the reach ring in the scene grows from 5,52 to 6,98 km.
Change a site cost and it applies at once, because a price moves no
physics. A figure edited by hand stays an assumption unless you give it a
source — that distinction is the difference between exploring and
reporting. **Dosyaya yaz** writes what you have back out as a file that
goes straight back in through `--defaults`.

It moves the answers, too. At a mast cost of 8500 TL existing signs still
win; at 5000 TL masts take over at 17 anchors for 264906 TL. The
break-even the costing predicts at 6588 TL is something you can walk up
to from either side by editing one line.

## Siting

```bash
yerkon site --corridor 12000 --tolerance 5
```

Searches for the least expensive deployment that meets a target, using
the structures the corridor already carries and building only where none
stands. Every candidate is a deployment somebody could build, scored by
the same link budget and priced by the same bill of materials the table
uses.

Over 8 km of rolling ground at a 5 m ranging tolerance, with signs
standing every 250 m:

| Deployment | Anchors | CAPEX | Corridor covered |
|---|---|---|---|
| Existing roadside signs every 600 m | 21 | 274736 TL | %96,7 |
| Existing roadside signs every 500 m | 25 | 327067 TL | %96,7 |
| Purpose-built 25 m masts every 800 m | 16 | 1529323 TL | %96,7 |

**The signs win by five and a half times**, despite reaching 1,66 km
against a mast's 5,52 km. Height buys range, and range is not what is
scarce — money is, and a sign that already stands costs a thirty-fourth
of a mast that does not. That is the mixed-mounting strategy arrived at
by search rather than by assertion, and it inverts the intuition the
range figures give (ADR-0015).

The search refuses, too. A tolerance under the radio's own ~2,94 m
measurement floor is not a siting problem, and no arrangement of anchors
meets it, so nothing is returned rather than the best of a bad set.

What it cannot do is invent a survey. Which structures stand where is
configuration, and the defaults are an assumption about a typical stretch
of Turkish highway.

## The table

```bash
yerkon table
```

| Sistem | Teknoloji | Ortam | HPE P50 [m] | HPE P95 [m] | VPE P95 [m] | Kullanılabilirlik | Alan [km²] | CAPEX [TL/km²] | OPEX [TL/km²/yıl] |
|---|---|---|---|---|---|---|---|---|---|
| YERKON (Şehir içi) | Karasal PNT (SX1280/LoRa TWR) | Dış | 1,64 | 4,92 | 43,65 | %99,11 | 10,54 | 19055 | 8828 |
| YERKON (Kırsal) | Karasal PNT (E28-SX1280 TWR) | Dış | 2,71 | 10,35 | 143,34 | %89,55 | 671,75 | 4696 | 195 |
| YERKON (Tünel) | Karasal PNT (UWB/DWM3000 TWR) | İç + dış | 1,81 | 2,96 | 8,25 | %100,00 | 0,02 | 4453423 | 849511 |
| YERKON Ağırlıklı Ortalama | Karasal PNT | İç + dış | 2,02 | 7,65 | 109,84 | %93,39 | 273,97 | 456748 | 89443 |

Every row stands on **real Ankara ground**, fetched once from the
Copernicus 30 m DEM and committed inside the package, so a clone
reproduces these numbers with no network (ADR-0008). The town is Kızılay,
three kilometres on a side, rising and falling 91 m across it. The open
country is the Polatlı plain, twenty kilometres on a side and 486 m of
relief. The tunnel is a real 2 km alignment through the mountains at
Kızılcahamam, falling 1,79 % between portals whose elevations are the
mountain's.

Nothing anywhere is flat, and that is a decision rather than a detail —
see ADR-0021. Each row also carries two units sharing the air, which is
why the update rate is half what one unit would see; and only the tunnel
is a corridor, which the addendum to ADR-0014 explains.

The OPEX column is the one the report leaves empty for all four rows. It
comes from an inventory of named recurring items rather than a percentage
of capital (ADR-0006), and like every cost figure here it rests mostly on
rates nobody supplied — the command prints that share alongside.

Three things the table will not do without saying so:

**The tunnel's cost per km² is not comparable to the other rows.** A bore
12 m wide over 2 km is 0,024 km², so dividing by it produces a large
number by arithmetic rather than by judgement. On cost per route
kilometre the tunnel is 53441 TL. The other two rows serve areas rather
than lines, so their route kilometres are the length of a test journey
and no cost per kilometre is quoted for them at all.

**The service area is where a position is available**, not where a packet
arrives. For the rural region those are 671,75 and 1188,00 km², a factor
of 1,8, and the notes print both every time (ADR-0012).

**Rural availability is decided by terrain, and by the length of a
round.** Not one rural link fails for distance — every single failure
would close if the ground were taken away — so more masts are the wrong
instinct. What was wrong was the round: eight anchors polled over ground
that blocks half of them yields about four replies, exactly what a cold
fix needs and nothing spare. Polling twelve took the row from 82,3 % to
89,6 % for no capital at all, costing a third of the update rate and
0,4 m of horizontal error. Getting past 90 % does cost money: about twice
the mast capital, either as more masts or taller ones. ADR-0022 has the
priced curve, and the two things that were tried and did not work.

**VPE is what the geometry supports**, with no height constraint
anywhere. Tens of metres in the open, under seven in the tunnel where the
anchors surround the receiver rather than lining up beside it (ADR-0011).

## Choosing a deployment

```bash
yerkon options                       # what is on hand
yerkon options rural-dense           # one of them in full
yerkon table --option rural-dense    # run the table against it
```

Every number that shapes a deployment lives in `defaults.toml` alongside
the physics — anchor spacing, site extent, stagger, anchors polled per
round, ranging tolerance, bore width. So an **option** is just a short
list of edits to that file plus the reason somebody made them, and a new
one costs a file rather than a code change (ADR-0023). Options compose
with `--defaults`, so real quotations and a denser grid survive together.

Four ship, and the first two are there together on purpose:

| option | what it is |
|---|---|
| `rural-dense` | 49 masts at 3 km, 30 m tall — the cheapest way past 90 % |
| `rural-tall` | The same 33 masts, 10 m taller — loses at equal money, wins per site |
| `urban-dense` | Anchors on every lighting column rather than every other |
| `rural-hard-ground` | The Gölbaşı hills: what this design costs where it was not meant to go |

Which of the first two is right depends on whether money or site access
is the scarce thing, and this project does not have the figures to say.
So it ships both rather than picking.

### Searching for a new one

```bash
yerkon solve --scenario tunnel --availability 0.99 --hpe-p50 1.0 --save tunnel-precise
```

Searches arrangements against a target, and saves the cheapest that meets
it as a named option. Every candidate is a full simulation against real
ground — slow, and its answers agree with the table by construction.

It found something nobody had tried, because trying it used to mean
editing a literal: **120 m bracket spacing takes the tunnel row from
1,81 m to 0,48 m** at the fiftieth percentile. Seventeen anchors instead
of fourteen, 23000 TL more, in the row whose cost per square kilometre is
already the largest in the table by three orders of magnitude.

Two things it refuses. If nothing meets the target it returns nothing
rather than the best of a bad set, because a search that hands back its
least-bad failure needs checking by hand every time. And if the settings
already meet the target it says so instead of saving an option that
changes nothing.

`--vary KEY=A,B,C` searches any figure in the settings file, not just the
short default list per scenario.

## Where the error came from

```bash
yerkon budget
```

An accuracy figure nobody can act on is half a result. This re-runs each
scenario with one error source silenced at a time — seven sources,
sixteen runs each — and reports what every one of them was worth
(ADR-0020). It is the same engine the table uses, so it cannot disagree
with it.

```
Tünel — HPE P50 1,81 m, P95 2,96 m; bir menzilin σ'sı 0,10 m, geometri çarpanı ×18,1

  Hata kaynağı           Tek başına  Kalkarsa  Kazanç  Çare
  ---------------------  ----------  --------  ------  -----------------------------------
  Direk konum ölçümü           1,77      0,17    1,64  direkleri GNSS ile daha iyi ölçmek
  Donanım ölçüm tabanı         0,19      1,78    0,02  daha iyi bir modül
  Dalga formu gürültüsü        0,11      1,82   -0,02  daha yüksek güç, daha yakın direk
  Saat kayması                 0,10      1,80    0,00  TCXO ya da çift taraflı TWR
  Fazladan yol (engel)         0,09      1,81    0,00  direği yükseltmek
  Kaybolan alışveriş           0,09      1,81    0,00  daha temiz kanal
  Tur içi hareket              0,00      1,80    0,01  daha kısa tur
  Model artığı                 0,09                    hiçbir kaynak açık değilken kalan
```

Two columns, because they answer different questions. **Tek başına** is
the error if that source were the only one. **Kalkarsa** is what the
whole error falls to if it goes away and every other stays — always the
smaller saving, because errors add in quadrature, and the only one of the
two that is a purchase decision.

The tunnel is the most accurate deployment in the study by every hardware
measure and comes out the least accurate of the three. The dissection
says why: its bore multiplies one range's sigma by eighteen, and what it
multiplies hardest is the anchor survey error, the one term that never
averages out. Buying a better radio for it buys nothing; surveying its
brackets properly takes it from 1,81 m to 0,17 m.

On the open road the ranking inverts. In town the module's own
measurement floor is worth 1,13 m and the survey error 0,09 m; in the
country the waveform noise dominates at 2,10 m against the floor's
1,51 m, because a rural link is kilometres long and the bound rises with
distance. The geometry multiplier for both is *below one* — 0,6 and 0,5 —
so an area with a filter running across it comes out better than a single
range. That number is the quantitative form of what the corridor framing
had been hiding.

One row of the table only became measurable when the ground did.
**Fazladan yol** — the extra distance a signal travels over an
obstruction — read exactly 0,00 m everywhere while two of the three
scenarios stood on a level plane, not because the term is small but
because a plane cannot obstruct anything. On real Ankara it is 0,41 m in
the country, 0,11 m in town and 0,09 m in the bore. See ADR-0021.

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

A corridor study — not one of the table's rows, two of which are areas.
24 km over rolling ground, anchors staggered either side on 25 m masts, a
vehicle at 100 km/h, no height constraint:

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
| 5 km, 25 m mast | 14,8 dB | 4,10 m |
| 10 km, 25 m mast | 2,7 dB | 16,41 m |
| 5 km, 35 m mast | 17,7 dB | 2,94 m |
| 10 km, 35 m mast | 5,7 dB | 11,72 m |
| 15 km, 35 m mast | does not close | — |

Every one of those links closes, and that is the least interesting thing
about them. Closing is not the constraint; **precision** is. A link with
33 dB in hand still measures distance to sixteen metres, because the
ranging bound falls off with signal-to-noise ratio long after the packet
is still being decoded.

The gap is a factor of two, not the factor of seven this project claimed
for a fortnight. The link budget was adding the 30,1 dB despreading gain
and then testing against a threshold that already assumed it, so links
"closed" 24 dB below the part's own sensitivity. Writing a simulation of
the receiver is what caught it: nothing demodulates at −20 dB after
correlation, because there is no peak to find. Corrected, the SX1280
closes to 11,7 km and ranges usefully to 5,52 km (ADR-0017). The usable
range did not move — only the overstated half.

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

## What sharing the air costs

A deployment serves traffic, not one vehicle, and the units queue at the
same anchors. A round is every unit's exchanges laid end to end, so a
second unit does not halve the work — it doubles the wait:

| | One unit | Two units |
|---|---|---|
| Round, 16 urban anchors | 509 ms | 1018 ms |
| Fixes per unit per second | 1,96 | 0,98 |
| Rounds attempted over a journey | 179 | 178 |

The last row is the finding. The total number of fixes the network
produces barely moves, because the air was already fully spent; what
changes is how it is divided. Urban HPE at the median went from 3,35 m
with one unit to 5,06 m with two, since each filter now coasts twice as
long between updates. The earlier figure described a network with one
customer.

Both receivers in the bill of materials carry an SX1280 *and* a DWM3000,
which is what lets one unit range against town anchors on the road and
tunnel anchors inside a bore without changing. A unit ranges against
every anchor it shares a waveform with and ignores the rest — so a unit
carrying only the spread module simply does not see the tunnel anchors.
ADR-0014 records all of this.

## What the exchange adds on top

A range is not read off a link budget. Two radios trade frames, and at
SF10 a frame lasts 15,8 ms. In single-sided ranging the difference
between the two clocks multiplies that whole reply delay:

| Clock offset | Single-sided error | Double-sided error |
|---|---|---|
| 10 ppm, uncorrected | 24,1 m | 0,3 mm |
| 0,0793 ppm, measured after correction | 0,19 m | 0,003 mm |

Twenty-four metres is eight times the largest error ever measured on the
part, so the published measurements are themselves evidence that the
frequency-offset estimate every receiver already makes is doing the
ranging work too. Without it, ranging on this radio does not function.

**That residual has been measured**, and it is the one figure in this
project that is no longer a guess. `matlab/yerkon_clock_residual.m` puts
it at **0,0793 ppm** — six times better than the 0,5 that stood in for
it (ADR-0018).

The measurement also says what limits it, which the guess could not. The
residual barely improves with signal: 30 dB more buys a factor of two,
where noise-limited would buy thirty. Run with no noise at all the same
estimator gives 0,0164–0,0643 ppm depending only on where the peak falls
between FFT bins, matching the measured plateau to four decimals. **The
floor is the peak interpolator, not the channel** — which means it does
not average down over repeated exchanges, and a finer interpolator would
lower it.

One design decision changed with it. At 0,5 ppm the impulse radio's
single-sided clock term was 10 cm against a 10 cm floor, so double-sided
ranging earned its third frame. Measured, that term is 1,6 cm and the
floor swallows it. **The tunnel deployment is single-sided now**: a third
less air time, 0,72 m at P95 instead of 1,00, and half again as many
fixes.

It models no phase noise, no multipath and no drift during the exchange,
so read it as a floor.

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

## Three errors that are not noise

A filter given enough noisy ranges converges on the truth. Real systems
do not behave that way, because their worst errors are not noise
(ADR-0019).

**A blocked path measures long.** The signal goes over the obstacle and
the range times that detour: `h²/2 · (1/d₁ + 1/d₂)`, which is centimetres
for a gentle rise on a long link and ten metres for a ridge across a
short one. Always positive, so it never averages away.

**A survey error is a property of an installation**, drawn once per
anchor and held. The estimator is told the surveyed position and treats
it as exact.

**A lost packet produces nothing** — interference in a shared band, a
collision, a fade. 2,4 GHz is the same band as wireless networking, which
is why the town figure is 15 % against 5 % on the open road and 0 in a
bore.

The survey error is the one that changed an answer:

| Anchor survey error | Tunnel HPE P50 |
|---|---|
| 0,00 m | 0,24 m |
| 0,05 m | 0,68 m |
| 0,15 m | 1,76 m |
| 0,30 m | 3,14 m |

**You cannot position better than you surveyed the anchors**, and on a
corridor you cannot get within ten times as well — the geometry that
leaves the vertical unobservable amplifies a survey error by about the
same factor. The tunnel's sub-metre figure had been resting on perfectly
known anchors.

The road rows barely moved, which is the same finding from the other
side: a spread radio ranges to about 3 m and 15 cm of survey error
vanishes underneath it. The floor is in every deployment and binds only
where everything else is better than it.

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
