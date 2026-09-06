"""DataFrame builders for every table the workbook needs.

Each function returns a ``pandas.DataFrame`` built from this project's own
typed records via ``flatten_dataclass``/``to_dict``, so evidence and
provenance fields travel into the table the same way everywhere.
"""
from __future__ import annotations

import dataclasses

import pandas as pd

from locbench3d.core.timing import (
    fractional_bandwidth,
    range_resolution_heuristic_m,
    signal_bandwidth,
    signal_center_frequency,
    wavelength_m,
)
from locbench3d.environment.environment3d import (
    Environment3D,
    anchor_density_3d,
    poisson_expected_anchors_in_range,
)
from locbench3d.hardware.matlab_uwb_import import MatlabUwbWaveformResult
from locbench3d.hardware.profiles import HARDWARE_PROFILE_REGISTRY
from locbench3d.hardware.sx1280_published import (
    ROBINSON_CALIBRATION_NOTES,
    ROBINSON_RANGING_OBSERVATIONS,
)
from locbench3d.methods.catalog import METHOD_CATALOG, applicability_matrix
from locbench3d.references.official_sources import OFFICIAL_SOURCES


def rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_hardware_profiles_table() -> pd.DataFrame:
    rows = [profile.to_dict() | {"profile_key": key} for key, profile in HARDWARE_PROFILE_REGISTRY.items()]
    return rows_to_dataframe(rows)


def build_sx1280_published_observations_table() -> pd.DataFrame:
    rows = []
    for obs in ROBINSON_RANGING_OBSERVATIONS:
        row = {
            "true_range_m": obs.true_range_m,
            "indicated_range_m": obs.indicated_range_m,
            "error_m": obs.error_m,
        }
        row.update(obs.evidence.to_dict())
        rows.append(row)
    return rows_to_dataframe(rows)


def build_sx1280_calibration_notes_table() -> pd.DataFrame:
    rows = []
    for note in ROBINSON_CALIBRATION_NOTES:
        row = {
            "label": note.label,
            "description": note.description,
            "is_verified_ranging_result": note.is_verified_ranging_result,
        }
        row.update(note.evidence.to_dict())
        rows.append(row)
    return rows_to_dataframe(rows)


def build_method_catalog_table() -> pd.DataFrame:
    rows = [dataclasses.asdict(m) for m in METHOD_CATALOG.values()]
    return rows_to_dataframe(rows)


def build_applicability_matrix_table() -> pd.DataFrame:
    matrix = applicability_matrix()
    rows = []
    for method, flags in matrix.items():
        row = {"method": method}
        row.update(flags)
        rows.append(row)
    return rows_to_dataframe(rows)


def build_official_references_table() -> pd.DataFrame:
    rows = []
    for src in OFFICIAL_SOURCES:
        row = {"topic": src.topic, "verified_this_session": src.verified_this_session}
        row.update(src.evidence.to_dict())
        rows.append(row)
    return rows_to_dataframe(rows)


def build_environment_comparison_table(environments: list[Environment3D]) -> pd.DataFrame:
    rows = []
    for env in environments:
        row = dataclasses.asdict(env)
        row["floor_area_m2"] = env.floor_area_m2
        row["volume_m3"] = env.volume_m3
        row["anchors_per_sqm"] = env.anchors_per_sqm
        row["anchors_per_cubic_m"] = env.anchors_per_cubic_m
        rows.append(row)
    return rows_to_dataframe(rows)


def build_volume_comparison_table(entries: list[dict]) -> pd.DataFrame:
    """Poisson-model anchor coverage planning approximation, clearly labeled.

    Each entry needs ``environment_id``, ``anchor_count``, ``volume_m3``,
    ``radius_m``. This is a planning approximation, not a geometry-validity
    result (see docs/EQUATIONS.md).
    """
    rows = []
    for e in entries:
        density = anchor_density_3d(e["anchor_count"], e["volume_m3"])
        expected = poisson_expected_anchors_in_range(density, e["radius_m"])
        rows.append(
            {
                "environment_id": e["environment_id"],
                "anchor_count": e["anchor_count"],
                "volume_m3": e["volume_m3"],
                "radius_m": e["radius_m"],
                "anchor_density_3d_per_m3": density,
                "expected_anchors_in_range": expected,
                "planning_approximation": True,
            }
        )
    return rows_to_dataframe(rows)


def build_channel_comparison_table(entries: list[dict]) -> pd.DataFrame:
    """Bandwidth/center-frequency/wavelength/resolution-heuristic per config.

    Each entry needs ``config_id``, ``f_low_hz``, ``f_high_hz``.
    """
    rows = []
    for e in entries:
        b = signal_bandwidth(e["f_high_hz"], e["f_low_hz"])
        fc = signal_center_frequency(e["f_high_hz"], e["f_low_hz"])
        rows.append(
            {
                "config_id": e["config_id"],
                "f_low_hz": e["f_low_hz"],
                "f_high_hz": e["f_high_hz"],
                "bandwidth_hz": b,
                "center_freq_hz": fc,
                "fractional_bandwidth": fractional_bandwidth(b, fc),
                "wavelength_m": wavelength_m(fc),
                "range_resolution_heuristic_m": range_resolution_heuristic_m(b),
                "resolution_heuristic_note": (
                    "delta_d ~ c/B is a resolution heuristic, not a "
                    "positioning accuracy figure."
                ),
            }
        )
    return rows_to_dataframe(rows)


def build_matlab_uwb_waveform_table(records: list[MatlabUwbWaveformResult]) -> pd.DataFrame:
    """Imported MATLAB UWB waveform ranging results, tagged MATLAB_WAVEFORM.

    Empty when no ``--matlab-uwb-csv`` was supplied to the CLI - this is
    optional evidence, not a required simulation.
    """
    return rows_to_dataframe([r.to_dict() for r in records])
