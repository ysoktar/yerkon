"""Command-line interface for the 3D localization benchmark.

Typical single-command usage (see scripts/run.sh for the full workflow
including environment setup and tests):

    python -m locbench3d.cli run-all --config examples/experiment_standard.yaml --out output
"""
from __future__ import annotations

import sys

import click
import pandas as pd

from locbench3d.benchmark.runner import run_benchmark
from locbench3d.experiment.config_io import load_experiment_config
from locbench3d.experiment.generator import preview_scenario_count, validate_design
from locbench3d.gnss.model import load_gnss_log_csv_path
from locbench3d.reporting import (
    build_dashboard_sheet,
    build_narrative_sheets,
    build_static_tables,
    write_outputs,
)
from locbench3d.tables.master_fields import build_field_catalog
from locbench3d.validate.invariants import check_master_table, check_range_comparison_table
from locbench3d.validate.workbook_validate import validate_workbook
from locbench3d.workbook.build import build_workbook


def _read_csv_safe(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


@click.group()
def main() -> None:
    """3D localization benchmark and comparison system."""


@main.command("validate-config")
@click.argument("config_path")
def validate_config_cmd(config_path: str) -> None:
    """Validate an experiment YAML file and print the scenario count preview."""
    config = load_experiment_config(config_path)
    validate_design(config.design)
    count = preview_scenario_count(config.design)
    click.echo(f"Config OK: {config_path}")
    click.echo(f"Scenario count preview: {count} scenario(s)")
    click.echo(f"Monte Carlo repeats per scenario: {config.n_repeats}")
    click.echo(f"Random seed: {config.seed}")
    if config.hard_requirements is not None:
        click.echo("Hard requirements configured: yes")
    else:
        click.echo("Hard requirements configured: no (feasibility/Pareto columns will be omitted)")


@main.command("run")
@click.option("--config", required=True, help="Path to the experiment YAML file.")
@click.option("--out", default="output", help="Output directory for result tables.")
@click.option("--gnss-log", default=None, help="Optional GNSS CSV log to import.")
def run_cmd(config: str, out: str, gnss_log: str | None) -> None:
    """Run the benchmark and write result tables (CSV + manifest) to --out."""
    cfg = load_experiment_config(config)
    gnss_fixes = None
    log_path = gnss_log or cfg.gnss_log_path
    if log_path:
        gnss_fixes = load_gnss_log_csv_path(log_path)

    click.echo(f"Running {preview_scenario_count(cfg.design)} scenario(s)...")
    outputs = run_benchmark(
        cfg.design,
        n_repeats=cfg.n_repeats,
        seed=cfg.seed,
        range_bin_edges_m=cfg.range_bin_edges_m,
        hard_requirements=cfg.hard_requirements,
        gnss_fixes=gnss_fixes,
    )
    table_paths, tables = write_outputs(outputs, f"{out}/tables")
    click.echo(f"Wrote {len(table_paths)} table(s) to {out}/tables")
    click.echo(f"Simulated: {len(outputs.master_rows)}, skipped: {len(outputs.skipped_scenarios)}")


@main.command("build-workbook")
@click.option("--tables-dir", default="output/tables", help="Directory of CSV tables from `run`.")
@click.option("--out", default="output/workbook.xlsx", help="Output workbook path.")
def build_workbook_cmd(tables_dir: str, out: str) -> None:
    """Build the Excel workbook from previously written CSV tables."""
    import json
    import os

    manifest_path = os.path.join(tables_dir, "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    tables: dict[str, pd.DataFrame] = {}
    for name, entry in manifest.items():
        tables[name] = _read_csv_safe(entry["csv_path"])

    tables.update(build_static_tables())

    all_rows = []
    for df in tables.values():
        if isinstance(df, pd.DataFrame) and not df.empty:
            all_rows.append(df.iloc[0].to_dict())
    tables["field_catalog"] = pd.DataFrame(
        [c.__dict__ for c in build_field_catalog(all_rows)]
    )

    class _FakeOutputs:
        scenarios = list(range(len(tables["master_comparison"])))
        master_rows = tables["master_comparison"].to_dict("records")
        skipped_scenarios = (
            tables["skipped_scenarios"].to_dict("records")
            if "skipped_scenarios" in tables
            else []
        )
        gnss_rows = tables.get("gnss_comparison", pd.DataFrame()).to_dict("records")

    narrative = build_narrative_sheets(_FakeOutputs(), n_repeats=0, seed=0)
    tables.update(narrative)
    tables["dashboard"] = build_dashboard_sheet(_FakeOutputs(), tables)

    build_workbook(tables, out)
    click.echo(f"Wrote workbook to {out}")


@main.command("validate-outputs")
@click.option("--tables-dir", default="output/tables")
@click.option("--workbook", default="output/workbook.xlsx")
def validate_outputs_cmd(tables_dir: str, workbook: str) -> None:
    """Run result-invariant checks and workbook structural validation."""
    import json
    import os

    errors: list[str] = []
    manifest_path = os.path.join(tables_dir, "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    tables = {name: _read_csv_safe(entry["csv_path"]) for name, entry in manifest.items()}

    if not tables["master_comparison"].empty:
        for v in check_master_table(tables["master_comparison"]):
            errors.append(f"[master_comparison] {v.check}: {v.message}")
    if "range_comparison" in tables and not tables["range_comparison"].empty:
        for v in check_range_comparison_table(tables["range_comparison"]):
            errors.append(f"[range_comparison] {v.check}: {v.message}")

    if os.path.exists(workbook):
        report = validate_workbook(workbook)
        errors.extend(report.errors)

    if errors:
        click.echo(f"VALIDATION FAILED: {len(errors)} issue(s)")
        for e in errors:
            click.echo(f"  - {e}")
        sys.exit(1)
    click.echo("Validation passed: no invariant violations, workbook structurally valid.")


@main.command("run-all")
@click.option("--config", default="examples/experiment_standard.yaml")
@click.option("--smoke", is_flag=True, help="Use examples/experiment_smoke.yaml instead of --config.")
@click.option("--out", default="output")
@click.option("--gnss-log", default="examples/gnss_sample_log.csv")
@click.pass_context
def run_all_cmd(ctx: click.Context, config: str, smoke: bool, out: str, gnss_log: str) -> None:
    """Validate config, run the benchmark, write tables, build and validate the workbook."""
    config_path = "examples/experiment_smoke.yaml" if smoke else config
    ctx.invoke(validate_config_cmd, config_path=config_path)
    ctx.invoke(run_cmd, config=config_path, out=out, gnss_log=gnss_log)
    ctx.invoke(build_workbook_cmd, tables_dir=f"{out}/tables", out=f"{out}/workbook.xlsx")
    ctx.invoke(validate_outputs_cmd, tables_dir=f"{out}/tables", workbook=f"{out}/workbook.xlsx")
    click.echo("")
    click.echo("Done. Output locations:")
    click.echo(f"  Tables:   {out}/tables/")
    click.echo(f"  Manifest: {out}/tables/manifest.json")
    click.echo(f"  Workbook: {out}/workbook.xlsx")


if __name__ == "__main__":
    main()
