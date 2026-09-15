"""The map somebody picks ground on, and the seam it sits across.

The picker draws a box; Python fetches one. Two languages, one piece of
arithmetic, and the failure mode is quiet: a box that reads 3 km on
screen and comes back 2,7 km on disk, with nothing to say which was
wrong. So the agreement is pinned rather than assumed.

Node runs the real module — the same file the browser loads, not a copy
of its formulas — and is skipped where there is no node, because this
project's users run it on machines that have Python and a browser and
need not have anything else.
"""

import json
import pathlib
import shutil
import subprocess

import pytest

from yerkon.site.model import box_around

STATIC = pathlib.Path(__file__).resolve().parents[1] / "src/yerkon/viewer/static"
MAP_JS = STATIC / "map.js"

node = pytest.mark.skipif(shutil.which("node") is None,
                          reason="node is not installed here")


def run_in_node(script: str):
    """Evaluate a snippet with the real `map.js` imported."""
    whole = 'import * as map from "{}";\n{}'.format(MAP_JS.as_uri(), script)
    finished = subprocess.run(
        ["node", "--input-type=module", "-e", whole],
        capture_output=True, text=True, timeout=60,
    )
    assert finished.returncode == 0, finished.stderr
    return json.loads(finished.stdout)


# --- The arithmetic the two sides share -----------------------------------


@node
@pytest.mark.parametrize("latitude", [0.0, 39.925, 60.0, -33.9])
@pytest.mark.parametrize("size_km", [1.0, 3.0, 40.0])
def test_the_box_the_map_draws_is_the_box_python_fetches(latitude, size_km):
    """Within a metre, everywhere anybody would put a site.

    The constants are the ones in `box_around`: a degree of longitude is
    shorter than a degree of latitude everywhere but the equator, so a
    box that uses one figure for both comes out a rectangle nobody drew.
    """
    longitude = 32.837
    drawn = run_in_node(
        "console.log(JSON.stringify("
        "map.boxAround({}, {}, {})))".format(latitude, longitude, size_km))
    fetched = box_around(latitude, longitude, size_km)

    for edge in ("south", "north", "west", "east"):
        # A ten-millionth of a degree is a centimetre of ground.
        assert drawn[edge] == pytest.approx(getattr(fetched, edge), abs=1e-7), edge


@node
def test_the_projection_is_the_one_the_fetch_downloads_tiles_in():
    """The picker and `tile_of` have to agree, or the tile somebody is
    looking at is not the tile that arrives."""
    from yerkon.site.fetch import tile_of

    for latitude, longitude, zoom in [
        (39.925, 32.837, 17), (0.0, 0.0, 3), (-33.87, 151.21, 12),
    ]:
        drawn = run_in_node(
            "console.log(JSON.stringify(["
            "Math.floor(map.lonToX({lon}, {z}) / 256), "
            "Math.floor(map.latToY({lat}, {z}) / 256)]))".format(
                lat=latitude, lon=longitude, z=zoom))
        assert tuple(drawn) == tile_of(latitude, longitude, zoom)


@node
def test_a_point_survives_the_round_trip_through_screen_pixels():
    """Every gesture on the map is degrees to pixels and back."""
    same = run_in_node("""
      const out = [];
      for (const [lat, lon, z] of [[39.925, 32.837, 14], [-12.5, -70.1, 8]]) {
        const x = map.lonToX(lon, z), y = map.latToY(lat, z);
        out.push([map.xToLon(x, z) - lon, map.yToLat(y, z) - lat]);
      }
      console.log(JSON.stringify(out));
    """)
    for dLon, dLat in same:
        assert abs(dLon) < 1e-9 and abs(dLat) < 1e-9


@node
def test_how_much_ground_a_box_covers_is_measured_the_same_way():
    """The count in the map's bar is `across * along / spacing²`, and the
    spans it multiplies have to be the ones the fetch will sample."""
    from yerkon.site.model import BoundingBox

    box = BoundingBox(south=39.9115, west=32.8194, north=39.9385, east=32.8546)
    span = run_in_node(
        "console.log(JSON.stringify(map.boxSpanKm({})))".format(
            json.dumps({"south": box.south, "west": box.west,
                        "north": box.north, "east": box.east})))
    per_lat, per_lon = box.metres_per_degree()
    assert span["across"] == pytest.approx(
        (box.east - box.west) * per_lon / 1000, rel=1e-9)
    assert span["along"] == pytest.approx(
        (box.north - box.south) * per_lat / 1000, rel=1e-9)


# --- What the page is handed ----------------------------------------------


def test_the_page_can_actually_load_the_module():
    """It is served by name, and a module the server does not serve is a
    map that never opens — which is not a failure the page reports, it is
    a button that does nothing."""
    import yerkon.viewer.server as server

    served = []

    class OnlyTheRouting(server.Handler):
        def __init__(self, path):
            self.path = path

        def _file(self, name, content_type):
            served.append((name, content_type))

        def send_error(self, code, *args, **kwargs):
            served.append(("error", code))

        def _json(self, produce):
            served.append(("json", None))

    OnlyTheRouting("/map.js").do_GET()
    assert served == [("map.js", "text/javascript; charset=utf-8")]
    assert MAP_JS.exists()


def test_the_engine_names_the_map_rather_than_the_page_keeping_a_copy():
    """Every other list the page draws from is named by the engine, so
    that `--map-tiles` reaches the picker without a second copy
    somewhere to forget."""
    from yerkon.viewer.scene import MAP_TILES, scene
    from yerkon.viewer.state import from_scenario

    payload = scene(from_scenario("urban"))
    assert payload["map_tiles"] == MAP_TILES[0]
    assert "{z}" in payload["map_tiles"] and "{x}" in payload["map_tiles"]


def test_no_tile_address_is_a_choice_the_payload_can_carry():
    """`--map-tiles ""` on a machine with no way out. An empty string has
    to survive as an empty string: the page draws ruled ground and says
    why, which is not the same as a map that failed to load."""
    from yerkon.viewer import scene as scene_module
    from yerkon.viewer.state import from_scenario

    was = scene_module.MAP_TILES[0]
    try:
        scene_module.MAP_TILES[0] = ""
        assert scene_module.scene(from_scenario("urban"))["map_tiles"] == ""
    finally:
        scene_module.MAP_TILES[0] = was


def test_the_map_ships_with_openstreetmap_and_the_drape_ships_with_nothing():
    """Not two minds about one question (ADR-0042).

    Picking a place is the few dozen tiles OSM's policy calls ordinary
    use. Draping a city is thousands at once, which it calls bulk — so
    that one has no default and the person choosing a provider is the
    person accepting its terms.
    """
    from yerkon.site.fetch import TileImagery
    from yerkon.viewer.scene import MAP_TILES

    assert "openstreetmap.org" in MAP_TILES[0]
    assert TileImagery().url_template == ""


def test_the_gesture_hint_and_the_credit_are_in_both_languages():
    """OpenStreetMap asks to be credited where its tiles are shown, and a
    credit in one language is a credit missing from the other."""
    words = (STATIC / "words.js").read_text(encoding="utf-8")
    for key in ("fetch.map.credit", "fetch.map.hint", "fetch.map.none",
                "fetch.map.take", "fetch.map.draw"):
        assert '"{}"'.format(key) in words, key
    assert "OpenStreetMap" in words
