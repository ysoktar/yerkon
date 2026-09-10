"""Turning a state into something a browser can draw and read.

Everything here is JSON. The geometry the page renders and the numbers it
prints come from the same objects the report is built from, so a figure
on screen and a figure in the table cannot disagree (ADR-0001).

Three jobs, deliberately separate, because they cost wildly different
amounts of time and the page asks for them independently: the scene is
instant, the sweep takes seconds, and the run takes longer still.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

from yerkon.cost import DEFAULT_RATES, price
from yerkon.design import Design, MOUNTING_CHOICES, RADIO_CHOICES, REGION_CHOICES, chosen
from yerkon.evaluate import coverage_grid, run_scenario
from yerkon.estimator import track
from yerkon.numbers import decimal_comma
from yerkon.rf import Terminal, closure_range_m, usable_range_m
from yerkon.viewer.state import ViewState

#: Samples across the scene for the ground mesh.
#:
#: A hundred by forty is enough for hills three kilometres apart to read
#: as hills, and small enough that the browser redraws it while a slider
#: is still moving.
MESH_COLUMNS = 100
MESH_ROWS = 40


def sweep_margin_m(state: ViewState) -> float:
    """How far past the anchors both the sweep and the mesh reach.

    One function, because a mesh smaller than the sweep paints coverage
    cells over nothing and a mesh larger than it wastes the frame.
    """
    return max(state.spacing_m * 3.0, 4000.0)


def design_of(state: ViewState, run=None) -> Design:
    """One anchor run's settings, as the confirmation panel understands them.

    The panel talks about a radio on a mounting at a tolerance, and a
    corridor now carries more than one of those, so it is asked about one
    run at a time and the panel says which.
    """
    run = run or (state.runs[0] if state.runs else None)
    # From the state's own catalogues, so that editing a mounting height
    # or a noise figure by hand moves what the panel says it moves.
    mounting_of, radio_of = state.catalogues()
    return Design(
        region=chosen(REGION_CHOICES, state.region, "region"),
        anchor_radio=chosen(radio_of, run.radio if run else "sx1280", "radio"),
        mounting=chosen(
            mounting_of, run.mounting if run else "mast", "mounting"
        ),
        receiver_height_m=_lowest_unit(state),
        surface_roughness_m=state.roughness_m,
        target_ranging_sigma_m=state.tolerance_m,
    )


def _lowest_unit(state: ViewState) -> float:
    """The worst case among the units, which is the one range is quoted for."""
    if not state.units:
        return 1.5
    return min(unit.antenna_height_m for unit in state.units)


def reach_of(state: ViewState, run) -> float:
    """How far one run's anchors range within tolerance, over open ground.

    A flat-ground figure, drawn as a ring. Real terrain moves it either
    way and the sweep is what actually decides coverage; the ring is an
    intuition, not a claim.
    """
    design = design_of(state, run)
    anchor = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m)
    )
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.receiver_height_m)
    )
    return usable_range_m(
        anchor, receiver, design.anchor_radio,
        target_sigma_m=state.tolerance_m, region=design.region,
    )


def closure_of(state: ViewState, run) -> float:
    design = design_of(state, run)
    anchor = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m)
    )
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, design.receiver_height_m)
    )
    return closure_range_m(anchor, receiver, region=design.region)


def sweep_margin_m(state: ViewState) -> float:
    """How far past the anchors both the sweep and the mesh reach.

    One function, because a mesh smaller than the sweep paints coverage
    cells over nothing and a mesh larger than it wastes the frame.
    """
    widest = max((run.spacing_m for run in state.runs), default=2000.0)
    return max(widest * 3.0, 4000.0)


def scene(state: ViewState) -> dict:
    """Ground, road, anchors and units. Cheap enough to redraw on every drag."""
    terrain = state.terrain()
    deployment = state.deployment(terrain)

    margin = sweep_margin_m(state)
    positions = [a.position_m for a in deployment.anchors]
    xs = np.linspace(
        min(p[0] for p in positions) - margin,
        max(p[0] for p in positions) + margin,
        MESH_COLUMNS,
    )
    ys = np.linspace(
        min(p[1] for p in positions) - margin,
        max(p[1] for p in positions) + margin,
        MESH_ROWS,
    )
    heights = [[terrain.height_at(float(x), float(y)) for x in xs] for y in ys]

    # One reach per run, because a UWB bracket and a mast on the same
    # corridor do not cover remotely the same ground.
    reach = {run.identifier: reach_of(state, run) for run in state.runs}
    closure = {run.identifier: closure_of(state, run) for run in state.runs}
    run_of = {}
    for run in state.runs:
        for identifier, _, _, _ in run.anchors(terrain):
            run_of[identifier] = run.identifier

    anchors = []
    for anchor in deployment.anchors:
        x, y = anchor.ground_position_m
        run_id = run_of.get(anchor.identifier, "")
        anchors.append({
            "id": anchor.identifier,
            "run": run_id,
            "x": float(x),
            "y": float(y),
            "ground_z": terrain.height_at(x, y),
            "z": anchor.position_m[2],
            "mounting": anchor.mounting.kind,
            "radio": anchor.radio.part,
            "height_m": float(anchor.mounting.height_m.value),
            "moved": anchor.identifier in state.moved,
            "reach_m": reach.get(run_id, 0.0),
        })

    road = [
        {
            "x": float(x),
            "y": 0.0,
            "z": terrain.height_at(float(x), 0.0),
        }
        for x in np.linspace(0.0, state.corridor_m, 120)
    ]

    units = []
    for unit in deployment.receivers:
        trail = [
            unit.journey.position_at(at_s)
            for at_s in np.linspace(0.0, unit.journey.duration_s, 40)
        ]
        units.append({
            "id": unit.identifier,
            "kind": unit.product,
            "hears": len(deployment.anchors_heard_by(unit)),
            "radios": [radio.part for radio in unit.radios],
            "at": list(unit.journey.position_at(0.0)),
            "trail": [list(point) for point in trail],
        })

    return {
        "terrain": {
            "xs": [float(x) for x in xs],
            "ys": [float(y) for y in ys],
            "heights": heights,
            "description": terrain.description,
        },
        "road": road,
        "anchors": anchors,
        "units": units,
        "runs": [
            {
                **run.as_json(),
                "reach_m": reach[run.identifier],
                "closure_m": closure[run.identifier],
                "count": sum(
                    1 for a in anchors if a["run"] == run.identifier
                ),
            }
            for run in state.runs
        ],
        "round_s": deployment.round_duration_s(),
        "assumed": len(state.settings().assumed),
        "assumed_total": len(state.settings().entries),
        "state": state.as_json(),
    }


#: How the figures are grouped in the panel, and what to call each group.
GROUPS = (
    ("mounting", "Montaj yapıları"),
    ("operating", "İşletme giderleri"),
    ("radio", "Modüllerin yayımlanmamış değerleri"),
    ("clock", "Saatler"),
    ("ranging", "Ölçüm alışverişi"),
    ("site", "Saha"),
    ("estimator", "Kestirici"),
)


def figures(state: ViewState) -> dict:
    """Every figure nobody supplied, as the panel needs it.

    Sent whole rather than by group, because the thing a person wants to
    see is how much of the study is still resting on guesses, and that is
    a property of the list rather than of any part of it.
    """
    settings = state.settings()
    listed = []
    for key, entry in sorted(settings.entries.items()):
        head = key.split(".")[0]
        listed.append({
            "key": key,
            "group": head,
            "value": float(entry.sourced.value),
            "unit": entry.sourced.unit,
            "provenance": entry.sourced.provenance.value,
            "source": entry.sourced.source,
            "note": entry.sourced.note,
            "affects": entry.affects,
            "sensitivity": entry.sensitivity,
            "assumed": entry.is_assumed,
            "edited": key in state.overrides,
        })
    return {
        "figures": listed,
        "groups": [
            {"key": key, "label": label}
            for key, label in GROUPS
            if any(f["group"] == key for f in listed)
        ],
        "assumed": len(settings.assumed),
        "total": len(settings.entries),
    }


def sweep(state: ViewState) -> dict:
    """How many anchors reach each cell of the ground. Seconds, not milliseconds."""
    terrain = state.terrain()
    deployment = state.deployment(terrain)

    grid = coverage_grid(
        deployment,
        terrain,
        receiver_height_m=_lowest_unit(state),
        target_sigma_m=state.tolerance_m,
        resolution_m=state.sweep_m,
        margin_m=sweep_margin_m(state),
    )

    return {
        "xs": [float(x) for x in grid.xs],
        "ys": [float(y) for y in grid.ys],
        "counts": grid.counts.tolist(),
        "resolution_m": grid.resolution_m,
        "reached_km2": grid.area_reached_by(1),
        "served_km2": grid.area_reached_by(4),
    }


def simulate(state: ViewState) -> dict:
    """Drive the journey and price the deployment. The slow one."""
    deployed = state.deployed()
    samples = run_scenario(deployed.scenario)

    terrain = state.terrain()
    grid = coverage_grid(
        state.deployment(terrain), terrain,
        receiver_height_m=_lowest_unit(state),
        target_sigma_m=state.tolerance_m,
        resolution_m=state.sweep_m,
        margin_m=sweep_margin_m(state),
    )
    served_km2 = grid.area_reached_by(4)

    costing = price(deployed.inventory(served_km2), DEFAULT_RATES)
    hpe_p50, _ = samples.percentile(50)
    hpe_p95, vpe_p95 = samples.percentile(95)

    return {
        "hpe_p50_m": hpe_p50,
        "hpe_p95_m": hpe_p95,
        "vpe_p95_m": vpe_p95,
        "availability": samples.availability,
        "fixes": samples.produced,
        "attempted": samples.attempted,
        "lost_links": samples.lost_links,
        "attempted_links": samples.attempted_links,
        "served_km2": served_km2,
        "reached_km2": grid.area_reached_by(1),
        "anchors": len(deployed.scenario.deployment.anchors),
        "capex_tl": costing.capex_tl,
        "opex_tl_per_year": costing.opex_tl_per_year,
        "capex_tl_per_km2": costing.capex_tl_per_km2,
        "opex_tl_per_km2_year": costing.opex_tl_per_km2_year,
        "capex_tl_per_route_km": costing.capex_tl_per_route_km,
        "assumed_share": costing.assumed_share,
        "round_s": deployed.scenario.deployment.round_duration_s(),
        "units": len(deployed.scenario.deployment.receivers),
    }
