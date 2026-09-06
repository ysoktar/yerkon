# Field definitions

The master comparison table's exact columns depend on which methods a
given run actually simulates (a GNSS row and a UWB row do not share the
same field set). Rather than hand-maintain a list that can drift out of
sync with the code, the workbook's `field_catalog` sheet is generated at
build time from the union of real columns across that run's tables (see
`locbench3d/tables/master_fields.py`). This file documents the groups and
naming convention that catalog follows; open `field_catalog` in a
generated workbook (or `output/*/tables/manifest.json` for the raw column
lists) for the literal field list of a specific run.

## Naming convention (prefix -> group)

| Prefix | Group | Source module |
| --- | --- | --- |
| (none: `scenario_id`, `method`, `family`) | identity | `tables.master_row` |
| `scenario_` | method/radio/timing/synchronization configuration | `experiment.schema.ScenarioSpec` |
| `hw_` | hardware provenance | `hardware.profiles.HardwareProfile` |
| `acc_` | axis / horizontal / vertical / 3D accuracy | `metrics.accuracy.AccuracyResult` |
| `rel_` | reliability | `metrics.reliability.ReliabilityResult` |
| `scale_` | network scalability, latency, capacity | `metrics.scalability.ScalabilityResult` |
| `pathm_` | path performance | `metrics.path_metrics.PathMetricsResult` |
| `geom_` | geometry validity | `core.geometry_bounds.GeometryResult` |
| `crlb_` | theoretical bounds | `core.geometry_bounds.CRLBResult` / `methods.tdoa.tdoa_crlb` |
| `feas_` | requirements / feasibility | `feasibility.requirements.FeasibilityResult` |
| `pareto_` | Pareto status | `pareto.pareto.ParetoResult` |
| `evidence_` | provenance / evidence confidence | `core.evidence.EvidenceRecord` |
| `gnss_` | GNSS-specific fields | `gnss.model.GnssFix` |
| `cost_` | cost | `metrics.cost.CostBreakdown` |
| `energy_` | energy | `metrics.energy.EnergyBudget` |
| `range_` (in the range comparison table) | range summary | `metrics.range_comparison.RangeComparisonRow` |
| `env_` (in the environment comparison table) | environment | `environment.environment3d.Environment3D` |

Units are inferred from each field's suffix (`_m` = meters, `_s` =
seconds, `_hz` = hertz, `_probability`/`_rate`/`_fraction` = a value in
[0, 1], and so on - see `tables/master_fields.py` for the full suffix
table) and recorded per field in the generated catalog, so every field has
an explicit unit rather than an implied one.

## Ground truth and coordinate frames

Range-based scenarios operate natively in one local 3D Cartesian frame
(the scenario's own `width_m`/`length_m`/`height_m` box); ground truth is
the simulator's own true path position, which is exact by construction
(it is what was actually solved for). GNSS fixes are stored in WGS84
ellipsoidal lat/lon/alt (`coordinate_frame` field on `GnssFix`);
`gnss.geodesy.lla_to_local_enu` converts a fix into a local ENU frame
against an explicitly supplied reference origin when comparing against
local ground truth - this conversion is never applied silently.

## Missing vs. zero

A field is `None`/blank whenever the underlying computation could not be
performed (zero successful fixes, an unobservable CRLB axis, a
threshold the caller never configured, and so on). It is never replaced
with `0`, since a `0` in an accuracy or reliability field is a real,
distinguishable value (perfect accuracy, zero dropout rate) that must not
be confused with "not computed".

## Raw/child tables (not master-table columns)

Per-point path samples, per-range-bin statistics, per-measurement SX1280
hardware records, and per-fix GNSS logs are kept in their own normalized
tables (`path_comparison`, `range_comparison`, `sx1280_raw_measurements`,
`gnss_comparison`) rather than as master-table columns, per the
requirement not to create one master column per raw observation.

## YAML experiment configuration schema

See `examples/experiment_smoke.yaml` and `examples/experiment_standard.yaml`.

```yaml
template:              # fixed values shared by every scenario in this run
  width_m: 20.0
  length_m: 20.0
  height_m: 6.0
  frame_duration_s: 0.001
  guard_duration_s: 0.0002
  scheduling_model: scheduled   # or "aloha"
  hardware_profile: null         # or e.g. "Semtech SX1280"
  nlos_probability: 0.1
  nlos_bias_m: 0.5
  timing_uncertainty_m: 0.15
  # ... any other ScenarioTemplate field (see experiment/schema.py)

variables:              # dimensions to sweep; Cartesian product of all lists
  method: ["UWB_SS_TWR", "TDOA"]
  anchor_count: [4, 5, 8]
  tag_count: [1, 10]
  update_rate_hz: [1.0, 5.0]

n_repeats: 20            # Monte Carlo repeats per scenario
seed: 0
range_bin_edges_m: [0, 5, 10, 20, 30, 50]

hard_requirements:       # optional; omit for no feasibility/Pareto columns
  max_3d_p95_m: 3.0
  min_availability: 0.8

gnss_log_path: examples/gnss_sample_log.csv   # optional
```
