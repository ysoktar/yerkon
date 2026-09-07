# Release notes

## 0.1.3 - scripts/run.ps1 confirmed working on real Windows

Following up on 0.1.2's underlying-commands confirmation, the same user
ran `.\scripts\run.ps1 -SmokeOnly` directly (the script itself, not its
commands typed one at a time) on the same Windows 11 machine. Result: all
seven phases completed, 269 passed / 1 skipped, and a correctly validated
workbook. No PowerShell-specific issue turned up - parameter binding,
`$LASTEXITCODE` propagation, and execution-policy interaction all worked
as written.

No code changes in this release; `docs/LIMITATIONS.md`, `docs/VALIDATION.md`,
and `README.md` updated to reflect that `run.ps1` itself is now confirmed,
narrowing what remains untested to the full (non-smoke) run on Windows and
other Windows/PowerShell version combinations.

## 0.1.2 - Windows verified on real hardware; a genuine test bug fixed

A user ran this project's underlying commands directly on Windows 11
(PowerShell, Python 3.13, `conda` base environment): venv creation,
dependency install, `pytest -q`, and `run-all --smoke`. Result: 269/270
tests passed, and the smoke benchmark produced a valid workbook end to
end.

- Fixed `tests/test_run_sh_passes_bash_syntax_check`: it assumed
  `shutil.which("bash") is not None` meant bash actually works, which is
  false on Windows when the `bash.exe` WSL-relay stub is on PATH but no
  WSL distro is installed - the test now verifies bash actually runs
  (`bash -c "true"`) before trusting it, and skips otherwise instead of
  failing on an environment condition unrelated to `run.sh`'s syntax.
- `scripts/run.ps1` as a script (invoked directly, not its commands typed
  one at a time) remains unconfirmed - see `docs/LIMITATIONS.md`.

## 0.1.1 - Windows support and optional MATLAB UWB waveform evidence

- Added `scripts/run.ps1`, a PowerShell equivalent of `scripts/run.sh`
  covering the same seven steps (environment prep, tests, config
  validation, smoke benchmark, standard benchmark, output validation,
  printed output locations). Reviewed carefully but not executed on a
  real Windows machine or under any PowerShell interpreter - none was
  available in this environment. See `docs/LIMITATIONS.md`.
- Replaced remaining hardcoded forward-slash path concatenation in the CLI
  (`locbench3d/cli.py`) with `os.path.join`, so output paths are
  constructed correctly on Windows as well as Linux/macOS.
- Added `tests/test_run_scripts.py`: structural checks on both run
  scripts, including a real `bash -n` syntax check for `run.sh`.
- Added an optional MATLAB UWB waveform ranging pipeline:
  `matlab/uwb_waveform_ranging.m` (Gaussian pulse, synthetic multipath,
  AWGN, matched-filter leading-edge detection, self-calibrating against a
  known reference delay), a Python importer
  (`locbench3d/hardware/matlab_uwb_import.py`, fully tested) producing
  `MATLAB_WAVEFORM` evidence, and `--matlab-uwb-csv` on `run`/`run-all`
  populating the new `matlab_uwb_waveform` workbook sheet. This is
  optional and does not change the default workflow; the `.m` script
  itself has never been executed (no MATLAB license was available) - see
  `matlab/README.md` and `docs/LIMITATIONS.md`.

## 0.1.0 - initial release

First release of `locbench3d`, built from scratch (no prior codebase or
workbook existed). Implements the full requirements document: native 3D
positioning, 3D geometry/observability classification, TWR/TDoA/ToA/ToF
comparison with correct protocol traffic scaling, Semtech SX1280 hardware
support (including the SX1280/SX1281 ranging-support distinction and a
flagged provenance conflict between them), Stuart Robinson's published
SX1280 field data, GNSS fix import and comparison, evidence-aware
provenance throughout, a several-hundred-field master comparison table
generated from real result columns, feasibility and Pareto analysis, an
Excel workbook covering every required sheet, and a single-command
end-to-end workflow.

### Highlights

- 253 tests, all passing, written test-first alongside the implementation
  (270 as of 0.1.1).
- Smoke (2 scenarios), standard (96 scenarios), and a larger stress
  configuration (288 scenarios) all validate end to end with zero result
  invariants violated.
- TWR frame-per-fix counts and sequential-fix latency correctly scale with
  anchor count (`2*N_a`/`3*N_a`, not a flat 2-3 frames per multi-anchor
  fix); TDoA uses its own range-difference Jacobian and shared-reference
  covariance rather than reusing absolute-range TWR geometry.
- SX1280 and SX1281 are kept as distinct hardware profiles, with a
  recorded provenance conflict between the shared datasheet's title and
  the current per-part product pages.
- GNSS constellation, signal bands, positioning mode, and fix state are
  kept as separate fields; the workbook never compares "GPS" and "RTK" as
  equivalent categories.
- The Excel workbook is fully pre-computed by Python (no live formulas),
  requires no Microsoft Excel installation to generate, and includes every
  required sheet even when a specific run produced no data for it (with
  an explicit placeholder notice rather than a silently missing sheet).

### Known limitations

See `docs/LIMITATIONS.md` for the full, explicit list. In short: no
physical hardware was available during development (no `MEASURED_HARDWARE`
evidence exists anywhere in this codebase), network access for source
verification was blocked except for two search-confirmed facts, the
`energy`/`cost` workbook sheets are empty by default because
`ScenarioTemplate` has no power/cost configuration fields yet, GNSS import
supports only this project's own CSV schema (not raw NMEA/UBX/RINEX), the
optional MATLAB UWB waveform script has never been executed (no MATLAB
license was available), and `scripts/run.ps1` has never been executed on
a real Windows machine (none was available).

### Compatibility

- Python 3.10+ (developed and tested on 3.11).
- Dependencies: numpy, scipy, pandas, openpyxl, PyYAML, click, pytest (see
  `requirements.txt` for pinned ranges).
- Tested end to end on Linux x86_64 in a container environment, including
  from a clean ZIP extraction.
- `scripts/run.ps1` provides the same single-command workflow for Windows
  PowerShell; not executed on a real Windows machine (see above). The
  underlying CLI has no Windows-specific code path and uses platform-safe
  path construction throughout.
- Not tested on macOS specifically, though `scripts/run.sh` uses only
  POSIX-portable bash/`venv`/`pip` conventions.
- MATLAB (optional, for `matlab/uwb_waveform_ranging.m` only): requires
  Communications Toolbox and Signal Processing Toolbox. Never executed by
  this project (see above); not required to run anything else here.
