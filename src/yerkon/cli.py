"""Command line entry points.

``fetch`` is the only thing that touches the network; it writes a cache,
and everything else reads that cache and runs offline. ADR-0008 is why
they are separate.

``design`` shows what a set of settings implies, and asks once before
changing them. The panel it prints is built in ``proposal`` and rendered
unchanged by the application too, so both front ends ask the same
question in the same words. See ADR-0001 and ADR-0009.
"""

from __future__ import annotations

import argparse
import sys

from yerkon.site.cache import SiteCache
from yerkon.site.fetch import (
    CopernicusElevation,
    GeoTiffElevation,
    OpenStreetMapBuildings,
    ServiceElevation,
    Unreachable,
    build_site,
)
from yerkon.design import (
    ANTENNA_CHOICES,
    Design,
    MOUNTING_CHOICES,
    RADIO_CHOICES,
    REGION_CHOICES,
    chosen,
    derive,
)
from yerkon.numbers import decimal_comma
from yerkon.proposal import OUTCOME_LABELS, confirm, show_outcome
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
    parser.add_argument(
        "--no-copernicus", action="store_true",
        help="skip the Copernicus tiles, leaving only the query service",
    )
    parser.add_argument(
        "--tile-cache", default="sites/_tiles",
        help="where Copernicus tiles are kept (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    bounds = BoundingBox(
        south=args.south, west=args.west, north=args.north, east=args.east
    )

    sources = []
    if args.geotiff:
        sources.append(GeoTiffElevation(args.geotiff))
    if not args.no_copernicus:
        sources.append(CopernicusElevation(cache_directory=args.tile_cache))
    sources.append(ServiceElevation())

    print("Fetching {:.4f},{:.4f} to {:.4f},{:.4f} at {:.0f} m".format(
        bounds.south, bounds.west, bounds.north, bounds.east, args.spacing
    ))
    print("  ground: {} (each tried in turn until one answers)".format(
        ", then ".join(source.name for source in sources)
    ))
    if not args.no_buildings:
        print("  features: OpenStreetMap")

    # What the query service would cost, and only when it is the source
    # that will actually be asked. A GeoTIFF or a Copernicus tile answers
    # first and makes no calls at all, so quoting a rate limit ahead of
    # them describes a fetch that is not going to happen.
    if isinstance(sources[0], ServiceElevation):
        service = sources[0]
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


EDITS = {
    "region": (REGION_CHOICES, "region"),
    "radio": (RADIO_CHOICES, "radio"),
    "mounting": (MOUNTING_CHOICES, "mounting"),
    "antenna": (ANTENNA_CHOICES, "antenna"),
}

#: Which Design field each command line option sets.
EDIT_FIELDS = {
    "region": "region",
    "radio": "anchor_radio",
    "mounting": "mounting",
    "antenna": "antenna",
    "receiver_height": "receiver_height_m",
    "roughness": "surface_roughness_m",
    "tolerance": "target_ranging_sigma_m",
}


def design(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="yerkon design",
        description=(
            "Show what a set of settings implies. Given an edit, show "
            "everything it would change and ask once before applying it."
        ),
    )
    for option, (catalogue, what) in EDITS.items():
        parser.add_argument(
            "--{}".format(option),
            help="{}: {}".format(what, ", ".join(sorted(catalogue))),
        )
    parser.add_argument("--receiver-height", type=float, help="metres above ground")
    parser.add_argument(
        "--roughness", type=float,
        help="root-mean-square height of the reflecting ground, in metres",
    )
    parser.add_argument(
        "--tolerance", type=float,
        help="ranging error a link may have and still count as usable, in metres",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="answer the confirmation yes without asking",
    )
    args = parser.parse_args(argv)

    current = Design()
    edits = {}
    for option, field in EDIT_FIELDS.items():
        value = getattr(args, option.replace("-", "_"))
        if value is None:
            continue
        if option in EDITS:
            catalogue, what = EDITS[option]
            try:
                value = chosen(catalogue, value, what)
            except ValueError as error:
                print(error, file=sys.stderr)
                return 2
        edits[field] = value

    if not edits:
        print(describe_outcome(current))
        return 0

    def ask(panel: str) -> bool:
        print(panel)
        if args.yes:
            print("\nApplying (--yes).")
            return True
        answer = input("\nApply all of that? [y/N] ").strip().lower()
        return answer in {"y", "yes"}

    try:
        updated, applied = confirm(current, ask, **edits)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    if not applied:
        print("\nNothing changed.")
        return 0

    print()
    print(describe_outcome(updated))
    return 0


def describe_outcome(design_: Design) -> str:
    """The settings and what they imply, in the panel's own words."""
    outcome = derive(design_)
    lines = ["Settings:"]
    lines.append("  region             {}".format(design_.region.region))
    lines.append("  anchor radio       {}".format(design_.anchor_radio.part))
    lines.append("  antenna            {}".format(design_.antenna.part))
    lines.append("  mounting           {}".format(design_.mounting.kind))
    lines.append("  receiver height    {} m".format(
        decimal_comma(design_.receiver_height_m, 2)))
    lines.append("  ground roughness   {} m".format(
        decimal_comma(design_.surface_roughness_m, 2)))
    lines.append("  ranging tolerance  {} m".format(
        decimal_comma(design_.target_ranging_sigma_m, 2)))
    lines.append("")
    lines.append("Which gives:")
    width = max(len(label) for label in OUTCOME_LABELS.values())
    for field, label in OUTCOME_LABELS.items():
        lines.append("  {:<{width}}  {}".format(
            label, show_outcome(field, getattr(outcome, field)), width=width
        ))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__.strip())
        print("\nUsage:")
        print("  yerkon fetch  --south .. --west .. --north .. --east .. --into DIR")
        print("  yerkon design [--region TR] [--mounting mast] [--tolerance 5]")
        return 0
    verb, rest = argv[0], argv[1:]
    if verb == "fetch":
        return fetch(rest)
    if verb == "design":
        return design(rest)
    print("Unknown command: {}".format(verb), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
