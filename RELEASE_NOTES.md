# Release notes

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

- 253 tests, all passing, written test-first alongside the implementation.
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

### Known limitations in this release

See `docs/LIMITATIONS.md` for the full, explicit list. In short: no
physical hardware was available during development (no `MEASURED_HARDWARE`
evidence exists anywhere in this codebase), network access for source
verification was blocked except for two search-confirmed facts, the
`energy`/`cost` workbook sheets are empty by default because
`ScenarioTemplate` has no power/cost configuration fields yet, and GNSS
import supports only this project's own CSV schema, not raw NMEA/UBX/RINEX
parsing.

### Compatibility

- Python 3.10+ (developed and tested on 3.11).
- Dependencies: numpy, scipy, pandas, openpyxl, PyYAML, click, pytest (see
  `requirements.txt` for pinned ranges).
- Tested on Linux x86_64 in a container environment. Not tested on Windows
  or macOS; `scripts/run.sh` requires bash.
