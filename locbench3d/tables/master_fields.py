"""Master field catalog, generated from the real columns the table builders produce.

Rather than maintaining a hand-written list that can drift out of sync
with the actual master comparison table, the catalog is built from the
union of keys across a set of representative rows (one per method
family), so "field definitions" always describes real columns. Category
and unit are inferred from the field's prefix and name; the description
names the source concept plainly. This keeps several hundred fields
documented without hand-authoring several hundred bespoke sentences that
could go stale independently of the code.
"""
from __future__ import annotations

from dataclasses import dataclass

_PREFIX_CATEGORY: list[tuple[str, str]] = [
    ("scenario_", "method configuration"),
    ("hw_", "hardware provenance"),
    ("acc_", "accuracy"),
    ("rel_", "reliability"),
    ("scale_", "network scalability"),
    ("pathm_", "path performance"),
    ("geom_", "geometry"),
    ("crlb_", "theoretical bounds"),
    ("cost_", "cost"),
    ("energy_", "energy"),
    ("feas_", "feasibility"),
    ("pareto_", "pareto status"),
    ("evidence_", "provenance"),
    ("gnss_", "gnss"),
    ("range_", "range summary"),
    ("env_", "environment"),
]

_UNIT_SUFFIXES: list[tuple[str, str]] = [
    ("_m3", "cubic meters"),
    ("_m2", "square meters"),
    ("_km", "kilometers"),
    ("_m_s2", "meters per second squared"),
    ("_m_s", "meters per second"),
    ("_m", "meters"),
    ("_s", "seconds"),
    ("_hz", "hertz"),
    ("_dbhz", "dB-Hz"),
    ("_dbm", "dBm"),
    ("_db", "dB"),
    ("_w", "watts"),
    ("_j", "joules"),
    ("_wh", "watt-hours"),
    ("_ma", "milliamps"),
    ("_ua", "microamps"),
    ("_ppm", "parts per million"),
    ("_deg", "degrees"),
    ("_pct", "percent"),
    ("_rate", "fraction 0-1"),
    ("_fraction", "fraction 0-1"),
    ("_probability", "probability 0-1"),
    ("_count", "count"),
]

_IDENTITY_FIELD_NAMES = {"scenario_id", "method", "family"}


@dataclass(frozen=True)
class FieldCatalogEntry:
    name: str
    category: str
    description: str
    unit: str


def _infer_category(name: str) -> str:
    if name in _IDENTITY_FIELD_NAMES:
        return "identity"
    for prefix, category in _PREFIX_CATEGORY:
        if name.startswith(prefix):
            return category
    return "other"


def _infer_unit(name: str) -> str:
    lower = name.lower()
    for suffix, unit in _UNIT_SUFFIXES:
        if lower.endswith(suffix):
            return unit
    if lower.endswith(("_flag", "_valid", "_optimal", "_overloaded", "_success", "_timeout")):
        return "boolean"
    if lower.endswith(("_index", "_rank", "_id", "_type", "_reason", "_state", "_note")):
        return "identifier/text"
    return "dimensionless / see description"


def _humanize(name: str, category: str) -> str:
    stripped = name
    for prefix, cat in _PREFIX_CATEGORY:
        if name.startswith(prefix):
            stripped = name[len(prefix):]
            break
    words = stripped.replace("_", " ").strip()
    return f"{words} ({category}). Field name matches the {category} result field {stripped!r}."


def build_field_catalog(rows: list[dict]) -> list[FieldCatalogEntry]:
    """Build the field catalog from the union of keys across sample rows.

    Pass one representative row per method family (radio-based, GNSS,
    ...) so the catalog covers every field group the master table can
    contain.
    """
    all_names: set[str] = set()
    for row in rows:
        all_names.update(row.keys())

    entries = []
    for name in sorted(all_names):
        category = _infer_category(name)
        entries.append(
            FieldCatalogEntry(
                name=name,
                category=category,
                description=_humanize(name, category),
                unit=_infer_unit(name),
            )
        )
    return entries
