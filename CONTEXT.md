# YERKON simulation context

This repository estimates what a terrestrial positioning network built from
the YERKON hardware would actually deliver, and what it would cost. Its
single output is the YERKON block of the comparison table on page 15 of the
YERKON report: four rows, ten columns, every number traceable to either a
datasheet, a published measurement, or a stated assumption.

## Glossary

Use these terms exactly. Where a term is ambiguous in the report, this file
picks one meaning and the code follows it.

**Anchor**: a fixed transmitter at a surveyed position. The report calls
these "yayın birimi". Three product variants exist and they are not
interchangeable, because each carries a different radio.

**Receiver**: the moving unit whose position is being estimated. The report
calls these "alıcı". Two product variants: pedestrian and road vehicle.

**Link**: an ordered pair of radios that could exchange a ranging packet at
a given instant. A link either closes or it does not, and the same
calculation that decides this also sets the quality of any measurement it
carries. There is no separate "maximum range" constant anywhere in this
codebase; range is an outcome, not an input. See ADR-0002.

**Observation**: what the receiver's estimator is allowed to see. Never
contains truth. A range observation carries a measured distance, the
anchor's surveyed position, a timestamp and a variance. If a quantity is
not in an Observation, the estimator cannot use it. See ADR-0003.

**Truth**: the simulated physical state. Only the world and the sensor
models may read it. The estimator may not.

**Fix**: one position estimate, with its covariance.

**Deployment**: a set of anchors placed along or across a **Site**, plus
the receiver product used there. This is the thing that has a cost.

**Site**: the physical place: terrain, roads, tunnels, buildings. Roads
have grade, so a receiver's height varies along them. Nothing in this
codebase fixes a road to a constant elevation. See ADR-0004.

**Service area**: the ground area over which a deployment is claimed to
work, in km². It is the ground on which *enough anchors are reachable to
produce a position*, swept over the real terrain rather than drawn as a
corridor strip. This makes the km² denominator mean what it means in the
GNSS rows of the comparison table.

The ground merely *reached* by at least one anchor is a different and much
larger number, and it is reported alongside so the two are never confused:
with anchors every 4 km on 25 m masts, one anchor reaches 392,5 km² and
four reach 15,2 km². See ADR-0012. Cost per route kilometre is reported
alongside as well, for corridor deployments.

**Scenario**: a Deployment plus a set of receiver journeys plus the
evaluation settings. One scenario produces one table row.

**Weighted row**: the fourth table row. It is not a separate simulation. It
combines the raw per-fix error samples of the three scenarios under fixed
weights and recomputes the percentiles from the combined sample. Averaging
three P95 values does not produce a P95, so this codebase does not do that.
See ADR-0005.

## Products

From the report's bill of materials, page 14. Prices are the 100-unit tier
in Turkish lira, dated 6 September 2026.

| Product | Radio | Unit price |
|---|---|---|
| Şehir içi yayın birimi | SX1280 + 2,4 GHz anten | 1366,07 |
| Kırsal yayın birimi | E28-2G4M27S | 1082,68 |
| Kritik bölge yayın birimi | DWM3000 UWB | 1634,44 |
| Yaya alıcısı | SX1280 + DWM3000 + ESP32-S3 + BNO085 | 3117,74 |
| Kara aracı alıcısı | SX1280 + DWM3000 + STM32 + BNO085 | 4002,29 |

Named antennas in the same bill of materials: RF Solutions LAMBDA80-24S and
Inventek W24P-U. These are the stock antennas and the link budget uses their
published gain. No antenna is assumed better than the one in the report.

## What the table columns mean

**HPE, VPE**: horizontal and vertical position error, in metres, at the
stated percentile, over the evaluated journeys.

**Kullanılabilirlik**: the fraction of attempted fixes that produced a valid
position. This measures the modelled failure causes only, which are link
closure, packet loss and solver failure. It is not a service availability
figure and must not be read against the GNSS rows as though it were.

**Alan**: service area as defined above.

**CAPEX**: anchor hardware cost divided by service area. Hardware only. The
report's own scope note lists what is excluded.

**OPEX**: annual running cost per km². The report leaves this empty. This
codebase fills it from a stated inventory of recurring items. See ADR-0006.
