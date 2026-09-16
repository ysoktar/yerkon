"""The cache that lets a run be reproduced without a network.

ADR-0008: fetching writes here, running reads here. A cache directory is
a self-contained artefact. Commit it, send it to someone, and they get the
same numbers.
"""

from __future__ import annotations

import json
import pathlib
from typing import Optional

import numpy as np

from yerkon.site.model import (
    Aerial,
    BoundingBox,
    Buildings,
    Furniture,
    Site,
    SiteManifest,
)

MANIFEST_NAME = "manifest.json"
ELEVATION_NAME = "elevation.npy"
BUILDINGS_NAME = "buildings.npz"
#: The photograph, as a picture rather than as an array: it is
#: one, it compresses like one, and somebody can open it.
AERIAL_NAME = "aerial.png"
#: Roads and road furniture, as arrays rather than as JSON: Kızılay is
#: 1 638 lines of a few points each, and a text form of that is a
#: megabyte to parse where a compressed array is a fraction of it.
ROADS_NAME = "roads.npz"
FURNITURE_NAME = "furniture.npz"


class SiteCache:
    """A directory holding one fetched area."""

    def __init__(self, directory: str | pathlib.Path) -> None:
        self.directory = pathlib.Path(directory)

    @property
    def exists(self) -> bool:
        return (self.directory / MANIFEST_NAME).exists()

    def save(self, site: Site) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        np.save(self.directory / ELEVATION_NAME, site.elevation_grid_m)

        if site.buildings is not None and not site.buildings.is_empty:
            np.savez(
                self.directory / BUILDINGS_NAME,
                centre_x_m=site.buildings.centre_x_m,
                centre_y_m=site.buildings.centre_y_m,
                radius_m=site.buildings.radius_m,
                height_m=site.buildings.height_m,
            )

        if site.aerial is not None:
            from PIL import Image

            Image.fromarray(site.aerial.pixels, "RGB").save(
                self.directory / AERIAL_NAME, optimize=True)
        else:
            # Fetched again without one, over a site that had one. The
            # manifest would already say there is no photograph, so
            # nothing would read it — but the viewer serves this file by
            # name, and a file on disk is a thing that can be served.
            (self.directory / AERIAL_NAME).unlink(missing_ok=True)

        roads_path = self.directory / ROADS_NAME
        if site.roads_m:
            # One flat array of points and an array of lengths, because
            # `savez` cannot hold a ragged list and padding 1 638 lines
            # to the longest would store mostly nothing.
            flat = np.concatenate([np.asarray(line, dtype=float)
                                   for line in site.roads_m])
            np.savez_compressed(
                roads_path, points=flat,
                lengths=np.array([len(line) for line in site.roads_m]))
        else:
            roads_path.unlink(missing_ok=True)

        furniture_path = self.directory / FURNITURE_NAME
        if site.furniture is not None:
            np.savez_compressed(
                furniture_path,
                x_m=site.furniture.x_m, y_m=site.furniture.y_m,
                kind=np.array(site.furniture.kind, dtype=object),
            )
        else:
            furniture_path.unlink(missing_ok=True)

        payload = {
            "bounds": {
                "south": site.bounds.south, "west": site.bounds.west,
                "north": site.bounds.north, "east": site.bounds.east,
            },
            "grid_spacing_m": site.grid_spacing_m,
            # What the picture covers, which is whole tiles and so a
            # little more than the box that was asked for.
            "aerial": None if site.aerial is None else {
                "bounds": {
                    "south": site.aerial.bounds.south,
                    "west": site.aerial.bounds.west,
                    "north": site.aerial.bounds.north,
                    "east": site.aerial.bounds.east,
                },
                "source": site.aerial.source,
                "zoom": site.aerial.zoom,
            },
            "manifest": {
                "elevation_source": site.manifest.elevation_source,
                "elevation_resolution_m": site.manifest.elevation_resolution_m,
                "fetched_at": site.manifest.fetched_at,
                "feature_source": site.manifest.feature_source,
                "building_count": site.manifest.building_count,
                "notes": list(site.manifest.notes),
            },
        }
        (self.directory / MANIFEST_NAME).write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def load(self) -> Site:
        if not self.exists:
            raise FileNotFoundError(
                "No site cached at {}. Run `yerkon fetch` for this area "
                "first; see ADR-0008.".format(self.directory)
            )
        payload = json.loads((self.directory / MANIFEST_NAME).read_text(encoding="utf-8"))
        grid = np.load(self.directory / ELEVATION_NAME)

        buildings: Optional[Buildings] = None
        buildings_path = self.directory / BUILDINGS_NAME
        if buildings_path.exists():
            stored = np.load(buildings_path)
            buildings = Buildings(
                centre_x_m=stored["centre_x_m"], centre_y_m=stored["centre_y_m"],
                radius_m=stored["radius_m"], height_m=stored["height_m"],
            )

        aerial: Optional[Aerial] = None
        aerial_path = self.directory / AERIAL_NAME
        if aerial_path.exists() and payload.get("aerial"):
            from PIL import Image

            stored = payload["aerial"]
            aerial = Aerial(
                pixels=np.asarray(Image.open(aerial_path).convert("RGB"),
                                  dtype=np.uint8),
                bounds=BoundingBox(**stored["bounds"]),
                source=stored.get("source", ""),
                zoom=int(stored.get("zoom", 0)),
            )

        roads = ()
        roads_path = self.directory / ROADS_NAME
        if roads_path.exists():
            stored = np.load(roads_path)
            points, lengths = stored["points"], stored["lengths"]
            at = 0
            lines = []
            for count in lengths:
                lines.append(tuple(
                    (float(x), float(y)) for x, y in points[at:at + count]))
                at += int(count)
            roads = tuple(lines)

        furniture = None
        furniture_path = self.directory / FURNITURE_NAME
        if furniture_path.exists():
            stored = np.load(furniture_path, allow_pickle=True)
            furniture = Furniture(
                x_m=stored["x_m"], y_m=stored["y_m"],
                kind=tuple(str(k) for k in stored["kind"]),
            )

        raw = payload["manifest"]
        return Site(
            roads_m=roads,
            furniture=furniture,
            bounds=BoundingBox(**payload["bounds"]),
            elevation_grid_m=grid,
            grid_spacing_m=payload["grid_spacing_m"],
            manifest=SiteManifest(
                elevation_source=raw["elevation_source"],
                elevation_resolution_m=raw["elevation_resolution_m"],
                fetched_at=raw["fetched_at"],
                feature_source=raw["feature_source"],
                building_count=raw["building_count"],
                notes=tuple(raw["notes"]),
            ),
            buildings=buildings,
            aerial=aerial,
        )
