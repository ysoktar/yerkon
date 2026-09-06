"""GNSS fix schema and log import.

Four things are kept as separate fields on every fix, because collapsing
them loses information the spec explicitly asks to preserve:

* ``constellation_set``: which satellite systems were used (GPS, Galileo,
  GLONASS, BeiDou, QZSS, NavIC, or a multi-GNSS combination expressed as a
  list of more than one).
* ``signal_bands``: which frequency bands were used (free-form strings
  such as "L1", "L5", "E5a"; band naming is constellation-specific and not
  worth forcing into one enum).
* ``positioning_mode``: the configured positioning/correction approach
  (SPP, RTK_FIXED, PPP, HAS, ...).
* ``fix_state``: the actually achieved solution state for this epoch,
  which can differ from the configured mode (e.g. configured for RTK but
  currently floating).

"GPS" and "RTK" are never the same kind of value here: GPS is a member of
``GnssConstellation``, RTK_FIXED is a member of ``PositioningMode``.

Coordinate-frame provenance: position is stored as WGS84 ellipsoidal
lat/lon/alt (``coordinate_frame`` records this explicitly). Conversion to
a local 3D ENU frame for comparison against range-based ground truth is a
separate, explicit step (see ``gnss.geodesy.lla_to_local_enu``), not
performed silently on import.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from enum import Enum
from typing import IO, Optional

from locbench3d.core.evidence import EvidenceRecord, EvidenceType


class GnssConstellation(str, Enum):
    GPS = "GPS"
    GALILEO = "GALILEO"
    GLONASS = "GLONASS"
    BEIDOU = "BEIDOU"
    QZSS = "QZSS"
    NAVIC = "NAVIC"


class PositioningMode(str, Enum):
    SPP = "SPP"
    SINGLE_FREQUENCY = "SINGLE_FREQUENCY"
    DUAL_FREQUENCY = "DUAL_FREQUENCY"
    MULTI_FREQUENCY = "MULTI_FREQUENCY"
    SBAS = "SBAS"
    DGNSS = "DGNSS"
    RTK_FLOAT = "RTK_FLOAT"
    RTK_FIXED = "RTK_FIXED"
    NETWORK_RTK = "NETWORK_RTK"
    PPK = "PPK"
    PPP = "PPP"
    PPP_AR = "PPP_AR"
    HAS = "HAS"
    GNSS_PLUS_INS = "GNSS_PLUS_INS"


class FixState(str, Enum):
    NO_FIX = "NO_FIX"
    STANDALONE = "STANDALONE"
    SBAS = "SBAS"
    DGNSS = "DGNSS"
    RTK_FLOAT = "RTK_FLOAT"
    RTK_FIXED = "RTK_FIXED"
    PPP_FLOAT = "PPP_FLOAT"
    PPP_FIXED = "PPP_FIXED"
    DEAD_RECKONING = "DEAD_RECKONING"


GNSS_FIX_FIELDS: tuple[str, ...] = (
    "timestamp",
    "receiver_hardware",
    "constellation_set",
    "signal_bands",
    "num_frequencies",
    "positioning_mode",
    "correction_source",
    "correction_type",
    "rtk_base_distance_km",
    "correction_age_s",
    "fix_state",
    "satellites_tracked",
    "satellites_used",
    "hdop",
    "vdop",
    "pdop",
    "gdop",
    "cn0_mean_dbhz",
    "cn0_min_dbhz",
    "cn0_max_dbhz",
    "lat_deg",
    "lon_deg",
    "alt_m",
    "horizontal_error_m",
    "vertical_error_m",
    "error_3d_m",
    "velocity_error_m_s",
    "timing_error_s",
    "cold_ttff_s",
    "warm_ttff_s",
    "hot_ttff_s",
    "convergence_time_s",
    "availability",
    "integrity_info",
    "environment_class",
    "receiver_power_w",
    "receiver_cost",
    "correction_service_cost",
)

_FLOAT_FIELDS = {
    "num_frequencies",
    "rtk_base_distance_km",
    "correction_age_s",
    "satellites_tracked",
    "satellites_used",
    "hdop",
    "vdop",
    "pdop",
    "gdop",
    "cn0_mean_dbhz",
    "cn0_min_dbhz",
    "cn0_max_dbhz",
    "lat_deg",
    "lon_deg",
    "alt_m",
    "horizontal_error_m",
    "vertical_error_m",
    "error_3d_m",
    "velocity_error_m_s",
    "timing_error_s",
    "cold_ttff_s",
    "warm_ttff_s",
    "hot_ttff_s",
    "convergence_time_s",
    "availability",
    "receiver_power_w",
    "receiver_cost",
    "correction_service_cost",
}


@dataclass(frozen=True)
class GnssFix:
    timestamp: Optional[str] = None
    receiver_hardware: Optional[str] = None
    constellation_set: list[GnssConstellation] = None  # type: ignore[assignment]
    signal_bands: list[str] = None  # type: ignore[assignment]
    num_frequencies: Optional[float] = None
    positioning_mode: Optional[PositioningMode] = None
    correction_source: Optional[str] = None
    correction_type: Optional[str] = None
    rtk_base_distance_km: Optional[float] = None
    correction_age_s: Optional[float] = None
    fix_state: Optional[FixState] = None
    satellites_tracked: Optional[float] = None
    satellites_used: Optional[float] = None
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    gdop: Optional[float] = None
    cn0_mean_dbhz: Optional[float] = None
    cn0_min_dbhz: Optional[float] = None
    cn0_max_dbhz: Optional[float] = None
    lat_deg: Optional[float] = None
    lon_deg: Optional[float] = None
    alt_m: Optional[float] = None
    coordinate_frame: str = "WGS84_LLA"
    horizontal_error_m: Optional[float] = None
    vertical_error_m: Optional[float] = None
    error_3d_m: Optional[float] = None
    velocity_error_m_s: Optional[float] = None
    timing_error_s: Optional[float] = None
    cold_ttff_s: Optional[float] = None
    warm_ttff_s: Optional[float] = None
    hot_ttff_s: Optional[float] = None
    convergence_time_s: Optional[float] = None
    availability: Optional[float] = None
    integrity_info: Optional[str] = None
    environment_class: Optional[str] = None
    receiver_power_w: Optional[float] = None
    receiver_cost: Optional[float] = None
    correction_service_cost: Optional[float] = None
    evidence: Optional[EvidenceRecord] = None

    def to_dict(self) -> dict:
        d = {}
        for f in fields(self):
            if f.name == "evidence":
                continue
            v = getattr(self, f.name)
            if f.name == "constellation_set" and v is not None:
                v = "|".join(c.value for c in v)
            elif f.name == "positioning_mode" and v is not None:
                v = v.value
            elif f.name == "fix_state" and v is not None:
                v = v.value
            elif f.name == "signal_bands" and v is not None:
                v = "|".join(v)
            d[f.name] = v
        if self.evidence is not None:
            d.update(self.evidence.to_dict())
        return d


def _parse_row(row: dict[str, str]) -> GnssFix:
    kwargs: dict = {}
    for name in GNSS_FIX_FIELDS:
        raw = (row.get(name) or "").strip()
        if raw == "":
            kwargs[name] = None
            continue
        if name == "constellation_set":
            kwargs[name] = [GnssConstellation(v) for v in raw.split("|") if v]
        elif name == "signal_bands":
            kwargs[name] = [v for v in raw.split("|") if v]
        elif name == "positioning_mode":
            kwargs[name] = PositioningMode(raw)
        elif name == "fix_state":
            kwargs[name] = FixState(raw)
        elif name in _FLOAT_FIELDS:
            kwargs[name] = float(raw)
        else:
            kwargs[name] = raw

    if kwargs.get("constellation_set") is None:
        kwargs["constellation_set"] = []
    if kwargs.get("signal_bands") is None:
        kwargs["signal_bands"] = []

    evidence_type_raw = (row.get("evidence_type") or "").strip()
    if evidence_type_raw:
        kwargs["evidence"] = EvidenceRecord(
            evidence_type=EvidenceType(evidence_type_raw),
            source_name=(row.get("source_name") or "").strip() or "unspecified",
            source_url=(row.get("source_url") or "").strip(),
            source_scope=(row.get("source_scope") or "").strip() or "unspecified",
        )

    return GnssFix(**kwargs)


def load_gnss_log_csv(source: IO[str]) -> list[GnssFix]:
    """Load GNSS fixes from this project's CSV log schema.

    This is not a raw NMEA/UBX binary parser; it is the flat CSV schema
    documented in docs/FIELD_DEFINITIONS.md, which a receiver export or a
    conversion script can populate. See docs/LIMITATIONS.md for why this
    project did not implement a binary-protocol parser.
    """
    reader = csv.DictReader(source)
    return [_parse_row(row) for row in reader]


def load_gnss_log_csv_path(path: str) -> list[GnssFix]:
    with open(path, newline="", encoding="utf-8") as f:
        return load_gnss_log_csv(f)
