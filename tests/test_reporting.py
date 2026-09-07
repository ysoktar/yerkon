"""Output writing (CSV + manifest) and static/narrative workbook sheets."""
import json

import pandas as pd

from locbench3d.benchmark.runner import run_benchmark
from locbench3d.experiment.generator import ExperimentDesign
from locbench3d.experiment.schema import ScenarioTemplate
from locbench3d.reporting import build_static_tables, write_outputs


def _design():
    return ExperimentDesign(
        template=ScenarioTemplate(
            width_m=10.0, length_m=10.0, height_m=4.0,
            frame_duration_s=0.001, guard_duration_s=0.0002,
        ),
        variables={"method": ["UWB_SS_TWR"], "anchor_count": [5], "tag_count": [1], "update_rate_hz": [1.0]},
    )


def test_write_outputs_reports_a_locked_csv_file_cleanly(tmp_path, monkeypatch):
    """Same failure mode as a locked workbook: a CSV open in Excel on
    Windows raises PermissionError from df.to_csv. Must become an
    actionable message, not an opaque pandas/OS traceback."""
    import pandas.core.generic as pd_generic

    def _raise_permission_error(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(pd_generic.NDFrame, "to_csv", _raise_permission_error)

    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    try:
        write_outputs(outputs, str(tmp_path))
        assert False, "expected a PermissionError"
    except PermissionError as exc:
        message = str(exc)
        assert "open" in message.lower()
        assert "excel" in message.lower() or "another program" in message.lower()


def test_write_outputs_creates_csv_files_and_manifest(tmp_path):
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    table_paths, tables = write_outputs(outputs, str(tmp_path))
    assert (tmp_path / "master_comparison.csv").exists()
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert "master_comparison" in manifest
    assert manifest["master_comparison"]["row_count"] == len(outputs.master_rows)


def test_write_outputs_returns_dataframes_matching_csvs(tmp_path):
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    table_paths, tables = write_outputs(outputs, str(tmp_path))
    df_from_csv = pd.read_csv(table_paths["master_comparison"])
    assert len(df_from_csv) == len(tables["master_comparison"])


def test_energy_and_cost_tables_are_genuinely_empty_when_not_configured(tmp_path):
    """A rollup with no matching prefix columns must not look populated
    with nothing but identity columns; it must be truly empty."""
    outputs = run_benchmark(_design(), n_repeats=5, seed=0, range_bin_edges_m=[0, 5, 10, 20])
    _, tables = write_outputs(outputs, str(tmp_path))
    assert tables["energy"].empty
    assert tables["cost"].empty


def test_build_static_tables_includes_hardware_and_method_catalog():
    tables = build_static_tables()
    assert "hardware_profiles" in tables
    assert "method_catalog" in tables
    assert len(tables["hardware_profiles"]) >= 6
