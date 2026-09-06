"""Import MATLAB UWB waveform ranging results.

Reads the CSV schema documented in ``matlab/README.md`` and produced by
``matlab/uwb_waveform_ranging.m``. Every imported record is tagged
``MATLAB_WAVEFORM`` evidence, and its scope note states plainly that the
producing script has never been executed in this project (no MATLAB
license was available) - a caveat that must travel with the data itself,
not live only in a doc file someone might not open.

This project has not run the MATLAB script and ships no real output from
it; the importer is exercised in tests against a synthetic CSV matching
the documented schema.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from typing import IO, Optional

from locbench3d.core.evidence import EvidenceRecord, EvidenceType

MATLAB_UWB_FIELDS: tuple[str, ...] = (
    "measurement_id",
    "true_range_m",
    "estimated_range_m",
    "error_m",
    "bandwidth_hz",
    "center_freq_hz",
    "snr_db",
    "sample_rate_hz",
    "multipath_profile",
    "trial",
    "seed",
)

_REQUIRED_FIELDS = ("true_range_m", "estimated_range_m", "error_m")

_FLOAT_FIELDS = {
    "measurement_id",
    "true_range_m",
    "estimated_range_m",
    "error_m",
    "bandwidth_hz",
    "center_freq_hz",
    "snr_db",
    "sample_rate_hz",
    "trial",
    "seed",
}

_SCOPE_NOTE = (
    "Waveform-level UWB ranging simulation (Gaussian RF pulse, synthetic "
    "multipath channel, AWGN, matched-filter leading-edge detection) run "
    "in MATLAB with Communications Toolbox and Signal Processing Toolbox "
    "(matlab/uwb_waveform_ranging.m). IMPORTANT: the producing script has "
    "never been executed by this project - no MATLAB license or "
    "Communications Toolbox was available in the build environment. It "
    "was reviewed carefully, including a self-calibration step meant to "
    "cancel a possible constant error in its hand-derived delay-alignment "
    "math, but it does not carry the verification every other module in "
    "this project has (a passing pytest suite). See matlab/README.md for "
    "the sanity check to run before trusting any output from it, and "
    "docs/LIMITATIONS.md for the full caveat."
)


@dataclass(frozen=True)
class MatlabUwbWaveformResult:
    measurement_id: Optional[float] = None
    true_range_m: Optional[float] = None
    estimated_range_m: Optional[float] = None
    error_m: Optional[float] = None
    bandwidth_hz: Optional[float] = None
    center_freq_hz: Optional[float] = None
    snr_db: Optional[float] = None
    sample_rate_hz: Optional[float] = None
    multipath_profile: Optional[str] = None
    trial: Optional[float] = None
    seed: Optional[float] = None
    evidence: Optional[EvidenceRecord] = None

    def to_dict(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "evidence"}
        if self.evidence is not None:
            d.update(self.evidence.to_dict())
        return d


def _parse_value(raw: str) -> Optional[float]:
    v = raw.strip()
    if v == "" or v.lower() == "nan":
        return None
    return float(v)


def _parse_row(row: dict[str, str]) -> MatlabUwbWaveformResult:
    kwargs: dict = {}
    for name in MATLAB_UWB_FIELDS:
        raw = row.get(name, "")
        raw = raw.strip() if raw is not None else ""
        if name in _FLOAT_FIELDS:
            kwargs[name] = _parse_value(raw)
        else:
            kwargs[name] = raw or None

    kwargs["evidence"] = EvidenceRecord(
        evidence_type=EvidenceType.MATLAB_WAVEFORM,
        source_name="matlab/uwb_waveform_ranging.m (never executed)",
        source_url="",
        source_scope=_SCOPE_NOTE,
    )
    return MatlabUwbWaveformResult(**kwargs)


def load_matlab_uwb_csv(source: IO[str]) -> list[MatlabUwbWaveformResult]:
    """Load MATLAB UWB waveform ranging results from a CSV file-like object."""
    reader = csv.DictReader(source)
    if reader.fieldnames is None:
        raise ValueError("MATLAB UWB waveform CSV has no header row")
    missing = [c for c in _REQUIRED_FIELDS if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"MATLAB UWB waveform CSV missing required columns: {missing}")
    return [_parse_row(row) for row in reader]


def load_matlab_uwb_csv_path(path: str) -> list[MatlabUwbWaveformResult]:
    with open(path, newline="", encoding="utf-8") as f:
        return load_matlab_uwb_csv(f)
