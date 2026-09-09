"""Real ground and real buildings, and the cache that makes runs repeatable."""

import json
import math

import numpy as np
import pytest

from yerkon.site.cache import SiteCache
from yerkon.site.fetch import (
    GeoTiffElevation,
    OpenStreetMapBuildings,
    ServiceElevation,
    Unreachable,
    build_site,
    _assumed_footprint_radius_m,
    _parse_height,
)
from yerkon.site.model import BoundingBox, Buildings, Site, SiteManifest

ANKARA = BoundingBox(south=39.90, west=32.80, north=39.95, east=32.88)


def a_site(grid=None, buildings=None, spacing_m=30.0):
    grid = np.zeros((20, 25)) if grid is None else grid
    return Site(
        bounds=ANKARA,
        elevation_grid_m=grid,
        grid_spacing_m=spacing_m,
        manifest=SiteManifest("test", 30.0, "2026-09-09T00:00:00+00:00"),
        buildings=buildings,
    )


# --- Geometry -------------------------------------------------------------


def test_a_degree_of_longitude_is_shorter_than_one_of_latitude_in_turkey():
    per_latitude, per_longitude = ANKARA.metres_per_degree()
    assert per_latitude == pytest.approx(111_035.0, rel=0.001)
    assert per_longitude == pytest.approx(85_410.0, rel=0.001)
    assert per_longitude < per_latitude


def test_a_bounding_box_must_be_the_right_way_round():
    with pytest.raises(ValueError, match="south < north"):
        BoundingBox(south=40.0, west=32.0, north=39.0, east=33.0)


def test_ground_height_interpolates_between_grid_nodes():
    grid = np.array([[0.0, 100.0], [0.0, 100.0]])
    site = a_site(grid=grid, spacing_m=10.0)
    assert site.height_at(0.0, 0.0) == pytest.approx(0.0)
    assert site.height_at(10.0, 0.0) == pytest.approx(100.0)
    assert site.height_at(5.0, 0.0) == pytest.approx(50.0)


def test_sampling_outside_the_grid_clamps_rather_than_raising():
    """A link budget grazes the edge of a site and should not crash there."""
    site = a_site(grid=np.array([[7.0, 7.0], [7.0, 7.0]]), spacing_m=10.0)
    assert site.height_at(-500.0, -500.0) == pytest.approx(7.0)
    assert site.height_at(9_999.0, 9_999.0) == pytest.approx(7.0)


def test_a_uniform_slope_reads_as_smooth():
    """Roughness feeds the reflection model, which wants scatter not shape.

    A tilted plane reflects perfectly well, so a constant slope must not
    be reported as rough or the model would scatter a good reflection.
    """
    rows, columns = 40, 40
    ramp = np.tile(np.arange(columns, dtype=float) * 5.0, (rows, 1))
    assert a_site(grid=ramp).roughness_m() == pytest.approx(0.0, abs=1e-9)


def test_broken_ground_reads_as_rough():
    rng = np.random.default_rng(0)
    noisy = rng.normal(0.0, 4.0, size=(40, 40))
    assert a_site(grid=noisy).roughness_m() > 2.0


# --- Buildings ------------------------------------------------------------


def test_only_buildings_the_path_crosses_obstruct_it():
    """A tower beside the road does not block a link running past it."""
    buildings = Buildings(
        centre_x_m=np.array([500.0, 500.0]),
        centre_y_m=np.array([0.0, 400.0]),
        radius_m=np.array([20.0, 20.0]),
        height_m=np.array([15.0, 90.0]),
    )
    height, fraction = buildings.tallest_along((0.0, 0.0, 10.0), (1000.0, 0.0, 10.0))
    assert height == pytest.approx(15.0), "the 90 m tower is 400 m off the path"
    assert fraction == pytest.approx(0.5, abs=0.05)


def test_no_buildings_means_no_obstruction():
    empty = Buildings(*(np.array([]) for _ in range(4)))
    assert empty.is_empty
    assert empty.tallest_along((0.0, 0.0, 5.0), (100.0, 0.0, 5.0)) == (0.0, 0.5)


@pytest.mark.parametrize(
    "raw,expected",
    [("12", 12.0), ("12 m", 12.0), ("12.5", 12.5), (None, None), ("tall", None), ("0", None)],
)
def test_building_heights_are_read_where_a_mapper_recorded_one(raw, expected):
    assert _parse_height(raw) == expected


def test_a_taller_building_is_assumed_broader():
    assert _assumed_footprint_radius_m(50.0) > _assumed_footprint_radius_m(6.0)
    assert _assumed_footprint_radius_m(1.0) >= 6.0


# --- The manifest ---------------------------------------------------------


def test_a_site_without_buildings_says_so_rather_than_implying_open_ground():
    """The difference between 'no buildings here' and 'nobody looked'."""
    manifest = SiteManifest("SRTM", 30.0, "2026-09-09T00:00:00+00:00")
    assert not manifest.has_buildings
    assert "no building data" in manifest.describe()


def test_a_site_with_buildings_reports_where_they_came_from():
    manifest = SiteManifest(
        "SRTM", 30.0, "2026-09-09T00:00:00+00:00",
        feature_source="OpenStreetMap", building_count=412,
    )
    assert "412 buildings from OpenStreetMap" in manifest.describe()


# --- The cache ------------------------------------------------------------


def test_a_cached_site_reloads_identically(tmp_path):
    """ADR-0008. Someone else with this directory gets the same numbers."""
    buildings = Buildings(
        centre_x_m=np.array([10.0, 20.0]), centre_y_m=np.array([5.0, 6.0]),
        radius_m=np.array([8.0, 9.0]), height_m=np.array([12.0, 30.0]),
    )
    original = a_site(grid=np.linspace(0, 100, 400).reshape(20, 20), buildings=buildings)

    cache = SiteCache(tmp_path / "ankara")
    assert not cache.exists
    cache.save(original)
    assert cache.exists

    reloaded = cache.load()
    assert np.array_equal(reloaded.elevation_grid_m, original.elevation_grid_m)
    assert reloaded.bounds == original.bounds
    assert reloaded.buildings is not None
    assert np.array_equal(reloaded.buildings.height_m, buildings.height_m)
    assert reloaded.manifest.elevation_source == "test"


def test_loading_a_missing_cache_says_what_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="yerkon fetch"):
        SiteCache(tmp_path / "nowhere").load()


def test_the_manifest_is_readable_without_this_codebase(tmp_path):
    """A cache is an artefact to share, so its record has to be plain JSON."""
    cache = SiteCache(tmp_path / "ankara")
    cache.save(a_site())
    payload = json.loads((cache.directory / "manifest.json").read_text(encoding="utf-8"))
    assert payload["manifest"]["elevation_source"] == "test"
    assert payload["bounds"]["south"] == pytest.approx(39.90)


# --- Fetching -------------------------------------------------------------


class FakeElevation:
    """An elevation source that answers, for testing composition."""

    name = "fake"

    def __init__(self, height_m=42.0):
        self.height_m = height_m

    def grid_for(self, bounds, spacing_m):
        from yerkon.site.fetch import ElevationGrid

        return ElevationGrid(
            values_m=np.full((8, 8), self.height_m), spacing_m=spacing_m,
            source=self.name, resolution_m=spacing_m,
        )


class DeadSource:
    name = "dead"

    def grid_for(self, bounds, spacing_m):
        raise Unreachable("no route to host")


def test_the_first_source_that_answers_wins():
    """So a caller lists the local raster first and the services after."""
    site = build_site(ANKARA, elevation_sources=(DeadSource(), FakeElevation(11.0)))
    assert site.elevation_grid_m[0, 0] == pytest.approx(11.0)
    assert site.manifest.elevation_source == "fake"


def test_a_source_that_failed_is_recorded_not_hidden():
    site = build_site(ANKARA, elevation_sources=(DeadSource(), FakeElevation()))
    assert any("dead unavailable" in note for note in site.manifest.notes)


def test_no_ground_at_all_is_the_one_fatal_case():
    with pytest.raises(Unreachable, match="No elevation source answered"):
        build_site(ANKARA, elevation_sources=(DeadSource(),))


def test_missing_buildings_do_not_stop_a_fetch():
    """Ground without buildings is still a usable site."""

    class DeadBuildings:
        name = "dead OSM"

        def buildings_for(self, bounds):
            raise Unreachable("rate limited")

    site = build_site(
        ANKARA, elevation_sources=(FakeElevation(),), buildings_source=DeadBuildings()
    )
    assert site.buildings is None
    assert not site.manifest.has_buildings
    assert any("dead OSM unavailable" in note for note in site.manifest.notes)


# --- The GeoTIFF reader ---------------------------------------------------


def test_a_geotiff_on_disk_is_read_and_resampled(tmp_path):
    """Exercises the reader against a real file rather than trusting it.

    Writes a raster whose height rises with longitude, then checks the
    resampled grid rises with x. That catches a transposed axis, which is
    the mistake this reader is most likely to make.
    """
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import from_origin

    path = tmp_path / "ground.tif"
    rows, columns = 60, 80
    values = np.tile(np.arange(columns, dtype="float32") * 10.0, (rows, 1))

    with rasterio.open(
        path, "w", driver="GTiff", height=rows, width=columns, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=from_origin(32.80, 39.95, 0.001, 0.001),
    ) as raster:
        raster.write(values, 1)

    grid = GeoTiffElevation(str(path)).grid_for(ANKARA, spacing_m=200.0)

    assert grid.values_m.shape[0] >= 2 and grid.values_m.shape[1] >= 2
    assert grid.values_m[0, -1] > grid.values_m[0, 0], "height must rise with x"
    assert "ground.tif" in grid.source


def test_the_services_are_named_so_a_manifest_can_cite_them():
    assert "OpenTopoData" in ServiceElevation().name
    assert OpenStreetMapBuildings().name == "OpenStreetMap"


def test_a_site_becomes_terrain_that_carries_its_own_roughness():
    """Real ground brings its reflection behaviour with it, unchosen."""
    from yerkon.world import terrain_from_site

    rng = np.random.default_rng(1)
    site = a_site(grid=rng.normal(50.0, 3.0, size=(40, 40)))
    terrain = terrain_from_site(site)

    assert terrain.micro_roughness_m > 1.0
    assert terrain.micro_roughness_m == pytest.approx(site.roughness_m())


def test_a_path_over_a_building_has_to_clear_its_roof():
    """A footprint reports the roof, because that is what blocks the path."""
    from yerkon.world import terrain_from_site

    buildings = Buildings(
        centre_x_m=np.array([300.0]), centre_y_m=np.array([0.0]),
        radius_m=np.array([40.0]), height_m=np.array([60.0]),
    )
    site = a_site(grid=np.zeros((30, 30)), buildings=buildings)
    terrain = terrain_from_site(site)

    assert terrain.height_at(300.0, 0.0) == pytest.approx(60.0)
    assert terrain.height_at(300.0, 200.0) == pytest.approx(0.0), "beside it, not over it"

    obstruction = terrain.obstruction_between((0.0, 0.0, 25.0), (600.0, 0.0, 2.0), 200)
    assert obstruction.peak_terrain_m == pytest.approx(60.0)
