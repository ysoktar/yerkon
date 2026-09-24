"""Real ground and real buildings, and the cache that makes runs repeatable."""

import json
import math

import numpy as np
import pytest

from yerkon.site.cache import SiteCache
from yerkon.site.fetch import (
    CopernicusElevation,
    GeoTiffElevation,
    OpenStreetMapBuildings,
    ServiceElevation,
    Unreachable,
    build_site,
    _assumed_footprint_radius_m,
    _parse_height,
    copernicus_tile_name,
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
    assert "bina verisi yok" in manifest.describe()


def test_a_site_with_buildings_reports_where_they_came_from():
    manifest = SiteManifest(
        "SRTM", 30.0, "2026-09-09T00:00:00+00:00",
        feature_source="OpenStreetMap", building_count=412,
    )
    assert "OpenStreetMap kaynağından 412 bina" in manifest.describe()


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
    assert any("dead: no route to host" in note for note in site.manifest.notes)


def test_no_ground_at_all_is_the_one_fatal_case():
    with pytest.raises(Unreachable, match="Hiçbir yükseklik kaynağı cevap vermedi"):
        build_site(ANKARA, elevation_sources=(DeadSource(),))


def test_missing_buildings_do_not_stop_a_fetch():
    """Ground without buildings is still a usable site."""

    class DeadBuildings:
        name = "dead OSM"

        def buildings_for(self, bounds):
            raise Unreachable("rate limited")

    site = build_site(
        ANKARA, elevation_sources=(FakeElevation(),),
        buildings_sources=(DeadBuildings(),)
    )
    assert site.buildings is None
    assert not site.manifest.has_buildings
    assert any("dead OSM erişilemedi" in note for note in site.manifest.notes)


# --- The GeoTIFF reader ---------------------------------------------------


def test_a_geotiff_on_disk_is_read_and_resampled(tmp_path):
    """Exercises the reader against a real file rather than trusting it.

    Writes a raster whose height rises with longitude, then checks the
    resampled grid rises with x. That catches a transposed axis, which is
    the mistake this reader is most likely to make.
    """
    rasterio = pytest.importorskip("rasterio")
    from affine import Affine

    path = tmp_path / "ground.tif"
    rows, columns = 60, 80
    values = np.tile(np.arange(columns, dtype="float32") * 10.0, (rows, 1))

    with rasterio.open(
        path, "w", driver="GTiff", height=rows, width=columns, count=1,
        dtype="float32", crs="EPSG:4326",
        # Built directly rather than through rasterio's from_origin, which
        # multiplies two Affines with * and trips a deprecation warning
        # inside the library.
        transform=Affine(0.001, 0.0, 32.80, 0.0, -0.001, 39.95),
    ) as raster:
        raster.write(values, 1)

    grid = GeoTiffElevation(str(path)).grid_for(ANKARA, spacing_m=200.0)

    assert grid.values_m.shape[0] >= 2 and grid.values_m.shape[1] >= 2
    assert grid.values_m[0, -1] > grid.values_m[0, 0], "height must rise with x"
    assert "ground.tif" in grid.source


def test_the_services_are_named_so_a_manifest_can_cite_them():
    assert "OpenTopoData" in ServiceElevation().name
    assert OpenStreetMapBuildings().name == "OpenStreetMap"


# --- OpenStreetMap, short of the network ---------------------------------
#
# Overpass is blocked from the sandbox this was built in (ADR-0021), and
# every mirror with it, so the one thing these cannot check is the HTTP
# hop. Everything on either side of it is checked here against a recorded
# Overpass answer: the query that goes out, and what comes back becoming
# buildings a link budget can be blocked by.


OVERPASS_ANSWER = {
    "version": 0.6,
    "elements": [
        # A mapper recorded a height.
        {"type": "way", "id": 1, "center": {"lat": 39.9200, "lon": 32.8540},
         "tags": {"building": "yes", "height": "24"}},
        # Another recorded it with a unit on it.
        {"type": "way", "id": 2, "center": {"lat": 39.9210, "lon": 32.8550},
         "tags": {"building": "apartments", "height": "31 m"}},
        # A third recorded storeys instead.
        {"type": "way", "id": 3, "center": {"lat": 39.9220, "lon": 32.8560},
         "tags": {"building": "yes", "building:levels": "8"}},
        # A fourth recorded neither.
        {"type": "way", "id": 4, "center": {"lat": 39.9230, "lon": 32.8570},
         "tags": {"building": "retail"}},
        # A fifth is a relation with no centre at all, which Overpass does
        # return and which has no position to place.
        {"type": "way", "id": 5, "tags": {"building": "yes"}},
    ],
}


class RecordedOverpass:
    """Overpass, as it answered. Records what was asked of it."""

    def __init__(self, payload=None, status=200):
        self.payload = OVERPASS_ANSWER if payload is None else payload
        self.status = status
        self.asked = None

    def post(self, url, data=None, timeout=None):
        self.asked = {"url": url, "data": data, "timeout": timeout}
        return self

    def raise_for_status(self):
        if self.status != 200:
            raise RuntimeError("{} from Overpass".format(self.status))

    def json(self):
        return self.payload

    # The parts of a response the fetch reads through `yerkon.site.http`.
    @property
    def status_code(self):
        return self.status

    @property
    def content(self):
        import json

        return json.dumps(self.payload).encode("utf-8")

    headers = {}


def overpass_answering(monkeypatch, recorded):
    """Put a recorded Overpass in the place the real one is imported from."""
    import sys
    import types

    module = types.ModuleType("requests")
    module.post = recorded.post
    monkeypatch.setitem(sys.modules, "requests", module)
    return recorded


def test_the_overpass_query_asks_for_the_bounding_box_it_was_given(monkeypatch):
    """South, west, north, east, in that order.

    Overpass takes its bounding box in an order nothing else here uses, and
    getting it wrong returns buildings from somewhere else entirely rather
    than an error.
    """
    recorded = overpass_answering(monkeypatch, RecordedOverpass())
    bounds = BoundingBox(south=39.91, west=32.84, north=39.93, east=32.86)

    OpenStreetMapBuildings().buildings_for(bounds)

    query = recorded.asked["data"]["data"]
    assert "way[building](39.91,32.84,39.93,32.86)" in query, query
    assert "out center tags" in query
    assert "[out:json]" in query
    assert recorded.asked["url"].endswith("/api/interpreter")


def test_a_mapped_height_beats_a_storey_count_beats_a_default(monkeypatch):
    """And the manifest says how many of each, because a site whose heights
    are mostly the default is weaker evidence than one whose heights are
    mapped."""
    overpass_answering(monkeypatch, RecordedOverpass())
    bounds = BoundingBox(south=39.91, west=32.84, north=39.93, east=32.86)

    buildings, notes = OpenStreetMapBuildings().buildings_for(bounds)

    # The one with no centre is dropped; Overpass returns those.
    assert len(buildings.height_m) == 4
    assert list(buildings.height_m) == [24.0, 31.0, 24.0, 9.0]
    assert "2 bina yüksekliği etiketlenmiş, 1 tanesi kat sayısından" in (
        " ".join(notes)
    )


def test_buildings_land_in_metres_from_the_corner_of_the_box(monkeypatch):
    """Overpass answers in degrees and everything downstream is in metres."""
    overpass_answering(monkeypatch, RecordedOverpass())
    bounds = BoundingBox(south=39.91, west=32.84, north=39.93, east=32.86)
    per_lat, per_lon = bounds.metres_per_degree()

    buildings, _ = OpenStreetMapBuildings().buildings_for(bounds)

    assert buildings.centre_x_m[0] == pytest.approx((32.8540 - 32.84) * per_lon)
    assert buildings.centre_y_m[0] == pytest.approx((39.9200 - 39.91) * per_lat)
    # Ordered south to north in the answer, so ordered up in metres.
    assert list(buildings.centre_y_m) == sorted(buildings.centre_y_m)
    assert (buildings.radius_m > 0).all()


def test_overpass_failing_is_reported_rather_than_swallowed(monkeypatch):
    """A site silently built with no buildings is a site that says a town
    is open ground."""
    overpass_answering(monkeypatch, RecordedOverpass(status=504))
    bounds = BoundingBox(south=39.91, west=32.84, north=39.93, east=32.86)

    with pytest.raises(Unreachable) as raised:
        OpenStreetMapBuildings().buildings_for(bounds)
    assert "OpenStreetMap" in str(raised.value)


def test_fetched_buildings_become_ground_a_packet_can_be_blocked_by(monkeypatch):
    """The whole point of asking Overpass: a link that crosses a tower
    should not close as though the tower were not there."""
    from yerkon.world import terrain_from_site

    overpass_answering(monkeypatch, RecordedOverpass())
    bounds = BoundingBox(south=39.91, west=32.84, north=39.93, east=32.86)
    buildings, _ = OpenStreetMapBuildings().buildings_for(bounds)

    # Its own site, big enough to hold the box the buildings came from.
    site = Site(
        bounds=bounds,
        elevation_grid_m=np.zeros((120, 120)),
        grid_spacing_m=30.0,
        manifest=SiteManifest("test", 30.0, "2026-09-09T00:00:00+00:00"),
        buildings=buildings,
    )
    terrain = terrain_from_site(site)

    tallest = int(buildings.height_m.argmax())
    x = float(buildings.centre_x_m[tallest])
    y = float(buildings.centre_y_m[tallest])
    # A point inside a footprint reports the roof, because that is the
    # surface a path over it has to clear.
    assert terrain.height_at(x, y) == pytest.approx(
        float(buildings.height_m[tallest])
    ), "the tallest building is not standing on the ground it was put on"
    # And open ground beside it is still open ground.
    assert terrain.height_at(x + 500.0, y + 500.0) == pytest.approx(0.0)


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


def test_an_area_too_large_for_the_service_is_refused_before_asking():
    """Say so up front rather than after four hundred requests.

    The public service allows a thousand calls a day. A 35 by 14 km box
    at 30 m spacing is 479,000 points, which is 4,791 calls, so the fetch
    cannot succeed and should not start.
    """
    service = ServiceElevation()
    wide = BoundingBox(south=39.85, west=32.70, north=39.98, east=33.05)

    assert service.points_required(wide, 30.0) > 400_000

    with pytest.raises(Unreachable, match="--spacing"):
        service.grid_for(wide, spacing_m=30.0)

    with pytest.raises(Unreachable, match="--geotiff"):
        service.grid_for(wide, spacing_m=30.0)


def test_the_refusal_suggests_a_spacing_that_would_fit():
    service = ServiceElevation()
    wide = BoundingBox(south=39.85, west=32.70, north=39.98, east=33.05)
    try:
        service.grid_for(wide, spacing_m=30.0)
    except Unreachable as error:
        message = str(error)
    suggested = float(message.split("--spacing ")[1].split()[0])
    assert service.points_required(wide, suggested) <= 400 * service.batch


def test_a_failed_fetch_says_which_source_refused_and_why():
    """A network failure and an oversized request need opposite responses.

    Reporting only that nothing answered leaves the caller unable to tell
    them apart, which is what happened the first time this ran.
    """
    class Chatty:
        name = "chatty"

        def grid_for(self, bounds, spacing_m):
            raise Unreachable("try --spacing 200 instead")

    with pytest.raises(Unreachable, match="--spacing 200"):
        build_site(ANKARA, elevation_sources=(Chatty(),))


# --- Degrading rather than crashing --------------------------------------


def test_a_missing_raster_falls_through_to_the_next_source():
    """A wrong path must not end the fetch with a traceback.

    The whole point of listing sources in order is that a failure moves
    to the next one. A rasterio exception is not Unreachable, so before
    this it escaped the handler and crashed.
    """
    site = build_site(
        ANKARA,
        elevation_sources=(GeoTiffElevation("nowhere/missing.tif"), FakeElevation(3.0)),
    )
    assert site.elevation_grid_m[0, 0] == pytest.approx(3.0)
    assert any("No file at" in note for note in site.manifest.notes)


def test_an_unreadable_file_is_reported_as_such(tmp_path):
    """Present but not a raster is a different failure from absent."""
    not_a_raster = tmp_path / "notes.tif"
    not_a_raster.write_text("this is text", encoding="utf-8")

    with pytest.raises(Unreachable, match="could not be read as a raster"):
        GeoTiffElevation(str(not_a_raster)).grid_for(ANKARA, spacing_m=200.0)


# --- Rate limiting --------------------------------------------------------


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._payload


class FakeRequests:
    """Stands in for the requests module, counting what was asked."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_a_rate_limited_request_is_waited_out_rather_than_abandoned(monkeypatch):
    """429 asks for patience. It is not a refusal.

    The first real run fired as fast as the network allowed and was
    rejected on its first batch.
    """
    monkeypatch.setattr("yerkon.site.fetch.time.sleep", lambda seconds: None)

    service = ServiceElevation()
    fake = FakeRequests([
        FakeResponse(429, headers={"Retry-After": "1"}),
        FakeResponse(429),
        FakeResponse(200, {"results": [{"elevation": 900.0}]}),
    ])

    payload = service._call(fake, "39.9,32.8", index=1, total=1)
    assert payload["results"][0]["elevation"] == 900.0
    assert fake.calls == 3


def test_a_service_that_never_lets_up_says_to_use_a_raster(monkeypatch):
    monkeypatch.setattr("yerkon.site.fetch.time.sleep", lambda seconds: None)

    service = ServiceElevation(retries_on_rate_limit=2)
    fake = FakeRequests([FakeResponse(429)] * 3)

    with pytest.raises(Unreachable, match="--geotiff"):
        service._call(fake, "39.9,32.8", index=1, total=1)


def test_a_failure_does_not_quote_the_hundred_coordinates_it_sent():
    """The query is a hundred coordinates and burying the reason in them
    helps nobody. The first real run printed all of them."""
    service = ServiceElevation()
    fake = FakeRequests([FakeResponse(500)])

    with pytest.raises(Unreachable) as raised:
        service._call(fake, "39.9,32.8|39.9,32.9", index=2, total=7)

    message = str(raised.value)
    assert "request 2 of 7" in message
    assert "39.9" not in message


def test_requests_are_spaced_to_respect_the_stated_limit(monkeypatch):
    slept = []
    monkeypatch.setattr("yerkon.site.fetch.time.sleep", slept.append)

    service = ServiceElevation(seconds_between_requests=1.1)
    assert service.seconds_between_requests == pytest.approx(1.1)


def test_a_connection_failure_reports_the_cause_not_the_query():
    """requests embeds the whole URL in its exceptions.

    The URL here is a hundred coordinates, so formatting the exception
    drags them into the message even when the message does not mention
    them. The first two attempts at this test still leaked them.
    """
    class Exploding:
        def get(self, url, params=None, timeout=None):
            raise OSError(
                "HTTPSConnectionPool(host='api.opentopodata.org', port=443): "
                "Max retries exceeded with url: /v1/srtm30m?locations="
                "39.900000%2C32.850000%7C39.900901%2C32.851170 "
                "(Caused by ProxyError('Tunnel connection failed: 403'))"
            )

    with pytest.raises(Unreachable) as raised:
        ServiceElevation()._call(Exploding(), "39.9,32.8", index=1, total=6)

    message = str(raised.value)
    assert "39.900000" not in message
    assert "locations=" not in message
    assert "403" in message, "the actual reason has to survive"


# --- Copernicus tiles -----------------------------------------------------


@pytest.mark.parametrize(
    "latitude, longitude, expected",
    [
        (39, 32, "Copernicus_DSM_COG_10_N39_00_E032_00_DEM"),
        (0, 0, "Copernicus_DSM_COG_10_N00_00_E000_00_DEM"),
        (-34, -59, "Copernicus_DSM_COG_10_S34_00_W059_00_DEM"),
        (7, 5, "Copernicus_DSM_COG_10_N07_00_E005_00_DEM"),
    ],
)
def test_a_tile_is_named_after_the_corner_of_its_degree_square(
    latitude, longitude, expected
):
    """The name is the whole address. Get the padding wrong and the
    bucket answers 404 for a square that is plainly land."""
    assert copernicus_tile_name(latitude, longitude) == expected


def test_a_box_inside_one_degree_square_needs_one_tile():
    assert CopernicusElevation().tiles_covering(ANKARA) == [(39, 32)]


def test_a_box_that_straddles_a_meridian_needs_a_tile_on_each_side():
    """The user's own area runs from 32.70 to 33.05 and needs two."""
    straddling = BoundingBox(south=39.85, west=32.70, north=39.98, east=33.05)
    assert CopernicusElevation().tiles_covering(straddling) == [(39, 32), (39, 33)]


class FakeStream:
    """A streamed response, as a context manager like requests returns."""

    def __init__(self, status_code, body=b"", chunks=None):
        self.status_code = status_code
        self._body = body
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise OSError("{} Server Error".format(self.status_code))

    def iter_content(self, chunk_size=None):
        if self._chunks is not None:
            return iter(self._chunks)
        return iter([self._body])


class FakeBucket:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def get(self, url, stream=None, timeout=None):
        self.urls.append(url)
        return self.responses.pop(0)


def test_a_tile_is_downloaded_once_and_read_from_disk_after(tmp_path):
    """A second site in the same degree square must cost nothing."""
    copernicus = CopernicusElevation(cache_directory=str(tmp_path))
    bucket = FakeBucket([FakeStream(200, b"raster bytes")])

    first = copernicus.ensure_tile(39, 32, http=bucket)
    second = copernicus.ensure_tile(39, 32, http=bucket)

    assert first == second
    assert first.read_bytes() == b"raster bytes"
    assert len(bucket.urls) == 1, "the second call must not go to the network"
    assert "Copernicus_DSM_COG_10_N39_00_E032_00_DEM" in bucket.urls[0]


def test_a_square_with_no_tile_says_it_is_probably_sea(tmp_path):
    """404 here is not a failure of the fetcher. The bucket holds land."""
    copernicus = CopernicusElevation(cache_directory=str(tmp_path))
    bucket = FakeBucket([FakeStream(404)])

    with pytest.raises(Unreachable, match="all sea"):
        copernicus.ensure_tile(40, 20, http=bucket)


def test_a_cut_transfer_leaves_no_file_a_later_run_would_trust(tmp_path):
    """A tile is a hundred megabytes. Half of one on disk under the real
    name would be read as cached for good."""

    def explode():
        yield b"the first megabyte"
        raise OSError("connection reset by peer")

    copernicus = CopernicusElevation(cache_directory=str(tmp_path))
    bucket = FakeBucket([FakeStream(200, chunks=explode())])

    with pytest.raises(Unreachable, match="unreachable"):
        copernicus.ensure_tile(39, 32, http=bucket)

    assert not list(tmp_path.glob("*.tif"))
    assert not list(tmp_path.glob("*.partial")), "nor the half of it that arrived"


def write_tile(directory, latitude, longitude, value):
    """A one-degree raster in the bucket's own naming, of constant height."""
    rasterio = pytest.importorskip("rasterio")
    from affine import Affine

    path = directory / "{}.tif".format(copernicus_tile_name(latitude, longitude))
    samples = 120
    step = 1.0 / samples
    with rasterio.open(
        path, "w", driver="GTiff", height=samples, width=samples, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=Affine(step, 0.0, float(longitude), 0.0, -step, float(latitude + 1)),
    ) as raster:
        raster.write(np.full((samples, samples), value, dtype="float32"), 1)
    return path


def test_a_cached_tile_is_read_without_touching_the_network(tmp_path):
    write_tile(tmp_path, 39, 32, 900.0)
    copernicus = CopernicusElevation(cache_directory=str(tmp_path))

    grid = copernicus.grid_for(ANKARA, spacing_m=500.0)

    assert np.allclose(grid.values_m, 900.0)
    assert grid.resolution_m == pytest.approx(30.0)
    assert "×1" in grid.source


def test_two_tiles_are_joined_along_the_meridian_they_share(tmp_path):
    """The half of the box in each tile must carry that tile's ground.

    Reading each tile with its gaps already filled would put the median
    of the western tile over the eastern half, which is why the mosaic
    reads them unfilled.
    """
    write_tile(tmp_path, 39, 32, 900.0)
    write_tile(tmp_path, 39, 33, 300.0)
    copernicus = CopernicusElevation(cache_directory=str(tmp_path))

    straddling = BoundingBox(south=39.85, west=32.70, north=39.98, east=33.05)
    grid = copernicus.grid_for(straddling, spacing_m=500.0)

    assert "×2" in grid.source
    assert grid.values_m[0, 0] == pytest.approx(900.0), "west of the meridian"
    assert grid.values_m[0, -1] == pytest.approx(300.0), "east of it"
    assert set(np.unique(grid.values_m)) == {900.0, 300.0}


def test_a_raster_reports_nothing_where_it_covers_nothing(tmp_path):
    """Sampling beyond a raster's edge returns a number, not an error.

    Taking that number for ground is how a mosaic ends up with one
    tile's median spread across the next tile's half of the box.
    """
    pytest.importorskip("rasterio")
    path = write_tile(tmp_path, 39, 33, 300.0)

    grid = GeoTiffElevation(str(path), fill_gaps=False).grid_for(ANKARA, spacing_m=500.0)

    assert np.isnan(grid.values_m).all(), "ANKARA lies a whole degree west"


# --- Overture, the other road to the same buildings ------------------------


def test_a_site_that_brings_buildings_is_charged_no_blanket_clutter():
    """ADR-0038. Two models of the same obstruction is one too many.

    `clutter_loss_db_per_km` stands in for what the terrain cannot show.
    Where the fetch brought footprints the terrain shows it, and charging
    both put the urban row at 71 % available and 3,22 m — worse than
    either model alone, from arithmetic rather than from Ankara.
    """
    import numpy as np

    from yerkon.site.model import Buildings, BoundingBox, Site, SiteManifest
    from yerkon.world import terrain_from_site

    def a_site(buildings):
        return Site(
            bounds=BoundingBox(south=39.9, west=32.8, north=39.91, east=32.81),
            elevation_grid_m=np.zeros((4, 4)) + 900.0,
            grid_spacing_m=30.0,
            manifest=SiteManifest(
                elevation_source="test", elevation_resolution_m=30.0,
                fetched_at="now",
                feature_source=None if buildings is None else "test",
                building_count=0 if buildings is None else len(buildings),
            ),
            buildings=buildings,
        )

    bare = terrain_from_site(a_site(None), clutter_loss_db_per_km=30.0)
    assert bare.clutter_loss_db_per_km == 30.0

    built = terrain_from_site(
        a_site(Buildings(
            centre_x_m=np.array([50.0]), centre_y_m=np.array([50.0]),
            radius_m=np.array([10.0]), height_m=np.array([12.0]),
        )),
        clutter_loss_db_per_km=30.0,
    )
    assert built.clutter_loss_db_per_km == 0.0


def test_finding_what_stands_at_a_point_does_not_read_the_whole_town():
    """A link budget asks sixty-five times a path, for every link.

    Over Kızılay's five thousand footprints the array pass that answered
    it stopped the table finishing. The index has to give the same answer
    as the scan it replaced, on points inside a footprint and outside
    one.
    """
    import numpy as np

    from yerkon.site.model import Buildings

    rng = np.random.default_rng(7)
    count = 400
    buildings = Buildings(
        centre_x_m=rng.uniform(0, 2000, count),
        centre_y_m=rng.uniform(0, 2000, count),
        radius_m=rng.uniform(4, 30, count),
        height_m=rng.uniform(3, 40, count),
    )

    def by_scanning(x, y):
        inside = ((x - buildings.centre_x_m) ** 2
                  + (y - buildings.centre_y_m) ** 2) <= buildings.radius_m ** 2
        return float(buildings.height_m[inside].max()) if inside.any() else 0.0

    hits = 0
    for x, y in zip(rng.uniform(-100, 2100, 600), rng.uniform(-100, 2100, 600)):
        want = by_scanning(x, y)
        assert buildings.tallest_at(float(x), float(y)) == want, (x, y)
        hits += want > 0.0
    assert hits > 20, "this stopped testing points that land on a roof"


def test_the_index_is_rebuilt_rather_than_shipped_to_a_worker():
    """ADR-0025 spreads scenarios across processes by pickling them."""
    import pickle

    import numpy as np

    from yerkon.site.model import Buildings

    buildings = Buildings(
        centre_x_m=np.array([10.0, 80.0]), centre_y_m=np.array([10.0, 80.0]),
        radius_m=np.array([5.0, 5.0]), height_m=np.array([7.0, 9.0]),
    )
    assert buildings.tallest_at(10.0, 10.0) == 7.0
    again = pickle.loads(pickle.dumps(buildings))
    assert "_cells" not in again.__dict__
    assert again.tallest_at(80.0, 80.0) == 9.0


def test_overture_is_read_from_object_storage_rather_than_a_query_service():
    """ADR-0038. Which of the two answers is a property of the network.

    Overpass is a query service many networks refuse outright; Overture
    is a range read against a public bucket, the same kind of place the
    Copernicus tiles come from. The point of the second source is that
    road, so this pins it rather than the parsing.
    """
    from yerkon.site.fetch import OVERTURE_BUCKET, OvertureBuildings

    source = OvertureBuildings()
    assert OVERTURE_BUCKET.startswith("https://")
    assert "s3" in OVERTURE_BUCKET
    assert source.bucket == OVERTURE_BUCKET
    assert "overpass" not in source.bucket.lower()


def test_both_building_sources_are_offered_and_the_first_that_answers_wins():
    """A site with no buildings because nothing answered and one with no
    buildings because there are none are different evidence, so every
    refusal is recorded on the way past."""
    import numpy as np

    from yerkon.site.fetch import Unreachable, build_site
    from yerkon.site.model import Buildings

    class Refuses:
        name = "first"

        def buildings_for(self, bounds):
            raise Unreachable("no")

    class Answers:
        name = "second"

        def buildings_for(self, bounds):
            return Buildings(
                centre_x_m=np.array([1.0]), centre_y_m=np.array([1.0]),
                radius_m=np.array([2.0]), height_m=np.array([5.0]),
            ), ("a note",)

    site = build_site(
        ANKARA, elevation_sources=(FakeElevation(),),
        buildings_sources=(Refuses(), Answers()),
    )
    assert site.manifest.feature_source == "second"
    assert site.manifest.building_count == 1
    assert any("first" in note for note in site.manifest.notes)


# --- Adding a region, for somebody who has not done it before -------------


def test_a_box_is_given_as_a_centre_and_a_size():
    """What somebody reading a map has is a pin and a size, not four
    decimal degrees.

    A degree of longitude is shorter than a degree of latitude
    everywhere but the equator, so a box computed as if they matched
    comes out as a rectangle nobody asked for.
    """
    from yerkon.site.model import box_around

    box = box_around(37.8716, 32.4847, 12.0)
    per_lat, per_lon = box.metres_per_degree()
    assert (box.east - box.west) * per_lon == pytest.approx(12_000.0, rel=0.01)
    assert (box.north - box.south) * per_lat == pytest.approx(12_000.0, rel=0.01)
    assert box.centre[0] == pytest.approx(37.8716, abs=1e-6)
    assert box.centre[1] == pytest.approx(32.4847, abs=1e-6)

    with pytest.raises(ValueError):
        box_around(37.0, 32.0, 0.0)


def test_a_bare_name_is_fetched_where_the_viewer_looks(tmp_path):
    """The mistake this exists to stop: the fetch reports success and the
    site never appears.

    `--into konya` used to mean a directory called konya beside wherever
    the shell happened to be, which is not the one place `fetched()` and
    the ground picker read.
    """
    import pathlib

    from yerkon.cli import _site_directory
    from yerkon.scenarios import SITES

    assert _site_directory("konya") == SITES / "konya"
    assert _site_directory("sites/konya") == pathlib.Path("sites/konya")
    elsewhere = tmp_path / "konya"
    assert _site_directory(str(elsewhere)) == elsewhere


def test_a_fetch_takes_a_centre_and_a_size_or_four_edges_but_not_both():
    """Both together describe two different boxes, and picking one
    silently is how somebody fetches ground they did not ask for."""
    import argparse

    from yerkon.cli import _box_from

    def asked(**changes):
        fields = dict(centre=None, size=None, south=None, west=None,
                      north=None, east=None)
        fields.update(changes)
        return argparse.Namespace(**fields)

    middle = _box_from(asked(centre="37.8716,32.4847", size=6.0))
    assert middle.centre[0] == pytest.approx(37.8716, abs=1e-6)

    edges = _box_from(asked(south=39.91, west=32.81, north=39.94, east=32.85))
    assert edges.south == 39.91

    with pytest.raises(ValueError, match="either"):
        _box_from(asked(centre="37.8,32.4", size=6.0, south=39.9))
    with pytest.raises(ValueError, match="needs"):
        _box_from(asked(centre="37.8,32.4"))
    with pytest.raises(ValueError, match="enlem"):
        _box_from(asked(centre="somewhere", size=6.0))
    with pytest.raises(ValueError, match="all four"):
        _box_from(asked(south=39.9))


def test_a_coordinate_reads_the_several_ways_people_write_one():
    """Somebody adding a region pastes what a map gave them, and what a
    map gives them depends on the map and on the locale.

    This project writes every other number with a comma for a decimal
    mark (ADR-0035), so `39,9250 32,8370` is what a Turkish reader types
    — and a reader that split on commas saw four numbers and crashed. It
    did: the page's own placeholder was in that form.
    """
    from yerkon.site.model import read_point

    ankara = (39.925, 32.837)
    for written in (
        "39,9250 32,8370",       # comma decimals, as this project writes them
        "39.9250, 32.8370",      # what most maps copy out
        "39.9250 32.8370",
        "39,9250, 32,8370",
        "39,9250,32,8370",       # commas doing both jobs at once
        " 39.9250 ; 32.8370 ",
        "39.9250,32.8370",
    ):
        assert read_point(written) == pytest.approx(ankara), written


def test_a_centre_nobody_typed_says_what_to_type_rather_than_raising_a_key():
    """It fell through to four corners the page had stopped sending, so
    pressing Fetch with the box empty raised `KeyError: 'south'` in a
    background thread and the page showed nothing useful."""
    from yerkon.site.model import read_point

    for nothing in ("", "   ", None):
        with pytest.raises(ValueError, match="Merkez girilmedi"):
            read_point(nothing)

    with pytest.raises(ValueError, match="enlem"):
        read_point("nerede burası")
    with pytest.raises(ValueError, match="-90"):
        read_point("200, 10")
    with pytest.raises(ValueError, match="-180"):
        read_point("39,9250 200,0")


def test_the_fetch_task_refuses_an_empty_centre_in_the_page_s_language():
    """The message is the one thing a person sees when they get it wrong."""
    from yerkon.viewer.state import from_scenario
    from yerkon.viewer.tasks import fetch

    turkish = from_scenario("urban")
    with pytest.raises(ValueError, match="Merkez girilmedi"):
        fetch(turkish, {"name": "x"})(lambda line: None)

    english = turkish.merged({"language": "en"})
    with pytest.raises(ValueError, match="No centre given"):
        fetch(english, {"name": "x", "centre": ""})(lambda line: None)


# --- What this install can fetch with (ADR-0051) --------------------------


def test_a_plain_install_is_short_of_nothing_for_a_fetch():
    """The page used to grey its fetch button and say "pip install" on
    any install without rasterio, requests and pyarrow. None of the three
    is needed now (ADR-0087); they only make a fetch better, and which of
    them is missing is still answerable without importing them."""
    import importlib.util

    from yerkon.site import fetch as fetching

    assert fetching.missing_for_a_fetch() == ()
    assert fetching.FETCH_BETTER_WITH == ("rasterio", "requests", "pyarrow")

    real = importlib.util.find_spec
    try:
        importlib.util.find_spec = (
            lambda name, *rest, **kw: None
            if name.split(".")[0] in ("rasterio", "pyarrow") else real(name, *rest, **kw)
        )
        assert fetching.better_with() == ("rasterio", "pyarrow")
        assert fetching.missing_for_a_fetch() == ()

        # A package that is installed but broken answers "there", and
        # says so itself when it is used.
        def angry(name, *rest, **kw):
            raise ValueError("__spec__ is not set")

        importlib.util.find_spec = angry
        assert fetching.better_with() == fetching.FETCH_BETTER_WITH
    finally:
        importlib.util.find_spec = real


def test_a_missing_package_says_so_in_the_language_on_screen():
    """These sentences name a command somebody has to type, and they
    were the one part of a fetch still written only in English."""
    from yerkon.language import say

    for key in ("site.needs_rasterio", "site.needs_requests",
                "site.needs_pyarrow"):
        for language in ("tr", "en"):
            said = say(key, language)
            assert said and "pip install" in said, (key, language)
        assert say(key, "tr") != say(key, "en")
