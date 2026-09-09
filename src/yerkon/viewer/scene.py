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


def design_of(state: ViewState) -> Design:
    """The state's radio settings as the confirmation panel understands them."""
    return Design(
        region=chosen(REGION_CHOICES, state.region, "region"),
        anchor_radio=chosen(RADIO_CHOICES, state.radio, "radio"),
        mounting=chosen(MOUNTING_CHOICES, state.mounting, "mounting"),
        receiver_height_m=state.receiver_height_m,
        surface_roughness_m=state.roughness_m,
        target_ranging_sigma_m=state.tolerance_m,
    )


def scene(state: ViewState) -> dict:
    """Ground, road and anchors. Cheap enough to recompute on every drag."""
    terrain = state.terrain()
    deployment = state.deployment(terrain)
    design = design_of(state)

    # Measured from the anchors with the same margin the sweep uses, so
    # no coverage cell is ever painted over ground the mesh does not
    # cover. Centring the mesh on the road instead would leave the far
    # side short by the anchors' own offset.
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

    reach_m = _reach(state, design)

    anchors = []
    for anchor in deployment.anchors:
        x, y = anchor.ground_position_m
        anchors.append({
            "id": anchor.identifier,
            "x": float(x),
            "y": float(y),
            "ground_z": terrain.height_at(x, y),
            "z": anchor.position_m[2],
            "mounting": anchor.mounting.kind,
            "height_m": float(anchor.mounting.height_m.value),
            "moved": anchor.identifier in state.moved,
            "reach_m": reach_m,
        })

    road = [
        {
            "x": float(x),
            "y": 0.0,
            "z": terrain.height_at(float(x), 0.0) + state.receiver_height_m,
        }
        for x in np.linspace(0.0, state.corridor_m, 120)
    ]

    return {
        "terrain": {
            "xs": [float(x) for x in xs],
            "ys": [float(y) for y in ys],
            "heights": heights,
            "description": terrain.description,
        },
        "road": road,
        "anchors": anchors,
        "reach_m": reach_m,
        "closure_m": _closure(state, design),
        "state": state.as_json(),
    }


def _reach(state: ViewState, design: Design) -> float:
    """How far one anchor ranges within tolerance, over flat open ground.

    A single number for the whole chain, drawn as a ring on the ground.
    It is the flat-ground figure, so real terrain moves it either way and
    the sweep is what actually decides coverage; the ring is an intuition,
    not a claim.
    """
    anchor = Terminal(design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m))
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, state.receiver_height_m)
    )
    return usable_range_m(
        anchor, receiver, design.anchor_radio,
        target_sigma_m=state.tolerance_m, region=design.region,
    )


def _closure(state: ViewState, design: Design) -> float:
    anchor = Terminal(design.anchor_radio, design.antenna, (0.0, 0.0, design.anchor_height_m))
    receiver = Terminal(
        design.anchor_radio, design.antenna, (0.0, 0.0, state.receiver_height_m)
    )
    return closure_range_m(anchor, receiver, region=design.region)


def sweep(state: ViewState) -> dict:
    """How many anchors reach each cell of the ground. Seconds, not milliseconds."""
    terrain = state.terrain()
    deployment = state.deployment(terrain)

    grid = coverage_grid(
        deployment,
        terrain,
        receiver_height_m=state.receiver_height_m,
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
        receiver_height_m=state.receiver_height_m,
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
        "round_s": deployed.scenario.deployment.round_duration_s,
    }
