# Equations

Every formula below has a corresponding implementation and unit test; the
file/function is named so you can check the two against each other.

## Core 3D model

`core/geometry3d.py`

- True range: `r_i = sqrt((x-x_i)^2 + (y-y_i)^2 + (z-z_i)^2)`
- 3D position error: `e_3D = sqrt((x_hat-x)^2 + (y_hat-y)^2 + (z_hat-z)^2)`
- Horizontal error: `e_H = sqrt((x_hat-x)^2 + (y_hat-y)^2)`
- Vertical error: `e_V = |z_hat - z|`

## Geometry and theoretical bounds

`core/geometry_bounds.py`

- Range Jacobian, row i: `d r_i / d p = (p - a_i) / r_i` (unit vector from
  anchor i to the position).
- Fisher information (absolute range, i.i.d. noise): `FIM = J^T J / sigma^2`.
- CRLB: `cov = FIM^-1`, `CRLB_axis = sqrt(cov[axis, axis])`. An axis is
  reported `None` (not 0) when it is unobservable and its Fisher-information
  row/column is not decoupled from an observable one.
- DOP-like values (unit-weighted covariance `Q = (J^T J)^-1`):
  `HDOP = sqrt(Q_xx + Q_yy)`, `VDOP = sqrt(Q_zz)`, `PDOP = sqrt(HDOP^2 + VDOP^2)`.
- Coplanarity: the third singular value of the centered anchor-position
  matrix is negligible relative to the first.

## TDoA (range-difference geometry)

`methods/tdoa.py` - deliberately separate from the absolute-range module above.

- Measurement: `d_i = r_i - r_ref` (range difference against a reference anchor).
- Jacobian, row i: `u_i - u_ref` (difference of two absolute-range unit
  vectors), one row per non-reference anchor.
- Measurement covariance (shared-reference structure, i.i.d. per-anchor
  noise `sigma`): diagonal `2*sigma^2`, off-diagonal `sigma^2`.
- Fisher information: `FIM = J^T Cov^-1 J` (never the absolute-range
  `J^T J / sigma^2`).

## Timing and bandwidth

`core/timing.py`

- `B = f_H - f_L`
- `f_c = (f_H + f_L) / 2`
- `fractionalBW = B / f_c`
- `lambda = c / f_c`
- Resolution heuristics (not accuracy claims): `delta_t ~ 1/B`, `delta_d ~ c/B`
- RMS bandwidth of a flat rectangular spectrum: `beta = B / sqrt(12)`
- Deterministic-delay AWGN CRLB: `sigma_tau >= 1 / sqrt(8 pi^2 beta^2 SNR)`,
  `sigma_r = c * sigma_tau`
- Clock drift: `delta_t_clock ~ epsilon * delta_T`,
  distance-equivalent: `c * |epsilon| * delta_T`

## Protocol traffic

`protocol/traffic.py`

- SS-TWR: `framesPerFix = 2 * N_a`
- DS-TWR: `framesPerFix = 3 * N_a`
- TDoA (tag-side blink) / one-way ToA / ToF: `framesPerFix = 1`
- Sequential TWR latency: `framesPerFix * (frame_duration + guard_duration)`,
  scaling with anchor count; TDoA/ToA/ToF tag-side latency does not scale
  with anchor count (anchor synchronization/backhaul traffic is a
  separate, not-automatically-included, concern).
- Offered load fraction: `n_tags * update_rate_hz * framesPerFix * (frame + guard)`
- Scheduled occupancy above 1.0 marks a scenario overloaded.
- Pure-ALOHA collision-free probability: `P = exp(-2G)`,
  `G = attempts_per_second * frame_duration`. End-to-end delivery
  multiplies this by `(1 - configured_packet_loss_probability)`.

## Environment and coverage planning

`environment/environment3d.py`

- Anchor density: `rho_3D = N_a / V`
- Poisson planning approximation: `mu = rho_3D * (4/3) * pi * R^3`
  (explicitly labeled a planning approximation, not a geometry-validity result)

## Accuracy metrics

`metrics/accuracy.py`

- Bias: mean signed error per axis.
- RMSE: `sqrt(mean(error^2))`.
- P50/P68/P75/P90/P95/P99: empirical percentiles of the observed error
  distribution, not a Gaussian-sigma approximation.
- CEP50/CEP95, SEP50/SEP95: empirical percentiles of the horizontal/3D
  radial error (this project has per-fix samples, so the direct
  percentile is used rather than a summary-statistic approximation formula).
- Error-ellipsoid volume: `(4/3) * pi * a * b * c`, where `a, b, c` are the
  square roots of the eigenvalues of the empirical 3x3 error covariance
  matrix.

## Reliability

`metrics/reliability.py`

- Rates (`valid_fix_rate`, `dropout_rate`, `solver_failure_rate`) are
  computed over `attempted_fixes`, which includes timeouts and solver
  failures.
- Availability under a threshold: fraction of *attempted* fixes with
  `error_3D <= threshold` (a timeout or solver failure counts as not
  meeting the threshold, it does not drop out of the denominator).

## Energy and cost

`metrics/energy.py`, `metrics/cost.py`

- `total_energy_per_fix = tx + rx + processing + synchronization + idle + sleep`
- `energy_per_valid_fix = total_energy_per_fix / valid_fix_rate`
- Battery life: `capacity_Wh / (active_power_W * duty_cycle + sleep_power_W * (1 - duty_cycle))`,
  so sleep power is always included, never omitted from a long-life estimate.
- `CAPEX = device + anchor + antenna + compute + installation + survey + calibration`
  (recurring OPEX - subscription, maintenance, correction service - is
  reported separately, not folded into CAPEX).

## Pareto analysis

`pareto/pareto.py`

- Record `a` dominates `b` if `a` is at least as good as `b` on every
  objective and strictly better on at least one (each objective converted
  to "smaller is better" internally). Only feasible records participate;
  an infeasible record's `pareto_front_index` is always `None`.
