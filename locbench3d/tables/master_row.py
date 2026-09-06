"""Master comparison row builders.

One row represents one technology + method + hardware + configuration +
environment + evidence condition, per the requirements. Radio/range-based
scenarios and GNSS fixes produce rows with disjoint prefixed field sets
(``acc_``/``rel_``/``scale_``/... vs ``gnss_``) so a GNSS row is never
mistaken for carrying range-based accuracy fields computed the same way,
and vice versa; both share the same identity/evidence field names so they
still line up in one sheet.
"""
from __future__ import annotations

from typing import Optional

from locbench3d.gnss.model import GnssFix
from locbench3d.hardware.profiles import HardwareProfile
from locbench3d.tables.pipeline import ScenarioResult
from locbench3d.tables.serialize import flatten_dataclass


def build_master_row(
    result: ScenarioResult, hardware_profile: Optional[HardwareProfile]
) -> dict:
    row: dict = {
        "scenario_id": result.spec.scenario_id,
        "method": result.spec.method,
        "family": "LOCAL_RADIO",
    }
    row.update(flatten_dataclass(result.spec, prefix="scenario_"))
    if hardware_profile is not None:
        row.update(flatten_dataclass(hardware_profile, prefix="hw_"))
    row.update(flatten_dataclass(result.accuracy, prefix="acc_"))
    row.update(flatten_dataclass(result.reliability, prefix="rel_"))
    row.update(flatten_dataclass(result.scalability, prefix="scale_"))
    row.update(flatten_dataclass(result.path_metrics, prefix="pathm_"))
    row["geom_geometry_valid_fraction"] = result.geometry_valid_fraction
    row.update(flatten_dataclass(result.representative_geometry, prefix="geom_"))
    row.update(flatten_dataclass(result.representative_crlb, prefix="crlb_"))
    row.update(flatten_dataclass(result.error_model_evidence, prefix="evidence_"))
    return row


def build_gnss_master_row(scenario_id: str, fix: GnssFix) -> dict:
    row: dict = {
        "scenario_id": scenario_id,
        "method": "GNSS",
        "family": "GNSS",
    }
    row.update(flatten_dataclass(fix, prefix="gnss_"))
    return row
