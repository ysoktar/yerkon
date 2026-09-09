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
            resolution_m = float(abs(raster.transform.a))
            if raster.crs and raster.crs.to_epsg() == 4326:
                resolution_m *= per_lon

        grid = sampled.reshape(rows, columns)
        if nodata is not None:
            grid = np.where(grid == nodata, np.nan, grid)
        if np.isnan(grid).any():
            filled = float(np.nanmedian(grid)) if not np.isnan(grid).all() else 0.0
            grid = np.where(np.isnan(grid), filled, grid)

        return ElevationGrid(
            values_m=grid, spacing_m=spacing_m,
            source="{} ({})".format(self.name, self.path),
            resolution_m=resolution_m,
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
                        self.name, index, total, error
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
            raise Unreachable("OpenStreetMap access needs requests.") from error

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
            raise Unreachable("{} did not answer: {}".format(self.name, error)) from error

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
            "{} building heights tagged, {} from storey counts, {} defaulted "
            "to {:.0f} m".format(
                from_height_tag, from_levels, from_default, self.default_height_m
            ),
            "Footprints are circles of an area implied by height, because "
            "OpenStreetMap centres were fetched rather than outlines. A link "
            "budget only asks whether a building is in the way.",
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
        detail = "\n  ".join(refusals) if refusals else "no sources were given"
        raise Unreachable("No elevation source answered.\n  " + detail)

    buildings: Optional[Buildings] = None
    feature_source: Optional[str] = None
    if buildings_source is not None:
        try:
            buildings, building_notes = buildings_source.buildings_for(bounds)
            feature_source = buildings_source.name
            notes.extend(building_notes)
        except Unreachable as error:
            notes.append("{} unavailable: {}".format(buildings_source.name, error))

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
