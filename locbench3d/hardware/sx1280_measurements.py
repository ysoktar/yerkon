"""Raw SX1280 ranging measurement schema and CSV import.

One row represents one ranging attempt, successful or not. Failed attempts
and timeouts are kept, not filtered out, because reliability analysis
needs them (see ``locbench3d.metrics.reliability``).

This project has no physical SX1280 hardware attached in the environment
it was built in. The importer here is exercised in tests and in the
example workbook against:

* Stuart Robinson's published short-range table, mapped into this schema
  with ``evidence_type=PUBLISHED_EXPERIMENT`` (only the fields that table
  actually reports are filled in; everything else is left ``None``), and
* a synthetic example CSV clearly labeled ``SIMULATED_MONTE_CARLO``, used
  only to demonstrate the import pipeline shape.

No row in this project is labeled ``MEASURED_HARDWARE`` unless it came
from an actual hardware log. See docs/LIMITATIONS.md.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from typing import IO, Optional

from locbench3d.core.evidence import EvidenceRecord, EvidenceType

RANGING_MEASUREMENT_FIELDS: tuple[str, ...] = (
    "measurement_id",
    "timestamp",
    "experiment_id",
    "test_id",
    "anchor_id",
    "tag_id",
    "hardware_profile_anchor",
    "hardware_profile_tag",
    "hardware_revision_anchor",
    "hardware_revision_tag",
    "radio_ic_anchor",
    "radio_ic_tag",
    "software_or_driver_identity",
    "firmware_identity",
    "true_range_m",
    "raw_ranging_value",
    "reported_range_m",
    "corrected_range_m",
    "range_error_m",
    "range_error_pct",
    "center_freq_hz",
    "measured_freq_error_hz",
    "bandwidth_hz",
    "spreading_factor",
    "coding_rate",
    "tx_power_dbm",
    "calibration_value",
    "calibration_profile",
    "ranging_rssi_dbm",
    "packet_rssi_dbm",
    "snr_db",
    "los_state",
    "environment",
    "temperature_c",
    "antenna_info",
    "orientation_anchor",
    "orientation_tag",
    "success",
    "timeout",
    "exchange_duration_s",
    "ground_truth_system",
    "ground_truth_uncertainty_m",
    "notes",
)

_FLOAT_FIELDS = {
    "true_range_m",
    "raw_ranging_value",
    "reported_range_m",
    "corrected_range_m",
    "range_error_m",
    "range_error_pct",
    "center_freq_hz",
    "measured_freq_error_hz",
    "bandwidth_hz",
    "tx_power_dbm",
    "calibration_value",
    "ranging_rssi_dbm",
    "packet_rssi_dbm",
    "snr_db",
    "temperature_c",
    "exchange_duration_s",
    "ground_truth_uncertainty_m",
}
_INT_FIELDS = {"spreading_factor"}
_BOOL_FIELDS = {"success", "timeout"}


@dataclass(frozen=True)
class RangingMeasurement:
    measurement_id: Optional[str] = None
    timestamp: Optional[str] = None
    experiment_id: Optional[str] = None
    test_id: Optional[str] = None
    anchor_id: Optional[str] = None
    tag_id: Optional[str] = None
    hardware_profile_anchor: Optional[str] = None
    hardware_profile_tag: Optional[str] = None
    hardware_revision_anchor: Optional[str] = None
    hardware_revision_tag: Optional[str] = None
    radio_ic_anchor: Optional[str] = None
    radio_ic_tag: Optional[str] = None
    software_or_driver_identity: Optional[str] = None
    firmware_identity: Optional[str] = None
    true_range_m: Optional[float] = None
    raw_ranging_value: Optional[float] = None
    reported_range_m: Optional[float] = None
    corrected_range_m: Optional[float] = None
    range_error_m: Optional[float] = None
    range_error_pct: Optional[float] = None
    center_freq_hz: Optional[float] = None
    measured_freq_error_hz: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    spreading_factor: Optional[int] = None
    coding_rate: Optional[str] = None
    tx_power_dbm: Optional[float] = None
    calibration_value: Optional[float] = None
    calibration_profile: Optional[str] = None
    ranging_rssi_dbm: Optional[float] = None
    packet_rssi_dbm: Optional[float] = None
    snr_db: Optional[float] = None
    los_state: Optional[str] = None
    environment: Optional[str] = None
    temperature_c: Optional[float] = None
    antenna_info: Optional[str] = None
    orientation_anchor: Optional[str] = None
    orientation_tag: Optional[str] = None
    success: Optional[bool] = None
    timeout: Optional[bool] = None
    exchange_duration_s: Optional[float] = None
    ground_truth_system: Optional[str] = None
    ground_truth_uncertainty_m: Optional[float] = None
    notes: Optional[str] = None
    evidence: Optional[EvidenceRecord] = None

    def to_dict(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "evidence"}
        if self.evidence is not None:
            d.update(self.evidence.to_dict())
        return d


def _parse_bool(raw: str) -> Optional[bool]:
    v = raw.strip().lower()
    if v == "":
        return None
    if v in ("true", "1", "yes", "y"):
        return True
    if v in ("false", "0", "no", "n"):
        return False
    raise ValueError(f"cannot parse boolean field value {raw!r}")


def _parse_row(row: dict[str, str]) -> RangingMeasurement:
    kwargs: dict = {}
    for name in RANGING_MEASUREMENT_FIELDS:
        raw = row.get(name, "")
        raw = raw.strip() if raw is not None else ""
        if raw == "":
            kwargs[name] = None
            continue
        if name in _BOOL_FIELDS:
            kwargs[name] = _parse_bool(raw)
        elif name in _INT_FIELDS:
            kwargs[name] = int(float(raw))
        elif name in _FLOAT_FIELDS:
            kwargs[name] = float(raw)
        else:
            kwargs[name] = raw

    evidence_type_raw = (row.get("evidence_type") or "").strip()
    if evidence_type_raw:
        kwargs["evidence"] = EvidenceRecord(
            evidence_type=EvidenceType(evidence_type_raw),
            source_name=row.get("source_name", "").strip() or "unspecified",
            source_url=row.get("source_url", "").strip(),
            source_scope=row.get("source_scope", "").strip() or "unspecified",
            retrieved_date=row.get("retrieved_date", "").strip(),
        )

    # Derive range error from reported vs true range only if both are known
    # and the exchange did not fail, and only if the file did not already
    # supply it. Never invent an error value for a failed/timed-out attempt.
    if (
        kwargs.get("range_error_m") is None
        and kwargs.get("true_range_m") is not None
        and kwargs.get("reported_range_m") is not None
    ):
        true_r = kwargs["true_range_m"]
        reported_r = kwargs["reported_range_m"]
        kwargs["range_error_m"] = reported_r - true_r
        if kwargs.get("range_error_pct") is None and true_r != 0:
            kwargs["range_error_pct"] = (reported_r - true_r) / true_r * 100.0

    return RangingMeasurement(**kwargs)


def load_measurements_csv(source: IO[str]) -> list[RangingMeasurement]:
    """Load ranging measurements from a CSV file-like object.

    Every row from the file is kept, including failed/timed-out attempts.
    Any column not recognized as a schema field or evidence column is
    ignored; any recognized field left blank becomes ``None``, never a
    silently invented ``0``.
    """
    reader = csv.DictReader(source)
    return [_parse_row(row) for row in reader]


def load_measurements_csv_path(path: str) -> list[RangingMeasurement]:
    with open(path, newline="", encoding="utf-8") as f:
        return load_measurements_csv(f)
