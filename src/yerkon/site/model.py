"""A site: ground, buildings, and a record of where they came from."""

from __future__ import annotations

import math
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
            inside = (
                (x - self.centre_x_m) ** 2 + (y - self.centre_y_m) ** 2
            ) <= self.radius_m**2
            if not inside.any():
                continue
            height = float(self.height_m[inside].max())
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
