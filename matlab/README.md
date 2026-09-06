# MATLAB UWB waveform ranging (optional, unverified)

`uwb_waveform_ranging.m` is an optional, standalone MATLAB script that
simulates UWB ranging at the waveform level (Gaussian RF pulse, synthetic
multipath channel, AWGN, matched-filter leading-edge detection) and writes
a results CSV that `locbench3d`'s Python side imports as `MATLAB_WAVEFORM`
evidence - the evidence type this project's requirements specifically
call out as distinct from a hardware measurement, a Monte Carlo
simulation, and an analytic bound.

**This script has never been executed.** No MATLAB license or
Communications Toolbox was available in the environment this project was
built in. It has been reviewed carefully (see the self-calibration design
described in its header comment, which is specifically there to cancel a
possible constant error in a piece of hand-derived delay-alignment math
that could not be checked by running it), but it does not carry the same
guarantee as the rest of this project, where every module has a passing
pytest suite. Read `docs/LIMITATIONS.md` before relying on its output.

## Requirements

- MATLAB with Communications Toolbox (`gauspuls`, `awgn`) and Signal
  Processing Toolbox (`xcorr`).
- No internet access or additional data files needed; everything is
  generated synthetically inside the script.

## Running it

```matlab
run('matlab/uwb_waveform_ranging.m')
```

or from a terminal with MATLAB on PATH:

```bash
matlab -batch "run('matlab/uwb_waveform_ranging.m')"
```

**Before trusting the output**, run the built-in sanity check: edit the
script's `multipath_amplitude` to `[0, 0]` and `snr_db` to something high
like `60`, run it, and confirm `error_m` comes out near zero (well under a
centimeter) at every range. If it does not, the detector has a bug that
needs fixing before the multipath/noise results mean anything - see the
script's header comment for what the calibration step does and does not
protect against.

The script writes `matlab/matlab_uwb_waveform_results.csv` (not committed
to version control - it is regenerated output, like everything under
`output/`).

## Feeding results into locbench3d

```bash
python -m locbench3d.cli run-all \
  --config examples/experiment_standard.yaml \
  --matlab-uwb-csv matlab/matlab_uwb_waveform_results.csv \
  --out output/standard
```

This populates the `matlab_uwb_waveform` sheet in the generated workbook
(and its CSV in `output/standard/tables/`). Without `--matlab-uwb-csv`,
that sheet is left as an empty placeholder, same as before this feature
existed - nothing else in the pipeline changes.

## CSV schema

One row per (true range, trial). Column names are exactly the field names
`writetable` produces from the script's `results` table:

| Column | Meaning | Unit |
| --- | --- | --- |
| `measurement_id` | row counter | - |
| `true_range_m` | configured true one-way range | meters |
| `estimated_range_m` | detector output after calibration | meters |
| `error_m` | `estimated_range_m - true_range_m` | meters |
| `bandwidth_hz` | pulse bandwidth used | hertz |
| `center_freq_hz` | pulse center frequency used | hertz |
| `snr_db` | configured receive SNR | dB |
| `sample_rate_hz` | simulation sample rate | hertz |
| `multipath_profile` | text description of the reflection delays/amplitudes used | - |
| `trial` | repeat index within this true range | - |
| `seed` | RNG seed for this trial | - |

`locbench3d/hardware/matlab_uwb_import.py` reads exactly this schema.
