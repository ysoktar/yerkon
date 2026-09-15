"""A site: ground, buildings, and a record of where they came from."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from yerkon.language import say


@dataclass(frozen=True)
class BoundingBox:
    """A rectangle in degrees, the unit every source speaks."""

    south: float
    west: float
    north: float
    east: float

    def __post_init__(self) -> None:
        if self.south >= self.north or self.west >= self.east:
            raise ValueError("a bounding box needs south < north and west < east")
        if not -90.0 <= self.south <= 90.0 or not -90.0 <= self.north <= 90.0:
            raise ValueError("latitude out of range")

    @property
    def centre(self) -> tuple[float, float]:
        return (0.5 * (self.south + self.north), 0.5 * (self.west + self.east))

    def metres_per_degree(self) -> tuple[float, float]:
        """Ground distance per degree of latitude and of longitude here.

        Longitude degrees shrink toward the poles, so the two differ and
        the study needs metres rather than degrees. Good to a fraction of
        a percent over a box this size.
        """
        latitude, _ = self.centre
        per_latitude = 111_132.92 - 559.82 * math.cos(2 * math.radians(latitude))
        per_longitude = 111_412.84 * math.cos(math.radians(latitude))
        return per_latitude, per_longitude


def read_point(text: str, language: Optional[str] = None) -> tuple[float, float]:
    """A latitude and longitude, written the several ways people write them.

    Somebody adding a region right-clicks a map and pastes what it gives
    them, and what it gives them depends on the map and on the locale.
    This project writes every other number with a comma for a decimal
    mark (ADR-0035), so a Turkish reader typing a coordinate by hand
    writes `39,9250 32,8370` — which a reader that split on commas would
    see as four numbers. It did, and it crashed.

    So: whitespace separates the two when there is any, and a comma is
    then a decimal mark. With no whitespace, two comma-separated pieces
    are a pair with decimal points, and four are a pair with decimal
    commas. Anything else is refused rather than guessed at, because
    guessing here fetches ground somewhere nobody asked about.
    """
    # A comma touching whitespace is separating the two numbers; a comma
    # between digits is a decimal mark. `39.9250, 32.8370` and
    # `39,9250 32,8370` are both common and they disagree about what a
    # comma is, so which one it is here is decided by what is beside it.
    spaced = re.sub(r",(?=\s)|(?<=\s),", " ", str(text or "").replace(";", " "))
    cleaned = " ".join(spaced.split())
    if not cleaned:
        raise ValueError(say("point.none", language))

    if " " in cleaned:
        pieces = [piece.replace(",", ".") for piece in cleaned.split(" ")]
    else:
        parts = cleaned.split(",")
        if len(parts) == 2:
            pieces = parts
        elif len(parts) == 4:
            pieces = [".".join(parts[:2]), ".".join(parts[2:])]
        else:
            pieces = [cleaned]

    if len(pieces) != 2:
        raise ValueError(say("point.unreadable", language, text=text))
    try:
        latitude, longitude = (float(piece) for piece in pieces)
    except ValueError:
        raise ValueError(
            say("point.unreadable", language, text=text)) from None

    if not -90.0 <= latitude <= 90.0:
        raise ValueError(
            say("point.not_a_latitude", language, value=latitude))
    if not -180.0 <= longitude <= 180.0:
        raise ValueError(
            say("point.not_a_longitude", language, value=longitude))
    return latitude, longitude


def box_around(latitude: float, longitude: float, size_km: float) -> BoundingBox:
    """A square box of that many kilometres, centred on a point.

    What somebody reading a map actually has is a pin and a sense of how
    much ground around it, not four decimal degrees. A degree of
    longitude is shorter than a degree of latitude everywhere but the
    equator, so the two half-widths differ and a box computed as if they
    did not comes out as a rectangle nobody asked for.
    """
    if size_km <= 0.0:
        raise ValueError("a box is some kilometres across")
    if not -90.0 < latitude < 90.0:
        raise ValueError("latitude out of range")
    half_m = size_km * 500.0
    per_latitude = 111_132.92 - 559.82 * math.cos(2 * math.radians(latitude))
    per_longitude = 111_412.84 * math.cos(math.radians(latitude))
    if per_longitude <= 0.0:
        raise ValueError("a square box has no meaning at the pole")
    return BoundingBox(
        south=latitude - half_m / per_latitude,
        north=latitude + half_m / per_latitude,
        west=longitude - half_m / per_longitude,
        east=longitude + half_m / per_longitude,
    )


@dataclass(frozen=True)
class Buildings:
    """Footprints with heights, in local metres.

    Stored as flat arrays rather than polygons because the link budget
    only ever asks whether something blocks a path and by how much, and
    a footprint's outline does not change that answer.
    """

    #: One row per building: centre x, centre y, footprint radius, height.
    centre_x_m: np.ndarray
    centre_y_m: np.ndarray
    radius_m: np.ndarray
    height_m: np.ndarray

    def __post_init__(self) -> None:
        lengths = {
            len(self.centre_x_m), len(self.centre_y_m),
            len(self.radius_m), len(self.height_m),
        }
        if len(lengths) != 1:
            raise ValueError("building arrays must be the same length")

    def __len__(self) -> int:
        return len(self.centre_x_m)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    # --- Finding the few that matter -------------------------------------
    #
    # A link budget asks "what stands here" at sixty-five points along
    # every path, for every link, for every fix. Testing all of them each
    # time is an array pass over the whole town: with the 5 231 buildings
    # Kızılay brought, the table stopped finishing. A uniform grid of
    # cells turns each question into a look at the handful whose footprint
    # reaches that cell.
    #
    # Built on first use rather than in `__post_init__`, because most
    # sites are loaded and never asked, and kept out of the pickle so a
    # worker rebuilds it instead of receiving it (ADR-0025).

    def __getstate__(self) -> dict:
        state = dict(self.__dict__)
        state.pop("_cells", None)
        state.pop("_cell_m", None)
        return state

    def _index(self) -> tuple:
        cells = self.__dict__.get("_cells")
        if cells is not None:
            return cells, self.__dict__["_cell_m"]

        # Wide enough that a typical footprint touches one cell or four,
        # narrow enough that a cell holds few buildings.
        cell_m = max(float(np.median(self.radius_m)) * 4.0, 20.0)
        cells: dict = {}
        for index in range(len(self)):
            x, y, r = (float(self.centre_x_m[index]),
                       float(self.centre_y_m[index]),
                       float(self.radius_m[index]))
            for column in range(int((x - r) // cell_m), int((x + r) // cell_m) + 1):
                for row in range(int((y - r) // cell_m), int((y + r) // cell_m) + 1):
                    cells.setdefault((column, row), []).append(index)
        packed = {key: np.array(value, dtype=int) for key, value in cells.items()}
        object.__setattr__(self, "_cells", packed)
        object.__setattr__(self, "_cell_m", cell_m)
        return packed, cell_m

    def tallest_at(self, x: float, y: float) -> float:
        """The tallest roof over this point, or zero where there is none."""
        if self.is_empty:
            return 0.0
        cells, cell_m = self._index()
        near = cells.get((int(x // cell_m), int(y // cell_m)))
        if near is None:
            return 0.0
        inside = (
            (x - self.centre_x_m[near]) ** 2 + (y - self.centre_y_m[near]) ** 2
        ) <= self.radius_m[near] ** 2
        if not inside.any():
            return 0.0
        return float(self.height_m[near][inside].max())

    def tallest_along(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        samples: int = 64,
    ) -> tuple[float, float]:
        """Highest roof the path passes over, and where along it.

        Returns ``(height, fraction)``. A building only counts when the
        path actually crosses its footprint, so a tower beside the road
        does not obstruct a link running past it.
        """
        if self.is_empty:
            return 0.0, 0.5

        fractions = np.linspace(0.0, 1.0, samples + 1)[1:-1]
        xs = a[0] + (b[0] - a[0]) * fractions
        ys = a[1] + (b[1] - a[1]) * fractions

        best_height = 0.0
        best_fraction = 0.5
        for fraction, x, y in zip(fractions, xs, ys):
            height = self.tallest_at(float(x), float(y))
            if height > best_height:
                best_height, best_fraction = height, float(fraction)
        return best_height, best_fraction


@dataclass(frozen=True)
class SiteManifest:
    """Where every piece of a site came from.

    The point of ADR-0008. A number in the comparison table should be
    traceable to a source in the same way a datasheet figure is, and for
    ground that means recording which service answered, when, and at what
    resolution.
    """

    elevation_source: str
    elevation_resolution_m: float
    fetched_at: str
    feature_source: Optional[str] = None
    building_count: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_buildings(self) -> bool:
        return self.feature_source is not None

    def describe(self, language: Optional[str] = None) -> str:
        parts = [
            say("site.ground", language,
                source=self.elevation_source,
                resolution_m=self.elevation_resolution_m)
        ]
        if self.has_buildings:
            parts.append(say("site.buildings", language,
                             source=self.feature_source,
                             count=self.building_count))
        else:
            parts.append(say("site.no_buildings", language))
        return "; ".join(parts)


@dataclass(frozen=True)
class Site:
    """Real ground and real buildings, in local metres.

    The origin sits at the bounding box's south-west corner, x runs east
    and y runs north. Everything downstream works in these metres and
    never sees a degree.
    """

    bounds: BoundingBox
    elevation_grid_m: np.ndarray
    grid_spacing_m: float
    manifest: SiteManifest
    buildings: Optional[Buildings] = None

    def __post_init__(self) -> None:
        if self.elevation_grid_m.ndim != 2:
            raise ValueError("the elevation grid must be two-dimensional")
        if self.grid_spacing_m <= 0.0:
            raise ValueError("grid spacing must be positive")

    @property
    def width_m(self) -> float:
        return (self.elevation_grid_m.shape[1] - 1) * self.grid_spacing_m

    @property
    def height_m(self) -> float:
        return (self.elevation_grid_m.shape[0] - 1) * self.grid_spacing_m

    def height_at(self, x: float, y: float) -> float:
        """Ground elevation at a point, bilinear between grid nodes.

        Clamps outside the grid rather than raising, because a link budget
        samples along a path that can graze the edge and a hard failure
        there would be less useful than the nearest known ground.
        """
        rows, columns = self.elevation_grid_m.shape
        cx = min(max(x / self.grid_spacing_m, 0.0), columns - 1.0)
        cy = min(max(y / self.grid_spacing_m, 0.0), rows - 1.0)

        x0, y0 = int(cx), int(cy)
        x1, y1 = min(x0 + 1, columns - 1), min(y0 + 1, rows - 1)
        fx, fy = cx - x0, cy - y0

        grid = self.elevation_grid_m
        top = grid[y0, x0] * (1 - fx) + grid[y0, x1] * fx
        bottom = grid[y1, x0] * (1 - fx) + grid[y1, x1] * fx
        return float(top * (1 - fy) + bottom * fy)

    @property
    def relief_m(self) -> float:
        """Difference between the highest and lowest ground on the site."""
        return float(self.elevation_grid_m.max() - self.elevation_grid_m.min())

    def roughness_m(self) -> float:
        """Root-mean-square deviation of the ground from its own local trend.

        Feeds the reflection model, which needs the scatter of a surface
        rather than its shape. Detrended so a uniform slope reads as
        smooth, because a tilted plane reflects perfectly well.
        """
        grid = self.elevation_grid_m
        if grid.size < 4:
            return 0.0
        smoothed = 0.25 * (
            np.roll(grid, 1, axis=0) + np.roll(grid, -1, axis=0)
            + np.roll(grid, 1, axis=1) + np.roll(grid, -1, axis=1)
        )
        interior = (grid - smoothed)[1:-1, 1:-1]
        return float(np.sqrt(np.mean(interior**2)))
