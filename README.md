# locbench3d - 3D localization benchmark

A test-first Python package that compares 3D localization methods (local
radio ranging, UWB, Semtech SX1280, GNSS, and other imported/sourced
positioning results) under one evidence-aware model. Every result carries
where it came from: measured hardware, a hardware-calibrated model, a
Monte Carlo simulation, a published field test, or a manufacturer
specification are never mixed together as equivalent.

## Quick start

From a clean checkout, one command prepares the environment, runs the
tests, runs the smoke and standard benchmarks, builds the Excel workbook,
and validates the outputs.

**Linux / macOS:**

```bash
./scripts/run.sh
```

**Windows (PowerShell):**

```powershell
.\scripts\run.ps1
```

If Windows blocks the script from running, either run it with the policy
bypassed for that one invocation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```

or allow local scripts once per machine/user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Faster smoke-only run (skips the 96-scenario standard sweep):

```bash
./scripts/run.sh --smoke-only        # Linux/macOS
.\scripts\run.ps1 -SmokeOnly         # Windows
```

Both scripts require Python 3.10+ on PATH (`python3`/`python` on
Linux/macOS, `py` or `python` on Windows) and do the same seven steps in
the same order; `scripts/run.ps1`'s syntax has been checked carefully but
has not been executed on an actual Windows machine (none was available
while building this project - see `docs/LIMITATIONS.md`). If it doesn't
work as expected, running the underlying commands directly (see "Running
it yourself, step by step" below) works identically on any platform.

Neither script requires Microsoft Excel; the workbook is written directly
with `openpyxl`. Outputs land in `output/smoke/` and `output/standard/`:

- `tables/*.csv` - every result table, plus `tables/manifest.json` mapping
  table name to file, row count, and columns
- `workbook.xlsx` - the populated comparison workbook

## What this is

- Native 3D positioning: every solver estimates x, y, and z together in
  one nonlinear system, never a 2D fix with height added afterward.
- A method catalog distinguishing the mathematical minimum anchor count,
  the preferred benchmark anchor count, and whether a method has a native
  simulator here or needs sourced/imported evidence instead.
- TWR (SS/DS), TDoA (range-difference geometry with shared-reference
  covariance, not absolute-range geometry), ToA/ToF, RSSI trilateration,
  and Wi-Fi RTT/FTM via one Monte Carlo engine.
- Semtech SX1280 hardware profiles (SX1280 vs SX1281 kept distinct, with a
  flagged provenance conflict between the shared datasheet title and the
  current per-part product pages), Stuart Robinson's published SX1280
  ranging field data, and a hardware-calibrated bootstrap error model
  built from it.
- GNSS fix import from a CSV log schema, keeping constellation, signal
  bands, positioning mode, and fix state as separate fields.
- Optional MATLAB UWB waveform-level ranging evidence (`matlab/`):
  generate physically grounded UWB ranging errors (Gaussian pulse,
  multipath, AWGN, matched-filter leading-edge detection) in MATLAB and
  import the result as `MATLAB_WAVEFORM` evidence with
  `--matlab-uwb-csv`. Not required to run this project - see
  `matlab/README.md` and `docs/LIMITATIONS.md` (this script has never
  been executed; no MATLAB license was available while building it).
- Protocol traffic modeling where SS-TWR/DS-TWR frame counts and
  sequential-fix latency scale with anchor count (not a fixed 2-3 frames
  per fix), plus ALOHA-style collision modeling and scheduled-occupancy
  overload detection.
- Geometry validity (coplanarity, Jacobian rank, condition number, convex
  hull containment), CRLB, and DOP-like values, distinct from a simple
  anchor-count check.
- Accuracy (axis/horizontal/vertical/3D, with P50-P99 first class),
  reliability, path, range-bin, energy, and cost metrics.
- A feasibility decision order (applicability -> geometry validity -> hard
  requirements) and multi-objective Pareto analysis, so a configuration
  that fails a hard requirement never outranks a feasible one by score.
- A several-hundred-field master comparison table, generated from the
  union of real result columns rather than a hand-maintained list that can
  drift out of sync with the code.
- An Excel workbook with every required sheet always present, built from
  fully pre-computed values (no live formulas), so it needs no formula
  engine to open correctly.

See `docs/LIMITATIONS.md` for what this project could not test, measure,
or verify in the environment it was built in.

## Project layout

```
locbench3d/            the package (see docs/ARCHITECTURE.md)
tests/                 pytest test suite (test-first; run before every commit)
examples/              example experiment configs and a sample GNSS log
matlab/                optional MATLAB UWB waveform script (never executed - see docs/LIMITATIONS.md)
scripts/run.sh         the single command described above (Linux/macOS)
scripts/run.ps1        the same single command, for Windows PowerShell
docs/                  architecture, field definitions, equations, sources, limitations
RELEASE_NOTES.md        what changed in this version
VERSION                 current version string
CHECKSUMS.sha256        checksums for the release artifact
```

## Running it yourself, step by step

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q

python -m locbench3d.cli validate-config examples/experiment_standard.yaml
python -m locbench3d.cli run --config examples/experiment_standard.yaml --out output/standard
python -m locbench3d.cli build-workbook --tables-dir output/standard/tables --out output/standard/workbook.xlsx
python -m locbench3d.cli validate-outputs --tables-dir output/standard/tables --workbook output/standard/workbook.xlsx
```

Or all of it in one call:

```bash
python -m locbench3d.cli run-all --config examples/experiment_standard.yaml --out output/standard
```

## Writing your own experiment

Copy `examples/experiment_standard.yaml`, edit `template` (fixed
environment/protocol parameters) and `variables` (dimensions to sweep -
method, anchor count, tag count, update rate, hardware profile, and any
other `ScenarioTemplate` field), then run `validate-config` before a full
run to check the scenario count and catch configuration errors early.

## Documentation

- `docs/ARCHITECTURE.md` - module map and how a scenario flows through the pipeline
- `docs/FIELD_DEFINITIONS.md` - the master table's field groups, and where to find the generated field catalog
- `docs/EQUATIONS.md` - every formula this project implements
- `docs/SOURCES.md` - official, published, and community sources, with scope and verification status
- `docs/LIMITATIONS.md` - what was not tested, measured, or verified, stated explicitly
- `docs/VALIDATION.md` - what was checked before this release, and how to re-check it yourself
