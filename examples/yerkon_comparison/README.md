# YERKON comparison-table simulation

This folder simulates the three deployment groups described in the TOBB
ETU "YERKON" competition presentation (a terrestrial GNSS-backup
positioning system proposed for T.C. Ulaştırma ve Altyapı Bakanlığı /
UDHAM's "Ulaşan ve Erişen Türkiye 2053" competition), using locbench3d's
core simulation primitives, and renders 4 comparison-table rows from the
results:

| Row | Grup (deck) | Ortam | Donanım |
|---|---|---|---|
| YERKON (Şehir İçi - Kalibreli) | Grup 1 | Dış | SX1280/LoRa TWR, per-unit ranging-offset calibrated |
| YERKON (Şehir İçi - Ham) | Grup 1 | Dış | SX1280/LoRa TWR, uncalibrated |
| YERKON (Kırsal) | Grup 2 | Dış | E28-2G4M27S (SX1280-based) TWR |
| YERKON (Kritik Bölge/Tünel) | Grup 3 | İç + dış | UWB/DWM3000 TWR |

## Run it

```bash
pip install -e .            # from the repo root, if not already installed
pip install matplotlib      # only needed for the table image, not a locbench3d dependency

python examples/yerkon_comparison/simulate_yerkon.py
# -> writes yerkon_rows.csv: just the 4 formatted YERKON rows

python examples/yerkon_comparison/simulate_yerkon.py --json
# -> also prints + writes the full raw metrics as yerkon_results.json

python examples/yerkon_comparison/render_comparison_table.py
# -> writes yerkon_comparison_table.png (10 baseline rows + the 4 YERKON rows)
```

Both `render_comparison_table.py` and the CSV output call
`simulate_yerkon.run_all()` / `format_rows.build_yerkon_rows()` directly, so
the numbers in the CSV and the PNG always match a fresh simulation run -
there is no separate, hand-copied set of numbers to go stale.

## Method

- `simulate_path_fixes` + DS-TWR (YERKON's own design explicitly avoids
  TDoA to sidestep network-wide clock synchronization), 300 repeats per
  scenario, fixed seed (42) for reproducibility.
- Anchor layouts are hand-designed per scenario's real geometry rather than
  using `tables.pipeline.run_scenario`'s default box-corner preset, which
  gives poor vertical geometry (VDOP) for wide/thin coverage areas - a real
  geometric effect (near-coplanar, low anchors), not a library bug.
  - **Şehir İçi**: 200x200 m cell, 8 anchors, pole/building/rooftop mounts
    (8/20/35 m).
  - **Kırsal**: 20 km x 2 km corridor, 5 anchors, tower heights (35-45 m).
  - **Tünel**: 2 km corridor, 12 anchors (matching the deck's own stated
    "10-15 yayın düğümü / koridor" pilot density), alternating wall/ceiling
    mounts.

## Evidence provenance

- SX1280 scenarios (urban, rural) use
  `hardware.sx1280_error_model.build_robinson_calibrated_model`, a
  bootstrap built from Stuart Robinson's published SX1280 ranging
  measurements - the same source the YERKON deck itself cites for its
  "<1 m LOS" claim. Evidence type: `HARDWARE_CALIBRATED_MODEL`.
- The tunnel scenario uses DWM3000 UWB, for which this project has no
  calibrated hardware profile, so a configured Gaussian/NLOS-bias model is
  used instead, parameterized to the deck's own stated target (+/-10 cm
  class error). Evidence type: `SIMULATED_MONTE_CARLO` - not a
  hardware-calibrated claim.

## Caveats

1. **Calibrated vs. raw (Şehir İçi)**: Robinson's raw published SX1280 data
   carries a mean bias of about +2.83 m. The deck's own architecture
   section recommends per-unit ranging-offset calibration, which the
   "Kalibreli" row applies (mean-bias removed from the same real data).
   The "Ham" row shows the same scenario without that step - HPE changes
   little, but VPE nearly doubles (7.05 m -> 12.75 m), since a constant
   range bias is amplified by weak vertical geometry.
2. **Small sample size**: Robinson's dataset has n=6 short-range points;
   the resulting sigma/bias estimates are the only real hardware evidence
   available for SX1280, but should not be over-read as precise.
2. **Kırsal VPE (~233 m)**: a genuine effect of sparse (5-tower), wide-area
   3D geometry with a high condition number - not a simulation artifact.
   YERKON's own map-constrained fusion architecture (known road/terrain
   height) would be expected to suppress this substantially in practice;
   this simulation reports the free-3D geometric result only.
3. **Tünel along-corridor weakness**: increasing density from 6 to 12
   anchors (matching the deck's own pilot spec) improved HPE P50 from
   ~0.77 m to ~0.45 m, but a linear corridor deployment retains a
   comparatively weak along-axis direction regardless of density.
4. **CAPEX is component (BOM) cost only**, from the deck's own bulk
   (100-unit) pricing table - it excludes installation, certification, and
   labor (per the deck's own footnote). Real CAPEX will be higher.
5. **OPEX** is left as "-" for all YERKON rows, consistent with the source
   table's own convention for systems lacking published annual operating
   cost data.
6. All accuracy figures are **single-epoch** fix errors (not
   Kalman-filtered/tracked), matching how the other rows in the source
   table are reported.
