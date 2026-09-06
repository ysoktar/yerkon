"""Stuart Robinson's published SX1280 2.4 GHz ranging field observations.

Primary source:
https://stuartsprojects.github.io/2019/04/26/Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html

Related sources (balloon tracker long-range calibration):
https://stuartsprojects.github.io/2019/10/07/2-4ghz-nicerf-sx1280-lora-balloon-tracker-85km-achieved.html
https://stuartsprojects.github.io/2019/10/08/2-4ghz-nicerf-sx1280-lora-balloon-tracker-update-now-89km-achieved.html
https://stuartsprojects.github.io/2019/10/07/sx1280-fast-LoRa.html

All entries here are ``PUBLISHED_EXPERIMENT`` evidence: one individual's
field tests, not a project measurement and not a manufacturer
specification. Community discussion (GitHub issue) is separately kept as
``COMMUNITY_REFERENCE``, a lower authority level, in
``sx1280_community.py``.

Do not read the ~40 km or ~85 km calibrated results as a general SX1280
accuracy figure: they come from one calibration path, one hardware
configuration, and (for the ~40 km case) one specific radio setting
(SF10, 406 kHz). Short-range accuracy and long-range calibrated accuracy
are kept as separate observation sets for this reason.
"""
from __future__ import annotations

from dataclasses import dataclass

from locbench3d.core.evidence import EvidenceRecord, EvidenceType

_PRIMARY_URL = (
    "https://stuartsprojects.github.io/2019/04/26/"
    "Semtech-SX1280-2-4Ghz-LoRa-ranging-tranceivers.html"
)
_BALLOON_85KM_URL = (
    "https://stuartsprojects.github.io/2019/10/07/"
    "2-4ghz-nicerf-sx1280-lora-balloon-tracker-85km-achieved.html"
)
_BALLOON_89KM_URL = (
    "https://stuartsprojects.github.io/2019/10/08/"
    "2-4ghz-nicerf-sx1280-lora-balloon-tracker-update-now-89km-achieved.html"
)
_FAST_LORA_URL = "https://stuartsprojects.github.io/2019/10/07/sx1280-fast-LoRa.html"

_SHORT_RANGE_SCOPE = (
    "Stuart Robinson's short-range SX1280 ranging field test, published on "
    "his personal engineering blog. Single hobbyist test setup, unstated "
    "exact hardware revision and environment beyond what the blog post "
    "describes. Not a manufacturer specification and not a measurement "
    "taken by this project. Do not extrapolate these six points into a "
    "general SX1280 accuracy curve; they are the only short-range points "
    "this source publishes."
)


@dataclass(frozen=True)
class RobinsonRangingObservation:
    true_range_m: float
    indicated_range_m: float
    error_m: float
    evidence: EvidenceRecord


def _short_range_observation(truth: float, indicated: float, error: float):
    return RobinsonRangingObservation(
        true_range_m=truth,
        indicated_range_m=indicated,
        error_m=error,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 2.4GHz LoRa ranging transceivers",
            source_url=_PRIMARY_URL,
            source_scope=_SHORT_RANGE_SCOPE,
        ),
    )


ROBINSON_RANGING_OBSERVATIONS: list[RobinsonRangingObservation] = [
    _short_range_observation(0.0, 4.4, 4.4),
    _short_range_observation(50.0, 57.6, 7.6),
    _short_range_observation(100.0, 103.0, 3.0),
    _short_range_observation(150.0, 148.0, -2.0),
    _short_range_observation(200.0, 201.0, 1.0),
    _short_range_observation(250.0, 253.0, 3.0),
]


@dataclass(frozen=True)
class RobinsonCalibrationNote:
    """A long-range calibration or communication data point that must not be
    read as a generalized ranging-accuracy result, or in some cases must not
    be read as a ranging result at all."""

    label: str
    description: str
    is_verified_ranging_result: bool
    evidence: EvidenceRecord


_LONG_RANGE_SCOPE_40KM = (
    "One map-derived calibration path (~4.42 km) used to derive a "
    "source-specific raw-to-metres conversion factor, then applied to a "
    "single ~40 km test run at SF10 / 406 kHz. This is one calibrated "
    "result under one configuration, not a validated SX1280 long-range "
    "accuracy model."
)
_LONG_RANGE_SCOPE_85KM = (
    "One GPS-derived separation compared against one ranging result on a "
    "balloon flight. Single flight, single configuration; not a repeated "
    "or statistically characterized result."
)
_LONG_RANGE_SCOPE_89KM = (
    "A later communication reception at longer range than the ranging "
    "results above. This is a link-budget/reception event, not a ranging "
    "measurement, and must not be reported alongside the ranging error "
    "table as if it were a verified position/range accuracy result."
)
_COMM_SCOPE_203KBPS = (
    "A high-data-rate communication link test at 203 kbps and ~4.4 km. "
    "This characterizes communication range/throughput, not ranging "
    "accuracy, and must be kept in a separate category from the ranging "
    "error table."
)

ROBINSON_CALIBRATION_NOTES: list[RobinsonCalibrationNote] = [
    RobinsonCalibrationNote(
        label="4.42 km calibration path, raw value 24515, factor ~0.1803 m/unit",
        description=(
            "Map-derived calibration path of approximately 4.42 km, reported "
            "average raw ranging value 24515 at that distance, giving a "
            "source-specific conversion factor around 0.1803 m per raw unit. "
            "This factor is local to this source's setup and firmware "
            "version at the time and should not be assumed to transfer to a "
            "different SX1280 configuration without re-deriving it."
        ),
        is_verified_ranging_result=True,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 balloon tracker, 85 km achieved",
            source_url=_BALLOON_85KM_URL,
            source_scope=_LONG_RANGE_SCOPE_40KM,
        ),
    ),
    RobinsonCalibrationNote(
        label="~40 km test: 40.650 km map distance vs 40.745 km converted ranging result",
        description=(
            "At SF10 and 406 kHz, one ranging test converted with the "
            "~0.1803 m/unit factor gave 40.745 km against an approximately "
            "40.650 km map-derived distance."
        ),
        is_verified_ranging_result=True,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 balloon tracker, 85 km achieved",
            source_url=_BALLOON_85KM_URL,
            source_scope=_LONG_RANGE_SCOPE_40KM,
        ),
    ),
    RobinsonCalibrationNote(
        label="~85 km flight: 85.325 km GPS-derived vs 85.133 km ranging result",
        description=(
            "Approximately 85.325 km GPS-derived separation compared "
            "against an 85.133 km ranging result during a balloon flight."
        ),
        is_verified_ranging_result=True,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 balloon tracker, 85 km achieved",
            source_url=_BALLOON_85KM_URL,
            source_scope=_LONG_RANGE_SCOPE_85KM,
        ),
    ),
    RobinsonCalibrationNote(
        label="~89.237 km later communication reception (not a ranging result)",
        description=(
            "A later balloon-tracker update reports communication reception "
            "at approximately 89.237 km. This must not be labeled a "
            "verified ranging result; it is a reception/link event."
        ),
        is_verified_ranging_result=False,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 balloon tracker update, 89 km achieved",
            source_url=_BALLOON_89KM_URL,
            source_scope=_LONG_RANGE_SCOPE_89KM,
        ),
    ),
    RobinsonCalibrationNote(
        label="~4.4 km at 203 kbps communication benchmark",
        description=(
            "A fast-LoRa communication throughput benchmark at approximately "
            "4.4 km and 203 kbps. This is a communication benchmark, not a "
            "ranging-accuracy result, and is kept out of the ranging error "
            "table for that reason."
        ),
        is_verified_ranging_result=False,
        evidence=EvidenceRecord(
            evidence_type=EvidenceType.PUBLISHED_EXPERIMENT,
            source_name="Stuart Robinson, SX1280 fast LoRa",
            source_url=_FAST_LORA_URL,
            source_scope=_COMM_SCOPE_203KBPS,
        ),
    ),
]

SOFTWARE_REFERENCES = [
    EvidenceRecord(
        evidence_type=EvidenceType.SOFTWARE_REFERENCE,
        source_name="StuartsProjects/SX1280",
        source_url="https://github.com/StuartsProjects/SX1280",
        source_scope=(
            "Reference driver/example code for SX1280 ranging used in the "
            "author's published tests. Software reference, not a hardware "
            "specification or a project measurement."
        ),
    ),
    EvidenceRecord(
        evidence_type=EvidenceType.SOFTWARE_REFERENCE,
        source_name="StuartsProjects/SX12XX-LoRa",
        source_url="https://github.com/StuartsProjects/SX12XX-LoRa",
        source_scope=(
            "Broader SX12xx driver library covering SX1280 ranging among "
            "other SX12xx parts. Software reference."
        ),
    ),
]

COMMUNITY_REFERENCES = [
    EvidenceRecord(
        evidence_type=EvidenceType.COMMUNITY_REFERENCE,
        source_name="SX12XX-LoRa issue #34 (ranging RSSI / frequency error discussion)",
        source_url="https://github.com/StuartsProjects/SX12XX-LoRa/issues/34",
        source_scope=(
            "Community discussion thread that may justify recording ranging "
            "RSSI and frequency error as measurement fields. Lower authority "
            "than manufacturer documentation or the primary published field "
            "tests above; treated as a hint for what to capture, not as a "
            "numeric result."
        ),
    ),
]
