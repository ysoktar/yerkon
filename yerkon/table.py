"""Turning simulation results into the four comparison-table rows.

Formatting lives here rather than in the renderer so that the CSV and the
image can never disagree: both call :func:`build_rows`, and neither holds
a hand-copied number.

Numbers are formatted Turkish-style, with a comma for the decimal mark and
a dot for thousands, to match the table this output is meant to slot into.
"""
from __future__ import annotations

import csv
from typing import Iterable, Optional, Sequence

from yerkon.scenarios import ScenarioResult

COLUMNS = (
    "Sistem",
    "Teknoloji",
    "Ortam",
    "HPE P50 [m]",
    "HPE P95 [m]",
    "VPE P95 [m]",
    "Kullanılabilirlik",
    "Alan [km²]",
    "CAPEX [TL/km²]",
    "OPEX [TL/km²/yıl]",
)

#: Footnote markers, in the order the rows are produced. The footnote text
#: itself lives in README.md, next to the table it annotates.
FOOTNOTES = ("¹", "²", "³", "⁴")


def fmt_metres(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return "-"
    if value >= 100:
        return "≈ {:,.0f}".format(value).replace(",", ".")
    return "{:.{d}f}".format(value, d=decimals).replace(".", ",")


def fmt_percent(fraction: Optional[float]) -> str:
    if fraction is None:
        return "-"
    return "≈ %{:.1f}".format(fraction * 100).replace(".", ",")


def fmt_lira(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return "≈ {:,.0f}".format(value).replace(",", ".")


def fmt_area(value: float) -> str:
    return "{:.2f}".format(value).replace(".", ",")


def build_rows(results: Sequence[ScenarioResult]) -> list[tuple[str, ...]]:
    """One formatted row per scenario, in :data:`COLUMNS` order.

    OPEX is left as "-" for every row. The presentation gives no annual
    operating cost, and the comparison table already uses "-" for the other
    systems whose operators do not publish one. Putting a guess there would
    be the only invented number in the table.
    """
    rows = []
    for result, marker in zip(results, FOOTNOTES):
        scenario = result.scenario
        rows.append(
            (
                scenario.display_name + marker,
                scenario.technology,
                scenario.environment,
                fmt_metres(result.accuracy.horizontal_p50_m),
                fmt_metres(result.accuracy.horizontal_p95_m),
                fmt_metres(result.accuracy.vertical_p95_m),
                fmt_percent(result.reliability.valid_fix_rate),
                fmt_area(scenario.area_km2),
                fmt_lira(result.capex_per_km2_tl),
                "-",
            )
        )
    return rows


def write_csv(rows: Iterable[tuple[str, ...]], path: str) -> None:
    """Write the rows as UTF-8 with a BOM, so Excel opens Turkish text correctly."""
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def detail_records(results: Sequence[ScenarioResult]) -> list[dict]:
    """Everything behind the four rows, for the JSON output and the docs.

    The table shows nine numbers per system. This shows the rest: the
    geometry that produced them, the failure breakdown behind the
    availability figure, and how far the links ran beyond the range the
    error model was calibrated over.
    """
    records = []
    for result in results:
        scenario = result.scenario
        accuracy = result.accuracy
        reliability = result.reliability
        geometry = result.geometry
        records.append(
            {
                "key": scenario.key,
                "display_name": scenario.display_name,
                "technology": scenario.technology,
                "environment": scenario.environment,
                "evidence_type": scenario.error_model.evidence.evidence_type.value,
                "error_model": scenario.error_model.name,
                "error_model_scope": scenario.error_model.evidence.source_scope,
                "error_model_caveats": scenario.error_model.evidence.caveats,
                "ranging_sigma_m": scenario.error_model.sigma_m(),
                "anchor_groups": [
                    {"label": g.label, "count": g.count, "unit_price_tl": g.unit_price_tl}
                    for g in scenario.groups
                ],
                "anchor_count": scenario.anchor_count,
                "area_km2": scenario.area_km2,
                "corridor_length_km": scenario.corridor_length_km,
                "max_link_range_m": scenario.max_link_range_m,
                "packet_loss_probability": scenario.packet_loss_probability,
                "attempted_fixes": reliability.attempted_fixes,
                "valid_fix_rate": reliability.valid_fix_rate,
                "coverage_gap_rate": reliability.coverage_gap_rate,
                "dropout_rate": reliability.dropout_rate,
                "solver_failure_rate": reliability.solver_failure_rate,
                "hpe_p50_m": accuracy.horizontal_p50_m,
                "hpe_p95_m": accuracy.horizontal_p95_m,
                "hpe_max_m": accuracy.horizontal_max_m,
                "vpe_p50_m": accuracy.vertical_p50_m,
                "vpe_p95_m": accuracy.vertical_p95_m,
                "error_3d_p95_m": accuracy.error_3d_p95_m,
                "availability_by_threshold_m": reliability.availability_by_threshold,
                "median_anchors_reachable": geometry.median_anchors_reachable,
                "median_anchors_used": geometry.median_anchors_used,
                "min_anchors_used": geometry.min_anchors_used,
                "median_hdop": geometry.median_hdop,
                "median_vdop": geometry.median_vdop,
                "worst_vdop": geometry.worst_vdop,
                "median_condition_number": geometry.median_condition_number,
                "median_link_range_m": geometry.median_link_range_m,
                "max_link_range_used_m": geometry.max_link_range_m,
                "links_beyond_calibrated_envelope": (
                    geometry.links_beyond_calibrated_envelope
                ),
                "capex_total_tl": scenario.capex_total_tl,
                "capex_per_km2_tl": result.capex_per_km2_tl,
                "capex_per_km_tl": result.capex_per_km_tl,
                "evidence": [e.to_dict() for e in scenario.evidence_records],
                "notes": list(scenario.notes),
            }
        )
    return records
