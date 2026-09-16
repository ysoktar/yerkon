"""Roads and the structures beside them, and reading geometry without a library.

Two things in this project were built waiting for this data and greyed
until it arrived: the route that drives the real road (ADR-0045) and the
placements that bolt an anchor to a structure that already stands
(ADR-0040). Both are about the same fetch.
"""

import struct

import numpy as np
import pytest

from yerkon.site.fetch import (
    MOUNTABLE,
    OVERTURE_INFRASTRUCTURE,
    OVERTURE_ROADS,
    OvertureFurniture,
    OvertureRoads,
    lines_in,
)
from yerkon.site.model import Furniture


# --- WKB, decoded by hand -------------------------------------------------


def a_line(points, order="<", code=2):
    """One WKB LineString, written the way a spatial database writes one."""
    body = struct.pack(order + "BII", 1 if order == "<" else 0, code,
                       len(points))
    for x, y in points:
        body += struct.pack(order + "dd", x, y)
    return body


def test_a_line_comes_back_as_the_points_that_went_in():
    points = [(32.8, 39.9), (32.9, 39.95), (33.0, 39.9)]
    assert lines_in(a_line(points)) == [points]


def test_it_reads_both_byte_orders():
    """WKB carries its own byte order in the first byte, and a reader
    that assumes one is a reader that works on half the world's data."""
    points = [(1.0, 2.0), (3.0, 4.0)]
    assert lines_in(a_line(points, "<")) == lines_in(a_line(points, ">"))


def test_a_collection_of_lines_is_read_as_several():
    """A road split by a junction arrives as a MultiLineString, and each
    part carries its own byte order and type code."""
    one = a_line([(0.0, 0.0), (1.0, 1.0)])
    two = a_line([(5.0, 5.0), (6.0, 6.0)], ">")
    multi = struct.pack("<BII", 1, 5, 2) + one + two
    assert lines_in(multi) == [[(0.0, 0.0), (1.0, 1.0)],
                               [(5.0, 5.0), (6.0, 6.0)]]


def test_a_line_with_a_height_in_it_is_still_a_line():
    """Extra ordinates are read and dropped: this project takes height
    from the terrain, and a road that carries one is still a road."""
    body = struct.pack("<BII", 1, 2 | 0x80000000, 2)
    body += struct.pack("<6d", 1.0, 2.0, 30.0, 3.0, 4.0, 31.0)
    assert lines_in(body) == [[(1.0, 2.0), (3.0, 4.0)]]


def test_something_that_is_not_a_line_says_so():
    """Rather than returning an empty list somebody would read as "no
    road here"."""
    with pytest.raises(ValueError, match="not a line"):
        lines_in(struct.pack("<BII", 1, 3, 1))


def test_nothing_at_all_is_no_lines_rather_than_a_failure():
    assert lines_in(b"") == []


def test_a_line_of_one_point_is_not_a_line():
    assert lines_in(a_line([(1.0, 2.0)])) == []


# --- Which structures count -----------------------------------------------


def test_only_things_an_anchor_could_be_bolted_to_are_mountable():
    """The point of ADR-0015 is that a structure which already stands
    costs nothing — not that anything in the data does. A wall, a kerb
    and a piece of public art are all in this theme."""
    kinds = set(MOUNTABLE)
    assert ("transportation", "traffic_signals") in kinds
    assert ("transit", "bus_stop") in kinds
    for not_a_mounting in (("barrier", "wall"), ("barrier", "kerb"),
                           ("barrier", "fence"), ("pedestrian", "artwork"),
                           ("pedestrian", "atm"), ("transit", "parking")):
        assert not_a_mounting not in kinds, not_a_mounting


def test_every_mountable_structure_names_a_mounting_this_project_has():
    """The kind travels with the position because it decides how high the
    anchor sits and what it costs."""
    from yerkon.viewer.state import ViewState

    mountings, _ = ViewState().catalogues()
    for kind in set(MOUNTABLE.values()):
        assert kind in mountings, kind


def test_footways_and_steps_are_not_roads_a_receiver_drives():
    """A parameter rather than a rule: a study of pedestrians would want
    exactly them."""
    keep = OvertureRoads().keep
    assert "primary" in keep and "residential" in keep
    for on_foot in ("footway", "steps", "cycleway", "path"):
        assert on_foot not in keep, on_foot


def test_the_two_sources_read_two_different_parts_of_the_bucket():
    """One index per theme. Sharing one would hand a road scan the
    buildings' row groups, which is a wrong answer rather than a slow
    one."""
    assert OvertureRoads().theme == OVERTURE_ROADS
    assert OvertureFurniture().theme == OVERTURE_INFRASTRUCTURE
    assert OvertureRoads().theme != OvertureFurniture().theme


def test_the_index_is_cached_under_the_theme_as_well_as_the_release(tmp_path):
    from yerkon.site.fetch import _OvertureReader

    roads = _OvertureReader(OvertureRoads(cache_directory=str(tmp_path)))
    kit = _OvertureReader(OvertureFurniture(cache_directory=str(tmp_path)))
    assert roads._index_path() != kit._index_path()


# --- What the site carries ------------------------------------------------


def test_furniture_needs_a_kind_for_every_structure():
    with pytest.raises(ValueError, match="kind for every"):
        Furniture(x_m=np.array([1.0, 2.0]), y_m=np.array([1.0, 2.0]),
                  kind=("column",))


def test_a_site_counts_what_it_found_rather_than_what_was_asked_for():
    """A place with no traffic signals should say so rather than leave a
    reader to infer it from an empty list."""
    kit = Furniture(x_m=np.array([1.0, 2.0, 3.0]),
                    y_m=np.array([1.0, 2.0, 3.0]),
                    kind=("column", "sign", "column"))
    assert kit.counted() == {"column": 2, "sign": 1}


def test_the_shipped_sites_carry_roads_and_structures():
    """The two features that were greyed until this arrived."""
    from yerkon.scenarios import fetched

    site = fetched("kizilay")
    assert site.roads_m, "kizilay should carry road geometry"
    assert site.furniture is not None and len(site.furniture)

    # Roads are in local metres, and are the real geometry rather than
    # geometry cut to the site: a segment whose box overlaps the site can
    # run past it, and a road pulled back to the boundary is a road that
    # bends where it does not. The cutting happens when a route is made.
    assert all(len(line) >= 2 for line in site.roads_m)
    near = [(x, y) for line in site.roads_m for x, y in line
            if 0 <= x <= site.width_m and 0 <= y <= site.height_m]
    assert len(near) > 100, "most of this network is on the site"

    kinds = site.furniture.counted()
    assert set(kinds) <= set(MOUNTABLE.values())
    assert sum(kinds.values()) == len(site.furniture)


def test_roads_and_structures_survive_being_written_out_and_read_back(tmp_path):
    from dataclasses import replace

    from yerkon.scenarios import fetched
    from yerkon.site.cache import SiteCache

    site = fetched("kizilay")
    cache = SiteCache(tmp_path)
    cache.save(site)
    again = cache.load()

    assert len(again.roads_m) == len(site.roads_m)
    assert again.roads_m[0] == site.roads_m[0]
    assert len(again.furniture) == len(site.furniture)
    assert again.furniture.kind == site.furniture.kind
    assert np.allclose(again.furniture.x_m, site.furniture.x_m)


def test_a_site_without_them_drops_the_files_rather_than_leaving_them(tmp_path):
    """Fetched again with `--no-roads` over a site that had them. The
    manifest would already say there are none; a file on disk is a thing
    that can be read."""
    from dataclasses import replace

    from yerkon.scenarios import fetched
    from yerkon.site.cache import SiteCache

    cache = SiteCache(tmp_path)
    cache.save(fetched("kizilay"))
    assert (tmp_path / "roads.npz").exists()
    assert (tmp_path / "furniture.npz").exists()

    cache.save(replace(fetched("kizilay"), roads_m=(), furniture=None))
    assert not (tmp_path / "roads.npz").exists()
    assert not (tmp_path / "furniture.npz").exists()
    assert cache.load().roads_m == ()
    assert cache.load().furniture is None


# --- The two things that were waiting for it ------------------------------


def test_the_real_road_route_is_now_one_a_receiver_can_drive():
    """Greyed until this arrived (ADR-0045)."""
    from yerkon.viewer.scene import scene
    from yerkon.viewer.state import from_scenario

    urban = from_scenario("urban")
    assert urban.course().road, "the course carries the road now"
    assert "road" in scene(urban)["choices"]["routes_live"]

    drove = urban.road(urban.terrain(), "road")
    assert len(drove.centreline_m) >= 2
    # A network is not a path. Kızılay is 1 638 segments split at every
    # junction, and driving them in stored order would teleport a vehicle
    # between roads that do not meet.
    assert len(urban.course().road) > 100
    assert drove.length_m > 1000.0
    for x, y in drove.centreline_m:
        assert 0.0 <= x <= urban.corridor_m + 1e-6
        assert 0.0 <= y <= urban.width_m + 1e-6


def test_carrying_a_road_network_is_not_the_same_as_having_one_to_drive():
    """The tunnel row's fetch brought four segments and none of them runs
    inside its two-kilometre corridor, so the route is greyed rather than
    offered and then refused (ADR-0036)."""
    from yerkon.routes import drivable
    from yerkon.viewer.scene import scene
    from yerkon.viewer.state import from_scenario

    bore = from_scenario("tunnel")
    assert bore.course().road, "it does carry a network"
    assert not drivable(bore.course()), "and none of it is on the site"
    assert "road" not in scene(bore)["choices"]["routes_live"]

    with pytest.raises(ValueError, match="inside the site"):
        bore.road(bore.terrain(), "road")


def test_a_search_now_bolts_anchors_to_structures_that_already_stand():
    """The other half of ADR-0040, which had a test using invented
    furniture because there was none to fetch."""
    from dataclasses import replace

    from yerkon.viewer.state import from_scenario

    state = from_scenario("urban")
    standing = state.furniture()
    assert standing, "kizilay brings structures"

    searching = replace(state, runs=tuple(
        replace(run, method="greedy-dop", most=10) for run in state.runs))
    terrain = searching.terrain()
    placed = searching.anchors(terrain)
    assert placed

    where = {(round(spot.x_m, 3), round(spot.y_m, 3)) for spot in standing}
    on_a_structure = sum(
        1 for anchor in placed
        if (round(anchor.ground_position_m[0], 3),
            round(anchor.ground_position_m[1], 3)) in where
    )
    assert on_a_structure == len(placed), (
        "a search over ground with furniture should place on it, not on a "
        "lattice beside it"
    )


def test_modelled_ground_has_no_structures_and_says_so():
    """Nowhere is not somewhere, so it has no traffic signals."""
    from dataclasses import replace

    from yerkon.viewer.state import from_scenario

    modelled = replace(from_scenario("urban"), site="")
    assert modelled.furniture() == ()
    assert modelled.course().road == ()
