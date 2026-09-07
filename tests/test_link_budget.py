import pytest

from yerkon.evidence import EvidenceType
from yerkon.link_budget import (
    E28_2G4M27S_REFERENCE_DISTANCE_M,
    RURAL_LINK_RANGE,
    SX1280_REFERENCE_DISTANCE_M,
    TUNNEL_LINK_RANGE,
    URBAN_LINK_RANGE,
    minimum_spacing_for_fix,
)
from yerkon.scenarios import (
    TUNNEL_MAX_SPACING_FOR_FIX_M,
    TUNNEL_NODE_SPACING_M,
    critical_zone_scenario,
)
from yerkon.simulate import anchors_in_range


def test_published_reference_distances_are_the_manufacturer_figures():
    assert SX1280_REFERENCE_DISTANCE_M == 3000.0
    assert E28_2G4M27S_REFERENCE_DISTANCE_M == 8000.0


def test_every_modelled_range_is_below_its_published_reference():
    # The reference distance is an open-field, 1 kbps figure. A deployment
    # cannot beat it, so a modelled range above it would be a mistake.
    for link in (URBAN_LINK_RANGE, RURAL_LINK_RANGE):
        assert link.range_m < link.reference_distance_m
        assert 0.0 < link.fraction_of_reference < 1.0


def test_ranges_are_labelled_as_this_project_s_judgement():
    # The reference distances are published; the derating from them is not.
    for link in (URBAN_LINK_RANGE, RURAL_LINK_RANGE, TUNNEL_LINK_RANGE):
        assert link.evidence.evidence_type is EvidenceType.ENGINEERING_ASSUMPTION
        assert link.evidence.source_scope.strip()
        assert link.evidence.caveats.strip()


def test_dwm3000_has_no_published_reference_to_derate_from():
    assert TUNNEL_LINK_RANGE.reference_distance_m is None
    assert TUNNEL_LINK_RANGE.fraction_of_reference is None
    assert "no maximum range" in TUNNEL_LINK_RANGE.evidence.source_scope.lower()


def test_spacing_ceiling_follows_from_range_and_the_four_anchor_minimum():
    # A receiver on a line of anchors spaced S apart hears about 2R/S of
    # them; four are needed for a 3D fix.
    assert minimum_spacing_for_fix(150.0) == pytest.approx(75.0)
    assert minimum_spacing_for_fix(150.0, minimum_anchors=6) == pytest.approx(50.0)
    assert minimum_spacing_for_fix(150.0, sides=2) == pytest.approx(150.0)


def test_spacing_ceiling_rejects_an_impossible_anchor_minimum():
    with pytest.raises(ValueError):
        minimum_spacing_for_fix(150.0, minimum_anchors=3)


def test_the_reports_own_tunnel_spacing_cannot_produce_a_fix():
    # The report proposes 10-15 nodes per 2 km corridor, about 150 m apart.
    # At the DWM3000's modelled range that leaves a receiver hearing fewer
    # than the four anchors a 3D fix needs. This is the study's one
    # concrete correction back to the report, so it is pinned by a test.
    from yerkon.scenarios import tunnel_layout

    reports_spacing = tunnel_layout(length_m=4000.0, spacing_m=150.0)
    tag = [2000.0, 9.0, 1.5]
    heard = anchors_in_range(tag, reports_spacing.positions, TUNNEL_LINK_RANGE.range_m)
    assert int(heard.sum()) < 4


def test_the_chosen_tunnel_spacing_stays_under_the_ceiling():
    assert TUNNEL_NODE_SPACING_M < TUNNEL_MAX_SPACING_FOR_FIX_M
    scenario = critical_zone_scenario()
    counts = [
        int(anchors_in_range(p, scenario.anchors, scenario.max_link_range_m).sum())
        for p in scenario.path.points()
    ]
    assert min(counts) >= 4
