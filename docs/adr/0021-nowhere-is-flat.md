# ADR-0021: nowhere is flat, and a plane is not the neutral choice

## Status

Accepted.

## Context

Two of the three scenarios stood on `flat_terrain`. The urban row was a
perfectly level plane with a clutter figure over it; the tunnel row was a
perfectly level bore. Only the rural row had relief, and it had 40 m of
it over a 3 km wavelength — gentle farmland, chosen because it was a
plausible-sounding number and not because anywhere measured it.

A level plane looks like the neutral, conservative, assumption-free
choice. It is none of those things.

It is **the most favourable ground this model can draw.** The two-ray
term takes a specular reflection off the ground between the terminals,
and over a plane every reflection arrives at exactly the specular angle
the model assumes. Real ground scatters most of that energy elsewhere.
Flat ground is where the two-ray model is most confident and most
generous.

It also removes, by construction, one of the seven errors the
dissection had just been built to measure: the excess path over an
obstruction (ADR-0019, ADR-0020). Over a plane, nothing obstructs
anything, so `excess_path` read exactly 0,00 m in every row — not because
the term is small, but because the terrain could not produce it. On real
Ankara it reads 0,41 m in the country, 0,11 m in town and 0,09 m in the
bore. A model cannot measure a term its own ground forbids, and this one
had been reporting that zero as a finding.

And it makes the vertical geometry degenerate. On a level bore every
anchor and every receiver sits at one height, which is the arrangement
least able to say anything about VPE.

Ankara is not flat. Its centre rises and falls 91 m across three
kilometres. The open country south of it climbs 907 m across twenty — an
order of magnitude more than the figure this project had been using.

## Decision

Fetch Ankara, ship it, and never fall back to a plane.

Three `yerkon fetch` runs are committed inside the package, under
`src/yerkon/site/ankara/`: `kizilay` for the town, `golbasi` for the open
country, `kizilcahamam` for the mountain the tunnel goes through. They
total a megabyte. ADR-0008 already said a cache directory is a
self-contained artefact; this is the first time the project has taken it
at its word, and it means a clone reproduces every number with no
network.

**A tunnel is the exception that proves the rule.** A bore cannot be
built by draping a road over terrain, because it goes through the hill
rather than over it. `bore_terrain` is a straight line between two
portals — and it *slopes*, because every road tunnel is built to a
drainage gradient. The alignment was found by searching the fetched
mountain for a two kilometre line that keeps rock above it the whole way
and falls within the half to three percent a road tunnel is built to.
It keeps between 9 and 156 m of overburden and falls 1,79 %. Those
portal elevations are a mountain's, not a choice.

**Where nothing has been fetched, the fallback is rolling ground, never
a plane.** Its relief and its ridge spacing are in `defaults.toml` as
what they are — measurements off the fetched grids, marked MEASUREMENT
and sourced to the Copernicus fetch — so the fallback is traceable rather
than invented.

`flat_terrain` stays, and its docstring now says what it is: a laboratory
instrument for isolating one variable in a test, not a description of
anywhere. Nothing that ships uses it. The viewer's relief slider no
longer reaches zero, and the viewer gained a ground selector, so real
Ankara is one click away rather than a command-line fetch away.

## Consequences

The table moved, and the rural row moved twice.

Urban went from 1,24 m to 1,64 m at the fiftieth percentile and from
100 % availability to 99,11 %: real ground puts things in the way that a
plane could not.

The tunnel moved the other way, and the reason is the one this ADR is
about. A level bore put every anchor 4 m off the centreline at one height
and every receiver at another — a fixed two-ray geometry repeated the
length of the tunnel, and a fixed geometry can sit in a fixed null.
Sloping the floor 1,79 % varies that geometry along the bore, and the
lost exchanges fell from 37,7 % to 7,8 %, availability from 98,02 % to
100 %. The level model was not conservative there either; it was
differently wrong.

The rural row is the finding, and it took two fetches to read correctly.

Put on the hills at Gölbaşı — 907 m of relief over twenty kilometres —
the row collapsed: 45,28 % availability, two thirds of exchanges lost to
terrain. The first instinct was that the grid was too coarse. It was not:

| Mast spacing | Masts | Availability |
|---|---|---|
| 4000 m | 33 | 45,3 % |
| 3000 m | 49 | 48,3 % |
| 2500 m | 77 | 53,6 % |
| 2000 m | 116 | 57,8 % |
| 1500 m | 189 | 60,8 % |

Five and a half times the capital buys fifteen points. Siting each mast
on the highest ground within 1,5 km buys eight. Neither is a fix, because
neither addresses what is wrong: **an intercity road does not cross a
mountain range on a rectangle**, and neither does the network beside it.
A receiver in a valley cannot see a mast over the ridge above it however
many masts there are.

Roads follow the gentler ground — that is why the towns are there — so
the rural row now stands on the Polatlı plain west of Ankara, 486 m of
relief over the same twenty kilometres, which is the ground an intercity
corridor in this province actually runs through. The same thirty-three
masts at the same four kilometre spacing give **82,3 %** availability
there instead of 45,3 %, with only the ground changed.

Gölbaşı stays fetched and stays in the package. It is the case that says
what this deployment costs in terrain it was not designed for, and that
number belongs in the report rather than in a footnote nobody wrote.

The one thing not fixed: the rural journey is still a rectangle over the
ground rather than a road that follows it. OpenStreetMap was unreachable
from the machine that did these fetches, so no site in the package
carries buildings or road geometry. A real alignment would raise every
rural figure again, and until one is fetched the rural row is
conservative for a reason that is written down rather than assumed.
