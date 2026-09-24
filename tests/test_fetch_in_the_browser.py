"""Fetching ground from the published site (ADR-0086).

The site's simulator is Python in a browser worker, which reads no
GeoTIFF, no GeoParquet and cannot ask the Copernicus bucket. So a fetch
there takes terrain tiles and Overpass, and the photograph crosses from
the worker to the page as base64. These run the same code on localhost:
a terrain tile server stands up, Overpass is recorded, and only the
browser's own request is missing.
"""

import base64
import http.server
import io
import json
import math
import pathlib
import socket
import threading

import numpy as np
import pytest

from yerkon.site import fetch as fetching
from yerkon.site.fetch import (
    AERIAL_TILES,
    PAGE_MOST_TILES,
    OpenStreetMapRoads,
    TerrainTileElevation,
    Unreachable,
    fitted_zoom,
    tile_bounds,
    tile_of,
)
from yerkon.site.model import BoundingBox, box_around

STATIC = pathlib.Path(__file__).resolve().parents[1] / "src/yerkon/viewer/static"
KIZILAY = box_around(39.9208, 32.8541, 3.0)


# --- Terrain tiles --------------------------------------------------------


def _height_at(latitude, longitude):
    """A plane that rises 1000 m a degree northward and 100 m a degree
    eastward, so orientation and scale can both be read back."""
    return 900.0 + (latitude - 39.9) * 1000.0 + (longitude - 32.8) * 100.0


class Terrarium(http.server.BaseHTTPRequestHandler):
    """Terrarium tiles of `_height_at`, pixel by pixel."""

    asked = []

    def do_GET(self):                                    # noqa: N802
        from PIL import Image

        _, zoom, x, y = self.path.rsplit("/", 3)
        zoom, x, y = int(zoom), int(x), int(y.split(".")[0])
        Terrarium.asked.append((zoom, x, y))
        world = 256 * 2 ** zoom
        columns = (x * 256 + np.arange(256) + 0.5) / world * 360.0 - 180.0
        rows = np.degrees(np.arctan(np.sinh(
            math.pi * (1.0 - 2.0 * (y * 256 + np.arange(256) + 0.5) / world))))
        longitude, latitude = np.meshgrid(columns, rows)
        value = _height_at(latitude, longitude) + 32768.0
        red = np.floor(value / 256.0)
        green = np.floor(value - red * 256.0)
        blue = np.floor((value - red * 256.0 - green) * 256.0)
        pixels = np.stack([red, green, blue], axis=-1).astype(np.uint8)
        buffer = io.BytesIO()
        Image.fromarray(pixels, "RGB").save(buffer, "PNG")
        body = buffer.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):                        # noqa: D102
        pass


@pytest.fixture
def terrarium():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Terrarium)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    Terrarium.asked = []
    try:
        yield "http://127.0.0.1:{}/{{z}}/{{x}}/{{y}}.png".format(port)
    finally:
        server.shutdown()


def test_terrain_tiles_read_back_the_ground_they_encode(terrarium, tmp_path):
    """North up, east right, metres in metres."""
    source = TerrainTileElevation(url_template=terrarium,
                                  cache_directory=str(tmp_path))
    grid = source.grid_for(KIZILAY, 30.0)

    per_lat, per_lon = KIZILAY.metres_per_degree()
    rows, columns = grid.values_m.shape
    latitudes = KIZILAY.south + np.arange(rows) * 30.0 / per_lat
    longitudes = KIZILAY.west + np.arange(columns) * 30.0 / per_lon
    lon, lat = np.meshgrid(longitudes, latitudes)
    expected = _height_at(lat, lon)
    # A tile pixel is about 30 m here and the plane rises 0,27 m across
    # one, so the residue is interpolation and the encoding's 1/256 m.
    assert np.abs(grid.values_m - expected).max() < 0.5
    assert grid.source.startswith("AWS Terrain Tiles z")


def test_the_zoom_follows_the_grid_step_and_the_tile_budget():
    """A pixel no wider than the step; coarser if the box is too big."""
    source = TerrainTileElevation()
    fine = source.zoom_for(KIZILAY, 30.0)
    coarse = source.zoom_for(KIZILAY, 120.0)
    assert fine > coarse
    assert fine <= source.most_zoom
    huge = BoundingBox(south=38.0, west=31.0, north=41.0, east=35.0)
    zoom = source.zoom_for(huge, 30.0)
    assert fetching._tile_count(huge, zoom) <= source.most_tiles


def test_a_second_fetch_of_the_same_ground_asks_for_nothing(terrarium, tmp_path):
    TerrainTileElevation(url_template=terrarium,
                         cache_directory=str(tmp_path)).grid_for(KIZILAY, 30.0)
    first = len(Terrarium.asked)
    assert first > 0
    TerrainTileElevation(url_template=terrarium,
                         cache_directory=str(tmp_path)).grid_for(KIZILAY, 30.0)
    assert len(Terrarium.asked) == first


def test_no_tile_arriving_is_a_failure_not_flat_ground(tmp_path):
    with pytest.raises(Unreachable):
        TerrainTileElevation(url_template="http://127.0.0.1:1/{z}/{x}/{y}.png",
                             cache_directory=str(tmp_path)).grid_for(KIZILAY, 30.0)


# --- Roads from Overpass --------------------------------------------------


class RecordedRoads:
    def __init__(self):
        self.asked = None
        self.status_code = 200
        self.headers = {}
        self.content = json.dumps({"elements": [
            {"type": "way", "tags": {"highway": "primary"}, "geometry": [
                {"lat": 39.915, "lon": 32.845}, {"lat": 39.925, "lon": 32.855}]},
            {"type": "way", "tags": {"highway": "residential"}, "geometry": [
                {"lat": 39.920, "lon": 32.850}]},
        ]}).encode("utf-8")

    def post(self, url, data=None, timeout=None):
        self.asked = {"url": url, "data": data}
        return self


def test_osm_roads_ask_for_driven_ways_and_land_in_metres(monkeypatch):
    import sys
    import types

    recorded = RecordedRoads()
    module = types.ModuleType("requests")
    module.post = recorded.post
    monkeypatch.setitem(sys.modules, "requests", module)

    roads, notes = OpenStreetMapRoads().roads_for(KIZILAY)

    query = recorded.asked["data"]["data"]
    assert "way[highway~" in query and "primary" in query
    assert "footway" not in query
    assert "out geom" in query
    # The one-point way has nowhere to drive and is dropped.
    assert len(roads) == 1
    per_lat, per_lon = KIZILAY.metres_per_degree()
    (x0, y0), (x1, y1) = roads[0]
    assert x0 == pytest.approx((32.845 - KIZILAY.west) * per_lon)
    assert y1 == pytest.approx((39.925 - KIZILAY.south) * per_lat)
    assert notes


# --- The photograph -------------------------------------------------------


def test_a_large_box_takes_a_coarser_photograph_rather_than_none():
    city = BoundingBox(south=39.80, west=32.70, north=40.00, east=32.95)
    zoom = fitted_zoom(city, 17, PAGE_MOST_TILES)
    assert zoom < 17
    assert fetching._tile_count(city, zoom) <= PAGE_MOST_TILES
    assert fitted_zoom(KIZILAY, 15, PAGE_MOST_TILES) == 15


def test_the_page_offers_a_tick_and_names_no_address():
    """The owner chose the provider; nobody pastes a URL (ADR-0086)."""
    page = (STATIC / "simulator.html").read_text(encoding="utf-8")
    assert 'type="checkbox" id="fetch-imagery"' in page
    assert "{z}/{x}/{y}" not in page
    assert "fetch-imagery-zoom" not in page
    words = (STATIC / "words.js").read_text(encoding="utf-8")
    assert "Esri" in words        # the credit the provider asks for
    assert "arcgisonline" not in words
    assert "{z}" in AERIAL_TILES and "{y}" in AERIAL_TILES


def test_the_fetch_task_sends_the_built_in_provider_when_ticked(monkeypatch):
    """What the tick turns into, without fetching anything."""
    from yerkon.site import fetch as source
    from yerkon.viewer import tasks
    from yerkon.viewer.state import ViewState

    seen = {}

    def build_site(bounds, **kw):
        seen.update(kw)
        raise Unreachable("stop here")

    monkeypatch.setattr(source, "build_site", build_site)
    work = tasks.fetch(ViewState(), {"name": "deneme", "centre": "39,92 32,85",
                                     "size_km": 2, "imagery": True})
    with pytest.raises(Unreachable):
        work(lambda line: None)
    imagery = seen["imagery_source"]
    assert imagery.url_template == AERIAL_TILES
    assert "Esri" in imagery.name
    # And a desktop tries Copernicus first and terrain tiles after it.
    names = [type(s).__name__ for s in seen["elevation_sources"]]
    assert names[:2] == ["CopernicusElevation", "TerrainTileElevation"]
    assert "OpenStreetMapRoads" in [type(s).__name__ for s in seen["roads_sources"]]


def test_in_a_browser_the_fetch_uses_only_what_a_browser_reaches(monkeypatch):
    from yerkon.site import fetch as source
    from yerkon.site import http
    from yerkon.viewer import tasks
    from yerkon.viewer.state import ViewState

    monkeypatch.setattr(http, "IN_A_BROWSER", True)
    assert source.missing_for_a_fetch() == ()

    seen = {}

    def build_site(bounds, **kw):
        seen.update(kw)
        raise Unreachable("stop here")

    monkeypatch.setattr(source, "build_site", build_site)
    work = tasks.fetch(ViewState(), {"name": "deneme", "centre": "39,92 32,85",
                                     "size_km": 2, "imagery": False})
    with pytest.raises(Unreachable):
        work(lambda line: None)
    kinds = lambda key: [type(s).__name__ for s in seen[key]]  # noqa: E731
    assert kinds("elevation_sources") == ["TerrainTileElevation"]
    assert kinds("buildings_sources") == ["OpenStreetMapBuildings"]
    assert kinds("roads_sources") == ["OpenStreetMapRoads"]
    assert seen["imagery_source"] is None


def test_the_photograph_crosses_from_the_worker_as_base64(tmp_path, monkeypatch):
    """It used to be refused with a 404, so a site fetched in the browser
    had no picture."""
    from PIL import Image

    from yerkon.viewer import server

    place = tmp_path / "yer"
    place.mkdir()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(place / "aerial.png")
    monkeypatch.setattr(server, "SITES", tmp_path)

    status, kind, text, encoding = json.loads(
        server.answer("GET", "/api/aerial.png?site=yer"))
    assert status == 200 and kind == "image/png" and encoding == "base64"
    picture = Image.open(io.BytesIO(base64.b64decode(text)))
    assert picture.getpixel((0, 0)) == (10, 20, 30)

    # Text answers are unchanged: three entries, no encoding.
    assert len(json.loads(server.answer("GET", "/api/figures.toml"))) == 3


def test_the_page_asks_for_the_photograph_through_fetch():
    """An image's own request would bypass the worker."""
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    loader = app[app.index("function loadPhotograph"):]
    loader = loader[:loader.index("\n}\n")]
    assert "fetch(aerial.url)" in loader
    assert "picture.src = aerial.url" not in loader
    local = (STATIC / "local.js").read_text(encoding="utf-8")
    assert 'reply.encoding === "base64"' in local
    worker = (STATIC / "sim-worker.js").read_text(encoding="utf-8")
    assert 'loadPackage("pillow")' in worker
