# Architecture

## Module map

```
locbench3d/
  core/
    evidence.py          Controlled evidence-type vocabulary, EvidenceRecord
    geometry3d.py         Native 3D position/range/error math
    geometry_bounds.py     Jacobian, FIM, CRLB, DOP, coplanarity, convex hull,
                            geometry validity classification
    timing.py              Bandwidth/timing heuristics, deterministic-delay TOA CRLB

  hardware/
    profiles.py             SX1280/SX1281/NiceRF/Ebyte E28 hardware profile registry
    sx1280_published.py     Stuart Robinson's published ranging observations
    sx1280_measurements.py  Raw ranging measurement schema + CSV importer
    sx1280_error_model.py   Hardware-calibrated bootstrap error model
    matlab_uwb_import.py    Importer for matlab/uwb_waveform_ranging.m output
                              (MATLAB_WAVEFORM evidence; see docs/LIMITATIONS.md)

  methods/
    catalog.py       Method definitions, minimum/preferred anchor counts,
                       applicability matrix
    tdoa.py           TDoA range-difference Jacobian, shared-reference
                       covariance, Fisher information, CRLB, geometry

  protocol/
    traffic.py        Frames-per-fix rules, sequential latency, occupancy,
                       ALOHA collision model

  gnss/
    geodesy.py         WGS84 lat/lon/alt <-> local ENU conversion
    model.py            GnssFix schema, CSV log importer

  environment/
    environment3d.py    3D environment variables, Poisson coverage planning approximation

  paths/
    trajectories.py      Every required 3D path generator, plus custom-CSV import

  simulate/
    solver.py             Native 3D nonlinear least-squares solvers (absolute range, TDoA)
    monte_carlo.py         Per-path-sample, per-repeat fix simulation

  metrics/
    accuracy.py, reliability.py, path_metrics.py, range_comparison.py,
    energy.py, cost.py, scalability.py, gnss.py

  experiment/
    schema.py            ScenarioTemplate / ScenarioSpec
    generator.py           Combinatorial scenario generation, count preview, validation
    config_io.py            YAML experiment configuration loading

  feasibility/
    requirements.py        Hard requirements, applicability -> geometry -> requirements
                             decision order

  pareto/
    pareto.py               Multi-objective dominance, front index, optional weighted score

  tables/
    serialize.py            Generic dataclass -> flat dict for table rows
    pipeline.py              One ScenarioSpec -> one ScenarioResult (the integration point)
    master_row.py             Master comparison row builders (radio, GNSS)
    master_fields.py           Field catalog, generated from real row columns
    builders.py                 DataFrame builders for every static/reference table

  references/
    official_sources.py       Official/primary source list with verification status

  benchmark/
    runner.py                 An ExperimentDesign -> every result table (BenchmarkOutputs)

  validate/
    invariants.py             Result invariant checks over real generated tables
    workbook_validate.py        Workbook structural validation

  workbook/
    build.py                    openpyxl workbook construction

  reporting.py                  CSV/manifest writing, static and narrative sheets
  cli.py                         click CLI: validate-config, run, build-workbook,
                                  validate-outputs, run-all
```

## How a scenario runs

1. `experiment.config_io.load_experiment_config` reads a YAML file into an
   `ExperimentDesign` (a `ScenarioTemplate` plus a variable grid) and
   optional `HardRequirements`.
2. `experiment.generator.generate_scenarios` validates the design and
   expands it into one `ScenarioSpec` per combination in the variable grid.
3. `benchmark.runner.run_benchmark` iterates every scenario:
   - Methods without a native simulator (see `methods.catalog`) are
     recorded in `skipped_scenarios` with the reason, not silently dropped.
   - Methods with a simulator go through `tables.pipeline.run_scenario`:
     build a default anchor layout and path, build a range-error sampler
     (hardware-calibrated for SX1280, a configured Gaussian/NLOS-bias
     model otherwise), run `simulate.monte_carlo.simulate_path_fixes`,
     then compute accuracy/reliability/path/scalability metrics and
     representative geometry/CRLB.
   - `tables.master_row.build_master_row` flattens the result into one row.
   - If hard requirements were supplied, `feasibility.requirements` and
     `pareto.pareto` attach feasibility and Pareto columns.
4. `reporting.write_outputs` writes every table to CSV plus a manifest.
5. `reporting.build_static_tables` / `build_narrative_sheets` /
   `build_dashboard_sheet` build the reference and narrative sheets.
6. `workbook.build.build_workbook` assembles the final `.xlsx`.
7. `validate.invariants` and `validate.workbook_validate` check the result.

## Design choices worth knowing about

- **No live spreadsheet formulas.** Every workbook sheet is pre-computed
  by Python. This removes an entire class of formula-recalculation and
  reference-corruption risk, at the cost of the workbook not being
  "live" if you edit an input cell by hand - it is a report, not a
  calculator.
- **Anchor layouts and default paths are simple presets, not optimized.**
  `tables.pipeline.default_anchor_layout` and `default_path` exist so a
  scenario spec (which only fixes environment dimensions, not exact
  anchor/path coordinates) can still run; a real deployment plan should
  supply its own layout.
- **Range-error models are configured, not physically simulated.** Except
  for the SX1280 hardware-calibrated model (built from Stuart Robinson's
  published data), every other method uses a Gaussian/NLOS-bias model
  driven directly by the scenario's own `timing_uncertainty_m`,
  `nlos_probability`, and `nlos_bias_m` fields. This matches the
  requirement not to simulate unnecessary RF/electrical detail, but it
  also means accuracy numbers for methods other than SX1280 are only as
  good as the configured uncertainty, not an independent physical
  prediction.
