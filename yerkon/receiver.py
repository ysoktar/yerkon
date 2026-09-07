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

_PEDESTRIAN_MAP_EVIDENCE = assumption(
    "Walking surface height known to 1.5 m (1 sigma)",
    "A pedestrian is not confined to a surveyed carriageway and may be on "
    "a footbridge, a stair or a platform, so the height constraint is much "
    "weaker than a vehicle's and is applied loosely.",
)


def vehicle_receiver() -> ReceiverProfile:
    """The report's road vehicle unit: IMU, CAN wheel odometry, map."""
    return ReceiverProfile(
        key="vehicle",
        display_name="Kara aracı alıcısı (IMU + odometri + harita)",
        imu=ImuSpec(
            heading_error_deg=3.5,
            accel_noise_m_s2=0.08,
            accel_bias_m_s2=0.03,
            evidence=_BNO085_EVIDENCE,
        ),
        odometry=OdometrySpec(
            scale_error=0.02,
            speed_noise_m_s=0.05,
            evidence=_ODOMETRY_EVIDENCE,
        ),
        map_constraint=MapConstraintSpec(
            height_sigma_m=0.5,
            lateral_sigma_m=None,
            evidence=_MAP_EVIDENCE,
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
