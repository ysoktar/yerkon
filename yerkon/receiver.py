"""The three receivers the YERKON report specifies, as error models.

The report does not describe a bare ranging device. It describes a receiver
that fuses radio ranges with an inertial unit, wheel odometry and map
constraints through a Kalman filter, and it names the parts: a BNO085 IMU
in both the pedestrian and vehicle units, a CAN connection to wheel speed
and steering angle in the vehicle unit, and wheel encoders in the IoT unit.

Modelling the radio alone therefore answers a question the report never
asked. This module supplies what the filter in ``yerkon/fusion.py`` needs
to answer the real one: how well does each receiver hold position.

Sensor figures are the manufacturer's where one exists. The BNO085
rotation vector is specified at 2.0 degrees static and 3.5 degrees dynamic
heading error; that dynamic figure is what a moving vehicle sees and is
what is used here. Wheel odometry has no single published figure because
the dominant term is wheel radius scale error, which varies with tyre
pressure, load, wear and temperature, so it is modelled as a slowly
varying scale factor with a stated magnitude.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from yerkon.evidence import EvidenceRecord, EvidenceType, assumption
from yerkon.matlab_import import load_imu_drift

#: Outage length the acceleration noise is fitted at, in seconds. The
#: ranging interval is 0.2 s, so that is the gap the filter actually has to
#: bridge and the one the figure should describe.
DRIFT_FIT_OUTAGE_S = 0.2

#: Fallback acceleration noise, used when no MATLAB characterisation is
#: present. It was this project's guess before one existed, and the
#: measured figure came out roughly half of it.
FALLBACK_ACCEL_NOISE_M_S2 = 0.08

BNO085_URL = "https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf"


@dataclass(frozen=True)
class ImuSpec:
    """Inertial unit, as the filter sees it.

    The BNO085 runs its own fusion and outputs an orientation, so the
    quantity that matters downstream is heading error, not raw gyro noise.
    Acceleration noise still matters: it sets how fast the position
    estimate drifts between range fixes.
    """

    heading_error_deg: float
    accel_noise_m_s2: float
    accel_bias_m_s2: float
    evidence: EvidenceRecord


@dataclass(frozen=True)
class OdometrySpec:
    """Wheel-derived speed.

    ``scale_error`` is the fractional error in distance per wheel
    revolution. It is a slowly varying bias, not noise: a tyre 2% under
    its nominal radius reports 2% short for the whole trip, and averaging
    does not remove it.
    """

    scale_error: float
    speed_noise_m_s: float
    evidence: EvidenceRecord


@dataclass(frozen=True)
class MapConstraintSpec:
    """What a digital map pins down without any radio measurement.

    On a road, height is the strongest constraint available: the surface
    elevation at a given point is surveyed, and a vehicle sits on it. That
    single fact removes most of the vertical error the radio geometry
    cannot resolve, which is why the report's architecture includes it.

    The consequence has to be stated rather than enjoyed quietly: once a
    map height constraint is applied, the vertical figure measures the map,
    not the positioning system.
    """

    height_sigma_m: float
    lateral_sigma_m: Optional[float]
    evidence: EvidenceRecord


@dataclass(frozen=True)
class ReceiverProfile:
    key: str
    display_name: str
    imu: Optional[ImuSpec]
    odometry: Optional[OdometrySpec]
    map_constraint: Optional[MapConstraintSpec]
    ranging_rate_hz: float
    filter_rate_hz: float
    notes: tuple[str, ...] = ()

    @property
    def evidence_records(self) -> tuple[EvidenceRecord, ...]:
        records = []
        for part in (self.imu, self.odometry, self.map_constraint):
            if part is not None:
                records.append(part.evidence)
        return tuple(records)


_BNO085_EVIDENCE = EvidenceRecord(
    evidence_type=EvidenceType.OFFICIAL_SPECIFICATION,
    source_name="BNO085 rotation vector heading accuracy",
    source_url=BNO085_URL,
    source_scope=(
        "Manufacturer specification for the BNO085, the IMU the YERKON "
        "report names: 2.0 degrees static and 3.5 degrees dynamic heading "
        "error for the rotation vector output. The dynamic figure is used "
        "here because the receivers are moving."
    ),
    caveats=(
        "The acceleration noise and bias values used alongside it are this "
        "project's figures for a consumer MEMS unit of this class, not "
        "quoted from the datasheet."
    ),
)

_ODOMETRY_EVIDENCE = assumption(
    "Wheel odometry scale error of 2% and 0.05 m/s speed noise",
    "No single published figure exists: the dominant term is wheel radius "
    "scale error, which varies with tyre pressure, load, wear and "
    "temperature. 2% is a conventional magnitude for an uncalibrated "
    "vehicle and is modelled as a bias that persists for the run rather "
    "than as noise that averages away.",
)

_ENCODER_EVIDENCE = assumption(
    "Wheel encoder scale error of 1% and 0.02 m/s speed noise",
    "A robot wheel encoder on a known wheel in a controlled indoor "
    "environment is better behaved than a road vehicle's tyre, so the "
    "scale error is set lower. Still this project's figure, not a "
    "measurement.",
)

_MAP_EVIDENCE = assumption(
    "Road surface height known to 0.5 m (1 sigma) from a digital map",
    "The YERKON architecture lists map constraints as a fusion input. A "
    "surveyed road centreline carries a surface elevation, and a vehicle "
    "sits on that surface. 0.5 m is this project's figure for the combined "
    "map elevation error and vehicle-height uncertainty; no accuracy "
    "specification for the intended map source was available. Applying "
    "this constraint makes the vertical result a statement about the map "
    "rather than about the radio.",
)

_CORRIDOR_MAP_EVIDENCE = assumption(
    "Carriageway position known to 3.0 m (1 sigma) from a digital map, on a "
    "corridor whose direction is known",
    "The same surveyed centreline that carries a surface elevation also "
    "carries where the carriageway runs. On a corridor that constrains the "
    "across-road coordinate the way the elevation constrains the vertical, "
    "and it matters for the same reason: a line of anchors along a corridor "
    "hardly observes the across-road axis at all. Range is nine times more "
    "sensitive to along-road position than across it in the rural layout. "
    "3.0 m is this project's figure, chosen so the constraint says which "
    "carriageway rather than which lane: at three sigma it spans roughly "
    "the 24 m carriageway the scenario models. A tighter figure would be a "
    "claim about lane-level map matching, which needs more than a map.",
)

_PEDESTRIAN_MAP_EVIDENCE = assumption(
    "Walking surface height known to 1.5 m (1 sigma)",
    "A pedestrian is not confined to a surveyed carriageway and may be on "
    "a footbridge, a stair or a platform, so the height constraint is much "
    "weaker than a vehicle's and is applied loosely.",
)


def measured_accel_noise_m_s2() -> tuple[float, EvidenceRecord]:
    """Acceleration noise from the MATLAB IMU characterisation, if present.

    Free-inertial position error grows as roughly ``sigma * t^2 / 2``, so
    the measured drift at the ranging interval inverts to the noise figure
    the filter should carry. Falls back to this project's earlier guess
    when the export is absent.
    """
    try:
        drift = load_imu_drift()
    except (FileNotFoundError, ValueError):
        return FALLBACK_ACCEL_NOISE_M_S2, assumption(
            "Acceleration noise of {:.2f} m/s^2".format(FALLBACK_ACCEL_NOISE_M_S2),
            "This project's figure for a consumer MEMS unit. No "
            "characterisation of the part was available when it was chosen.",
        )
    sigma = drift.implied_accel_noise_m_s2(DRIFT_FIT_OUTAGE_S)
    return sigma, EvidenceRecord(
        evidence_type=EvidenceType.SIMULATED_MONTE_CARLO,
        source_name="MATLAB imuSensor free-inertial drift characterisation",
        source_scope=(
            "Acceleration noise of {:.3f} m/s^2, inverted from the measured "
            "free-inertial position drift of {:.1f} cm over {:.1f} s. Drift "
            "was produced by MathWorks' imuSensor with noise density, bias "
            "instability and random walk set for a consumer MEMS part, "
            "along the same turning motion the scenario tracks use, and "
            "differenced against an ideal sensor so gravity cancels."
        ).format(
            sigma,
            drift.drift_at(DRIFT_FIT_OUTAGE_S) * 100,
            DRIFT_FIT_OUTAGE_S,
        ),
        caveats=(
            "The sensor parameters fed to imuSensor are this project's "
            "figures for the class of MEMS part inside a BNO085, not the "
            "vendor's Allan-variance numbers, which are not published."
        ),
    )


def vehicle_receiver(lateral_sigma_m: Optional[float] = None) -> ReceiverProfile:
    """The report's road vehicle unit: IMU, CAN wheel odometry, map.

    ``lateral_sigma_m`` switches on the map's across-road constraint. Pass
    it only where the corridor direction is known and fixed, which in this
    project means the rural highway and the tunnel. The city grid has
    streets running both ways and the test track turns, so there is no
    single across-road axis to constrain and the argument does not apply.
    """
    accel_noise, accel_evidence = measured_accel_noise_m_s2()
    return ReceiverProfile(
        key="vehicle" if lateral_sigma_m is None else "vehicle-corridor",
        display_name="Kara aracı alıcısı (IMU + odometri + harita)",
        imu=ImuSpec(
            heading_error_deg=3.5,
            accel_noise_m_s2=accel_noise,
            accel_bias_m_s2=0.03,
            evidence=accel_evidence,
        ),
        odometry=OdometrySpec(
            scale_error=0.02,
            speed_noise_m_s=0.05,
            evidence=_ODOMETRY_EVIDENCE,
        ),
        map_constraint=MapConstraintSpec(
            height_sigma_m=0.5,
            lateral_sigma_m=lateral_sigma_m,
            evidence=(
                _MAP_EVIDENCE if lateral_sigma_m is None
                else _CORRIDOR_MAP_EVIDENCE
            ),
        ),
        ranging_rate_hz=5.0,
        filter_rate_hz=10.0,
        notes=(
            "CAN bus supplies wheel speed and steering angle, per the "
            "report's description of this unit.",
        ),
    )


def pedestrian_receiver() -> ReceiverProfile:
    """The report's handheld unit: IMU, no odometry, weak height constraint."""
    return ReceiverProfile(
        key="pedestrian",
        display_name="Yaya alıcısı (IMU, odometri yok)",
        imu=ImuSpec(
            heading_error_deg=3.5,
            accel_noise_m_s2=0.15,
            accel_bias_m_s2=0.05,
            evidence=_BNO085_EVIDENCE,
        ),
        odometry=None,
        map_constraint=MapConstraintSpec(
            height_sigma_m=1.5,
            lateral_sigma_m=None,
            evidence=_PEDESTRIAN_MAP_EVIDENCE,
        ),
        ranging_rate_hz=5.0,
        filter_rate_hz=10.0,
        notes=(
            "Handheld motion is noisier than a vehicle's and there is no "
            "wheel to measure, so this receiver leans harder on the radio.",
        ),
    )


def iot_receiver() -> ReceiverProfile:
    """The report's robot/IoT unit: wheel encoders and IMU indoors."""
    return ReceiverProfile(
        key="iot",
        display_name="Nesnelerin interneti alıcısı (enkoder + IMU)",
        imu=ImuSpec(
            heading_error_deg=3.5,
            accel_noise_m_s2=0.06,
            accel_bias_m_s2=0.02,
            evidence=_BNO085_EVIDENCE,
        ),
        odometry=OdometrySpec(
            scale_error=0.01,
            speed_noise_m_s=0.02,
            evidence=_ENCODER_EVIDENCE,
        ),
        map_constraint=MapConstraintSpec(
            height_sigma_m=0.3,
            lateral_sigma_m=None,
            evidence=assumption(
                "Floor height known to 0.3 m (1 sigma)",
                "A robot on a known floor of a known building has a "
                "tighter height constraint than a road vehicle. This "
                "project's figure.",
            ),
        ),
        ranging_rate_hz=5.0,
        filter_rate_hz=10.0,
    )


ALL_RECEIVERS = {
    "vehicle": vehicle_receiver,
    "pedestrian": pedestrian_receiver,
    "iot": iot_receiver,
}
