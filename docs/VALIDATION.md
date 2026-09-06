# Validation summary

This is what was checked before this release, and how to re-check it
yourself from a clean checkout.

## Automated tests

```
pytest -q
```

270 tests pass, 0 failures, in `tests/` (41 test files covering every
module listed in `docs/ARCHITECTURE.md`). The suite is test-first: the
protocol-traffic, TDoA range-difference, geometry-validity, invariant, and
evidence-provenance rules each have a dedicated regression test written
before or alongside the implementation, not added after the fact to match
whatever the code happened to do.

## Smoke benchmark

```
python -m locbench3d.cli run-all --smoke --out output/smoke
```

2 scenarios (UWB SS-TWR and TDoA, 5 anchors, 10 Monte Carlo repeats each)
run end to end: config validation, simulation, table writing, workbook
build, and output validation all pass with zero invariant violations.
Runtime, including the full test suite from a freshly created virtual
environment: about 30 seconds.

## Standard benchmark

```
python -m locbench3d.cli run-all --config examples/experiment_standard.yaml --out output/standard
```

96 scenarios (UWB SS-TWR/DS-TWR, TDoA, SX1280 ranging in a multilateration
configuration; 4/5/8 anchors; 1/10 tags; 1/5 Hz; with and without the
SX1280 hardware profile; 20 Monte Carlo repeats each) run end to end with
zero invariant violations. The resulting workbook has 38 sheets (34
required plus a few extra dynamic ones this run happened to produce) and
a 382-field `field_catalog`. Runtime: about 27 seconds after the venv and
tests from the smoke run above.

## Larger experiment configuration

```
python -m locbench3d.cli run-all --config examples/experiment_large_stress.yaml --out output/stress
```

288 scenarios (4 methods x 4 anchor counts x 3 tag counts x 3 update rates
x 2 hardware profiles, 8 Monte Carlo repeats each) run end to end with
zero invariant violations in about 33 seconds. This is the check against
the requirement that larger experiment configurations, not just the
standard example, validate.

## Result invariants checked

`locbench3d/validate/invariants.py`, run automatically by
`validate-outputs` (and therefore by `run-all`):

- no duplicate scenario IDs
- valid fixes never exceed attempted fixes
- P95 >= P50 and P99 >= P95 wherever both are present
- rate/fraction/probability/availability columns stay in [0, 1]
  (utilization ratios like airtime/occupancy are explicitly exempted,
  since exceeding 1.0 is exactly what "overloaded" means)
- counts never go negative
- the range comparison table never contains an empty bin
- an overloaded scenario is never simultaneously marked feasible
- TWR frame-per-fix counts match the expected `2*N_a`/`3*N_a` scaling

Additional invariants (TDoA range-difference semantics, TWR sequential
latency scaling, missing-value handling) are pinned by unit tests at the
function level (`tests/test_tdoa.py`, `tests/test_protocol_traffic.py`,
and the `None`-not-zero assertions throughout `tests/test_*_metrics.py`)
rather than re-checked generically over a DataFrame, since they are
properties of a single computation, not a property that can be checked
from table shape alone.

## Workbook validation

`locbench3d/validate/workbook_validate.py`, also run by `validate-outputs`:

- every required sheet (see `workbook/build.py:REQUIRED_SHEET_NAMES`,
  34 sheets) is present
- each dynamic result table's row count and column headers match the
  sheet the workbook actually contains
- every cell is scanned for a literal Excel error token
  (`#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, `#N/A`, `#NULL!`, `#NUM!`)
- the workbook contains no live formulas (checked as a warning, since the
  design is to have none at all - see `docs/ARCHITECTURE.md`)

## What was not (and could not be) tested here

See `docs/LIMITATIONS.md` for the full list: no physical hardware was
available, network access for source verification was blocked except for
two search-confirmed facts, and this project's own test/benchmark runs
were done in one Linux x86_64 container.

## Windows: confirmed on real hardware after release

A user ran the underlying commands directly on Windows 11 (PowerShell,
Python 3.13, `conda` base environment): `python -m venv .venv`,
`Activate.ps1`, `pip install -r requirements.txt`, `pytest -q`, and
`python -m locbench3d.cli run-all --smoke --out output\smoke`. Result:
269/270 tests passed, and the smoke benchmark produced a valid workbook.
The one failure (`test_run_sh_passes_bash_syntax_check`) was a real bug in
the test, not the project: Windows's `bash.exe` WSL-relay stub is found by
`shutil.which` even with no WSL distro installed, then fails at
invocation - fixed by having the test verify bash actually runs before
trusting that it's present.

`scripts/run.ps1` as a script (run via `.\scripts\run.ps1` itself, not its
underlying commands typed one at a time) is still unconfirmed - see
`docs/LIMITATIONS.md` for exactly what that gap covers.

## MATLAB: still fully unconfirmed on the MATLAB side

`matlab/uwb_waveform_ranging.m` itself has never been executed (no MATLAB
license was available), but everything downstream of its documented CSV
output - the Python importer, the workbook sheet it populates, and the
CLI's `--matlab-uwb-csv` wiring - is exercised by
`tests/test_matlab_uwb_import.py` and `tests/test_cli_matlab_uwb.py`
against a synthetic CSV matching that schema, and confirmed end to end
with `python -m locbench3d.cli run-all --smoke --matlab-uwb-csv
<synthetic csv>` producing a correctly populated `matlab_uwb_waveform`
sheet.

## Packaging checks

- `.gitignore` excludes `__pycache__/`, `.pytest_cache/`, `.venv/`,
  `build/`, `dist/`, and `output/` from version control; the release ZIP
  is built from a clean `git archive` (or equivalent), so no virtual
  environment, cache, or previous run's output is packaged.
- `CHECKSUMS.sha256` records the SHA-256 of the release ZIP and the
  example workbook shipped alongside it.
