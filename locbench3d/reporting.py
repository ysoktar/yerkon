"""Writing benchmark outputs to disk and building the workbook's static sheets.

``write_outputs`` writes one CSV per result table plus a manifest mapping
table name to its file, row count, and columns; ``build_static_tables``
and ``build_narrative_sheets`` build the reference/documentation sheets
that do not depend on a specific benchmark run.
"""
from __future__ import annotations

import json
import os

import pandas as pd

from locbench3d.benchmark.runner import BenchmarkOutputs
from locbench3d.hardware.sx1280_published import COMMUNITY_REFERENCES, SOFTWARE_REFERENCES
from locbench3d.tables import builders


def _locked_file_error(path: str, exc: PermissionError) -> PermissionError:
    """A clean, actionable message for the common "file open in Excel" case."""
    return PermissionError(
        f"Could not write '{path}': permission denied. This usually means "
        "the file is currently open in Excel or another program - Windows "
        "locks open files, so close it there and run this again."
    )


def _select_columns(df: pd.DataFrame, id_cols: list[str], prefix: str) -> pd.DataFrame:
    """Roll up a prefix's columns from the master table, plus identity columns.

    Returns an empty DataFrame (not a table of bare identity columns with
    no actual data) when nothing in this run has a column under the given
    prefix, so a truly empty result reads as empty in the workbook rather
    than looking populated with nothing in it.
    """
    if df.empty:
        return pd.DataFrame()
    prefixed = [c for c in df.columns if c.startswith(prefix)]
    if not prefixed:
        return pd.DataFrame()
    cols = [c for c in df.columns if c in id_cols] + prefixed
    return df[cols]


def write_outputs(
    outputs: BenchmarkOutputs,
    out_dir: str,
    extra_tables: dict[str, pd.DataFrame] | None = None,
) -> tuple[dict[str, str], dict[str, pd.DataFrame]]:
    """Write every result table to CSV plus a manifest.

    ``extra_tables`` merges in tables this run produced outside the normal
    ``BenchmarkOutputs`` flow (for example, imported MATLAB UWB waveform
    results); a caller-supplied table with the same name as one built here
    overrides it.
    """
    os.makedirs(out_dir, exist_ok=True)

    tables: dict[str, pd.DataFrame] = {
        "master_comparison": pd.DataFrame(outputs.master_rows),
        "range_comparison": pd.DataFrame(outputs.range_comparison_rows),
        "path_comparison": pd.DataFrame(outputs.path_comparison_rows),
        "geometry_comparison": pd.DataFrame(outputs.geometry_comparison_rows),
        "scalability_comparison": pd.DataFrame(outputs.scalability_comparison_rows),
        "skipped_scenarios": pd.DataFrame(outputs.skipped_scenarios),
        "evidence_record": pd.DataFrame(outputs.evidence_records),
        "environment_comparison": pd.DataFrame(outputs.environment_comparison_rows),
        "volume_comparison": pd.DataFrame(outputs.volume_comparison_rows),
        "channel_comparison": pd.DataFrame(outputs.channel_comparison_rows),
    }
    if outputs.gnss_rows:
        tables["gnss_comparison"] = pd.DataFrame(outputs.gnss_rows)
    if outputs.gnss_summary_row:
        tables["gnss_summary"] = pd.DataFrame([outputs.gnss_summary_row])

    master = tables["master_comparison"]
    tables["accuracy"] = _select_columns(master, ["scenario_id", "method"], "acc_")
    tables["latency"] = _select_columns(
        master, ["scenario_id", "method", "latency_sequential_fix_s"], "scale_frames"
    )
    tables["energy"] = _select_columns(master, ["scenario_id", "method"], "energy_")
    tables["cost"] = _select_columns(master, ["scenario_id", "method"], "cost_")

    if extra_tables:
        tables.update(extra_tables)

    table_paths: dict[str, str] = {}
    manifest: dict[str, dict] = {}
    for name, df in tables.items():
        path = os.path.join(out_dir, f"{name}.csv")
        try:
            df.to_csv(path, index=False)
        except PermissionError as exc:
            raise _locked_file_error(path, exc) from exc
        table_paths[name] = path
        manifest[name] = {
            "csv_path": path,
            "row_count": int(len(df)),
            "columns": list(df.columns),
        }

    manifest_path = os.path.join(out_dir, "manifest.json")
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except PermissionError as exc:
        raise _locked_file_error(manifest_path, exc) from exc

    return table_paths, tables


def _software_refs_table() -> pd.DataFrame:
    rows = []
    for ref in SOFTWARE_REFERENCES:
        rows.append({"kind": "software", **ref.to_dict()})
    for ref in COMMUNITY_REFERENCES:
        rows.append({"kind": "community", **ref.to_dict()})
    return pd.DataFrame(rows)


def build_static_tables() -> dict[str, pd.DataFrame]:
    return {
        "hardware_profiles": builders.build_hardware_profiles_table(),
        "sx1280_published_data": builders.build_sx1280_published_observations_table(),
        "sx1280_calibration_notes": builders.build_sx1280_calibration_notes_table(),
        "method_catalog": builders.build_method_catalog_table(),
        "applicability_matrix": builders.build_applicability_matrix_table(),
        "official_references": builders.build_official_references_table(),
        "sx1280_software_refs": _software_refs_table(),
    }


def build_narrative_sheets(outputs: BenchmarkOutputs, n_repeats: int, seed: int) -> dict[str, list]:
    n_scenarios = len(outputs.scenarios)
    n_run = len(outputs.master_rows)
    n_skipped = len(outputs.skipped_scenarios)
    return {
        "start_here": [
            "3D localization benchmark - start here",
            "",
            "This workbook is generated entirely by the locbench3d Python package.",
            "Run `locbench3d run-all --config <path>` to regenerate it from scratch.",
            "",
            "Sheet guide:",
            "  master_comparison   - one row per simulated scenario, all metric groups",
            "  range_comparison    - accuracy binned by true range, no empty bins",
            "  path_comparison     - per-path length/speed/tracking error",
            "  geometry_comparison - Jacobian rank, CRLB, condition number per scenario",
            "  scalability_comparison - traffic, occupancy, overload, achievable rate",
            "  gnss_comparison     - imported GNSS fixes, when a GNSS log was supplied",
            "  hardware_profiles   - SX1280/SX1281/NiceRF/Ebyte E28 hardware records",
            "  sx1280_published_data - Stuart Robinson's published ranging observations",
            "  skipped_scenarios   - methods with no native simulator, and why",
            "  field_catalog       - every column in this workbook, with unit and category",
            "  definitions / equations / sources - the model this benchmark implements",
            "  dashboard           - run summary",
            "",
            "See docs/LIMITATIONS.md in the project for what this build could not verify",
            "or measure directly (network access, physical hardware).",
        ],
        "experiment_count_preview": [
            "Experiment count preview",
            "",
            f"Scenarios generated: {n_scenarios}",
            f"Scenarios simulated (native simulator available): {n_run}",
            f"Scenarios skipped (sourced evidence needed instead): {n_skipped}",
            f"Monte Carlo repeats per scenario: {n_repeats}",
            f"Random seed: {seed}",
        ],
        "definitions": [
            "Core definitions",
            "",
            "3D position error e_3D = sqrt((x_hat-x)^2 + (y_hat-y)^2 + (z_hat-z)^2)",
            "Horizontal error e_H = sqrt((x_hat-x)^2 + (y_hat-y)^2)",
            "Vertical error e_V = |z_hat - z|",
            "P95/P99 are percentiles of the empirical error distribution, not a",
            "Gaussian-sigma approximation.",
            "CEP50/CEP95 and SEP50/SEP95 here are empirical percentiles of the",
            "horizontal/3D radial error, computed directly from per-fix samples.",
            "See docs/FIELD_DEFINITIONS.md for the full field list and",
            "docs/EQUATIONS.md for every formula this project implements.",
        ],
        "equations": [
            "Key equations implemented by this project (see docs/EQUATIONS.md for all of them)",
            "",
            "r_i = sqrt((x-x_i)^2 + (y-y_i)^2 + (z-z_i)^2)                  true range",
            "Range Jacobian row i = (p - a_i) / r_i                         unit vector",
            "CRLB: FIM = J^T J / sigma^2, cov = FIM^-1, CRLB_axis = sqrt(cov_axis,axis)",
            "TDoA: measurement = r_i - r_ref, shared-reference covariance,",
            "      FIM = J^T Cov^-1 J (never J^T J / sigma^2)",
            "B = f_H - f_L; f_c = (f_H+f_L)/2; fractionalBW = B/f_c; lambda = c/f_c",
            "Resolution heuristic: delta_d ~ c/B (not a positioning accuracy claim)",
            "TOA CRLB: sigma_tau >= 1/sqrt(8 pi^2 beta^2 SNR), sigma_r = c sigma_tau",
            "SS-TWR framesPerFix = 2*N_a; DS-TWR framesPerFix = 3*N_a;",
            "TDoA/TOA/ToF tag-side framesPerFix = 1",
            "Poisson planning approximation: rho_3D = N_a/V, mu = rho_3D*(4/3)*pi*R^3",
        ],
        "sources": [
            "Source scope",
            "",
            "See the official_references, sx1280_published_data, and",
            "sx1280_software_refs sheets for the full list with URLs and scope",
            "notes. Every row in this workbook that comes from a source outside",
            "this project's own simulation carries its evidence_type,",
            "source_name, source_url, and source_scope fields.",
        ],
    }


def build_dashboard_sheet(outputs: BenchmarkOutputs, tables: dict[str, pd.DataFrame]) -> list:
    master = tables.get("master_comparison", pd.DataFrame())
    lines = [
        "Benchmark dashboard",
        "",
        f"Total scenarios generated: {len(outputs.scenarios)}",
        f"Scenarios simulated: {len(outputs.master_rows)}",
        f"Scenarios skipped (no native simulator): {len(outputs.skipped_scenarios)}",
    ]
    if "feas_feasible" in master.columns:
        feasible_count = int((master["feas_feasible"] == True).sum())  # noqa: E712
        lines.append(f"Feasible scenarios (hard requirements met): {feasible_count} / {len(master)}")
    if "pareto_pareto_optimal" in master.columns:
        optimal_count = int((master["pareto_pareto_optimal"] == True).sum())  # noqa: E712
        lines.append(f"Pareto-optimal scenarios: {optimal_count}")
    if "acc_error_3d_rmse_m" in master.columns:
        valid = master["acc_error_3d_rmse_m"].dropna()
        if len(valid):
            lines.append(f"3D RMSE across scenarios: min={valid.min():.3f} m, max={valid.max():.3f} m")
    if outputs.gnss_rows:
        lines.append(f"GNSS fixes imported: {len(outputs.gnss_rows)}")
    return lines
