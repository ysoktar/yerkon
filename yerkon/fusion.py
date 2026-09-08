"""Extended Kalman filter over the receiver's sensors, as the report describes.

The YERKON architecture does not position from radio alone. It fuses
two-way ranges with an inertial unit, wheel odometry and map constraints,
and holds the estimate through gaps. This module is that filter, so the
reported numbers describe the system the report proposes rather than a
stripped-down version of it.

State is position, velocity and the IMU's heading bias,
``[x, y, z, vx, vy, vz, heading_bias]``. The inertial
unit drives the propagation: the filter integrates the acceleration the
IMU reports, corrupted by that unit's noise and bias, rather than assuming
the receiver keeps a constant velocity. That distinction is not cosmetic.
A vehicle rounding a bend at 50 km/h pulls about 0.6 m/s2 sideways, which
is several times any consumer IMU's noise; a constant-velocity filter
falls behind on every corner, its range innovations grow until the outlier
gate rejects them, and it then coasts blind. Four measurement types update
the propagated state: ranges to anchors, wheel speed, IMU heading, and map
height.

The result depends far more on how the range error is modelled than on the
filter itself, and getting that wrong is the easy way to produce a
flattering number:

**Not all range error averages away.** A filter running at 5 Hz sees
hundreds of ranges to the same anchor over a minute. If every error were
independent noise, the average would drive the error towards zero and the
filter would report centimetres from a metre-class radio. Real ranging
error is partly a fixed per-installation offset (antenna delay, mounting,
local multipath geometry) that repeats on every measurement and cannot be
averaged out. The six published SX1280 points cannot separate the two, so
the split is an explicit parameter, ``bias_variance_fraction``, and its
effect is reported rather than buried.

**NLOS is not white either.** An obstruction between a receiver and one
anchor persists while the geometry persists. It is modelled as a
first-order process with a correlation time, not redrawn every epoch.

**Odometry scale error is a bias.** A tyre 2% under its nominal radius
reports 2% short for the whole trip.

**A map is wrong in a fixed way, not a noisy one.** The surveyed height at
a point does not change between one second and the next. Feeding the
constraint as fresh independent noise at every step would let the filter
average hundreds of readings and drive the vertical error far below the
map's own accuracy, which is how a simulation ends up claiming 14 cm of
height from a half-metre map. The map error is therefore drawn once per
pass and held.

**IMU heading error is mostly a slow error too.** The 3.5 degree figure is
not something that averages away in a second, so it is split into a
per-pass bias and a smaller white part. The filter carries that bias as a
seventh state and estimates it, which is what a real receiver does. Left
unestimated, repeated heading updates make the filter confident in a
biased direction and the aiding does more harm than good: measured on the
rural corridor, horizontal P95 went from 22 m to 35 m before the bias
state was added.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from yerkon.path import Track
from yerkon.receiver import ReceiverProfile
from yerkon.simulate import select_anchor_indices, solve_position_3d

#: Share of the ranging error variance treated as a fixed per-anchor
#: offset rather than as noise that averages away. The published SX1280
#: data cannot resolve this, so it is stated, not derived. At 0.0 the
#: filter can average the error to nothing; at 1.0 no amount of filtering
#: helps. docs/FUSION.md shows the sensitivity.
DEFAULT_BIAS_VARIANCE_FRACTION = 0.5

#: Correlation time of an NLOS obstruction, in seconds. An obstruction
#: lasts while the geometry that causes it lasts.
DEFAULT_NLOS_CORRELATION_S = 8.0

#: Innovation gate, in standard deviations. Real receivers reject ranges
#: that disagree wildly with the current estimate; without a gate a single
#: gross NLOS return drags the filter off for several seconds.
DEFAULT_GATE_SIGMA = 4.0

#: Share of the IMU heading error held as a per-pass bias rather than
#: redrawn each step. A heading error that averaged away in a second would
#: make the specification meaningless.
HEADING_BIAS_FRACTION = 0.7

#: White part of the map height constraint, in metres: vehicle body
#: movement on its suspension, which does average out, as opposed to the
#: map's own error, which does not.
MAP_WHITE_NOISE_M = 0.10


@dataclass(frozen=True)
class FusionSettings:
    bias_variance_fraction: float = DEFAULT_BIAS_VARIANCE_FRACTION
    nlos_correlation_s: float = DEFAULT_NLOS_CORRELATION_S
    gate_sigma: float = DEFAULT_GATE_SIGMA
    use_odometry: bool = True
    use_heading: bool = True
    use_map_height: bool = True
    #: Apply the map's lateral constraint as well as its height.
    #:
    #: A road map that knows the surface elevation also knows where the
    #: carriageway runs. On a straight corridor that pins the across-road
    #: coordinate the same way the height constraint pins the vertical, and
    #: it matters for the same reason: a line of anchors along a corridor
    #: barely observes the across-road axis.
    use_map_lateral: bool = True


@dataclass(frozen=True)
class TrackResult:
    """Per-epoch errors along one filtered run."""

    error_horizontal_m: np.ndarray
    error_vertical_m: np.ndarray
    #: Horizontal error split along the two ground axes, signed.
    #:
    #: The magnitude alone hides the shape of the problem in a corridor.
    #: Anchors strung along one line say a lot about how far the receiver
    #: is from that line and little about where it is along it, so the two
    #: axes behave differently and only the split shows it.
    error_x_m: np.ndarray
    error_y_m: np.ndarray
    error_3d_m: np.ndarray
    ranging_epochs: int
    gated_range_fraction: float
    converged_after_s: Optional[float]


def _range_error_split(sigma_total_m: float, bias_fraction: float) -> tuple[float, float]:
    """Split total ranging sigma into a per-anchor bias and white noise."""
    if not 0.0 <= bias_fraction <= 1.0:
        raise ValueError("bias_variance_fraction must be in [0, 1]")
    variance = sigma_total_m**2
    sigma_bias = float(np.sqrt(variance * bias_fraction))
    sigma_white = float(np.sqrt(variance * (1.0 - bias_fraction)))
    return sigma_bias, sigma_white


def run_filter(
    track: Track,
    anchors: np.ndarray,
    receiver: ReceiverProfile,
    sigma_range_m: float,
    common_bias_m: float,
    max_range_m: Optional[float],
    max_anchors_per_fix: Optional[int],
    packet_loss_probability: float,
    nlos_probability: float,
    nlos_bias_m: float,
    seed: int,
    settings: FusionSettings = FusionSettings(),
    minimum_anchors: int = 4,
    solver_anchors: Optional[np.ndarray] = None,
) -> TrackResult:
    """Run one filtered pass along a track and return its per-epoch errors."""
    rng = np.random.default_rng(seed)
    dt = track.dt_s
    n_anchors = len(anchors)
    # Ranges are measured against the true anchor positions; the filter
    # solves and updates against the surveyed ones. Passing the same array
    # for both is the perfect-survey case.
    if solver_anchors is None:
        solver_anchors = anchors
    solver_anchors = np.asarray(solver_anchors, dtype=float)

    sigma_bias, sigma_white = _range_error_split(
        sigma_range_m, settings.bias_variance_fraction
    )
    # Fixed per-anchor offsets, drawn once: this installation's antenna
    # delays and local multipath, not something a longer average removes.
    anchor_bias = rng.normal(0.0, sigma_bias, n_anchors) if sigma_bias > 0 else np.zeros(n_anchors)
    # A common-mode offset sits on every anchor at once: this is what an
    # uncalibrated ranging chain looks like, and unlike the per-anchor
    # spread it cannot be cancelled by good geometry either. It is the one
    # error the per-unit calibration step in the report's architecture
    # removes, so it is what separates the calibrated and raw rows.
    anchor_bias = anchor_bias + common_bias_m

    # NLOS state per anchor, held over a correlation time rather than
    # redrawn every epoch.
    nlos_active = rng.random(n_anchors) < nlos_probability
    switch_probability = dt / max(settings.nlos_correlation_s, dt)

    odometry_scale_bias = 0.0
    if receiver.odometry is not None:
        odometry_scale_bias = rng.normal(0.0, receiver.odometry.scale_error)

    # The IMU's own bias, drawn once: it is a property of the unit, not of
    # the moment, so it does not average away over a drive either.
    accel_bias = (
        rng.normal(0.0, receiver.imu.accel_bias_m_s2, 3)
        if receiver.imu is not None
        else np.zeros(3)
    )

    heading_sigma = (
        np.radians(receiver.imu.heading_error_deg) if receiver.imu is not None else 0.0
    )
    heading_bias = rng.normal(0.0, heading_sigma * np.sqrt(HEADING_BIAS_FRACTION))
    heading_white_sigma = heading_sigma * np.sqrt(1.0 - HEADING_BIAS_FRACTION)

    # The map is wrong by a fixed amount at a given place, so this is drawn
    # once and held for the pass.
    map_bias = 0.0
    if receiver.map_constraint is not None:
        map_bias = rng.normal(0.0, receiver.map_constraint.height_sigma_m)
        lateral_sigma = receiver.map_constraint.lateral_sigma_m
        lateral_bias = (
            rng.normal(0.0, lateral_sigma) if lateral_sigma else 0.0
        )

    ranging_period = max(int(round(receiver.filter_rate_hz / receiver.ranging_rate_hz)), 1)

    truth_positions = track.positions()
    truth_velocities = track.velocities()
    truth_accelerations = track.accelerations()

    state = None
    covariance = None
    accel_noise = receiver.imu.accel_noise_m_s2 if receiver.imu else 1.0

    errors_h: list[float] = []
    errors_x: list[float] = []
    errors_y: list[float] = []
    errors_v: list[float] = []
    errors_3d: list[float] = []
    epoch_times: list[float] = []
    ranging_epochs = 0
    gated = 0
    offered = 0

    for step in range(track.n_steps):
        truth_p = truth_positions[step]
        truth_v = truth_velocities[step]

        # NLOS obstructions come and go on their own timescale.
        flips = rng.random(n_anchors) < switch_probability
        redraw = rng.random(n_anchors) < nlos_probability
        nlos_active = np.where(flips, redraw, nlos_active)

        do_ranging = (step % ranging_period) == 0
        visible = np.empty((0, 3))
        visible_surveyed = np.empty((0, 3))
        visible_index = None
        if do_ranging:
            visible_index = select_anchor_indices(
                truth_p, anchors, max_range_m, max_anchors_per_fix
            )
            if len(visible_index):
                visible = anchors[visible_index]
                visible_surveyed = solver_anchors[visible_index]
            else:
                visible_index = None

        # --- initialisation: a receiver starts from a single-epoch fix ---
        if state is None:
            if not do_ranging or visible_index is None or len(visible_index) < minimum_anchors:
                continue
            measured = _measure_ranges(
                truth_p, visible, visible_index, anchor_bias, nlos_active,
                nlos_bias_m, sigma_white, rng,
            )
            estimate, ok = solve_position_3d(visible_surveyed, measured)
            if not ok:
                continue
            state = np.concatenate(
                [estimate, truth_v + rng.normal(0.0, 1.0, 3), [0.0]]
            )
            covariance = np.diag(
                [25.0, 25.0, 100.0, 4.0, 4.0, 4.0, heading_sigma**2]
            )
            continue

        # --- predict, on what the IMU reports ---
        measured_accel = (
            truth_accelerations[step]
            + accel_bias
            + rng.normal(0.0, accel_noise, 3)
        )
        transition = np.eye(7)
        transition[:3, 3:6] = np.eye(3) * dt
        state = transition @ state
        state[:3] += 0.5 * measured_accel * dt**2
        state[3:6] += measured_accel * dt

        # Process noise covers what the IMU got wrong: its white noise plus
        # the bias it is still carrying.
        q = accel_noise**2 + (receiver.imu.accel_bias_m_s2**2 if receiver.imu else 0.0)
        process = np.zeros((7, 7))
        process[:3, :3] = np.eye(3) * (q * dt**4 / 4.0)
        process[:3, 3:6] = np.eye(3) * (q * dt**3 / 2.0)
        process[3:6, :3] = np.eye(3) * (q * dt**3 / 2.0)
        process[3:6, 3:6] = np.eye(3) * (q * dt**2)
        # The heading bias drifts slowly rather than staying frozen, so the
        # filter never becomes certain enough to stop tracking it.
        process[6, 6] = (heading_sigma * 0.02) ** 2 * dt
        covariance = transition @ covariance @ transition.T + process

        # --- range updates ---
        if do_ranging and visible_index is not None and len(visible_index) >= minimum_anchors:
            ranging_epochs += 1
            measured = _measure_ranges(
                truth_p, visible, visible_index, anchor_bias, nlos_active,
                nlos_bias_m, sigma_white, rng,
            )
            delivered = rng.random(len(visible)) >= packet_loss_probability
            # The filter is told the total spread, including the part it
            # cannot average away, or it would be overconfident.
            r_range = sigma_white**2 + sigma_bias**2 + common_bias_m**2
            for anchor, measurement in zip(
                visible_surveyed[delivered], measured[delivered]
            ):
                offered += 1
                offset = state[:3] - anchor
                predicted = float(np.linalg.norm(offset))
                if predicted < 1e-6:
                    continue
                jacobian = np.zeros(7)
                jacobian[:3] = offset / predicted
                innovation = measurement - predicted
                innovation_var = float(jacobian @ covariance @ jacobian) + r_range
                if innovation**2 > (settings.gate_sigma**2) * innovation_var:
                    gated += 1
                    continue
                state, covariance = _update(
                    state, covariance, jacobian, innovation, innovation_var
                )

        # --- odometry: speed from the wheels ---
        if settings.use_odometry and receiver.odometry is not None:
            true_speed = float(np.linalg.norm(truth_v))
            measured_speed = true_speed * (1.0 + odometry_scale_bias) + rng.normal(
                0.0, receiver.odometry.speed_noise_m_s
            )
            predicted_speed = float(np.linalg.norm(state[3:6]))
            if predicted_speed > 0.1:
                jacobian = np.zeros(7)
                jacobian[3:6] = state[3:6] / predicted_speed
                r_speed = (
                    receiver.odometry.speed_noise_m_s**2
                    + (receiver.odometry.scale_error * max(true_speed, 1.0)) ** 2
                )
                innovation = measured_speed - predicted_speed
                innovation_var = float(jacobian @ covariance @ jacobian) + r_speed
                state, covariance = _update(
                    state, covariance, jacobian, innovation, innovation_var
                )

        # --- heading: which way the IMU says the receiver is pointing ---
        if settings.use_heading and receiver.imu is not None:
            true_speed = float(np.linalg.norm(truth_v[:2]))
            predicted_speed = float(np.linalg.norm(state[3:5]))
            if true_speed > 0.5 and predicted_speed > 0.1:
                true_heading = np.arctan2(truth_v[1], truth_v[0])
                measured_heading = (
                    true_heading + heading_bias + rng.normal(0.0, heading_white_sigma)
                )
                # The measurement is the true heading plus the unit's bias,
                # so the predicted measurement carries the bias state.
                predicted_heading = np.arctan2(state[4], state[3]) + state[6]
                innovation = _wrap_angle(measured_heading - predicted_heading)
                jacobian = np.zeros(7)
                jacobian[3] = -state[4] / predicted_speed**2
                jacobian[4] = state[3] / predicted_speed**2
                jacobian[6] = 1.0
                r_heading = heading_white_sigma**2
                innovation_var = float(jacobian @ covariance @ jacobian) + r_heading
                state, covariance = _update(
                    state, covariance, jacobian, innovation, innovation_var
                )

        # --- map: the surface the receiver is on ---
        if settings.use_map_height and receiver.map_constraint is not None:
            sigma_h = receiver.map_constraint.height_sigma_m
            measured_height = (
                truth_p[2] + map_bias + rng.normal(0.0, MAP_WHITE_NOISE_M)
            )
            jacobian = np.zeros(7)
            jacobian[2] = 1.0
            innovation = measured_height - state[2]
            # The filter is told the map's full accuracy, not just the part
            # it can average away.
            innovation_var = (
                float(jacobian @ covariance @ jacobian)
                + sigma_h**2
                + MAP_WHITE_NOISE_M**2
            )
            state, covariance = _update(
                state, covariance, jacobian, innovation, innovation_var
            )

        # --- map: the carriageway the receiver is on ---
        #
        # Drawn once per pass like the height bias, because a map is wrong
        # in a fixed way rather than a noisy one.
        #
        # The corridor here runs along x, so the across-road axis is y.
        # This is a straight-corridor simplification: on a curving road the
        # constraint acts along the local normal to the centreline, not
        # along a fixed axis, and the filter would need the heading to
        # rotate it. The rural track is straight, so the two coincide.
        lateral_sigma = (
            receiver.map_constraint.lateral_sigma_m
            if receiver.map_constraint is not None
            else None
        )
        if settings.use_map_lateral and lateral_sigma:
            measured_lateral = (
                truth_p[1] + lateral_bias + rng.normal(0.0, MAP_WHITE_NOISE_M)
            )
            jacobian = np.zeros(7)
            jacobian[1] = 1.0
            innovation = measured_lateral - state[1]
            innovation_var = (
                float(jacobian @ covariance @ jacobian)
                + lateral_sigma**2
                + MAP_WHITE_NOISE_M**2
            )
            state, covariance = _update(
                state, covariance, jacobian, innovation, innovation_var
            )

        error = state[:3] - truth_p
        errors_h.append(float(np.hypot(error[0], error[1])))
        errors_x.append(float(error[0]))
        errors_y.append(float(error[1]))
        errors_v.append(float(abs(error[2])))
        errors_3d.append(float(np.linalg.norm(error)))
        epoch_times.append(float(track.t_s[step]))

    if not errors_3d:
        empty = np.array([])
        return TrackResult(empty, empty, empty, empty, empty, 0, 0.0, None)

    return TrackResult(
        error_horizontal_m=np.array(errors_h),
        error_vertical_m=np.array(errors_v),
        error_x_m=np.array(errors_x),
        error_y_m=np.array(errors_y),
        error_3d_m=np.array(errors_3d),
        ranging_epochs=ranging_epochs,
        gated_range_fraction=(gated / offered) if offered else 0.0,
        converged_after_s=_convergence_time(np.array(errors_3d), np.array(epoch_times)),
    )


def _measure_ranges(
    truth_p: np.ndarray,
    visible: np.ndarray,
    visible_index: np.ndarray,
    anchor_bias: np.ndarray,
    nlos_active: np.ndarray,
    nlos_bias_m: float,
    sigma_white: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Ranges as the receiver measures them: truth, plus what does not average."""
    true_ranges = np.linalg.norm(visible - truth_p[None, :], axis=1)
    fixed = anchor_bias[visible_index]
    obstruction = nlos_active[visible_index] * nlos_bias_m
    white = rng.normal(0.0, sigma_white, len(visible)) if sigma_white > 0 else 0.0
    return true_ranges + fixed + obstruction + white


def _update(
    state: np.ndarray,
    covariance: np.ndarray,
    jacobian: np.ndarray,
    innovation: float,
    innovation_var: float,
) -> tuple[np.ndarray, np.ndarray]:
    """One scalar EKF update, applied with the Joseph form for stability."""
    gain = covariance @ jacobian / innovation_var
    state = state + gain * innovation
    factor = np.eye(len(state)) - np.outer(gain, jacobian)
    covariance = (
        factor @ covariance @ factor.T
        + np.outer(gain, gain) * (innovation_var - float(jacobian @ covariance @ jacobian))
    )
    covariance = 0.5 * (covariance + covariance.T)
    return state, covariance


def _wrap_angle(angle: float) -> float:
    return float((angle + np.pi) % (2.0 * np.pi) - np.pi)


def _convergence_time(
    errors: np.ndarray,
    times: np.ndarray,
    threshold_m: float = 10.0,
    hold_s: float = 5.0,
):
    """Time to first settle below a threshold and hold it.

    "Stays below forever" is the wrong test: one ordinary excursion late in
    a run would report the whole run as unconverged. What matters is when
    the startup transient ends, so this asks for a sustained hold instead.
    """
    if errors.size == 0:
        return None
    below = errors < threshold_m
    if not below.any():
        return None
    dt = float(np.median(np.diff(times))) if times.size > 1 else 1.0
    hold_steps = max(int(round(hold_s / dt)), 1)
    for i in range(len(below) - hold_steps + 1):
        if below[i : i + hold_steps].all():
            return float(times[i] - times[0])
    return None
