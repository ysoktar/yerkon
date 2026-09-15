"""A photograph of the ground: the tiles, the stitching, and what reads it.

Every tile server is blocked from the sandbox this was built in, the same
way Overpass is (ADR-0021). So rather than record a payload and test half
the path, these stand up a tile server on localhost and fetch through the
real code: the URL template, the threads, the disk cache, the stitch and
the bounds it reports all run. Only the internet is missing, and the
internet is not the part that has bugs in it.
"""

import http.server
import math
import socket
import threading

import numpy as np
import pytest

from yerkon.site.fetch import (
    DEFAULT_ZOOM,
    MOST_TILES,
    TileImagery,
    Unreachable,
    build_site,
    tile_bounds,
    tile_of,
)
from yerkon.site.model import Aerial, BoundingBox

ANKARA = BoundingBox(south=39.9115, west=32.8194, north=39.9385, east=32.8546)


# --- The tile numbering ---------------------------------------------------


def test_a_tile_is_numbered_the_way_every_web_map_numbers_one():
    """Slippy-map numbering, so any `{z}/{x}/{y}` server works.

    Zoom nought is one tile holding the world; each step doubles.
    """
    assert tile_of(0.0, -180.0, 0) == (0, 0)
    assert tile_of(0.0, 0.0, 1) == (1, 1)

    x, y = tile_of(39.925, 32.837, 17)
    box = tile_bounds(x, y, 17)
    assert box.west <= 32.837 <= box.east
    assert box.south <= 39.925 <= box.north


def test_the_default_zoom_is_about_a_metre_a_pixel():
    """Fine enough to see a building, coarse enough that a city is not
    tens of thousands of tiles."""
    box = tile_bounds(*tile_of(39.925, 32.837, DEFAULT_ZOOM), DEFAULT_ZOOM)
    _, per_lon = box.metres_per_degree()
    across_m = (box.east - box.west) * per_lon
    assert 0.5 < across_m / 256 < 2.0


# --- Fetching, for real, over a socket ------------------------------------


class Tiles(http.server.BaseHTTPRequestHandler):
    """Serves a distinct colour per tile, so a stitch can be checked."""

    def do_GET(self):                                    # noqa: N802
        from PIL import Image

        try:
            _, zoom, x, y = self.path.rsplit("/", 3)
            x, y = int(x), int(y.split(".")[0])
        except ValueError:
            self.send_error(404)
            return
        if (x + y) % 3 == 0:
            # A third of them are missing, because some always are. The
            # share is high on purpose: a box is a handful of tiles, and a
            # rule that refuses one in a hundred would refuse none of them
            # and test nothing.
            self.send_error(404)
            return

        import io

        colour = (x % 256, y % 256, 200)
        buffer = io.BytesIO()
        Image.new("RGB", (256, 256), colour).save(buffer, "PNG")
        body = buffer.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):                        # noqa: D102
        pass


@pytest.fixture
def tile_server():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Tiles)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:{}/{{z}}/{{x}}/{{y}}.png".format(port)
    finally:
        server.shutdown()


def test_a_photograph_is_stitched_from_the_tiles_that_cover_the_box(
        tile_server, tmp_path):
    """The whole path: numbering, threads, cache, stitch, crop."""
    imagery = TileImagery(url_template=tile_server, zoom=14,
                          cache_directory=str(tmp_path))
    picture = imagery.image_for(ANKARA)

    assert isinstance(picture, Aerial)
    assert picture.pixels.ndim == 3 and picture.pixels.shape[2] == 3
    assert picture.zoom == 14
    # Whole tiles, so it covers at least the box it was asked for.
    assert picture.bounds.west <= ANKARA.west
    assert picture.bounds.east >= ANKARA.east
    assert picture.bounds.south <= ANKARA.south
    assert picture.bounds.north >= ANKARA.north
    assert 1.0 < picture.metres_per_pixel < 100.0


def test_a_tile_that_never_arrives_is_a_hole_rather_than_a_failure(
        tile_server, tmp_path):
    """Losing a whole city's photograph over one missing square is not
    what anybody wants, and a grey square is obvious on screen.

    Of the six tiles this box covers, the stand-in server refuses two.
    """
    picture = TileImagery(url_template=tile_server, zoom=14,
                          cache_directory=str(tmp_path)).image_for(ANKARA)
    flat = picture.pixels.reshape(-1, 3)
    assert (flat == np.array([128, 128, 128])).all(axis=1).any(), "no hole"
    assert not (flat == np.array([128, 128, 128])).all(), "nothing but holes"


def test_the_second_fetch_of_the_same_ground_asks_for_nothing(
        tile_server, tmp_path):
    """Tiles land on disk beside the Copernicus ones."""
    imagery = TileImagery(url_template=tile_server, zoom=14,
                          cache_directory=str(tmp_path))
    first = imagery.image_for(ANKARA)
    on_disk = list((tmp_path / "aerial").rglob("*.png"))
    assert on_disk, "nothing was cached"

    # With the server gone, the cache alone has to answer.
    gone = TileImagery(url_template="http://127.0.0.1:1/{z}/{x}/{y}.png",
                       zoom=14, cache_directory=str(tmp_path))
    again = gone.image_for(ANKARA)
    assert np.array_equal(first.pixels, again.pixels)


def test_no_url_says_that_choosing_a_provider_is_the_caller_s_to_make():
    """Every provider has terms and most want a key. A default here would
    be somebody else's terms accepted on their behalf."""
    with pytest.raises(Unreachable, match="karo adresi"):
        TileImagery(url_template="").image_for(ANKARA)


def test_a_box_that_would_be_ten_thousand_tiles_is_refused_before_it_starts(
        tile_server, tmp_path):
    """Usually somebody who left the zoom at 19 over a region."""
    with pytest.raises(Unreachable, match="karo"):
        TileImagery(url_template=tile_server, zoom=19,
                    cache_directory=str(tmp_path)).image_for(
            BoundingBox(south=39.0, west=32.0, north=40.0, east=33.0))


def test_nothing_coming_back_at_all_is_a_failure_rather_than_a_grey_sheet(
        tmp_path):
    """One missing tile is a hole; none of them arriving is a wrong URL,
    a missing key or the wrong network, and saying so beats handing back
    a picture of nothing."""
    with pytest.raises(Unreachable, match="hiçbir karo"):
        TileImagery(url_template="http://127.0.0.1:1/{z}/{x}/{y}.png",
                    zoom=14, cache_directory=str(tmp_path)).image_for(ANKARA)


# --- What reads it --------------------------------------------------------


def test_the_colour_under_a_point_is_the_pixel_over_it():
    """Nearest pixel rather than blended: a mix of a roof and the road
    beside it is a colour neither of them is."""
    pixels = np.zeros((4, 4, 3), dtype=np.uint8)
    pixels[0, 0] = (255, 0, 0)        # north-west
    pixels[3, 3] = (0, 0, 255)        # south-east
    picture = Aerial(pixels=pixels,
                     bounds=BoundingBox(south=39.0, west=32.0,
                                        north=39.4, east=32.4))

    north_west = picture.sample(np.array([32.01]), np.array([39.39]))
    south_east = picture.sample(np.array([32.39]), np.array([39.01]))
    assert tuple(north_west[0]) == (255, 0, 0)
    assert tuple(south_east[0]) == (0, 0, 255)


def test_a_point_outside_the_photograph_clamps_rather_than_raising():
    """A link path can graze the edge, and the elevation clamps there for
    the same reason."""
    pixels = np.full((2, 2, 3), 7, dtype=np.uint8)
    picture = Aerial(pixels=pixels,
                     bounds=BoundingBox(south=39.0, west=32.0,
                                        north=39.1, east=32.1))
    assert tuple(picture.sample(np.array([99.0]), np.array([-80.0]))[0]) == (7, 7, 7)


def test_a_site_turns_its_own_metres_into_a_colour(tile_server, tmp_path):
    """The site knows where its origin is; the picture knows only degrees."""
    from yerkon.site.fetch import ElevationGrid

    class FlatGround:
        name = "test ground"

        def grid_for(self, bounds, spacing_m):
            return ElevationGrid(values_m=np.zeros((8, 8)) + 900.0,
                                 spacing_m=spacing_m, source=self.name,
                                 resolution_m=spacing_m)

    site = build_site(
        ANKARA, spacing_m=100.0, elevation_sources=(FlatGround(),),
        imagery_source=TileImagery(url_template=tile_server, zoom=14,
                                   cache_directory=str(tmp_path)),
    )
    assert site.aerial is not None
    colours = site.colours_at([0.0, site.width_m], [0.0, site.height_m])
    assert colours.shape == (2, 3)
    assert any("hava görüntüsü" in note for note in site.manifest.notes)


def test_a_site_with_no_photograph_says_so_rather_than_inventing_one():
    """Nothing in the simulation reads the picture, so its absence costs
    nothing — but a caller drawing it has to be able to tell."""
    from yerkon.scenarios import fetched

    site = fetched("kizilay")
    assert site.aerial is None
    assert site.colours_at([0.0], [0.0]) is None


def test_the_photograph_survives_being_written_out_and_read_back(
        tile_server, tmp_path):
    """It is stored as a picture rather than as an array: it is one, it
    compresses like one, and somebody can open it."""
    from yerkon.site.cache import SiteCache
    from yerkon.site.fetch import ElevationGrid

    class FlatGround:
        name = "test ground"

        def grid_for(self, bounds, spacing_m):
            return ElevationGrid(values_m=np.zeros((8, 8)) + 900.0,
                                 spacing_m=spacing_m, source=self.name,
                                 resolution_m=spacing_m)

    site = build_site(
        ANKARA, spacing_m=100.0, elevation_sources=(FlatGround(),),
        imagery_source=TileImagery(url_template=tile_server, zoom=14,
                                   cache_directory=str(tmp_path / "tiles")),
    )
    cache = SiteCache(tmp_path / "written")
    cache.save(site)
    assert (tmp_path / "written" / "aerial.png").exists()

    again = cache.load()
    assert again.aerial is not None
    assert np.array_equal(again.aerial.pixels, site.aerial.pixels)
    assert again.aerial.zoom == site.aerial.zoom
    assert again.aerial.bounds.west == pytest.approx(site.aerial.bounds.west)


# --- What the page is handed ---------------------------------------------


def test_a_site_with_no_photograph_tells_the_page_so_rather_than_nothing():
    """The scene carries the picture's address, not its pixels, and says
    plainly when there is none so the page can grey its tick (ADR-0036)."""
    from dataclasses import replace

    from yerkon.viewer.scene import scene
    from yerkon.viewer.state import fetched_sites, from_scenario

    state = replace(from_scenario("urban"), site=fetched_sites()[0])
    assert scene(state)["terrain"]["aerial"] is None


def test_the_photograph_is_addressed_by_site_rather_than_served_as_colours(
        tile_server, tmp_path, monkeypatch):
    """A mesh node is three bytes of colour and there are twenty-two
    thousand of them, so colours in the scene payload would be a quarter
    of a megabyte on every drag. The address goes instead, and it carries
    the site's name so one site's picture is never handed back for
    another's."""
    from yerkon.site.cache import SiteCache
    from yerkon.site.fetch import ElevationGrid
    from yerkon.viewer import scene as scene_module
    from yerkon.viewer import state as state_module

    class FlatGround:
        name = "test ground"

        def grid_for(self, bounds, spacing_m):
            return ElevationGrid(values_m=np.zeros((40, 40)) + 900.0,
                                 spacing_m=spacing_m, source=self.name,
                                 resolution_m=spacing_m)

    site = build_site(
        ANKARA, spacing_m=60.0, elevation_sources=(FlatGround(),),
        imagery_source=TileImagery(url_template=tile_server, zoom=14,
                                   cache_directory=str(tmp_path / "tiles")),
    )
    places = tmp_path / "places"
    SiteCache(places / "resimli").save(site)
    monkeypatch.setattr(state_module, "SITES", places)
    monkeypatch.setattr(scene_module, "fetched_sites", lambda: ("resimli",))
    monkeypatch.setattr("yerkon.scenarios.SITES", places)

    from dataclasses import replace

    from yerkon.viewer.state import from_scenario

    payload = scene_module.scene(
        replace(from_scenario("urban"), site="resimli").on_measured_ground())
    aerial = payload["terrain"]["aerial"]
    assert aerial["url"] == "/api/aerial.png?site=resimli"
    assert aerial["metres_per_pixel"] > 0.0
    assert "colours" not in payload["terrain"]

    # Whole tiles, so the picture hangs off the site on every side and
    # the corner the page is told about is the real one.
    west, south, east, north = aerial["extent_m"]
    assert west <= 0.0 and south <= 0.0
    assert east >= site.width_m and north >= site.height_m


def test_asking_for_a_picture_by_a_path_rather_than_a_name_gets_nothing():
    """The name arrives in a query string, and a query string is
    somewhere a person can type `../../etc/passwd`."""
    import yerkon.viewer.server as server

    refused = []

    class OnlyTheRouting(server.Handler):
        def __init__(self, path):
            self.path = path

        def send_error(self, code, *args, **kwargs):
            refused.append(code)

    for path in ("/api/aerial.png?site=../../etc",
                 "/api/aerial.png?site=.",
                 "/api/aerial.png?site=a/b",
                 "/api/aerial.png"):
        OnlyTheRouting(path)._aerial()
    assert refused == [404, 404, 404, 404]


def test_fetching_again_without_a_photograph_takes_the_old_one_off_the_disk(
        tile_server, tmp_path):
    """The manifest would already say there is none, so nothing would
    read it. But the viewer serves this file by name, and a file on disk
    is a thing that can be served."""
    from dataclasses import replace

    from yerkon.site.cache import SiteCache
    from yerkon.site.fetch import ElevationGrid

    class FlatGround:
        name = "test ground"

        def grid_for(self, bounds, spacing_m):
            return ElevationGrid(values_m=np.zeros((8, 8)) + 900.0,
                                 spacing_m=spacing_m, source=self.name,
                                 resolution_m=spacing_m)

    site = build_site(
        ANKARA, spacing_m=100.0, elevation_sources=(FlatGround(),),
        imagery_source=TileImagery(url_template=tile_server, zoom=14,
                                   cache_directory=str(tmp_path / "tiles")),
    )
    cache = SiteCache(tmp_path / "again")
    cache.save(site)
    assert (tmp_path / "again" / "aerial.png").exists()

    cache.save(replace(site, aerial=None))
    assert not (tmp_path / "again" / "aerial.png").exists()
    assert cache.load().aerial is None
