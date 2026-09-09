"""Command line entry points.

Two verbs, and ADR-0008 is the reason they are separate. ``fetch`` is the
only thing that touches the network; it writes a cache. Everything else
reads that cache and runs offline.
"""

from __future__ import annotations

import argparse
import sys

from yerkon.site.cache import SiteCache
from yerkon.site.fetch import (
    GeoTiffElevation,
    OpenStreetMapBuildings,
    ServiceElevation,
    Unreachable,
    build_site,
)
from yerkon.site.model import BoundingBox


def fetch(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon fetch",
        description=(
            "Download ground and buildings for an area into a cache. This is "
            "the only command that uses the network; runs read the cache."
        ),
    )
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument(
        "--into", required=True,
        help="cache directory to write, for example sites/ankara-o20",
    )
    parser.add_argument(
        "--spacing", type=float, default=30.0,
        help="grid spacing in metres (default: %(default)s)",
    )
    parser.add_argument(
        "--geotiff",
        help=(
            "a downloaded elevation raster to prefer over the online "
            "service. Faster, higher resolution, and it needs no network."
        ),
    )
    parser.add_argument(
        "--no-buildings", action="store_true",
        help="skip OpenStreetMap; the site records that nobody looked",
    )
    args = parser.parse_args(argv)

    bounds = BoundingBox(
        south=args.south, west=args.west, north=args.north, east=args.east
    )

    sources = []
    if args.geotiff:
        sources.append(GeoTiffElevation(args.geotiff))
    sources.append(ServiceElevation())

    print("Fetching {:.4f},{:.4f} to {:.4f},{:.4f} at {:.0f} m".format(
        bounds.south, bounds.west, bounds.north, bounds.east, args.spacing
    ))
    for source in sources:
        print("  elevation source: {}".format(source.name))
    if not args.no_buildings:
        print("  features: OpenStreetMap")

    service = next((s for s in sources if isinstance(s, ServiceElevation)), None)
    if service is not None and not args.geotiff:
        points = service.points_required(bounds, args.spacing)
        calls = (points + service.batch - 1) // service.batch
        minutes = calls * service.seconds_between_requests / 60.0
        print("  {:,} points, {:,} calls, about {:.0f} minutes at the "
              "service's rate limit".format(points, calls, minutes))

    try:
        site = build_site(
            bounds,
            spacing_m=args.spacing,
            elevation_sources=tuple(sources),
            buildings_source=None if args.no_buildings else OpenStreetMapBuildings(),
        )
    except Unreachable as error:
        print("\nNothing answered.\n  {}".format(error), file=sys.stderr)
        print(
            "\nEither pass --geotiff with a downloaded raster, or run this "
            "from a machine that can reach the elevation service.",
            file=sys.stderr,
        )
        return 1

    SiteCache(args.into).save(site)

    print("\nWrote {}".format(args.into))
    print("  {}".format(site.manifest.describe()))
    print("  {:.0f} x {:.0f} m, relief {:.0f} m, roughness {:.2f} m".format(
        site.width_m, site.height_m, site.relief_m, site.roughness_m()
    ))
    for note in site.manifest.notes:
        print("  note: {}".format(note))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.strip())
        print("\nUsage:\n  yerkon fetch --south .. --west .. --north .. --east .. --into DIR")
        return 0
    verb, rest = argv[0], argv[1:]
    if verb == "fetch":
        return fetch(rest)
    print("Unknown command: {}".format(verb), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
