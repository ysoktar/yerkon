"""The only module in this project that opens a socket. See ADR-0008.

Three sources, used together where they are reachable and separately where
they are not. A GeoTIFF on disk needs no network at all, so it is the
source to prefer when someone has downloaded one; the two services fill in
when nobody has.

Every fetcher degrades rather than fails. A site with ground and no
buildings is worth having, and the manifest records what is missing so
nothing downstream mistakes absent data for open ground.
"""

from __future__ import annotations

import datetime
import math
import pathlib
import time
from dataclasses import dataclass
from typing import Optional, Protocol

import numpy as np

from yerkon.language import say
from yerkon.site.model import BoundingBox, Buildings, Site, SiteManifest

DEFAULT_TIMEOUT_S = 30.0


class Unreachable(RuntimeError):
    """A source could not be reached. Never fatal on its own."""


@dataclass(frozen=True)
class ElevationGrid:
    """What an elevation source returns."""

    values_m: np.ndarray
    spacing_m: float
    source: str
    resolution_m: float


class ElevationSource(Protocol):
    """Anything that can say how high the ground is over an area."""

    name: str

    def grid_for(self, bounds: BoundingBox, spacing_m: float) -> ElevationGrid: ...


# --- GeoTIFF on disk ------------------------------------------------------


@dataclass
class GeoTiffElevation:
    """Ground from a raster someone downloaded.

    Reads whatever coordinate system the file carries and resamples onto
    the local metre grid. Preferred over the services when available: it
    needs no network, it is usually higher resolution, and it does not
    change between runs.

    Works with SRTM, Copernicus DEM and the Turkish national data, which
    all ship as GeoTIFF.
    """

    path: str
    name: str = "GeoTIFF"
    #: Replace points the raster does not cover with the median of those
    #: it does.
    #:
    #: On for a single file, because a run needs a number everywhere and
    #: a plausible one beats a crash. Off when several tiles are being
    #: mosaicked, where a gap in one tile is ground in the next and
    #: filling it first would hide the real value behind an invention.
    fill_gaps: bool = True

    def grid_for(self, bounds: BoundingBox, spacing_m: float) -> ElevationGrid:
        try:
            import rasterio
            from rasterio.warp import transform as warp_transform
        except ImportError as error:
            raise Unreachable(
                "Reading a GeoTIFF needs rasterio. Install it with "
                "`pip install rasterio`."
            ) from error

        if not pathlib.Path(self.path).exists():
            raise Unreachable(
                "No file at {}. Check the path; on Windows the shell does "
                "not expand ~ and the extension may be .tiff rather than "
                ".tif.".format(self.path)
            )

        per_lat, per_lon = bounds.metres_per_degree()
        columns = max(int((bounds.east - bounds.west) * per_lon / spacing_m), 2)
        rows = max(int((bounds.north - bounds.south) * per_lat / spacing_m), 2)

        xs_m = np.arange(columns) * spacing_m
        ys_m = np.arange(rows) * spacing_m
        longitudes = bounds.west + xs_m / per_lon
        latitudes = bounds.south + ys_m / per_lat

        mesh_lon, mesh_lat = np.meshgrid(longitudes, latitudes)

        try:
            raster = rasterio.open(self.path)
        except Exception as error:
            raise Unreachable(
                "{} could not be read as a raster: {}".format(self.path, error)
            ) from error

        with raster:
            flat_lon = mesh_lon.ravel().tolist()
            flat_lat = mesh_lat.ravel().tolist()
            if raster.crs and raster.crs.to_epsg() != 4326:
                flat_x, flat_y = warp_transform(
                    "EPSG:4326", raster.crs, flat_lon, flat_lat
                )
            else:
                flat_x, flat_y = flat_lon, flat_lat

            sampled = np.array(
                [value[0] for value in raster.sample(zip(flat_x, flat_y))],
                dtype=float,
            )
            nodata = raster.nodata
            # Points beyond the raster's own extent, marked before the
            # nodata check because a file that tags no nodata value hands
            # back a plausible-looking number out there rather than
            # admitting it has nothing.
            outside = _outside(np.array(flat_x), np.array(flat_y), raster.bounds)
            resolution_m = float(abs(raster.transform.a))
            if raster.crs and raster.crs.to_epsg() == 4326:
                resolution_m *= per_lon

        sampled = np.where(outside, np.nan, sampled)
        grid = sampled.reshape(rows, columns)
        if nodata is not None:
            grid = np.where(grid == nodata, np.nan, grid)
        if self.fill_gaps and np.isnan(grid).any():
            filled = float(np.nanmedian(grid)) if not np.isnan(grid).all() else 0.0
            grid = np.where(np.isnan(grid), filled, grid)

        return ElevationGrid(
            values_m=grid, spacing_m=spacing_m,
            source="{} ({})".format(self.name, self.path),
            resolution_m=resolution_m,
        )


def _outside(xs: np.ndarray, ys: np.ndarray, extent) -> np.ndarray:
    """Which sample points the raster does not cover."""
    return (
        (xs < extent.left) | (xs > extent.right)
        | (ys < extent.bottom) | (ys > extent.top)
    )


# --- Copernicus DEM, straight from public object storage ------------------


COPERNICUS_BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"


def copernicus_tile_name(latitude: int, longitude: int) -> str:
    """The tile covering the degree square whose corner this is.

    Tiles are one degree on a side and named by their south-west corner,
    so a box spanning two degrees needs two tiles.
    """
    ns = "N" if latitude >= 0 else "S"
    ew = "E" if longitude >= 0 else "W"
    return "Copernicus_DSM_COG_10_{}{:02d}_00_{}{:03d}_00_DEM".format(
        ns, abs(latitude), ew, abs(longitude)
    )


@dataclass
class CopernicusElevation:
    """Ground from the Copernicus 30 m model in public object storage.

    The best of the three sources and the one to reach for first. It needs
    no key, imposes no rate limit, serves whole one-degree tiles in a few
    seconds, and is the same data the download portals hand out. A tile
    for central Turkey is 3600 by 3600 samples covering 651 to 1863 m.

    Tiles are cached on disk, so a second site in the same degree square
    costs nothing.
    """

    cache_directory: str = "sites/_tiles"
    name: str = "Copernicus DEM 30 m"
    nominal_resolution_m: float = 30.0
    bucket: str = COPERNICUS_BUCKET

    def tiles_covering(self, bounds: BoundingBox) -> list[tuple[int, int]]:
        south, north = math.floor(bounds.south), math.ceil(bounds.north)
        west, east = math.floor(bounds.west), math.ceil(bounds.east)
        return [
            (lat, lon)
            for lat in range(south, north)
            for lon in range(west, east)
        ]

    def _tile_path(self, latitude: int, longitude: int) -> pathlib.Path:
        directory = pathlib.Path(self.cache_directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / "{}.tif".format(copernicus_tile_name(latitude, longitude))

    def ensure_tile(self, latitude: int, longitude: int, http=None) -> pathlib.Path:
        """Fetch one tile unless it is already on disk.

        ``http`` stands in for the requests module so this can be
        exercised without a network.
        """
        path = self._tile_path(latitude, longitude)
        if path.exists() and path.stat().st_size > 0:
            return path

        if http is None:
            try:
                import requests as http
            except ImportError as error:
                raise Unreachable("Fetching a tile needs requests.") from error

        name = copernicus_tile_name(latitude, longitude)
        url = "{}/{}/{}.tif".format(self.bucket, name, name)
        try:
            with http.get(url, stream=True, timeout=DEFAULT_TIMEOUT_S * 10) as response:
                if response.status_code == 404:
                    raise Unreachable(
                        "No Copernicus tile for {}; the square is probably "
                        "all sea.".format(name)
                    )
                response.raise_for_status()
                # Written beside the tile and renamed only once the whole
                # transfer arrived. A tile is a hundred megabytes and a
                # cut connection would otherwise leave a truncated file
                # that every later run would read as cached.
                partial = path.with_suffix(".partial")
                try:
                    with open(partial, "wb") as handle:
                        for block in response.iter_content(chunk_size=1 << 20):
                            handle.write(block)
                    partial.replace(path)
                finally:
                    partial.unlink(missing_ok=True)
        except Unreachable:
            raise
        except Exception as error:
            raise Unreachable(
                "{} unreachable: {}".format(self.name, ServiceElevation._cause(error))
            ) from error
        return path

    def grid_for(self, bounds: BoundingBox, spacing_m: float) -> ElevationGrid:
        tiles = self.tiles_covering(bounds)
        if not tiles:
            raise Unreachable("That box covers no Copernicus tile.")

        paths = [str(self.ensure_tile(lat, lon)) for lat, lon in tiles]

        # One tile is the common case and reads directly. Several are
        # mosaicked, which needs the whole set open at once.
        if len(paths) == 1:
            grid = GeoTiffElevation(paths[0], name=self.name).grid_for(bounds, spacing_m)
        else:
            grid = _mosaic_grid(paths, bounds, spacing_m, self.name)

        return ElevationGrid(
            values_m=grid.values_m, spacing_m=grid.spacing_m,
            # Written the same way in both languages, because it is a
            # record of what was fetched rather than a sentence about it,
            # and it is stored in the manifest on disk (ADR-0035).
            source="{} ×{}".format(self.name, len(paths)),
            resolution_m=self.nominal_resolution_m,
        )


def _mosaic_grid(
    paths: list[str], bounds: BoundingBox, spacing_m: float, name: str
) -> ElevationGrid:
    """Sample several tiles into one grid, taking whichever covers a point.

    Each tile is read without gap filling, so a point it does not cover
    stays absent instead of becoming that tile's median. The tiles are
    then laid over one another and the first real value at each point
    wins; where they overlap they are the same data, so which one wins
    does not matter.
    """
    grids = [
        GeoTiffElevation(path, name=name, fill_gaps=False).grid_for(bounds, spacing_m)
        for path in paths
    ]

    combined = grids[0].values_m.copy()
    for grid in grids[1:]:
        combined = np.where(np.isnan(combined), grid.values_m, combined)

    if np.isnan(combined).any():
        filled = float(np.nanmedian(combined)) if not np.isnan(combined).all() else 0.0
        combined = np.where(np.isnan(combined), filled, combined)

    return ElevationGrid(
        values_m=combined, spacing_m=spacing_m,
        source=name, resolution_m=grids[0].resolution_m,
    )


# --- Elevation service ----------------------------------------------------


@dataclass
class ServiceElevation:
    """Ground from a public elevation service.

    Defaults to OpenTopoData's SRTM 30 m dataset. Queries are batched
    because the service takes a hundred locations per request and a site
    needs thousands.

    Slower and coarser than a GeoTIFF, and it depends on somebody else's
    server staying up, which is exactly why ADR-0008 puts the result in a
    cache instead of calling this during a run.
    """

    endpoint: str = "https://api.opentopodata.org/v1/srtm30m"
    name: str = "OpenTopoData SRTM 30 m"
    batch: int = 100
    nominal_resolution_m: float = 30.0
    #: Seconds between requests.
    #:
    #: The public service allows one a second and answers 429 to anything
    #: faster. Firing as fast as the network allows gets the first batch
    #: rejected, which is what happened the first time this ran.
    seconds_between_requests: float = 1.1
    #: How many times to wait and retry when the service says 429.
    retries_on_rate_limit: int = 4
    #: Most requests this fetcher will issue before refusing.
    #:
    #: The public service allows a thousand calls a day at one a second.
    #: A grid is easy to ask for and expensive to serve: a 35 by 14 km box
    #: at 30 m spacing is 479,000 points, which is 4,791 calls and about
    #: an hour and a half of somebody else's server. Refusing up front is
    #: better than discovering it after four hundred requests.
    request_budget: int = 400

    def points_required(self, bounds: BoundingBox, spacing_m: float) -> int:
        per_lat, per_lon = bounds.metres_per_degree()
        columns = max(int((bounds.east - bounds.west) * per_lon / spacing_m), 2)
        rows = max(int((bounds.north - bounds.south) * per_lat / spacing_m), 2)
        return rows * columns

    def _refuse_if_too_large(self, bounds: BoundingBox, spacing_m: float) -> None:
        points = self.points_required(bounds, spacing_m)
        requests_needed = (points + self.batch - 1) // self.batch
        if requests_needed <= self.request_budget:
            return

        affordable = self.request_budget * self.batch
        coarser = spacing_m * math.sqrt(points / affordable)
        raise Unreachable(
            "This area needs {points:,} points, which is {calls:,} calls to "
            "{name}. Its public limit is a thousand a day at one a second, "
            "so the fetch would fail part way through. Either use "
            "--spacing {coarser:.0f} or coarser, or download a raster for "
            "this area and pass --geotiff, which needs no network and is "
            "higher resolution.".format(
                points=points, calls=requests_needed, name=self.name,
                coarser=math.ceil(coarser / 10.0) * 10.0,
            )
        )

    def grid_for(self, bounds: BoundingBox, spacing_m: float) -> ElevationGrid:
        self._refuse_if_too_large(bounds, spacing_m)
        try:
            import requests
        except ImportError as error:
            raise Unreachable("The elevation service needs requests.") from error

        per_lat, per_lon = bounds.metres_per_degree()
        columns = max(int((bounds.east - bounds.west) * per_lon / spacing_m), 2)
        rows = max(int((bounds.north - bounds.south) * per_lat / spacing_m), 2)

        longitudes = bounds.west + np.arange(columns) * spacing_m / per_lon
        latitudes = bounds.south + np.arange(rows) * spacing_m / per_lat
        mesh_lon, mesh_lat = np.meshgrid(longitudes, latitudes)
        points = list(zip(mesh_lat.ravel(), mesh_lon.ravel()))

        heights: list[float] = []
        total_batches = (len(points) + self.batch - 1) // self.batch
        last_call_at = 0.0

        for index, start in enumerate(range(0, len(points), self.batch)):
            chunk = points[start:start + self.batch]
            locations = "|".join("{:.6f},{:.6f}".format(la, lo) for la, lo in chunk)

            wait = self.seconds_between_requests - (time.monotonic() - last_call_at)
            if wait > 0.0:
                time.sleep(wait)

            payload = self._call(requests, locations, index + 1, total_batches)
            last_call_at = time.monotonic()

            for result in payload.get("results", []):
                value = result.get("elevation")
                heights.append(float(value) if value is not None else math.nan)

        if len(heights) != rows * columns:
            raise Unreachable(
                "{} returned {} of {} points".format(
                    self.name, len(heights), rows * columns
                )
            )

        grid = np.array(heights, dtype=float).reshape(rows, columns)
        if np.isnan(grid).any():
            filled = float(np.nanmedian(grid)) if not np.isnan(grid).all() else 0.0
            grid = np.where(np.isnan(grid), filled, grid)

        return ElevationGrid(
            values_m=grid, spacing_m=spacing_m, source=self.name,
            resolution_m=self.nominal_resolution_m,
        )

    @staticmethod
    def _cause(error: Exception) -> str:
        """The reason a request failed, without the query it carried.

        A requests exception embeds the whole URL, which here is a
        hundred coordinates. Formatting the exception drags them back
        into the message even when the message itself does not mention
        them, so the URL is cut out explicitly.
        """
        text = str(error)

        # The real reason sits after the URL, so look for it first.
        # Stripping the URL before that throws the reason away with it,
        # which is what the first attempt at this did.
        marker = "(Caused by "
        if marker in text:
            text = text[text.index(marker) + len(marker):].rstrip(")")
        elif "url:" in text:
            text = text.split("url:")[0]

        text = " ".join(text.split())
        return text[:200] if text else type(error).__name__

    def _call(self, requests, locations: str, index: int, total: int) -> dict:
        """One request, waiting out a rate limit rather than giving up.

        A 429 means the service is asking for patience, not refusing, so
        it is worth waiting for. Anything else is a real failure and is
        reported without the query attached, because a rejected URL
        carries a hundred coordinates and burying the reason in them
        helps nobody.
        """
        delay = self.seconds_between_requests
        for attempt in range(self.retries_on_rate_limit + 1):
            try:
                response = requests.get(
                    self.endpoint, params={"locations": locations},
                    timeout=DEFAULT_TIMEOUT_S,
                )
            except Exception as error:
                raise Unreachable(
                    "{} unreachable on request {} of {}: {}".format(
                        self.name, index, total, self._cause(error)
                    )
                ) from error

            if response.status_code == 429:
                if attempt == self.retries_on_rate_limit:
                    raise Unreachable(
                        "{} is rate limiting this fetch and did not let up "
                        "after {} attempts. Its public quota is a thousand "
                        "calls a day; this run needs {}. Use a raster with "
                        "--geotiff instead.".format(
                            self.name, attempt + 1, total
                        )
                    )
                retry_after = response.headers.get("Retry-After")
                pause = float(retry_after) if retry_after else delay
                time.sleep(pause)
                delay *= 2.0
                continue

            if not response.ok:
                raise Unreachable(
                    "{} answered {} on request {} of {}".format(
                        self.name, response.status_code, index, total
                    )
                )

            try:
                return response.json()
            except ValueError as error:
                raise Unreachable(
                    "{} sent something that is not JSON".format(self.name)
                ) from error

        raise Unreachable("{} did not answer".format(self.name))


# --- Buildings ------------------------------------------------------------

DEFAULT_STOREY_HEIGHT_M = 3.0
DEFAULT_BUILDING_HEIGHT_M = 9.0


@dataclass
class OpenStreetMapBuildings:
    """Building footprints and heights from OpenStreetMap.

    Height comes from the ``height`` tag where a mapper recorded one, from
    ``building:levels`` times a storey height where they recorded that
    instead, and from a default otherwise. Which of the three applied is
    counted and reported, because a site whose heights are mostly the
    default is a weaker piece of evidence than one whose heights are
    mapped, and the difference should not be invisible.
    """

    endpoint: str = "https://overpass-api.de/api/interpreter"
    name: str = "OpenStreetMap"
    storey_height_m: float = DEFAULT_STOREY_HEIGHT_M
    default_height_m: float = DEFAULT_BUILDING_HEIGHT_M

    def buildings_for(self, bounds: BoundingBox) -> tuple[Buildings, tuple[str, ...]]:
        try:
            import requests
        except ImportError as error:
            raise Unreachable(say("site.needs_requests")) from error

        query = (
            "[out:json][timeout:60];"
            "way[building]({s},{w},{n},{e});"
            "out center tags;"
        ).format(s=bounds.south, w=bounds.west, n=bounds.north, e=bounds.east)

        try:
            response = requests.post(
                self.endpoint, data={"data": query}, timeout=DEFAULT_TIMEOUT_S * 3
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            raise Unreachable(
                say("site.no_answer", None, name=self.name, error=error)
            ) from error

        per_lat, per_lon = bounds.metres_per_degree()
        xs, ys, radii, heights = [], [], [], []
        from_height_tag = from_levels = from_default = 0

        for element in payload.get("elements", []):
            centre = element.get("center") or {}
            latitude, longitude = centre.get("lat"), centre.get("lon")
            if latitude is None or longitude is None:
                continue

            tags = element.get("tags", {})
            height = _parse_height(tags.get("height"))
            if height is not None:
                from_height_tag += 1
            else:
                levels = _parse_height(tags.get("building:levels"))
                if levels is not None:
                    height = levels * self.storey_height_m
                    from_levels += 1
                else:
                    height = self.default_height_m
                    from_default += 1

            xs.append((longitude - bounds.west) * per_lon)
            ys.append((latitude - bounds.south) * per_lat)
            radii.append(_assumed_footprint_radius_m(height))
            heights.append(height)

        notes = (
            say("site.heights_tagged", None,
                tagged=from_height_tag, levels=from_levels,
                defaulted=from_default, default_m=self.default_height_m),
            say("site.footprints"),
        )

        return (
            Buildings(
                centre_x_m=np.array(xs), centre_y_m=np.array(ys),
                radius_m=np.array(radii), height_m=np.array(heights),
            ),
            notes,
        )


def _parse_height(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    text = str(raw).strip().lower().replace("m", "").strip()
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0.0 else None


def _assumed_footprint_radius_m(height_m: float) -> float:
    """A stand-in footprint, since only centres were fetched.

    Taller buildings are broader on average. This is a shape assumption,
    not a measurement, and the manifest says so.
    """
    return max(6.0, 0.9 * math.sqrt(max(height_m, 1.0)) * 3.0)


# --- Putting a site together ---------------------------------------------


def build_site(
    bounds: BoundingBox,
    spacing_m: float = 30.0,
    elevation_sources: tuple[ElevationSource, ...] = (),
    buildings_source: Optional[OpenStreetMapBuildings] = None,
) -> Site:
    """Fetch a site, using whatever is reachable.

    Elevation sources are tried in order and the first that answers wins,
    so callers put the local GeoTIFF first and the services after it.
    Buildings are fetched alongside and their absence is recorded rather
    than treated as open ground.

    Raises only when no elevation source answered, because a site without
    ground is not a site.
    """
    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    notes: list[str] = []

    grid: Optional[ElevationGrid] = None
    refusals: list[str] = []
    for source in elevation_sources:
        try:
            grid = source.grid_for(bounds, spacing_m)
            break
        except Unreachable as error:
            reason = "{}: {}".format(getattr(source, "name", source), error)
            refusals.append(reason)
            notes.append(reason)

    if grid is None:
        # Carry each source's own reason forward. A caller told only that
        # nothing answered cannot tell a network failure from an area too
        # large to ask for, and those need opposite responses.
        detail = "\n  ".join(refusals) if refusals else say("site.no_sources")
        raise Unreachable(say("site.no_elevation", None, detail=detail))

    buildings: Optional[Buildings] = None
    feature_source: Optional[str] = None
    if buildings_source is not None:
        try:
            buildings, building_notes = buildings_source.buildings_for(bounds)
            feature_source = buildings_source.name
            notes.extend(building_notes)
        except Unreachable as error:
            notes.append(say("site.unreachable", None,
                              name=buildings_source.name, error=error))

    return Site(
        bounds=bounds,
        elevation_grid_m=grid.values_m,
        grid_spacing_m=grid.spacing_m,
        manifest=SiteManifest(
            elevation_source=grid.source,
            elevation_resolution_m=grid.resolution_m,
            fetched_at=fetched_at,
            feature_source=feature_source,
            building_count=0 if buildings is None else len(buildings),
            notes=tuple(notes),
        ),
        buildings=buildings,
    )
